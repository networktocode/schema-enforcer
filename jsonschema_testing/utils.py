import os
import json
import glob
from collections.abc import Mapping, Sequence

from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString as DQ
import jsonref
from jsonschema import (
    RefResolver,
    Draft7Validator,
    draft7_format_checker,
    ValidationError,
)

from .ansible_inventory import AnsibleInventory
import toml
from pathlib import Path
from termcolor import colored
import importlib
from collections import defaultdict


YAML_HANDLER = YAML()
YAML_HANDLER.indent(sequence=4, offset=2)
YAML_HANDLER.explicit_start = True
VALIDATION_ERROR_ATTRS = ["message", "schema_path", "validator", "validator_value"]
CONFIG_DEFAULTS = {
    "schema_exclude_filenames": [],
    "schema_search_directories": ["schema/schemas/"],
    "schema_file_extensions": [".json", ".yml"],
    "instance_exclude_filenames": [".yamllint.yml", ".travis.yml"],
    "instance_search_directories": ["hostvars/"],
    "instance_file_extensions": [".json", ".yml"],
    "yaml_schema_path": "schema/yaml/schemas/",
    "json_schema_path": "schema/json/schemas/",
    # Define location to place schema definitions after resolving ``$ref``
    "json_schema_definitions": "schema/json/definitions",
    "yaml_schema_definitions": "schema/yaml/definitions",
    "json_full_schema_definitions": "schema/json/full_schemas",
    # Define network device variables location
    "device_variables": "hostvars/",
    # Define path to inventory
    "inventory_path": "inventory/",
    "schema_mapping": {},
}


def warn(msg):
    print(colored("WARNING |", "yellow"), msg)


def error(msg):
    print(colored("  ERROR |", "red"), msg)


def load_config(tool_name="jsonschema_testing", defaults={}):
    """
    Loads configuration files and merges values based on precedence.

    Loads configuration from pyprojects.toml under the specified tool.{toolname} section.

    Retuns:
        dict: The values from the cfg files.
    """
    # TODO Make it so the script runs regardless of whether a config file is defined by using sensible defaults
    # TODO should we search parent folders for pyproject.toml ?

    config = defaultdict()
    config.update(CONFIG_DEFAULTS)
    config.update(defaults)

    try:
        config_string = Path("pyproject.toml").read_text()
        tomlcfg = toml.loads(config_string)
        config.update(tomlcfg["tool"][tool_name])
    except KeyError:
        warn(f"[tool.{tool_name}] section is not defined in pyproject.toml,")
        warn(f"Please see {tool_name}/example/ folder for sample of this section")
        warn(f"Using built-in defaults for [tool.{tool_name}]")

    except (FileNotFoundError, UnboundLocalError):
        warn(f"Could not find pyproject.toml in the current working directory.")
        warn(f"Script is being executed from CWD: {os.getcwd()}")
        warn(f"Using built-in defaults for [tool.{tool_name}]")

    if not len(config["schema_mapping"]):
        warn(
            f"[tool.{tool_name}.schema_mapping] is not defined, instances must be tagged to apply schemas to instances"
        )

    return config


def get_path_and_filename(filepath):
    """
    Splits ``filepath`` into the directory path and filename w/o extesion.

    Args:
        filepath (str): The path to a file.

    Returns:
        tuple: The directory where the file is located, and the filename w/o extension.

    Example:
        >>> path, filename = get_path_and_filename("schema/json/schemas/ntp.json")
        >>> print(path)
        'schema/json/schemas'
        >>> print(filename)
        'ntp'
        >>>
    """
    file, extension = os.path.splitext(filepath)
    return os.path.split(file)


def ensure_strings_have_quotes_sequence(sequence_object):
    """
    Ensures Sequence objects have quotes on string entries.

    Args:
        sequence_object (iter): A python iterable object to ensure strings have quotes.

    Returns:
        iter: The ``sequence_object`` is returned having its string values with quotes.
    """
    iter_type = type(sequence_object)
    sequence_with_strings = []
    for entry in sequence_object:
        if isinstance(entry, str):
            new_entry = DQ(entry)
        elif isinstance(entry, Sequence):
            new_entry = ensure_strings_have_quotes_sequence(entry)
        elif isinstance(entry, Mapping):
            new_entry = ensure_strings_have_quotes_mapping(entry)
        else:
            new_entry = entry

        sequence_with_strings.append(new_entry)
    return iter_type(sequence_with_strings)


def ensure_strings_have_quotes_mapping(mapping_object):
    """
    Recursively ensures Mapping objects have quotes on string values.

    Args:
        mapping_object (dict): A python dictionary to ensure strings have quotes.

    Returns:
        dict: The ``mapping_object`` with double quotes added to string values.
    """
    for key, value in mapping_object.items():
        if isinstance(value, str):
            mapping_object[key] = DQ(value)
        elif isinstance(value, Sequence):
            mapping_object[key] = ensure_strings_have_quotes_sequence(value)
        elif isinstance(value, Mapping):
            ensure_strings_have_quotes_mapping(value)
    return mapping_object


def get_conversion_filepaths(original_path, original_extension, conversion_path, conversion_extension):
    """
    Finds files matching a glob pattern and derives path to conversion file.

    Args:
        original_path (str): The path to look for files to convert.
        original_extension (str): The original file extension of files being converted.
        conversion_path (str): The root path to place files after conversion.
        conversion_extension (str): The file extension to use for files after conversion

    Returns:
        list: A tuple of paths to the original and the conversion files.

    Example:
        >>> os.listdir("schema/yaml/schemas/")
        ["ntp.yml", "snmp.yml"]
        >>> conversion_paths = get_conversion_filepaths(
        ...     "schema/yaml/", "yml", "schema/json", "json"
        ... )
        >>> for yaml_path, json_path in conversion_paths:
        ...     print(f"Original: {yaml_path} -> Conversion: {json_path}")
        ...
        Original: schema/yaml/schemas/ntp.yml -> Conversion: schema/json/schemas/ntp.json
        Original: schema/yaml/schemas/snmp.yml -> Conversion: schema/json/schemas/snmp.json
        >>>
    """
    original_path = os.path.normpath(original_path)
    conversion_path = os.path.normpath(conversion_path)
    glob_path = os.path.normpath(f"{original_path}/**/*.{original_extension}")
    glob_files = glob.glob(glob_path, recursive=True)
    if not glob_files:
        raise FileNotFoundError(f"No {original_extension} files were found in {original_path}/**/")
    original_paths_and_filenames = (get_path_and_filename(file) for file in glob_files)
    original_paths, filenames = zip(*original_paths_and_filenames)
    conversion_paths = [path.replace(original_path, conversion_path, 1) for path in original_paths]
    conversion_files = [f"{filename}.{conversion_extension}" for filename in filenames]
    for directory in set(conversion_paths):
        os.makedirs(directory, exist_ok=True)
    return [
        (glob_files[seq], os.path.normpath(f"{path}/{conversion_files[seq]}"))
        for seq, path in enumerate(conversion_paths)
    ]


def load_schema_from_json_file(schema_root_dir, schema_filepath):
    """
    Loads a jsonschema defintion file into a Validator instance.

    Args:
        schema_root_dir (str): The full path to root directory of schema files.
        schema_file_path (str): The path to a schema definition file.

    Returns:
        jsonschema.Validator: A Validator instance with schema loaded with a RefResolver and format_checker.

    Example:
        >>> schema_root_dir = "/home/users/admin/network-schema/schema/json"
        >>> schema_filepath = "schema/json/schemas/ntp.json"
        >>> validator = load_schema_from_json_file(schema_root_dir, schema_filepath)
        >>> validator.schema
        >>> {...}
        >>>
    """
    base_uri = f"file:{schema_root_dir}/".replace("\\", "/")
    with open(os.path.join(schema_root_dir, schema_filepath), encoding="utf-8") as fh:
        schema_definition = json.load(fh)

    # Notes: The Draft7Validator will use the base_uri to resolve any relative references within the loaded schema_defnition
    # these references must match the full filenames currently, unless we modify the RefResolver to handle other cases.
    validator = Draft7Validator(
        schema_definition,
        format_checker=draft7_format_checker,
        resolver=RefResolver(base_uri=base_uri, referrer=schema_definition),
    )
    return validator


def generate_validation_error_attributes(json_var_file, validator):
    """
    Generates a map between ValidationError Attributes and their values.

    Args:
        json_var_file (str): The path to a json variable file.
        validator (jsonschema.Validator): A validator to validate var data.

    Returns:
        dict: Keys are attribute names, and values are the attribute's value.

    Example:
        >>> validator = load_schema_from_json_file(schema_root_dir, schema_filepath)
        >>> invalid_data = "tests/mocks/invalid/ntp/invalid_ip.json"
        >>> error_attrs = generate_validation_error_attributes(invalid_data, validator)
        >>> for attr, value in error_attributes.items():
        ...     print(f"{attr:20} = {value}")
        ...
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
        >>>
    """
    with open(json_var_file, encoding="utf-8") as fh:
        var_data = json.load(fh)
    try:
        validator.validate(var_data)
        error_attrs = {}
    except ValidationError as error:
        error_attrs = {attr: getattr(error, attr) for attr in VALIDATION_ERROR_ATTRS}

    return error_attrs


def dump_data_to_yaml(data, yaml_path):
    """
    Dumps data to a YAML file with special formatting.

    Args:
        data (dict): The data to write to a YAML file.
        yaml_path (str): The path where to write the YAML file.

    Returns:
        None: Data is written to a file.

    Example:
        >>> os.listdir("hostvars/sw01/")
        ["dns.yml", "snmp.yml"]
        >>> data = {"ntp": {"servers": [{"address": "10.1.1.1", "vrf": "mgmt"}]}}
        >>> yaml_file = "hostvars/sw01/ntp.yml"
        >>> os.listdir("hostvars/sw01/")
        ["dns.yml", "ntp.yml", "snmp.yml"]
        >>>
    """
    data_formatted = ensure_strings_have_quotes_mapping(data)
    with open(yaml_path, "w", encoding="utf-8") as fh:
        YAML_HANDLER.dump(data_formatted, fh)


def dump_data_to_json(data, json_path):
    """
    Dumps data to a JSON file with special formatting.

    Args:
        data (dict): The data to write to a JSON file.
        json_path (str): The path where to write the JSON file.

    Returns:
        None: Data is written to a file.

    Example:
        >>> os.listdir("hostvars/sw01/")
        ["dns.json", "snmp.json"]
        >>> data = {"ntp": {"servers": [{"address": "10.1.1.1", "vrf": "mgmt"}]}}
        >>> json_file = "hostvars/sw01/json.yml"
        >>> os.listdir("hostvars/sw01/")
        ["dns.json", "ntp.json", "snmp.json"]
        >>>
    """
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=4)
        fh.write("\n")


def fix_references(data, old_file_ext, new_file_ext, _recursive=False, **kwargs):
    """
    Updates any relative $ref so that they point to the new_file_ext for local file resolution

    """
    try:
        if not isinstance(data["$ref"], str):
            raise TypeError
    except (TypeError, LookupError):
        pass
    else:
        if "://" not in data["$ref"]:
            data["$ref"] = data["$ref"].replace(old_file_ext, new_file_ext)
            # re.sub(f"%s{old_file_ext}", new_file_ext, data["$ref"])  # regex needs to handle #fragmenets
        return data

    # Recurse through the data and replace any relative $ref file extensions
    if isinstance(data, Mapping):
        data = type(data)((k, fix_references(v, old_file_ext, new_file_ext, _recursive=True)) for k, v in data.items())
    elif isinstance(data, Sequence) and not isinstance(data, str):
        data = type(data)(fix_references(v, old_file_ext, new_file_ext) for i, v in enumerate(data))

    return data


def convert_yaml_to_json(yaml_path, json_path, silent=False):
    """
    Reads YAML files and writes them to JSON files.

    Args:
        yaml_path (str): The root directory containing YAML files to convert to JSON.
        json_path (str): The root directory to build JSON files from YAML files in
                         ``yaml_path``.

    Returns:
        None: JSON files are written with data from YAML files.

    Example:
        >>> os.listdir("schema/")
        ['yaml']
        >>> convert_yaml_to_json("schema/yaml", "schema/json")
        >>> os.listdir("schema/")
        ['json', 'yaml']
        >>> os.listdir("schema/json/schema")
        ['ntp.json', 'snmp.json']
        >>>
    """
    yaml_json_pairs = get_conversion_filepaths(yaml_path, "yml", json_path, "json")
    for yaml_file, json_file in yaml_json_pairs:
        with open(yaml_file, encoding="utf-8") as fh:
            yaml_data = YAML_HANDLER.load(fh)

        yaml_data = fix_references(data=yaml_data, old_file_ext=".yml", new_file_ext=".json")
        if not silent:
            print(f"Converting {yaml_file} -> {json_file}")
        dump_data_to_json(yaml_data, json_file)


def convert_json_to_yaml(json_path, yaml_path, silent=False):
    """
    Reads JSON files and writes them to YAML files.

    Args:
        json_path (str): The root directory containing JSON files to convert to YAML.
        yaml_path (str): The root directory to build YAML files from JSON files in
                         ``json_path``.

    Returns:
        None: YAML files are written with data from JSON files.

    Example:
        >>> os.listdir("schema/")
        ['json']
        >>> convert_json_to_yaml("schema/json", "schema/yaml")
        >>> os.listdir("schema/")
        ['json', 'yaml']
        >>> os.listdir("schema/yaml/schema")
        ['ntp.yml', 'snmp.yml']
        >>>
    """
    json_yaml_pairs = get_conversion_filepaths(json_path, "json", yaml_path, "yml")
    for json_file, yaml_file in json_yaml_pairs:
        with open(json_file, encoding="utf-8") as fh:
            json_data = json.load(fh)

        json_data = fix_references(data=json_data, old_file_ext=".json", new_file_ext=".yml")
        if not silent:
            print(f"Converting {json_file} -> {yaml_file}")
        dump_data_to_yaml(json_data, yaml_file)


def get_schema_properties(schema_files):
    """
    Maps schema filenames to top-level properties.

    Args:
        schema_files (iterable): The list of schema definition files.

    Returns:
        dict: Schema filenames are the keys, and the values are list of property names.

    Example:
        >>> schema_files = [
        ...     'schema/json/schemas/ntp.json', 'schema/json/schemas/snmp.json'
        ... ]
        >>> schema_property_map = get_schema_properties(schema_files)
        >>> print(schema_property_map)
        {
            'ntp': ['ntp_servers', 'ntp_authentication'],
            'snmp': ['snmp_servers']
        }
        >>>
    """
    schema_property_map = {}
    for schema_file in schema_files:
        with open(schema_file, encoding="utf-8") as fh:
            schema = json.load(fh)

        path, filename = get_path_and_filename(schema_file)
        schema_property_map[filename] = list(schema["properties"].keys())

    return schema_property_map


def dump_schema_vars(output_dir, schema_properties, variables):
    """
    Writes variable data to file per schema in schema_properties.

    Args:
        output_dir (str): The directory to write variable files to.
        schema_properties (dict): The mapping of schema files to top-level properties.
        variables (dict): The variables per inventory source.

    Returns:
        None: Files are written for each schema definition.

    Example:
        >>> output_dir = "inventory/hostvars/host1"
        >>> schema_files = glob.glob("schema/json/schemas/*.json")
        >>> schema_properties = get_schema_properties(schema_files)
        >>> host_variables = magic_hostvar_generator()
        >>> os.isdir(output_dir)
        False
        >>> dump_schema_vars(output_dir, schema_properties, host_variables)
        >>> os.listdir(output_dir)
        ['ntp.yml', 'snmp.yml']
        >>>
    """
    os.makedirs(output_dir, exist_ok=True)
    # Somewhat of a hack to remove non basic object types from data structure
    variables = json.loads(json.dumps(variables))
    for schema, properties in schema_properties.items():
        schema_data = {}
        for prop in properties:
            try:
                schema_data[prop] = variables[prop]
            except KeyError:
                pass
        if schema_data:
            print(f"-> {schema}")
            yaml_file = f"{output_dir}/{schema}.yml"
            dump_data_to_yaml(schema_data, yaml_file)


def find_files(file_extensions, search_directories, excluded_filenames, excluded_directories=[], return_dir=False):
    """
    Walk provided search directories and return the full filename for all files matching file_extensions except the excluded_filenames.

    Args:
        file_extensions (list, str): The extensions to look for when finding schema files.
        search_directories (list, str): The list of directories or python package names to search for schema files.
        excluded_filenames (list, str): Specify any files that should be excluded from importing as schemas (exact matches).
        return_dir (bool): Default False, When Tru, Return each file as a tuple with the dir and the file name
    Returns:
        list: Each element of the list will be a Tuple if return_dir is True otherwise it will be a string
    """

    def is_part_of_excluded_dirs(current_dir):
        """Check if the current_dir is part of one of excluded_directories.
        
        To simplify the matching all dirs are converted to absolute path

        Args:
            current_dir (str): Relative or Absolute path to a directory

        Returns:
            bool: 
                True if the current_directory is part of the list of excluded directories
                False otherwise
        """

        for directory in excluded_directories:
            abs_current = os.path.abspath(current_dir)
            abs_excluded = os.path.abspath(directory)
            if abs_current.startswith(abs_excluded):
                return True

        return False

    if not isinstance(search_directories, list):
        search_directories = list(search_directories)

    filenames = []
    for search_directory in search_directories:
        # if the search_directory is a simple name without a / we try to find it as a python package looking in the {pkg}/schemas/ dir
        if "/" not in search_directory:
            try:
                dir = os.path.join(
                    os.path.dirname(importlib.machinery.PathFinder().find_module(search_directory).get_filename()),
                    "schemas",
                )
            except AttributeError:
                error(f"Failed to find python package `{search_directory}' for loading {search_directory}/schemas/")
                continue

            search_directory = dir

        for root, dirs, files in os.walk(search_directory):  # pylint: disable=W0612

            if is_part_of_excluded_dirs(root):
                continue

            for file in files:
                # Extract the extension of the file and check if the extension matches the list
                _, ext = os.path.splitext(file)
                if ext in file_extensions:
                    if file not in excluded_filenames:
                        if return_dir:
                            filenames.append((root, file))
                        else:
                            filenames.append(os.path.join(root, file))

    return filenames


def load_file(filename, file_type=None):
    """
    Loads the specified file, using json or yaml loaders based on file_type or extension.

    Files with json extension are loaded with json, otherwise yaml is assumed.

    Returns parsed object of respective loader.
    """
    if not file_type:
        file_type = "json" if filename.endswith(".json") else "yaml"

    # When called from JsonRef, filename will contain a URI not just a local file,
    # but this function only handles local files. See jsonref.JsonLoader for a fuller implementation
    if filename.startswith("file:///"):
        filename = filename.replace("file://", "")

    handler = YAML_HANDLER if file_type == "yaml" else json
    with open(filename, "r") as f:
        file_data = handler.load(f)

    return file_data


def load_data(file_extensions, search_directories, excluded_filenames, file_type=None, data_key=None):
    """
    Walk a directory and load all files matching file_extension except the excluded_filenames

    If file_type is not specified, yaml is assumed unless file_extension matches json

    Dictionary returned is based on the filename, unless a data_key is specifiied
    """
    data = {}

    # Find all of the matching files and attempt to load the data
    for filename in find_files(
        file_extension=file_extensions, search_directories=search_directories, excluded_filenames=excluded_filenames
    ):
        file_data = load_file(filename, file_type)
        key = file_data.get(data_key, filename)
        data.update({key: file_data})

    return data
