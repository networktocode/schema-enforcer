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


YAML_HANDLER = YAML()
YAML_HANDLER.indent(sequence=4, offset=2)
YAML_HANDLER.explicit_start = True
VALIDATION_ERROR_ATTRS = ["message", "schema_path", "validator", "validator_value"]


def load_config():
    """
    Loads configuration files and merges values based on precedence.

    The lowest preferred cfg file is ``examples/schema.cfg``.
    The highest preferred cfg file is ``schema.cfg``.

    Retuns:
        dict: The values from the cfg files.
    """
    config = {}
    for file in ("examples/schema.cfg", "schema.cfg"):
        try:
            with open(file, encoding="utf-8") as fh:
                config.update(YAML_HANDLER.load(fh))
        except FileNotFoundError:
            pass

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


def get_conversion_filepaths(
    original_path, original_extension, conversion_path, conversion_extension
):
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
        raise FileNotFoundError(
            f"No {original_extension} files were found in {original_path}/**/"
        )
    original_paths_and_filenames = (get_path_and_filename(file) for file in glob_files)
    original_paths, filenames = zip(*original_paths_and_filenames)
    conversion_paths = [
        path.replace(original_path, conversion_path, 1) for path in original_paths
    ]
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
        jsonschema.Validator: A Validator instance with schema loaded with a RefResolver.

    Example:
        >>> schema_root_dir = "/home/users/admin/network-schema/schema/json"
        >>> schema_filepath = "schema/json/schemas/ntp.json"
        >>> validator = load_schema_from_json_file(schema_root_dir, schema_filepath)
        >>> validator.schema
        >>> {...}
        >>>
    """
    base_uri = f"file:{schema_root_dir}/".replace("\\", "/")
    with open(schema_filepath, encoding="utf-8") as fh:
        schema_definition = json.load(fh)

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


def convert_yaml_to_json(yaml_path, json_path):
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

        print(f"Converting {yaml_file} -> {json_file}")
        dump_data_to_json(yaml_data, json_file)


def convert_json_to_yaml(json_path, yaml_path):
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

        print(f"Converting {json_file} -> {yaml_file}")
        dump_data_to_yaml(json_data, yaml_file)


def resolve_json_refs(json_schema_path, output_path):
    """
    Loads JSONSchema schema files, resolves ``refs``, and writes to a file.

    Args:
        json_schema_path: The path to JSONSchema schema definitions.
        output_path: The path to write updated JSONSchema schema files.

    Returns:
        None: JSONSchema definitions are written to files.

    Example:
        >>> json_schema_path = "schema/json/schemas"
        >>> os.listdir(json_schema_path)
        ['ntp.json', 'snmp.json']
        >>> output_path = "schema/json/full_schemas"
        >>> os.isdir(output_path)
        False
        >>> resolve_json_refs(json_schema_path, output_path)
        >>> os.listdir(output_path)
        ['ntp.json', 'snmp.json']
        >>>
    """
    os.makedirs(output_path, exist_ok=True)
    # It is necessary to replace backslashes with forward slashes on Windows systems
    base_uri = f"file:{os.path.realpath(json_schema_path)}/".replace("\\", "/")
    for file in glob.iglob(f"{json_schema_path}/*.json"):
        path, filename = get_path_and_filename(file)
        with open(file, encoding="utf-8") as fh:
            schema = jsonref.load(fh, base_uri=base_uri, jsonschema=True)
        json_file = f"{output_path}/{filename}.json"
        print(f"Converting {file} -> {json_file}")
        dump_data_to_json(schema, json_file)


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


def generate_hostvars(inventory_path, schema_path, output_path):
    """
    Generates variable files per host per schema file.

    This creates a directory per host and then writes a var file per schema file.
    The var files will contain only the data that corresponds with the top-level
    properties in the schema files. For example, if the `ntp.json` schema file
    defines top-level properites for "ntp_servers" and "ntp_authentication", then
    the `ntp.yml` vars file will only have the variables for "ntp_servers" and
    "ntp_authentication". If the device does not have have top-level data defined,
    then a var file will not be written for that host.

    Args:
        inventory_path (str): The path to Ansible inventory.
        schema_path (str): The path to the schema definition directory.
        output_path (str): The path to write var files to.

    Returns:
        None: Var files are written per schema per host.

    Example:
        >>> with open(inventory_artifact) as fh:
        ...     ansible_hostvars = json.load(fh)
        ...
        >>> schema_path = "schema/json/schemas"
        >>> os.listdir(schema_path)
        ['bgp.json', 'ntp.json']
        >>> ouput_dir = "inventory/hostvars"
        >>> os.listdir(output_dir)
        []
        >>> generate_hostvars(ansible_inventory, schema_path, output_path)
        >>> os.listdir(output_dir)
        ['host1', 'host2', 'host3']
        >>> os.listdir(f"{output_dir}/host1")
        ['bgp.yml', 'ntp.yml']
        >>> os.listdr(f"{output_dir}/host2")
        ['ntp.yml']
    """
    schema_files = glob.glob(f"{schema_path}/*.json")
    schema_properties = get_schema_properties(schema_files)
    inventory = AnsibleInventory(inventory_path)
    hosts = inventory.get_hosts_containing()
    for host in hosts:
        print(f"Generating var files for {host}")
        output_dir = f"{output_path}/{host}"
        host_vars = inventory.get_host_vars(host)
        dump_schema_vars(output_dir, schema_properties, host_vars)
