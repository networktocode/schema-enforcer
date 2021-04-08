"""Exception classes used in Schema Enforcer.

Copyright (c) 2020 Network To Code, LLC <info@networktocode.com>
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
  http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


class SchemaNotDefined(Exception):
    """Raised when a schema is declared but not defined.

    Args (Exception): Base Exception Object
    """


class InvalidJSONSchema(Exception):
    """Raised when a JSONschema file is invalid.

    Args (Exception): Base Exception Object
    """

    def __init__(self, schema):
        """Provide instance variables when invalid schema is detected."""
        super().__init__(schema)
        self.schema = schema

    def __str__(self):
        """Generate error string including validation errors."""
        errors = [result.message for result in self.schema.check_if_valid() if not result.passed()]
        message = f"Invalid JSONschema file: {self.schema.filename} - {errors}"
        return message
