
# This program demonstrates using the heatclient api
import keystoneclient.v2_0.client as keystone_client
import heatclient.v1.client as heat_client
import heatclient.openstack.common.uuidutils as uuidutils
import neutronclient.v2_0.client as neutron_client
import novaclient.v1_1.client as nova_client
import novaclient.v1_1.servers as nova_servers
# import novaclient.v3.client as nova_client
import yaml
import json
import pudb
import argparse
import logging
import pprint
import time
import string

DESCRIPTION="Scale Tester"
EPILOG = "Copyright 2014 OneCloud, Inc.  All rights reserved."
#DEFAULT_HOT_TEMPLATE_FILE = "servers_in_3_neutrons.yaml"
DEFAULT_HOT_TEMPLATE_FILE = "nh.yaml"

yaml_endpoint = """
    tenant: admin
    user: admin
    password: 52243b7a96194e9d 
    auth_url: http://10.1.10.63:5000/v2.0/
    heat_url: http://10.1.10.63:8004/v1
"""

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("scale_test.out")
logger.addHandler(file_handler)

def parse_args():
    """
    parse command line arguments
    """
    parser = argparse.ArgumentParser(description=DESCRIPTION,epilog=EPILOG)
    
    """
    parser.add_argument('template',
                        default=DEFAULT_HOT_TEMPLATE_FILE,
                        metavar=DEFAULT_HOT_TEMPLATE_FILE,
                        help='hot template file path')
    """
    args = parser.parse_args()

    return args

def main():
     
    
    command_line_args = parse_args()

    # read configuration
    configuration = yaml.load(yaml_endpoint)

    # login and obtain token
    keystoneClient = keystone_client.Client(auth_url=configuration['auth_url'],
                                            username=configuration['user'],
                                            password=configuration['password'],
                                            tenant_name=configuration['tenant'])
    
    nc = nova_client.Client(auth_url=configuration['auth_url'],
                       username=configuration['user'],
                       auth_token=keystoneClient.auth_token,
                       #password=configuration['password'],
                       tenant_id=keystoneClient.tenant_id
                      )


    neutronClient = neutron_client.Client(auth_url=configuration['auth_url'],
                                           username=configuration['user'],
                                           password=configuration['password'],
                                           tenant_name=configuration['tenant'])
    
    # nc.servers.create(name="nh-vm-test",image="cirros"

    server = nc.servers.get("b25707da-a690-47a0-83a4-9b8efec2ada6")
    server_image = nc.images.get("edc8e372-f1b7-4d69-8323-2bfe694c70a9")

    server_flavors = nc.flavors.list(detailed=True)

    for flavor in server_flavors:
        pprint.pprint(flavor)
    
    pu.db 
    # 1 is m1.tiny
    server_flavor = nc.flavors.get(1)
    
    nh_network = nc.networks.get("52442f0c-f493-4caf-8792-d26014a1dc58")
    
    nic_1_conf_dict = {'net-id':"52442f0c-f493-4caf-8792-d26014a1dc58"}
    
    nics = [nic_1_conf_dict]
    created_server = nc.servers.create(name="nh-vm-test-1",
                      image=server_image,
                      flavor=server_flavor,
                      nics=nics 
                     )
    # only EXT-NET
    floating_ip_pools = nc.floating_ip_pools.list()
    
    for pool in floating_ip_pools:
        pprint.pprint(pool)
    
    ext_net_pool = nc.floating_ip_pools.find(name='EXT-NET')

    floating_ip = nc.floating_ips.create(pool='EXT-NET')
    
    created_server.add_floating_ip(floating_ip)

    server_interfaces = created_server.interface_list() 

    for interface in server_interfaces:
        pprint.pprint(interface)

    list_of_servers = nc.servers.list()

    for server in list_of_servers:
        pprint.pprint(server)

    
    # logger.debug("tenant_id : ", keystoneClient.auth_tenant_id)
    # print(keystoneClient.auth_token)
    #pu.db
    host_ports = {} 
    neutron_ports = neutronClient.list_ports()
    for port in neutron_ports['ports']:
        port_id = port['id']
        if (string.find(port['device_owner'], "compute") >= 0):
            #print("VM PORT id: %s, ip: %s, type: %s" % (port['id'],
            #                                            port['fixed_ips'][0]['ip_address'],
            #                                            port['device_owner']))
            #print("VM PORT: %s" % port)
            host_ports[port_id] = port

        #if (string.find(port['device_owner'], "float") >= 0):
        #    print("FLOATING IP PORT ip: %s, type: %s" % (port['fixed_ips'][0]['ip_address'],
        #                                                 port['device_owner']))
        #    fip_ports[port_id] = port


    all_floating_ips = neutronClient.list_floatingips()
    for fip in all_floating_ips['floatingips']:
        print("floating ip: %s" % (fip))
        port_id = fip['port_id']
        host_ports[port_id]['floating_ip'] = fip['floating_ip_address']

    for host_port in host_ports.values():
        print("vm port: %s" % (host_port))

if __name__=='__main__':
    main()
