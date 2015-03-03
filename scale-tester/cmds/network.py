"""
This file contains a collection of neutron based commands for creating
routers and networks for a given tenant.
"""

import logging
import cmd
import program
import keystoneclient.v2_0.client as keystone_client
# import novaclient.v1_1.client as nova_client
#import novaclient.v1_1.servers as nova_servers
import neutronclient.v2_0.client as neutron_client
import pprint
import pudb
import time
import cmds.compute

LOG = logging.getLogger("scale_tester")

class CreateNetworksCmd(cmd.Command):
    """
    This command will iterate through a list of tenants
    and spawn individual CreateNetworkCmd objects for each
    tenant.
    """
    def __init__(self, cmd_context, program, **kwargs):
        """
        constructor
        """
        super(CreateNetworksCmd,self).__init__()
        self.context = cmd_context
        self.program = program

    def init(self):
        LOG.debug("init")

        if ("program.resources" in self.program.context and
            "ext_router_name" in self.context and
            "ext_net_id" in self.context and
            "tenant_network_configs" in self.context and
            "vm_configs" in self.context):

            LOG.debug("preconditions met")
            return cmd.SUCCESS 
        else:
            LOG.debug("preconditions not met")
            return cmd.FAILURE_HALT
    
    def execute(self):
        LOG.debug("execute")
        resources = self.program.context['program.resources']
        program_runner = self.program.context['program_runner']

        if (resources is not None and program_runner is not None):
            LOG.debug("Walking the set of created tenants")

            for tenant_id, tenant in \
                sorted(resources.tenants.iteritems(),
                       key=lambda (k,v): v.name):
                
                a_user = resources.tenant_users[tenant_id][0] 
                LOG.debug(pprint.pformat(a_user))
                
                tenant_network_configs = self.context['tenant_network_configs']
                vm_configs = self.context['vm_configs']
                
                tenant_net_cmd_context = {}
                create_network_cmd = \
                    CreateTenantNetworkCmd(tenant_net_cmd_context,
                                           self.program,
                                           tenant_name=tenant.name,
                                           tenant_user=a_user.name,
                                           tenant_user_password=a_user.name,
                                           router_name=self.context['ext_router_name'],
                                           ext_net_id=self.context['ext_net_id'],
                                           tenant_network_configs=tenant_network_configs,
                                           vm_configs=vm_configs
                                          )

                program_runner.execution_queue.append(create_network_cmd)
                LOG.debug("Enqueued CreateNetworkCmd")

        return cmd.SUCCESS 
    
    def done(self):
        LOG.debug("done")
        return cmd.SUCCESS 
    
    def undo(self):
        LOG.debug("Undo")
        return cmd.SUCCESS 



class CreateTenantNetworkCmd(cmd.Command):
    """
    This command is responsible for creating the networks for a specified
    tenant
    """

    def __init__(self, cmd_context, program, **kwargs):
        """
        constructor
        """
        super(CreateTenantNetworkCmd,self).__init__()
        self.context = cmd_context
        self.program = program

        #extra kwargs
        self.tenant_name = kwargs['tenant_name']
        self.tenant_user = kwargs['tenant_user']
        self.tenant_password = kwargs['tenant_user_password']

        self.router_name = kwargs.get('router_name',None)
        self.ext_net_id = kwargs.get('ext_net_id',None)

        # if supplied, tenant_network_configs is a list of networks that
        # should be created on behalf of a client
        # tenant_network_configurations is a list of dictionaries
        #
        # [ {"ip_version":4,
        #    "cidr":"45.45.45.0/24"
        #   },
        #   {
        #    ...
        #   }
        # ]
        self.tenant_network_configs = \
                        kwargs.get('tenant_network_configs',None)
       
        # if supplied, dictates how vms should be spun up in each
        # network
        #
        # Sample format for the parameter
        # vm_configs = {"num_vms_per_network":1,
        #               "max_num_of_vms":3
        #              }
        self.vm_configs = \
                        kwargs.get('vm_configs',None)
        
        # a delay to pause the processing of the command
        self.intentional_delay = kwargs.get('delay',0)
    
    def init(self):
        LOG.debug("init")
        return cmd.SUCCESS 
   
    def _spawn_vms(self,neutron_client, created_networks):
        
        program_runner = self.program.context['program_runner']

        total_created_vms = 0
        if (self.vm_configs is not None and 
            created_networks is not None):

            LOG.debug("vm_configs = %s" % (pprint.pformat(self.vm_configs)))
            pu.db 
            external_network = \
                neutron_client.show_network(self.ext_net_id)

            for created_network in created_networks:
                
                for index in xrange(0,self.vm_configs['num_vms_per_network']):
                   vm_name = "%s-server-%d" % (created_network['network']['name'],index)
                   cmd_context = {}
                   createVMCmd = \
                    cmds.compute.CreateVMCmd(cmd_context,
                                             self.program,
                                             tenant_name=self.tenant_name,
                                             tenant_user=self.tenant_user,
                                             tenant_user_password=self.tenant_password,
                                             vm_name=vm_name,
                                             vm_image_id=self.vm_configs['vm_image_id'],
                                             vm_flavor=self.vm_configs['vm_flavor'],
                                             private_net_id=created_network['network']['id'],
                                             ext_net_name = external_network['network']['name'])
                    
                   program_runner.execution_queue.append(createVMCmd)
                   LOG.debug("Enqueued CreateVMCmd (%s)" % (vm_name))

                   total_created_vms = total_created_vms + 1
                
                if (total_created_vms >= self.vm_configs['max_num_of_vms']):
                    break

    def execute(self):
        LOG.debug("execute")

        # obtain keystone client
        openstack_conf = self.program.context["openstack_conf"]
        keystone_c = keystone_client.Client(auth_url=openstack_conf['openstack_auth_url'],
                                   username=self.tenant_user,
                                   password=self.tenant_password,
                                   tenant_name=self.tenant_name)
        """                                   
        nova_c = \
            nova_client.Client(auth_url=openstack_conf['openstack_auth_url'],
                               username = self.tenant_user,
                               auth_token=keystone_c.auth_token,
                               tenant_id = keystone_c.tenant_id)
           
        """
        neutron_c = neutron_client.Client(auth_url=openstack_conf['openstack_auth_url'],
                                          username = self.tenant_user,
                                          password = self.tenant_password,
                                          tenant_name=self.tenant_name)
        
        router_conf = {
            "name":self.router_name,
            "external_gateway_info":{
                "network_id":self.ext_net_id
            },
            "admin_state_up": True
        }
        
        # create_router returns a dictionary containing a key, "router" which 
        # contains the attributes of created router
        created_router = neutron_c.create_router({"router":router_conf})
    

        index = 0
        LOG.debug("num of tenant_network_configs = %d" % \
                  (len(self.tenant_network_configs)))

        created_networks = []

        # create each network and attach it to the external facing router
        for tenant_net_config in self.tenant_network_configs:
            
            network_name = "%s-net-%d" % (self.tenant_name,index)
            network_conf = {'name':network_name,'admin_state_up':True}
            
            created_network = neutron_c.create_network({"network":network_conf})
            
            created_networks.append(created_network)

            subnet_name = "%s-subnet-%d" % (self.tenant_name,index)

            subnet_conf = {"name":subnet_name,
                           "network_id":created_network['network']['id'],
                           "tenant_id":keystone_c.tenant_id,
                           "ip_version":self.tenant_network_configs[index]['ip_version'],
                           "cidr":self.tenant_network_configs[index]['cidr']
                          }
            created_subnet = neutron_c.create_subnet({"subnet":subnet_conf})
            
            created_router_interface = \
                neutron_c.add_interface_router(created_router['router']['id'],
                                 {'subnet_id':created_subnet['subnet']['id']})

            LOG.debug("Added router interface %s" % \
                       (pprint.pformat(created_router_interface)))

            LOG.info("Created network %s, subnet %s" % \
                      (network_name,subnet_name))

            index = index+1

        self._spawn_vms(neutron_c, created_networks) 
        
        if (self.intentional_delay > 0):
            LOG.debug("Intentional delay of %d seconds" % \
                       (self.intentional_delay))
            time.sleep(self.intentional_delay)

        return cmd.SUCCESS
    
    def done(self):
        LOG.debug("done")
        return cmd.SUCCESS 
    
    def undo(self):
        LOG.debug("Undo")
        return cmd.SUCCESS 
        
