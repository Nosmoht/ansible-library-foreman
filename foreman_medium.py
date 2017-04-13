#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage Foreman medium resources.
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
module: foreman_medium
short_description: Manage Foreman media using Foreman API v2
description:
- Create, update and delete Foreman media using Foreman API v2
options:
  name:
    description:
    - Medium name, a combination of name '*' and state 'absent' can be used to clean up, by deleting all present media
    required: true
  path:
    description:
    - The path to the medium, can be a URL or a valid NFS server (exclusive of the architecture).
    required: true
  os_family:
    description:
    - Operating system family
    required: false
  state:
    description:
    - Medium state, , a combination of name '*' and state 'absent' can be used to clean up, by deleting all present media
    required: false
    default: 'present'
    choices: ['present', 'absent']
  foreman_host:
    description:
    - Hostname or IP address of Foreman system
    required: false
    default: 127.0.0.1
  foreman_port:
    description:
    - Port of Foreman API
    required: false
    default: 443
  foreman_user:
    description:
    - Username to be used to authenticate on Foreman
    required: true
  foreman_pass:
    description:
    - Password to be used to authenticate user on Foreman
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
- name: Medium
  foreman_medium:
    name: CentOS mirror
    path: http://mirror.centos.org/centos/$version/os/$arch
    os_family: RedHat
    state: present
    foreman_user: admin
    foreman_pass: secret
    foreman_host: foreman.example.com
    foreman_port: 443
'''

try:
    from foreman.foreman import *

    foremanclient_found = True
except ImportError:
    foremanclient_found = False


def ensure(module):
    name = module.params['name']
    path = module.params['path']
    state = module.params['state']
    os_family = module.params['os_family']

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


    if name == '*' and state == 'absent':
        try:
            all_media_list = theforeman.get_resources(resource_type=MEDIA)
            for element in all_media_list:
                theforeman.delete_medium(id=element.get('id'))
            return True, all_media_list
        except ForemanError as e:
            module.fail_json(msg='Error in deleting all existing media: {0}'.format(e.message))

    try:
        medium = theforeman.search_medium(data=data)
    except ForemanError as e:
        module.fail_json(msg='Could not get medium: {0}'.format(e.message))

    data['path'] = path
    data['os_family'] = os_family

    if not medium and state == 'present':
        try:
            medium = theforeman.create_medium(data=data)
            return True, medium
        except ForemanError as e:
            module.fail_json(msg='Could not create medium: {0}'.format(e.message))

    if medium:
        if state == 'absent':
            try:
                medium = theforeman.delete_medium(id=medium.get('id'))
                return True, medium
            except ForemanError as e:
                module.fail_json('Could not delete medium: {0}'.format(e.message))
        if medium.get('path') != path or medium.get('os_family') != os_family:
            try:
                medium = theforeman.update_medium(id=medium.get('id'), data=data)
                return True, medium
            except ForemanError as e:
                module.fail_json(msg='Could not update medium: {0}'.format(e.message))

    return False, medium



def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            path=dict(type='str', required=False),
            os_family=dict(type='str', required=False),
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

    changed, medium = ensure(module)
    module.exit_json(changed=changed, medium=medium)


from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()