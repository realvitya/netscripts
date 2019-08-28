#!/usr/bin/env python
###############################################
# Dot1x cleaning from switches                #
# Currently this script needs custom textfsm  #
# template fot dot1x portlist!                #
# The working template can be obtained:       #
# https://github.com/realvitya/ntc-templates  #
# You just have to keep it in $HOME           #
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


def findallports(conn):
    '''
    Finds all ports on a switch and output is the array of the ports
    '''
    try:
        interfaces = conn.send_command("sh run | i ^interface .*thernet")
        return re.findall('^interface (.*)', interfaces, re.M)

    except Exception, e:
        raise e

def findallportswith(conn, configregex):
    '''
    Finds all ports on a switch with a given configuration
    configregex must be an exact line (can be regex)
    More config line under a single interface is NOT supported
    output is a list of interfaces
    example:
     interface GigabitEthernet1/0/1
      mab

    findallportswith(conn, " mab")
    [('GigabitEthernet1/0/1', ' mab')]
    '''
    interfaces = list()
    interface = ""
    try:
        cinput = conn.send_command("sh run | i ^interface|^%s" % configregex)
        for line in cinput.split("\n"):
            m = re.match('^interface (.*)', line)
            if m:
                #  memorize found interface
                interface = m.group(1)
            m = re.match(configregex, line)
            if m:
                #  found match for config, add interface to output list
                if interface != "":
                    interfaces.append((interface, m.group(0)))

        if len(interfaces)>0:
            return interfaces
        else:
            return None
    except Exception, e:
        return 'error while findallportswitch: %s' % e


def worker(device):
    global logging
    global dryrun

    templatescleared = False
    descriptions = dict()
    try:
        conn = ConnectHandler(**device)
        conn.enable()
        print("%s - connected" % device['host'])

        #  To log:
        conn.send_command("show clock")

        #  Check if we have dot1x enabled ports and save descriptions
        dot1xports = conn.send_command("show dot1x all", use_textfsm=True)
        if type(dot1xports) is not list:
            print("%s has no dot1x ports configured!" % device['host'])
            dot1xports = []
        else:
            dot1xports = [ i['interface'] for i in dot1xports ]
        descout = findallportswith(conn, " description .*")
        for interface, description in descout:
            descriptions[interface] = description

 
        '''  
        Check if we have interface template because then we have to change
        the template itself. Assuming we use only User defined templates.
        Check if we have template and whether it contains dot1x config.
        example:
        show template | i User
        USER_ACCESS_TEMPLATE                           owner      User            
        MULTIAUTH_ACCESS_TEMPLATE                        owner      User

        output: ['USER_ACCESS_TEMPLATE','MULTIAUTH_ACCESS_TEMPLATE']
        '''
        porttemplates = conn.send_command("sh template | i User")
        porttemplates = re.findall('^(\w+)\s{2,}.*',porttemplates,re.M)

        if len(porttemplates)>0:
            '''
            We have templates. So we check if we have dot1x in them:
            show template interface source user TEMPLATENAME

            '''
            for template in porttemplates:
                templateconfig = conn.send_command("show template interface source user %s" % template)
                #if re.search('port-control auto',templateconfig,re.M): #  Do we have dot1x enabled?
                if True:
                    '''
                    Clean dot1x from template
                    It must be access-session commands:
                     dot1x pae authenticator
                     dot1x timeout tx-period 10
                     mab
                     access-session control-direction in
                     access-session closed
                     access-session port-control auto
                     service-policy type control subscriber SOMEPOLICY

                    To remove:
                     no access-session port-control
                     no access-session control-direction
                     no access-session closed
                     no mab
                     no dot1x pae
                     no dot1x timeout tx-period
                     no service-policy type control subscriber
                    '''
                    #print("%s has dot1x commands" % template)
                    commands = ['template %s' % template,
                                'no access-session port-control',
                                'no access-session control-direction',
                                'no access-session closed',
                                'no access-session host-mode',
                                'no mab',
                                'no dot1x pae',
                                'no dot1x timeout tx-period',
                                'no service-policy type control subscriber',
                               ]
                    if dryrun: #  don't run the commands, just print them
                        for command in commands:
                            print("%s - cmd: %s" % (device['host'],command))
                    else:
                        # run commands
                        conn.config_mode()
                        conn.send_config_set(commands,exit_config_mode=False)
                        conn.exit_config_mode()


                    templatescleared = True

        '''  
        Check if we have IBNS2.0 service templates, class and policy maps
        These must be removed in this order:
        1. policy maps
        2. class maps
        3. service templates
        example:
        SWITCH#sh run | i policy-map type control subscriber              
        policy-map type control subscriber ACCESS_POLICY
        output: ['USER_ACCESS_TEMPLATE','MULTIAUTH_ACCESS_TEMPLATE']
        '''
        controlpolicies = conn.send_command("sh run | i ^policy-map type control subscriber")
        controlpolicies = re.findall('policy-map type control subscriber ([0-9a-zA-Z_/]+)',controlpolicies,re.M)
        #  Clear policies from interfaces
        for cp in controlpolicies:
            cp_interfaces = findallportswith(conn, ' service-policy type control subscriber %s' % cp)
            #print("cp: %s" % cp)
            #print("cpi: %s" % cp_interfaces)
            if type(cp_interfaces) is list:
                if not dryrun:
                    conn.config_mode()
                for (interface, c) in cp_interfaces:
                    commands = ['interface %s' % interface,
                                'no service-policy type control subscriber',
                               ]
                    if dryrun:
                        for command in commands:
                            print("%s - cmd: %s" % (device['host'],command))
                    else:
                        # run commands
                        conn.send_config_set(commands,exit_config_mode=False)
                if not dryrun:
                    conn.exit_config_mode()

        #  Clear policies
        commands = list()
        for cp in controlpolicies:
            commands.append('no policy-map type control subscriber %s' % cp)
            if dryrun:
                print("%s - cmd: %s" % (device['host'], commands[-1]))
        if len(commands)>0 and not dryrun:
            conn.config_mode()
            conn.send_config_set(commands,exit_config_mode=False)
            conn.exit_config_mode()

        
        #  Clear class-map type control
        classmaps = conn.send_command("sh run | i ^class-map type control subscriber")
        #classmaps = re.findall('class-map type control subscriber (.*)', classmaps,re.M)
        if classmaps != "":
            if not dryrun:
                conn.config_mode()
            for classmap in classmaps.split("\n"):
                commands = 'no %s' %  classmap
                if dryrun:
                    print("%s - cmd: %s" % (device['host'], commands))
                else:
                    conn.send_config_set(commands,exit_config_mode=False)
            if not dryrun:
                conn.exit_config_mode()

        #  Clear service templates
        servicetemplates = conn.send_command("sh run | i ^service-template")
        if servicetemplates != "":
            if not dryrun:
                conn.config_mode()
            for servicetemplate in servicetemplates.split("\n"):
                commands = 'no %s' %  servicetemplate
                if dryrun:
                    print("%s - cmd: %s" % (device['host'], commands))
                else:
                    conn.send_config_set(commands,exit_config_mode=False)
            if not dryrun:
                conn.exit_config_mode()


        #  Check if we have dot1x enabled ports even after clearing templates
        dot1xports = conn.send_command("show dot1x all", use_textfsm=True)
        if type(dot1xports) is not list:
            if not templatescleared:
                print("%s has no dot1x ports configured!" % device['host'])
            else:
                print("%s - dot1x cleared from templates/IBNS2 policies!" % device['host'])
            #  Stop clearing individual interfaces:
            dot1xports = list()

        #  Let's configure individual ports:
        dot1xports = [ i['interface'] for i in dot1xports ]
        '''
        remove dot1x commands and update description
        example:
         authentication control-direction in
         authentication event fail action authorize vlan 88
         authentication event server dead action authorize 
         authentication event no-response action authorize vlan 88
         authentication event server alive action reinitialize 
         authentication order dot1x mab
         authentication port-control auto
         authentication host-mode multi-auth
         mab
         dot1x pae authenticator
         dot1x timeout tx-period 10

        to remove:
         description [original] (Dot1xNR)
         no authentication control-direction
         no authentication event fail
         no authentication event server dead
         no authentication event no-response
         no authentication event server alive
         no authentication order
         no authentication port-control
         no authentication host-mode multi-auth
         no mab
         no dot1x pae
         no dot1x timeout tx-period

        '''
        if not dryrun:
            conn.config_mode()
        for port in dot1xports:
            description = "description User Port (Dot1xNR)"
            if port in descriptions:
                description = descriptions[port]
                if not re.match('.*dot1xnr.*', description, re.I):
                    description += " (Dot1xNR)"
            commands = ['interface %s' % port,
                        description,
                        'no authentication port-control',
                        'no authentication control-direction',
                        'no authentication event fail',
                        'no authentication event server dead',
                        #  on some device the below is working:
                        'no authentication event server dead action authorize',
                        'no authentication event no-response',
                        'no authentication event server alive',
                        'no authentication order',
                        'no authentication host-mode',
                        'no mab',
                        'no dot1x pae',
                        'no dot1x timeout tx-period',
                       ]
            if dryrun:
                for command in commands:
                    print("%s - cmd: %s" % (device['host'],command))
            else:
                conn.send_config_set(commands,exit_config_mode=False)
        if not dryrun:
            conn.exit_config_mode()


        '''
        Remove global dot1x config
        example:
        dot1x system-auth-control
        dot1x guest-vlan supplicant

        to remove:
        no dot1x system-auth-control
        no dot1x guest-vlan supplicant
        '''
        commands = ['no dot1x system-auth-control',
                    'no dot1x guest-vlan supplicant',
                    'no dot1x logging verbose',
                    'no dot1x critical eapol',
                   ]
        if dryrun:
            for command in commands:
                print("%s - cmd: %s" % (device['host'],command))
        else:
            conn.config_mode()
            conn.send_config_set(commands,exit_config_mode=False)
            conn.exit_config_mode()



        '''
        Save config!
        '''
	if dryrun:
	   print("%s - cmd: %s" % (device['host'],"wr m"))
	else:
            conn.send_command("wr mem")

        conn.disconnect()

    except Exception, e:
        print("%s - error: %s" % (device['host'],e))
    finally:
        print("%s - done" % device['host'])

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
    for c in config.items('global'):
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
