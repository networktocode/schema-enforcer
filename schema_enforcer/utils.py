"""Library of utility functions."""
import os
import json
import glob
from collections.abc import Mapping, Sequence
import importlib

from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString as DQ
from jsonschema import (  # pylint: disable=no-name-in-module
    RefResolver,
    Draft7Validator,
)

from termcolor import colored


from click import Option, UsageError

YAML_HANDLER = YAML()
YAML_HANDLER.indent(sequence=4, offset=2)
YAML_HANDLER.explicit_start = True


def warn(msg):
    """Print warning message in yellow."""
    print(colored("WARNING |", "yellow"), msg)


def error(msg):
    """Print a error message in red."""
    print(colored("  ERROR |", "red"), msg)


def get_path_and_filename(filepath):
    """Splits ``filepath`` into the directory path and filename w/o extesion.

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
    file, _ = os.path.splitext(filepath)
    return os.path.split(file)


def ensure_strings_have_quotes_sequence(sequence_object):
    """Ensures Sequence objects have quotes on string entries.

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
    """Recursively ensures Mapping objects have quotes on string values.

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
    """Finds files matching a glob pattern and derives path to conversion file.

    Args:
        original_path (str): The path to look for files to convert.
        original_extension (str): The original file extension of files being converted.
        conversion_path (str): The root path to place files after conversion.
        conversion_extension (str): The file extension to use for files after conversion.

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
    """Loads a jsonschema defintion file into a Validator instance.

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
    with open(os.path.join(schema_root_dir, schema_filepath), encoding="utf-8") as fileh:
        schema_definition = json.load(fileh)

    # Notes: The Draft7Validator will use the base_uri to resolve any relative references within the loaded schema_defnition
    # these references must match the full filenames currently, unless we modify the RefResolver to handle other cases.
    validator = Draft7Validator(
        schema_definition,
        format_checker=Draft7Validator.FORMAT_CHECKER,
        resolver=RefResolver(base_uri=base_uri, referrer=schema_definition),
    )
    return validator


def dump_data_to_yaml(data, yaml_path):
    """Dumps data to a YAML file with special formatting.

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
    with open(yaml_path, "w", encoding="utf-8") as fileh:
        YAML_HANDLER.dump(data_formatted, fileh)


def dump_data_to_json(data, json_path):
    """Dumps data to a JSON file with special formatting.

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
    with open(json_path, "w", encoding="utf-8") as fileh:
        json.dump(data, fileh, indent=4)
        fileh.write("\n")


def get_schema_properties(schema_files):
    """Maps schema filenames to top-level properties.

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
        with open(schema_file, encoding="utf-8") as fileh:
            schema = json.load(fileh)

        _, filename = get_path_and_filename(schema_file)
        schema_property_map[filename] = list(schema["properties"].keys())

    return schema_property_map


def dump_schema_vars(output_dir, schema_properties, variables):
    """Writes variable data to file per schema in schema_properties.

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


def find_files(
    file_extensions, search_directories, excluded_filenames, excluded_directories=[], return_dir=False
):  # pylint: disable=dangerous-default-value
    """Walk provided search directories and return the full filename for all files matching file_extensions except the excluded_filenames.

    Args:
        file_extensions (list, str): The extensions to look for when finding schema files.
        search_directories (list, str): The list of directories or python package names to search for schema files.
        excluded_filenames (list, str): Specify any files that should be excluded from importing as schemas (exact matches).
        excluded_directories (list): Specify a list of directories that should be excluded from search.
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
    for search_directory in search_directories:  # pylint: disable=too-many-nested-blocks
        # if the search_directory is a simple name without a / we try to find it as a python package looking in the {pkg}/schemas/ dir
        if "/" not in search_directory:
            try:
                directory = os.path.join(
                    os.path.dirname(importlib.machinery.PathFinder().find_module(search_directory).get_filename()),
                    "schemas",
                )
            except AttributeError:
                error(f"Failed to find python package `{search_directory}' for loading {search_directory}/schemas/")
                continue

            search_directory = directory

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
    """Loads the specified file, using json or yaml loaders based on file_type or extension.

    Files with json extension are loaded with json, otherwise yaml is assumed.

    Returns:
        dict or list: content of the file in a python variable.
    """
    if not file_type:
        file_type = "json" if filename.endswith(".json") else "yaml"

    # When called from JsonRef, filename will contain a URI not just a local file,
    # but this function only handles local files. See jsonref.JsonLoader for a fuller implementation
    if filename.startswith("file:///"):
        filename = filename.replace("file://", "")

    handler = YAML_HANDLER if file_type == "yaml" else json
    with open(filename, "r", encoding="utf-8") as fileh:
        file_data = handler.load(fileh)

    return file_data


def load_data(file_extensions, search_directories, excluded_filenames, file_type=None, data_key=None):
    """Walk a directory and load all files matching file_extension except the excluded_filenames.

    If file_type is not specified, yaml is assumed unless file_extension matches json.
    Dictionary returned is based on the filename, unless a data_key is specified.
    """
    data = {}

    # Find all of the matching files and attempt to load the data
    for filename in find_files(
        file_extensions=file_extensions, search_directories=search_directories, excluded_filenames=excluded_filenames
    ):
        file_data = load_file(filename, file_type)
        key = file_data.get(data_key, filename)
        data.update({key: file_data})

    return data


def find_file(filename, extensions=("yml", "yaml", "json")):
    """Search for a file with multiple extensions and return the filename if found.

    If multiple files with the same name but different extensions exist, only the first match is returned.

    Args:
        filename (str): Full filename of the file to search for, without the extension.
        formats(Tuple[str]): Tuple of formats (file extensions) appended to the file to search for it's existence.

    Returns:
        str or None: string of the filename found
    """
    for ext in extensions:
        file_ext = f"{filename}.{ext}"
        if not os.path.isfile(file_ext):
            continue

        return file_ext


def find_and_load_file(filename, formats=("yml", "yaml", "json")):
    """Search a file based on multiple extensions and load its content if found.

    Args:
        filename (str): Full filename of the file to search and load, without the extension.
        formats (List[str]): List of formats to search.

    Returns:
        dict, list or None: content of the file in a python variable. None if no file could be found.
    """
    for ext in formats:
        file_ext = f"{filename}.{ext}"
        if not os.path.isfile(file_ext):
            continue

        data = load_file(file_ext)
        return data

    return None


class MutuallyExclusiveOption(Option):
    """Add support for Mutually Exclusive option in Click.

    Examples:
        @command(help="Run the command.")
        @option('--jar-file', cls=MutuallyExclusiveOption,
                help="The jar file the topology lives in.",
                mutually_exclusive=["other_arg"])
        @option('--other-arg',
                cls=MutuallyExclusiveOption,
                help="The jar file the topology lives in.",
                mutually_exclusive=["jar_file"])
        def cli(jar_file, other_arg):
            print "Running cli."
            print "jar-file: {}".format(jar_file)
            print "other-arg: {}".format(other_arg)
    """

    def __init__(self, *args, **kwargs):
        """Initializes MutuallyExclusiveOption class."""
        self.mutually_exclusive = set(kwargs.pop("mutually_exclusive", []))
        help = kwargs.get("help", "")  # pylint: disable=redefined-builtin
        if self.mutually_exclusive:
            ex_str = ", ".join(self.mutually_exclusive)
            kwargs["help"] = help + (" NOTE: This argument is mutually exclusive with " " arguments: [" + ex_str + "].")
        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        """Validate that two mutually exclusive arguments are not provided together.

        Args:
            ctx : context.
            opts : options.
            args : arguments.

        Raises:
            UsageError: If two mutually exclusive arguments are provided.

        Returns:
            ctx, opts, args.
        """
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise UsageError(
                f"Illegal usage: `{self.name}` is mutually exclusive with "
                f"arguments `{', '.join(self.mutually_exclusive)}`."
            )

        return super().handle_parse_result(ctx, opts, args)
