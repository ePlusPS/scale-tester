# placeholder for heatclient related with commands

import cmd

class StackReqRsp:
    """
    Represents a common input/output object for interacting
    with different stack creation APIs.

    Can be fed into either a HeatClient based stack create 
    service or nova/neutron based stack create implementation.
    """

    def __init__(self,**kwargs):
        self.networks = []
        self.vms = []
        self.routers = []

class CreateStacksCmd(cmd.Command):
    """
    This cmd creates invidual CreateStackCmd 
    commands based on the number of tenants
    """
    
    def __init__(self):
        pass

    def init(self):
        pass

    def execute(self):
        # walk the number of tenants
        #  figure out how many networks
        pass

    def undo(self):
        pass

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
