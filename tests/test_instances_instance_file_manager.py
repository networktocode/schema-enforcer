"""
Tests instances.py InstanceFileManager class
"""
# pylint: disable=redefined-outer-name,unnecessary-comprehension

import os

import pytest

from schema_enforcer.schemas.manager import SchemaManager
from schema_enforcer.instances.file import InstanceFileManager, InstanceFile
from schema_enforcer import config
from schema_enforcer.config import Settings
from schema_enforcer.validation import ValidationResult

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures", "test_instances")

CONFIG_DATA = {
    "main_directory": os.path.join(FIXTURES_DIR, "schema"),
    # "definitions_directory":
    # "schema_directory":
    "data_file_search_directories": [os.path.join(FIXTURES_DIR, "hostvars")],
    "schema_mapping": {"dns.yml": ["schemas/dns_servers"]},
}


@pytest.fixture
def ifm():
    """
    Instantiate an InstanceFileManager Class for use in tests.

    Returns:
        InstanceFileManager: Instantiated InstanceFileManager class
    """
    instance_file_manager = InstanceFileManager(Settings(**CONFIG_DATA))

    return instance_file_manager


def test_init(ifm):
    """
    Tests initialization of InstanceFileManager object
    """
    assert len(ifm.instances) == 4


def test_print_instances_schema_mapping(ifm, capsys):
    """
    Tests print_instances_schema_mapping func of InstanceFileManager object
    """
    print_string = (
        "Structured Data File                               Schema ID\n"
        "--------------------------------------------------------------------------------\n"
        "/local/tests/fixtures/test_instances/hostvars/chi-beijing-rt1/dns.yml ['schemas/dns_servers']\n"
        "/local/tests/fixtures/test_instances/hostvars/chi-beijing-rt1/syslog.yml []\n"
        "/local/tests/fixtures/test_instances/hostvars/eng-london-rt1/dns.yaml []\n"
        "/local/tests/fixtures/test_instances/hostvars/eng-london-rt1/ntp.yaml ['schemas/ntp']\n"
    )
    ifm.print_schema_mapping()
    captured = capsys.readouterr()
    captured_stdout = captured[0]
    assert captured_stdout == print_string
