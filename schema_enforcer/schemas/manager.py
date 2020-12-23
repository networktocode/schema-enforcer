"""Schema manager."""
import os
import json
import jsonref
from termcolor import colored
from schema_enforcer.utils import load_file, find_file, find_and_load_file, find_files, dump_data_to_yaml
from schema_enforcer.validation import ValidationResult, RESULT_PASS, RESULT_FAIL
from schema_enforcer.exceptions import SchemaNotDefined
from schema_enforcer.utils import error, warn
import sys

from schema_enforcer.schemas.jsonschema import JsonSchema

from rich.console import Console
from rich.table import Table


class SchemaManager:
    """The SchemaManager class is designed to load and organaized all the schemas."""

    def __init__(self, config):
        """Initialize the SchemaManager and search for all schema files in the schema_directories.

        Args:
            config (Config): Instance of Config object returned by schema_enforcer.config.load() method.
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

    def create_schema_from_file(self, root, filename):  # pylint: disable=no-self-use
        """Create a new JsonSchema object for a given file.

        Load the content from disk and resolve all JSONRef within the schema file.

        Args:
            root (string): Absolute location of the file in the filesystem.
            filename (string): Name of the file.

        Returns:
            JsonSchema: JsonSchema object newly created.
        """
        file_data = load_file(os.path.join(root, filename))

        # TODO Find the type of Schema based on the Type, currently only jsonschema is supported
        # schema_type = "jsonschema"
        base_uri = f"file:{root}/"
        schema_full = jsonref.JsonRef.replace_refs(file_data, base_uri=base_uri, jsonschema=True, loader=load_file)
        return JsonSchema(schema=schema_full, filename=filename, root=root)

    def iter_schemas(self):
        """Return an iterator of all schemas in the SchemaManager.

        Returns:
            Iterator: Iterator of all schemas in K,v format (key, value).
        """
        return self.schemas.items()

    def print_schemas_list(self):
        """Print the list of all schemas to the cli.

        To avoid very long location string, dynamically replace the current dir with a dot.
        """
        console = Console()
        table = Table(show_header=True, header_style="bold cyan")
        current_dir = os.getcwd()
        table.add_column("Schema ID", style="bright_green")
        table.add_column("Type")
        table.add_column("Location")
        table.add_column("Filename")
        for schema_id, schema in self.iter_schemas():
            table.add_row(schema_id, schema.schematype, schema.root.replace(current_dir, "."), schema.filename)
        console.print(table)

    def test_schemas(self):
        """Validate all schemas passing tests defined for them.

        For each schema, 3 set of tests will be potentially executed.
          - schema must be Draft7 valid.
          - Valid tests must pass.
          - Invalid tests must pass.
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
        """Execute all valid tests for a given schema.

        Args:
            schema_id (str): The unique identifier of a schema.

        Returns:
            list of ValidationResult.
        """
        schema = self.schemas[schema_id]

        # TODO Check if top dir is present
        # TODO Check if valid dir is present

        # See how we can define a better name
        short_schema_id = schema_id.split("/")[1]
        test_dir = self.test_directory
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

            for result in schema.validate(test_data, strict=strict):
                result.instance_name = filename
                result.instance_location = root
                result.instance_type = "TEST"
                results.append(result)

        return results

    def test_schema_invalid(self, schema_id):  # pylint: disable=too-many-locals
        """Execute all invalid tests for a given schema.

        - Acquire structured data to be validated against a given schema. Do this by searching for a file named
          "data.yml", "data.yaml", or "data.json" within a directory of hierarchy
          "./<test_directory>/<schema_id>/invalid/"
        - Acquire results expected after data is validated against a giveh schema. Do this by searching for a file
          named "results.yml", "results.yaml", or "results.json" within a directory of hierarchy
          "./<test_directory>/<schema_id>/results/"
        - Validate expected results match actual results of data after it is checked for adherence to schema.

        Args:
            schema_id (str): The unique identifier of a schema.

        Returns:
            list of ValidationResult objects.
        """
        schema = self.schemas[schema_id]

        root = os.path.abspath(os.getcwd())
        short_schema_id = schema_id.split("/")[1] if "/" in schema_id else schema_id
        invalid_test_dir = f"{self.test_directory}/{short_schema_id}/invalid"
        if not os.path.exists(os.path.join(root, invalid_test_dir)):
            error("Tried to search {} for invalid data and results, but the path does not exist.".format(os.path.join(root, invalid_test_dir)))
            sys.exit(1)
        test_dirs = next(os.walk(invalid_test_dir))[1]

        results = []
        for test_dir in test_dirs:
            data_file = find_file(os.path.join(root, invalid_test_dir, test_dir, "data"))
            expected_results_file = find_file(os.path.join(root, invalid_test_dir, test_dir, "results"))

            if not data_file:
                warn("Could not find data file {}. Skipping...".format(os.path.join(root, invalid_test_dir, test_dir, "data")))
                continue

            if not expected_results_file:
                warn("Could not find expected_results_file {}. Skipping...".format(os.path.join(root, invalid_test_dir, test_dir, "results")))
                continue

            data = load_file(data_file)
            expected_results = load_file(expected_results_file)

            tmp_results = schema.validate_to_dict(data)

            # Currently the expected results are using OrderedDict instead of Dict
            # the easiest way to remove that is to dump into JSON and convert back into a "normal" dict
            expected_results = json.loads(json.dumps(expected_results["results"]))

            results_sorted = sorted(tmp_results, key=lambda i: i.get("message", ""))
            expected_results_sorted = sorted(expected_results, key=lambda i: i.get("message", ""))

            params = dict(
                schema_id=schema_id, instance_type="TEST", instance_name=test_dir, instance_location=invalid_test_dir
            )
            if results_sorted != expected_results_sorted:
                params["result"] = RESULT_FAIL
                params["message"] = "Invalid test results do not match expected test results from {}".format(
                    expected_results_file
                )
            else:
                params["result"] = RESULT_PASS

            val = ValidationResult(**params)
            results.append(val)

        return results  # [ ValidationResult(**result) for result in results ]

    def generate_invalid_tests_expected(self, schema_id):
        """Generate expected invalid test results for a given schema.

        Args:
            schema_id (str): unique identifier of a schema
        """
        schema = self.schemas[schema_id]
        root = os.path.abspath(os.getcwd())
        short_schema_id = schema_id.split("/")[1]

        # Find list of all subdirectory in the invalid dir
        invalid_test_dir = f"{self.test_directory}/{short_schema_id}/invalid"
        if not os.path.exists(os.path.join(root, invalid_test_dir)):
            error("Tried to search {} for invalid data and results, but the path does not exist.".format(os.path.join(root, invalid_test_dir)))
            sys.exit(1)

        test_dirs = next(os.walk(invalid_test_dir))[1]

        # For each test, load the data file, test the data against the schema and save the results
        for test_dir in test_dirs:

            data_file = find_file(os.path.join(root, invalid_test_dir, test_dir, "data"))

            if not data_file:
                warn("Could not find data file {}".format(os.path.join(root, invalid_test_dir, test_dir, f"data")))

            data = load_file(data_file)
            results = schema.validate_to_dict(data)
            result_file = os.path.join(root, invalid_test_dir, test_dir, "results.yml")
            dump_data_to_yaml({"results": results}, result_file)
            print(f"Generated/Updated results file: {result_file}")

    @property
    def test_directory(self):
        """Return the path to the main schema test directory."""
        return f"{self.config.main_directory}/{self.config.test_directory}"

    def validate_schemas_exist(self, schema_ids):
        """Validate that each schema ID in a list of schema IDs exists.

        Args:
            schema_ids (list): A list of schema IDs, each of which should exist as a schema object.
        """
        if not isinstance(schema_ids, list):
            raise TypeError("schema_ids argument passed into validate_schemas_exist must be of type list")
        for schema_id in schema_ids:
            if not self.schemas.get(schema_id, None):
                raise SchemaNotDefined(f"Schema ID {schema_id} declared but not defined")
