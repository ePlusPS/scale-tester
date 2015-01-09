# This utility program generates a user-defined HOT template file
# based on the input of 
# - number of tenant networks
# - number of vms per network

import argparse
import logging
import yaml
import pprint
import pudb

DESCRIPTION = "HOT File Creator"


LOG = logging.getLogger("hot_file_creater")

formatter = \
    logging.Formatter('%(asctime)s - %(module)s - %(funcName)s - (%(lineno)d) %(levelname)s \n %(message)s')

fh = logging.FileHandler("debug.out")
fh.setFormatter(formatter)
fh.setLevel(logging.DEBUG)

LOG.addHandler(fh)
LOG.setLevel(logging.DEBUG)

app_context = {}

def parse_args():
    """
    Parse command line arguments
    """

    parser = argparse.ArgumentParser(description=DESCRIPTION)
    
    # make this required
    parser.add_argument('--num-networks',
                        type=int,
                        help='number of tenant networks')

    # make this required
    parser.add_argument('--num-vms',
                        type=int,
                        help='number of vms per network')

    parser.add_argument('yaml',
                        help='yaml file')
                        
    args = parser.parse_args()

    # set app_context

    num_networks = args.num_networks
    num_vms = args.num_vms
    
    app_context['num_networks'] = num_networks
    app_context['num_vms'] = num_vms

    LOG.debug("num_networks = %d, num vms = %d" % (app_context['num_networks'],
                                                   app_context['num_vms']))
    
    # enable in order to see the debug output for a reference yaml ->
    # dictionary conversion

    # yaml_stream = open(args.yaml,'r')
    # yaml_data = yaml.load(yaml_stream)
    # LOG.debug("%s" %(pprint.pformat(yaml_data)))


def create_yaml_template(description):
    """
    This function creates the basic keys for a yaml dictionary
    """

    yaml_dict = {}

    yaml_dict['description'] = description
    yaml_dict['heat_template_version'] = '2013-05-23'
    yaml_dict['outputs'] = {}
    yaml_dict['parameters'] = {}
    yaml_dict['resources'] = {}

    return yaml_dict

def create_yaml_output_value_attributes(list_of_get_attributes):
    """
    A helper function for creating output value attribute dictionary for a
    output parameter
    """
    output_param_value_dict = {'get_attr':list_of_get_attributes}

    return output_param_value_dict
     


def add_yaml_template_output_parameter(yaml_dict,
                                       output_param_name,
                                       output_param_description,
                                       output_val_dict):
    """
    Sets a output parameter to the heat template
    """

    if ('outputs' in yaml_dict):
        output_params = yaml_dict['outputs']

        output_params[output_param_name] = {'description':output_param_description,
                                            'value':output_val_dict}
    else:
        LOG.debug('yaml_dict parameter key %s not present' % 
                  ('outputs'))

# input parameter handling
def create_input_parameter(description,parameter_type):
    """
    Returns a dictionary representing input parameter attributes
    """

    input_param = {}
    input_param['description'] = description
    input_param['parameter_type'] = parameter_type
    return input_param

def add_input_parameter(parameters,input_param_name, input_param_value):
    parameters[input_param_name] = input_param_value
    LOG.debug("Added input param %s to parameters" % (input_param_name))


# output parameter handling
def create_output_parameter(description,value):
    """
    This function creates the "value" for a output parameter
    """
    output_param = {}
    output_param['description'] = description
    output_param['value'] = value

    return output_param

def add_output_parameter(outputs, output_param_name, output_param_value):
    """
    This function adds a output parameter to a outputs dictionary
    """
    outputs[output_param_name] = output_param_value
    LOG.debug("Added output param %s to outputs" % (output_param_name))

# resource handling 
def create_resource(resource_type, properties=None, metadata=None,
                    depends_on=None, update_policy=None, deletion_policy=None):
    """
    This function creates a resource (as represented by a dictionary)
    that has the following keys initialized

    type
    properties
    metadata
    depends_on
    update_policy
    deletion_policy
    """
    resource = {}
    
    resource['type'] = resource_type
    # resource['properties']=properties
    # resource['metadata']=metadata
    # resource['depends_on']=depends_on
    # resource['update_policy']=update_policy
    #resource['deletion_policy']=deletion_policy

    return resource
    
def add_resource(resources, resource_id, resource):
    """
    resources - a dictionary that will hold all the resources
    resource_id - resource name/label
    resource - the actual dict containing the key-value pairs for a resource
    """
    resources[resource_id] = resource
    LOG.debug("Added resource %s to resources" % (resource_id))

def add_resource_property(resources,
                          resource_name,
                          property_name,
                          property_value):
    """
    
    For example, for the params, property_name and property_value
    {
       'properties':{'floating_network_id':{'get_param':'public_net_id'},
                       'port_id':{'get_resource': 'net_1_server1_port'}}
    }

    where the first property name is 'floating_network_id' and
     property_value is {'get_param':'public_net_id'}
    """
    if resource_name in resources:
        resource = resources[resource_name]

        if 'properties' not in resource:
            resource['properties'] = {}
        
        properties = resource['properties']
        
        properties[property_name] = property_value

        LOG.debug("Added %s" % \
            (pprint.pformat(properties[property_name])))

def add_resource_depends(resources, resource_name, dependency_value): 
    """
    This function adds a depends_on (dependency) value for resource
    """
    if resource_name in resources:
        resource = resources[resource_name]
        resource['depends_on'] = dependency_value

        LOG.debug("Added depenency value %s to resource %s" % \
                  (dependency_value, resource_name))
    else:
        LOG.debug("Could not find resource %s in resources" % (resource_name))
            
def main():
    parse_args()
    test_hot_template_api()

def test_hot_template_api():

    hot_template_description = \
        "HOT template for %d networks and %d vms per network" % \
        (app_context['num_networks'],app_context['num_vms'])

    yaml_dict = create_yaml_template(hot_template_description)

    
    # input parameter handling
    parameters = yaml_dict['parameters']
    image_id_param_value = create_input_parameter('Image Name','string')
    add_input_parameter(parameters,'image_id',image_id_param_value)

    outputs = yaml_dict['outputs']

    get_attr_list = ['net_1_server1','first_address']
    output_val_dict = create_yaml_output_value_attributes(get_attr_list) 

    output_param = create_output_parameter('private ip of server!',
                                            output_val_dict)

    add_output_parameter(outputs,'server_ip',output_param)

    
    # example of creating a floating ip
    resources = yaml_dict['resources']

    floating_ip_resource = create_resource('OS::Neutron::FloatingIP')
    
    add_resource(resources,'net_1_floating_ip1', floating_ip_resource)

    add_resource_property(resources,'net_1_floating_ip1','floating_network_id',{'get_param':'public_net_id'})
    add_resource_property(resources,'net_1_floating_ip1','port_id',{'get_resource':'net_1_server1_port'})

    add_resource_depends(resources,'net_1_floating_ip1','router1_interface_1')

    LOG.debug("%s" % (pprint.pformat(yaml_dict)))

if __name__ == "__main__":
    main()
