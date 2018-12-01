#!/usr/bin/env python

from __future__ import print_function, unicode_literals
import re
import os
from ConfigParser import SafeConfigParser
from getpass import getpass
import sys

def load_devices(device_file):
    devices = SafeConfigParser(allow_no_value=True)
    devices.read([device_file])
    return devices

def load_config(configfile = "scripts.cfg"):
    config = SafeConfigParser(allow_no_value=True)
    config.read([configfile, os.path.expanduser('~/scripts.cfg')])
    return config

def clean_device(device):
    del device['ns_extra']
    return device

def create_devices(device_file, config, devicegroup):
    #  Load config file
    username = ""
    password = ""
    enable = ""
    devices = list()

    devices_conf = load_devices(device_file)

    logging = False
    logdir = "."
    storage = ""
    #  Read global config
    for c in config.items('global'):
        if c[0] == 'username':
            username = c[1]
        elif c[0] == 'password':
            password = c[1]
        elif c[0] == 'enable':
            enable = c[1]
        elif c[0] == 'logging':
            if re.match("1|on|true|yes", c[1], re.I):
                logging = True
        elif c[0] == 'logdir':
            logdir = c[1]
        elif c[0] == 'storage':
            storage = c[1]
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
    if storage == "":
        print("Please specify storage URL. e.g: ftp://1.1.1.1 (if empty, then assuming it's not needed)")
        storage = raw_input("storage URL: ")
    if len(storage)>1:
        if storage[-1] != "/":
            storage+="/"
    #  Load switches from inventory
    try:
        if re.match("asa-.*", devicegroup):
            devicetype = "cisco_asa"
        elif re.match("telnet-.*", devicegroup):
            devicetype = "cisco_ios_telnet"
        else:
            devicetype = "cisco_ios"
        for device in devices_conf.items(devicegroup):
            d={'device_type'        : devicetype,
               'host'               : device[0],
               'username'           : username,
               'password'           : password,
               'secret'             : enable,
               'global_delay_factor': 2,
               'ns_extra'           : {'storage' : storage},
              }
            if logging:
                d['session_log'] = "%s/%s.log" % (logdir,device[0])
                d['session_log_file_mode'] = "append"
            devices.append(d)

    except Exception, e:
        print("Configread: %s" % e)

    return devices
