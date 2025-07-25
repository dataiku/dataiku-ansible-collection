import copy
import os
import re
import sys
import traceback

from ansible.module_utils import six
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.common.collections import Mapping

# Import Error handling required du to ansible sanity checks handling of non-default python libraries
# https://docs.ansible.com/ansible/latest/dev_guide/testing/sanity/import.html
try:
    from packaging import version
except ImportError:
    version = None
    HAS_PACKAGING_LIBRARY = False
    PACKAGING_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_PACKAGING_LIBRARY = True
    PACKAGING_IMPORT_ERROR = None


class MakeNamespace(object):
    def __init__(self, values):
        self.__dict__.update(values)


def is_version_more_recent(module, input_version, baseline):
    if not HAS_PACKAGING_LIBRARY:
        module.fail_json(
            msg=missing_required_lib("packaging"),
            exception=PACKAGING_IMPORT_ERROR
        )
    else:
        input_version = version.parse(input_version)
        baseline = version.parse(baseline)
        return input_version > baseline


def discover_install_dir_python(data_dir):
    pattern = re.compile(r'^export\sDKUINSTALLDIR=\"(.*)\"$')
    try:
        for line in open(f"{data_dir}/bin/env-default.sh", encoding="UTF-8"):
            match = re.match(pattern, line)
            if match:
                install_dir = match.group(1)
                return f"{install_dir}/python"
        return
    except FileNotFoundError:
        return


def bootstrap_dataiku_module(module):
    if module.params.get("connect_to"):
        if module.params["connect_to"].get("node_type"):
            module.no_log_values.remove(module.params['connect_to']['node_type'])
        if module.params["connect_to"].get("data_dir"):
            module.no_log_values.remove(module.params['connect_to']['data_dir'])
        if module.params["connect_to"].get("port"):
            module.no_log_values.remove(module.params['connect_to']['port'])
    add_dataikuapi_to_path(module)


def add_dataikuapi_to_path(module):
    args = MakeNamespace(module.params)

    data_dir = os.environ.get("DATAIKU_ANSIBLE_DSS_DATADIR", "/data/dataiku/dss_data")
    if args.data_dir:
        data_dir = args.data_dir
    elif args.connect_to and "data_dir" in args.connect_to:
        data_dir = args.connect_to["data_dir"]

    install_dir = discover_install_dir_python(data_dir)

    if install_dir is None:
        module.fail_json(
            msg=f"Failed to discover install_dir with the provided data_dir \'{install_dir}\' information."
        )

    sys.path.append(install_dir)
    return


def add_dss_connection_args(module_args):
    module_args.update(
        {
            "connect_to": dict(type="dict", required=False, default=None, no_log=True),
            "host": dict(type="str", required=False, default="127.0.0.1"),
            "port": dict(type="str", required=False, default=None),
            "api_key": dict(type="str", required=False, default=None, no_log=True),
            "node_type": dict(type="str", required=False, default=None),
            "data_dir": dict(type="str", required=False, default=None),
        }
    )


def get_client_from_parsed_args(module, supported_node_types):
    args = MakeNamespace(module.params)
    api_key = os.environ.get("DATAIKU_ANSIBLE_DSS_API_KEY", None)
    if args.api_key:
        api_key = args.api_key
    elif args.connect_to and "api_key" in args.connect_to:
        api_key = args.connect_to["api_key"]

    if api_key is None:
        module.fail_json(
            msg="Missing an API Key, either from 'api_key' parameter, 'connect_to' parameter or DATAIKU_ANSIBLE_DSS_API_KEY env var"
        )

    port = os.environ.get("DATAIKU_ANSIBLE_DSS_PORT", "80")
    if args.port:
        port = args.port
    elif args.connect_to and "port" in args.connect_to:
        port = args.connect_to["port"]

    host = os.environ.get("DATAIKU_ANSIBLE_DSS_HOST", "127.0.0.1")
    if args.host:
        host = args.host
    elif args.connect_to and "host" in args.connect_to:
        host = args.connect_to["host"]

    node_type = os.environ.get("DATAIKU_ANSIBLE_DSS_NODE_TYPE", "design")
    if args.node_type:
        node_type = args.node_type
    elif args.connect_to and "node_type" in args.connect_to:
        node_type = args.connect_to["node_type"]

    if node_type not in supported_node_types:
        module.fail_json(
            msg="Node type {} is not supported. See the list of supported nodes for this module {}".format(node_type, supported_node_types)
        )

    if node_type == "govern":
        from dataikuapi.govern_client import GovernClient
        client = GovernClient(f"http://{host}:{port}", api_key=api_key)
    else:
        from dataikuapi.dssclient import DSSClient
        client = DSSClient(f"http://{host}:{port}", api_key=api_key)

    return client


# Similar to dict.update but deep
def update(d, u):
    if isinstance(d, Mapping):
        for k, v in six.iteritems(u):
            if isinstance(v, Mapping):
                d[k] = update(d.get(k, {}), v)
            else:
                d[k] = v
    else:
        d = u
    return d


def smart_update_named_lists(l1, l2):
    result = copy.deepcopy(l1)
    for el2 in l2:
        name2 = el2["name"]
        for idx1, el1 in enumerate(l1):
            if el1["name"] == name2:
                result[idx1].update(el2)
                break
        else:
            result.append(el2)
    return result


def extract_keys(input_data, keys_reference):
    if isinstance(input_data, Mapping):
        extracted_data = {}
        for k, v in keys_reference.items():
            if isinstance(v, Mapping):
                extracted_data[k] = extract_keys(input_data.get(k, {}), v)
            else:
                extracted_data[k] = input_data.get(k, None)
    else:
        extracted_data = input_data
    return extracted_data


def exclude_keys(dictionary, excluded_keys):
    result = {}
    excluded_parts = [key.split(".") for key in excluded_keys]
    first_level_keys = [part[0] for part in excluded_parts]
    for key, value in dictionary.items():
        if key not in first_level_keys:
            result[key] = value
        else:
            if isinstance(value, dict):
                nested_excluded_keys = [".".join(part[1:]) for part in excluded_parts if len(part) > 1]
                result[key] = exclude_keys(value, nested_excluded_keys)
            else:
                result[key] = None
    return result


def _build_template_from_field(base_template, values, default_value):
    current_key = values.pop(0)
    if len(values) == 0:
        base_template[current_key] = default_value
    else:
        base_template[current_key] = _build_template_from_field(dict(), values, default_value)
    return base_template


def build_template_from_fields(fields, default_value, delimiter="."):
    result = dict()
    for field in fields:
        all_keys = field.split(delimiter)
        result.update(_build_template_from_field(dict(), all_keys, default_value))
    return result
