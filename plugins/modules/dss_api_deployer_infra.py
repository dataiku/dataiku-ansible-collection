#!/usr/bin/python

ANSIBLE_METADATA = {"metadata_version": "1.1", "status": ["preview"], "supported_by": "dataiku-ansible-collection"}

DOCUMENTATION = """
---
module: dss_api_deployer_infra

short_description: Set up an API Deployer infrastructure

description:
    This module creates and edits a DSS deployer infrastructure

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
    state:
        type: str
        description:
            - Is the deployer infra supposed to be there or not. Either "present" or "absent". Default "present"
        required: false
        default: present
    id:
        type: str
        description:
            - Id of the deployer Infra
        required: true
    stage:
        type: str
        description:
            - Stage of the deployer infra
        required: true
    type:
        type: str
        description:
            - Type of the deployer infra
        required: true
    api_nodes:
        type: list
        elements: dict
        description:
            - List of API nodes used to provision the deployer infra. Each API node is identified by its "url", "admin_api_key" and its "graphite_prefix"
        required: true
    permissions:
        type: list
        elements: dict
        description:
            - List of permissions to apply to the deployer infra. Should reference a group and the permissions
        required: false
        default: []
    carbonapi_url:
        type: str
        description:
            - The URL of the Carbon API server in which API Nodes metrics can be found
        required: false
author:
    - Jean-Bernard Jansen (jean-bernard.jansen@dataiku.com)
"""

EXAMPLES = """
- name: Get API credentials
  become: true
  become_user: dataiku
  dataiku.dss.dss_get_credentials:
    datadir: /home/dataiku/api
    api_key_name: myadminkey
  register: dss_api_info

- name: Get credentials
  become: true
  become_user: dataiku
  dataiku.dss.dss_get_credentials:
    datadir: /home/dataiku/dss
    api_key_name: myadminkey
  register: dss_connection_info

- name: Setup an infra
  become: true
  become_user: dataiku
  dataiku.dss.dss_api_deployer_infra:
    connect_to: "{{ dss_connection_info }}"
    id: infra_dev
    type: STATIC
    stage: Development
    api_nodes:
      - url: "http://localhost:{{ dss_api_info.port }}/"
        admin_api_key: "{{ dss_api_info.api_key }}"
        graphite_prefix: apinode
    permissions:
      - group: "data_team"
        read: true
        deploy: true
        admin: false
"""

RETURN = """
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
)


# TODO: make idempotent
def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        state=dict(type="str", required=False, default="present"),
        id=dict(type="str", required=True),
        stage=dict(type="str", required=True),
        type=dict(type="str", required=True),
        api_nodes=dict(type="list", required=True, elements="dict"),
        permissions=dict(type="list", required=False, default=[], elements="dict"),
        carbonapi_url=dict(type="str", required=False, default=None),
    )
    add_dss_connection_args(module_args)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    add_dataikuapi_to_path(module)

    args = MakeNamespace(module.params)
    result = dict(changed=False, message="UNCHANGED", id=args.id, )

    client = None
    exists = True
    create = False
    infra = None
    try:
        client = get_client_from_parsed_args(module)
        api_deployer = client.get_apideployer()
        infras_status = api_deployer.list_infras(as_objects=False)
        infras_id = []
        for infra_status in infras_status:
            infras_id.append(infra_status["infraBasicInfo"]["id"])
        exists = args.id in infras_id
        if not exists and args.state == "present":
            create = True

        result["changed"] = create or (exists and args.state == "absent")
        if result["changed"]:
            if create:
                result["message"] = "CREATED"
            elif exists:
                if args.state == "absent":
                    result["message"] = "DELETED"
                # elif current != new_def:
                #     result["message"] = "MODIFIED"

        # Prepare the result for dry-run mode
        if module.check_mode:
            module.exit_json(**result)

        # Apply the changes
        if args.state == "present":
            if create:
                infra = api_deployer.create_infra(args.id, args.stage, args.type)
            else:
                infra = api_deployer.get_infra(args.id)
            infra_settings = infra.get_settings()
            previous_settings = copy.deepcopy(infra_settings.get_raw())

            # Remove all / push all
            infra_settings.get_raw()["permissions"] = args.permissions
            infra_settings.get_raw()["apiNodes"] = []
            for api_node in args.api_nodes:
                infra_settings.add_apinode(
                    api_node["url"], api_node["admin_api_key"], api_node.get("graphite_prefix", "")
                )
            if args.carbonapi_url is not None:
                infra_settings.get_raw().update({"carbonAPISettings": {"carbonAPIURL": args.carbonapi_url}})
            infra_settings.save()
            if infra_settings.get_raw() != previous_settings and not result["changed"]:
                # result["previous"] = previous_settings
                # result["new"] = infra_settings.get_raw()
                result["changed"] = True
                result["message"] = "MODIFIED"

        if args.state == "absent" and exists:
            # TODO implement
            pass

        module.exit_json(**result)
    except Exception as e:
        module.fail_json(msg="{}\n\n{}\n\n{}".format(str(e), traceback.format_exc(), "".join(traceback.format_stack())))


def main():
    run_module()


if __name__ == "__main__":
    main()
