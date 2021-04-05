# pylint: disable=redefined-outer-name
""" Test manager.py SchemaManager class """
import os
import pytest
from schema_enforcer.schemas.manager import SchemaManager
from schema_enforcer.config import Settings
from schema_enforcer.exceptions import InvalidJSONSchema

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")

CONFIG = {
    "main_directory": os.path.join(FIXTURE_DIR, "test_instances", "schema"),
    "data_file_search_directories": [os.path.join(FIXTURE_DIR, "hostvars")],
    "schema_mapping": {"dns.yml": ["schemas/dns_servers"]},
}


@pytest.fixture
def schema_manager():
    """
    Instantiated SchemaManager class

    Returns:
        SchemaManager
    """
    schema_manager = SchemaManager(config=Settings(**CONFIG))

    return schema_manager


@pytest.mark.parametrize("schema_id, result_file", [(None, "all.txt"), ("schemas/dns_servers", "byid.txt")])
def test_dump(capsys, schema_manager, schema_id, result_file):
    """ Test validates schema dump for multiple parameters. """

    test_file = os.path.join(FIXTURE_DIR, "test_manager", "dump", result_file)
    with open(test_file) as res_file:
        expected = res_file.read()
    schema_manager.dump_schema(schema_id)
    captured = capsys.readouterr()
    assert captured.out == expected


def test_invalid():
    """ Test validates that SchemaManager reports an error when an invalid schema is loaded. """
    config = {
        "main_directory": os.path.join(FIXTURE_DIR, "test_manager", "invalid", "schema"),
        "data_file_search_directories": [os.path.join(FIXTURE_DIR, "hostvars")],
        "schema_mapping": {"dns.yml": ["schemas/dns_servers"]},
    }
    with pytest.raises(InvalidJSONSchema) as e:  # pylint: disable=invalid-name
        schema_manager = SchemaManager(config=Settings(**config))  # noqa pylint: disable=unused-variable
        expected_error = """Invalid JSONschema file: invalid.yml - ["'bla bla bla bla' is not of type 'object', 'boolean'", "'integer' is not of type 'object', 'boolean'"]"""
        assert expected_error in str(e)
