
import keystoneclient.v2_0.client as keystone_client
import logging

# Return codes for commands
SUCCESS = 0

# Cmd failed, halt the program
FAILURE = 1
# Command failed, stop further command execution
FAILURE_HALT = 2
# Command failed, but continue onto the next cmd
FAILURE_CONTINUE = 3

LOG = logging.getLogger("scale_tester")

def get_keystone_client(program):
    """
    Using the program context, connect and obtain the
    keystone client/token
    """
    keystone_c = \
      keystone_client.Client(username=program.context['openstack_user'],
                             password=program.context['openstack_password'],
                             tenant_name=program.context['openstack_project'],
                             auth_url=program.context['openstack_auth_url'])
    
    LOG.debug("obtained keystone client")
    return keystone_c


class Command(object):
    """
    This class represents an abstract Command
    """
    
    def __init__(self,name=None, program=None):
        self.context = {}
        self.name = name
        self.program = program 

    def init(self):
        """
        The init allows a Command to check whether the preconditions
        to execute are met.
        """
        pass
    
    def execute(self):
        """
        The execute method implements the Command
        """
        pass

    def done(self):
        """
        The done method can be used as a placeholder to invoke any sort
        post-processing logic when the command has finished.
        """
        pass
    
    def undo(self):
        """
        If implemented, undo provides a mechanism by which the results of
        a command are roll-back
        """
        pass
