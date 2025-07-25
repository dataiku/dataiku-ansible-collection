#!/usr/bin/python

ANSIBLE_METADATA = {"metadata_version": "1.1", "status": ["preview"], "supported_by": "dataiku-ansible-collection"}

DOCUMENTATION = """
---
module: dss_connection_postgresql

short_description: Creates, edit or delete a Data Science Studio postgresql connection

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
    name:
        type: str
        description:
            - Name of the connection
        required: true
    postgresql_host:
        type: str
        description:
            - Hostname of the postgresql server. Not needed if modifying an existing connection.
        required: false
    postgresql_port:
        type: int
        description:
            - Hostname of the postgresql server.
        required: false
    user:
        type: str
        description:
            - Username to connect. Not needed if modifying an existing connection.
        required: false
    password:
        type: str
        description:
            - Password to connect. Not needed if modifying an existing connection.
        required: false
    silent_update_password:
        type: bool
        description:
            - Whether to notify of a connection password update. This is the only way to achieve idempotency as passwords are
              encrypted based on a salt. This makes the password encryption not idempotent an thus makes password updates not
              idempotent. By providing this setting as true by default, any password change on the connection will not be notified.
              Setting it to 'false' will always return a 'Changed' state.
        default: true
        required: false
    database:
        type: str
        description:
            - Database to use. Not needed if modifying an existing connection.
        required: false
    additional_args:
        type: dict
        description:
            - A dictionary of additional arguments passed into the json of the connection.
        required: false
        default: {}
    state:
        type: str
        description:
            - Wether the connection is supposed to exist or not. Possible values are "present" and "absent"
        default: present
        required: false
author:
    - Jean-Bernard Jansen (jean-bernard.jansen@dataiku.com)
"""

EXAMPLES = """
# Creates admin api key using dss_get_credentials
- name: Get the API Key
  become: true
  become_user: dataiku
  dataiku.dss.dss_get_credentials:
    datadir: /home/dataiku/dss
    api_key_name: myadminkey
  register: dss_connection_info

- name: Create a postgresql connection
  dataiku.dss.dss_connection_postgresql:
    connect_to: "{{ dss_connection_info }}"
    state: present
    name: pg_test_connection
    postgresql_host: localhost
    postgresql_port: "5432"
    user: pgadmin
    password: <pgadmin-password>
    database: postgres

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
    bootstrap_dataiku_module,
    update,
)

supported_node_types = ["design", "automation", "deployer"]

connection_template = {
    "allowManagedDatasets": True,
    "allowManagedFolders": False,
    "allowWrite": True,
    "allowedGroups": [],
    # "creationTag": {},
    "credentialsMode": "GLOBAL",
    "detailsReadability": {"allowedGroups": [], "readableBy": "NONE"},
    "indexingSettings": {"indexForeignKeys": False, "indexIndices": False, "indexSystemTables": False},
    "maxActivities": 0,
    # "name": "",
    "params": {
        "autocommitMode": False,
        # "db": "",
        # "host": "",
        "namingRule": {
            "canOverrideSchemaInManagedDatasetCreation": False,
            "tableNameDatasetNamePrefix": "${projectKey}_",
        },
        # "password": "",
        "port": 5432,
        "properties": [],
        "useTruncate": False,
        "useURL": False,
        # "user": ""
    },
    "type": "PostgreSQL",
    "usableBy": "ALL",
    "useGlobalProxy": False,
}


def run_module():
    module_args = dict(
        name=dict(type="str", required=True),
        state=dict(type="str", required=False, default="present"),
        postgresql_host=dict(type="str", default=None, required=False),
        postgresql_port=dict(type="int", default=None, required=False),
        user=dict(type="str", default=None, required=False),
        password=dict(type="str", required=False, no_log=True),
        silent_update_password=dict(type="bool", required=False, default=True, no_log=False),
        database=dict(type="str", default=None, required=False),
        additional_args=dict(type="dict", default={}, required=False),
    )
    add_dss_connection_args(module_args)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    bootstrap_dataiku_module(module)
    from dataikuapi.utils import DataikuException

    args = MakeNamespace(module.params)
    if args.state not in ["present", "absent"]:
        module.fail_json(
            msg="Invalid value '{}' for argument state : must be either 'present' or 'absent'".format(args.source_type)
        )

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
            if str(e) == "java.lang.IllegalArgumentException: Connection '{}' does not exist".format(args.name):
                exists = False
                if args.state == "present":
                    create = True
            else:
                raise
        except Exception:
            raise

        if exists:
            result["previous_connection_def"] = current_def
            # Check this is the same type
            if current_def["type"] != connection_template["type"]:
                module.fail_json(
                    msg="Connection '{}' already exists but is of type '{}'".format(args.name, current_def["type"])
                )
                return
        else:
            if args.state == "present":
                for mandatory_create_param in ["user", "password", "database", "postgresql_host"]:
                    if module.params[mandatory_create_param] is None:
                        module.fail_json(
                            msg="Connection '{}' does not exist and cannot be created without the '{}' parameter".format(
                                args.name, mandatory_create_param
                            )
                        )

        # Build the new definition
        new_def = copy.deepcopy(current_def) if exists else connection_template  # Used for modification

        # Apply every attribute except the password for now
        new_def["name"] = args.name
        if args.database is not None:
            new_def["params"]["db"] = args.database
        if args.user is not None:
            new_def["params"]["user"] = args.user
        if args.postgresql_host is not None:
            new_def["params"]["host"] = args.postgresql_host
        if args.postgresql_port is not None:
            new_def["params"]["port"] = args.postgresql_port

        # Bonus args
        update(new_def, args.additional_args)

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
        if result["changed"] or (args.password is not None and exists):
            if create:
                new_def["params"]["password"] = args.password
                params = {
                    "db": args.database,
                    "user": args.user,
                    "password": args.password,
                    "host": args.postgresql_host,
                }
                if args.postgresql_port is not None:
                    params["port"] = args.postgresql_port
                connection = client.create_connection(args.name, connection_template["type"], params)
                connection.set_definition(new_def)  # 2nd call to apply additional parameters
            elif exists:
                if args.state == "absent":
                    connection.delete()
                elif current_def != new_def or args.password is not None:
                    if args.password is not None:
                        new_def["params"]["password"] = args.password
                    connection.set_definition(new_def)
                    if result["changed"]:
                        result["message"] = "MODIFIED"

                    # Notify password change if explicitly asked
                    if args.password is not None and not args.silent_update_password:
                        result["changed"] = True
                        result["message"] = "MODIFIED"

        module.exit_json(**result)
    except Exception as e:
        module.fail_json(msg="{}\n\n{}\n\n{}".format(str(e), traceback.format_exc(), "".join(traceback.format_stack())))


def main():
    run_module()


if __name__ == "__main__":
    main()
