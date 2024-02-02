"""InstanceFile and InstanceFileManager."""
import os
import re
import itertools
from pathlib import Path
from ruamel.yaml.comments import CommentedMap
from schema_enforcer.utils import find_files, load_file

SCHEMA_TAG = "jsonschema"


class InstanceFileManager:  # pylint: disable=too-few-public-methods
    """InstanceFileManager."""

    def __init__(self, config):
        """Initialize the interface File manager.

        The file manager will locate all potential instance files in the search directories.

        Args:
            config (pydantic.BaseSettings): The Pydantec settings object.
        """
        self.instances = []
        self.config = config

        # Find all instance files
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
            matches = set()
            if filename in config.schema_mapping:
                matches.update(config.schema_mapping[filename])

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
        print("{:50} Schema ID".format("Structured Data File"))  # pylint: disable=consider-using-f-string
        print("-" * 80)
        print_strings = []
        for instance in self.instances:
            filepath = f"{instance.path}/{instance.filename}"
            print_strings.append(f"{filepath:50} {sorted(instance.matches)}")
        print("\n".join(sorted(print_strings)))


class InstanceFile:
    """Class to manage an instance file."""

    def __init__(self, root, filename, matches=None):
        """Initializes InstanceFile object.

        Args:
            root (string): Absolute path to the directory where the schema file is located.
            filename (string): Name of the file.
            matches (set, optional): Set of schema IDs that matches with this Instance file. Defaults to None.
        """
        self.data = None
        self.path = root
        self.full_path = os.path.realpath(root)
        self.filename = filename

        # Internal vars for caching data
        self._top_level_properties = set()

        if matches:
            self.matches = matches
        else:
            self.matches = set()

        self._add_matches_by_decorator()

    @property
    def top_level_properties(self):
        """Return a list of top level properties in the structured data defined by the data pulled from _get_content.

        Returns:
            set: Set of the strings of top level properties defined by the data file
        """
        if not self._top_level_properties:
            content = self._get_content()
            # TODO: Investigate and see if we should be checking this on initialization if the file doesn't exists or is empty.
            if not content:
                return self._top_level_properties

            if isinstance(content, CommentedMap) or hasattr(content, "keys"):
                self._top_level_properties = set(content.keys())
            elif isinstance(content, str):
                self._top_level_properties = set([content])
            elif isinstance(content, list):
                properties = set()
                for m in content:
                    if isinstance(m, dict) or hasattr(m, "keys"):
                        properties.update(m.keys())
                    else:
                        properties.add(m)
                self._top_level_properties = properties
            else:
                self._top_level_properties = set(content)

        return self._top_level_properties

    def _add_matches_by_decorator(self, content=None):
        """Add matches which declare schema IDs they should adhere to using a decorator comment.

        If a line of the form # jsonschema: <schema_id>,<schema_id> is defined in the data file, the
        schema IDs will be added to the list of schema IDs the data will be checked for adherence to.

        Args:
            content (string, optional): Content of the file to analyze. Default to None.

        Returns:
            set(string): Set of matches (strings of schema_ids) found in the file.
        """
        if not content:
            content = self._get_content(structured=False)

        matches = set()

        if SCHEMA_TAG in content:
            line_regexp = r"^#.*{0}:\s*(.*)$".format(SCHEMA_TAG)  # pylint: disable=consider-using-f-string
            match = re.match(line_regexp, content, re.MULTILINE)
            if match:
                matches = {x.strip() for x in match.group(1).split(",")}

        self.matches.update(matches)

    def _get_content(self, structured=True):
        """Returns the content of the instance file.

        Args:
            structured (bool): Return structured data if true. If false returns the string representation of the data
            stored in the instance file. Defaults to True.

        Returns:
            dict, list, or str: File Contents. Dict or list if structured is set to True. Otherwise returns a string.
        """
        file_location = os.path.join(self.full_path, self.filename)

        if not structured:
            return Path(file_location).read_text(encoding="utf-8")

        return load_file(file_location)

    def add_matches_by_property_automap(self, schema_manager):
        """Adds schema_ids to self.matches by automapping top level schema properties to top level keys in instance data.

        Args:
            schema_manager (schema_enforcer.schemas.manager.SchemaManager): Schema manager oject
        """
        matches = set()

        for schema_id, schema_obj in schema_manager.iter_schemas():
            if schema_obj.top_level_properties.intersection(self.top_level_properties):
                matches.add(schema_id)

        self.matches.update(matches)

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
            schema.validate(self._get_content(), strict)
            results = schema.get_results()
            errs = itertools.chain(errs, results)
            schema.clear_results()

        return errs
