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

    def set_program(self,program):
        self.program = program
        
        # pop the first command from the program
        cmd = self.program.commands.popleft()

        self.execution_queue.append(cmd)

    def run(self):

        while(True):
            
            if len(self.execution_queue) > 0:
                cmd = self.execution_queue.popleft()

                cmd.execute()
            elif len(self.program.commands) > 0: 
                cmd = self.program.commands.popleft()
                self.execution_queue.append(cmd)
            else:
                LOG.debug("no more commands")
                break


