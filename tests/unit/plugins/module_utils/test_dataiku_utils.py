import os
import pytest

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.dataiku.dss.plugins.module_utils.dataiku_utils import (
    MakeNamespace,
    is_version_more_recent,
    discover_install_dir_python,
    add_dataikuapi_to_path,
    add_dss_connection_args,
    get_client_from_parsed_args,
    update,
    extract_keys,
    exclude_keys
)


def test_MakeNamespaces():
    input_dict = dict(data_dir="/data/dataiku/dss", host="localhost", port=10000, api_key="thisissecret")

    namespace = MakeNamespace(input_dict)

    assert getattr(namespace, "data_dir") == "/data/dataiku/dss"
    assert getattr(namespace, "host") == "localhost"
    assert getattr(namespace, "port") == 10000
    assert getattr(namespace, "api_key") == "thisissecret"


@pytest.mark.parametrize("test_input, expected", [
    (("12.3.0", "12.0.0"), True),
    (("11.3.0", "12.0.0"), False),
    (("12.0.1-beta1", "12.0.0"), True),
    (("12.0.0-beta1", "12.0.0"), False),
])
def test_is_version_more_recent(test_input, expected):
    assert is_version_more_recent(None, *test_input) == expected


def test_discover_install_dir_python():
    data_dir = "/tmp/"
    install_dir = "/tmp/install_dir"
    file_content = f"""
# this is a comment line
export SOME_VARIABLE=value

export DKUINSTALLDIR="{install_dir}"
if test -z "$DKUINSTALLDIR"; then
    echo 'hello'
fi
"""
    os.mkdir(f"{data_dir}/bin")
    with open(f"{data_dir}/bin/env-default.sh", "w", encoding="UTF-8") as writer:
        writer.write(file_content)

    computed_install_dir_1 = discover_install_dir_python(data_dir)
    computed_install_dir_2 = discover_install_dir_python("/some_other_dir")

    assert computed_install_dir_1 == f"{install_dir}/python"
    assert computed_install_dir_2 is None


def test_update():
    input_dict = dict(data_dir="/data/dataiku/dss", nested=dict(host="localhost", port=10000, api_key="thisissecret"))
    update_keys = dict(nested=dict(port=20000))
    expected = dict(data_dir="/data/dataiku/dss", nested=dict(host="localhost", port=20000, api_key="thisissecret"))

    updated_dict = update(input_dict, update_keys)

    return updated_dict == expected


@pytest.mark.parametrize("test_input, expected", [
    ((dict(data_dir="/data/dataiku/dss", host="localhost", port=10000, api_key="thisissecret"), dict(host="", port=1)),
     dict(host="localhost", port=10000)),
    ((dict(data_dir="/data/dataiku/dss", host="localhost", port=10000, api_key="thisissecret"), dict(data_dir="", api_key="")),
     dict(data_dir="/data/dataiku/dss", api_key="thisissecret")),
    ((dict(data_dir="/data/dataiku/dss", host="localhost", port=10000, api_key="thisissecret"), dict(does_not_exist="")),
     dict(does_not_exist=None)),
])
def test_extract_keys(test_input, expected):
    assert extract_keys(*test_input) == expected


@pytest.mark.parametrize("test_input, expected", [
    ((dict(data_dir="/data/dataiku/dss", host="localhost", port=10000, api_key="thisissecret"), ["data_dir", "api_key"]),
     dict(data_dir=None, host="localhost", port=10000, api_key=None)),
    ((dict(data_dir="/data/dataiku/dss", host="localhost", port=10000, api_key="thisissecret"), ["host", "port", "unknown"]),
     dict(data_dir="/data/dataiku/dss", host=None, port=None, api_key="thisissecret")),
    ((dict(data_dir="/data/dataiku/dss", port=10000, nested=dict(port=10000, host="localhost")), ["port", "nested.port"]),
     dict(data_dir="/data/dataiku/dss", port=None, nested=dict(port=None, host="localhost"))),
])
def test_exclude_keys(test_input, expected):
    assert exclude_keys(*test_input) == expected
