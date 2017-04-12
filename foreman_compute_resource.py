#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage Foreman compute resource resources.
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
module: foreman_compute_resource
short_description: Manage Foreman Compute resources using Foreman API v2
description:
- Create and delete Foreman Compute Resources using Foreman API v2
options:
  name:
    description: Compute Resource name
    required: true
  datacenter: Name of Datacenter (only for Vmware)
    required: false
    default: None
  description: Description of compute resource
    required: false
    default: None
  password:
    description: Password for Ovirt, EC2, Vmware, Openstack. Secret key for EC2
    required: false
    default: None
  provider:
    description: Providers name (e.g. Ovirt, EC2, Vmware, Openstack, EC2, Google)
    required: false
    default: None
  server:
    description: Hostname of Vmware vSphere system
    required: false
    default: None
  state:
    description: Compute Resource state
    required: false
    default: present
    choices: ["present", "absent"]
  tenant:
    description: Tenant name for Openstack
    required: false
    default: None
  url:
    description: URL for Libvirt, Ovirt, and Openstack
    required: false
    default: None
  user:
    description: Username for Ovirt, EC2, Vmware, Openstack. Access Key for EC2.
    required: false
    default: None
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
- name: Ensure Vmware compute resource
  foreman_compute_resource:
    name: VMware
    datacenter: dc01
    provider: VMware
    server: vsphere.example.com
    url: vsphere.example.com
    user: domain\admin
    password: secret
    state: present
    foreman_user: admin
    foreman_pass: secret
- name: Ensure Openstack compute resource
  foreman_compute_resource:
    name: Openstack
    provider: OpenStack
    tenant: ExampleTenant
    url: https://compute01.example.com:5000/v2.0/tokens
    user: admin
'''

try:
    from foreman.foreman import *
except ImportError:
    foremanclient_found = False
else:
    foremanclient_found = True


def get_provider_params(provider):
    provider_name = provider.lower()

    if provider_name == 'docker':
        return ['password', 'url', 'user']
    elif provider_name == 'ec2':
        return ['access_key', 'password', 'region', 'url', 'user']
    elif provider_name == 'google':
        return ['email', 'key_path', 'project', 'url', 'zone']
    elif provider_name == 'libvirt':
        return ['display_type', 'url']
    elif provider_name == 'ovirt':
        return ['url', 'user', 'password']
    elif provider_name == 'openstack':
        return ['url', 'user', 'password', 'tenant']
    elif provider_name == 'vmware':
        return ['datacenter', 'user', 'password', 'server']
    else:
        return []

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
    provider = module.params['provider']
    description = module.params['description']
    locations = module.params['locations']
    organizations = module.params['organizations']

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

    data = dict(name=name)


    try:
        compute_resource = theforeman.search_compute_resource(data=data)
    except ForemanError as e:
        module.fail_json(msg='Could not get compute resource: {0}'.format(e.message))

    if organizations:
         data['organization_ids'] = get_organization_ids(module, theforeman, organizations)

    if locations:
         data['location_ids'] = get_location_ids(module, theforeman, locations)

    if state == 'absent':
        if compute_resource:
            try:
                compute_resource = theforeman.delete_compute_resource(id=compute_resource.get('id'))
            except ForemanError as e:
                module.fail_json(msg='Could not delete compute resource: {0}'.format(e.message))
            return True, compute_resource

    data['provider'] = provider
    params = get_provider_params(provider=provider) + ['description']
    for key in params:
        data[key] = module.params[key]

    if state == 'present':
        if not compute_resource:
            try:
                compute_resource = theforeman.create_compute_resource(data=data)
            except ForemanError as e:
                module.fail_json(msg='Could not create compute resource: {0}'.format(e.message))
            return True, compute_resource

        # Foreman's API doesn't return the password we can't tell if we need to
        # change it
        data['password'] = None
        if not all(data.get(key, None) == compute_resource.get(key, None) for key in params):
            try:
                compute_resource = theforeman.update_compute_resource(id=compute_resource.get('id'), data=data)
            except ForemanError as e:
                module.fail_json(msg='Could not update compute resource: {0}'.format(e.message))
            return True, compute_resource

    return False, compute_resource


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            access_key=dict(type='str', requireD=False),
            datacenter=dict(type='str', required=False),
            description=dict(type='str', required=False),
            display_type=dict(type='str', required=False),
            email=dict(type='str', required=False),
            key_path=dict(type='str', required=False),
            password=dict(type='str', required=False, no_log=True),
            provider=dict(type='str', required=False),
            region=dict(type='str', required=False),
            server=dict(type='str', required=False),
            url=dict(type='str', required=False),
            user=dict(type='str', required=False),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            tenat=dict(type='str', required=False),
            locations=dict(type='list', required=False),
            organizations=dict(type='list', required=False),
            foreman_host=dict(type='str', default='127.0.0.1'),
            foreman_port=dict(type='str', default='443'),
            foreman_user=dict(type='str', required=True),
            foreman_pass=dict(type='str', required=True, no_log=True),
            foreman_ssl=dict(type='bool', default=True)
        ),
    )

    if not foremanclient_found:
        module.fail_json(msg='python-foreman module is required. See https://github.com/Nosmoht/python-foreman.')

    changed, compute_resource = ensure(module)
    module.exit_json(changed=changed, compute_resource=compute_resource)


from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
