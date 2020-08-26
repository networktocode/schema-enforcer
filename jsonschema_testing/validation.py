from typing import Dict, FrozenSet, List, Optional, Sequence, Set, Tuple, Union, Any
from enum import Enum, IntEnum
from pydantic import BaseModel
from termcolor import colored


class ResultEnum(str, Enum):
    passed = "PASS"
    failed = "FAIL"


class ValidationResult(BaseModel):

    result: ResultEnum
    schema_id: str
    instance_name: Optional[str]
    instance_location: Optional[str]
    instance_type: Optional[str]
    source: Any = None
    strict: bool = False

    # if failed
    absolute_path: Optional[List[str]] = []
    message: Optional[str]

    def passed(self):

        if self.result == ResultEnum.passed:
            return True

        return False

    def print(self):

        if self.result == ResultEnum.failed:
            self.print_failed()

        else:
            self.print_passed()

    def print_failed(self):
        print(
            colored(f"FAIL", "red") + f" | [ERROR] {self.message}"
            f" [{self.instance_type}] {self.instance_location}/{self.instance_name}"
            f" [PROPERTY] {':'.join(str(item) for item in self.absolute_path)}"
        )

    def print_passed(self):
        print(colored(f"PASS", "green") + f" [{self.instance_type}] {self.instance_location}/{self.instance_name}")
