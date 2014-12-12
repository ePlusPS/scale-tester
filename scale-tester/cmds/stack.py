# placeholder for heatclient related with commands

import cmd
import pprint
import logging
import heatclient.v1.client as heat_client
import heatclient.openstack.common.uuidutils as uuidutils
import yaml
import pudb

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
        self.input = {}
        # output key-value pairs for the template output parameters
        self.output = [] 
    
    def generate_heat_create_req(self,stack_name):
        """
        Returns a dictionary compliant with the kwargs keys
        for heat.stacks.create()
        """
        params = {}
        params['disable_rollback'] = False
        params['environment'] = {}
        params['files']={}
        params['parameters']= {'image_id': \
                                self.input['image_id'],
                               'public_net': self.input['public_net']
                              }

        params['stack_name']=stack_name

        heat_template_stream = open(self.input['heat_hot_file'])
        heat_template_dict = yaml.load(heat_template_stream)

        params['template'] = heat_template_dict 

        # parse heat_template dictionary and note down output params
        if ('outputs' in heat_template_dict):
            output_dict = heat_template_dict['outputs']

            for key in output_dict:
                self.output.append(key)

            LOG.debug("output params parsed from heat template")
            LOG.debug(pprint.pformat(self.output))

        return params

class CreateStacksCmd(cmd.Command):
    """
    This is a factory cmd that walks resource data structures (tenants and
    users) and creates invidual CreateStackCmd for each tenant. 
    """
    
    def __init__(self, cmd_context, program):
        super(cmd.Command,self).__init__()
        self.context = cmd_context
        self.program = program

    def init(self):
        if ("program.resources" in self.program.context):
            return cmd.SUCCESS
        else:
            return cmd.FAILURE_HALT
        
        # make sure that self.program.context['program_runner'] exists
        return cmd.SUCCESS

    def execute(self):
        """
        This method walks the program resources object.  For each
        tenant, create and enqueue (in the program_runner) a CreateStackCmd
        object.
        """

        all_stacks = []
        self.program.context["all_stacks"] = all_stacks

        resources = self.program.context['program.resources']
        LOG.debug("Walking resources") 
        if (resources is not None):
            for tenant_id in resources.tenants:
                LOG.debug(pprint.pformat(resources.tenants[tenant_id]))
                tenant = resources.tenants[tenant_id]

                if (tenant_id in resources.tenant_users and \
                    len(resources.tenant_users[tenant_id]) > 0):

                    LOG.debug(pprint.pformat(resources.tenant_users[tenant_id][0]))
                    a_user = resources.tenant_users[tenant_id][0]
                    
                    # create child commands for creating individual stacks
                    create_stack_cmd_obj = \
                        create_stack_cmd(tenant,a_user, self.context,self.program)

                    all_stacks.append(create_stack_cmd_obj)

                    program_runner = self.program.context['program_runner']
                    program_runner.execution_queue.append(create_stack_cmd_obj)
                    msg = "enqueued CreateStackCmd for tenant:%s, user:%s in \
                           program_runner execution_queue" % \
                           (tenant.name,a_user.name)
                    LOG.debug(msg)

        return cmd.SUCCESS

    def undo(self):
        return cmd.SUCCESS

def create_stack_cmd(tenant, user, parent_cmd_context, program):
    """
    Factory function for instantiating CreateStackCmd objects

    Assumes that parent_cmd_context has the following keys set
    * vm_image_id
    * external_network
    * heat_hot_file
    """
    stack_name = "stack-" + tenant.name
    cmd_context = {}
    
    # this should be parametrized
    cmd_context['vm_image_id']      = parent_cmd_context['vm_image_id']
    cmd_context['external_network'] = parent_cmd_context['external_network']
    cmd_context['heat_hot_file']    = parent_cmd_context['heat_hot_file']

    create_stack_cmd_obj = CreateStackCmd(cmd_context,
                                          program,
                                          stack_name=stack_name,
                                          tenant_name=tenant.name,
                                          user_name=user.name)

    return create_stack_cmd_obj
    

class CreateStackCmd(cmd.Command):
    """
    This cmd creates a OpenStack Heat Stack instance
    
    Notable context keys
       'vm_image_id'
       'external_network'
       'heat_hot_file'
    """
    
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
        
        self.stack_name = kwargs['stack_name']
        self.tenant_name = kwargs['tenant_name']
        self.user_name   = kwargs['user_name']
        self.vm_image_id = kwargs['vm_image_id']
        self.external_network = kwargs['external_network']
        self.heat_hot_file = kwargs['heat_hot_file']



    def init(self):
        # precondition, tenant and user exists
        # check that hot file key exists
        LOG.debug("init")
        LOG.debug(pprint.pformat(self.context))
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

        # assumming that we're using heat
        heat_url = self.program.context['openstack_heat_url']
        heat_url = heat_url % (keystone_c.auth_tenant_id)
        
        LOG.debug("heat_url = %s" % (heat_url)) 
        
        heat_c = heat_client.Client(heat_url,
                                    token=keystone_c.auth_token)

        LOG.debug("obtained heat client")
        self.stack_uuid = uuidutils.generate_uuid()
        LOG.debug("proposed stack uuid = %s" % (self.stack_uuid))

        stackReqRsp = StackReqRsp()
        stackReqRsp.input['image_id']=self.vm_image_id
        stackReqRsp.input['public_net']=self.external_network
        stackReqRsp.input['heat_hot_file']=self.heat_hot_file

        heat_req = stackReqRsp.generate_heat_create_req(self.stack_name)
        LOG.debug("heat request dictionary generated")
        LOG.debug(pprint.pformat(heat_req))

        """
        resp = heat_c.stacks.create(**heat_req)
       
        # process out-parameters and update Resource tracking dictionaries

        """


        return cmd.SUCCESS

    def undo(self):
        """
        When invoked, will delete the stack created by this command
        """
        return cmd.SUCCESS
