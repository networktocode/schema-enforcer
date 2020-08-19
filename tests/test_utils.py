import os
import json
import shutil
import itertools
from collections import deque

import utils


# fmt: off
TEST_DATA = {
    'key': 'value',
    "list_of_strings": ["one", "two"],
    "list_of_lists": [[1, 2], [3, 4]],
    "list_of_dicts": [
        {"one": 1, "two": 2},
        {"one": "1", "two": "2"},
    ],
    "nested": {
        "data": ["one", "two"],
    },
}
# fmt: on


ANSIBLE_HOST_VARIABLES = {
    "host1": {
        "ntp_servers": [{"address": "10.1.1.1", "vrf": "mgmt"}],
        "ntp_authentication": True,
        "dns_servers": [{"address": "10.1.1.1", "vrf": "mgmt"}],
        "syslog_servers": [{"address": "10.1.1.1."}],
    },
    "host2": {
        "ntp_servers": [{"address": "10.2.1.1", "vrf": "mgmt"}],
        "dns_servers": [{"address": "10.2.1.1", "vrf": "mgmt"}],
    },
}


def test_load_config():
    actual = utils.load_config()
    mock = {
        "json_schema_path": "examples/schema/json",
        "yaml_schema_path": "examples/schema/yaml",
        "json_schema_definitions": "examples/schema/json/schemas",
        "yaml_schema_definitions": "examples/schema/yaml/schemas",
        "json_full_schema_definitions": "examples/schema/json/full_schemas",
        "device_variables": "examples/hostvars",
        "inventory_path": "examples/inventory",
    }
    assert actual == mock


def test_get_path_and_filename():
    path, filename = utils.get_path_and_filename("json/schemas/ntp.json")
    assert path == "json/schemas"
    assert filename == "ntp"


def test_ensure_yaml_output_format():
    data_formatted = utils.ensure_strings_have_quotes_mapping(TEST_DATA)
    yaml_path = "tests/mocks/utils/.formatted.yml"
    with open(yaml_path, "w", encoding="utf-8") as fh:
        utils.YAML_HANDLER.dump(data_formatted, fh)

    with open(yaml_path, encoding="utf-8") as fh:
        actual = fh.read()

    with open("tests/mocks/utils/formatted.yml") as fh:
        mock = fh.read()

    assert actual == mock
    os.remove(yaml_path)
    assert not os.path.isfile(yaml_path)


def test_get_conversion_filepaths():
    yaml_path = "tests/mocks/schema/yaml"
    json_path = yaml_path.replace("yaml", "json")
    actual = utils.get_conversion_filepaths(yaml_path, "yml", json_path, "json")
    expected_defs = [
        (f"{yaml_path}/definitions/{subdir}/ip.yml", f"{json_path}/definitions/{subdir}/ip.json",)
        for subdir in ("arrays", "objects", "properties")
    ]
    expected_schemas = [
        (f"{yaml_path}/schemas/{schema}.yml", f"{json_path}/schemas/{schema}.json") for schema in ("dns", "ntp")
    ]
    mock = set(expected_defs + expected_schemas)
    # the results in actual are unordered, so test just ensures contents are the same
    assert not mock.difference(actual)


def test_load_schema_from_json_file():
    schema_root_dir = os.path.realpath("tests/mocks/schema/json")
    schema_filepath = f"{schema_root_dir}/schemas/ntp.json"
    validator = utils.load_schema_from_json_file(schema_root_dir, schema_filepath)
    with open("tests/mocks/ntp/valid/full_implementation.json", encoding="utf-8") as fh:
        # testing validation tests that the RefResolver works as expected
        validator.validate(json.load(fh))


def test_generate_validation_error_attributes():
    schema_root_dir = os.path.realpath("tests/mocks/schema/json")
    schema_filepath = f"{schema_root_dir}/schemas/ntp.json"
    validator = utils.load_schema_from_json_file(schema_root_dir, schema_filepath)
    invalid_data = "tests/mocks/ntp/invalid/invalid_ip.json"
    actual = utils.generate_validation_error_attributes(invalid_data, validator)
    mock = {
        "message": "'10.1.1.1000' is not a 'ipv4'",
        "schema_path": deque(["properties", "ntp_servers", "items", "properties", "address", "format"]),
        "validator": "format",
        "validator_value": "ipv4",
    }
    assert actual == mock


def test_dump_data_to_yaml():
    test_file = "tests/mocks/utils/.test_data.yml"
    assert not os.path.isfile(test_file)
    utils.dump_data_to_yaml(TEST_DATA, test_file)
    with open(test_file, encoding="utf-8") as fh:
        actual = fh.read()
    with open("tests/mocks/utils/formatted.yml") as fh:
        mock = fh.read()
    assert actual == mock
    os.remove(test_file)
    assert not os.path.isfile(test_file)


def test_dump_data_json():
    test_file = "tests/mocks/utils/.test_data.json"
    assert not os.path.isfile(test_file)
    utils.dump_data_to_json(TEST_DATA, test_file)
    with open(test_file, encoding="utf-8") as fh:
        actual = fh.read()
    with open("tests/mocks/utils/formatted.json") as fh:
        mock = fh.read()
    assert actual == mock
    os.remove(test_file)
    assert not os.path.isfile(test_file)


def test_convert_yaml_to_json():
    output_path = "tests/mocks/schema/_json"
    yaml_path = output_path.replace("_json", "yaml")
    assert not os.path.isdir(output_path)
    utils.convert_yaml_to_json(yaml_path, output_path)
    with open(f"{output_path}/schemas/ntp.json", encoding="utf-8") as fh:
        actual = fh.read()
    with open("tests/mocks/schema/json/schemas/ntp.json", encoding="utf-8") as fh:
        mock = fh.read()
    assert actual == mock
    shutil.rmtree(output_path)
    assert not os.path.isdir(output_path)


def test_convert_json_to_yaml():
    output_path = "tests/mocks/schema/_yaml"
    json_path = output_path.replace("_yaml", "json")
    assert not os.path.isdir(output_path)
    utils.convert_json_to_yaml(json_path, output_path)
    with open(f"{output_path}/schemas/ntp.yml", encoding="utf-8") as fh:
        actual = fh.read()
    with open("tests/mocks/schema/yaml/schemas/ntp.yml", encoding="utf-8") as fh:
        mock = fh.read()
    assert actual == mock
    shutil.rmtree(output_path)
    assert not os.path.isdir(output_path)


def test_resolve_json_refs():
    json_schema_path = "tests/mocks/schema/json/schemas"
    output_path = "tests/mocks/schema/json/_full_schemas"
    assert not os.path.isdir(output_path)
    utils.resolve_json_refs(json_schema_path, output_path)
    with open(f"{output_path}/ntp.json", encoding="utf-8") as fh:
        actual = fh.read()
    with open("tests/mocks/schema/json/full_schemas/ntp.json", encoding="utf-8") as fh:
        mock = fh.read()
    assert actual == mock
    shutil.rmtree(output_path)
    assert not os.path.isdir(output_path)


def test_get_schema_properties():
    schema_files = [f"tests/mocks/schema/json/schemas/{schema}.json" for schema in ("dns", "ntp")]
    actual = utils.get_schema_properties(schema_files)
    mock = {
        "dns": ["dns_servers"],
        "ntp": ["ntp_servers", "ntp_authentication", "ntp_logging"],
    }
    assert actual == mock


def test_dump_schema_vars():
    output_dir = "tests/mocks/utils/hostvar"
    assert not os.path.isdir(output_dir)
    schema_properties = {
        "dns": ["dns_servers"],
        "ntp": ["ntp_servers", "ntp_authentication", "ntp_logging"],
    }
    host_variables = ANSIBLE_HOST_VARIABLES["host1"]
    utils.dump_schema_vars(output_dir, schema_properties, host_variables)
    for file in ("dns.yml", "ntp.yml"):
        with open(f"{output_dir}/{file}", encoding="utf-8") as fh:
            actual = fh.read()
        with open(f"tests/mocks/utils/host1/{file}", encoding="utf-8") as fh:
            mock = fh.read()

        assert actual == mock

    shutil.rmtree(output_dir)
    assert not os.path.isdir(output_dir)


def test_generate_hostvars():
    schema_path = "tests/mocks/schema/json/schemas"
    output_path = "tests/mocks/utils/hostvars"
    inventory_path = "tests/mocks/inventory"
    assert not os.path.isdir(output_path)
    utils.generate_hostvars(inventory_path, schema_path, output_path)
    hosts = ("host3", "host4")
    files = ("dns.yml", "ntp.yml")
    for host, file in itertools.product(hosts, files):
        with open(f"{output_path}/{host}/{file}", encoding="utf-8") as fh:
            actual = fh.read()
        with open(f"tests/mocks/utils/{host}/{file}", encoding="utf-8") as fh:
            mock = fh.read()

        assert actual == mock
        assert len(os.listdir(f"{output_path}/{host}/")) == 2

    shutil.rmtree(output_path)
    assert not os.path.isdir(output_path)
