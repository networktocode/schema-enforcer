"""Classes for custom validator plugins."""
# pylint: disable=E1101, R0903, W0122
from pathlib import Path
import jmespath
from schema_enforcer.validation import ValidationResult


class ValidationError(Exception):
    """Base exception for errors during validator."""


class ModelValidation:
    """Base class for ModelValidation classes. A singleton of each subclass will be stored in validators."""

    validators = []

    def __init_subclass__(cls, **kwargs):
        """Register singleton of each subclass."""
        super().__init_subclass__(**kwargs)
        cls.validators.append(cls())


class JmesPathModelValidation:
    """Base class for JmesPathModelValidation classes. A singleton of each subclass will be stored in validators."""

    validators = []

    def __init_subclass__(cls, **kwargs):
        """Register singleton of each subclass."""
        super().__init_subclass__(**kwargs)
        cls.validators.append(cls())

    @classmethod
    def validate(cls, data: dict, strict: bool):  # pylint: disable=W0613
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


def load_validators(validator_path: str):
    """Load all validator plugins from validator_path."""
    # Make base class and helper functions available to validation plugins without import
    context = {
        "ModelValidation": ModelValidation,
        "JmesPathModelValidation": JmesPathModelValidation,
        "ValidationError": ValidationError,
        "ValidationResult": ValidationResult,
        "jmes": jmespath.compile,
    }

    validator_path = Path(validator_path).expanduser().resolve()
    for filename in validator_path.glob("*.py"):
        source = open(filename).read()
        code = compile(source, filename, "exec")
        exec(code, context)  # nosec
    return ModelValidation.validators + JmesPathModelValidation.validators
