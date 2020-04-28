#!/usr/bin/env python

import os
from glob import glob
from collections import defaultdict

from invoke import task

CFG = defaultdict(str)
SCHEMA_TEST_DIR = "tests"
# The build and install phase do not require all packages
if os.sys.argv[1] not in {"build", "install", "--list"}:
    try:
        import utils
    except ModuleNotFoundError:
        from jsonschema_testing import utils

    CFG = utils.load_config()


IS_WINDOWS = os.sys.platform.startswith("win")
SEP = os.path.sep
if not IS_WINDOWS:
    EXE_PATH = f".venv{SEP}bin{SEP}"
else:
    EXE_PATH = f".venv{SEP}Scripts{SEP}"

PYTHON_EXECUTABLES = ["python", "pip", "invoke", "activate"]
for exe in PYTHON_EXECUTABLES:
    var_name = f"{exe.upper()}_EXE"
    if not IS_WINDOWS:
        locals()[var_name] = f"{EXE_PATH}{exe}"
    else:
        if exe != "activate":
            locals()[var_name] = f"{EXE_PATH}{exe}.exe"
        else:
            locals()[var_name] = f"{EXE_PATH}{exe}.bat"


@task
def install(context):
    """
    installs ``requirments.txt`` into Python Environment.
    """
    context.run(f"{PIP_EXE} install -r requirements.txt")  # noqa F821


@task(post=[install])
def build(context):
    """
    Creates a Virtual Environment and installs ``requirements.txt` file.
    """
    context.run(f"{os.sys.executable} -m virtualenv .venv")


@task
def convert_yaml_to_json(
    context, yaml_path=CFG["yaml_schema_path"], json_path=CFG["json_schema_path"],
):
    """
    Reads YAML files and writes them to JSON files.

    Args:
        yaml_path (str): The root directory containing YAML files to convert to JSON.
        json_path (str): The root directory to build JSON files from YAML files in ``yaml_path``.

    Example:
        $ ls schema/
        yaml
        $ python -m invoke convert-yaml-to-json -y schema/yaml -j schema/json
        Converting schema/yaml/definitions/arrays/ip.yml ->
        schema/yaml/definitions/arrays/ip.json
        Converting schema/yaml/definitions/objects/ip.yml ->
        schema/yaml/definitions/objects/ip.json
        Converting schema/yaml/definitions/properties/ip.yml ->
        schema/yaml/definitions/properties/ip.json
        Converting schema/yaml/schemas/ntp.yml ->
        schema/yaml/schemas/ntp.json
        $ ls schema/
        json    yaml
        $
    """
    utils.convert_yaml_to_json(yaml_path, json_path)


@task
def convert_json_to_yaml(
    context, json_path=CFG["json_schema_path"], yaml_path=CFG["yaml_schema_path"],
):
    """
    Reads JSON files and writes them to YAML files.

    Args:
        json_path (str): The root directory containing JSON files to convert to YAML.
        yaml_path (str): The root directory to build YAML files from JSON files in ``json_path``.

    Example:
        $ ls schema/
        json
        $ python -m invoke convert-json-to-yaml -y schema/yaml -j schema/json
        Converting schema/yaml/definitions/arrays/ip.json ->
        schema/yaml/definitions/arrays/ip.yml
        Converting schema/yaml/definitions/objects/ip.json ->
        schema/yaml/definitions/objects/ip.yml
        Converting schema/yaml/definitions/properties/ip.json ->
        schema/yaml/definitions/properties/ip.yml
        Converting schema/yaml/schemas/ntp.json ->
        schema/yaml/schemas/ntp.yml
        $ ls schema/
        json    yaml
        $
    """
    utils.convert_json_to_yaml(json_path, yaml_path)


@task
def resolve_json_refs(
    context,
    json_schema_path=CFG["json_schema_definitions"],
    output_path=CFG["json_full_schema_definitions"],
):
    """
    Loads JSONSchema schema files, resolves ``refs``, and writes to a file.

    Args:
        json_schema_path: The path to JSONSchema schema definitions.
        output_path: The path to write updated JSONSchema schema files.

    Example:
    $ ls schema/json/
    definitions    schemas
    $ python -m invoke resolve-json-refs -j schema/json/schemas -o schema/json/full
    Converting schema/json/schemas/ntp.json -> schema/json/full/ntp.json
    Converting schema/json/schemas/snmp.json -> schema/json/full/snmp.json
    $ ls schema/json
    definitions    full    schemas
    $
    """
    utils.resolve_json_refs(json_schema_path, output_path)


@task(iterable=["schema"])
def validate(context, schema, vars_dir=None, hosts=None):
    """
    Executes Pytest to validate data against schema

    Args:
        schema (list): The specific schema to execute tests against.
        vars_dir (str): The path to device directories containig variable definitions.
        hosts (str): The comma-separated subset of hosts to execute against.

    Example:
        $ python -m invoke validate -s ntp -s snmp -v ../my_project/hostvars -h csr1,eos1
        python -m pytest tests/test_data_against_schema.py --schema=ntp --schema=ntp --hosts=csr1,eos1 -vv
        ============================= test session starts =============================
        collecting ... collected 4 items
        tests/test_data_against_schema.py::test_config_definitions_against_schema[ntp-validator0-csr1] PASSED [ 25%]
        tests/test_data_against_schema.py::test_config_definitions_against_schema[snmp-validator1-csr1] PASSED [ 50%]
        tests/test_data_against_schema.py::test_config_definitions_against_schema[ntp-validator0-eos1] PASSED [ 75%]
        tests/test_data_against_schema.py::test_config_definitions_against_schema[snmp-validator1-eos1] PASSED [ 100%]
        $
    """
    cmd = f"python -m pytest {SCHEMA_TEST_DIR}/test_data_against_schema.py"
    if schema:
        schema_flag = " --schema=".join(schema)
        cmd += f" --schema={schema_flag}"
    if vars_dir is not None:
        cmd += f" --hostvars={vars_dir}"
    if hosts is not None:
        cmd += f" --hosts={hosts}"
    context.run(f"{cmd} -vv", echo=True)


@task
def view_validation_error(context, schema, mock_file):
    """
    Generates ValidationError from invalid mock data and prints available Attrs.

    This is meant to be used as an aid to generate test cases for invalid mock
    schema data.

    Args:
        schema (str): The name of the schema to validate against.
        mock_file (str): The name of the mock file to view the error attributes.

    Example:
        $ python -m invoke view-validation-error -s ntp -m invalid_ip

        absolute_path        = deque(['ntp_servers', 0, 'address'])
        absolute_schema_path = deque(['properties', 'ntp_servers', 'items', ...])
        cause                = None
        context              = []
        message              = '10.1.1.1000' is not a 'ipv4'
        parent               = None
        path                 = deque(['ntp_servers', 0, 'address'])
        schema               = {'type': 'string', 'format': 'ipv4'}
        schema_path          = deque(['properties', 'ntp_servers', 'items', ...])
        validator            = format
        validator_value      = ipv4

        $
    """
    schema_root_dir = os.path.realpath(CFG["json_schema_path"])
    schema_filepath = f"{CFG['json_schema_definitions']}/{schema}.json"
    mock_file = f"tests/mocks/{schema}/invalid/{mock_file}.json"

    validator = utils.load_schema_from_json_file(schema_root_dir, schema_filepath)
    error_attributes = utils.generate_validation_error_attributes(mock_file, validator)
    print()
    for attr, value in error_attributes.items():
        print(f"{attr:20} = {value}")


@task
def generate_hostvars(
    context,
    output_path=CFG["device_variables"],
    schema_path=CFG["json_schema_definitions"],
    inventory_path=CFG["inventory_path"],
):
    """
    Generates ansible variables and creates a file per schema for each host.

    Args:
        output_path (str): The path to store the variable files.
        schema_path (str): The path to JSONSchema schema definitions.
        inventory_path (str): The path to ansible inventory.

    Example:
        $ ls example/hostvars
        $
        $ python -m invoke generate-hostvars -o example/hostvars -s schema/json/schemas -i inventory
        Generating var files for bra-saupau-rt1
        -> dns
        -> syslog
        Generating var files for chi-beijing-rt1
        -> bgp
        -> dns
        -> syslog
        Generating var files for mex-mexcty-rt1
        -> dns
        -> syslog
        $ ls example/hostvars/
        bra-saupau-rt1    chi-beijing-rt1    mex-mexcty-rt1
        $
    """
    os.makedirs(output_path, exist_ok=True)
    utils.generate_hostvars(inventory_path, schema_path, output_path)


@task
def create_invalid_expected(context, schema):
    """
    Generates expected ValidationError data from mock_file and writes to mock dir.

    This is meant to be used as an aid to generate test cases for invalid mock
    schema data.

    Args:
        schema (str): The name of the schema to validate against.

    Example:
        $ ls tests/mocks/ntp/invalid/
        invalid_format.json    invalid_ip.json
        $ python -m invoke create-invalid-expected -s ntp
        Writing file to tests/mocks/ntp/invalid/invalid_format.yml
        Writing file to tests/mocks/ntp/invalid/invalid_ip.yml
        $ ls tests/mocks/ntp/invalid/
        invalid_format.json    invalid_format.yml    invalid_ip.json
        invalid_ip.yml
        $
    """
    schema_root_dir = os.path.realpath(CFG["json_schema_path"])
    schema_filepath = f"{CFG['json_schema_definitions']}/{schema}.json"
    validator = utils.load_schema_from_json_file(schema_root_dir, schema_filepath)
    mock_path = f"tests/mocks/{schema}/invalid"
    for invalid_mock in glob(f"{mock_path}/*.json"):
        error_attributes = utils.generate_validation_error_attributes(
            invalid_mock, validator
        )
        mock_attributes = {attr: str(error_attributes[attr]) for attr in error_attributes}
        mock_attributes_formatted = utils.ensure_strings_have_quotes_mapping(
            mock_attributes
        )
        mock_response = f"{invalid_mock[:-4]}yml"
        print(f"Writing file to {mock_response}")
        with open(mock_response, "w", encoding="utf-8") as fh:
            utils.YAML_HANDLER.dump(mock_attributes_formatted, fh)
