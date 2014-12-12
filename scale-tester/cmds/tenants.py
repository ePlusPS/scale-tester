import logging
import cmd
import program
import keystoneclient.v2_0.client as keystone_client
import keystoneclient.v2_0.tenants as keystone_tenants
import pprint
import pudb

LOG = logging.getLogger("scale_tester")

Test_Tenant_Prefix = "test-tenant-%d"

class CreateTenantsCmd(cmd.Command):
    """
    This command is responsible for inspecting the scale test input parameters
    and generating the subsequent CreateTenantAndUsers command
    """
    def __init__(self,cmd_context, program):
        """
        constructor
        """
        super(cmd.Command,self).__init__()
        self.context = cmd_context
        self.program = program
    
    def init(self):
        """
        check that the preconditions are met
        """
        # obtain program context
        LOG.debug("init") 

        global_test_params = self.program.context["global_test_parameters"]

        if ("num_of_tenants" in global_test_params and
            "num_users_per_tenant" in global_test_params and
            "program_runner" in self.program.context):
            return cmd.SUCCESS
        else:
            return cmd.FAILURE
    
    def execute(self):
        # create the resource tracker
        if ("program.resources" not in self.program.context):
            resources = program.Resources()
            self.program.context['program.resources'] = resources

        global_test_params = self.program.context["global_test_parameters"]

        num_tenants = global_test_params['num_of_tenants']
        num_users_per_tenant = global_test_params['num_users_per_tenant']

        LOG.debug("execute, num_tenants=%d, num_users_per_tenant=%d" % \
                  (num_tenants, num_users_per_tenant))
        
        program_runner = self.program.context['program_runner']

        for x in xrange(0,num_tenants):
            """
            create tenant commands
            Each tenant will be named "Test_Tenant_Prefix + index"
            """
            cmd_context = {}
            tenant_name = Test_Tenant_Prefix % (x)
            createTenantAndUsersCmd = CreateTenantAndUsers(cmd_context,
                                                           self.program,
                                                           tenant_name=tenant_name,
                                                           num_users=num_users_per_tenant)
            
            program_runner.enqueue_command(createTenantAndUsersCmd)
            
            
    def done(self):
        LOG.debug("done")
    
    def undo(self):
        """
        Actual work is performed in child CreateTenantAndUsers cmd
        """
        LOG.debug("undo")

class CreateTenantAndUsers(cmd.Command):
    """
    This command creates a tenant and also creates a specified number 
    of tenant users
    """

    def __init__(self, cmd_context, program, **kwargs):
        """
        constructor
        kwargs: 'tenant_name', 'num_users'
        """
        super(cmd.Command,self).__init__()
        self.name = __name__ 
        self.context = cmd_context
        self.program = program

        self.tenant_name = kwargs['tenant_name']
        self.num_users = kwargs['num_users']

        self.created_tenant = None
        self.created_users = []

    def init(self):
        LOG.debug("init - %s ", self.__class__.__name__)

        # any precondition logic that should prevent the command from being 
        # executed should be coded here
        if ("program.resources" in self.program.context): 
            return cmd.SUCCESS
        else:
            return cmd.FAILURE


    def execute(self):
        """
        When this command is executed, if successful, it will modify the
        program's context.  Specifically the Resources object keyed at 
        "program.resources".
        """

        LOG.debug("execute")
        LOG.debug(pprint.pformat(self.program.context))
        
        # obtain handle to program context/program resources
        program_resources = self.program.context["program.resources"]
        
        keystone_c = cmd.get_keystone_client(self.program)

        self.created_tenant = \
                        keystone_c.tenants.create(tenant_name=self.tenant_name,
                        description='scale test created',
                        enabled = True)
        

        program_resources.add_tenant(self.created_tenant)

        for i in xrange(0,self.num_users):
            new_user_name = "%s-%d" % (self.tenant_name,i)

            created_user = keystone_c.users.create(name=new_user_name,
                                        password=new_user_name,
                                        email=None,
                                        tenant_id=self.created_tenant.id,
                                        enabled=True)
            # what about the user role?
            LOG.debug("created tenant user %s" % (new_user_name))
            program_resources.add_user(created_user)
            self.created_users.append(created_user)

        return cmd.SUCCESS

    def done(self):
        LOG.debug("done")
        return cmd.SUCCESS

    def undo(self):
        """
        When invoked, will attempt to delete the tenant and associated users
        created by this command
        """
        LOG.debug("undo")
        
        # should just access some singleton for keystone
        keystone_c = \
            cmd.get_keystone_client(self.program)

        if (self.created_tenant is not None):
            keystone_c.tenants.delete(self.created_tenant)

        for user in self.created_users:
            LOG.debug("deleting %s",str(user))
            keystone_c.users.delete(user)

        return cmd.SUCCESS
