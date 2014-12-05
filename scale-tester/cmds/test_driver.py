# A temporary test driver
import program
import tenants
# import pudb
import logging

LOG = logging.getLogger("scale_tester")

formatter = \
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
    program_context['openstack_password']='c48d4870d911442c'
    program_context['openstack_auth_url']='http://10.1.10.127:5000/v2.0/'

    cmd_context = {}

    createTenantsAndUsersCmd = \
        tenants.CreateTenantAndUsers(tenant_name="tenant-test",
                                     num_of_users=3,
                                     cmd_context=cmd_context,
                                     program=test_program)
    
    test_program.add_command(createTenantsAndUsersCmd)

    # pu.db
    program_runner.set_program(test_program)
    program_runner.run()

if __name__=="__main__":
    main()
