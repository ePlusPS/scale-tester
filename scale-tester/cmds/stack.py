# placeholder for heatclient related with commands

import cmd
import logging
import heatclient.v1.client as heat_client
import heatclient.openstack.common.uuidutils as uuidutils

LOG = logging.getLogger("scale_tester")

class StackReqRsp:
    """
    Represents a common input/output object for interacting
    with different stack creation APIs.

    Can be fed into either a HeatClient based stack create 
    service or nova/neutron based stack create implementation.
    """

    def __init__(self,**kwargs):
        self.networks = []
        self.vms = []
        self.routers = []

class CreateStacksCmd(cmd.Command):
    """
    This cmd creates invidual CreateStackCmd 
    commands based on the number of tenants
    """
    
    def __init__(self):
        pass

    def init(self):
        pass

    def execute(self):
        # walk the number of tenants
        #  figure out how many networks
        pass

    def undo(self):
        pass

class CreateStackCmd(cmd.Command):
    """
    This cmd creates a OpenStack Heat Stack instance
    """
    
    def __init__(self, tenant_name, user_name, program):
        self.tenant_name = tenant
        self.user_name   = user_name
        self.program = program

    def init(self):
        # precondition, tenant and user exist
        return cmd.SUCCESS

    def execute(self):
        """
        connect as tenant user and obtain keystone handle
        """
        keystone_c = \
         cmd.get_keystone_client_for_tenant_user(tenant_name=self.tenant_name,
                                  user_name=self.user_name,
                                  password=self.user_name,
                                  auth_url=\
                                  self.program.context["openstack_auth_url"])

        heat_url = self.program.context['openstack_heat_url'] %
            (keystone_c.auth_tenant_id)
        
        LOG.debug("heat_url = %s" % (heat_url)) 
        
        heat_c = heat_client.Client(heat_url,
                                    token=keystone_c.auth_token)


        self.stack_uuid = uuidutils.generate_uuid()

        LOG.debug("proposed stack uuid = %s" % (self.stack_uuid))


        return cmd.SUCCESS

    def undo(self):
        pass
