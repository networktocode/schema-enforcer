
import os
import jsonref
from jsonschema_testing.utils import load_file, find_files

from .jsonschema import JsonSchema

class SchemaManager:

    def __init__(self, schema_directories, excluded_filenames, file_extensions=[]):

        self.schemas = {}

        files = find_files(
            file_extensions=[".yaml", ".yml", ".json"],
            search_directories=schema_directories,
            excluded_filenames=excluded_filenames,
            return_dir=True,
        )

        for root, filename in files:
            schema = self.create_schema_from_file(root, filename)
            self.schemas[schema.get_id()] = schema

    def create_schema_from_file(self, root, filename):

        file_data = load_file(os.path.join(root, filename))

        # TODO Find the type of Schema based on the Type, currently only jsonschema is supported
        schema_type = "jsonschema"
        base_uri = f"file:{root}/"
        schema = jsonref.JsonRef.replace_refs(file_data, base_uri=base_uri, jsonschema=True, loader=load_file)

        key = file_data.get("$id", filename)
        
        schema = JsonSchema(
            schema=schema,
            filename=filename,
            root=root
        )

        return schema
    
    def iter_schemas(self):
        return self.schemas.items()






