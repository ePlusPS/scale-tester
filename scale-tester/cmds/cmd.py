
class Command(object):
    """
    This class represents an abstract Command
    """
    
    def __init__(self,name=None):
        self.context = {}
        self.name = name

    def init(self):
        """
        The init allows a Command to check whether the preconditions
        to execute are met.
        """
        pass
    
    def execute(self):
        """
        The execute method implements the Command
        """
        pass

    def done(self):
        """
        The done method can be used as a placeholder to invoke any sort
        post-processing logic when the command has finished.
        """
        pass
    
    def undo(self):
        """
        If implemented, undo provides a mechanism by which the results of
        a command are roll-back
        """
        pass
