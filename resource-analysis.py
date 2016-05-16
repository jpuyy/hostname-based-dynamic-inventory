#!/usr/bin/env python
#-*- coding:utf-8 -*-

import yaml
import json
import etcd

class ResourceAnalysis():

    def __init__(self):
        self.counter = {}
        config = self.read_settings()
        client = etcd.Client(host=config.get('etcd_host'), port=int(config.get('etcd_port')))
        self.get_hostvars(client)
        self.iterate_hosts()
        print json.dumps(self.counter)

    def read_settings(self):
        config = yaml.safe_load(open("vars/etcd_host.yml"))
        return config

    def get_hostvars(self, etcd):
        my_hostvars = etcd.read('/hostvars', recursive=True)
        self.hostvars = self.parse_hostvars(my_hostvars._children)

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

    def pick_project(self, hostname): 
        project = hostname.replace('.','-').split('-')[0]
        return project

    def iterate_hosts(self):
        ''' iterate hosts( i.e. ip_address) '''
        for (ip_address, value) in self.hostvars.items():
            if isinstance(value, dict):
                hostname=value.get('hostname')
                if hostname is not None and '.' in hostname:
                    project = self.pick_project(hostname)
                    self.counter.setdefault(project, 0)
                    self.counter[project] += 1
            else:
                continue

# Run
ResourceAnalysis()
