import logging
import cmd
import keystoneclient.v2_0.client as keystone_client
import keystoneclient.v2_0.tenants as keystone_tenants
import pprint

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

        self.created_tenant = None
        self.created_users = []

    def init(self):
        LOG.debug("init - %s ", self.__class__.__name__)
        # any precondition logic that should prevent the command from being 
        # executed should be coded here


    def execute(self):
        LOG.debug("execute")
        
        LOG.debug(pprint.pformat(self.program.context))

        keystone_c = \
        keystone_client.Client(username=self.program.context['openstack_user'],
                               password=self.program.context['openstack_password'],
                               tenant_name='admin',
                               auth_url=self.program.context['openstack_auth_url'])
        
        self.created_tenant = keystone_c.tenants.create(tenant_name=self.tenant_name,
                                  description='scale test created',
                                  enabled = True)

        # LOG.debug("Created Tenant : ", tenant)

        LOG.debug(pprint.pformat(keystone_c.tenants.list()))

        for i in xrange(0,self.num_users):
            new_user_name = "%s-%d" % (self.tenant_name,i)

            LOG.debug("creating tenant user %s" % (new_user_name))

            self.created_users.append(keystone_c.users.create(name=new_user_name,
                                                              password=new_user_name,
                                                              email=None,
                                                              tenant_id=self.created_tenant.id,
                                                              enabled=True))

              

    def done(self):
        LOG.debug("done")

    def undo(self):
        """
        When invoked, will attempt to delete the tenant and associated users
        created by this command
        """
        LOG.debug("undo")
        
        # should just access some singleton for keystone
        keystone_c = \
        keystone_client.Client(username=self.program.context['openstack_user'],
                               password=self.program.context['openstack_password'],
                               tenant_name='admin',
                               auth_url=self.program.context['openstack_auth_url']) 

        if (self.created_tenant is not None):
            keystone_c.tenants.delete(self.created_tenant)

        for user in self.created_users:
            LOG.debug("deleting %s",str(user))
            keystone_c.users.delete(user)



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
