import logging
import paramiko
import neutronclient.v2_0.client as neutron_client
import pprint
import cmd

LOG = logging.getLogger("scale_tester")


class TrafficLauncherCommand(cmd.Command):
    """
    This command triggers a ping from a VM to a destination IP.
    """

    def __init__(self, cmd_context, program, **kwargs):
        """
        constructor
        """
        super(cmd.Command,self).__init__()
        self.name = __name__ 
        self.program = program
        self.cmd_context = cmd_context


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

                    stack_name = "stack-" + tenant.name
                    intra_ping_cmd_obj = IntraTenantPingTestCommand(self.cmd_context,
                                                                    self.program,
                                                                    stack_name=stack_name,
                                                                    tenant_name=tenant.name,
                                                                    user_name=a_user.name,
                                                                    password=a_user.password)

                    program_runner = self.program.context['program_runner']
                    program_runner.execution_queue.append(intra_ping_cmd_obj)
                    msg = "enqueued IntraTenantPingTestCommand for tenant:%s, user:%s in \
                           program_runner execution_queue" % \
                           (tenant.name,a_user.name)
                    LOG.debug(msg)
        
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


class IntraTenantPingTestCommand(cmd.Command):

    def __init__(self, cmd_context, program, **kwargs):
        """
        constructor
        """
        super(cmd.Command,self).__init__()
        self.name = __name__ 
        self.program = program

        self.stack_name = kwargs['stack_name']
        self.tenant_name = kwargs['tenant_name']
        self.user_name   = kwargs['user_name']
        self.password = kwargs['password']

        self.results_dict = {}


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

        auth_url = self.program.context["openstack_auth_url"]

        neutron_session = neutron_client.Client(auth_url=auth_url,
                                                username=self.user_name,
                                                password=self.password,
                                                tenant_name=self.tenant_name)

        tenant_fixed_ips = []
        tenant_floating_ips = []
        tenant_floating_ip_objs = neutron_session.list_floatingips()
        tenant_floating_ip_objs = tenant_floating_ip_objs['floatingips']

        for fip_dict in tenant_floating_ip_objs:
            tenant_fixed_ips.append(fip_dict['fixed_ip_address'])
            tenant_floating_ips.append(fip_dict['floating_ip_address'])
            LOG.debug("tenant: %s, floating ip dict: %s" % (self.tenant_name, fip_dict))
    
        # do all to all ping within tenant
        for src_ip in tenant_floating_ips:
            self.results_dict[src_ip] = {}

            for dst_ip in tenant_fixed_ips:
                result = self._trigger_ping(src_ip, dst_ip)
                self.results_dict[src_ip][dst_ip] = result

        for src_ip, results in self.results_dict.items():
            LOG.debug("Ping Result,  src_ip: %s,  results: %s" % (src_ip, results))
        
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


    def _trigger_ping(self, source_vm_ip, dst_ip, count=10, interval=1):

        # make source_vm an object later, just use it as src_ip for now
        # src_ip = source_vm['ip']
        src_ip = source_vm_ip

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(hostname=src_ip,
                    port=22,
                    username="cirros",
                    password="cubswin:)")

        cmd_str = "ping -c %s %s" % (count, dst_ip)
        LOG.debug("running command: %s" % (cmd_str))

        sin, sout, serr = ssh.exec_command(cmd_str)
        rc = sout.channel.recv_exit_status()

        LOG.debug("ping rc: %s" % rc)
        LOG.debug("ping output:\n")
        for line in sout.readlines():
            LOG.debug("  %s" % line)

        ssh.close()

        return {"rc": rc,
                "stdout": sout}


def main():
    ping_tester = TrafficLauncherCommand(None)
    ping_tester._trigger_ping("7.1.1.46", "7.1.1.1")
    
if __name__ == "__main__":
    main()
        
        

        
        
