"""Classes for custom validator plugins."""

# pylint: disable=no-member, too-few-public-methods
# See PEP585 (https://www.python.org/dev/peps/pep-0585/)
from __future__ import annotations
from typing import List, Union
import pkgutil
import importlib
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


class PydanticValidation(BaseValidation):
    """Basic wrapper for Pydantic models to be used as validators."""

    model: BaseModel

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
            self.add_validation_error(str(err))


def is_validator(obj) -> bool:
    """Returns True if the object is a BaseValidation or JmesPathModelValidation subclass."""
    try:
        return (issubclass(obj, BaseValidation) or issubclass(obj, BaseModel)) and obj not in (
            BaseModel,
            BaseValidation,
            JmesPathModelValidation,
        )
    except TypeError:
        return False


def pydantic_validation_factory(orig_model) -> PydanticValidation:
    """Create a PydanticValidation instance from a Pydantic model."""
    return type(
        orig_model.__name__,
        (PydanticValidation,),
        {
            "id": f"{orig_model.id}",
            "top_level_properties": set([property for property in orig_model.model_fields]),
            "model": orig_model,
        },
    )


def load_pydantic_validators(
    model_packages: list,
) -> dict[str, PydanticValidation]:
    """Load all validator plugins from validator_packages."""
    validators = {}
    for package in model_packages:
        module_name, attr = package.split(":")
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            print(f"Unable to load the validator {package}, the module ({module_name}) does not exist.")
            continue

        manager = getattr(module, attr, None)
        if not manager:
            print(f"Unable to load the validator {package}, the module or attribute ({attr}) does not exist.")
            continue

        for model in manager.models:
            model.id = f"{manager.prefix}/{model.__name__}" if manager.prefix else model.__name__
            cls = pydantic_validation_factory(model)

            if cls.id in validators:
                print(f"Unable to load the validator {cls.id}, there is already a validator with the same name.")
                continue

            validators[cls.id] = cls()

    return validators


def load_validators_path(
    validators_path: str,
) -> dict[str, Union[BaseValidation, PydanticValidation]]:
    """Load all validators from local path."""
    validators = {}
    for importer, module_name, _ in pkgutil.iter_modules([validators_path]):
        module = importer.find_module(module_name).load_module(module_name)
        for name, cls in inspect.getmembers(module, is_validator):
            # Default to class name if id doesn't exist
            if not hasattr(cls, "id"):
                cls.id = name

            if issubclass(cls, BaseModel) and not issubclass(cls, PydanticValidation):
                # Save original pydantic model that will be used for validation
                cls = pydantic_validation_factory(cls)

            if cls.id in validators:
                print(
                    f"Unable to load the validator {cls.id}, there is already a validator with the same name ({name})."
                )
                continue

            validators[cls.id] = cls()

    return validators


def load_validators(
    validators_path: str, pydantic_validators: List[str] = None
) -> dict[str, Union[BaseValidation, PydanticValidation]]:
    """Load all validator plugins from validator_path."""
    if not pydantic_validators:
        pydantic_validators = []
    validators = load_validators_path(validators_path)
    validators.update(load_pydantic_validators(pydantic_validators))
    return validators
