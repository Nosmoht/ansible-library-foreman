#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage Foreman operating system resources.
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: foreman_operatingsystem
short_description:
- Manage Foreman Operatingsystems using Foreman API v2.
description:
- Create, update and and delete Foreman Operatingsystems using Foreman API v2
options:
  description:
    description: OS description
    required: false
    default: None
  name:
    description: OS name
    required: true
  major:
    description: OS major version
    required: true
  minor:
    description: OS minor version
    required: false
    default: None
  release_name:
    description: Release name
    required: false
    default: None
  state:
    description: OS state
    required: false
    default: 'present'
    choices: ['present', 'absent']
  foreman_host:
    description: Hostname or IP address of Foreman system
    required: false
    default: 127.0.0.1
  foreman_port:
    description: Port of Foreman API
    required: false
    default: 443
  foreman_user:
    description: Username to be used to authenticate on Foreman
    required: true
  foreman_pass:
    description: Password to be used to authenticate user on Foreman
    required: true
  foreman_ssl:
    description: Enable SSL when connecting to Foreman API
    required: false
    default: true
notes:
- Requires the python-foreman package to be installed. See https://github.com/Nosmoht/python-foreman.
version_added: "2.0"
author: "Thomas Krahn (@nosmoht)"
'''

EXAMPLES = '''
- name: Ensure CoreOS 607.0.0
  foreman_operatingsystem:
    name: CoreOS 607.0.0
    architectures:
    - x86_64
    description: CoreOS Current stable
    media:
    - CoreOS mirror
    major: 607
    minor: 0.0
    ptables:
    - CoreOS default fake
    state: present
    foreman_host: 127.0.0.1
    foreman_port: 443
    foreman_user: admin
    foreman_pass: secret
'''

try:
    from foreman.foreman import *

    foremanclient_found = True
except ImportError:
    foremanclient_found = False


def list_to_dict_list(alist, key):
    result = []
    if alist:
        for item in alist:
            result.append({key: item})
    return result


def dict_list_to_list(alist, key):
    result = list()
    if alist:
        for item in alist:
            result.append(item.get(key, None))
    return result


def equal_dict_lists(l1, l2, compare_key='name'):
    s1 = set(dict_list_to_list(alist=l1, key=compare_key))
    s2 = set(dict_list_to_list(alist=l2, key=compare_key))
    return s1.issubset(s2) and s2.issubset(s1)


def get_resources(resource_type, resource_specs):
    result = []
    for item in resource_specs:
        search_data = dict()
        if isinstance(item, dict):
            for key in item:
                search_data[key] = item[key]
        else:
            search_data['name'] = item
        try:
            resource = theforeman.search_resource(resource_type=resource_type, data=search_data)
            if not resource:
                module.fail_json(
                    msg='Could not find resource type {resource_type} defined as {spec}'.format(
                        resource_type=resource_type,
                        spec=item))
            result.append(resource)
        except ForemanError as e:
            module.fail_json(msg='Could not search resource type {resource_type} defined as {spec}: {error}'.format(
                resource_type=resource_type, spec=item, error=e.message))
    return result


def ensure():
    comparable_keys = ['description', 'family', 'major', 'minor', 'release_name']
    name = module.params['name']
    state = module.params['state']

    data = dict(name=name)
    data['major'] = module.params['major']

    try:
        os = theforeman.search_operatingsystem(data=data)
        if os:
            os = theforeman.get_operatingsystem(id=os.get('id'))
    except ForemanError as e:
        module.fail_json(msg='Could not get operatingsystem: {0}'.format(e.message))

    if state == 'absent':
        if os:
            try:
                os = theforeman.delete_operatingsystem(id=os.get('id'))
                return True, os
            except ForemanError as e:
                module.fail_json(msg='Could not delete operatingsystem: {0}'.format(e.message))

        return False, os

    data['architectures'] = get_resources(resource_type='architectures', resource_specs=module.params['architectures'])
    data['description'] = module.params['description']
    data['family'] = module.params['family']
    data['minor'] = module.params['minor']
    if module.params['media']:
        data['media'] = get_resources(resource_type='media', resource_specs=module.params['media'])

    if module.params['ptables']:
        data['ptables'] = get_resources(resource_type='ptables', resource_specs=module.params['ptables'])
    data['release_name'] = module.params['release_name']

    if not os:
        try:
            os = theforeman.create_operatingsystem(data=data)
            return True, os
        except ForemanError as e:
            module.fail_json(msg='Could not create operatingsystem: {0}'.format(e.message))

    if (not all(data[key] == os.get(key, data[key]) for key in comparable_keys)) or (
            not equal_dict_lists(l1=data.get('architectures', None), l2=os.get('architectures', None))) or (
            not equal_dict_lists(l1=data.get('media', None), l2=os.get('media', None))) or (
            not equal_dict_lists(l1=data.get('ptables', None), l2=os.get('ptables', None))):
        try:
            os = theforeman.update_operatingsystem(id=os.get('id'), data=data)
            return True, os
        except ForemanError as e:
            module.fail_json(msg='Could not update operatingsystem: {0}'.format(e.message))

    return False, os


def main():
    global module
    global theforeman

    module = AnsibleModule(
        argument_spec=dict(
            architectures=dict(type='list', required=False),
            description=dict(type='str', required=False),
            family=dict(type='str', required=False),
            major=dict(type='str', required=False),
            media=dict(type='list', required=False),
            minor=dict(type='str', required=False),
            name=dict(type='str', required=True),
            ptables=dict(type='list', required=False),
            release_name=dict(type='str', required=False),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            foreman_host=dict(type='str', default='127.0.0.1'),
            foreman_port=dict(type='str', default='443'),
            foreman_user=dict(type='str', required=True),
            foreman_pass=dict(type='str', required=True, no_log=True),
            foreman_ssl=dict(type='bool', default=True)
        ),
    )

    if not foremanclient_found:
        module.fail_json(msg='python-foreman module is required. See https://github.com/Nosmoht/python-foreman.')

    foreman_host = module.params['foreman_host']
    foreman_port = module.params['foreman_port']
    foreman_user = module.params['foreman_user']
    foreman_pass = module.params['foreman_pass']
    foreman_ssl = module.params['foreman_ssl']

    theforeman = Foreman(hostname=foreman_host,
                         port=foreman_port,
                         username=foreman_user,
                         password=foreman_pass,
                         ssl=foreman_ssl)

    changed, os = ensure()
    module.exit_json(changed=changed, operatingsystem=os)


from ansible.module_utils.basic import *

if __name__ == '__main__':
main()