#!/usr/bin/env python

from __future__ import print_function, unicode_literals
import threading
from multiprocessing.pool import ThreadPool
from datetime import datetime
from ConfigParser import SafeConfigParser
from getpass import getpass
from netmiko import ConnectHandler
from int2range import int2range

def worker(device):
    try:
        conn = ConnectHandler(**device)
        print("Connected to %s" % device['host'])
        dot1xports = conn.send_command("show dot1x all", use_textfsm=True)
        #dot1xports = [{'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/1', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'MULTI_DOMAIN', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/2', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/3', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/4', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/5', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/6', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/7', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/8', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/9', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/10', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/11', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/12', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/13', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/14', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'MULTI_DOMAIN', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/15', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/16', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/17', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'MULTI_DOMAIN', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/18', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'MULTI_DOMAIN', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/19', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'MULTI_DOMAIN', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/20', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/21', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'MULTI_DOMAIN', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/22', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/23', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/24', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/26', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/27', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}, {'masreq': '2', 'sysauthcontrol': 'Enabled', 'servertimeout': '0', 'ratelimitperiod': '', 'supptimeout': '30', 'dot1xversion': '3', 'hostmode': 'SINGLE_HOST', 'critical_recovery_delay': '', 'reauthmax': '2', 'quietperiod': '60', 'reauthperiod': '', 'txperiod': '10', 'pae': 'AUTHENTICATOR', 'reauthentication': '', 'interface': 'GigabitEthernet0/28', 'critical_eapol': '', 'controldirection': 'In', 'portcontrol': 'AUTO'}]
        if type(dot1xports) is not list:
            print("%s has no dot1x ports configured!" % device['host'])
            return
        dot1xports = [ i['interface'] for i in dot1xports ]
        print(int2range(dot1xports))
    except Exception, e:
        print(e)

def load_devices(device_file):
    devices = SafeConfigParser(allow_no_value=True)
    devices.read([device_file])
    return devices

def main():
    devices_conf = load_devices("devices.txt")
    devices = list()
    numthreads = 5
    logging = True
    logdir = "."


    username = "nvsu098710"
    password = getpass()

    #  Load switches from inventory
    try:
        types = 'switch'
        for device in devices_conf.items(types):
            if logging:
                devices.append({'device_type' : 'cisco_ios',
                                'host' : device[0],
                                'username' : username,
                                'password' : password,
                                'session_log': "%s/%s.log" % (logdir,device[0]),
                                #'session_log_file_mode' : "append",
                               })
            else:
                devices.append({'device_type' : 'cisco_ios',
                                'host' : device[0],
                                'username' : username,
                                'password' : password,
                               })
    except Exception, e:
        print(e)

    threads = ThreadPool(numthreads)
    results = threads.map(worker, devices)

    threads.close()
    threads.join()

if __name__ == "__main__":
    main()
