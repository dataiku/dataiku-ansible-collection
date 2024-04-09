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


def add_dataikuapi_to_path(module):
    args = MakeNamespace(module.params)

    install_dir = (
        discover_install_dir_python(args.connect_to.get("data_dir"))
        if args.connect_to is not None
        else None
    )
    if install_dir is None:
        module.fail_json(
            msg=f"Failed to discover install_dir with the provided data_dir \'{args.connect_to.get('data_dir')}\' information."
        )

    sys.path.append(install_dir)
    return


def add_dss_connection_args(module_args):
    module_args.update(
        {
            "connect_to": dict(type="dict", required=True, no_log=True),
            "host": dict(type="str", required=False, default="127.0.0.1"),
            "port": dict(type="str", required=False, default=None),
            "api_key": dict(type="str", required=False, default=None, no_log=True),
            "data_dir": dict(type="str", required=False, default=None),
        }
    )


def get_client_from_parsed_args(module):
    from dataikuapi.dssclient import DSSClient

    args = MakeNamespace(module.params)
    api_key = (
        args.api_key
        if args.api_key is not None
        else args.connect_to.get("api_key", os.environ.get("DATAIKU_ANSIBLE_DSS_API_KEY", None))
    )
    if api_key is None:
        module.fail_json(
            msg="Missing an API Key, either from 'api_key' parameter, 'connect_to' parameter or DATAIKU_ANSIBLE_DSS_API_KEY env var"
        )
    port = (
        args.port
        if args.port is not None
        else args.connect_to.get("port", os.environ.get("DATAIKU_ANSIBLE_DSS_PORT", "80"))
    )
    host = args.host

    client = DSSClient(f"http://{args.host}:{port}", api_key=api_key)

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
