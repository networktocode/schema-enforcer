"""main cli commands."""
import sys

import click
from termcolor import colored

from schema_enforcer.utils import MutuallyExclusiveOption
from schema_enforcer import config
from schema_enforcer.schemas.manager import SchemaManager
from schema_enforcer.instances.file import InstanceFileManager
from schema_enforcer.utils import error
from schema_enforcer.exceptions import InvalidJSONSchema


@click.group()
def main():
    """SCHEMA ENFORCER.

    This tool is used to ensure data adheres to a schema definition. The data can come
    from YAML files, JSON files, or an Ansible inventory. The schema to which the data
    should adhere can currently be defined using the JSONSchema language in YAML or JSON
    format.
    """


@click.option(
    "--show-pass",
    default=False,
    help="Shows validation checks that passed",
    is_flag=True,
    show_default=True,
)
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
    help="Shows the schemas to be checked for each structured data file",
    is_flag=True,
    show_default=True,
)
@main.command()
def validate(show_pass, show_checks, strict):  # noqa D205
    """Validates instance files against defined schema.

    \f

    Args:
        show_pass (bool): show successful schema validations
        show_checks (bool): show schemas which will be validated against each instance file
        strict (bool): Forces a stricter schema check that warns about unexpected additional properties
    """
    config.load()

    # ---------------------------------------------------------------------
    # Load Schema(s) from disk
    # ---------------------------------------------------------------------
    try:
        smgr = SchemaManager(config=config.SETTINGS)
    except InvalidJSONSchema as exc:
        error(str(exc))
        sys.exit(1)

    if not smgr.schemas:
        error("No schemas were loaded")
        sys.exit(1)

    # ---------------------------------------------------------------------
    # Load Instances
    # ---------------------------------------------------------------------
    ifm = InstanceFileManager(config=config.SETTINGS)

    if not ifm.instances:
        error("No instance files were found to validate")
        sys.exit(1)

    if config.SETTINGS.data_file_automap:
        ifm.add_matches_by_property_automap(smgr)

    if show_checks:
        ifm.print_schema_mapping()
        sys.exit(0)

    error_exists = False
    for instance in ifm.instances:
        for result in instance.validate(smgr, strict):
            result.instance_type = "FILE"
            result.instance_name = instance.filename
            result.instance_location = instance.path

            if not result.passed():
                error_exists = True
                result.print()

            elif result.passed() and show_pass:
                result.print()

    if not error_exists:
        print(colored("ALL SCHEMA VALIDATION CHECKS PASSED", "green"))
    else:
        sys.exit(1)


@click.option(
    "--list",
    "list_schemas",
    default=False,
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["generate_invalid", "check", "schema-id", "dump"],
    help="List all available schemas",
    is_flag=True,
)
@click.option(
    "--dump",
    "dump_schemas",
    default=False,
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["generate_invalid", "check", "list"],
    help="Dump full schema for all schemas or schema-id",
    is_flag=True,
)
@click.option(
    "--check",
    default=False,
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["generate_invalid", "list", "dump"],
    help="Validates that all schemas are valid (spec and unit tests)",
    is_flag=True,
)
@click.option(
    "--generate-invalid",
    default=False,
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["check", "list", "dump"],
    help="Generates expected invalid result from a given schema [--schema-id] and data defined in a data file",
    is_flag=True,
)
@click.option(
    "--schema-id",
    default=None,
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["list"],
    help="The name of a schema.",
)
@main.command()
def schema(check, generate_invalid, list_schemas, schema_id, dump_schemas):  # noqa: D417,D301,D205
    """Manage your schemas.

    \f

    Args:
        check (bool): Validates that all schemas are valid (spec and unit tests)
        generate_invalid (bool): Generates expected invalid data from a given schema
        list_schemas (bool): List all available schemas
        schema_id (str): Name of schema to evaluate
        dump_schemas (bool): Dump all schema data or a single schema if schema_id is provided
    """
    if not check and not generate_invalid and not list_schemas and not schema_id and not dump_schemas:
        error(
            "The 'schema' command requires one or more arguments. You can run the command 'schema-enforcer schema --help' to see the arguments available."
        )
        sys.exit(1)

    config.load()

    # ---------------------------------------------------------------------
    # Load Schema(s) from disk
    # ---------------------------------------------------------------------
    try:
        smgr = SchemaManager(config=config.SETTINGS)
    except InvalidJSONSchema as exc:
        error(str(exc))
        sys.exit(1)

    if not smgr.schemas:
        error("No schemas were loaded")
        sys.exit(1)

    if list_schemas:
        smgr.print_schemas_list()
        sys.exit(0)

    if dump_schemas:
        smgr.dump_schema(schema_id)
        sys.exit(0)

    if generate_invalid:
        if not schema_id:
            sys.exit("Please indicate the schema you'd like to generate invalid data for using the --schema-id flag")
        smgr.generate_invalid_tests_expected(schema_id=schema_id)
        sys.exit(0)

    if check:
        smgr.test_schemas()
        sys.exit(0)


@main.command()
@click.option("--inventory", "-i", help="Ansible inventory file.", required=False)
@click.option(
    "--host",
    "-h",
    "limit",
    help="Limit the execution to a single host.",
    required=False,
)
@click.option(
    "--show-pass",
    default=False,
    help="Shows validation checks that passed",
    is_flag=True,
    show_default=True,
)
@click.option(
    "--show-checks",
    default=False,
    help="Shows the schemas to be checked for each ansible host",
    is_flag=True,
    show_default=True,
)
def ansible(
    inventory, limit, show_pass, show_checks
):  # pylint: disable=too-many-branches,too-many-locals,too-many-locals,too-many-statements  # noqa: D417,D301
    """Validate the hostvars for all hosts within an Ansible inventory.

    The hostvars are dynamically rendered based on groups to which each host belongs.
    For each host, if a variable `schema_enforcer_schema_ids` is defined, it will be used
    to determine which schemas should be use to validate each key. If this variable is
    not defined, the hostvars top level keys will be automatically mapped to a schema
    definition's top level properties to automatically infer which schema should be used
    to validate which hostvar.
    \f

    Args:
        inventory (string): The name of the file used to construct an ansible inventory.
        limit (string, None): Name of a host to limit the execution to.
        show_pass (bool): Shows validation checks that pass. Defaults to False.
        show_checks (bool): Shows the schema ids each host will be evaluated against.

    Example:
        $ cd examples/ansible
        $ ls -ls
        total 8
        drwxr-xr-x  5 damien  staff   160B Jul 25 16:37 group_vars
        drwxr-xr-x  4 damien  staff   128B Jul 25 16:37 host_vars
        -rw-r--r--  1 damien  staff    69B Jul 25 16:37 inventory.ini
        drwxr-xr-x  4 damien  staff   128B Jul 25 16:37 schema
        $ schema-enforcer ansible -i inventory.ini
        Found 4 hosts in the inventory
        FAIL | [ERROR] False is not of type 'string' [HOST] spine1 [PROPERTY] dns_servers:0:address
        FAIL | [ERROR] False is not of type 'string' [HOST] spine2 [PROPERTY] dns_servers:0:address
        $ schema-enforcer ansible -i inventory.ini -h leaf1
        Found 4 hosts in the inventory
        ALL SCHEMA VALIDATION CHECKS PASSED
        $ schema-enforcer ansible -i inventory.ini -h spine1 --show-pass
        Found 4 hosts in the inventory
        FAIL | [ERROR] False is not of type 'string' [HOST] spine1 [PROPERTY] dns_servers:0:address
        PASS | [HOST] spine1 [SCHEMA ID] schemas/interfaces
    """
    # Ansible is currently always installed by schema-enforcer. This was added in the interest of making ansible an
    # optional dependency. We decided to make two separate packages installable via PyPi, one with ansible, one without.
    # This has been left in the code until such a time as we implement the change to two packages so code will not need
    # to be re-written/
    try:
        from schema_enforcer.ansible_inventory import AnsibleInventory  # pylint: disable=import-outside-toplevel
    except ModuleNotFoundError:
        error(
            "ansible package not found, you can run the command 'pip install schema-enforcer[ansible]' to install the latest schema-enforcer sanctioned version."
        )
        sys.exit(1)

    if inventory:
        config.load(config_data={"ansible_inventory": inventory})
    else:
        config.load()

    # ---------------------------------------------------------------------
    # Load Schema(s) from disk
    # ---------------------------------------------------------------------
    try:
        smgr = SchemaManager(config=config.SETTINGS)
    except InvalidJSONSchema as exc:
        error(str(exc))
        sys.exit(1)

    if not smgr.schemas:
        error("No schemas were loaded")
        sys.exit(1)

    # ---------------------------------------------------------------------
    # Load Ansible Inventory file
    #  - generate hostvar for all devices in the inventory
    #  - Validate Each key in the hostvar individually against the schemas defined in the var jsonschema_mapping
    # ---------------------------------------------------------------------
    inv = AnsibleInventory(inventory=config.SETTINGS.ansible_inventory)
    hosts = inv.get_hosts_containing()
    print(f"Found {len(hosts)} hosts in the inventory")

    if show_checks:
        inv.print_schema_mapping(hosts, limit, smgr)
        sys.exit(0)

    error_exists = False

    for host in hosts:
        if limit and host.name != limit:
            continue

        # Acquire Host Variables
        hostvars = inv.get_clean_host_vars(host)

        # Acquire validation settings for the given host
        schema_validation_settings = inv.get_schema_validation_settings(host)
        declared_schema_ids = schema_validation_settings["declared_schema_ids"]
        strict = schema_validation_settings["strict"]
        automap = schema_validation_settings["automap"]

        # Validate declared schemas exist
        smgr.validate_schemas_exist(declared_schema_ids)

        # Acquire schemas applicable to the given host
        applicable_schemas = inv.get_applicable_schemas(hostvars, smgr, declared_schema_ids, automap)
        for schema_obj in applicable_schemas.values():
            # Combine host attributes into a single data structure matching to properties defined at the top level of the schema definition
            if not strict:
                data = {}
                for var in schema_obj.top_level_properties:
                    data.update({var: hostvars.get(var)})

            # If the schema_enforcer_strict bool is set, hostvars should match a single schema exactly.
            # Thus, we want to pass the entirety of the cleaned host vars into the validate method rather
            # than creating a data structure with only the top level vars defined by the schema.
            else:
                data = hostvars

            # Validate host vars against schema
            schema_obj.validate(data=data, strict=strict)

            for result in schema_obj.get_results():
                result.instance_type = "HOST"
                result.instance_hostname = host.name

                if not result.passed():
                    error_exists = True
                    result.print()

                elif result.passed() and show_pass:
                    result.print()
            schema_obj.clear_results()

    if not error_exists:
        print(colored("ALL SCHEMA VALIDATION CHECKS PASSED", "green"))
    else:
        sys.exit(1)
