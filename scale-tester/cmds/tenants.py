import logging
import cmd
import keystoneclient.v2_0.client as keystone_client
import keystoneclient.v2_0.tenants as keystone_tenants

LOG = logging.getLogger("scale_tester")

class CreateTenantsCmd(cmd.Command):

    def __init__(self):
        """
        constructor
        """
        super(cmd.Command,self).__init__()
    
    def init(self):
        print("init") 
    
    def execute(self):
        print("execute")
    
    def done(self):
        print("done")
    
    def undo(self):
        print("undo")

class CreateTenantAndUsers(cmd.Command):
    """
    This command creates a tenant and also creates a specified number 
    of tenant users
    """

    def __init__(self, tenant_name, num_of_users, cmd_context, program):
        """
        constructor
        """
        super(cmd.Command,self).__init__()
        self.name = __name__ 
        self.program = program

        self.tenant_name = tenant_name
        self.num_users = num_of_users
        self.context = cmd_context

    def init(self):
        LOG.debug("init - %s ", self.__class__.__name__)


    def execute(self):
        LOG.debug("execute")
        
        LOG.debug(self.program.context)

        keystone_c = \
        keystone_client.Client(username=self.program.context['openstack_user'],
                               password=self.program.context['openstack_password'],
                               tenant_name='admin',
                               auth_url=self.program.context['openstack_auth_url'])
        
        tenant = keystone_c.tenants.create(tenant_name=self.tenant_name,
                                  description='scale test created',
                                  enabled = True)

        # LOG.debug("Created Tenant : ", tenant)
        LOG.debug(keystone_c.tenants.list())
        
        keystone_c.tenants.delete(tenant)
        

    def done(self):
        LOG.debug("done")

class CreateTenantCmd(cmd.Command):
    """
    This class represents the logic to create a single OpenStack tenant
    """
    def __init__(self):
        """
        constructor
        """
        super(cmd.Command,self).__init__()
    
    def init(self):
        print("init") 
    
    def execute(self):
        print("execute")
    
    def done(self):
        print("done")
    
    def undo(self):
        print("undo")

class CreateUserCmd(cmd.Command):
    """
    This class represents the logic to create a single OpenStack User
    """
    def __init__(self):
        """
        constructor
        """
        super(cmd.Command,self).__init__()
    
    def init(self):
        print("init") 
    
    def execute(self):
        print("execute")
    
    def done(self):
        print("done")
    
    def undo(self):
        print("undo")
