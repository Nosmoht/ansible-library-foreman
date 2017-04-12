#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage Foreman environment resources.
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
module: foreman_environment
short_description: Manage Foreman Environment using Foreman API v2
description:
- Create and delete Foreman Environments using Foreman API v2
options:
  name:
    description: Name of environment
    required: true
  state:
    description: State of environment
    required: false
    default: present
    choices: ["present", "absent"]
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
- name: Ensure Production environment is present
  foreman_environment:
    name: Production
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

import logging

def get_organization_ids(module, theforeman, organizations):
    result = []
    for i in range(0, len(organizations)):
        try:
            organization = theforeman.search_organization(data={'name': organizations[i]})
            if not organization:
                module.fail_json('Could not find Organization {0}'.format(organizations[i]))
            result.append(organization.get('id'))
        except ForemanError as e:
            module.fail_json('Could not get Organizations: {0}'.format(e.message))
    return result


def get_location_ids(module, theforeman, locations):
    result = []
    for i in range(0, len(locations)):
        try:
            location = theforeman.search_location(data={'name':locations[i]})
            if not location:
                module.fail_json('Could not find Location {0}'.format(locations[i]))
            result.append(location.get('id'))
        except ForemanError as e:
            module.fail_json('Could not get Locations: {0}'.format(e.message))
    return result


def ensure(module):
    name = module.params['name']
    state = module.params['state']
    organizations = module.params['organizations']
    locations = module.params['locations']

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

    data = {'name': name}

    try:
        env = theforeman.search_environment(data=data)
    except ForemanError as e:
        module.fail_json(msg='Could not get environment: {0}'.format(e.message))
        
    if organizations:
         data['organization_ids'] = get_organization_ids(module, theforeman, organizations)

    if locations:
         data['location_ids'] = get_location_ids(module, theforeman, locations)


    if not env and state == 'present':
        try:
            env = theforeman.create_environment(data=data)
            return True, env
        except ForemanError as e:
            module.fail_json(msg='Could not create environment: {0}'.format(e.message))

    if env and state == 'absent':
        try:
            env = theforeman.delete_environment(id=env.get('id'))
            return True, env
        except ForemanError as e:
            module.fail_json(msg='Could not delete environment: {0}'.format(e.message))

    return False, env


def main():
    logging.basicConfig(filename='/tmp/ansible.log', level=logging.DEBUG)
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            organizations=dict(type='list', required=False),
            locations=dict(type='list', required=False),
            foreman_host=dict(type='str', default='127.0.0.1'),
            foreman_port=dict(type='str', default='443'),
            foreman_user=dict(type='str', required=True),
            foreman_pass=dict(type='str', required=True, no_log=True),
            foreman_ssl=dict(type='bool', default=True)
        ),
    )

    if not foremanclient_found:
        module.fail_json(msg='python-foreman module is required. See https://github.com/Nosmoht/python-foreman.')

    changed, env = ensure(module)
    module.exit_json(changed=changed, environment=env)


from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
