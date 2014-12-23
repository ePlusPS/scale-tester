import logging
import pprint
import cmd
import subprocess
import time
import re
import importlib

import paramiko
import neutronclient.v2_0.client as neutron_client

LOG = logging.getLogger("scale_tester")

DEFAULT_SUB_CMD = "cmds.traffic.IntraTenantPingTestCmd"

MODULE_CLASS_REGEX = "(.+)\.(\w+)"

class TrafficLauncherCmd(cmd.Command):
    """
    This command triggers a ping from a VM to a destination IP.
    """

    def __init__(self, cmd_context, program, **kwargs):
        """
        constructor
        """
        super(TrafficLauncherCmd,self).__init__()
        self.name = __name__ 
        self.program = program
        self.cmd_context = cmd_context


    def init(self):
        LOG.debug("init - %s ", self.__class__.__name__)
        # any precondition logic that should prevent the command from being 
        # executed should be coded here
        return cmd.SUCCESS


    def _get_ips_for_tenant(self, tenant, user):
        # retrieve set of IPs for this tenant

        openstack_conf = self.program.context["openstack_conf"]
        auth_url = openstack_conf["openstack_auth_url"]

        neutron_session = neutron_client.Client(auth_url=auth_url,
                                                username=user.name,
                                                password=user.name,
                                                tenant_name=tenant.name)

        tenant_floating_ip_objs = neutron_session.list_floatingips()
        tenant_floating_ip_objs = tenant_floating_ip_objs['floatingips']

        return tenant_floating_ip_objs

    def execute(self):
        """
        When this command is executed, it will run a ping command on a VM, targeting the dest IP.
        """
        LOG.debug("execute")
        
        #LOG.debug(pprint.pformat(self.program.context))
        
        # obtain handle to program context/program resources
        #program_resources = self.program.context["program.resources"]

        resources = self.program.context['program.resources']

        tenant_ips = {}

        LOG.debug("Walking resources") 
        if (resources is not None):
            for tenant_id in resources.tenants:
                LOG.debug(pprint.pformat(resources.tenants[tenant_id]))
                tenant = resources.tenants[tenant_id]

                if (tenant_id in resources.tenant_users and \
                    len(resources.tenant_users[tenant_id]) > 0):

                    LOG.debug(pprint.pformat(resources.tenant_users[tenant_id][0]))
                    a_user = resources.tenant_users[tenant_id][0]

                    tenant_ips[tenant_id] = self._get_ips_for_tenant(tenant, a_user)

                    stack_name = "stack-" + tenant.name

                    LOG.debug("self.cmd_context: %s, type: %s" % (self.cmd_context,
                                                                  type(self.cmd_context)))

                    if "sub_cmd" in self.cmd_context:
                        sub_cmd = self.cmd_context["sub_cmd"]
                    else:
                        sub_cmd = DEFAULT_SUB_CMD
                    
                    match_results = re.match(MODULE_CLASS_REGEX, sub_cmd)
                    
                    module = importlib.import_module(match_results.group(1))
                    class_obj = getattr(module,match_results.group(2))

                    LOG.debug("module_path=%s" % module)
                    LOG.debug("class name = %s " % class_obj)

                    intra_ping_cmd_obj = class_obj(self.cmd_context,
                                                   self.program,
                                                   stack_name=stack_name,
                                                   tenant_name=tenant.name,
                                                   tenant_id=tenant_id,
                                                   user_name=a_user.name,
                                                   password=a_user.name)

                    program_runner = self.program.context['program_runner']
                    program_runner.execution_queue.append(intra_ping_cmd_obj)
                    msg = "enqueued IntraTenantPingTestCommand for tenant:%s, user:%s in \
                           program_runner execution_queue" % \
                           (tenant.name,a_user.name)
                    LOG.debug(msg)

        resources.tenant_ips = tenant_ips
        
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


class IntraTenantPingTestCmd(cmd.Command):

    def __init__(self, cmd_context, program, **kwargs):
        """
        constructor
        """
        super(cmd.Command,self).__init__()
        self.name = __name__ 
        self.program = program

        self.stack_name = kwargs['stack_name']
        self.tenant_name = kwargs['tenant_name']
        self.tenant_id = kwargs['tenant_id']
        self.user_name   = kwargs['user_name']
        self.password = kwargs['password']

        self.results_dict = {}

        self.threaded = True


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
                
        self._setup_tenant()

        src_ip_list = self._get_src_ip_list()
        dst_ip_list = self._get_dst_ip_list()
        fail_ip_list = []

        pending_session_list = list(src_ip_list)
        session_dict = {}

        LOG.debug("Attempting to create SSH sessions...")
        start_time = time.time()

        while len(pending_session_list) > 0:
            cur_time = time.time()
            time_delta = cur_time - start_time
            
            # allow 8 minutes for VMs to boot
            if time_delta > 480: 
                for vm_ip in pending_session_list:
                    LOG.error("Could not open session to %s, timeout exceeded" % vm_ip)
                    src_ip_list.remove(vm_ip)
                    fail_ip_list.append(vm_ip)
                break
                
            for vm_ip in pending_session_list:
                LOG.debug("Connecting to %s..." % vm_ip)
                ssh_session = self._get_ssh_session(vm_ip)
                if ssh_session:
                    pending_session_list.remove(vm_ip)
                    session_dict[vm_ip] = ssh_session
                    LOG.debug("Connection success")
                else:
                    LOG.debug("Connection failed.")

            if len(pending_session_list) > 0:
                time.sleep(10)
            
        # do all to all ping within tenant
        for src_ip in src_ip_list:
            self.results_dict[src_ip] = {}
            for dst_ip in dst_ip_list:
                ssh_session = session_dict[src_ip]
                rc = self._trigger_ping_async(ssh_session, dst_ip)
                #self.results_dict[src_ip][dst_ip] = result

        # let pings run, wait 25s
        time.sleep(25)

        # retrieve ping results
        for src_ip in src_ip_list:
            self.results_dict[src_ip] = {}
            for dst_ip in dst_ip_list:
                ssh_session = session_dict[src_ip]
                result = self._get_ping_results(ssh_session, dst_ip)
                self.results_dict[src_ip][dst_ip] = result

        for src_ip, results in self.results_dict.items():
            LOG.debug("Ping Result,  src_ip: %s,  results:\n%s" % (src_ip, pprint.pformat(results)))
            ssh_session = session_dict[src_ip]
            ssh_session.close()

        if len(fail_ip_list) > 0:
            LOG.error("Failed IPs: %s" % pprint.pformat(fail_ip_list))
        
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

    def _setup_tenant(self):
        openstack_conf = self.program.context["openstack_conf"]
        auth_url = openstack_conf["openstack_auth_url"]

        neutron_session = neutron_client.Client(auth_url=auth_url,
                                                username=self.user_name,
                                                password=self.password,
                                                tenant_name=self.tenant_name)

        # make default security group allow ICMP and SSH
        security_groups = neutron_session.list_security_groups()
        LOG.debug("security_groups: %s" % security_groups)
        security_groups = security_groups['security_groups']
        for sg in security_groups:
            if sg['name'] == "default":
                sg_id = sg['id']
                LOG.debug("found default secgrp, adding ssh/icmp rules")
                self._add_icmp_ssh_sg_rules(neutron_session, sg_id)        


    def _add_icmp_ssh_sg_rules(self, neutron_session, sg_id):
        icmp_ingress_rule =  {'security_group_rule': 
                              {'remote_group_id': None,
                               'direction': 'ingress', 
                               'remote_ip_prefix': '0.0.0.0/0',
                               'protocol': 'icmp', 
                               #'tenant_id': u'7b2f81c93dec438aa3960dd947043e8f', 
                               'port_range_max': None, 
                               'security_group_id': sg_id, 
                               'port_range_min': None, 
                               'ethertype': 'IPv4'}}

        icmp_egress_rule =  {'security_group_rule': 
                              {'remote_group_id': None,
                               'direction': 'egress', 
                               'remote_ip_prefix': '0.0.0.0/0',
                               'protocol': 'icmp', 
                               #'tenant_id': u'7b2f81c93dec438aa3960dd947043e8f', 
                               'port_range_max': None, 
                               'security_group_id': sg_id, 
                               'port_range_min': None, 
                               'ethertype': 'IPv4'}}

        ssh_rule = {'security_group_rule': 
                    {'remote_group_id': None,
                     'direction': 'ingress',
                     'remote_ip_prefix': '0.0.0.0/0', 
                     'protocol': 'tcp', 
                     #'tenant_id': u'7b2f81c93dec438aa3960dd947043e8f', 
                     'port_range_max': 22, 
                     'security_group_id': sg_id,
                     'port_range_min': 22, 
                     'ethertype': 'IPv4'}}

        neutron_session.create_security_group_rule(icmp_ingress_rule)
        neutron_session.create_security_group_rule(icmp_egress_rule)
        neutron_session.create_security_group_rule(ssh_rule)        

    # not used for now
    def _check_ping_connectivity(self, tenant_floating_ips):
        # check that machines are up before proceeding
        ping_ip_list = list(tenant_floating_ips)
        while len(ping_ip_list) > 0:
            for fip in ping_ip_list:
                try:
                    cmd_str = "ping -c 5 %s" % fip
                    LOG.debug("running command: %s" % cmd_str)
                    subprocess.check_call(cmd_str, shell=True)
                    ping_ip_list.remove(fip)
                    LOG.debug("ping command success")
                except subprocess.CalledProcessError:
                    LOG.debug("ping command failed")
            if len(ping_ip_list) > 0:
                LOG.debug("sleeping for 10s...")
                time.sleep(10)


    def _get_src_ip_list(self):
        resources = self.program.context['program.resources']

        tenant_floating_ip_objs = resources.tenant_ips[self.tenant_id]

        tenant_fixed_ips = []
        tenant_floating_ips = []

        for fip_dict in tenant_floating_ip_objs:
            tenant_fixed_ips.append(fip_dict['fixed_ip_address'])
            tenant_floating_ips.append(fip_dict['floating_ip_address'])
            LOG.debug("tenant: %s, floating ip dict: %s" % (self.tenant_name, fip_dict))

        return tenant_floating_ips

    def _get_dst_ip_list(self):
        resources = self.program.context['program.resources']

        tenant_floating_ip_objs = resources.tenant_ips[self.tenant_id]

        tenant_fixed_ips = []
        tenant_floating_ips = []

        for fip_dict in tenant_floating_ip_objs:
            tenant_fixed_ips.append(fip_dict['fixed_ip_address'])
            tenant_floating_ips.append(fip_dict['floating_ip_address'])
            LOG.debug("tenant: %s, floating ip dict: %s" % (self.tenant_name, fip_dict))

        return tenant_fixed_ips
        # return tenant_floating_ips


    def _get_ssh_session(self, vm_ip):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh.connect(hostname=vm_ip,
                        port=22,
                        username="cirros",
                        password="cubswin:)",
                        timeout=10)
            return ssh
        except Exception:
            return None

    def _trigger_ping(self, ssh_session, dst_ip, count=10, interval=1):

        cmd_str = "ping -c %s %s" % (count, dst_ip)
        LOG.debug("running command: %s" % (cmd_str))

        sin, sout, serr = ssh_session.exec_command(cmd_str)
        rc = sout.channel.recv_exit_status()

        LOG.debug("ping rc: %s" % rc)
        LOG.debug("ping output:\n")
        output_lines = []
        for line in sout.readlines():
            LOG.debug("  %s" % line)
            output_lines.append(line)

        return {"rc": rc,
                "stdout": output_lines}

    def _trigger_ping_async(self, ssh_session, dst_ip, count=10, interval=1):

        cmd_str = "sh -c 'ping -c %s %s > %s.out; echo $? > %s.rc.out' &" % (count, dst_ip, dst_ip, dst_ip)
        LOG.debug("running command: %s" % (cmd_str))
        
        sin, sout, serr = ssh_session.exec_command(cmd_str, timeout=10)
        rc = sout.channel.recv_exit_status()

        LOG.debug("ping async rc: %s" % rc)

        return rc

    def _get_ping_results(self, ssh_session, dst_ip):

        cmd_str = "cat %s.out" % (dst_ip)
        LOG.debug("running command: %s" % (cmd_str))
        
        sin, sout, serr = ssh_session.exec_command(cmd_str, timeout=10)
        rc = sout.channel.recv_exit_status()

        output_lines = []
        for line in sout.readlines():
            LOG.debug("  %s" % line)
            output_lines.append(line)

        cmd_str = "cat %s.rc.out" % (dst_ip)
        LOG.debug("running command: %s" % (cmd_str))
        
        sin, sout, serr = ssh_session.exec_command(cmd_str, timeout=10)
        rc = sout.channel.recv_exit_status()

        for line in sout.readlines():
            LOG.debug("  %s" % line)
            ping_rc = int(line)

        LOG.debug("ping async rc: %s" % ping_rc)

        return {"rc": ping_rc,
                "stdout": output_lines}


class CrossTenantPingTestCmd(IntraTenantPingTestCmd):
    
    def _get_dst_ip_list(self):
        resources = self.program.context['program.resources']
        tenant_floating_ips = []
        for tenant_id, fips in resources.tenant_ips.items():
            for fip_dict in fips:
                tenant_floating_ips.append(fip_dict['floating_ip_address'])
                LOG.debug("tenant: %s, floating ip dict: %s" % (self.tenant_name, fip_dict))

        return tenant_floating_ips


def main():
    ping_tester = TrafficLauncherCommand(None)
    ping_tester._trigger_ping("7.1.1.46", "7.1.1.1")
    
if __name__ == "__main__":
    main()
