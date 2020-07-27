import os
import jsonref
from jsonschema_testing.utils import load_file, find_files

from .jsonschema import JsonSchema


class SchemaManager:
    """THe SchemaManager class is designed to load and organaized all the schemas."""

    def __init__(self, schema_directories, excluded_filenames):
        """Initialize the SchemaManager and search for all schema files in the schema_directories.

        Args:
            schema_directories  (list, str): The list of directories or python package names to search for schema files.
            (list, str): Specify any files that should be excluded from importing as schemas (exact matches).
        """
        self.schemas = {}

        files = find_files(
            file_extensions=[".yaml", ".yml", ".json"],
            search_directories=schema_directories,
            excluded_filenames=excluded_filenames,
            return_dir=True,
        )

        # For each schema file, determine the absolute path to the directory
        # Create and save a JsonSchema object for each file
        for root, filename in files:
            root = os.path.realpath(root)
            schema = self.create_schema_from_file(root, filename)
            self.schemas[schema.get_id()] = schema

    def create_schema_from_file(self, root, filename):
        """Create a new JsonSchema object for a given file
        
        Load the content from disk and resolve all JSONRef within the schema file

        Args:
            root (string): Absolute location of the file in the filesystem
            filename (string): Name of the file

        Returns:
            JsonSchema: JsonSchema object newly created
        """
        file_data = load_file(os.path.join(root, filename))

        # TODO Find the type of Schema based on the Type, currently only jsonschema is supported
        schema_type = "jsonschema"
        base_uri = f"file:{root}/"
        schema_full = jsonref.JsonRef.replace_refs(file_data, base_uri=base_uri, jsonschema=True, loader=load_file)
        return JsonSchema(schema=schema_full, filename=filename, root=root)

    def iter_schemas(self):
        """Return an iterator of all schemas in the SchemaManager

        Returns:
            Iterator: Iterator of all schemas in K,v format (key, value)
        """
        return self.schemas.items()
