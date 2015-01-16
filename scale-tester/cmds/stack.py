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
import re

LOG = logging.getLogger("scale_tester")
TENANT_NAME_REGEX = "tenant-test-.*"
MAX_FAILED_STACK_UPDATES = 5

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
    
    def generate_heat_update_req(self,use_existing_params=False):
        """
        returns a dicitionary compliant with kwargs keys for
        heat.stacks.update()

        fields = {
            'stack_id': args.id,
            'parameters': utils.format_parameters(args.parameters),
            'existing': args.existing, <--- if true, reuse existing parameters applied to stack
            'template': template,
            'files': dict(list(tpl_files.items()) + list(env_files.items())), <--- environment file
            'environment': env
        }
        """
        params = {}

        if (use_existing_params):
            params['existing'] = use_existing_params 
        else:
            params['parameters']= {'image_id': \
                                    self.input['image_id'],
                                   'public_net': self.input['public_net'],
                                   'public_net_id':self.input['public_net_id']
                                  }
        params['environment'] = {}
        params['files']={}
        
        # updated heat template file
        heat_template_stream = open(self.input['heat_hot_file'])
        heat_template_dict = yaml.load(heat_template_stream)

        params['template'] = heat_template_dict 
       
        return params

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

def _get_stack(heat_session, stack_name, filter_attribute="name"):
    # filter = {"name": stack_name}
    filter = {filter_attribute: stack_name}
    stack_list = heat_session.stacks.list(filters=filter)
    for stack_item in stack_list:
        LOG.debug("stack status: %s" % stack_item)
        LOG.debug("   stack_id: %s" % stack_item.id)
        return stack_item

class GetStacksCmd(cmd.Command):
    """
    Get list of existing stacks instead of creating new ones
    """

    def __init__(self, cmd_context, program):
        super(GetStacksCmd,self).__init__()
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
        openstack_conf = self.program.context["openstack_conf"]
        auth_url = openstack_conf["openstack_auth_url"]
        heat_url = openstack_conf['openstack_heat_url']

        resources = self.program.context['program.resources']
        tenants_stacks_dict = resources.tenants_stacks

        admin_keystone_c = cmd.get_keystone_client(self.program)
        tenant_list = admin_keystone_c.tenants.list()

        for tenant in tenant_list:

            if re.match(TENANT_NAME_REGEX,tenant.name) != None:
                LOG.info("GET TENANT: %s" % (tenant))

                user_list = admin_keystone_c.tenants.list_users(tenant)
                username = None
                target_user = None
                for user in user_list:
                    if user.name != "admin":
                        LOG.info("    GET USER: %s" % (user))
                        username = user.name
                        target_user = user

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

                tenant.stack_list = stack_list
                tenant.target_user = target_user
                tenants_stacks_dict[tenant.name] = tenant
                
        
        return cmd.SUCCESS

    def undo(self):
        return cmd.SUCCESS
        

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
        #LOG.info("sleeping for 45s...")
        #time.sleep(45)
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
        if self.program.failed:
            self.rollback_started = True
            return cmd.SUCCESS
        
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
        time_limit = 180
        start_time = time.time()
        cur_time = time.time()
        LOG.info("Polling stack status for %ds ..." % time_limit)
        while cur_time - start_time < time_limit:
            time.sleep(5)
            cur_time = time.time()
            stack_status = self._get_stack(self.tenant_heat_c, self.stack_name)
            if stack_status is None:
                LOG.info("For tenant %s, Stack for stack_cmd %s not found, \
                will abort test" % (self.tenant_name,self.stack_name))
                self.program.failed = True
                self.rollback_started = True

            if(stack_status.stack_status == "ROLLBACK_IN_PROGRESS"):
                LOG.info("For tenant %s, Stack for stack_cmd %s doing \
                rollback, will abort test" % (self.tenant_name, self.stack_name))
                self.program.failed = True
                self.rollback_started = True
                
            if(stack_status.stack_status == "ROLLBACK_FAILED"):
                LOG.info("For tenant %s, Stack rollback failed for \
                stack_cmd %s" % (self.tenant_name,self.stack_name))
                self.program.failed = True
                break

            if self.rollback_started is True:
                break

            if(stack_status.stack_status == "CREATE_COMPLETE"):
                LOG.info("Tenant %s stack %s completed in %d seconds" % \
                          (self.tenant_name, self.stack_name,
                          (cur_time - start_time)))
                break
        
        if cur_time - start_time > time_limit:
            LOG.error("Could not create stack within %ds, aborting test" %
                      (time_limit))

            self.program.failed = True

        return cmd.SUCCESS

    def undo(self):
        """
        When invoked, will delete the stack created by this command
        """

        return cmd.SUCCESS
        # disabled for now
        # use -d option instead
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

class UpdateStacksCmd(cmd.Command):
    """
    This command will iterate through all the tenant stacks 
    and create tenant specific update stack cmds
    """

    def __init__(self,cmd_context,program, **kwargs):
        """
        constructor
        """
        super(UpdateStacksCmd,self).__init__()
        self.context = cmd_context
        self.program = program
    
    def init(self):
        """
        Check for command precondition state
        """
        if ("program.resources" in self.program.context):
            return cmd.SUCCESS
        else:
            return cmd.FAILURE_HALT
    
    def execute(self):
        resources = self.program.context['program.resources']
        tenants_stacks_dict = resources.tenants_stacks
        
        program_runner = self.program.context['program_runner']

        # set a global counter that will track the number of stack update
        # failures
        self.program.context['update_stacks_failures'] = 0

        for tenant_name in tenants_stacks_dict:
            tenant = tenants_stacks_dict[tenant_name]

            tenant_user = tenant.target_user
            for tenant_stack in tenant.stack_list:
                LOG.debug("Preparing to update tenant %s, stack %s" % \
                          (tenant_name,tenant_stack.stack_name))
                kwargs = {
                    'stack_id':tenant_stack.id,
                    'tenant_name':tenant_name,
                    'user_name':tenant.target_user.username,
                    'vm_image_id':self.context['vm_image_id'],
                    'external_network':self.context['external_network'],
                    'external_network_id':self.context['external_network_id'],
                    'heat_hot_file': self.context['heat_hot_file']
                }
                update_stack_cmd = UpdateStackCmd({},self.program,**kwargs)
                program_runner.execution_queue.append(update_stack_cmd)
        
        return cmd.SUCCESS

    def undo(self):
        """
        """
        pass

class UpdateStackCmd(cmd.Command):
    """
    This class is encapsulates the functionality for updating the stack
    for a given tenant, user
    Notable context keys
        'vm_image_id'
        'external_network'
        'heat_hot_file' <--- path to update heat template file
    """
    
    def __init__(self,cmd_context,program, **kwargs):
        """
        constructor
        kwargs - 'stack_id',
                 'tenant_name',
                 'user_name'
                 'vm_image_id'
                 'external_network'
                 'external_network_id'
                 'heat_hot_file' <--- This is the updated hot template file
        """
        super(UpdateStackCmd,self).__init__()
        self.context = cmd_context
        self.program = program
        
        # existing stack_id
        self.stack_id = kwargs['stack_id'] 
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
        LOG.debug("init")
        LOG.debug(pprint.pformat(self.context))
        return cmd.SUCCESS
    
    def execute(self):
        
        # skip if program has already failed
        if self.program.failed:
            LOG.error("Not executing update stack for tenant %s, user %s, \
             stack %s" % (self.tenant_name,self.user_name,self.stack_id))
            return cmd.SUCCESS
        else: 
            # login for tenant, user
            openstack_conf = self.program.context["openstack_conf"]

            self.tenant_keystone_c = \
                cmd.get_keystone_client_for_tenant_user(
                                              tenant_name=self.tenant_name,
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

            stackReqRsp = StackReqRsp()
            # template parameters - perhaps not needed if existing paramter values
            # are used
            stackReqRsp.input['image_id']=self.vm_image_id
            stackReqRsp.input['public_net']=self.external_network
            stackReqRsp.input['public_net_id']=self.external_network_id
            stackReqRsp.input['heat_hot_file']=self.heat_hot_file

            heat_update_req = \
                stackReqRsp.generate_heat_update_req(use_existing_params=False)
            LOG.debug("heat update request dictionary generated")
            LOG.debug(pprint.pformat(heat_update_req))
            self.tenant_heat_c.stacks.update(self.stack_id, **heat_update_req)

            LOG.info("Updated stack for tenant %s, stack id %s" % \
                     (self.tenant_name, self.stack_id))
            
            # wait for stack update to complete
            # refactor this section so that the timer part is common for
            # both stack create and update
            LOG.info("Polling stack status for 180s...")
            time_limit = 360
            start_time = time.time()
            cur_time = time.time()
            
            while cur_time - start_time < time_limit:
                time.sleep(5)
                cur_time = time.time()
                stack_status = _get_stack(self.tenant_heat_c,
                                          self.stack_id,
                                          filter_attribute="id")
            
                if stack_status is None:
                    LOG.info("For tenant %s, Stack for stack_cmd %s not found, \
                    will abort test" % (self.tenant_name,self.stack_name))
                    self.program.failed = True
                    self.rollback_started = True

                if(stack_status.stack_status == "ROLLBACK_IN_PROGRESS"):
                    LOG.info("For tenant %s, Stack for stack_cmd %s doing \
                    rollback, will abort test" % (self.tenant_name, self.stack_name))
                    self.program.failed = True
                    self.rollback_started = True
                
                if(stack_status.stack_status == "ROLLBACK_FAILED"):
                    LOG.info("For tenant %s, Stack rollback failed for \
                    stack_cmd %s" % (self.tenant_name,self.stack_name))
                    self.program.failed = True
                    break

                if self.rollback_started is True:
                    break

                if(stack_status.stack_status == "UPDATE_COMPLETE"):
                    LOG.info("Tenant %s stack id %s completed in %d seconds" % \
                              (self.tenant_name, self.stack_id,
                              (cur_time - start_time)))
                    break
        
            if cur_time - start_time > time_limit:
                LOG.error("Could not create stack within %ds, aborting test" % \
                           (time_limit))
                
                num_failures = self.program.context['update_stacks_failures']
                num_failures = num_failures + 1
                self.program.context['update_stacks_failures'] = num_failures

                if (num_failures > MAX_FAILED_STACK_UPDATES):
                    self.program.failed = True
    
            return cmd.SUCCESS

    def undo(self):
        """
        undo implementation
        """
        # use -d option to wipe allocated resources
        return cmd.SUCCESS
