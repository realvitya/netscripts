#!/usr/bin/env python
###############################################
# Dot1x cleaning from switches                #
###############################################

from __future__ import print_function, unicode_literals
import threading
import re
import os
from multiprocessing.pool import ThreadPool
from ConfigParser import SafeConfigParser
from getpass import getpass
from netmiko import ConnectHandler
import signal
import sys

def worker(device):
    global logging
    global dryrun

    templatescleared = False
    descriptions = dict()
    try:
        conn = ConnectHandler(**device)
        conn.enable()
        print("%s - OK" % device['host'])

        conn.disconnect()

    except Exception, e:
        print("%s - error: %s" % (device['host'],e))

def load_devices(device_file):
    devices = SafeConfigParser(allow_no_value=True)
    devices.read([device_file])
    return devices

def load_config():
    config = SafeConfigParser(allow_no_value=True)
    config.read(['scripts.cfg',os.path.expanduser('~/clicol.cfg')])
    return config

def main():
    global logging
    global dryrun

    signal.signal(signal.SIGPIPE, signal.SIG_DFL) # IOError: Broken pipe
    signal.signal(signal.SIGINT, signal.SIG_DFL) # KeyboardInterrupt: Ctrl-C
    devices_conf = load_devices("devices.txt")
    config = load_config()
    devices = list()
    numthreads = 4
    logging = True
    logdir = "."
    dryrun = True
    helptext = """
Help:
    Check if device is reachable and credentials are valid
cmd [-f] -g {groupname}
    -f         : force change on devices
    -g [group] : use group from devices.txt
Example:

    cmd -f -g switches
"""


    #  Load config file
    username = ""
    password = ""
    enable = ""

    #  Read arguments
    try:
        if len(sys.argv) > 1:
            while len(sys.argv) > 1:
                if sys.argv[1] == "-f":
                    dryrun = False
                    del sys.argv[1]
                elif sys.argv[1] == "-g":
                    devicegroup = sys.argv[2]
                    del sys.argv[1]
                    del sys.argv[1]
                else:
                    print(helptext)
                    return 1
        else:
            print(helptext)
            return 1
    except:
        print(helptext)
        return 1

    #  Read global config
    for c in config.items('credentials'):
        if c[0] == 'username':
            username = c[1]
        elif c[0] == 'password':
            password = c[1]
        elif c[0] == 'enable':
            enable = c[1]
    if username == "":
        username = raw_input("Username: ")
    if password == "":
        password = getpass()
    if enable == "":
        enable = getpass("Enable: ")

    #  Load switches from inventory
    try:
        for device in devices_conf.items(devicegroup):
            d={'device_type' : 'cisco_ios',
               'host' : device[0],
               'username' : username,
               'password' : password,
               'secret'   : enable,
               'global_delay_factor': 2,
               #'session_log': "%s/%s.log" % (logdir,device[0]),
               #'session_log_file_mode' : "append",
              }
            if logging:
                d['session_log'] = "%s/%s.log" % (logdir,device[0])
                d['session_log_file_mode'] = "append"
            devices.append(d)

    except Exception, e:
        print(e)



    threads = ThreadPool(numthreads)
    results = threads.map(worker, devices)

    threads.close()
    threads.join()

if __name__ == "__main__":
    main()
