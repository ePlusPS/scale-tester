"""
This file contains a collection of nova compute based commands for creating
virtual machines.
"""

import logging
import cmd
import program
import keystoneclient.v2_0.client as keystone_client
import novaclient.v1_1.client as nova_client
import novaclient.v1_1.servers as nova_servers
import pprint
import pudb
import time

LOG = logging.getLogger("scale_tester")

class CreateVMsCmd(cmd.Command):
    """
    This command will n-number of vms in a specified
    private network.
    """
    def __init__(self, cmd_context, program, **kwargs):
        """
        constructor
        """
        super(CreateVMsCmd,self).__init__()
        self.context = cmd_context
        self.program = program

    def init(self):
        LOG.debug("init")

        if ("tenant_name" in self.context and
            "tenant_user" in self.context and
            "tenant_user_password" in self.context and
            "num_of_vms" in self.context and
            "vm_image_id" in self.context and
            "vm_flavor" in self.context and
            "ext_net_name" in self.context and 
            "private_network_id" in self.context):
            LOG.debug("preconditions met")
            return cmd.SUCCESS 
        else:
            LOG.debug("preconditions not met")
            return cmd.FAILURE_HALT
    
    def execute(self):
        LOG.debug("execute")
        
        tenant_name          = self.context['tenant_name']
        tenant_user          = self.context['tenant_user']
        tenant_user_password = self.context['tenant_user_password']

        vm_base_index = self.context['vm_base_index']
        num_of_vms = self.context['num_of_vms']
        vm_name_prefix = self.context['vm_name_prefix']
        vm_image_id = self.context['vm_image_id']
        vm_flavor = self.context['vm_flavor']
        ext_net_name = self.context['ext_net_name']
        private_net_id = self.context['private_network_id']
        program_runner = self.program.context['program_runner']

        LOG.debug("# of vms to spin-up %d" % (num_of_vms))
        for index in xrange(0,num_of_vms):
            """
            spawn a vm create command
            """
            cmd_context = {}
            vm_index = vm_base_index + index
            vm_name = "%s-%d" % (vm_name_prefix, vm_index)
            
            createVMCmd = CreateVMCmd(cmd_context, self.program,
                                      tenant_name=tenant_name,
                                      tenant_user=tenant_user,
                                      tenant_user_password=tenant_user_password,
                                      vm_name=vm_name,
                                      vm_image_id=vm_image_id,
                                      vm_flavor=vm_flavor,
                                      private_net_id=private_net_id,
                                      ext_net_name=ext_net_name)

            program_runner.execution_queue.append(createVMCmd)
            
            LOG.debug("Enqueued CreateVMCmd (%s)" % (vm_name))

        return cmd.SUCCESS 
    
    def done(self):
        LOG.debug("done")
        return cmd.SUCCESS 
    
    def undo(self):
        LOG.debug("Undo")
        return cmd.SUCCESS 



class CreateVMCmd(cmd.Command):
    """
    This command is responsible for creating a vm in a tenant network
    """

    def __init__(self, cmd_context, program, **kwargs):
        """
        constructor
        """
        super(CreateVMCmd,self).__init__()
        self.context = cmd_context
        self.program = program

        #extra kwargs
        self.tenant_name = kwargs['tenant_name']
        self.tenant_user = kwargs['tenant_user']
        self.tenant_password = kwargs['tenant_user_password']

        self.vm_name = kwargs['vm_name']
        self.vm_image_id = kwargs['vm_image_id']
        self.vm_flavor = kwargs['vm_flavor']
        self.private_net_id = kwargs['private_net_id']
        self.ext_net_name = kwargs['ext_net_name']
        
    
    def init(self):
        LOG.debug("init")
        return cmd.SUCCESS 
    
    def execute(self):
        LOG.debug("execute")
        # obtain keystone client
        openstack_conf = self.program.context["openstack_conf"]
        keystone_c = keystone_client.Client(auth_url=openstack_conf['openstack_auth_url'],
                                   username=self.tenant_user,
                                   password=self.tenant_password,
                                   tenant_name=self.tenant_name)
        nova_c = \
            nova_client.Client(auth_url=openstack_conf['openstack_auth_url'],
                               username = self.tenant_user,
                               auth_token=keystone_c.auth_token,
                               tenant_id = keystone_c.tenant_id)
                                                   
        
        server_image = nova_c.images.get(self.vm_image_id)
        server_flavor = nova_c.flavors.get(self.vm_flavor)
    
        nic_1_conf_dict = {'net-id':self.private_net_id}

        nics = [nic_1_conf_dict]

        created_server = nova_c.servers.create(name=self.vm_name,
                                               image=server_image,
                                               flavor=server_flavor,
                                               nics=nics)
        
        time.sleep(3.0)
        num_tries = 0
        while(num_tries < 5):
            try:
                floating_ip = nova_c.floating_ips.create(pool=self.ext_net_name)
                created_server.add_floating_ip(floating_ip)
                LOG.info("Created VM %s" % (self.vm_name))
                break
            except:
                time.sleep(3.0)
                num_tries += 1

        return cmd.SUCCESS 
    
    def done(self):
        LOG.debug("done")
        return cmd.SUCCESS 
    
    def undo(self):
        LOG.debug("Undo")
        return cmd.SUCCESS 
        
