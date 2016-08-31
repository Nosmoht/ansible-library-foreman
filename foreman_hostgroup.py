#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage Foreman hostgroup resources.
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
module: foreman_hostgroup
short_description: Manage Foreman Hostgroup using Foreman API v2
description:
- Manage Foreman Hostgroup using Foreman API v2
options:
  architecture:
    description: Architecture name
    required: False
    default: None
  domain:
    description: Domain name
    required: False
    default: None
  environment:
    description: Environment name
    required: False
    default: None
  medium:
    description: Medium name
    required: False
    default: None
  name:
    description: Hostgroup name
    required: True
  operatingsystem:
    description: Operatingsystem name
    required: False
    default: None
  parameters:
    description: List of parameters and values
    required: false
    default: None
  partition_table:
    description: Partition table name
    required: False
    default: None
  root_pass:
    description: root password
    required: false
    default: None
  smart_proxy:
    description: Smart Proxy name
    required: False
    default: None
  subnet:
    description: Subnet name
    required: False
    default: None
  state:
    description: Hostgroup state
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
- name: Ensure Hostgroup
  foreman_hostgroup:
    name: MyHostgroup
    state: present
    architecture: x86_64
    domain: MyDomain
    operatingsystem: MyOS
    subnet: MySubnet
    foreman_host: 127.0.0.1
    foreman_port: 443
    foreman_user: admin
    foreman_pass: secret
'''

try:
    from foreman.foreman import *
except ImportError:
    foremanclient_found = False
else:
    foremanclient_found = True


def get_resource(module, resource_type, resource_func, resource_name, search_title=False):
    """
    Look for a resource within Foreman Database. Return the resource if found or fail.
    If the Resource could not be found by name search by title.

    :param module:
    :param resource_type:
    :param resource_func:
    :param resource_name:
    :return:
    """
    try:
        result = resource_func(data=dict(name=resource_name))
        if not result and search_title:
            result = resource_func(data=dict(title=resource_name))
        if not result:
            module.fail_json(msg='{0} {1} not found'.format(resource_type, resource_name))
    except ForemanError as e:
        module.fail_json(msg='Error while getting {0}: {1}'.format(resource_type, e.message))
    return result


def filter_hostgroup(hg):
    """Filter all _name parameters since we only care about the IDs and convert
    ids to strings since this is what we need to feed back to foreman

    >>> filter_hostgroup({"a_name": "foo", "a_id": 1})
    {'a_id': '1'}
    """
    filtered = {}
    keep = ['title', 'name', 'root_pass']
    for k, v in hg.items():
        if k.endswith('_id') and v is not None:
            filtered[k] = str(v)
        elif k in keep:
            filtered[k] = v
    return filtered


def split_parent(name):
    """
    Split hostgroup name in parent part and name:

    >>> split_parent("a/b/c")
    ('c', 'a/b')
    """
    if '/' in name:
        parent, name = name.rsplit('/',1)
    else:
        return name, None
    return name, parent


def ensure(module):
    changed = False
    full_name = module.params['name']
    short_name, parent_name = split_parent(full_name)
    architecture_name = module.params[ARCHITECTURE]
    compute_profile_name = module.params[COMPUTE_PROFILE]
    domain_name = module.params[DOMAIN]
    environment_name = module.params[ENVIRONMENT]
    medium_name = module.params[MEDIUM]
    operatingsystem_name = module.params[OPERATINGSYSTEM]
    partition_table_name = module.params['partition_table']
    root_pass = module.params['root_pass']
    smart_proxy_name = module.params[SMART_PROXY]
    subnet_name = module.params[SUBNET]
    state = module.params['state']
    parameters = module.params['parameters']
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

    data = {'title': full_name, 'name': short_name}

    try:
        hostgroup = theforeman.search_hostgroup(data=data)
    except ForemanError as e:
        module.fail_json(msg='Could not get hostgroup: {0}'.format(e.message))

    # Architecture
    if architecture_name:
        architecture = get_resource(module=module,
                                    resource_type=ARCHITECTURE,
                                    resource_func=theforeman.search_architecture,
                                    resource_name=architecture_name)
        data['architecture_id'] = str(architecture.get('id'))

    # Compute Profile
    if compute_profile_name:
        compute_profile = get_resource(module=module,
                                       resource_type=COMPUTE_PROFILE,
                                       resource_func=theforeman.search_compute_profile,
                                       resource_name=compute_profile_name)
        data['compute_profile_id'] = str(compute_profile.get('id'))

    # Domain
    if domain_name:
        domain = get_resource(module=module,
                              resource_type=DOMAIN,
                              resource_func=theforeman.search_domain,
                              resource_name=domain_name)
        data['domain_id'] = str(domain.get('id'))

    # Environment
    if environment_name:
        environment = get_resource(module=module,
                                   resource_type=ENVIRONMENT,
                                   resource_func=theforeman.search_environment,
                                   resource_name=environment_name)
        data['environment_id'] = str(environment.get('id'))

    # Medium
    if medium_name:
        medium = get_resource(module=module,
                              resource_type=MEDIUM,
                              resource_func=theforeman.search_medium,
                              resource_name=medium_name)
        data['medium_id'] = str(medium.get('id'))

    # Operatingssystem
    if operatingsystem_name:
        operatingsystem = get_resource(module=module,
                                       resource_type=OPERATINGSYSTEM,
                                       resource_func=theforeman.search_operatingsystem,
                                       resource_name=operatingsystem_name,
                                       search_title=True)
        data['operatingsystem_id'] = str(operatingsystem.get('id'))

    # Partition Table
    if partition_table_name:
        partition_table = get_resource(module=module,
                                       resource_type=PARTITION_TABLE,
                                       resource_func=theforeman.search_partition_table,
                                       resource_name=partition_table_name)
        data['ptable_id'] = str(partition_table.get('id'))
    # Root password
    if root_pass:
        data['root_pass'] = root_pass

    # Smart Proxy
    if smart_proxy_name:
        smart_proxy = get_resource(module=module,
                                   resource_type=SMART_PROXY,
                                   resource_func=theforeman.search_smart_proxy,
                                   resource_name=smart_proxy_name)
        data['puppet_proxy_id'] = str(smart_proxy.get('id'))

    # Subnet
    if subnet_name:
        subnet = get_resource(module=module,
                              resource_type=SUBNET,
                              resource_func=theforeman.search_subnet,
                              resource_name=subnet_name)
        data['subnet_id'] = str(subnet.get('id'))

    # Parent
    if parent_name:
        environment = get_resource(module=module,
                                   resource_type=HOSTGROUP,
                                   resource_func=theforeman.search_hostgroup,
                                   search_title=True,
                                   resource_name=parent_name)
        data['parent_id'] = str(environment.get('id'))

    if not hostgroup and state == 'present':
        try:
            hostgroup = theforeman.create_hostgroup(data=data)
            changed = True
        except ForemanError as e:
            module.fail_json(msg='Could not create hostgroup: {0}'.format(e.message))
    elif hostgroup:
        if state == 'absent':
            try:
                hostgroup = theforeman.delete_hostgroup(id=hostgroup.get('id'))
                return True, hostgroup
            except ForemanError as e:
                module.fail_json(msg='Could not delete hostgroup: {0}'.format(e.message))

        cmp_hostgroup = filter_hostgroup(hostgroup)
        if not all(data.get(key, None) == cmp_hostgroup.get(key, None) for key in data.keys() + cmp_hostgroup.keys()):
            try:
                hostgroup = theforeman.update_hostgroup(id=hostgroup.get('id'), data=data)
                changed = True
            except ForemanError as e:
                module.fail_json(msg='Could not update hostgroup: {0}'.format(e.message))

    hostgroup_id = hostgroup.get('id')

    # Parameters
    if parameters:
        try:
            hostgroup_parameters = theforeman.get_hostgroup_parameters(hostgroup_id=hostgroup_id)
        except ForemanError as e:
            module.fail_json(
                msg='Could not get hostgroup parameters: {0}'.format(e.message))

        # Delete parameters which are not defined
        for hostgroup_param in hostgroup_parameters:
            hostgroup_param_name = hostgroup_param.get('name')
            defined_params = [item for item in parameters if item.get(
                'name') == hostgroup_param_name]
            if not defined_params:
                try:
                    theforeman.delete_hostgroup_parameter(
                        hostgroup_id=hostgroup_id, parameter_id=hostgroup_param.get('id'))
                except ForemanError as e:
                    module.fail_json(msg='Could not delete host parameter {name}: {error}'.format(
                        name=hostgroup_param_name))
                changed = True

        # Create and update parameters
        for param in parameters:
            hostgroup_params = [item for item in hostgroup_parameters if item.get(
                'name') == param.get('name')]
            if not hostgroup_params:
                try:
                    theforeman.create_hostgroup_parameter(
                        hostgroup_id=hostgroup_id, data=param)
                except ForemanError as e:
                    module.fail_json(
                        msg='Could not create host parameter {param_name}: {error}'.format(param_name=param.get('name'),
                                                                                           error=e.message))
                changed = True
            else:
                for hostgroup_param in hostgroup_params:
                    hostgroup_value = hostgroup_param.get('value')
                    param_value = param.get('value')
                    if isinstance(param_value, list):
                        param_value = ','.join(param_value)
                    # Replace \n seems to be needed. Otherwise some strings are
                    # always changed although they look equal
                    if hostgroup_value.replace('\n', '') != param_value.replace('\n', ''):
                        try:
                            theforeman.update_hostgroup_parameter(hostgroup_id=hostgroup_id,
                                                             parameter_id=hostgroup_param.get(
                                                                 'id'),
                                                             data=param)
                        except ForemanError as e:
                            module.fail_json(
                                msg='Could not update host parameter {param_name}: {error}'.format(
                                    param_name=param.get('name'), error=e.message))
                        changed = True

    return changed, hostgroup


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            architecture=dict(type='str', default=None),
            compute_profile=dict(type='str', default=None),
            domain=dict(type='str', default=None),
            environment=dict(type='str', default=None),
            medium=dict(type='str', default=None),
            operatingsystem=dict(type='str', default=None),
            parameters=dict(type='list', default=None),
            partition_table=dict(type='str', default=None),
            root_pass=dict(type='str', default=None),
            smart_proxy=dict(type='str', default=None),
            subnet=dict(type='str', default=None),
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

    changed, hostgroup = ensure(module)
    module.exit_json(changed=changed, hostgroup=hostgroup)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
