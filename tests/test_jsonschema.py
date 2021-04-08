# pylint: disable=redefined-outer-name
"""Tests to validate functions defined in jsonschema.py"""
import os
import pytest

from schema_enforcer.schemas.jsonschema import JsonSchema
from schema_enforcer.validation import RESULT_PASS, RESULT_FAIL
from schema_enforcer.utils import load_file

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures", "test_jsonschema")
LOADED_SCHEMA_DATA = load_file(os.path.join(FIXTURES_DIR, "schema", "schemas", "dns.yml"))
LOADED_INSTANCE_DATA = load_file(os.path.join(FIXTURES_DIR, "hostvars", "chi-beijing-rt1", "dns.yml"))


@pytest.fixture
def schema_instance():
    """JSONSchema schema instance."""
    schema_instance = JsonSchema(
        schema=LOADED_SCHEMA_DATA, filename="dns.yml", root=os.path.join(FIXTURES_DIR, "schema", "schemas"),
    )
    return schema_instance


@pytest.fixture
def valid_instance_data():
    """Valid instance data loaded from YAML file."""
    return load_file(os.path.join(FIXTURES_DIR, "hostvars", "chi-beijing-rt1", "dns.yml"))


@pytest.fixture
def invalid_instance_data():
    """Invalid instance data loaded from YAML file."""
    return load_file(os.path.join(FIXTURES_DIR, "hostvars", "can-vancouver-rt1", "dns.yml"))


@pytest.fixture
def strict_invalid_instance_data():
    """Invalid instance data when strict mode is used. Loaded from YAML file."""
    return load_file(os.path.join(FIXTURES_DIR, "hostvars", "eng-london-rt1", "dns.yml"))


class TestJsonSchema:
    """Tests methods relating to schema_enforcer.schemas.jsonschema.JsonSchema Class"""

    @staticmethod
    def test_init(schema_instance):
        """Tests __init__() magic method of JsonSchema class.

        Args:
            schema_instance (JsonSchema): Instance of JsonSchema class
        """
        assert schema_instance.filename == "dns.yml"
        assert schema_instance.root == os.path.join(FIXTURES_DIR, "schema", "schemas")
        assert schema_instance.data == LOADED_SCHEMA_DATA
        assert schema_instance.id == LOADED_SCHEMA_DATA.get("$id")  # pylint: disable=invalid-name

    @staticmethod
    def test_get_id(schema_instance):
        """Tests git_id() method of JsonSchema class.

        Args:
            schema_instance (JsonSchema): Instance of JsonSchema class
        """
        assert schema_instance.get_id() == "schemas/dns_servers"

    @staticmethod
    def test_validate(schema_instance, valid_instance_data, invalid_instance_data, strict_invalid_instance_data):
        """Tests validate method of JsonSchema class

        Args:
            schema_instance (JsonSchema): Instance of JsonSchema class
        """
        schema_instance.validate(data=valid_instance_data)
        validation_results = schema_instance.get_results()
        assert len(validation_results) == 1
        assert validation_results[0].schema_id == LOADED_SCHEMA_DATA.get("$id")
        assert validation_results[0].result == RESULT_PASS
        assert validation_results[0].message is None
        schema_instance.clear_results()

        schema_instance.validate(data=invalid_instance_data)
        validation_results = schema_instance.get_results()
        assert len(validation_results) == 1
        assert validation_results[0].schema_id == LOADED_SCHEMA_DATA.get("$id")
        assert validation_results[0].result == RESULT_FAIL
        assert validation_results[0].message == "True is not of type 'string'"
        assert validation_results[0].absolute_path == ["dns_servers", "0", "address"]
        schema_instance.clear_results()

        schema_instance.validate(data=strict_invalid_instance_data, strict=False)
        validation_results = schema_instance.get_results()
        assert validation_results[0].result == RESULT_PASS
        schema_instance.clear_results()

        schema_instance.validate(data=strict_invalid_instance_data, strict=True)
        validation_results = schema_instance.get_results()
        assert validation_results[0].result == RESULT_FAIL
        assert (
            validation_results[0].message
            == "Additional properties are not allowed ('fun_extr_attribute' was unexpected)"
        )
        schema_instance.clear_results()

    @staticmethod
    def test_format_checkers(schema_instance, data_instance, expected_error_message):
        """Test format checkers"""
        validation_results = list(schema_instance.validate(data=data_instance))
        assert validation_results[0].result == RESULT_FAIL
        assert validation_results[0].message == expected_error_message

    @staticmethod
    def test_validate_to_dict(schema_instance, valid_instance_data):
        """Tests validate_to_dict method of JsonSchema class

        Args:
            schema_instance (JsonSchema): Instance of JsonSchema class
        """
        validation_results_dicts = schema_instance.validate_to_dict(data=valid_instance_data)
        assert isinstance(validation_results_dicts, list)
        assert isinstance(validation_results_dicts[0], dict)
        assert "result" in validation_results_dicts[0]
        assert validation_results_dicts[0]["result"] == RESULT_PASS

    @staticmethod
    def test_get_validator():
        pass

    @staticmethod
    def test_get_strict_validator():
        pass

    @staticmethod
    def test_check_if_valid():
        schema_data = load_file(os.path.join(FIXTURES_DIR, "schema", "schemas", "invalid.yml"))
        schema_instance = JsonSchema(
            schema=schema_data, filename="invalid.yml", root=os.path.join(FIXTURES_DIR, "schema", "schemas"),
        )
        results = schema_instance.check_if_valid()
        for result in results:
            assert not result.passed()

    # def test_get_id():
