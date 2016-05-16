#!/usr/bin/env python
#coding=utf-8

import etcd
import json

DOCUMENTATION = '''
---
module: etcd_record
short_description: manage the records in etcd
description:
    - manage the base information of host such as hostname, labels

examples:
    - name: set hostname
      local_action: etcd_record etcd_host=etcd.mysite.io port=4001 host=127.0.0.1 name='hostname' value=localhost

    - name: register service
      local_action: etcd_record etcd_host=etcd.mysite.io port=4001 host=127.0.0.1 name=labels value=redis

    - name: delete hostname
      local_action: etcd_record etcd_host=etcd.mysite.io port=4001 host=127.0.0.1 name='hostname' state=absent

    - name: unregister service
      local_action: etcd_record etcd_host=etcd.mysite.io port=4001 host=127.0.0.1 name=labels value=redis state=absent

    - name: offline host
      local_action: etcd_record etcd_host=etcd.mysite.io port=4001 host=127.0.0.1 name= state=absent
'''

class EtcdClient(object):

    def __init__(self, etcd_host, port):
        self.client = etcd.Client(host=etcd_host, port=port)
        self.changed = False
        self.root_path_tpl = '/hostvars/%s/%s'
        self.hostname = ''

    def _add(self, key, value):
        if(self._exist(key, value) == True):
            pass
        else:
            self.client.write(key, value)
            self.changed = True

    def _remove(self, key):
        try:
            self.client.read(key)
        except (etcd.EtcdKeyNotFound,UnboundLocalError,ValueError):
            pass
        else:
            self.client.delete(key, recursive=True)
            self.changed = True

    def _exist(self, key, value):
        try:
            result = self.client.read(key).value
        except (etcd.EtcdKeyNotFound,UnboundLocalError,ValueError):
            return False
        if result == value:
            return True
        else:
            return False

    def _get(self, key):
        try:
            value = self.client.read(key).value
        except (etcd.EtcdKeyNotFound,UnboundLocalError,ValueError):
            return None
        return value

    def do(self):
        pass

class Hostvars(EtcdClient):

    def __init__(self, module):
        super(Hostvars, self).__init__(module.params['etcd_host'], module.params['port'])
        self.module = module
        self.do()

    def do(self):
        if(self.module.params['host'] != ''):
            key = self.root_path_tpl % (self.module.params['host'], self.module.params['name'])
            if(self.module.params['state'] == 'absent'):
                return self._remove(key)
            else:
                return self._add(key, self.module.params['value'])


class ServiceCenter(EtcdClient):
    def __init__(self, module):
        super(ServiceCenter, self).__init__(module.params['etcd_host'], module.params['port'])
        self.root_path_tpl = '/hostvars/%s/labels/%s'
        self.module = module
        self.do()

    def do(self):
        if(self.module.params['host'] != ''):
            key = self.root_path_tpl % (self.module.params['host'], self.module.params['value'])
            blank_value = ''
            if(self.module.params['state'] == 'absent'):
                return self._remove(key)
            else:
                return self._add(key, blank_value)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            etcd_host = dict(required=True, tpye='str'),
            port = dict(type='int', default=4001),
            host = dict(required=True, type='str'),
            name = dict(required=True, choices=['', 'hostname', 'labels']),
            value = dict(default='', type='str'),
            state = dict(default='present', choices=[ 'present', 'absent', 'fetch' ]),
        )
    )
    name = module.params['name']
    if name == 'labels':
        result = ServiceCenter(module)
    else:
        result = Hostvars(module)
    module.exit_json(changed=result.changed, hostname=result.hostname)

from ansible.module_utils.basic import *
main()
