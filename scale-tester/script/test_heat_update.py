
# This program demonstrates using the heatclient api
# stack update
import keystoneclient.session as kssession
import keystoneclient.v2_0.client as keystone_client
import keystoneclient.auth.identity.v2 as v2_auth
import heatclient.v1.client as heat_client
import heatclient.openstack.common.uuidutils as uuidutils
import neutronclient.v2_0.client as neutron_client
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
    password: f73744eca7354bfb
    auth_url: http://10.1.10.169:5000/v2.0/
    heat_url: http://10.1.10.169:8004/v1
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

    parser.add_argument('stack_id',
                        help='stack_id')

    parser.add_argument('template',
                        default=DEFAULT_HOT_TEMPLATE_FILE,
                        metavar=DEFAULT_HOT_TEMPLATE_FILE,
                        help='hot template file path')

    args = parser.parse_args()

    return args

def old_way():
    command_line_args = parse_args()

    # read configuration
    configuration = yaml.load(yaml_endpoint)
    pu.db
    keystoneClient = keystone_client.Client(auth_url=configuration['auth_url'],
                                            username=configuration['user'],
                                            password=configuration['password'],
                                            tenant_name=configuration['tenant'])

    heat_url = 'http://10.1.10.169:8004/v1/%s' % (keystoneClient.auth_tenant_id) 

    logger.debug("heat_url=%s" %(heat_url))

    heat = heat_client.Client(heat_url,
                              token=keystoneClient.auth_token)
    
    params = {}

    # load the yaml
    #pu.db
    template_yml_stream = open(command_line_args.template)
    template = yaml.load(template_yml_stream)
    
    # setting up the kwargs for the stacks.create call
    params['environment'] = {}
    params['files']={}
    params['parameters']= {'image_id': '355b3761-a8d3-4650-914e-ea72569346d9',
                           'public_net': 'EX',
                           'public_net_id': '1e04dc1e-958b-4d11-b55f-51593c4606e3'
                          }
    params['existing'] = False
    params['stack_id']= command_line_args.stack_id
    params['template'] = template 

    pprint.pprint(params)

    heat.stacks.update(**params)
    
    print("done")

def main():
     
    
    command_line_args = parse_args()

    # read configuration
    configuration = yaml.load(yaml_endpoint)


    #establish a keystone session
    kwargs = {
        'insecure': False,
        'cacert': '',
        'cert': None,
        'key': None,
        'timeout': None 
    }

    keystone_session = kssession.Session(verify=None, cert=None, timeout=None)

    kwargs = {
        'username': configuration['user'], 
        'user_id': None, 
        'user_domain_id': None, 
        'user_domain_name': None, 
        'password': configuration['password'],
        'auth_token': None, 
        'project_id': None,
        'project_name': configuration['tenant'], 
        'project_domain_id': None, 
        'project_domain_name': None 
    }

    keystone_pass = v2_auth.Password(auth_url = configuration['auth_url'],
                                     username=configuration['user'],
                                     password=configuration['password'],
                                     tenant_id=None,
                                     tenant_name=configuration['tenant'])
    service_type = 'orchestration'
    heat_endpoint = keystone_pass.get_endpoint(session=keystone_session,
                                               service_type=service_type)
    endpoint_type = 'publicURL'
    
    heat_kwargs = {
        'auth_url': configuration['auth_url'], 
        'session': keystone_session,
        'auth': keystone_pass,
        'service_type': service_type,
        'endpoint_type': endpoint_type,
        'region_name': '', 
        'username': configuration['user'], 
        'password': configuration['password'], 
        'include_pass': False 
    }

    pu.db

    hc = heat_client.Client(api_version='1',
                            endpoint=heat_endpoint,
                            **heat_kwargs)
    # login and obtain token
    """ 
    keystoneClient = keystone_client.Client(auth_url=configuration['auth_url'],
                                            username=configuration['user'],
                                            password=configuration['password'],
                                            tenant_name=configuration['tenant'])
    neutronClient = neutron_client.Client(auth_url=configuration['auth_url'],
                                           username=configuration['user'],
                                           password=configuration['password'],
                                           tenant_name=configuration['tenant'])

    # logger.debug("tenant_id : ", keystoneClient.auth_tenant_id)
    # print(keystoneClient.auth_token)
    logger.debug(configuration['heat_url'])

    version = '1'
    # heat_url = "%s/%s" % (configuration['heat_url'],
    #                      keystoneClient.auth_tenant_id) 
    heat_url = 'http://10.1.10.169:8004/v1/%s' % (keystoneClient.auth_tenant_id) 

    logger.debug("heat_url=%s" %(heat_url))

    heat = heat_client.Client(heat_url,
                              token=keystoneClient.auth_token)
    for stack in heat.stacks.list(limit=10):
        print(stack)
    """


    uuid = uuidutils.generate_uuid()
    
    print(uuid)
    
    params = {}

    # load the yaml
    #pu.db
    template_yml_stream = open(command_line_args.template)
    template = yaml.load(template_yml_stream)
    
    # setting up the kwargs for the stacks.create call
    params['environment'] = {}
    params['files']={}
    params['parameters']= {'image_id': '355b3761-a8d3-4650-914e-ea72569346d9',
                           'public_net': 'EX',
                           'public_net_id': '1e04dc1e-958b-4d11-b55f-51593c4606e3'
                          }
    params['existing'] = False
    params['stack_id']= command_line_args.stack_id
    params['template'] = template 

    pprint.pprint(params)
    
    # json_template = json.dumps(template)
    # pprint.pprint(json_template)
    hc.stacks.update(**params)
    
    #print("resp type: %s" % type(resp))
    #for i in resp:
    #    print("resp item: %s" % i)

    pu.db
    
    """
    filter = {"name": params['stack_name']}
    stack_list = heat.stacks.list(filters=filter)
    for stack_item in stack_list:
        print("stack: %s" % stack_item)
        print("stack_id: %s" % stack_item.id)
        stack_id = stack_item.id
    
    stack = heat.stacks.get(stack_id)
    print("retrieved stack: %s" % stack)
    
    resources = heat.resources.list(stack_id)
    for resource in resources:
        print("RESOURCE: %s" % resource)
    """


    """
    print("waiting 10s to check ports...")
    time.sleep(10)

    host_ports = {}
    fip_ports = {}

    
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

    print("waiting 10s before delete...")
    time.sleep(10)
    print("deleting stack...")
    heat.stacks.delete(stack_id)
    """

if __name__=='__main__':
    # main()
    old_way()
