# placeholder for heatclient related with commands

import cmd
import pprint
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

    def __init__(self):
        self.stack_name = ""
        # input key-value pairs for the template
        self.input_keys = {}
        # output key-value pairs for the template output parameters
        self.output_keys = {}
    
    def generate_heat_create_req(self):
        """
        Returns a dictionary compliant with the kwargs keys
        for heat.stacks.create()
        """
        params = {}
        params['disable_rollback'] = False
        params['environment'] = {}
        params['files']={}
        params['parameters']= {'image_id': \
                                'adc34d8b-d752-4873-8873-0f2563ee8c72',
                               'public_net': 'EXT-NET'
                              }

        params['stack_name']="nh-stack-8"
        params['template'] = ""

        return params

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
    
    def __init__(self, stack_name, tenant_name, user_name, cmd_context, program):
        super(cmd.Command,self).__init__()
        self.stack_name = stack_name
        self.tenant_name = tenant_name
        self.user_name   = user_name

        self.context = cmd_context
        self.program = program

    def init(self):
        # precondition, tenant and user exists
        # check that hot file key exists
        if ('heat_hot_file' in self.context and
            'vm_image_id' in self.context and
            'external_network' in self.context):
            LOG.debug("init-precondition met for CreateStackCmd")
            return cmd.SUCCESS
        else:
            LOG.debug("init-precondition failed for CreateStackCmd")
            LOG.debug(pprint.pformat(self.context))
            return cmd.FAILURE_CONTINUE 

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

        heat_url = self.program.context['openstack_heat_url']
        heat_url = heat_url % (keystone_c.auth_tenant_id)
        
        LOG.debug("heat_url = %s" % (heat_url)) 
        
        heat_c = heat_client.Client(heat_url,
                                    token=keystone_c.auth_token)

        LOG.debug("obtained heat client")
        self.stack_uuid = uuidutils.generate_uuid()
        LOG.debug("proposed stack uuid = %s" % (self.stack_uuid))
        # stackReqRsp = StackReqRsp()

        return cmd.SUCCESS

    def undo(self):
        return cmd.SUCCESS
