"""Validation related classes."""
from typing import List, Optional, Any
from pydantic import BaseModel, validator  # pylint: disable=no-name-in-module
from termcolor import colored

RESULT_PASS = "PASS"  # nosec
RESULT_FAIL = "FAIL"


class ValidationResult(BaseModel):
    """ValidationResult object.

    This object is meant to store the result of a given test along with some contextual
    information about the test itself.
    """

    result: str
    schema_id: str
    instance_name: Optional[str]
    instance_location: Optional[str]
    instance_type: Optional[str]
    instance_hostname: Optional[str]
    source: Any = None
    strict: bool = False

    # if failed
    absolute_path: Optional[List[str]] = []
    message: Optional[str]

    @validator("result")
    def result_must_be_pass_or_fail(cls, var):  # pylint: disable=no-self-argument, no-self-use
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
        msg = colored("FAIL", "red") + f" | [ERROR] {self.message}"
        if self.instance_type == "FILE":
            msg += f" [{self.instance_type}] {self.instance_location}/{self.instance_name}"

        elif self.instance_type == "HOST":
            msg += f" [{self.instance_type}] {self.instance_hostname}"

        msg += f" [PROPERTY] {':'.join(str(item) for item in self.absolute_path)}"

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
