#!/usr/bin/python

ANSIBLE_METADATA = {"metadata_version": "1.1", "status": ["preview"], "supported_by": "dataiku-ansible-collection"}

DOCUMENTATION = """
---
module: dss_connection_generic

short_description: Creates, edit or delete a Data Science Studio connection of any kind

description:
    This module edits a complete connection

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
    type:
        type: str
        description:
            - Type of the connection
        required: true
    name:
        type: str
        description:
            - Name of the connection
        required: true
    connection_args:
        type: dict
        description:
            - A dictionary of additional arguments passed into the json of the connection.
        required: true
    state:
        type: str
        description:
            - Wether the connection is supposed to exist or not. Possible values are "present" and "absent"
        default: present
        required: false
    set_encrypted_fields_at_creation_only:
        type: bool
        description:
            - If connection already exits, encrypted fields such as "password" are not set again
            - This is useful to track if a change happened, since tracking encrypted changes is not
            - possible through the public API only.
        required: false
        default: false
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


- name: Create HDFS connection
  dataiku.dss.dss_connection_generic:
    name: "hdfs_test"
    type: HDFS
    connection_args:
      params:
        root: "/user/dataiku/test"
        defaultDatabase: dataiku
        aclSynchronizationMode: "NONE"
        namingRule:
          hdfsPathDatasetNamePrefix: "${projectKey}/"
          tableNameDatasetNamePrefix: "design_${projectKey}_"
          uploadsPathPrefix: uploads
      allowWrite: true
      allowManagedDatasets: true
      allowManagedFolders: true
      usableBy: ALLOWED
      allowedGroups:
        - data_team
      detailsReadability:
        allowedGroups:
            - data_team
        readableBy: ALLOWED

"""

RETURN = """
previous_connection_def:
    returned: on success
    description: The previous values
    type: dict
connection_def:
    returned: on success
    description: The current values if the connection have not been deleted
    type: dict
message:
    returned: on success
    description: CREATED, DELETED, MODIFIED or UNCHANGED
    type: str
changed:
    returned: on success
    description: whether changes were made
    type: bool
"""

import copy
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.dataiku.dss.plugins.module_utils.dataiku_utils import (
    MakeNamespace,
    add_dss_connection_args,
    get_client_from_parsed_args,
    add_dataikuapi_to_path,
    update,
)

supported_node_types = ["design", "automation", "deployer"]

connection_template = {
    "allowManagedDatasets": True,
    "allowManagedFolders": False,
    "allowWrite": True,
    "allowedGroups": [],
    # "creationTag": {},
    # "credentialsMode": "GLOBAL",
    "detailsReadability": {"allowedGroups": [], "readableBy": "NONE"},
    # "indexingSettings": {
    # "indexForeignKeys": False,
    # "indexIndices": False,
    # "indexSystemTables": False
    # },
    "maxActivities": 0,
    # "name": "",
    "params": {},
    # "type": "PostgreSQL",
    "usableBy": "ALL",
    "useGlobalProxy": False,
}

encrypted_fields_list = ["password"]


def run_module():
    module_args = dict(
        name=dict(type="str", required=True),
        state=dict(type="str", required=False, default="present"),
        type=dict(type="str", required=True),
        connection_args=dict(type="dict", required=True),
        set_encrypted_fields_at_creation_only=dict(type="bool", default=False, required=False),
        # params=dict(type='dict', default={}, required=False),
    )
    add_dss_connection_args(module_args)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    add_dataikuapi_to_path(module)
    from dataikuapi.utils import DataikuException

    args = MakeNamespace(module.params)
    if args.state not in ["present", "absent"]:
        module.fail_json(
            msg="Invalid value '{}' for argument state : must be either 'present' or 'absent'".format(args.source_type)
        )
    type = args.type

    result = dict(changed=False, message="UNCHANGED", )

    try:
        client = get_client_from_parsed_args(module, supported_node_types)
        exists = True
        create = False
        connection = client.get_connection(args.name)
        current_def = None
        try:
            current_def = connection.get_definition()
        except DataikuException as e:
            # if e.message.startswith("com.dataiku.dip.server.controllers.NotFoundException"):
            if str(e) == "java.lang.IllegalArgumentException: Connection '{}' does not exist".format(args.name):
                exists = False
                if args.state == "present":
                    create = True
            else:
                raise
        except Exception as e:
            raise

        current_def = None
        encrypted_fields_before_change = {"params": {}}
        if exists:
            result["previous_connection_def"] = current_def = connection.get_definition()
            # Check this is the same type
            if current_def["type"] != type:
                module.fail_json(
                    msg="Connection '{}' already exists but is of type '{}'".format(args.name, current_def["type"])
                )
                return
            # Remove some values from the current def
            for field in encrypted_fields_list:
                encrypted_field_before_change = current_def["params"].get(field, None)
                if encrypted_field_before_change is not None:
                    encrypted_fields_before_change["params"][field] = encrypted_field_before_change
                    del current_def["params"][field]
        else:
            if args.state == "present":
                # for mandatory_create_param in ["user", "password", "database", "postgresql_host"]:
                # if module.params[mandatory_create_param] is None:
                # module.fail_json(msg="Connection '{}' does not exist and cannot be created without the '{}' parameter"\
                # .format(args.name,mandatory_create_param))
                pass

        # Build the new definition
        new_def = copy.deepcopy(current_def) if exists else connection_template  # Used for modification

        # Apply every attribute except the password for now
        new_def["name"] = args.name
        update(new_def, args.connection_args)

        # Extract args that may be encrypted
        encrypted_fields = {"params": {}}
        for field in encrypted_fields_list:
            value = new_def["params"].get(field, None)
            if value is not None:
                encrypted_fields["params"][field] = value
                del new_def["params"][field]

        # Prepare the result for dry-run mode
        result["changed"] = create or (exists and args.state == "absent") or (exists and current_def != new_def)
        if result["changed"]:
            if create:
                result["message"] = "CREATED"
            elif exists:
                if args.state == "absent":
                    result["message"] = "DELETED"
                elif current_def != new_def:
                    result["message"] = "MODIFIED"

        if args.state == "present":
            result["connection_def"] = new_def

        if module.check_mode:
            module.exit_json(**result)

        # Apply the changes
        if result["changed"] or (0 < len(encrypted_fields["params"].keys()) and exists):
            if create:
                update(new_def, encrypted_fields)
                connection = client.create_connection(args.name, type, new_def["params"])
                def_after_creation = connection.get_definition()
                update(def_after_creation, new_def)
                connection.set_definition(def_after_creation)  # 2nd call to apply additional parameters
            elif exists:
                if args.state == "absent":
                    connection.delete()
                elif current_def != new_def or (0 < len(encrypted_fields["params"].keys()) and not args.set_encrypted_fields_at_creation_only):
                    for field in encrypted_fields_list:
                        new_def_value = encrypted_fields["params"].get(field, None)
                        previous_def_value = encrypted_fields_before_change.get(field)
                        if new_def_value is not None:
                            new_def["params"][field] = new_def_value
                        elif previous_def_value:
                            new_def["params"][field] = previous_def_value
                    connection.set_definition(new_def)
                    result["message"] = "MODIFIED"
                    if 0 < len(encrypted_fields["params"]):
                        # no need to compare, encrypted fields change value if reset
                        result["changed"] = True
                        result["message"] = "MODIFIED"

        module.exit_json(**result)
    except Exception as e:
        module.fail_json(msg="{}\n\n{}\n\n{}".format(str(e), traceback.format_exc(), "".join(traceback.format_stack())))


def main():
    run_module()


if __name__ == "__main__":
    main()
