# Standard Imports
import json
import os
import sys
from pathlib import Path

from glob import glob
from collections import defaultdict

# Third Party Imports
import click
import toml
from termcolor import colored
from jsonschema import Draft7Validator
from ruamel.yaml import YAML

from jsonschema_testing import utils
import pkgutil

YAML_HANDLER = YAML()

SCHEMA_TEST_DIR = "tests"

CFG = utils.load_config()


def get_instance_filenames(file_extension, search_directory, excluded_filenames):
    """
    Returns a list of filenames for the instances that we are going to validate
    """

    data = utils.find_files(file_extension=file_extension,
                            search_directory=search_directory,
                            excluded_filenames=excluded_filenames)

    return data

def get_schemas(file_extension, search_directory, excluded_filenames, file_type):
    """
    Returns a dictionary of schema IDs and schema data
    """

    data = utils.load_data(file_extension=file_extension,
                            search_directory=search_directory,
                            excluded_filenames=excluded_filenames,
                            file_type=file_type,
                            data_key='$id')

    return data

def get_instance_schema_mapping(schemas, instances, schema_mapping):
    """
    Returns a dictionary of instances and the schema IDs they map to

    This is currently based on filenames, but could use wildcard patterns or other key detection heuristics in the future
    """
    # Dict to return matching schemas
    instance_schema_mapping = defaultdict(list)

    # Map each instance to a set of schemas to validate the instance data against.
    for instance_filename in instances:
        for filepattern, schema_ids in schema_mapping.items():
            if instance_filename.endswith(filepattern):
                # Append the list of schema IDs to the matching filename, 
                # Note that is does not confirm that the schema is actually known/loaded
                # we could do that check here, but currently it is done in check_schemas_exist
                instance_schema_mapping[instance_filename].extend(schema_ids)

    return instance_schema_mapping

def check_schemas_exist(schemas, instance_file_to_schemas_mapping):
    """
    Verifies that the schemas declared in instance files are loaded and can be used to 
    validate instance data against. If this is not the case, a warning message is logged
    informing the script user that validation for the schema declared will not be checked

    Args:
        schemas ([type]): [description]
        instance_file_to_schemas_mapping ([type]): [description]
    """
    schemas_loaded_from_files = schemas.keys()

    for file_name, schema_names in instance_file_to_schemas_mapping.items():
        for schema_name in schema_names:
            if schema_name not in schemas_loaded_from_files:
                print(colored(f"WARN", "yellow") + f" | schema '{schema_name}' Will not be checked. It is declared in {file_name} but is not loaded.")
                errors = True

def validate_instances(schemas, instances, instance_file_to_schemas_mapping, show_pass=False):

    error_exists = False

    for schema_file, schema in schemas.items():
        config_validator = Draft7Validator(schema)

        for instance_file in instances:
            # We load the data on demand now, so we are not storing all instances in memory
            instance_data = utils.load_file(instance_file)

            # Get schemas which should be checked for this instance file. If the instance should not
            # be checked for adherence to this schema, don't skip checking it.
            if not schema["$id"] in instance_file_to_schemas_mapping.get(instance_file):
                continue

            error_exists_inner_loop = False

            for error in config_validator.iter_errors(instance_data):
                if len(error.absolute_path) > 0:
                    print(colored(f"FAIL", "red") + f" | [ERROR] {error.message}"
                    f" [FILE] {instance_file}"
                    f" [PROPERTY] {':'.join(str(item) for item in error.absolute_path)}"
                    f" [SCHEMA] {schema_file.split('/')[-1]}")
                if len(error.absolute_path) == 0:
                    print(colored(f"FAIL", "red") + f" | [ERROR] {error.message}"
                    f" [FILE] {instance_file}"
                    f" [SCHEMA] {schema_file.split('/')[-1]}")

                error_exists = True
                error_exists_inner_loop = True

            if not error_exists_inner_loop and show_pass:
                print(colored(f"PASS", "green") + f" | [SCHEMA] {schema_file.split('/')[-1]} | [FILE] {instance_file}")

    if not error_exists:
        print(colored("ALL SCHEMA VALIDATION CHECKS PASSED", "green"))


@click.group()
def main():
    pass

@main.command()
@click.option(
    "--yaml-path",
    help="The root directory containing YAML files to convert to JSON."
)
@click.option(
    "--json-path",
    help="The root directory to build JSON files from YAML files in ``yaml_path``."
)
def convert_yaml_to_json(yaml_path, json_path):
    """
    Reads YAML files and writes them to JSON files.

    Args:
        yaml_path (str): The root directory containing YAML files to convert to JSON.
        json_path (str): The root directory to build JSON files from YAML files in ``yaml_path``.

    Example:
        $ ls schema/
        yaml
        $ test-schema convert-yaml-to-json
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
    utils.convert_yaml_to_json(yaml_path or CFG["yaml_schema_path"], json_path or CFG["json_schema_path"])

@main.command()
@click.option(
    "--json-path",
    help="The root directory containing JSON files to convert to YAML."
)
@click.option(
    "--yaml-path",
    help="The root directory to build YAML files from JSON files in ``json_path``."
)
def convert_json_to_yaml(json_path, yaml_path):
    """
    Reads JSON files and writes them to YAML files.

    Args:
        json_path (str): The root directory containing JSON files to convert to YAML.
        yaml_path (str): The root directory to build YAML files from JSON files in ``json_path``.

    Example:
        $ ls schema/
        json
        $ test-schema convert-json-to-yaml
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
    utils.convert_json_to_yaml(json_path or CFG["json_schema_path"], yaml_path or CFG["yaml_schema_path"])

@main.command()
@click.option(
    "--json-schema-path",
    help="The path to JSONSchema schema definitions.", 
)
@click.option(
    "--output-path", "-o",
    help="The path to write updated JSONSchema schema files.", 
)
def resolve_json_refs(
    json_schema_path,
    output_path,
):
    """
    Loads JSONSchema schema files, resolves ``refs``, and writes to a file.

    Args:
        json_schema_path: The path to JSONSchema schema definitions.
        output_path: The path to write updated JSONSchema schema files.

    Example:
    $ ls schema/json/
    definitions    schemas
    $ test-schema resolve-json-refs
    Converting schema/json/schemas/ntp.json -> schema/json/full/ntp.json
    Converting schema/json/schemas/snmp.json -> schema/json/full/snmp.json
    $ ls schema/json
    definitions    full    schemas
    $
    """
    utils.resolve_json_refs(json_schema_path or CFG["json_schema_definitions"], output_path or CFG["json_full_schema_definitions"])

@click.option(
    "--show-pass", default=False, help="Shows validation checks that passed", is_flag=True, show_default=True
)
@click.option(
    "--show-checks", 
    default=False, 
    help="Shows the schemas to be checked for each instance file", 
    is_flag=True, 
    show_default=True
)
@main.command()
def validate_schema(show_pass, show_checks):
    """
    Validates instance files against defined schema

    Args:
        show_pass (bool): show successful schema validations
        show_checks (bool): show schemas which will be validated against each instance file
    """

    # Get Dict of Instance File Path and Data
    instances = get_instance_filenames(
        file_extension=CFG.get("instance_file_extension", ".yml"),
        search_directory=CFG.get("instance_search_directory", "./"),
        excluded_filenames=CFG.get("instance_exclude_filenames", [])
        )

    # Get Dict of Schema File Path and Data
    schemas = get_schemas(
        file_extension=CFG.get("schema_file_extension", ".json"),
        search_directory=CFG.get("schema_search_directory", "./"),
        excluded_filenames=CFG.get("schema_exclude_filenames", []),
        file_type=CFG.get("schema_file_type", "json")
        )

    # Get Mapping of Instance to Schema
    instance_file_to_schemas_mapping = get_instance_schema_mapping(
        schemas=schemas,
        instances=instances,
        schema_mapping=CFG.get("schema_mapping")
        )


    if show_checks:
        print("Instance File                                     Schema")
        print("-" * 80)
        for instance_file, schema in instance_file_to_schemas_mapping.items():
            print(f"{instance_file:50} {schema}")
        sys.exit(0)

    check_schemas_exist(schemas, instance_file_to_schemas_mapping)

    validate_instances(
        schemas=schemas,
        instances=instances,
        instance_file_to_schemas_mapping=instance_file_to_schemas_mapping,
        show_pass=show_pass
    )


@click.option(
    "--show-pass", default=False, help="Shows validation checks that passed", is_flag=True, show_default=True
)
@click.option(
    "--show-checks",
    default=False,
    help="Shows the schemas to be checked for each instance file",
    is_flag=True,
    show_default=True
)
@main.command()
def check_schemas(show_pass, show_checks):
    """
    Self validates that the defined schema files are compliant with draft7

    Args:
        show_pass (bool): show successful schema validations
        show_checks (bool): show schemas which will be validated against each instance file
    """

    # Get Dict of Schema File Path and Data
    instances = get_schemas(
        file_extension=CFG.get("schema_file_extension", ".json"),
        search_directory=CFG.get("schema_search_directory", "./"),
        excluded_filenames=CFG.get("schema_exclude_filenames", []),
        file_type=CFG.get("schema_file_type", "json")
        )

    v7data = pkgutil.get_data("jsonschema", "schemas/draft7.json")
    v7schema = json.loads(v7data.decode("utf-8"))
    schemas = {v7schema['$id']: v7schema}

    # Get Mapping of Instance to Schema
    instance_file_to_schemas_mapping = {x: ["http://json-schema.org/draft-07/schema#"] for x in instances.keys()}

    check_schemas_exist(schemas, instance_file_to_schemas_mapping)

    if show_checks:
        print("Instance File                                     Schema")
        print("-" * 80)
        for instance_file, schema in instance_file_to_schemas_mapping.items():
            print(f"{instance_file:50} {schema}")
        sys.exit(0)

    validate_instances(
        schemas=schemas,
        instances=instances,
        instance_file_to_schemas_mapping=instance_file_to_schemas_mapping,
        show_pass=show_pass
    )



# def validate(context, schema, vars_dir=None, hosts=None):
#     """
#     Executes Pytest to validate data against schema

#     Args:
#         schema (list): The specific schema to execute tests against.
#         vars_dir (str): The path to device directories containig variable definitions.
#         hosts (str): The comma-separated subset of hosts to execute against.

#     Example:
#         $ python -m invoke validate -s ntp -s snmp -v ../my_project/hostvars -h csr1,eos1
#         python -m pytest tests/test_data_against_schema.py --schema=ntp --schema=ntp --hosts=csr1,eos1 -vv
#         ============================= test session starts =============================
#         collecting ... collected 4 items
#         tests/test_data_against_schema.py::test_config_definitions_against_schema[ntp-validator0-csr1] PASSED [ 25%]
#         tests/test_data_against_schema.py::test_config_definitions_against_schema[snmp-validator1-csr1] PASSED [ 50%]
#         tests/test_data_against_schema.py::test_config_definitions_against_schema[ntp-validator0-eos1] PASSED [ 75%]
#         tests/test_data_against_schema.py::test_config_definitions_against_schema[snmp-validator1-eos1] PASSED [ 100%]
#         $
#     """
#     cmd = f"python -m pytest {SCHEMA_TEST_DIR}/test_data_against_schema.py"
#     if schema:
#         schema_flag = " --schema=".join(schema)
#         cmd += f" --schema={schema_flag}"
#     if vars_dir is not None:
#         cmd += f" --hostvars={vars_dir}"
#     if hosts is not None:
#         cmd += f" --hosts={hosts}"
#     context.run(f"{cmd} -vv", echo=True)

@main.command()
@click.option(
    "--schema", "-s",
    help=" The name of the schema to validate against.",
    required=True
)
@click.option(
    "--mock", "-m", "mock_file",
    help="The name of the mock file to view the error attributes.",
    required=True
)
def view_validation_error(schema, mock):
    """
    Generates ValidationError from invalid mock data and prints available Attrs.

    This is meant to be used as an aid to generate test cases for invalid mock
    schema data.

    Args:
        schema (str): The name of the schema to validate against.
        mock_file (str): The name of the mock file to view the error attributes.

    Example:
        $ test-schema view-validation-error -s ntp -m invalid_ip

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

@main.command()
@click.option(
    "--output-path", "-o",
    help="The path to store the variable files.", 
)
@click.option(
    "--schema-path", "-s",
    help="The path to JSONSchema schema definitions.", 
)
@click.option(
    "--ansible-inventory", "-i", "inventory_path",
    help="The path to ansible inventory.", 
)
def generate_hostvars(
    output_path,
    schema_path,
    inventory_path,
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
        $ test-schema --generate-hostvars -s schema/json -o outfiles/hostvars -i production/hosts.ini
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
    utils.generate_hostvars(
        inventory_path or CFG["inventory_path"], 
        schema_path or CFG["json_schema_definitions"], 
        output_path or CFG["device_variables"])

@main.command()
@click.option(
    "--schema",
    help="The name of the schema to validate against.",
    required=True
)
def generate_invalid_expected(schema):
    """
    Generates expected ValidationError data from mock_file and writes to mock dir.

    This is meant to be used as an aid to generate test cases for invalid mock
    schema data.

    Args:
        schema (str): The name of the schema to validate against.

    Example:
        $ ls tests/mocks/ntp/invalid/
        invalid_format.json    invalid_ip.json
        $ test-schema generate-invalid-expected --schema ntp
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


if __name__ == "__main__":
    main()