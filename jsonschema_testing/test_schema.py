# Standard Imports
import json
import os
import sys
from pathlib import Path

# Third Party Imports
import click
import yaml
from termcolor import colored
from jsonschema import Draft7Validator
import toml

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
                        file_data = yaml.safe_load(f)

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
                            file_data = yaml.safe_load(f)
                        if file_type == "json":
                            file_data = json.load(f)

                    schema_id = file_data["$id"]
                    data.update({schema_id: file_data})

    return data

def get_instance_schema_mapping(file_extension, search_directory, excluded_filenames):
    """
    Get dictionary of file and file data for schema and instance
    """
    # Define list of files to be loaded to have the schema tested against
    instance_schema_mapping = {}
    # Find all of the YAML files in the parent directory of the project
    for root, dirs, files in os.walk(search_directory):  # pylint: disable=W0612
        for lcl_file in files:
            if lcl_file.endswith(file_extension):
                if lcl_file not in excluded_filenames:
                    filename = os.path.join(root, lcl_file)
                    with open(filename, "r") as f:
                        file_data = f.read()
                    if "# jsonschema_testing:" in file_data or "#jsonschema_testing:" in file_data:
                        for line in file_data.strip().split("\n"):
                            if "# jsonschema_testing:" in line or "#jsonschema_testing:" in line:
                                schemas = line.split(":")[-1].strip()
                                unstripped_schemas = schemas.split(",")
                                schemas = []
                                [schemas.append(schema.strip()) for schema in unstripped_schemas]
                                instance_schema_mapping.update({filename: schemas})
                    else:
                        instance_schema_mapping.update({filename: []})


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
                print(colored(f"WARN", "yellow") + f" | schema '{schema_name}' Will not be checked. It is declared in {file_name} but is not loaded.")
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
    show_default=True
)
def main(show_success, show_checks):
    # Load Config
    config_string = Path("pyproject.toml").read_text()
    config = toml.loads(config_string)

    # Get Dict of Instance File Path and Data
    instances = get_instance_data(
        file_extension=config["tool"]["jsonschema_testing"]. get("instance_file_extension", ".yml"),
        search_directory=config["tool"]["jsonschema_testing"].get("instance_search_directory", "./"),
        excluded_filenames=config["tool"]["jsonschema_testing"].get("instance_exclude_filenames", [])
        )

    # Get Dict of Schema File Path and Data
    schemas = get_schemas(
        file_extension=config["tool"]["jsonschema_testing"].get("schema_file_extension", ".json"),
        search_directory=config["tool"]["jsonschema_testing"].get("schema_search_directory", "./"),
        excluded_filenames=config["tool"]["jsonschema_testing"].get("schema_exclude_filenames", []),
        file_type=config["tool"]["jsonschema_testing"].get("schema_file_type", "json")
        )

    # Get Mapping of Instance to Schema
    instance_file_to_schemas_mapping = get_instance_schema_mapping(
        file_extension=config["tool"]["jsonschema_testing"]. get("instance_file_extension", ".yml"),
        search_directory=config["tool"]["jsonschema_testing"].get("instance_search_directory", "./"),
        excluded_filenames=config["tool"]["jsonschema_testing"].get("instance_exclude_filenames", []),
        )

    if show_checks:
        print("Instance File                                     Schema")
        print("-" * 80)
        for instance_file, schemas in instance_file_to_schemas_mapping.items():
            print(f"{instance_file:50} {schemas}")
        sys.exit(0)

    check_schemas_exist(schemas, instance_file_to_schemas_mapping)

    check_schema(
        schemas=schemas,
        instances=instances,
        instance_file_to_schemas_mapping=instance_file_to_schemas_mapping,
        show_success=show_success
    )

if __name__ == "__main__":
    main()