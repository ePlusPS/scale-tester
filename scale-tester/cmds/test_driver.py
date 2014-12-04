# A temporary test driver
import program
import tenants
import pudb
import logging

LOG = logging.getLogger("scale_tester")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

fh  = logging.FileHandler("scale_tester.log")
fh.setFormatter(formatter)
LOG.addHandler(fh)
LOG.setLevel(logging.DEBUG)

def main():
    program_runner = program.ProgramRunner() 
    test_program = program.Program()

    cmd_context = {}
    createTenantsAndUsersCmd = tenants.CreateTenantAndUsers(3,cmd_context)
    
    test_program.add_command(createTenantsAndUsersCmd)

    # pu.db
    program_runner.set_program(test_program)
    program_runner.run()

if __name__=="__main__":
    main()
