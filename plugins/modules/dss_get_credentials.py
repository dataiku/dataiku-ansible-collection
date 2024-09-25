#!/usr/bin/python

ANSIBLE_METADATA = {"metadata_version": "1.1", "status": ["preview"], "supported_by": "dataiku-ansible-collection"}

DOCUMENTATION = """
---
module: dss_get_credentials

short_description: Creates/get an admin API key onto a DSS datadir.

description:
    This module reads a datadir and returns the port on which the studio is exposed, the admin API Key as well as the datadir path exposed to future usage.
    Warning: When running this module with `--check` mode activated, it does not return a real api_key, but rather its ID which will not be usable by other modules.
    Warning: Module is not idempotent.

options:
    datadir:
        type: str
        description:
            - The datadir where DSS is installed. Be mindful to become the applicative user to call this module.
        required: true
    api_key_name:
        type: str
        description:
            - The name of the api key to look for. No effect for now.
        required: false
        default: "dss-ansible-admin"

author:
    - Jean-Bernard Jansen (jean-bernard.jansen@dataiku.com)
"""

EXAMPLES = """
# Creates and displays a key with a label
- name: Get the API Key
  become: true
  become_user: dataiku
  dataiku.dss.dss_get_credentials:
    datadir: /home/dataiku/dss
    api_key_name: mytestkey
  register: dss_connection_info
- name: Debug
  debug:
    var: dss_connection_info
"""

RETURN = """
port:
    returned: on success
    description: The port on which DSS is exposed
    type: str
api_key:
    returned: on success
    description: An admin valid API Key
    type: str
data_dir:
    returned: on success
    description: DSS datadir path
    type: str
"""

import json
import logging
import os
import subprocess
import traceback

from ansible.module_utils import six
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.dataiku.dss.plugins.module_utils.dataiku_utils import MakeNamespace


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        datadir=dict(type="str", required=True),
        api_key_name=dict(type="str", required=False, default="dss-ansible-admin"),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    args = MakeNamespace(module.params)

    try:
        if not os.path.isdir(args.datadir):
            module.fail_json(msg="Datadir '{}' not found.".format(args.datadir))

        current_uid = os.getuid()
        current_datadir_uid = os.stat(args.datadir).st_uid
        if current_uid != current_datadir_uid:
            module.fail_json(
                msg="dss_get_credentials MUST run as the owner of the datadir (ran as UID={}, datadir owned by UID={})".format(
                    current_uid, current_datadir_uid
                )
            )

        # Setup the log
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
            filename="{}/run/ansible.log".format(args.datadir),
            filemode="a",
        )

        # Read the port
        config = six.moves.configparser.RawConfigParser()
        config.read("{}/install.ini".format(args.datadir))
        port = str(config.getint("server", "port"))
        nodetype = config.get("general", "nodetype").strip()
        logging.info("Reads port {} from install.ini".format(port))

        # Create/Get the api key
        changed = False
        api_key = None
        value_type = None
        exec_name = "apinode-admin" if nodetype == "api" else "dsscli"

        api_keys_list = json.loads(
            subprocess.check_output(
                [
                    "{}/bin/{}".format(args.datadir, exec_name),
                    "admin-keys-list" if nodetype == "api" else "api-keys-list",
                    "--output",
                    "json",
                ]
            )
        )
        for key in api_keys_list:
            if key.get("label", None) == args.api_key_name:
                if key["key"] == "******":
                    api_key = key["id"]
                    value_type = "id"
                else:
                    api_key = key["key"]
                    value_type = "key"
                if not module.check_mode:
                    logging.info('Found existing API Key labeled "{}".'.format(args.api_key_name))
                break

        if not module.check_mode:
            if api_key is not None:
                # delete existing key
                if nodetype == "api":
                    delete_command = [
                        "{}/bin/{}".format(args.datadir, exec_name),
                        "admin-key-delete-by-id" if value_type == "id" else "admin-key-delete",
                        api_key,
                    ]
                else:
                    delete_command = [
                        "{}/bin/{}".format(args.datadir, exec_name),
                        "api-key-delete",
                        api_key,
                    ]
                logging.info('Deleting existing API Key labeled "{}".'.format(args.api_key_name))
                subprocess.check_output(delete_command)

            # Create new key
            create_command = [
                "{}/bin/{}".format(args.datadir, exec_name),
                "admin-key-create" if nodetype == "api" else "api-key-create",
                "--output",
                "json",
                "--label",
                args.api_key_name,
            ]
            if nodetype != "api":
                create_command += ["--admin", "true"]
            api_keys_list = json.loads(subprocess.check_output(create_command))
            if nodetype == "api":
                api_key = api_keys_list["key"]
            else:
                api_key = api_keys_list[0]["key"]
            logging.info('Created new API Key labeled "{}".'.format(args.api_key_name))
            changed = True

        # Build result
        result = dict(changed=changed, port=port, api_key=api_key, data_dir=args.datadir)

        module.exit_json(**result)
    except Exception as e:
        module.fail_json(
            msg="{}\n\n{}\n\n{}".format(str(e), traceback.format_exc(e), "".join(traceback.format_stack()))
        )


def main():
    run_module()


if __name__ == "__main__":
    main()
