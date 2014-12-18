import logging
import cmd
import program
import keystoneclient.v2_0.client as keystone_client
import keystoneclient.v2_0.tenants as keystone_tenants
import pprint
import pudb

LOG = logging.getLogger("scale_tester")

# Test_Tenant_Prefix = "test-tenant-%d"

class CreateTenantsCmd(cmd.Command):
    """
    This command is responsible for inspecting the scale test input parameters
    and generating the subsequent CreateTenantAndUsers command
    """
    def __init__(self,cmd_context, program):
        """
        constructor
        """
        super(CreateTenantsCmd,self).__init__()
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
        
        tenant_name_prefix = global_test_params['tenant_name_prefix']
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

            # so if tenant_name_prefix == tenant-test, then the tenant_name
            # will be tenant-test-0, tenant-test-1, etc
            tenant_name = "%s-%d" % (tenant_name_prefix,x)
            createTenantAndUsersCmd = CreateTenantAndUsers(cmd_context,
                                                           self.program,
                                                           tenant_name=tenant_name,
                                                           num_users=num_users_per_tenant)
            
            program_runner.enqueue_command(createTenantAndUsersCmd)
            
        return cmd.SUCCESS
            
    def done(self):
        LOG.debug("done")
        return cmd.SUCCESS
    
    def undo(self):
        """
        Actual work is performed in child CreateTenantAndUsers cmd
        """
        LOG.debug("Undo")

def get_keystone_role(keystone_c,role_name="heat_stack_owner"):
    """
    Given a valid keystone client instance, return the heat_stack_owner
    role.  This function allows a role_name to be used to search keystone.
    Normally, keystone.roles.get expects a uuid to be used for retrieving a 
    role which isn't too friendly.  If found, will return the role object 
    for "heat_stack_owner", otherwise None returned
    """
    found_role = None

    if (role_name is not None and
        keystone_c is not None):

        list_of_roles = keystone_c.roles.list()

        for role in list_of_roles:
            if (role.name == role_name):
                found_role = role
                LOG.debug("Found role %s" % (role_name))
                break;

    return found_role

def get_keystone_user(keystone_c, user_name):
    """
    Given a valid keystone client instance, return the user
    object as specified by user_name (string)
    """
    found_user = None

    if (user_name is not None and
        keystone_c is not None):

        list_of_users = keystone_c.users.list()
        
        for user in list_of_users:
            if (user.username == user_name):
                found_user = user
                break

    return found_user

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
        super(CreateTenantAndUsers,self).__init__()
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
        if ("program.resources" in self.program.context and
            "openstack_conf" in self.program.context): 
            return cmd.SUCCESS
        else:
            LOG.info("Preconditions for creating tenant %s were not met" % \
                     (self.tenant_name))
            return cmd.FAILURE_CONTINUE

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
        
        # obtain keystone handle using global context (aka admin account)
        keystone_c = cmd.get_keystone_client(self.program)


        # create the tenant/project
        # perhaps at a later point, randomly create a suffix or prefix to
        # append to a tenant and user name
        self.created_tenant = \
                        keystone_c.tenants.create(tenant_name=self.tenant_name,
                        description='scale test created',
                        enabled = True)
        
        program_resources.add_tenant(self.created_tenant)
        
        openstack_conf = self.program.context["openstack_conf"]

        # associate admin user with newly created tenant project
        admin_user = get_keystone_user(keystone_c,"admin")
        admin_role = get_keystone_role(keystone_c,"admin")
        keystone_c.roles.add_user_role(admin_user,
                                       admin_role,
                                       self.created_tenant)
        
        # retrieve heat_stack_owner role
        heat_stack_owner_role = \
            get_keystone_role(keystone_c, \
                  openstack_conf["openstack_heat_stack_owner_role"])
        
        # create users for the tenant
        for i in xrange(0,self.num_users):
            new_user_name = "%s-%d" % (self.tenant_name,i)

            created_user = keystone_c.users.create(name=new_user_name,
                                        password=new_user_name,
                                        email=None,
                                        tenant_id=self.created_tenant.id,
                                        enabled=True)
            
            # associate role, heat_stack_owner to tenant user
            keystone_c.roles.add_user_role(created_user,
                                           heat_stack_owner_role,
                                           self.created_tenant)

            LOG.debug("created tenant user %s" % (new_user_name))
            program_resources.add_user(created_user)
            self.created_users.append(created_user)
        
        LOG.info("Successfully created tenant %s and users %s" % \
                (self.tenant_name, pprint.pformat(self.created_users)))
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
        """
        keystone_c = \
            cmd.get_keystone_client(self.program)

        if (self.created_tenant is not None):
            keystone_c.tenants.delete(self.created_tenant)
            LOG.info("deleted tenant %s",str(self.created_tenant))

        for user in self.created_users:
            keystone_c.users.delete(user)
            LOG.info("deleted %s",str(user))
        """
        return cmd.SUCCESS
