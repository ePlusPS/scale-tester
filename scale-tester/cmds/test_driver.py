# A temporary test driver
import program
import tenants
import stack
# import pudb
import logging

LOG = logging.getLogger("scale_tester")

formatter = \
    logging.Formatter('%(asctime)s - %(module)s - %(funcName)s - (%(lineno)d) %(levelname)s \n %(message)s')

fh = logging.FileHandler("scale_tester.log")
fh.setFormatter(formatter)
LOG.addHandler(fh)
LOG.setLevel(logging.DEBUG)

def main():
    program_runner = program.ProgramRunner() 
    test_program = program.Program()

    program_context = test_program.context
   
    # change this for your local environment
    program_context['openstack_user']='admin'
    program_context['openstack_project']='admin'
    program_context['openstack_password']='c48d4870d911442c'
    program_context['openstack_auth_url']='http://10.1.10.127:5000/v2.0/'
    program_context['openstack_heat_url']='http://10.10.127:8004/v1/%s'
    program_context['program_runner']  = program_runner


    cmd_context = {}

    createTenantsAndUsersCmd = \
        tenants.CreateTenantAndUsers(tenant_name="tenant-test",
                                     num_of_users=3,
                                     cmd_context=cmd_context,
                                     program=test_program)
    

    create_stacks_context = {}
    
    create_stacks_context['vm_image_id']='adc34d8b-d752-4873-8873-0f2563ee8c72'
    create_stacks_context['external_network']='EXT-NET'
    create_stacks_context['heat_hot_file']="nh.yaml"


    createStacksCmd = \
        stack.CreateStacksCmd(create_stacks_context,test_program)


    test_program.add_command(createTenantsAndUsersCmd)
    test_program.add_command(createStacksCmd)

    # pu.db
    program_runner.set_program(test_program)
    program_runner.run()

if __name__=="__main__":
    main()
