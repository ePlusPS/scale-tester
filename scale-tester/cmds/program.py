import logging
from collections import deque

LOG = logging.getLogger("scale_tester")

class Program(object):
    """
    This class represents a collection of parsed commands to be executed by the
    programm runner
    """

    def __init__(self):
        """
        attributes
        commands represents the list of commands in the program
        context represents program wide scope for state that's accessible
        to all commands
        """
        self.commands = deque()
        self.context = {}
        self.name = None

    def add_command(self,cmd):
        """appends a cmd to the commands list"""
        self.commands.append(cmd)

class ProgramRunner(object):
    """
    This class represents the execution engine for a program
    """

    def __init__(self):
        """
        constructor
        """
        self.execution_queue= deque()
        self.program = None
        self.completed_commands = deque() 

        # self.is_test_mode = True

    def set_program(self,program):
        self.program = program
        
        # pop the first command from the program
        cmd = self.program.commands.popleft()

        self.execution_queue.append(cmd)

    def run(self):
        LOG.debug("ProgramRunner run started")
        while(True):
            
            if len(self.execution_queue) > 0:
                LOG.debug("popping next command from the execution queue ")
                cmd = self.execution_queue.popleft()
               
                # wrap each command step in a function so that exception
                # handling is easier to deal with

                # we can add status checks after each call to check
                # whether the next step should be invoked or not
                cmd.init()
                cmd.execute()

                # if a cmd.done() indicates that it's not done, appendleft
                # the current cmd
                cmd.done()
                
                self.completed_commands.append(cmd)

            elif len(self.program.commands) > 0: 
                LOG.debug("popping next cmd from the program commands queue ")
                cmd = self.program.commands.popleft()
                self.execution_queue.append(cmd)
            else:
                LOG.debug("No more commands")
                break

        # Clean up the results of a program/test run
        while (len(self.completed_commands)>0):
            executed_cmd = self.completed_commands.popleft()
            executed_cmd.undo()






