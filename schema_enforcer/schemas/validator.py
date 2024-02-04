"""Classes for custom validator plugins."""
# pylint: disable=no-member, too-few-public-methods
# See PEP585 (https://www.python.org/dev/peps/pep-0585/)
from __future__ import annotations
from typing import Union
import pkgutil
import inspect
import jmespath
from pydantic import BaseModel, ValidationError
from schema_enforcer.validation import ValidationResult


class BaseValidation:
    """Base class for Validation classes."""

    def __init__(self):
        """Base init for all validation classes."""
        self._results: list[ValidationResult] = []

    def add_validation_error(self, message: str, **kwargs):
        """Add validator error to results.

        Args:
          message (str): error message
          kwargs (optional): additional arguments to add to ValidationResult when required
        """
        self._results.append(ValidationResult(result="FAIL", schema_id=self.id, message=message, **kwargs))

    def add_validation_pass(self, **kwargs):
        """Add validator pass to results.

        Args:
          kwargs (optional): additional arguments to add to ValidationResult when required
        """
        self._results.append(ValidationResult(result="PASS", schema_id=self.id, **kwargs))

    def get_results(self) -> list[ValidationResult]:
        """Return all validation results for this validator."""
        if not self._results:
            self._results.append(ValidationResult(result="PASS", schema_id=self.id))

        return self._results

    def clear_results(self):
        """Reset results for validator instance."""
        self._results = []

    def validate(self, data: dict, strict: bool):
        """Required function for custom validator.

        Args:
          data (dict): variables to be validated by validator
          strict (bool): true when --strict cli option is used to request strict validation (if provided)

        Returns:
          None

        Use add_validation_error and add_validation_pass to report results.
        """
        raise NotImplementedError


class JmesPathModelValidation(BaseValidation):
    """Base class for JmesPathModelValidation classes."""

    def validate(self, data: dict, strict: bool):  # pylint: disable=W0613
        """Validate data using custom jmespath validator plugin."""
        operators = {
            "gt": lambda r, v: int(r) > int(v),
            "gte": lambda r, v: int(r) >= int(v),
            "eq": lambda r, v: r == v,
            "lt": lambda r, v: int(r) < int(v),
            "lte": lambda r, v: int(r) <= int(v),
            "contains": lambda r, v: v in r,
        }
        lhs = jmespath.search(self.left, data)
        valid = True
        if lhs:
            # Check rhs for compiled jmespath expression
            if isinstance(self.right, jmespath.parser.ParsedResult):
                rhs = self.right.search(data)
            else:
                rhs = self.right
            valid = operators[self.operator](lhs, rhs)
        if not valid:
            self.add_validation_error(self.error)


class PydanticValidator(BaseValidation):
    """Basic wrapper for Pydantic models to be used as validators."""

    def __init__(self, model: BaseModel):
        """Override init to include Pydantic model."""
        super().__init__()
        self.model = model

    def validate(self, data: dict, strict: bool = False):
        """Validate data against Pydantic model.

        Args:
            data (dict): variables to be validated by validator
            strict (bool): true when --strict cli option is used to request strict validation (if provided)

        Returns:
            None

        Use add_validation_error and add_validation_pass to report results.
        """
        try:
            self.model.model_validate(data, strict=strict)
            self.add_validation_pass()
        except ValidationError as err:
            # TODO: Format the validation error from Pydantic to be more user friendly
            self.add_validation_error(str(err))


def is_validator(obj) -> bool:
    """Returns True if the object is a BaseValidation or JmesPathModelValidation subclass."""
    try:
        return (issubclass(obj, BaseValidation) or issubclass(obj, BaseModel)) and obj not in (
            JmesPathModelValidation,
            BaseValidation,
        )
    except TypeError:
        return False


def load_config_validators(
    validator_path: str,
    validator_packages: list,
) -> dict[str, Union[BaseValidation, PydanticValidator]]:
    """See if we still need this specific function."""
    validators = {}
    validator_packages.append(validator_path)
    for importer, module_name, _ in pkgutil.iter_modules(validator_packages):
        module = importer.find_module(module_name).load_module(module_name)
        for name, cls in inspect.getmembers(module, is_validator):
            # Default to class name if id doesn't exist
            if not hasattr(cls, "id"):
                cls.id = name

            # Skip any classes that are only BaseModel
            if cls == BaseModel:
                continue

            validator_kwargs = {}
            # If we're consuming Pydantic models, we need to set kwargs to pass in the Pydantic model
            if issubclass(cls, BaseModel):
                validator_kwargs = {"model": cls}
                cls = type(
                    cls.__name__,
                    (PydanticValidator,),
                    {
                        "id": name,
                        "top_level_properties": set([property for property in validator_kwargs["model"].model_fields]),
                    },
                )

            if cls.id in validators:
                print(
                    f"Unable to load the validator {cls.id}, there is already a validator with the same name ({name})."
                )
                continue

            validators[cls.id] = cls(**validator_kwargs)

    return validators


def load_validators(
    validator_path: str, validator_packages: list = None
) -> dict[str, Union[BaseValidation, PydanticValidator]]:
    """Load all validator plugins from validator_path."""
    if not validator_packages:
        validator_packages = []
    validators = load_config_validators(validator_path, validator_packages)
    return validators
