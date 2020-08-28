import os
import json
import jsonref
from termcolor import colored
from jsonschema_testing.utils import load_file, load_data, find_and_load_file, find_files, dump_data_to_yaml
from jsonschema_testing.validation import ValidationResult, RESULT_PASS, RESULT_FAIL

from .jsonschema import JsonSchema


class SchemaManager:
    """THe SchemaManager class is designed to load and organaized all the schemas."""

    def __init__(self, config):
        """Initialize the SchemaManager and search for all schema files in the schema_directories.

        Args:
            schema_directories (list, str): The list of directories or python package names to search for schema files.
            excluded_filenames (list, str): Specify any files that should be excluded from importing as schemas (exact matches).
        """
        self.schemas = {}
        self.config = config

        full_schema_dir = f"{config.main_directory}/{config.schema_directory}/"

        files = find_files(
            file_extensions=[".yaml", ".yml", ".json"],
            search_directories=[full_schema_dir],
            excluded_filenames=config.schema_file_exclude_filenames,
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

    def test_schemas(self):
        """Tests if all schemas are passing their tests.
        
        For each schema, 3 set of tests will be potentially executed.
          - schema must be Draft7 valid
          - Valid tests must pass
          - Invalid tests must pass 
        """
        error_exists = False

        for schema_id, schema in self.iter_schemas():

            schema_valid = schema.check_if_valid()
            valid_results = self.test_schema_valid(schema_id)
            invalid_results = self.test_schema_invalid(schema_id)

            for result in schema_valid + valid_results + invalid_results:
                if not result.passed():
                    error_exists = True

                result.print()

        if not error_exists:
            print(colored("ALL SCHEMAS ARE VALID", "green"))

    def test_schema_valid(self, schema_id, strict=False):
        """
        Execute all valid tests for a given schema. 

        Args:
            schema_id (str): unique identifier of a schema
        
        Returns:
            list of ValidationResult
        """

        schema = self.schemas[schema_id]

        # TODO Check if top dir is present
        # TODO Check if valid dir is present

        # See how we can define a better name
        short_schema_id = schema_id.split("/")[1]
        test_dir = self._get_test_directory()
        valid_test_dir = f"{test_dir}/{short_schema_id}/valid"

        valid_files = find_files(
            file_extensions=[".yaml", ".yml", ".json"],
            search_directories=[valid_test_dir],
            excluded_filenames=[],
            return_dir=True,
        )

        results = []

        for root, filename in valid_files:

            test_data = load_file(os.path.join(root, filename))

            error_exists = False
            for result in schema.validate(test_data, strict=strict):
                result.instance_name = filename
                result.instance_location = root
                result.instance_type = "TEST"
                results.append(result)

        return results

    def test_schema_invalid(self, schema_id, strict=False):
        """
        Execute all invalid tests for a given schema. 

        Args:
            schema_id (str): unique identifier of a schema
        
        Returns:
            list of ValidationResult
        """

        schema = self.schemas[schema_id]

        root = os.path.abspath(os.getcwd())
        test_dir = self._get_test_directory()
        short_schema_id = schema_id.split("/")[1]
        invalid_test_dir = f"{test_dir}/{short_schema_id}/invalid"
        test_dirs = next(os.walk(invalid_test_dir))[1]

        results = []
        for test_dir in test_dirs:

            # TODO Check if data and expected results are present
            data = find_and_load_file(os.path.join(root, invalid_test_dir, test_dir, "data"))
            expected_results = find_and_load_file(os.path.join(root, invalid_test_dir, test_dir, "results"))
            tmp_results = schema.validate_to_dict(data)

            if not expected_results:
                continue

            # Currently the expected results are using OrderedDict instead of Dict
            # the easiest way to remove that is to dump into JSON and convert back into a "normal" dict
            expected_results = json.loads(json.dumps(expected_results["results"]))

            results_sorted = sorted(tmp_results, key=lambda i: i.get("message", ""))
            expected_results_sorted = sorted(expected_results, key=lambda i: i.get("message", ""))

            params = dict(
                schema_id=schema_id, instance_type="TEST", instance_name=test_dir, instance_location=invalid_test_dir
            )
            import pdb

            pdb.set_trace()
            if results_sorted != expected_results_sorted:
                params["result"] = RESULT_FAIL
                params["message"] = "Invalid test do not match"
            else:
                params["result"] = RESULT_PASS

            val = ValidationResult(**params)
            results.append(val)

        return results  # [ ValidationResult(**result) for result in results ]

    def generate_invalid_tests_expected(self, schema_id):
        """
        Generate the expected invalid tests for a given Schema.

        Args:
            schema_id (str): unique identifier of a schema
        """

        # TODO check if schema is present
        schema = self.schemas[schema_id]

        root = os.path.abspath(os.getcwd())
        short_schema_id = schema_id.split("/")[1]

        # TODO Check if invalid dir exist for this schema
        # Find list of all subdirectory in the invalid dir
        test_dir = self._get_test_directory()
        invalid_test_dir = f"{test_dir}/{short_schema_id}/invalid"
        test_dirs = next(os.walk(invalid_test_dir))[1]

        # For each test, load the data file, test the data against the schema and save the results
        for test_dir in test_dirs:
            data = find_and_load_file(os.path.join(root, invalid_test_dir, test_dir, "data"))
            results = schema.validate_to_dict(data)
            result_file = os.path.join(root, invalid_test_dir, test_dir, "results.yml")
            dump_data_to_yaml({"results": results}, result_file)
            print(f"Generated/Updated results file: {result_file}")

    def _get_test_directory(self):
        """Return the path to the main schema test directory."""
        return f"{self.config.main_directory}/{self.config.test_directory}"
