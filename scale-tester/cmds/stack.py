# placeholder for heatclient related with commands

import cmd
import pprint
import logging
import heatclient.v1.client as heat_client
import keystoneclient.v2_0.client as keystone_client
import heatclient.openstack.common.uuidutils as uuidutils
import yaml
import pudb
import time

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
                               'public_net': self.input['public_net'],
                               'public_net_id':self.input['public_net_id']
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
        super(CreateStacksCmd,self).__init__()
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

    create_stack_cmd_obj = CreateStackCmd(cmd_context,
                                          program,
                                          stack_name=stack_name,
                                          tenant_name=tenant.name,
                                          user_name=user.name,
                                          vm_image_id=parent_cmd_context['vm_image_id'],
                                          external_network=parent_cmd_context['external_network'],
                                          external_network_id=parent_cmd_context['external_network_id'],
                                          heat_hot_file=parent_cmd_context['heat_hot_file'])

    LOG.info("CreateStackCmd obj for stack %s, tenant %s, user %s instantiated" % \
              (stack_name, tenant.name, user.name))
    return create_stack_cmd_obj
    

class UndoStackWaitCmd(cmd.Command):
    def __init__(self, cmd_context, program, **kwargs):
        super(UndoStackWaitCmd,self).__init__()

    def init(self):
        # precondition, tenant and user exists
        # check that hot file key exists
        LOG.debug("init")
        LOG.debug(pprint.pformat(self.context))
        return cmd.SUCCESS
    
    def execute(self):
        return cmd.SUCCESS

    def undo(self):
        LOG.info("sleeping for 45s...")
        time.sleep(45)
        LOG.info("stack undo-phase sleep done")
        return cmd.SUCCESS
                
    

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
        super(CreateStackCmd,self).__init__()
        self.context = cmd_context
        self.program = program
        
        self.stack_id = ""
        self.stack_name = kwargs['stack_name']
        self.tenant_name = kwargs['tenant_name']
        self.user_name   = kwargs['user_name']
        self.vm_image_id = kwargs['vm_image_id']
        self.external_network = kwargs['external_network']
        self.external_network_id = kwargs['external_network_id']
        self.heat_hot_file = kwargs['heat_hot_file']
        
        # keystone client session for the tenant / tenant-user
        self.tenant_keystone_c = None
        self.tenant_heat_c = None
        self.rollback_started = False

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
        
        openstack_conf = self.program.context["openstack_conf"]

        self.tenant_keystone_c = \
         cmd.get_keystone_client_for_tenant_user(tenant_name=self.tenant_name,
                                  user_name=self.user_name,
                                  password=self.user_name,
                                  auth_url=\
                                  openstack_conf["openstack_auth_url"])

        # assumming that we're using heat
        heat_url = openstack_conf['openstack_heat_url']
        heat_url = heat_url % (self.tenant_keystone_c.auth_tenant_id)
        
        LOG.debug("heat_url = %s" % (heat_url)) 
        
        self.tenant_heat_c = heat_client.Client(heat_url,
                                    token=self.tenant_keystone_c.auth_token)

        LOG.debug("obtained heat client")
        self.stack_uuid = uuidutils.generate_uuid()
        LOG.debug("proposed stack uuid = %s" % (self.stack_uuid))

        stackReqRsp = StackReqRsp()
        stackReqRsp.input['image_id']=self.vm_image_id
        stackReqRsp.input['public_net']=self.external_network
        stackReqRsp.input['public_net_id']=self.external_network_id
        stackReqRsp.input['heat_hot_file']=self.heat_hot_file

        heat_req = stackReqRsp.generate_heat_create_req(self.stack_name)
        LOG.debug("heat request dictionary generated")
        LOG.debug(pprint.pformat(heat_req))

        resp = self.tenant_heat_c.stacks.create(**heat_req)

        stack_response = resp['stack']
        self.stack_id = stack_response['id']
        
        LOG.info("Stack: %s, tenant: %s, user %s executed" % \
              (self.stack_name, self.tenant_name, self.user_name))

        #LOG.info("Sleeping before going to next command")
        #time.sleep(10)
        
        # Poll for stack status, proceed when stack create is finished
        LOG.info("Polling stack status for 180s...")
        time_limit = 180
        start_time = time.time()
        cur_time = time.time()
        while cur_time - start_time < time_limit:
            cur_time = time.time()
            stack_status = self._get_stack(self.tenant_heat_c, self.stack_name)
            if stack_status is None:
                LOG.error("Stack for stack_cmd %s not found, will abort test" % self.stack_name)
                self.program.failed = True
                self.rollback_started = True

            if(stack_status.stack_status == "ROLLBACK_IN_PROGRESS"):
                LOG.error("Stack for stack_cmd %s doing rollback, will abort test" % self.stack_name)
                self.program.failed = True
                self.rollback_started = True
                
            if(stack_status.stack_status == "ROLLBACK_FAILED"):
                LOG.error("Stack rollback failed for stack_cmd %s" % self.stack_name)
                self.program.failed = True
                break

            if self.rollback_started is True:
                break

            if(stack_status.stack_status == "CREATE_COMPLETE"):
                break
        
        if cur_time - start_time > time_limit:
            LOG.error("Could not create stack within 180s, aborting test")
            self.program.failed = True

        return cmd.SUCCESS

    def undo(self):
        """
        When invoked, will delete the stack created by this command
        """
        if self.rollback_started is True:
            LOG.info("rollback already started for stack %s,%s, skip undo" % (self.stack_name,
                                                                              self.stack_id))
            return cmd.SUCCESS

        LOG.debug("undo")
        
        openstack_conf = self.program.context["openstack_conf"]

        #keystone_c = self.get_keystone_client(self.program)
        
        #keystone_c = \
        #             keystone_client.Client(username=openstack_conf['openstack_user'],
        #                                    password=openstack_conf['openstack_password'],
        #                                    tenant_name=openstack_conf['openstack_project'],
        #                                    auth_url=openstack_conf['openstack_auth_url'])
        keystone_c = cmd.get_keystone_client_for_tenant_user(tenant_name=self.tenant_name,
                                                             user_name=self.user_name,
                                                             password=self.user_name,
                                                             auth_url=openstack_conf["openstack_auth_url"])
        # assumming that we're using heat
        heat_url = openstack_conf['openstack_heat_url']
        heat_url = heat_url % (keystone_c.auth_tenant_id)
        
        LOG.debug("heat_url = %s" % (heat_url)) 
        
        heat_c = heat_client.Client(heat_url,
                                    token=keystone_c.auth_token)
        
        self.tenant_heat_c = heat_c
        
	
        if (self.tenant_heat_c is not None):
            try:
                self.tenant_heat_c.stacks.delete(self.stack_id)
                LOG.info("tenant stack (id=%s) deleted" % (self.stack_id))
            except Exception:
                LOG.error("Exception while deleting stack %s" % self.stack_id)
        
        #LOG.info("sleeping for 45s...")
        #time.sleep(45)
        #LOG.info("stack undo-phase sleep done")
        
        return cmd.SUCCESS



    def _get_stack(self, heat_session, stack_name):
        filter = {"name": stack_name}
        stack_list = heat_session.stacks.list(filters=filter)
        for stack_item in stack_list:
            LOG.debug("stack status: %s" % stack_item)
            LOG.debug("   stack_id: %s" % stack_item.id)
            stack_id = stack_item.id
            return stack_item
