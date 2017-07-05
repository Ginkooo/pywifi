#!/usr/bin/python3

import sys
import os
import subprocess
import re

CONFIG_FILE = '/etc/wifi.conf'

IFACE = 'wlp7s0'

def log(message):
    if '-v' in sys.argv:
        print(message)

def is_root():
    return True if 'root' in subprocess.check_output(['whoami']).decode('utf-8') else False

def scan_for_networks():
    try:
        output = subprocess.check_output(['iwlist', IFACE, 'scanning']).decode('utf-8')
    except:
        print('There was a problem with iwlist, try retrying...')
        exit(2)
    return output

def get_networks(scan_results):
    #First is "scanning complete"
    networks = re.split('Cell\s\d+\s\-\s', scan_results)[1:]
    ret = []
    for network in networks:
        info = 0
        for line in network.splitlines():
            line = line.strip()
            if line.startswith('Address'):
                log('reading address')
                _, macaddr = line.split(':', 1)
                macaddr = macaddr.strip().strip('"')
                info = info + 1
            if line.startswith('ESSID'):
                log('reading ssid')
                _, ssid = line.split(':', 1)
                ssid = ssid.strip().strip('"')
                info = info + 1
            if line.startswith('Encryption'):
                log('reading encryption')
                _, encryption = line.split(':', 1)
                open = True if encryption == 'off' else False
                info = info + 1
        if info != 3:
            print('Not enough network information, ' + str(info) + ' readed')
            continue
        ret.append({
            'mac': macaddr,
            'ssid': ssid,
            'open': open
            })
    return ret

def get_saved_networks():
    if not os.path.exists(CONFIG_FILE):
        return []
    ret = []
    with open(CONFIG_FILE, 'r') as f:
        for line in f.readlines():
            ssid, mac, password = line.split(';')
            ret.append({
                'ssid': ssid,
                'mac': mac,
                'password': password
                });
    return ret

def is_network_saved(network, saved_networks):
    saved = False
    for saved_network in saved_networks:
        if network['mac'] == saved_network['mac']:
            saved = True
            break
    return saved

def choose_network(networks, saved_networks):
    for i, network in enumerate(networks):
        saved = is_network_saved(network, saved_networks)
        print('[' + str(i) + '] - ' + network['ssid'] + ' (' + network['mac'] + ')' + (' (open)' if network['open'] else '') + (' (saved)' if saved else ''))
    choice = int(input('Choose network to connect: '))
    return networks[choice]

def connect(network, password=None):
    print('Trying to connect {} with password {}'.format(network['ssid'], password))
    if not password:
        retcode = subprocess.call(['nmcli', 'dev', 'wifi', 'connect', network['ssid']])
        if retcode:
            raise RuntimeError('Couldnt connect')
        return True
    retcode = subprocess.call(['nmcli', 'dev', 'wifi', 'connect', network['ssid'], 'password', password])
    if retcode:
        raise RuntimeError('Couldnt connect')
    return True

def save(network, password):
    with open(CONFIG_FILE, 'a') as f:
        f.write(network['ssid'] + ';' + network['mac'] + ';' + password + '\n')

if __name__ == '__main__':
    if not is_root():
        print("Root access required")
        exit(1)
    scan_results = scan_for_networks()
    networks = get_networks(scan_results)
    saved_networks = get_saved_networks()
    network = choose_network(networks, saved_networks)
    if network['open']:
        connect(network)
        exit()
    if is_network_saved(network, saved_networks):
        for net in saved_networks:
            if net['mac'] == network['mac']:
                password = net['password']
    try:
        password
    except NameError:
        password = input('Type password for ' + network['ssid'] + ': ')
    success = connect(network, password)
    if success and not is_network_saved(network, saved_networks):
        save(network, password)
