import os
import json
import glob

import pytest
from jsonschema import Draft7Validator, RefResolver, draft7_format_checker

import utils


CFG = utils.load_config()

# It is necessary to replace backslashes with forward slashes on Windows systems
BASE_URI = f"file:{os.path.realpath(CFG['json_schema_path'])}/".replace("\\", "/")
JSON_SCHEMA_DEFINITIONS = CFG["json_schema_definitions"]
JSON_SCHEMA_FILES = [
    os.path.basename(file) for file in glob.glob(f"{JSON_SCHEMA_DEFINITIONS}/*.json")
]
DATA_MODELS = [os.path.splitext(filename)[0] for filename in JSON_SCHEMA_FILES]


def get_schema_test_data(test_type, models, validators):
    """
    Maps each ``models`` (in)valid mock files to their respecteve model and validator.

    Args:
        test_type (str): Either "valid" or "invalid", which maps to mock schema dirs.
        models (list): The schemas in ``DATA_MODELS`` or passed in ``--schema`` arg.
        validators (list): The list of validators created from each schema file.

    Returns:
        gen_exp: Tuples, mapping each mock file to its respective model and validator.

    Examples:
        >>> models = ["ntp", "snmp"]
        >>> schemas = [read_schemas(model) for model in models]
        >>> validators = [
        ...     jsonschema.Draft7Validator(
        ...         schema,
        ...         format_checker=draft7_format_checker,
        ...         resolver=RefResolver(base_uri=BASE_URI, referrer=schema)
        ...     )
        ...     for schema in schemas
        ... ]
        >>> test_data = get_schema_test_data("valid", models, validators)
        >>> for test in test_data:
        ...     model, validator, mock_file = test
        ...     print(f"Testing {mock_file}.json against {model} schema")
        ...
        Testing full_implementation.json against ntp schema
        Testing partial_implementation.json against ntp schema
        Testing full_implementation.json against snmp schema
        Testing snmpv3.json against snmp schema
        >>>
    """
    model_test_file_map = {
        model: glob.glob(f"tests/mocks/{model}/{test_type}/*.json") for model in models
    }
    return (
        (model, validator, utils.get_path_and_filename(valid_test_file)[1])
        for model, validator in zip(models, validators)
        # the read_dir_contents function is used to prevent failures for missing
        # test cases. There is a test to ensure test cases are written, which
        # provides a clearer indication of what the failure is.
        for valid_test_file in model_test_file_map[model]
    )


def read_schema(model):
    """
    Opens and loads a JSONSchema file into a dict.

    Args:
        model (str): The name of a schema file without the `.json` extension.

    Returns:
        dict: The contents of the JSONSchema file serialized into a dict.
    """
    with open(f"{JSON_SCHEMA_DEFINITIONS}/{model}.json", encoding="utf-8") as fh:
        return json.load(fh)


def pytest_addoption(parser):
    parser.addoption(
        "--schema",
        action="append",
        default=[],
        help="List of schemas to validate config files against.",
    )
    parser.addoption(
        "--hostvars",
        action="store",
        default=CFG["device_variables"],
        help="The path to the directory of host variables to validate against schema.",
    )
    parser.addoption(
        "--hosts",
        action="store",
        default=None,
        help="List of hosts to execute tests against.",
    )


@pytest.fixture(scope="session")
def hostvars(request):
    return request.config.getoption("hostvars")


def pytest_generate_tests(metafunc):
    hostvars = metafunc.config.getoption("hostvars")
    hosts = metafunc.config.getoption("hosts")
    if hosts is None:
        hostnames = [dirname for dirname in os.listdir(hostvars)]
    else:
        hostnames = [host.strip() for host in hosts.split(",")]
    if "hostname" in metafunc.fixturenames:
        metafunc.parametrize("hostname", hostnames)

    models = metafunc.config.getoption("schema") or DATA_MODELS
    schemas = [read_schema(model) for model in models]
    validators = [
        Draft7Validator(
            schema,
            format_checker=draft7_format_checker,
            resolver=RefResolver(base_uri=BASE_URI, referrer=schema),
        )
        for schema in schemas
    ]
    if metafunc.function.__name__ == "test_config_definitions_against_schema":
        metafunc.parametrize("model,validator", zip(models, validators))

    if "valid_mock_dir" in metafunc.fixturenames:
        valid_mock_dirs = [f"tests/mocks/{model}/valid" for model in models]
        metafunc.parametrize("valid_mock_dir", valid_mock_dirs)
    if "invalid_mock_dir" in metafunc.fixturenames:
        valid_mock_dirs = [f"tests/mocks/{model}/invalid" for model in models]
        metafunc.parametrize("invalid_mock_dir", valid_mock_dirs)

    if "valid_mock" in metafunc.fixturenames:
        valid_mock_args = get_schema_test_data("valid", models, validators)
        metafunc.parametrize("model,validator,valid_mock", valid_mock_args)
    if "invalid_mock" in metafunc.fixturenames:
        invalid_mock_args = get_schema_test_data("invalid", models, validators)
        metafunc.parametrize("model,validator,invalid_mock", invalid_mock_args)
