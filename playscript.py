#!/usr/bin/env python
############################################################################
# Playing scripts from script file                                         #
# Usage:                                                                   #
# Every line is a configuration item which will be executed in config mode #
# Lines starting with '#' are comment, script doesn't bother               #
# Empty lines are ignored                                                  #
# Lines starting with '!' are commands for the script.                     #
# Commands:                                                                #
# !clear {something} : script will run config "no {^something.*}           #
#                                                                          #
# !getvar {varname} {regex (var value)}:                                   #
#                      get var value and put into varname                  #
#                      This allows for dynamic variable management         #
#                                                                          #
# !quit              : quit the script immediately                         #
#                      (good for testing/tshooting)                        #
# !replace "{search}" "{replace}"      :                                   #
#                      replace input with defined string                   #
#                      example:                                            #
#   !replace "privilege ([a-z]+) level [0-9]+ (.*)" "privilege $1 reset $2"#
# !clear {something} : script will run config "no {^something.*}           #
#                                                                          #
# #variable# are variables which will be substitued with something         #
# Variables are read from scripts.cfg [{scriptname}-variables] section     #
# {scriptname} is the name of the script without file extension            #
# [setlocal-variables]                                                     #
# localuser=admin                                                          #
# localpasswd=secret                                                       #
############################################################################

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
    global script

    templatescleared = False
    descriptions = dict()
    try:
        conn = ConnectHandler(**device)
        conn.enable()
        print("%s - logged in" % device['host'])
        #conn.config_mode()
        #  For dynamic variables:
        variables = dict()
        config_apply = list()

        for line in script:
            '''
            Check if we have command.
            Commands:
             !quit  : quit session (good for tshooting)
             !clear : find config to remove. 
                      !clear tacacs-server
                      This will search for ^tacacs-server 1.1.1.1 and run:
                      no tacacs-server 1.1.1.1
             !getvar: get dynamic variable to use as replace later
                      !getvar {varname} {regex with one selector}
                      !getvar mgmt logging device-id ipaddress (.*)
                      will load to variables['mgmt']='management'
             !replace:
                      !replace "privilege ([a-z]+) level [0-9]+ (.*)" "privilege $1 reset $2"
            '''
            match = re.match('^!(clear|getvar|quit|replace)(?: (.*)|$)', line)
            if match:
                command = match.group(1)
                config = match.group(2)
                configs = []

                #  Send collected configs to device before handling commands
                if len(config_apply)>0:
                    out = conn.send_config_set(config_apply,exit_config_mode=False)
                    config_apply = list()
                do = "do "
                if dryrun or device['device_type'] == 'cisco_asa':
                    do = ""
                if command == "clear":
                    configs = conn.send_command(do + "show run | i ^%s" % config).split("\n")
                    configs = ["no %s" % c for c in configs if len(c)>0]
                    #  Append an enter for commands with confirmation (e.g. no username)
                    cout = list()
                    for c in configs:
                        cout.append(c)
                        cout.append("\n")
                    configs = cout
                elif command == "getvar":
                    varmatch = re.match("(\w+) (.*)", config)
                    if not varmatch:
                        print("Error - getvar (%s was not understood)" % config)
                        continue
                    varname = varmatch.group(1)
                    config = varmatch.group(2)
                    #  Take the first line of the output
                    out = conn.send_command(do + "show run | i ^%s" % config).split("\n")[0]
                    m = re.match(config, out)
                    if m:
                        variables[varname] = m.group(1)
                    #  No need to process this command further
                    continue
                elif command == "quit":
                    conn.disconnect()
                    return
                elif command == "replace":
                    #!replace "privilege ([a-z]+) level [0-9]+ (.*)" "privilege $1 reset $2"
                    m=re.match("\"(.*)\" \"(.*)\"",config)
                    if m:
                        search,replace=m.groups()
                        out = conn.send_command(do + "sh run | i ^" + search).split("\n")
                        for line in out:
                            matches = re.match(search, line)
                            if matches:
                                i = 0
                                config = replace
                                for var in matches.groups():
                                    i+=1
                                    config=config.replace("$%d" % i, var)
                                if re.match(".*$[0-9].*",config):
                                    print("Warning: unreplaced vars remained: %s" % config)
                                else:
                                    configs.append(config)
                    else:
                        print("%s - Warning: replace command syntax error: %s" % (device['host'],config))

                else:
                    print("Warning: %s command is unknown" % command)
                    continue

                #  Commands processed, go ahead and run commands
                for variable in variables:
                    configs = [line.replace("#"+variable+"#", variables[variable]) for line in configs]
                for line in configs:
                    if re.match(".*#\w+#.*", line):
                        print("%s - Warning: Unknown variable in \'%s\'" % (device['host'],line))
                        continue
                if dryrun:
                    for config in configs:
                        print("%s - cmd: %s" % (device['host'], config))
                else:
                    out = conn.send_config_set(configs,exit_config_mode=False)
            else:
                #  Process dynamic variables
                for variable in variables:
                    line = line.replace("#"+variable+"#", variables[variable])
                if re.match(".*#\w+#.*", line):
                    print("%s - Warning: Unknown variable in \'%s\'" % (device['host'],line))
                    continue
                if dryrun:
                    print("%s - cmd: %s" % (device['host'], line))
                else:
                    #out = conn.send_config_set(line,exit_config_mode=False)
                    config_apply.append(line)


        if len(config_apply)>0:
            out = conn.send_config_set(config_apply)
        #conn.exit_config_mode()
        conn.disconnect()
        print("%s - done" % device['host'])

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
    global script

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
    Play script on devices
cmd [-f] [-s {scriptfile}]
    -f              : force change on devices
    -g {group}      : use this group from scripts.cfg (run on these devices)
    -s {scriptfile} : play script from this file
                      If not specified, read script from standard input first
Example:

    cmd -f -g all -s cleanaaa.txt
"""


    #  Load config file
    username = ""
    password = ""
    enable = ""

    devicegroup = ""
    scriptfile = ""

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
                elif sys.argv[1] == "-s":
                    scriptfile = sys.argv[2]
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

    #  If we have group specific cred, then overwrite the global ones
    if 'credentials-'+devicegroup in config.sections():
        for c in config.items('credentials-'+devicegroup):
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
        if re.match("asa-.*", devicegroup):
            devicetype = "cisco_asa"
        elif re.match("telnet-.*", devicegroup):
            devicetype = "cisco_ios_telnet"
        else:
            devicetype = "cisco_ios"
        for device in devices_conf.items(devicegroup):
            d={'device_type' : devicetype,
               'host' : device[0],
               'username' : username,
               'password' : password,
               'secret'   : enable,
               'global_delay_factor': 2,
              }
            if logging:
                d['session_log'] = "%s/%s.log" % (logdir,device[0])
                d['session_log_file_mode'] = "append"
            devices.append(d)

    except Exception, e:
        print("Configread: %s" % e)

    try:
        scriptname = scriptfile.split(".")[0]
        scriptfile = file(scriptfile)
        script = [line.rstrip('\n') for line in scriptfile if re.match('^[^#]',line)]

        for variable, value in config.items('variables-' + scriptname):
            script = [line.replace("#"+variable+"#", value) for line in script]

        #for line in script:
        #    print(line)

    except Exception, e:
        print("Fileread: %s" % e)

    threads = ThreadPool(numthreads)
    results = threads.map(worker, devices)

    threads.close()
    threads.join()

if __name__ == "__main__":
    main()
