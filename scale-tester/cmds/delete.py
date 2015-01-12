import cmd
import pprint
import logging
import heatclient.v1.client as heat_client
import keystoneclient.v2_0.client as keystone_client
import heatclient.openstack.common.uuidutils as uuidutils
import yaml
import time


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

        admin_keystone_c = cmd.get_keystone_client(self.program)
        tenant_list = admin_keystone_c.tenants.list()

        for tenant in tenant_list:

            print("DELETE TENANT: %s" % (tenant))

            user_list = admin_keystone_c.tenants.list_users(tenant)
            for user in user_list:
                print("    DELETE USER: %s" % (user))

            heat_url = openstack_conf['openstack_heat_url']
            #heat_url = heat_url % (self.tenant_keystone_c.auth_tenant_id)
        
            #LOG.debug("heat_url = %s" % (heat_url)) 
        
            #self.tenant_heat_c = heat_client.Client(heat_url,
            #                                        token=self.admin_keystone_c.auth_token)

        return cmd.SUCCESS

    def undo(self):
        return cmd.SUCCESS
