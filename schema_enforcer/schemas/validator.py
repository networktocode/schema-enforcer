from pathlib import Path
import jmespath


class ValidationError(Exception):
    pass


class ModelValidation:
    """Base class for custom ModelValidation classes. A singleton of each subclass will be stored in validators. """

    validators = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.validators.append(cls())


class JmesPathModelValidation:
    """Base class for custom JmesPathModelValidation classes. A singleton of each subclass will be stored in validators. """

    validators = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.validators.append(cls())

    @classmethod
    def validate(cls, data: dict):
        operators = {
            "gt": lambda r, v: int(r) > int(v),
            "gte": lambda r, v: int(r) >= int(v),
            "eq": lambda r, v: r == v,
            "lt": lambda r, v: int(r) < int(v),
            "lte": lambda r, v: int(r) <= int(v),
            "contains": lambda r, v: v in r,
        }
        result = jmespath.search(cls.left, data)
        valid = True
        if result:
            if isinstance(result, list):
                result = result[0]
            valid = operators[cls.operator](result, cls.right)
        if not valid:
            raise ValidationError


def load(validator_path: str):
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
