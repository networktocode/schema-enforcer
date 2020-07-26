import copy
from jsonschema import (
    Draft7Validator,
    draft7_format_checker,
    ValidationError,
)


class JsonSchema:

    schematype = "jsonchema"

    def __init__(self, schema, filename, root):

        self.filename = filename
        self.root = root
        self.data = schema
        self.id = self.data.get("$id")
        self.validator = None
        self.strict_validator = None

    def get_id(self):
        return self.id

    def validate(self, data, strict=False):

        if strict:
            validator = self.__get_strict_validator()
        else:
            validator = self.__get_validator()

        return validator.iter_errors(data)

    def __get_validator(self):

        if self.validator:
            return self.validator

        self.validator = Draft7Validator(self.data)

        return self.validator

    def __get_strict_validator(self):

        if self.strict_validator:
            return self.strict_validator

        schema = copy.deepcopy(self.data)

        if schema.get("additionalProperties", False) is not False:
            print(f"{schema['$id']}: Overriding existing additionalProperties: {schema['additionalProperties']}")

        schema["additionalProperties"] = False

        # XXX This should be recursive, e.g. all sub-objects, currently it only goes one level deep, look in jsonschema for utilitiies
        for p, prop in schema.get("properties", {}).items():
            items = prop.get("items", {})
            if items.get("type") == "object":
                if items.get("additionalProperties", False) is not False:
                    print(f"{schema['$id']}: Overriding item {p}.additionalProperties: {items['additionalProperties']}")
                items["additionalProperties"] = False

        self.strict_validator = Draft7Validator(schema)

        return self.strict_validator

    # @staticmethod
    # def print_error(err, schema_id, instance_file):
    #     if len(err.absolute_path) > 0:
    #         print(
    #             colored(f"FAIL", "red") + f" | [ERROR] {err.message}"
    #             f" [FILE] {instance_file}"
    #             f" [PROPERTY] {':'.join(str(item) for item in err.absolute_path)}"
    #             # f" [SCHEMA] {schema_file.split('/')[-1]}"
    #             f" [SCHEMA] {schema_id}"
    #         )

    #     elif len(err.absolute_path) == 0:
    #         print(
    #             colored(f"FAIL", "red") + f" | [ERROR] {err.message}"
    #             f" [FILE] {instance_file}"
    #             # f" [SCHEMA] {schema_file.split('/')[-1]}"
    #             f" [SCHEMA] {schema_id}"
    #         )
