"""
Classes for custom validator plugins
"""
from pathlib import Path
import jmespath


class ValidationError(Exception):
    pass


class ModelValidation:
    """Base class for ModelValidation classes. A singleton of each subclass will be stored in validators. """

    validators = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.validators.append(cls())


class JmesPathModelValidation:
    """Base class for JmesPathModelValidation classes. A singleton of each subclass will be stored in validators. """

    validators = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.validators.append(cls())

    @classmethod
    def validate(cls, data: dict):
        """
        Validate data using custom jmespath validator plugin
        """
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
        if not valid:
            raise ValidationError


def load(validator_path: str):
    """
    Load all validator plugins from validator_path
    """
    # Make base class and helper functions available to validation plugins without import
    context = {
        "ModelValidation": ModelValidation,
        "JmesPathModelValidation": JmesPathModelValidation,
        "ValidationError": ValidationError,
        "jmes": jmespath.compile,
    }

    validator_path = Path(validator_path).expanduser().resolve()
    for filename in validator_path.glob("*.py"):
        source = open(filename).read()
        code = compile(source, filename, "exec")
        exec(code, context)
