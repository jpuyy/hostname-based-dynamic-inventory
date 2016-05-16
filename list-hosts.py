#!/usr/bin/env python
#-*- coding:utf-8 -*-

import etcd
import yaml

def parse_hostvars(data):
    hostvars = {}
    for d in data:
        key = d['key'].split('/')[-1]
        if key == '':
            key = '/'
        if 'dir' in d and d['dir'] and 'nodes' in d:
            hostvars[key] = parse_hostvars(d['nodes'])
        else:
            if 'value' not in d:
                d['value'] = ''
            hostvars[key] = d['value']
    return hostvars

def read_settings():
    config = yaml.safe_load(open("vars/etcd_host.yml"))
    return config

def main():
    config = read_settings()
    client = etcd.Client(host=config.get('etcd_host'), port=int(config.get('etcd_port')))
    my_hostvars = client.read('/hostvars', recursive=True)
    hostvars = parse_hostvars(my_hostvars._children)
    for (ip, value) in hostvars.items():
        if value and type(value) is dict and value.has_key('hostname'):
            print ip + ' ' + value['hostname']
        else:
            continue

if __name__ == '__main__':
    main()
