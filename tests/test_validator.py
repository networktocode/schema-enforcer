"""Test validator functions."""
import pytest
from schema_enforcer.schemas.validator import (
    BaseModel,
    BaseValidation,
    is_validator,
    JmesPathModelValidation,
    PydanticValidation,
    pydantic_validation_factory,
)


def test_is_validator_true():
    """
    Test if the is_validator function returns True for custom and Pydantic validators.
    """

    class CustomValidation(BaseValidation):
        """Custom model for testing."""

        def validate(self, data: dict, strict: bool = False):
            """Implement abstract method for testing."""

    assert is_validator(CustomValidation)
    assert is_validator(PydanticValidation)


@pytest.mark.parametrize("model", [BaseModel, BaseValidation, JmesPathModelValidation, int, str, dict, list])
def test_is_validator_false(model):
    """
    Test case to verify that the function is_validator returns False for various non validator types.
    """

    assert not is_validator(model)


def test_pydantic_validation_factory():
    """Test the pydantic factory provides the correct type and properties."""

    class TestModel(BaseModel):  # pylint: disable=too-few-public-methods
        """Custom model for testing."""

        field1: str = None
        field2: str = None

    # Add id as it's required further on and added when loading pydantic sub models.
    TestModel.id = TestModel.__name__
    validation = pydantic_validation_factory(TestModel)

    assert validation.__name__ == "TestModel"
    assert issubclass(validation, PydanticValidation)
    assert issubclass(validation, BaseValidation)
    assert validation.id == "TestModel"
    assert validation.top_level_properties == {"field1", "field2"}
