"""InstanceFile and InstanceFileManager."""
import os
import re
import itertools
from pathlib import Path
from schema_enforcer.utils import find_files, load_file

SCHEMA_TAG = "jsonschema"


class InstanceFileManager:  # pylint: disable=too-few-public-methods
    """InstanceFileManager."""

    def __init__(self, config):
        """Initialize the interface File manager.

        The file manager will locate all potential instance files in the search directories.

        Args:
            config (string): The pydantec config object.
        """
        self.instances = []
        self.config = config

        # Find all instance files
        # TODO need to load file extensions from the config
        files = find_files(
            file_extensions=config.data_file_extensions,
            search_directories=config.data_file_search_directories,
            excluded_filenames=config.data_file_exclude_filenames,
            excluded_directories=[config.main_directory],
            return_dir=True,
        )

        # For each instance file, check if there is a static mapping defined in the config
        # Create the InstanceFile object and save it
        for root, filename in files:
            matches = []
            if filename in config.schema_mapping:
                matches.extend(config.schema_mapping[filename])

            instance = InstanceFile(root=root, filename=filename, matches=matches)
            self.instances.append(instance)

    def print_schema_mapping(self):
        """Print in CLI the matches for all instance files."""
        print("{:50} Schema ID".format("Structured Data File"))
        print("-" * 80)
        print_strings = []
        for instance in self.instances:
            filepath = f"{instance.path}/{instance.filename}"
            print_strings.append(f"{filepath:50} {instance.matches}")
        print("\n".join(sorted(print_strings)))


class InstanceFile:
    """Class to manage an instance file."""

    def __init__(self, root, filename, matches=None):
        """Initializes InstanceFile object.

        Args:
            root (string): Absolute path to the directory where the schema file is located.
            filename (string): Name of the file.
            matches (list, optional): List of schema IDs that matches with this Instance file. Defaults to None.
        """
        self.data = None
        self.path = root
        self.full_path = os.path.realpath(root)
        self.filename = filename

        if matches:
            self.matches = matches
        else:
            self.matches = []

        self.matches.extend(self._find_matches_inline())

    def _find_matches_inline(self, content=None):
        """Find addition matches using the Schema ID decorator comment.

        Look for a line with # jsonschema: schema_id,schema_id

        Args:
            content (string, optional): Content of the file to analyze. Default to None.

        Returns:
            list(string): List of matches found in the file.
        """
        if not content:
            content = Path(os.path.join(self.full_path, self.filename)).read_text()

        matches = []

        if SCHEMA_TAG in content:
            line_regexp = r"^#.*{0}:\s*(.*)$".format(SCHEMA_TAG)
            match = re.match(line_regexp, content, re.MULTILINE)
            if match:
                matches = [x.strip() for x in match.group(1).split(",")]

        return matches

    def get_content(self):
        """Return the content of the instance file in structured format.

        Content returned can be either dict or list depending on the content of the file

        Returns:
            dict or list: Content of the instance file.
        """
        return load_file(os.path.join(self.full_path, self.filename))

    def validate(self, schema_manager, strict=False):
        """Validate this instance file with all matching schema in the schema manager.

        Args:
            schema_manager (SchemaManager): A SchemaManager object.
            strict (bool, optional): True is the validation should automatically flag unsupported element. Defaults to False.

        Returns:
            iterator: Iterator of ValidationErrors returned by schema.validate.
        """
        # TODO need to add something to check if a schema is missing
        # Create new iterator chain to be able to aggregate multiple iterators
        errs = itertools.chain()

        # Go over all schemas and skip any schema not present in the matches
        for schema_id, schema in schema_manager.iter_schemas():
            if schema_id not in self.matches:
                continue
            errs = itertools.chain(errs, schema.validate(self.get_content(), strict))

        return errs
