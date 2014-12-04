import cmd

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

    def __init__(self, num_of_users, context):
        """
        constructor
        """
        super(cmd.Command,self).__init__()
        self.name = "CreateTenantAndUsers"
        self.num_users = num_of_users
        self.context = context

    def init(self):
        print("init")

    def execute(self):
        print("execute")

    def done(self):
        print("done")

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
