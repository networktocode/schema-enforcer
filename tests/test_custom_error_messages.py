# pylint: disable=redefined-outer-name
"""Tests to validate functions defined in jsonschema.py"""
import os
import pytest

from schema_enforcer.schemas.jsonschema import JsonSchema
from schema_enforcer.validation import RESULT_PASS, RESULT_FAIL
from schema_enforcer.utils import load_file

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures", "test_custom_errors")
LOADED_SCHEMA_DATA = load_file(os.path.join(FIXTURES_DIR, "schema", "schemas", "hosts.yml"))


@pytest.fixture
def schema_instance():
    """JSONSchema schema instance."""
    schema_instance = JsonSchema(
        schema=LOADED_SCHEMA_DATA,
        filename="hosts.yml",
        root=os.path.join(FIXTURES_DIR, "schema", "schemas"),
    )
    return schema_instance


@pytest.fixture
def valid_instance_data():
    """Valid instance data loaded from YAML file."""
    return load_file(os.path.join(FIXTURES_DIR, "hostvars", "chi-beijing-hosts", "hosts.yml"))


@pytest.fixture
def invalid_instance_data():
    """Invalid instance data loaded from YAML file."""
    return load_file(os.path.join(FIXTURES_DIR, "hostvars", "can-vancouver-hosts", "hosts.yml"))


@pytest.fixture
def invalid_instance_data_root():
    """Invalid instance data with a root level error. Loaded from YAML file."""
    return load_file(os.path.join(FIXTURES_DIR, "hostvars", "eng-london-hosts", "hosts.yml"))


class TestCustomErrors:
    """Tests custom error message handling in jsonschema.py"""

    @staticmethod
    def test_validate(schema_instance, valid_instance_data, invalid_instance_data, invalid_instance_data_root):
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
        assert validation_results[0].message == "'3' is not valid. Please see docs."
        assert validation_results[0].absolute_path == ["hosts", "2", "aliases", "0"]
        schema_instance.clear_results()

        # Custom error message at root level should be ignored
        schema_instance.validate(data=invalid_instance_data_root)
        validation_results = schema_instance.get_results()
        assert len(validation_results) == 1
        assert validation_results[0].schema_id == LOADED_SCHEMA_DATA.get("$id")
        assert validation_results[0].result == RESULT_FAIL
        assert (
            validation_results[0].message
            == "Additional properties are not allowed ('hosts_2' was unexpected)"
        )
        assert validation_results[0].absolute_path == []
        schema_instance.clear_results()
