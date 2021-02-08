"""Classes for custom validator plugins."""
# pylint: disable=E1101, R0903, W0122
import pkgutil
import inspect
from typing import Iterable, Union
import jmespath
from schema_enforcer.validation import ValidationResult


class ModelValidation:
    """Base class for ModelValidation classes."""

    @classmethod
    def validate(cls, data: dict, strict: bool) -> Iterable[ValidationResult]:
        """Required function for custom validator."""


class JmesPathModelValidation:
    """Base class for JmesPathModelValidation classes."""

    @classmethod
    def validate(cls, data: dict, strict: bool) -> Iterable[ValidationResult]:  # pylint: disable=W0613
        """Validate data using custom jmespath validator plugin."""
        operators = {
            "gt": lambda r, v: int(r) > int(v),
            "gte": lambda r, v: int(r) >= int(v),
            "eq": lambda r, v: r == v,
            "lt": lambda r, v: int(r) < int(v),
            "lte": lambda r, v: int(r) <= int(v),
            "contains": lambda r, v: v in r,
        }
        lhs = jmespath.search(cls.left, data)
        valid = True
        if lhs:
            # Check rhs for compiled jmespath expression
            if isinstance(cls.right, jmespath.parser.ParsedResult):
                rhs = cls.right.search(data)
            else:
                rhs = cls.right
            valid = operators[cls.operator](lhs, rhs)
        if valid:
            result = "PASS"
        else:
            result = "FAIL"
        return [ValidationResult(result=result, schema_id=cls.id, message=cls.error)]


def is_validator(obj) -> bool:
    """Returns True if the object is a ModelValidation or JmesPathModelValidation subclass."""
    try:
        return issubclass(obj, (JmesPathModelValidation, ModelValidation)) and obj not in (
            JmesPathModelValidation,
            ModelValidation,
        )
    except TypeError:
        return False


def load_validators(validator_path: str) -> Iterable[Union[ModelValidation, JmesPathModelValidation]]:
    """Load all validator plugins from validator_path."""
    validators = dict()
    for importer, module_name, _ in pkgutil.iter_modules([validator_path]):
        module = importer.find_module(module_name).load_module(module_name)
        for name, cls in inspect.getmembers(module, is_validator):
            if name in validators:
                print(f"Duplicate validator name: {name}")
            else:
                validators[name] = cls
    return validators
