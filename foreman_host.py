#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from foreman import Foreman
    from foreman.foreman import ForemanError
except ImportError:
    foremanclient_found = False
else:
    foremanclient_found = True

def ensure(module):
    changed = False
    name = module.params['name']
    architecture_name = module.params['architecture']
    build = module.params['build']
    compute_profile_name = module.params['compute_profile']
    compute_resource_name = module.params['compute_resource']
    domain_name = module.params['domain']
    environment_name = module.params['environment']
    hostgroup_name = module.params['hostgroup']
    location_name = module.params['location']
    medium_name = module.params['medium']
    operatingsystem_name = module.params['operatingsystem']
    organization_name = module.params['organization']
    root_pass = module.params['root_pass']
    state = module.params['state']
    foreman_host = module.params['foreman_host']
    foreman_port = module.params['foreman_port']
    foreman_user = module.params['foreman_user']
    foreman_pass = module.params['foreman_pass']
    theforeman = Foreman(hostname=foreman_host,
                         port=foreman_port,
                         username=foreman_user,
                         password=foreman_pass)
    data = {}
    data['name'] = name + '.' + domain_name

    try:
        host = theforeman.get_host(data=data)
    except ForemanError as e:
        module.fail_json(msg='Could not get host: ' + e.message)

    if not host:
        if state == 'absent':
            return False, host

        # Architecture
        try:
            architecture = theforeman.get_architecture(data={'name': architecture_name})
            if not architecture:
                module.fail_json(mgs='Architecture not found: ' + architecture_name)
            data['architecture_id'] = architecture.get('id')
        except ForemanError as e:
            module.fail_json(msg='Could not get architecture: ' + e.message)

        if build:
            data['build'] = 'true'
        else:
            data['build'] = 'false'

        # Compute Profile
        if compute_profile_name:
            try:
                compute_profile = theforeman.get_compute_profile(data={'name': compute_profile_name})
                if not compute_profile:
                    module.fail_json(msg='Copmute Profile not found: ' + compute_profile_name)
                data['compute_profile_id'] = compute_profile.get('id')
            except ForemanError as e:
                module.fail_json(msg='Could not get compute profile: ' + e.message)

        # Compute Resource
        if compute_resource_name:
            try:
                compute_resource = theforeman.get_compute_resource(data={'name': compute_resource_name})
                if not compute_resource:
                    module.fail_json(msg='Compute Resource not found: ' + compute_resource_name)
                data['compute_resource_id'] = compute_resource.get('id')
            except ForemanError as e:
                module.fail_json(msg='Could not get compute profile: ' + e.message)

        # Domain
        if domain_name:
            try:
                domain = theforeman.get_domain(data={'name': domain_name})
                if not domain:
                    module.fail_json(msg='Domain not found: ' + domain_name)
                data['domain_id'] = domain.get('id')
            except ForemanError as e:
                module.fail_json(msg='Could not get domain: ' + e.message)

        # Environment
        if environment_name:
            try:
                environment = theforeman.get_environment(data={'name': environment_name})
                if not environment:
                    module.fail_json(mgs='Environment not found: ' + environment_name)
                data['environment_id'] = environment.get('id')
            except ForemanError as e:
                module.fail_json(msg='Could not get environment: ' + e.message)

        # Hostgroup
        if hostgroup_name:
            try:
                hostgroup = theforeman.get_hostgroup(data={'name': hostgroup_name})
                if not hostgroup:
                    module.fail_json(msg='Hostgroup not found: ' + hostgroup_name)
                data['hostgroup_id'] = hostgroup.get('id')
            except ForemanError as e:
                module.fail_json(msg='Could not get hostgroup: ' + e.message)

        # Location
        try:
            location = theforeman.get_location(data={'name': location_name})
            if not location:
                module.fail_json(msg='Location not found: ' + location_name)
            data['location_id'] = location.get('id')
        except ForemanError as e:
            module.fail_json(msg='Could not get location: ' + e.message)

        # Medium
        if medium_name:
            try:
                medium = theforeman.get_medium(data={'name' :medium_name})
                if not medium:
                    module.fail_json(msg='Medium not found: ' + medium_name)
                data['medium_id'] = medium.get('id')
            except ForemanError as e:
                module.fail_json(msg='Could not get medium: ' + e.message)

        # Organization
        if organization_name:
            try:
                organization = theforeman.get_organization(data={'name': organization_name})
                if not organization:
                    module.fail_json(msg='Organization not found: ' + organization_name)
                data['organization_id'] = organization.get('id')
            except ForemanError as e:
                module.fail_json(msg='Could not get organization: ' + e.message)

        # Operatingssystem
        if operatingsystem_name:
            try:
                operatingssystem = theforeman.get_operatingsystem(data={'name': operatingsystem_name})
                if not operatingssystem:
                    module.fail_json(msg='Operatingsystem not found: ' + operatingsystem_name)
                data['operatingsystem_id'] = operatingssystem.get('id')
            except ForemanError as e:
                module.fail_json(msg='Could not get operatingsystem: ' + e.message)

        # Root password
        if root_pass:
            data['root_pass'] = root_pass

        try:
            host = theforeman.create_host(data=data)
        except ForemanError as e:
            module.fail_json(msg='Could not create host: ' + e.message + '. Request: ' + str(e.request) + '. Status code: ' + str(e.status_code))

        changed = True

    if state == 'absent':
        try:
            theforeman.delete_host(data=host)
        except ForemanError as e:
            module.fail_json(msg='Could not delete host: ' + e.message + '. Request: ' + str(e.request) + '. Status code: ' + str(e.status_code))
        return True, host

    try:
        host_power_state = theforeman.get_host_power(host_id=host.get('name')).get('power')
    except ForemanError as e:
        module.fail_json(msg='Could not get host power state: ' + e.message)

    if state == 'rebooted':
        try:
            theforeman.reboot_host(host_id=host.get('name'))
            return True, host
        except ForemanError as e:
            module.fail_json(msg='Could not reboot host: ' + e.message)
    elif state == 'running' and host_power_state != 'poweredOn':
        try:
            theforeman.poweron_host(host_id=host.get('name'))
            return True, host
        except ForemanError as e:
            module.fail_json(msg='Could not power on host: ' + e.message)
    elif state == 'stopped' and host_power_state != 'poweredOff':
        try:
            theforeman.poweroff_host(host_id=host.get('name'))
            return True, host
        except ForemanError as e:
            module.fail_json(msg='Could not power off host: ' + e.message)

    return changed, host

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(Type='str', required=True),
            architecture=dict(Type='str', Default='x86_64'),
            build=dict(Type='bool', Default=True),
            compute_profile=dict(Type='str'),
            compute_resource=dict(Type='str'),
            domain=dict(Type='str'),
            environment=dict(Type='str'),
            hostgroup=dict(Type='str'),
            location=dict(Type='str', required=True),
            medium=dict(Type='str'),
            operatingsystem=dict(Type='str'),
            organization=dict(Type='str', required=True),
            root_pass=dict(Type='str'),
            state=dict(Type='str', Default='present', choices=['present', 'absent', 'running', 'stopped', 'rebooted']),
            foreman_host=dict(Type='str', Default='127.0.0.1'),
            foreman_port=dict(Type='str', Default='443'),
            foreman_user=dict(Type='str', required=True),
            foreman_pass=dict(Type='str', required=True)
        ),
    )

    if not foremanclient_found:
        module.fail_json(msg='python-foreman module is required')

    ensure_result = ensure(module)
    changed = ensure_result[0]
    host = ensure_result[1]
    module.exit_json(changed=changed, name=module.params['name'], hostname=host.get('name'), ip=host.get('ip'))

# import module snippets
from ansible.module_utils.basic import *
main()
