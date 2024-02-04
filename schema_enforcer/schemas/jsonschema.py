"""class to manage jsonschema type schema."""
import copy
import json
import os
from functools import cached_property

from jsonschema import Draft7Validator  # pylint: disable=import-self
from schema_enforcer.schemas.validator import BaseValidation
from schema_enforcer.validation import ValidationResult, RESULT_FAIL, RESULT_PASS


class JsonSchema(BaseValidation):  # pylint: disable=too-many-instance-attributes
    """class to manage jsonschema type schemas."""

    schematype = "jsonchema"

    def __init__(self, schema, filename, root):
        """Initilize a new JsonSchema object from a dict.

        Args:
            schema (dict): Data representing the schema. Must be jsonschema valid.
            filename (string): Name of the schema file on the filesystem.
            root (string): Absolute path to the directory where the schema file is located.
        """
        super().__init__()
        self.filename = filename
        self.root = root
        self.data = schema
        self.id = self.data.get("$id")  # pylint: disable=invalid-name
        self.top_level_properties = set(self.data.get("properties"))
        self.validator = None
        self.strict_validator = None
        self.format_checker = Draft7Validator.FORMAT_CHECKER

    @cached_property
    def v7_schema(self):
        """Draft7 Schema."""
        local_dirname = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(local_dirname, "draft7_schema.json"), encoding="utf-8") as fhd:
            v7_schema = json.loads(fhd.read())

        return v7_schema

    def get_id(self):
        """Return the unique ID of the schema."""
        return self.id

    def validate(self, data, strict=False):
        """Validate a given data with this schema.

        Args:
            data (dict, list): Data to validate against the schema.
            strict (bool, optional): if True the validation will automatically flag additional properties. Defaults to False.

        Returns:
            Iterator: Iterator of ValidationResult
        """
        if strict:
            validator = self.__get_strict_validator()
        else:
            validator = self.__get_validator()

        has_error = False
        for err in validator.iter_errors(data):
            has_error = True
            self.add_validation_error(err.message, absolute_path=list(err.absolute_path))

        if not has_error:
            self.add_validation_pass()
        return self.get_results()

    def validate_to_dict(self, data, strict=False):
        """Return a list of ValidationResult objects.

        These are generated with the validate() function in dict() format instead of as a Python Object.

        Args:
            data (dict, list): Data to validate against the schema.
            strict (bool, optional): if True the validation will automatically flag additional properties. Defaults to False.

        Returns:
            list of dictionnaries containing the results.
        """
        return [
            result.model_dump(exclude_unset=True, exclude_none=True)
            for result in self.validate(data=data, strict=strict)
        ]

    def __get_validator(self):
        """Return the validator for this schema, create if it doesn't exist already.

        Returns:
            Draft7Validator: The validator for this schema.
        """
        if self.validator:
            return self.validator

        self.validator = Draft7Validator(self.data, format_checker=self.format_checker)

        return self.validator

    def __get_strict_validator(self):
        """Return a strict version of the Validator, create it if it doesn't exist already.

        To create a strict version of the schema, this function adds `additionalProperties` to all objects in the schema.

        Returns:
            Draft7Validator: Validator for this schema in strict mode.
        """
        # TODO Currently the function is only modifying the top level object, need to add that to all objects recursively
        if self.strict_validator:
            return self.strict_validator

        # Create a copy if the schema first and modify it to insert `additionalProperties`
        schema = copy.deepcopy(self.data)

        if schema.get("additionalProperties", False) is not False:
            print(f"{schema['$id']}: Overriding existing additionalProperties: {schema['additionalProperties']}")

        schema["additionalProperties"] = False

        # TODO This should be recursive, e.g. all sub-objects, currently it only goes one level deep, look in jsonschema for utilitiies
        for prop_name, prop in schema.get("properties", {}).items():
            items = prop.get("items", {})
            if items.get("type") == "object":
                if items.get("additionalProperties", False) is not False:
                    print(
                        f"{schema['$id']}: Overriding item {prop_name}.additionalProperties: {items['additionalProperties']}"
                    )
                items["additionalProperties"] = False

        self.strict_validator = Draft7Validator(schema, format_checker=self.format_checker)
        return self.strict_validator

    def check_if_valid(self):
        """Check if the schema definition is valid against JsonSchema draft7.

        Returns:
            List[ValidationResult]: A list of validation result objects.
        """
        validator = Draft7Validator(self.v7_schema, format_checker=self.format_checker)

        results = []
        has_error = False
        for err in validator.iter_errors(self.data):
            has_error = True

            results.append(
                ValidationResult(
                    schema_id=self.id,
                    result=RESULT_FAIL,
                    message=err.message,
                    absolute_path=list(err.absolute_path),
                    instance_type="SCHEMA",
                    instance_name=self.id,
                    instance_location="",
                )
            )

        if not has_error:
            results.append(
                ValidationResult(
                    schema_id=self.id,
                    result=RESULT_PASS,
                    instance_type="SCHEMA",
                    instance_name=self.id,
                    instance_location="",
                )
            )

        return results
