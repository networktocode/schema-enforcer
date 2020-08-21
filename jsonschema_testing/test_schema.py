# Standard Imports
import json
import os
import sys
from pathlib import Path

from glob import glob
from collections import defaultdict

# Third Party Imports
import click
from termcolor import colored
from jsonschema import Draft7Validator
from ruamel.yaml import YAML

from jsonschema_testing import utils
from jsonschema_testing import config
from .schemas.manager import SchemaManager
from .instances.file import InstanceFileManager
from .ansible_inventory import AnsibleInventory
from .utils import warn, error


import pkgutil
import re

SCHEMA_TEST_DIR = "tests"


def validate_instances(schema_manager, instance_manager, show_pass=False, strict=False):
    """[summary]

    Args:
        schema_manager (SchemaManager): [description]
        instance_manager (InstanceFileManager): [description]
        show_pass (bool, optional): Show in CLI all tests executed even if they pass. Defaults to False.
        strict (bool, optional): 
    """

    error_exists = False

    for instance in instance_manager.instances:

        error_exists_inner_loop = False

        for err in instance.validate(schema_manager, strict):

            if len(err.absolute_path) > 0:
                print(
                    colored(f"FAIL", "red") + f" | [ERROR] {err.message}"
                    f" [FILE] {instance.path}/{instance.filename}"
                    f" [PROPERTY] {':'.join(str(item) for item in err.absolute_path)}"
                    # f" [SCHEMA] {schema_file.split('/')[-1]}"
                    f" [SCHEMA] {','.join(instance.matches)}"
                )
            if len(err.absolute_path) == 0:
                print(
                    colored(f"FAIL", "red") + f" | [ERROR] {err.message}"
                    f" [FILE] {instance.path}/{instance.filename}"
                    # f" [SCHEMA] {schema_file.split('/')[-1]}"
                    f" [SCHEMA] {','.join(instance.matches)}"
                )

            error_exists = True
            error_exists_inner_loop = True

        if not error_exists_inner_loop and show_pass:
            # print(colored(f"PASS", "green") + f" | [SCHEMA] {schema_file.split('/')[-1]} | [FILE] {instance_file}")
            # For now show the fully qualified schema id, in the future if we have our own BASE_URL
            # we could for example strip that off to have a ntc/core/ntp shortened names displayed
            print(
                colored(f"PASS", "green")
                + f" | [SCHEMA] {','.join(instance.matches)} | [FILE] {instance.path}/{instance.filename}"
            )

    if not error_exists:
        print(colored("ALL SCHEMA VALIDATION CHECKS PASSED", "green"))


@click.group()
def main():
    pass


@click.option("--show-pass", default=False, help="Shows validation checks that passed", is_flag=True, show_default=True)
@click.option(
    "--strict",
    default=False,
    help="Forces a stricter schema check that warns about unexpected additional properties",
    is_flag=True,
    show_default=True,
)
@click.option(
    "--show-checks",
    default=False,
    help="Shows the schemas to be checked for each instance file",
    is_flag=True,
    show_default=True,
)
@main.command()
def validate_schema(show_pass, show_checks, strict):
    """
    Validates instance files against defined schema

    Args:
        show_pass (bool): show successful schema validations
        show_checks (bool): show schemas which will be validated against each instance file
        strict (bool): Forces a stricter schema check that warns about unexpected additional properties
    """
    config.load()

    # ---------------------------------------------------------------------
    # Load Schema(s) from disk
    # ---------------------------------------------------------------------
    sm = SchemaManager(config=config.SETTINGS)

    if not sm.schemas:
        error("No schemas were loaded")
        sys.exit(1)

    # ---------------------------------------------------------------------
    # Load Instances
    # ---------------------------------------------------------------------
    ifm = InstanceFileManager(config=config.SETTINGS)

    if not ifm.instances:
        error("No instance files were found to validate")
        sys.exit(1)

    if show_checks:
        ifm.print_instances_schema_mapping()
        sys.exit(0)

    validate_instances(schema_manager=sm, instance_manager=ifm, show_pass=show_pass, strict=strict)


@click.option("--show-pass", default=False, help="Shows validation checks that passed", is_flag=True, show_default=True)
@main.command()
def check_schemas(show_pass):
    """
    Self validates that the defined schema files are compliant with draft7

    Args:
        show_pass (bool): show successful schema validations
    """
    config.load()
    # ---------------------------------------------------------------------
    # Load Schema(s) from disk
    # ---------------------------------------------------------------------
    sm = SchemaManager(config=config.SETTINGS)

    if not sm.schemas:
        error("No schemas were loaded")
        sys.exit(1)

    error_exists = False
    for schema_id, schema in sm.iter_schemas():
        error_exists_inner_loop = False
        for err in schema.check_if_valid():
            error_exists_inner_loop = True
            error_exists = True
            if len(err.absolute_path) > 0:
                print(
                    colored(f"FAIL", "red") + f" | [ERROR] {err.message}"
                    f" [PROPERTY] {':'.join(str(item) for item in err.absolute_path)}"
                    f" [SCHEMA] {schema_id}"
                )
            if len(err.absolute_path) == 0:
                print(colored(f"FAIL", "red") + f" | [ERROR] {err.message}" f" [SCHEMA] {schema_id}")

        if not error_exists_inner_loop and show_pass:
            print(colored(f"PASS", "green") + f" | [SCHEMA] {schema_id} is valid")

    if not error_exists:
        print(colored("ALL SCHEMAS ARE VALID", "green"))


@main.command()
@click.option("--schema", "-s", help=" The name of the schema to validate against.", required=True)
@click.option(
    "--mock", "-m", "mock_file", help="The name of the mock file to view the error attributes.", required=True
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
    config.load()

    sm = SchemaManager(config=config.SETTINGS)

    # TODO need to refactor this one this one
    # schema_root_dir = os.path.realpath(CFG["json_schema_path"])
    # schema_filepath = f"{CFG['json_schema_definitions']}/{schema}.json"
    # mock_file = f"tests/mocks/{schema}/invalid/{mock}.json"

    # validator = utils.load_schema_from_json_file(schema_root_dir, schema_filepath)
    # error_attributes = utils.generate_validation_error_attributes(mock_file, validator)
    # print()
    # for attr, value in error_attributes.items():
    #     print(f"{attr:20} = {value}")


@main.command()
@click.option("--schema", help="The name of the schema to validate against.", required=True)
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
    config.load()
    # TODO need to refactor this one this one
    # schema_root_dir = os.path.realpath(CFG["json_schema_path"])

    # schema_filepath = f"{CFG['json_schema_definitions']}/{schema}.json"
    # validator = utils.load_schema_from_json_file(schema_root_dir, schema_filepath)
    # mock_path = f"tests/mocks/{schema}/invalid"
    # for invalid_mock in glob(f"{mock_path}/*.json"):
    #     error_attributes = utils.generate_validation_error_attributes(invalid_mock, validator)
    #     mock_attributes = {attr: str(error_attributes[attr]) for attr in error_attributes}
    #     mock_attributes_formatted = utils.ensure_strings_have_quotes_mapping(mock_attributes)
    #     mock_response = f"{invalid_mock[:-4]}yml"
    #     print(f"Writing file to {mock_response}")
    #     with open(mock_response, "w", encoding="utf-8") as fh:
    #         utils.YAML_HANDLER.dump(mock_attributes_formatted, fh)


@main.command()
@click.option("--inventory", "-i", help="Ansible inventory file.", required=True)
@click.option("--host", "-h", "limit", help="Limit the execution to a single host.", required=False)
@click.option("--show-pass", default=False, help="Shows validation checks that passed", is_flag=True, show_default=True)
def ansible(inventory, limit, show_pass):
    """
    Validate the hostvar for all hosts within the Ansible inventory provided. 
    The hostvar are dynamically rendered based on groups. 

    For each host, if a variable `jsonschema_mapping` is defined, it will be used
    to determine which schemas should be use to validate each key.

    Args:
        inventory (string): The name of the inventory file to validate against
        limit (string, None): Name of a host to limit the execution to
        show_pass (bool): Shows validation checks that passed Default to False

    Example:
        $ cd examples/ansible
        $ ls -ls
        total 8
        drwxr-xr-x  5 damien  staff   160B Jul 25 16:37 group_vars
        drwxr-xr-x  4 damien  staff   128B Jul 25 16:37 host_vars
        -rw-r--r--  1 damien  staff    69B Jul 25 16:37 inventory.ini
        drwxr-xr-x  4 damien  staff   128B Jul 25 16:37 schema
        $ test-schema ansible -i inventory.ini
        Found 4 hosts in the ansible inventory
        FAIL | [ERROR] 12 is not of type 'string' [HOST] leaf1 [PROPERTY] dns_servers:0:address [SCHEMA] schemas/dns_servers
        FAIL | [ERROR] 12 is not of type 'string' [HOST] leaf2 [PROPERTY] dns_servers:0:address [SCHEMA] schemas/dns_servers
        $ test-schema ansible -i inventory.ini -h leaf1
        Found 4 hosts in the ansible inventory
        FAIL | [ERROR] 12 is not of type 'string' [HOST] leaf1 [PROPERTY] dns_servers:0:address [SCHEMA] schemas/dns_servers
        $ test-schema ansible -i inventory.ini -h spine1 --show-pass
        WARNING | Could not find pyproject.toml in the current working directory.
        WARNING | Script is being executed from CWD: /Users/damien/projects/jsonschema_testing/examples/ansible
        WARNING | Using built-in defaults for [tool.jsonschema_testing]
        WARNING | [tool.jsonschema_testing.schema_mapping] is not defined, instances must be tagged to apply schemas to instances
        Found 4 hosts in the inventory
        PASS | [HOST] spine1 | [VAR] dns_servers | [SCHEMA] schemas/dns_servers
        PASS | [HOST] spine1 | [VAR] interfaces | [SCHEMA] schemas/interfaces
        ALL SCHEMA VALIDATION CHECKS PASSED
    """
    config.load()

    def print_error(host, schema_id, err):
        """Print Validation error for ansible host to screen.
        
        Args:
            host (host): Ansible host object
            schema_id (string): Name of the schema
            err (ValidationError): JsonSchema Validation error
        """
        if len(err.absolute_path) > 0:
            print(
                colored(f"FAIL", "red") + f" | [ERROR] {err.message}"
                f" [HOST] {host.name}"
                f" [PROPERTY] {':'.join(str(item) for item in err.absolute_path)}"
                f" [SCHEMA] {schema_id}"
            )

        elif len(err.absolute_path) == 0:
            print(colored(f"FAIL", "red") + f" | [ERROR] {err.message}" f" [HOST] {host.name}" f" [SCHEMA] {schema_id}")

    # ---------------------------------------------------------------------
    # Load Schema(s) from disk
    # ---------------------------------------------------------------------
    sm = SchemaManager(config=config.SETTINGS)

    if not sm.schemas:
        error("No schemas were loaded")
        sys.exit(1)

    # ---------------------------------------------------------------------
    # Load Ansible Inventory file
    #  - generate hostvar for all devices in the inventory
    #  - Validate Each key in the hostvar individually against the schemas defined in the var jsonschema_mapping
    # ---------------------------------------------------------------------
    inv = AnsibleInventory(inventory=inventory)
    hosts = inv.get_hosts_containing()
    print(f"Found {len(hosts)} hosts in the inventory")

    error_exists = False

    for host in hosts:
        if limit and host.name != limit:
            continue

        # Generate host_var and automatically remove all keys inserted by ansible
        hostvar = inv.get_clean_host_vars(host)

        # if jsonschema_mapping variable is defined, used it to determine which schema to use to validate each key
        # if jsonschema_mapping is not defined, validate each key in the inventory agains all schemas in the SchemaManager
        mapping = None
        if "jsonschema_mapping" in hostvar:
            mapping = hostvar["jsonschema_mapping"]
            del hostvar["jsonschema_mapping"]

        applicable_schemas = {}

        for key, value in hostvar.items():
            if mapping and key in mapping.keys():
                applicable_schemas = {schema_id: sm.schemas[schema_id] for schema_id in mapping[key]}
            else:
                applicable_schemas = sm.schemas

            for schema_id, schema in applicable_schemas.items():
                error_exists_inner_loop = False
                for err in schema.validate({key: value}):
                    error_exists = True
                    error_exists_inner_loop = True
                    print_error(host, schema_id, err)

                if not error_exists_inner_loop and show_pass:
                    print(colored(f"PASS", "green") + f" | [HOST] {host.name} | [VAR] {key} | [SCHEMA] {schema_id}")

    if not error_exists:
        print(colored("ALL SCHEMA VALIDATION CHECKS PASSED", "green"))


if __name__ == "__main__":
    main()
