
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

    # ideally, the actual creation of the keystone client should only 
    # done once.
    
    openstack_conf = program.context["openstack_conf"]

    keystone_c = \
      keystone_client.Client(username=openstack_conf['openstack_user'],
                             password=openstack_conf['openstack_password'],
                             tenant_name=openstack_conf['openstack_project'],
                             auth_url=openstack_conf['openstack_auth_url'])
    
    LOG.debug("obtained keystone client")
    return keystone_c


def get_keystone_client_for_tenant_user(tenant_name, user_name, password, auth_url):
    """
    Using generalized credentials, obtain a keystone client
    """
    keystone_c = \
        keystone_client.Client(username=user_name,
                             password=password,
                             tenant_name=tenant_name,
                             auth_url=auth_url)
    
    LOG.debug("obtained keystone client for tenant %s, user %s" % 
             (tenant_name, user_name))

    return keystone_c


class Command(object):
    """
    This class represents an abstract Command
    """
    
    def __init__(self,name=None, program=None):
        self.context = {}
        self.name = name
        self.program = program
        self.threaded = False

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
    
    def get_result():
        """
        If implemented, returns a success/fail status code 
        for the command
        """
        return SUCCESS

    def get_result_detail():
        """
        Returns a string describing the results for a command
        """
        pass
