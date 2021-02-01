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
            config (pydantic.BaseSettings): The pydantec settings object.
        """
        self.instances = []
        self.config = config

        # Find all instance files
        # TODO need to load file extensions from the config
        instance_files = find_files(
            file_extensions=config.data_file_extensions,
            search_directories=config.data_file_search_directories,
            excluded_filenames=config.data_file_exclude_filenames,
            excluded_directories=[config.main_directory],
            return_dir=True,
        )

        # For each instance file, check if there is a static mapping defined in the config
        # Create the InstanceFile object and save it
        for root, filename in instance_files:
            matches = []
            if filename in config.schema_mapping:
                matches.extend(config.schema_mapping[filename])

            instance = InstanceFile(root=root, filename=filename, matches=matches)
            self.instances.append(instance)

    def add_matches_by_property_automap(self, schema_manager):
        """Adds schema_ids to matches by automapping top level schema properties to top level keys in instance data.

        Args:
            schema_manager (schema_enforcer.schemas.manager.SchemaManager): Schema manager oject
        """
        for instance in self.instances:
            instance.add_matches_by_property_automap(schema_manager)

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

        # Internal vars for caching data
        self._top_level_properties = None

        if matches:
            self.matches = matches
        else:
            self.matches = []

        self.matches.extend(self._find_matches_inline())

    def add_matches_by_property_automap(self, schema_manager):
        """Adds schema_ids to matches by automapping top level schema properties to top level keys in instance data.

        Args:
            schema_manager (schema_enforcer.schemas.manager.SchemaManager): Schema manager oject
        """
        matches = []

        for schema_id, schema_obj in schema_manager.iter_schemas():
            for top_level_property in schema_obj.top_level_properties:
                if top_level_property in self.top_level_properties and schema_id not in matches:
                    matches.append(schema_id)

        # Remove matches which have already been added
        matches = self._remove_pre_existing_matches(matches)
        self.matches.extend(matches)

    def _find_matches_inline(self, content=None):
        """Find addition matches using the Schema ID decorator comment.

        Look for a line with # jsonschema: schema_id,schema_id

        Args:
            content (string, optional): Content of the file to analyze. Default to None.

        Returns:
            list(string): List of matches (strings of schema_ids) found in the file.
        """
        # TODO Refactor this into a function for consistency
        if not content:
            content = Path(os.path.join(self.full_path, self.filename)).read_text()

        matches = []

        if SCHEMA_TAG in content:
            line_regexp = r"^#.*{0}:\s*(.*)$".format(SCHEMA_TAG)
            match = re.match(line_regexp, content, re.MULTILINE)
            if match:
                matches = [x.strip() for x in match.group(1).split(",")]

        matches = self._remove_pre_existing_matches(matches)
        return matches

    def get_content(self):
        """Return the content of the instance file in structured format.

        Content returned can be either dict or list depending on the content of the file

        Returns:
            dict or list: Content of the instance file.
        """
        return load_file(os.path.join(self.full_path, self.filename))

    def _remove_pre_existing_matches(self, matches):
        """Remove matches which already exist at `self.matches` from a list of matches.

        Args:
            matches (list[str]): List of schema IDs

        Returns:
            matches (list[str]): List of schema IDs
        """
        return list(set(matches) - set(self.matches))

    @property
    def top_level_properties(self):
        """Return a list of top level properties in the structured data defined by the data pulled from get_content.

        Returns:
            top_level_properties (list): List of the strings of top level properties defined by the data file
        """
        if self._top_level_properties:
            return self._top_level_properties

        content = self.get_content()
        top_level_properties = list(content.keys())
        return top_level_properties

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
