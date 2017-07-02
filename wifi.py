#!/usr/bin/python3

import sys
import os
import subprocess

CONF_FILE = '/etc/wifi.conf'

IFACE = 'wlan0'

def get_saved_networks():
    if not os.path.exists(CONF_FILE):
        return {}
    ret = {}
    with open(CONF_FILE, 'r') as f:
        for line in f.readlines():
            ssid, password = line.strip().split(';')
            ret[ssid] = password
    print(ret)
    return ret

def save_network(ssid, password):
    if not os.path.exists(CONF_FILE):
        with open(CONF_FILE, 'w') as f:
            pass
    with open(CONF_FILE, 'a') as f:
        f.write(ssid + ';'+password+'\n')

def connect_to(ssid, password):
    print('Trying to connect ', ssid, ' with password ', password)
    code = subprocess.call(['nmcli', 'dev', 'wifi', 'connect', ssid, 'password', password, '--timeout', '10'])
    if code:
        return False
    return True

def get_ssid_list():
    ret = []
    proc = subprocess.Popen(['iwlist', IFACE, 'scanning'], stdout=subprocess.PIPE)
    if proc.returncode:
        raise Error("Can't access network interface card")
    while(True):
        line = proc.stdout.readline().decode('utf-8')
        if 'ESSID' in line:
            _, ssid = line.split(':')
            ssid = ssid.strip().strip('"')
            ret.append(ssid)
        if not line:
            break
    return ret

if __name__ == '__main__':
    if not 'root' in subprocess.check_output(['whoami']).decode('utf-8'):
        print('Root required')
        exit()

    ssids = get_ssid_list()
    saved_networks = get_saved_networks()
    for i, ssid in enumerate(ssids):
        print('['+str(i)+'] - ' + ssid + (' (saved)' if ssid in saved_networks else ''))
    choice = int(input('Choose network to connect to: '))
    ssid = ssids[choice]
    if not ssid in saved_networks:
        password = input('Type your password for ' + ssid + ': ' )
        connect_to(ssid, password)
        save_network(ssid, password)
    else:
        connect_to(ssid, saved_networks[ssid])
