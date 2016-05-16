#!/usr/bin/env python
#-*- coding:utf-8 -*-

'''
Based on Etcd structure which root key is hostvars, hostvars will return

    "hostvars": {
        "192.168.1.182": {
            "labels": {
                "redis": ""
            },
            "hostname": "m-web-1-182-prd"
        },
        "192.168.1.215": {
            "hostname": "www-db-1-215-prd"
        },
    ...
'''

import yaml
import json
import etcd

class EtcdInventory():

    def __init__(self):
        self.inventory = {}
        config = self.read_settings()
        client = etcd.Client(host=config.get('etcd_host'), port=int(config.get('etcd_port')))
        self.get_hostvars(client)
        self.iterate_hosts()
        print json.dumps(self.inventory)

    def assemble_elements(self, my_string):
        if my_string is None:
            return []
        else:
            elements = my_string.replace('-','.').split('.')
            elements = filter(lambda s: not str(s).isdigit(), elements)
            return elements

    def read_settings(self):
        config = yaml.safe_load(open("vars/etcd_host.yml"))
        return config

    def get_hostvars(self, etcd):
        # hostvars is inventory _meta
        my_hostvars = etcd.read('/hostvars', recursive=True)
        self.hostvars = self.parse_hostvars(my_hostvars._children)
        self.inventory["_meta"] = {'hostvars': self.hostvars}

    def parse_hostvars(self, data):
        hostvars = {}
        for d in data:
            key = d['key'].split('/')[-1]
            if key == '':
                key = '/'
            if 'dir' in d and d['dir'] and 'nodes' in d:
                hostvars[key] = self.parse_hostvars(d['nodes'])
            else:
                if 'value' not in d:
                    d['value'] = ''
                hostvars[key] = d['value']
        return hostvars

    def iterate_hosts(self):
        ''' iterate hosts( i.e. ip_address) contains 2 parts '''
        for (ip_address, value) in self.hostvars.items():
            if isinstance(value, dict):
                # part 1: hostname as group name, One-to-One
                if(value.get('hostname') != 'localhost'):
                    self.inventory[value.get('hostname')] = { "hosts": [ip_address] }
                # part 2: self defined elements as group name, Many-to-Many
                elements = []
                if(value.get('labels')):
                    my_labels = value.get('labels').keys()
                    elements += my_labels
                elements = elements + self.assemble_elements(value.get('hostname'))
                for my_element in elements:
                    self.inventory.setdefault(my_element, {})
                    self.inventory[my_element].setdefault("hosts", []).append(ip_address)
                    host_list = list(set(self.inventory[my_element]["hosts"]))
                    self.inventory[my_element] = { "hosts" : host_list }
            else:
                continue

# Run
EtcdInventory()
