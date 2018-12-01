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
from netscript import create_devices
from netscript import load_config
from netscript import clean_device

def worker(device):
    global dryrun

    try:
        storage = device['ns_extra']['storage']
        destination = storage + device['host']

        device = clean_device(device)
        conn = ConnectHandler(**device)
        conn.enable()
	print("%s - connected" % device['host'])

        conn.send_command("write memory")
        if device['device_type'] != "cisco_asa":
            # disable file prompt
            conn.send_config_set("file prompt quiet")

            out=conn.send_command("copy start %s" % destination + ".cfg")
            if re.match('.*bytes copied .*',out,re.S):
                print("%s - config saved" % device['host'])
            out=conn.send_command("copy vlan.dat %s" % destination + "-vlan.dat")
            if re.match('.*bytes copied .*',out,re.S):
                print("%s - vlan.dat saved" % device['host'])
            out=conn.send_command("copy cat4000_flash:/vlan.dat %s" % destination + "-vlan.dat")
            if re.match('.*bytes copied .*',out,re.S):
                print("%s - vlan.dat saved" % device['host'])
            
            conn.send_config_set("no file prompt")
        else: #  ASA
            out=conn.send_command("copy /noconfirm running-config %s" % destination + ".cfg")
            if re.match('.*bytes copied .*',out,re.S):
                print("%s - config saved" % device['host'])
            out=conn.send_command("changeto system")
            if not re.match(".*ERROR:.*|.*Command not valid.*", out, re.S): #  successfully went into system context
                conn.send_command("write memory")
                destination += "-system"
                out=conn.send_command("copy /noconfirm running-config %s" % destination + ".cfg")
                if re.match('.*bytes copied .*',out,re.S):
                    print("%s - system config saved" % device['host'])

        conn.disconnect()

    except Exception, e:
        print("%s - error: %s" % (device['host'],e))

def main():
    global dryrun

    signal.signal(signal.SIGPIPE, signal.SIG_DFL) # IOError: Broken pipe
    signal.signal(signal.SIGINT, signal.SIG_DFL) # KeyboardInterrupt: Ctrl-C
    
    numthreads = 10

    dryrun = True
    helptext = """
Help:
    Backup device config + vlan.dat
    supporting : Cisco switches/routers/ASA
cmd [-f] -g {groupname}
    -f         : force change on devices
    -g [group] : use group from devices.txt
Example:

    cmd -f -g switches
"""


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

    config = load_config()
    devices = create_devices("devices.txt", config, devicegroup)

    threads = ThreadPool(numthreads)
    results = threads.map(worker, devices)

    threads.close()
    threads.join()

if __name__ == "__main__":
    main()
