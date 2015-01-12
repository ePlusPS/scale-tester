import cmd
import pprint
import logging
import heatclient.v1.client as heat_client
import keystoneclient.v2_0.client as keystone_client
import heatclient.openstack.common.uuidutils as uuidutils
import yaml
import time
import re

LOG = logging.getLogger("scale_tester")

TENANT_NAME_REGEX = "tenant-test-.*"

class DeleteStacksCmd(cmd.Command):
    """
    This is a factory cmd that walks resource data structures (tenants and
    users) and creates invidual CreateStackCmd for each tenant. 
    """
    
    def __init__(self, cmd_context, program):
        super(DeleteStacksCmd,self).__init__()
        self.context = cmd_context
        self.program = program

    def init(self):
        #if ("program.resources" in self.program.context):
        #    return cmd.SUCCESS
        #else:
        #    return cmd.FAILURE_HALT
        
        # make sure that self.program.context['program_runner'] exists
        return cmd.SUCCESS

    def execute(self):
        
        openstack_conf = self.program.context["openstack_conf"]
        auth_url = openstack_conf["openstack_auth_url"]
        heat_url = openstack_conf['openstack_heat_url']

        admin_keystone_c = cmd.get_keystone_client(self.program)
        tenant_list = admin_keystone_c.tenants.list()

        for tenant in tenant_list:

            if re.match(TENANT_NAME_REGEX,tenant.name) != None:
                LOG.info("DELETE TENANT: %s" % (tenant))

                user_list = admin_keystone_c.tenants.list_users(tenant)
                username = None
                for user in user_list:
                    if user.name != "admin":
                        LOG.info("    DELETE USER: %s" % (user))
                        username = user.name

                if username == None:
                    continue

                user_keystone_c = keystone_client.Client(auth_url=auth_url,
                                                         username=username,
                                                         password=username,
                                                         tenant_name=tenant.name)

                user_heat_url = heat_url % (user_keystone_c.auth_tenant_id)
                
                LOG.info("user_heat_url = %s" % (user_heat_url)) 
                
                user_heat_c = heat_client.Client(user_heat_url,
                                                 token=user_keystone_c.auth_token)
                
                stack_list = user_heat_c.stacks.list()
                for stack in stack_list:
                    LOG.info("    DELETE STACK: %s" % stack)
                    
                    try:
                        user_heat_c.stacks.delete(stack.id)
                        LOG.info("tenant stack (id=%s) deleted" % (stack.id))
                    except Exception:
                        LOG.error("Exception while deleting stack %s" % stack.id)
                
                    time_limit = 60
                    start_time = time.time()
                    cur_time = time.time()
                    while cur_time - start_time < time_limit:
                        time.sleep(5)
                        cur_time = time.time()
                        
                        stack_status = _get_stack(user_heat_c, stack.stack_name)
                        LOG.info("        STACK STATUS: %s" % stack_status)
                    
                    
        return cmd.SUCCESS

    def undo(self):
        return cmd.SUCCESS


def _get_stack(self, heat_session, stack_name):
    filter = {"name": stack_name}
    stack_list = heat_session.stacks.list(filters=filter)
    for stack_item in stack_list:
        LOG.debug("stack status: %s" % stack_item)
        LOG.debug("   stack_id: %s" % stack_item.id)
        return stack_item
