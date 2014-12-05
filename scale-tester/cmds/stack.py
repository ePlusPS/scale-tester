# placeholder for heatclient related with commands

import cmd

class StackReqRsp:
    """
    Represents a common input/output object for interacting
    with different stack creation APIs.

    Can be fed into either a HeatClient based stack create 
    service or nova/neutron based stack create implementation.
    """

    def __init__(self):
        self.networks = []
        self.vms = []
        self.routers = []
        

class CreateStackCmd(cmd.Command):
    """
    This cmd creates a OpenStack Heat Stack instance
    """
    
    def __init__(self):
        pass

    def init(self):
        pass

    def execute(self):
        pass

    def undo(self):
        pass
