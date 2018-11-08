#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage Foreman config template resources.
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
module: foreman_config_template
short_description:
- Manage Foreman Provision Templates using Foreman API v2.
description:
- Create, update and and delete Foreman provision templates using Foreman API v2
options:
  audit_comment:
    description:
    - Audit comment
    required: false
    default: None
  name:
    description: Provision template name
    required: true
    default: None
  locked:
    description: Whether or not the template is locked for editing
    required: false
    default: false
  operatingsystems:
    description: List of Operatingsystem names the template is assigned to
    required: false
    default: None
  template:
    description: RAW template content
    required: false
    default: None
  template_file:
    description: Path and filename to load the template from
    required: false
    default: None
  template_kind_name:
    description: Template Kind name
    required: false
    default: None
  snippet:
    description: Define if template is a snippet or not
    required: false
    default: false
  organizations:
    description:
    - List of organization the medium should be assigned to
    required: false
  locations:
    description:
    - List of locations the medium should be assigned to
    required: false
  state:
    description: Provision template state
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
- name: Ensure Config Template
  foreman_config_template:
    name: CoreOS Cloud-config
    locked: false
    operatingsystems:
      - CoreOS
    template_file: /tmp/coreos-cloud-config
    template_kind_name: provision
    snippet: true
    organizations:
      - Development
      - DevOps
    locations:
      - Prague
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

try:
    from ansible.module_utils.foreman_utils import *

    has_import_error = False
except ImportError as e:
    has_import_error = True
    import_error_msg = str(e)


def equal_dict_lists(l1, l2, compare_key='title'):
    s1 = set(dict_list_to_list(alist=l1, key=compare_key))
    s2 = set(dict_list_to_list(alist=l2, key=compare_key))
    return s1.issubset(s2) and s2.issubset(s1)


def templates_equal(data, config_template, compareable_keys):
    if not all(data.get(key, None) == config_template.get(key, None) for key in compareable_keys):
        return False
    if not equal_dict_lists(l1=data.get('operatingsystems', None), l2=config_template.get('operatingsystems', None)):
        return False
    if not organizations_equal(data, config_template):
        return False
    if not locations_equal(data, config_template):
        return False
    return True


def get_resources(resource_type, resource_func, resource_specs, search_field='name'):
    result = list()
    if not resource_specs:
        return result
    for item in resource_specs:
        search_data = dict()
        if isinstance(item, dict):
            for key in item:
                search_data[key] = item[key]
        else:
            search_data[search_field] = item
        try:
            resource = resource_func(data=search_data)
            if not resource:
                module.fail_json(
                    msg='Could not find resource type {resource_type} specified as {name}'.format(
                        resource_type=resource_type,
                        name=item))
            result.append(resource)
        except ForemanError as e:
            module.fail_json(msg='Could not search resource type {resource_type} specified as {name}: {error}'.format(
                resource_type=resource_type, name=item, error=e.message))
    return result


def ensure():
    audit_comment = module.params['audit_comment']
    compareable_keys = ['locked', 'snippet', 'template']
    locked = module.params['locked']
    name = module.params['name']
    operatingsystems = module.params['operatingsystems']
    state = module.params['state']
    snippet = module.params['snippet']
    template = module.params['template']
    template_file = module.params['template_file']
    template_kind_name = module.params['template_kind_name']
    organizations = module.params['organizations']
    locations = module.params['locations']

    theforeman = init_foreman_client(module)

    data = dict(name=name)

    try:
        config_template = theforeman.search_config_template(data=data)
        if config_template:
            config_template = theforeman.get_config_template(id=config_template.get('id'))
    except ForemanError as e:
        module.fail_json(msg='Could not get config template: {0}'.format(e.message))

    if state == 'absent':
        if config_template:
            try:
                config_template = theforeman.delete_config_template(id=config_template.get('id'))
                return True, config_template
            except ForemanError as e:
                module.fail_json(msg='Could not delete config template: {0}'.format(e.message))

    if state == 'present':
        if template and template_file:
            module.fail_json(msg='Only one of either template or template_file must be defined')

        if template:
            data['template'] = template
        elif template_file:
            try:
                with open(template_file) as f:
                    data['template'] = f.read()
            except IOError as e:
                module.fail_json(msg='Could not open file {0}: {1}'.format(template_file, e.message))
        else:
            if not config_template:
                # creating new template
                module.fail_json(msg='Either template or template_file must be defined')

        data['audit_comment'] = audit_comment
        data['locked'] = locked
        data['snippet'] = snippet

        if organizations is not None:
            data['organization_ids'] = get_organization_ids(module, theforeman, organizations)
        if locations is not None:
            data['location_ids'] = get_location_ids(module, theforeman, locations)

        if template_kind_name:
            res = get_resources(resource_type='template_kinds',
                                resource_func=theforeman.search_template_kind,
                                resource_specs=[template_kind_name])
            if res:
                data['template_kind_id'] = res[0]["id"]

        if not snippet:
            data['operatingsystems'] = get_resources(resource_type='operatingsystem',
                                                     resource_func=theforeman.search_operatingsystem,
                                                     resource_specs=operatingsystems,
                                                     search_field='title')

        if not config_template:
            try:
                config_template = theforeman.create_config_template(data=data)
                return True, config_template
            except ForemanError as e:
                module.fail_json(msg='Could not create config template: {0}'.format(e.message))

        if not templates_equal(data, config_template, compareable_keys):
            try:
                if config_template['locked']:
                    unlock = {'id': config_template.get('id'), 'locked': False}
                    theforeman.update_config_template(id=config_template.get('id'), data=unlock)
                if data['locked']:
                    data['locked'] = False
                    theforeman.update_config_template(id=config_template.get('id'), data=data)
                    data['locked'] = True
                config_template = theforeman.update_config_template(id=config_template.get('id'), data=data)
                return True, config_template
            except ForemanError as e:
                module.fail_json(msg='Could not update config template: {0}'.format(e.message))

    return False, config_template


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            audit_comment=dict(type='str', required=False),
            name=dict(type='str', required=True),
            locked=dict(type='bool', default=False),
            operatingsystems=dict(type='list', required=False),
            template=dict(type='str', required=False),
            template_file=dict(type='str', required=False),
            template_kind_name=dict(type='str', required=False),
            snippet=dict(type='bool', default=False),
            organizations=dict(type='list', required=False),
            locations=dict(type='list', required=False),
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
    if has_import_error:
        module.fail_json(msg=import_error_msg)

    changed, config_template = ensure()
    module.exit_json(changed=changed, config_template=config_template)


from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
