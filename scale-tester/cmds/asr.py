import logging
import cmd
import program
from ncclient import manager
import pprint
import pudb

LOG = logging.getLogger("scale_tester")

GET_SHOW_CLOCK = """
<filter type="subtree">
    <config-format-text-cmd>
        <text-filter-spec> | inc FFFFFFFFFFFFFFFF</text-filter-spec>
    </config-format-text-cmd>    
    <oper-data-format-text-block>
        <exec>show clock</exec>
    </oper-data-format-text-block>
</filter>
"""

GET_PROCESS_CPU_HISTORY = """
<filter type="subtree">
    <config-format-text-cmd>
        <text-filter-spec> | inc FFFFFFFFFFFFFFFF</text-filter-spec>
    </config-format-text-cmd>    
    <oper-data-format-text-block>
        <exec>show process cpu history</exec>
    </oper-data-format-text-block>
</filter>
"""

GET_PLATFORM_RESOURCES = """
<filter type="subtree">
    <config-format-text-cmd>
        <text-filter-spec> | inc FFFFFFFFFFFFFFFF</text-filter-spec>
    </config-format-text-cmd>    
    <oper-data-format-text-block>
        <exec>show platform resources slot %s  </exec>
    </oper-data-format-text-block>
</filter>
"""

def asr_connect(host, port, user, password):
    """
    ncclient manager factory method
    """
    return manager.connect(host=host,
                           port=port,
                           username=user,
                           password=password,
                           # device_params={'name': "csr"},
                           timeout=30
                          )

class GetASRHealthCmd(cmd.Command):
    """
    This command will fetch and log the CPU and resource health for a specified ASR router 
    """

    def __init__(self, cmd_context, program, **kwargs):
        """
        constructor
        """
        super(GetASRHealthCmd,self).__init__()
        self.context = cmd_context
        self.program = program

        #extra kwargs
        if ('tenant_name' in kwargs):
            self.tenant_name = kwargs['tenant_name']
    
        # obtain connection information for router
        self.asr_host = kwargs['asr_host']
        self.asr_host_port = kwargs['asr_host_port']
        self.asr_user = kwargs['asr_user']
        self.asr_password = kwargs['asr_password']
        
        self.asr_slot = kwargs.get('asr_slot',None)
        
    
    def init(self):
        LOG.debug("init")
        return cmd.SUCCESS 
    
    def execute(self):
        """
        Gets the timestamp for the designated ASR router,
        invokes show process cpu history 
        invokes show platform resources slot [optional]
        """
        LOG.debug("execute")

        pu.db

        with asr_connect(self.asr_host,
                         port=self.asr_host_port,
                         user=self.asr_user,
                         password=self.asr_password) as conn:
            try:
                filter_str = GET_SHOW_CLOCK
                rpc_obj = conn.get(filter=filter_str)

                LOG.info("ASR Host %s clock = %s" % \
                          (self.asr_host,rpc_obj.data_xml))
                
                filter_str = GET_PROCESS_CPU_HISTORY
                rpc_obj = conn.get(filter=filter_str)
                LOG.info("ASR Host %s cpu history = %s" % \
                          (self.asr_host,rpc_obj.data_xml))
               
                if (self.asr_slot is not None):
                    filter_str = GET_PLATFORM_RESOURCES % (self.asr_slot)
                    rpc_obj = conn.get(filter=filter_str)
                    LOG.info("ASR Host %s Slot %s Resource = %s" % \
                              (self.asr_host, self.asr_slot, rpc_obj.data_xml))

            except Exception as exc:
                LOG.debug("Caught exception %s" % (exc.message))

        return cmd.SUCCESS 
    
    def done(self):
        LOG.debug("done")
        return cmd.SUCCESS 
    
    def undo(self):
        LOG.debug("Undo")
        return cmd.SUCCESS 
       
if __name__ == "__main__":

    cmd_context = {}
    program = None
    asr_health_cmd = GetASRHealthCmd(cmd_context, 
                                     program,
                                     asr_host="10.1.10.252",
                                     asr_host_port=22,
                                     asr_user="admin",
                                     asr_password="admin",
                                     asr_slot="0")

    asr_health_cmd.init()
    asr_health_cmd.execute()
    asr_health_cmd.done()
                    
