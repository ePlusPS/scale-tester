import cmd
import pprint
import logging
import heatclient.v1.client as heat_client
import keystoneclient.v2_0.client as keystone_client
import heatclient.openstack.common.uuidutils as uuidutils
import yaml
import time

LOG = logging.getLogger("scale_tester")

class StackCreateBarrierCmd(cmd.Command):

    def __init__(self, cmd_context, program, **kwargs):
        """
        constructor
        kwargs - 'stack_name', 'tenant_name', 'user_name'
                 'vm_image_id'
                 'external_network'
                 'heat_hot_file'
        """
        super(cmd.Command,self).__init__()
        self.context = cmd_context
        self.program = program

    def init(self):
        # precondition, tenant and user exists
        # check that hot file key exists
        LOG.debug("init")
        LOG.debug(pprint.pformat(self.context))
        return cmd.SUCCESS

    def execute(self):

        all_stacks = self.program.context["all_stacks"]
        pending_stacks = []
        done_stacks = []
        for stack_cmd in all_stacks:
            pending_stacks.append(stack_cmd)
            stack_cmd.heat_session = self._get_session_for_stack(stack_cmd)

        while len(pending_stacks) > 0:
            for stack_cmd in pending_stacks:
                stack_status = self._get_stack(stack_cmd.heat_session, stack_cmd.stack_name)                
                if(stack_status['stack_status'] == "CREATE_COMPLETE"):
                    pending_stacks.remove(stack_cmd)
                    done_stacks.append(stack_cmd)

            if len(pending_stacks) > 0:
                time.sleep(5)

        return cmd.SUCCESS
    
    def undo(self):
        """
        No-op
        """
        return cmd.SUCCESS

    def _get_session_for_stack(self, stack_cmd):
        openstack_conf = self.program.context['openstack_conf']
        auth_url = openstack_conf["openstack_auth_url"]
        heat_url = openstack_conf["openstack_heat_url"]
        # admin_user = openstack_conf["openstack_user"]
        # admin_passwd = openstack_conf["openstack_password"]
        # admin_tenant_name = "admin"

        keystone_session = keystone_client.Client(auth_url=auth_url,
                                                  username=stack_cmd.user_name,
                                                  password=stack_cmd.user_name,
                                                  tenant_name=stack_cmd.tenant_name)

        heat_session = heat_client.Client(heat_url,
                                          token=keystone_session.auth_token)
        
        return heat_session


    
    def _get_stack(self, heat_session, stack_name):
        filter = {"name": stack_name}
        stack_list = heat_session.stacks.list(filters=filter)
        for stack_item in stack_list:
            LOG.debug("stack status: %s" % stack_item)
            LOG.debug("   stack_id: %s" % stack_item.id)
            stack_id = stack_item.id
            return stack_item
    
