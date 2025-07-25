#!/usr/bin/python

ANSIBLE_METADATA = {"metadata_version": "1.1", "status": ["preview"], "supported_by": "dataiku-ansible-collection"}

DOCUMENTATION = """
---
module: dss_group

short_description: Creates, edit or delete a Data Science Studio group

description:
    This module edits a complete group. If the group does not exist and is required to, it is created.
    If the group exists but is supposed not to, it is deleted

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
    node_type:
        type: str
        description:
            - The DSS node type
        required: false
    name:
        type: str
        description:
            - Name of the group
        required: true
    description:
        type: str
        description:
            - Description of the group
    source_type:
        type: str
        description:
            - The source type of the group, either LOCAL, LDAP or SAAS
        required: false
    state:
        type: str
        description:
            - Wether the user is supposed to exist or not. Possible values are "present" and "absent"
        required: false
        default: present
    admin:
        type: bool
        description:
            - Tells if the group has administration credentials
        required: false
    ldap_group_names:
        type: list
        elements: str
        description:
            - List of LDAP groups synced with the group
        required: false
    sso_group_names:
        type: list
        elements: str
        description:
            - List of SSO groups synced with the group
        required: false
    azure_ad_group_names:
        type: list
        elements: str
        description:
            - List of Azure AD groups synced with the group
        required: false
    custom_group_names:
        type: list
        elements: str
        description:
            - List of custom groups synced with the group
        required: false
    may_create_authenticated_connections:
        type: bool
        description:
            - Whether the group allows to create authenticated connections
        required: false
    may_create_code_studio_templates:
        type: bool
        description:
            - Whether the group allows to create code studio templates
        required: false
    may_create_data_collections:
        type: bool
        description:
            - Whether the group allows to create data collections
        required: false
    may_create_workspaces:
        type: bool
        description:
            - Whether the group allows to create workspaces
        required: false
    may_create_projects:
        type: bool
        description:
            - Whether the group allows to create projects
        required: false
    may_create_projects_from_macros:
        type: bool
        description:
            - Whether the group allows to create projects from macros
        required: false
    may_create_projects_from_templates:
        type: bool
        description:
            - Whether the group allows to create projects from templates
        required: false
    may_create_projects_from_dataiku_apps:
        type: bool
        description:
            - Whether the group allows to create projects from dataiku apps
        required: false
    may_create_published_API_services:
        type: bool
        description:
            - Whether the group allows to create published API services
        required: false
    may_create_published_projects:
        type: bool
        description:
            - Whether the group allows to create published projects
        required: false
    may_create_active_web_content:
        type: bool
        description:
            - Whether the group allows to create active web content
        required: false
    may_create_code_envs:
        type: bool
        description:
            - Whether the group allows to create code envs
        required: false
    may_create_clusters:
        type: bool
        description:
            - Whether the group allows to create clusters
        required: false
    may_develop_plugins:
        type: bool
        description:
            - Whether the group allows to create plugins
        required: false
    may_edit_lib_folders:
        type: bool
        description:
            - Whether the group allows to create lib folders
        required: false
    may_manage_code_envs:
        type: bool
        description:
            - Whether the group allows to manage code envs
        required: false
    may_manage_clusters:
        type: bool
        description:
            - Whether the group allows to manage clusters
        required: false
    may_manage_code_studio_templates:
        type: bool
        description:
            - Whether the group allows to manage code studio templates
        required: false
    may_manage_feature_store:
        type: bool
        description:
            - Whether the group allows to manage feature store
        required: false
    may_manage_UDM:
        type: bool
        description:
            - Whether the group allows to manage UDMs
        required: false
    may_publish_to_data_collections:
        type: bool
        description:
            - Whether the group allows to publish to data collections
        required: false
    may_share_to_workspaces:
        type: bool
        description:
            - Whether the group allows to share to workspaces
        required: false
    may_view_indexed_hive_connections:
        type: bool
        description:
            - Whether the group allows to view indexed hive connections
        required: false
    may_write_safe_code:
        type: bool
        description:
            - Whether the group allows to write safe code
        required: false
    may_write_unsafe_code:
        type: bool
        description:
            - Whether the group allows to write unsafe code
        required: false
    may_write_in_root_project_folder:
        type: bool
        description:
            - Whether the group allows to write the root project folder
        required: false
    can_obtain_API_ticket_from_cookies_for_groups_regex:
        type: str
        description:
            - Whether the group allows to obtain an API ticket from cookies for groups regex
        required: false
    may_manage_govern:
        type: bool
        description:
            - Whether the group allows to manage Govern
        required: false

author:
    - Jean-Bernard Jansen (jean-bernard.jansen@dataiku.com)
"""

EXAMPLES = """
# Creates a group using dss_get_credentials if you have SSH Access
- name: Get the API Key
  become: true
  become_user: dataiku
  dataiku.dss.dss_get_credentials:
    datadir: /home/dataiku/dss
    api_key_name: myadminkey
  register: dss_connection_info

- name: Add a group
  dataiku.dss.dss_group:
    connect_to: "{{ dss_connection_info }}"
    name: dssgroup
    admin: false
    ldap_group_names: []
    sso_group_names: []
    azure_ad_group_names: []
    custom_group_names: []
    source_type: LOCAL
    may_create_authenticated_connections: false
    may_create_code_envs: true
    may_create_clusters: true
    may_create_projects: true
    may_create_projects_from_macros: true
    may_create_projects_from_templates: true
    may_create_active_web_content: true
    may_create_published_API_services: true
    may_create_published_projects: true
    may_develop_plugins: true
    may_edit_lib_folders: true
    may_manage_code_envs: true
    may_manage_clusters: true
    may_manage_UDM: true
    may_view_indexed_hive_connections: false
    may_write_safe_code: true
    may_write_unsafe_code: true
    may_write_in_root_project_folder: true

# Creates a group using explicit host/port/key
# From local machine
- name: Add a user
  delegate_to: localhost
  dataiku.dss.dss_user:
    host: 192.168.0.2
    port: 80
    api_key: XXXXXXXXXXXXXX
    name: dssgroup

# Deletes a group
- name: Add a user
  become: true
  become_user: dataiku
  dataiku.dss.dss_user:
    connect_to: "{{ dss_connection_info }}"
    group: dssgroup
    state: absent
"""

RETURN = """
previous_group_def:
    returned: on success
    description: The previous values
    type: dict
group_def:
    returned: on success
    description: The current values is the group have not been deleted
    type: dict
message:
    returned: on success
    description: CREATED, MODIFIED, UNCHANGED or DELETED
    type: str
"""

import re
import copy
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.dataiku.dss.plugins.module_utils.dataiku_utils import (
    MakeNamespace,
    is_version_more_recent,
    add_dss_connection_args,
    get_client_from_parsed_args,
    bootstrap_dataiku_module
)

supported_node_types = ["design", "automation", "deployer", "govern"]
group_args_to_settings = {
    "ldap_group_names": "ldapGroupNames",
    "sso_group_names": "ssoGroupNames",
    "azure_ad_group_names": "azureADGroupNames",
    "custom_group_names": "customGroupNames",
}


def run_module():
    module_args = dict(
        # DSS group attributes
        name=dict(type="str", required=True),
        description=dict(type="str", required=False, default=None),
        source_type=dict(type="str", required=False, default=None),
        state=dict(type="str", required=False, default="present"),
        admin=dict(type="bool", required=False, default=None),
        ldap_group_names=dict(type="list", required=False, default=None, elements="str"),
        sso_group_names=dict(type="list", required=False, default=None, elements="str"),
        azure_ad_group_names=dict(type="list", required=False, default=None, elements="str"),
        custom_group_names=dict(type="list", required=False, default=None, elements="str"),
        # Design, Automation, Deployer group attributes
        may_create_authenticated_connections=dict(type="bool", required=False, default=None),
        may_create_code_envs=dict(type="bool", required=False, default=None),
        may_create_code_studio_templates=dict(type="bool", required=False, default=None),
        may_create_clusters=dict(type="bool", required=False, default=None),
        may_create_data_collections=dict(type="bool", required=False, default=None),
        may_create_projects=dict(type="bool", required=False, default=None),
        may_create_projects_from_macros=dict(type="bool", required=False, default=None),
        may_create_projects_from_templates=dict(type="bool", required=False, default=None),
        may_create_projects_from_dataiku_apps=dict(type="bool", required=False, default=None),
        may_create_published_API_services=dict(type="bool", required=False, default=None),
        may_create_published_projects=dict(type="bool", required=False, default=None),
        may_create_active_web_content=dict(type="bool", required=False, default=None),
        may_create_workspaces=dict(type="bool", required=False, default=None),
        may_develop_plugins=dict(type="bool", required=False, default=None),
        may_edit_lib_folders=dict(type="bool", required=False, default=None),
        may_manage_code_envs=dict(type="bool", required=False, default=None),
        may_manage_code_studio_templates=dict(type="bool", required=False, default=None),
        may_manage_clusters=dict(type="bool", required=False, default=None),
        may_manage_feature_store=dict(type="bool", required=False, default=None),
        may_manage_UDM=dict(type="bool", required=False, default=None),
        may_publish_to_data_collections=dict(type="bool", required=False, default=None),
        may_share_to_workspaces=dict(type="bool", required=False, default=None),
        may_view_indexed_hive_connections=dict(type="bool", required=False, default=None),
        may_write_safe_code=dict(type="bool", required=False, default=None),
        may_write_unsafe_code=dict(type="bool", required=False, default=None),
        may_write_in_root_project_folder=dict(type="bool", required=False, default=None),
        can_obtain_API_ticket_from_cookies_for_groups_regex=dict(type="str", required=False, default=None),
        # Govern group attributes
        may_manage_govern=dict(type="bool", required=False, default=None),
    )
    add_dss_connection_args(module_args)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    bootstrap_dataiku_module(module)
    from dataikuapi.utils import DataikuException

    args = MakeNamespace(module.params)
    if args.state not in ["present", "absent"]:
        module.fail_json(
            msg="Invalid value '{}' for argument state : must be either 'present' or 'absent'".format(args.state)
        )
    if args.source_type not in [None, "LOCAL", "LDAP", "SAAS", "AZURE_AD", "LOCAL_NO_AUTH", "CUSTOM"]:
        module.fail_json(
            msg="Invalid value '{}' for source_type : must be either 'LOCAL', 'LDAP', 'SAAS', 'AZURE_AD', 'LOCAL_NO_AUTH', or 'CUSTOM'".format(args.source_type)
        )

    result = dict(changed=False, message="UNCHANGED", )

    try:
        client = get_client_from_parsed_args(module, supported_node_types)
        group = client.get_group(args.name)
        dss_version = client.get_instance_info().raw.get("dssVersion")
        exists = True
        create = False
        current = None
        try:
            current = group.get_definition()
        except DataikuException as e:
            if str(e).startswith("com.dataiku.dip.server.controllers.NotFoundException"):
                exists = False
                if args.state == "present":
                    create = True
            else:
                raise
        except Exception:
            raise

        # Sort groups list before comparison as they should be considered sets
        if exists:
            for arg in group_args_to_settings.keys():
                setting_name = group_args_to_settings[arg]
                current_group_names = current.get(setting_name, "")
                if current_group_names and isinstance(current_group_names, str):
                    current[setting_name] = ",".join(sorted(current_group_names.split(",")))
                result["previous_group_def"] = current

        # Build the new user definition
        new_def = copy.deepcopy(current) if exists else {}  # Used for modification

        # Transform to camel case
        dict_args = {}
        for key, value in module.params.items():
            if key not in ["connect_to", "host", "port", "api_key", "node_type", "state"] + list(group_args_to_settings.keys()) and value is not None:
                camelKey = re.sub(r"_[a-zA-Z]", lambda x: x.group()[1:].upper(), key)
                dict_args[camelKey] = value
            elif key in group_args_to_settings.keys() and value is not None:
                dict_args[group_args_to_settings[key]] = value

        # Transform all <x>GroupNames to a list or a string depending on the version of DSS
        for arg in group_args_to_settings.keys():
            if getattr(args, arg) is not None:
                setting_name = group_args_to_settings[arg]
                # Trust what DSS returns first
                if exists and current.get(setting_name) is not None:
                    if isinstance(current[setting_name], str):
                        dict_args[setting_name] = ",".join(sorted(getattr(args, arg)))
                # Else use the DSS version
                elif is_version_more_recent(module, "12.6", dss_version):
                    dict_args[setting_name] = ",".join(sorted(getattr(args, arg)))

        new_def.update(dict_args)

        # Prepare the result for dry-run mode
        result["changed"] = create or (exists and args.state == "absent") or (exists and current != new_def)
        if result["changed"]:
            if create:
                result["message"] = "CREATED"
            elif exists:
                if args.state == "absent":
                    result["message"] = "DELETED"
                elif current != new_def:
                    result["message"] = "MODIFIED"

        if args.state == "present":
            result["group_def"] = new_def

        if module.check_mode:
            module.exit_json(**result)

        # Apply the changes
        if result["changed"]:
            if create:
                new_group = client.create_group(
                    args.name,
                    description=new_def.get("description", None),
                    source_type=new_def.get("source_type", "LOCAL"),
                )
                # 2nd request mandatory for capabilites TODO: fix the API
                if "mayWriteSafeCode" not in list(new_def.keys()):
                    new_def["mayWriteSafeCode"] = True
                new_group.set_definition(new_def)
                result["group_def"] = new_group.get_definition()
            elif exists:
                if args.state == "absent":
                    group.delete()
                elif current != new_def:
                    group.set_definition(new_def)
                    result["message"] = "MODIFIED"

        module.exit_json(**result)
    except Exception as e:
        module.fail_json(msg="{}\n\n{}\n\n{}".format(str(e), traceback.format_exc(), "".join(traceback.format_stack())))


def main():
    run_module()


if __name__ == "__main__":
    main()
