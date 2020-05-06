# Standard Imports
import json
import os
import sys
from pathlib import Path

# Third Party Imports
import click
import toml
from termcolor import colored
from jsonschema import Draft7Validator, validators
from ruamel.yaml import YAML

YAML_HANDLER = YAML()

CONFIG_SCHEMA = dict(
    type="object",
    properties=dict(
        instance_file_extension=dict(type="string", default=".yml"),
        instance_search_directory=dict(type="string", default="./"),
        instance_exclude_filenames=dict(type="array", items=dict(type="string"), default=[]),
        schema_file_extension=dict(type="string", default=".json"),
        schema_search_directory=dict(type="string", default="./"),
        schema_exclude_filenames=dict(type="array", items=dict(type="string"), default=[]),
        schema_file_type=dict(type="string", default="json", enum=["yaml", "json"]),  # add enum here
        schema_mapping=dict(type="object", default={}),
    ),
)


def extend_with_default(validator_class):
    """
    Args:
      validator_class:

    Returns:
    """
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        """
        Args:
          validator:
          properties:
          instance:
          schema:

        Returns:

        """
        for property_name, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(property_name, subschema["default"])

        for error in validate_properties(validator, properties, instance, schema):
            yield error

    return validators.extend(validator_class, {"properties": set_defaults})


def get_instance_data(file_extension, search_directory, excluded_filenames):
    """
    Get dictionary of file and file data for schema and instance
    """
    # Define list of files to be loaded to have the schema tested against
    data = {}
    # Find all of the YAML files in the parent directory of the project
    for root, dirs, files in os.walk(search_directory):  # pylint: disable=W0612
        for lcl_file in files:
            if lcl_file.endswith(file_extension):
                if lcl_file not in excluded_filenames:
                    filename = os.path.join(root, lcl_file)
                    with open(filename, "r") as f:
                        file_data = YAML_HANDLER.load(f)

                    data.update({filename: file_data})

    return data


def get_schemas(file_extension, search_directory, excluded_filenames, file_type):
    """
    Get dictionary of file and file data for schema and instance
    """
    # Define list of files to be loaded to have the schema tested against
    data = {}
    # Find all of the YAML files in the parent directory of the project
    for root, dirs, files in os.walk(search_directory):  # pylint: disable=W0612
        for lcl_file in files:
            if lcl_file.endswith(file_extension):
                if lcl_file not in excluded_filenames:
                    filename = os.path.join(root, lcl_file)
                    with open(filename, "r") as f:
                        if file_type == "yaml":
                            file_data = YAML_HANDLER.load(f)
                        if file_type == "json":
                            file_data = json.load(f)

                    schema_id = file_data["$id"]
                    data.update({schema_id: file_data})

    return data


def get_instance_schema_mapping(file_extension, search_directory, excluded_filenames, schema_mapping):
    """
    Get dictionary of file and file data for schema and instance
    """
    # Define dict of files to be loaded to have the schema tested against
    instance_schema_mapping = {}
    # Find all of the YAML files in the parent directory of the project
    for root, dirs, files in os.walk(search_directory):  # pylint: disable=W0612
        for lcl_file in files:
            if lcl_file.endswith(file_extension):
                if lcl_file not in excluded_filenames:
                    filename = os.path.join(root, lcl_file)
                    for instance_filename, schema_filenames in schema_mapping.items():

                        if lcl_file == instance_filename:
                            schemas = []
                            for schema_filename in schema_filenames:
                                with open(schema_filename, "r") as f:
                                    schema = YAML_HANDLER.load(f)
                                    schemas.append(schema["$id"])

                            instance_schema_mapping.update({filename: schemas})

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
    schemas_loaded_from_files = []
    for schema_name in schemas.keys():
        if schema_name not in schemas_loaded_from_files:
            schemas_loaded_from_files.append(schema_name)

    for file_name, schema_names in instance_file_to_schemas_mapping.items():
        for schema_name in schema_names:
            if schema_name not in schemas_loaded_from_files:
                print(
                    colored(f"WARN", "yellow")
                    + f" | schema '{schema_name}' Will not be checked. It is declared in {file_name} but is not loaded."
                )
                errors = True


def check_schema(schemas, instances, instance_file_to_schemas_mapping, show_success=False):

    error_exists = False

    for schema_file, schema in schemas.items():
        config_validator = Draft7Validator(schema)

        for instance_file, instance_data in instances.items():

            # Get schemas which should be checked for this instance file. If the instance should not
            # be checked for adherence to this schema, don't skip checking it.
            if not schema["$id"] in instance_file_to_schemas_mapping.get(instance_file):
                continue

            error_exists_inner_loop = False

            for error in config_validator.iter_errors(instance_data):
                if len(error.absolute_path) > 0:
                    print(
                        colored(f"FAIL", "red") + f" | [ERROR] {error.message}"
                        f" [FILE] {instance_file}"
                        f" [PROPERTY] {':'.join(str(item) for item in error.absolute_path)}"
                        f" [SCHEMA] {schema_file.split('/')[-1]}"
                    )
                if len(error.absolute_path) == 0:
                    print(
                        colored(f"FAIL", "red") + f" | [ERROR] {error.message}"
                        f" [FILE] {instance_file}"
                        f" [SCHEMA] {schema_file.split('/')[-1]}"
                    )

                error_exists = True
                error_exists_inner_loop = True

            if not error_exists_inner_loop and show_success:
                print(colored(f"PASS", "green") + f" | [SCHEMA] {schema_file.split('/')[-1]} | [FILE] {instance_file}")

    if error_exists:
        sys.exit(1)

    print(colored("ALL SCHEMA VALIDATION CHECKS PASSED", "green"))


@click.command()
@click.option(
    "--show-success", default=False, help="Shows validation checks that passed", is_flag=True, show_default=True
)
@click.option(
    "--show-checks",
    default=False,
    help="Shows the schemas to be checked for each instance file",
    is_flag=True,
    show_default=True,
)
def main(show_success, show_checks):
    # Load Config
    config_file = "pyproject.toml"
    config = {}

    if os.path.exists(config_file):
        try:
            config_string = Path(config_file).read_text()
            config = toml.loads(config_string)
        except:
            print(
                colored(
                    f"ERROR | Unable to read the configuration file {config_file}, please make sure it's a valid TOML file",
                    "red",
                )
            )
            sys.exit(1)

    config_validator = extend_with_default(Draft7Validator)
    v = config_validator(CONFIG_SCHEMA)
    config_errors = sorted(v.iter_errors(config), key=str)

    if len(config_errors) != 0:
        print(colored(f"ERROR | Found {len(config_errors)} error(s) in the configuration file ({config_file})", "red"))
        for error in config_errors:
            print(colored(f"  {error.message} in {'/'.join(error.absolute_path)}", "red"))
        sys.exit(1)

    # Get Dict of Instance File Path and Data
    instances = get_instance_data(
        file_extension=config["instance_file_extension"],
        search_directory=config["instance_search_directory"],
        excluded_filenames=config["instance_exclude_filenames"],
    )

    # Get Dict of Schema File Path and Data
    schemas = get_schemas(
        file_extension=config["schema_file_extension"],
        search_directory=config["schema_search_directory"],
        excluded_filenames=config["schema_exclude_filenames"],
        file_type=config["schema_file_type"],
    )

    # Get Mapping of Instance to Schema
    instance_file_to_schemas_mapping = get_instance_schema_mapping(
        file_extension=config["instance_file_extension"],
        search_directory=config["instance_search_directory"],
        excluded_filenames=config["instance_exclude_filenames"],
        schema_mapping=config["schema_mapping"],
    )

    if show_checks:
        print("Instance File                                     Schema")
        print("-" * 80)
        for instance_file, schema in instance_file_to_schemas_mapping.items():
            print(f"{instance_file:50} {schema}")
        sys.exit(0)

    check_schemas_exist(schemas, instance_file_to_schemas_mapping)

    check_schema(
        schemas=schemas,
        instances=instances,
        instance_file_to_schemas_mapping=instance_file_to_schemas_mapping,
        show_success=show_success,
    )


if __name__ == "__main__":
    main()
