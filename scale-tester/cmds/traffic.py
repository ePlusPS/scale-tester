import logging
import paramiko

import cmd

LOG = logging.getLogger("scale_tester")


class PingTestCommand(cmd.Command):
    """
    This command triggers a ping from a VM to a destination IP.
    """

    def __init__(self, program):
        """
        constructor
        """
        super(cmd.Command,self).__init__()
        self.name = __name__ 
        self.program = program


    def init(self):
        LOG.debug("init - %s ", self.__class__.__name__)
        # any precondition logic that should prevent the command from being 
        # executed should be coded here
        return cmd.SUCCESS


    def execute(self):
        """
        When this command is executed, it will run a ping command on a VM, targeting the dest IP.

        """
        LOG.debug("execute")
        
        #LOG.debug(pprint.pformat(self.program.context))
        
        # obtain handle to program context/program resources
        #program_resources = self.program.context["program.resources"]
        
        return cmd.SUCCESS

    def done(self):
        LOG.debug("done")
        return cmd.SUCCESS

    def undo(self):
        """
        Ping has no undo actions
        """
        LOG.debug("undo")

        return cmd.SUCCESS


    def _trigger_ping(self, source_vm, dst_ip, count=10, interval=1):

        # make source_vm an object later, just use it as src_ip for now
        # src_ip = source_vm['ip']
        src_ip = source_vm

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(hostname=src_ip,
                    port=22,
                    username="cirros",
                    password="cubswin:)")

        #chan = ssh.get_transport().open_session()
        #chan.get_pty()
        #chan.invoke_shell()
        
        cmd_str = "ping -c %s %s" % (count, dst_ip)
        print("running command: %s" % (cmd_str))

        sin, sout, serr = ssh.exec_command(cmd_str)
        #chan.send(cmd_str)
        #output_str = chan.recv(2048)
        rc = sout.channel.recv_exit_status()

        print("ping rc: %s" % rc)
        print("ping output:\n")
        for line in sout.readlines():
            print("  %s" % line)

        #chan.close()
        ssh.close()


def main():
    ping_tester = PingTestCommand(None)
    ping_tester._trigger_ping("7.1.1.46", "7.1.1.1")
    
if __name__ == "__main__":
    main()
        
        

        
        
