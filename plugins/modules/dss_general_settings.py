#!/usr/bin/python

ANSIBLE_METADATA = {"metadata_version": "1.1", "status": ["preview"], "supported_by": "dataiku-ansible-collection"}

DOCUMENTATION = """
---
module: dss_general_settings

short_description: Set up general settings values

description:
    This module edits DSS general settings

options:
    connect_to:
        type: dict
        description:
            - A dictionary containing "port" and "api_key". This parameter is a short hand to be used with dss_get_credentials
        required: false
    host:
        type: str
        description:
            - The host on which to make the requests.
        required: false
        default: 127.0.0.1
    port:
        type: str
        description:
            - The port on which to make the requests. Mandatory if connect_to is not used
        required: false
    api_key:
        type: str
        description:
            - The API Key to authenticate on the API. Mandatory if connect_to is not used
        required: false
    data_dir:
        type: str
        description:
            - The path of the datadir where DSS is installed
        required: false
    silent_update_secrets:
        type: bool
        description:
            - Whether to notify of a settings password or secret update. This is the only way to achieve idempotency as secrets are
              encrypted based on a salt. This makes the password encryption not idempotent an thus makes password updates not
              idempotent. By providing this setting as true by default, any secret change on the setting will not be notified.
              Setting it to 'false' will always return a 'Changed' state.
        default: true
        required: false
    enable_smart_update:
        type: bool
        description:
            - Whether to perform a smart update of the named lists attributes. When enabled, the DSS settings container exec configs
              and spark exec configs will be updated based on the 'name' key. The module will iterate over the existing exec configs
              and update the ones that have matching 'name' keys, else append them to the list. Warning, when enabled, it is not possible
              to delete an exec config using ansible.
        default: true
        required: false
    settings:
        type: dict
        description:
            - General settings values to modify. Can be ignored to just get the current values.
        required: false
        default: {}
author:
    - Jean-Bernard Jansen (jean-bernard.jansen@dataiku.com)
"""

EXAMPLES = """
- name: Get credentials
  become: true
  become_user: dataiku
  dataiku.dss.dss_get_credentials:
    datadir: /home/dataiku/dss
    api_key_name: myadminkey
  register: dss_connection_info

- name: Setup LDAP connectivity
  become: true
  become_user: dataiku
  dataiku.dss.dss_general_settings:
    connect_to: "{{ dss_connection_info }}"
    settings:
      ldapSettings:
        enabled: true
        url: ldap://ldap.internal.example.com/dc=example,dc=com
        bindDN: uid=readonly,ou=users,dc=example,dc=com
        bindPassword: theserviceaccountpassword
        useTls: true
        autoImportUsers: true
        userFilter: (&(objectClass=posixAccount)(uid={USERNAME}))
        defaultUserProfile: READER
        displayNameAttribute: gecos
        emailAttribute: mail
        enableGroups: true
        groupFilter: (&(objectClass=posixGroup)(memberUid={USERDN}))
        groupNameAttribute: cn
        groupProfiles: []
        authorizedGroups: dss-users
"""

RETURN = """
previous_settings:
    returned: on success
    description: Previous values held by required settings before update
    type: dict
dss_general_settings:
    returned: on success
    description: Return the current values after update
    type: dict
message:
    returned: on success
    description: MODIFIED or UNCHANGED
    type: str
changed:
    returned: on success
    description: whether changes were made
    type: bool
"""

import traceback
import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.dataiku.dss.plugins.module_utils.dataiku_utils import (
    MakeNamespace,
    add_dss_connection_args,
    extract_keys,
    get_client_from_parsed_args,
    add_dataikuapi_to_path,
    update,
    exclude_keys,
    smart_update_named_lists
)

smart_update_fields_template = {
    "containerSettings": {
        "executionConfigs": []
    },
    "sparkSettings": {
        "executionConfigs": []
    }
}

encrypted_fields = [
    "ldapSettings.bindPassword", "ssoSettings.samlSPParams.keystorePassword", "ssoSettings.openIDParams.clientSecret",
    "azureADSettings.credentialsClientSecret", "azureADSettings.credentialsCertificatePassword"
]
smart_update_fields = [
    "containerSettings.executionConfigs", "sparkSettings.executionConfigs"
]


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        settings=dict(type="dict", required=False, default={}),
        silent_update_secrets=dict(type="bool", required=False, default=True),
        enable_smart_update=dict(type="bool", required=False, default=True)
    )
    add_dss_connection_args(module_args)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    add_dataikuapi_to_path(module)

    args = MakeNamespace(module.params)

    result = dict(changed=False, message="UNCHANGED", previous_settings=None, settings=None)

    client = None
    general_settings = None
    try:
        client = get_client_from_parsed_args(module)
        general_settings = client.get_general_settings()

        current_settings = extract_keys(general_settings.settings, args.settings)
        new_settings = args.settings

        # Prepare the result for dry-run mode
        result["previous_settings"] = current_settings
        result["dss_general_settings"] = general_settings.settings

        smart_update_fields_changed = False
        if args.enable_smart_update:
            # Extract execution configs from regular settings
            current_values = exclude_keys(current_settings, smart_update_fields)
            new_settings = exclude_keys(args.settings, smart_update_fields)

            # Smart update of execution configs
            current_smart_update_fields = extract_keys(general_settings.settings, smart_update_fields_template)
            new_smart_update_fields = extract_keys(args.settings, smart_update_fields_template)
            updated_smart_update_fields = copy.deepcopy(current_smart_update_fields)
            for key in new_smart_update_fields.keys():
                if new_smart_update_fields[key]["executionConfigs"]:
                    updated_smart_update_fields[key]["executionConfigs"] = smart_update_named_lists(
                        current_smart_update_fields[key]["executionConfigs"],
                        new_smart_update_fields[key]["executionConfigs"]
                    ) or []
            smart_update_fields_changed = current_smart_update_fields != updated_smart_update_fields
        else:
            current_values = current_settings

        # Process regular settings
        if args.silent_update_secrets:
            current_values_password_excluded = exclude_keys(current_values, encrypted_fields)
            new_values_password_excluded = exclude_keys(new_settings, encrypted_fields)
            settings_changed = current_values_password_excluded != new_values_password_excluded
        else:
            settings_changed = current_values != new_settings

        result["changed"] = smart_update_fields_changed or settings_changed
        if result["changed"]:
            result["message"] = "MODIFIED"

        if module.check_mode:
            module.exit_json(**result)

        # Apply the changes
        if args.enable_smart_update:
            update(general_settings.settings, new_settings)
            update(general_settings.settings, updated_smart_update_fields)
        else:
            update(general_settings.settings, new_settings)
        general_settings.save()

        module.exit_json(**result)
    except Exception as e:
        module.fail_json(msg="{}\n\n{}\n\n{}".format(str(e), traceback.format_exc(), "".join(traceback.format_stack())))


def main():
    run_module()


if __name__ == "__main__":
    main()
