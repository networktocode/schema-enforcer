"""Validation related classes."""
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict, field_validator  # pylint: disable=no-name-in-module
from termcolor import colored

RESULT_PASS = "PASS"  # nosec
RESULT_FAIL = "FAIL"


class ValidationResult(BaseModel):
    """ValidationResult object.

    This object is meant to store the result of a given test along with some contextual
    information about the test itself.
    """

    # Added to allow coercion of numbers to strings as this doesn't appear to be a default in v2
    model_config = ConfigDict(coerce_numbers_to_str=True)

    result: str
    schema_id: str
    instance_name: Optional[str] = None
    instance_location: Optional[str] = None
    instance_type: Optional[str] = None
    instance_hostname: Optional[str] = None
    source: Any = None
    strict: bool = False

    # if failed
    absolute_path: Optional[List[str]] = []
    message: Optional[str] = None

    # TODO: I believe we can change result to be an Enum and accomplish the same result with less code.
    @field_validator("result")
    def result_must_be_pass_or_fail(cls, var):  # pylint: disable=no-self-argument
        """Validate that result either PASS or FAIL."""
        if var.upper() not in [RESULT_PASS, RESULT_FAIL]:
            raise ValueError("must be either PASS or FAIL")
        return var.upper()

    def passed(self):
        """Return True or False to indicate if the test has passed.

        Returns
            Bool: indicate if the test passed or failed
        """
        if self.result == RESULT_PASS:
            return True

        return False

    def print(self):
        """Print the result of the test in CLI."""
        if self.passed():
            self.print_passed()
        else:
            self.print_failed()

    def print_failed(self):
        """Print the result of the test to CLI when the test failed."""
        # Construct the message dynamically based on the instance_type
        msg = f"{colored('FAIL', 'red')} |"
        if self.instance_type == "FILE":
            msg += f" [{self.instance_type}] {self.instance_location}/{self.instance_name}"

        elif self.instance_type == "HOST":
            msg += f" [{self.instance_type}] {self.instance_hostname}"

        if self.schema_id:
            msg += f" [SCHEMA ID] {self.schema_id}"

        if self.absolute_path:
            msg += f" [PROPERTY] {':'.join(str(item) for item in self.absolute_path)}"

        if self.message:
            msg += f"\n      | [ERROR] {self.message}"

        # print the msg
        print(msg)

    def print_passed(self):
        """Print the result of the test to CLI when the test passed."""
        if self.instance_type == "FILE":
            print(colored("PASS", "green") + f" | [{self.instance_type}] {self.instance_location}/{self.instance_name}")

        if self.instance_type == "HOST":
            print(
                colored("PASS", "green")
                + f" | [{self.instance_type}] {self.instance_hostname} [SCHEMA ID] {self.schema_id}"
            )
