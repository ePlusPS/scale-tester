
# This file demonstrates accessing a ASR via ncclient and netconf 

import sys
import logging
import argparse
import pudb

from ncclient import manager

DESCRIPTION = """
python test_netconf.py --user admin --password {prefix with \ for special
characters} --host 1.1.1.1
"""

EPILOG="epilogue"

logger = logging.getLogger("test_netconf")

logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("test_netconf.out")
logger.addHandler(file_handler) 

DO_CD_SNIPPET= """
<config>
        <cli-config-data>
            <cmd>do cd</cmd>
        </cli-config-data>
</config>
"""

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

def parse_args():
    """
    parse command line arguments
    """
    parser = argparse.ArgumentParser(description=DESCRIPTION,epilog=EPILOG)
    
    parser.add_argument('--user',
                        help='user')
    parser.add_argument('--password',
                        help='password')
    parser.add_argument('--host',
                        help='ASR host')

    args = parser.parse_args()

    return args

def csr_connect(host, port, user, password):
    return manager.connect(host=host,
                           port=port,
                           username=user,
                           password=password,
                           # device_params={'name': "csr"},
                           timeout=30
                          )
def do_show_cpu_process_history(conn):
    try:
        show_str = DO_CD_SNIPPET 
        rpc_obj = conn.edit_config(target='running', config=show_str)

        logger.debug("do cd response %s" % rpc_obj.xml)

        # filter_str = GET_SHOW_CLOCK
        filter_str = GET_PROCESS_CPU_HISTORY
        rpc_obj = conn.get(filter=filter_str)
        # logger.debug("show clock response %s" % rpc_obj.__dict__)
        logger.debug("GET PROCESS CPU HISTORY response %s" % rpc_obj.data_xml) 
    
        slot = "0"
        filter_str = GET_PLATFORM_RESOURCES % ("0")
        rpc_obj = conn.get(filter=filter_str)
        # logger.debug("show clock response %s" % rpc_obj.__dict__)
        logger.debug("GET PLATFORM resources slot %s response %s" % (slot, rpc_obj.data_xml)) 


    except Exception:
        logger.debug("caught exception")

def main():
    command_line_args = parse_args()
    user = command_line_args.user
    password = command_line_args.password 
    host = command_line_args.host
    port = 22
    

    # output of csr_connect is m
    with csr_connect(host, port=port, user=user, password=password) as m:
        do_show_cpu_process_history(m)
        




if __name__ == '__main__':
    main()
    
