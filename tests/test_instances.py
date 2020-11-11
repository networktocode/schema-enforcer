"""
Tests objects from instances.py
"""
# pylint: disable=redefined-outer-name,unnecessary-comprehension

import os

import pytest

from jsonschema_testing.schemas.manager import SchemaManager
from jsonschema_testing.instances.file import InstanceFileManager, InstanceFile
from jsonschema_testing import config
from jsonschema_testing.validation import ValidationResult

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures", "test_instances")

CONFIG_DATA = {
    "main_directory": os.path.join(FIXTURES_DIR, "schema"),
    # "definitions_directory":
    # "schema_directory":
    "instance_search_directories": [os.path.join(FIXTURES_DIR, "hostvars")],
    "schema_mapping": {"dns.yml": ["schemas/dns_servers"]},
}


@pytest.fixture
def ifm():
    """
    Instantiate an InstanceFileManager Class for use in tests.

    Returns:
        InstanceFileManager: Instantiated InstanceFileManager class
    """
    # os.chdir(FIXTURES_DIR)
    config.load(config_data=CONFIG_DATA)
    instance_file_manager = InstanceFileManager(config.SETTINGS)

    return instance_file_manager


@pytest.fixture
def if_w_extended_matches():
    """
    InstanceFile class with extended matches defined as a `# jsonschema_testing:` decorator in the
    instance file.
    """
    config.load(config_data=CONFIG_DATA)
    if_instance = InstanceFile(root=os.path.join(FIXTURES_DIR, "hostvars", "eng-london-rt1"), filename="ntp.yaml")

    return if_instance


@pytest.fixture
def if_w_matches():
    """
    InstanceFile class with matches passed in
    """
    config.load(config_data=CONFIG_DATA)
    if_instance = InstanceFile(
        root=os.path.join(FIXTURES_DIR, "hostvars", "eng-london-rt1"),
        filename="dns.yaml",
        matches=["schemas/dns_servers"],
    )

    return if_instance


@pytest.fixture
def if_wo_matches():
    """
    InstanceFile class without matches passed in and without extended matches denoted in a `# jsonschema_testing`
    decorator in the instance file.
    """
    config.load(config_data=CONFIG_DATA)
    if_instance = InstanceFile(root=os.path.join(FIXTURES_DIR, "hostvars", "chi-beijing-rt1"), filename="syslog.yml")

    return if_instance


@pytest.fixture
def schema_manager():
    """
    Instantiated SchemaManager class

    Returns:
        SchemaManager
    """
    config.load(config_data=CONFIG_DATA)
    schema_manager = SchemaManager(config=config.SETTINGS)

    return schema_manager


class TestInstanceFileManager:
    """ Defines tests for InstanceFileManager class """

    @staticmethod
    def test_init(ifm):
        """
        Tests initialization of InstanceFileManager object
        """
        assert len(ifm.instances) == 4

    @staticmethod
    def test_print_instances_schema_mapping(ifm, capsys):
        """
        Tests print_instances_schema_mapping func
        """
        print_string = (
            "Instance File                                     Schema\n"
            "--------------------------------------------------------------------------------\n"
            "/local/tests/fixtures/test_instances/hostvars/chi-beijing-rt1/dns.yml ['schemas/dns_servers']\n"
            "/local/tests/fixtures/test_instances/hostvars/chi-beijing-rt1/syslog.yml []\n"
            "/local/tests/fixtures/test_instances/hostvars/eng-london-rt1/dns.yaml []\n"
            "/local/tests/fixtures/test_instances/hostvars/eng-london-rt1/ntp.yaml ['schemas/ntp']\n"
        )
        ifm.print_instances_schema_mapping()
        captured = capsys.readouterr()
        captured_stdout = captured[0]
        assert captured_stdout == print_string


class TestInstanceFile:
    """
    Methods to test the InstanceFile class
    """

    @staticmethod
    def test_init(if_wo_matches, if_w_matches, if_w_extended_matches):
        """
        Tests initialization of InstanceFile object

        Args:
            if_w_matches (InstanceFile): Initialized InstanceFile pytest fixture
        """
        assert if_wo_matches.matches == []
        assert not if_wo_matches.data
        assert if_wo_matches.path == os.path.join(FIXTURES_DIR, "hostvars", "chi-beijing-rt1")
        assert if_wo_matches.filename == "syslog.yml"

        assert if_w_matches.matches == ["schemas/dns_servers"]
        assert not if_w_matches.data
        assert if_w_matches.path == os.path.join(FIXTURES_DIR, "hostvars", "eng-london-rt1")
        assert if_w_matches.filename == "dns.yaml"

        assert if_w_extended_matches.matches == ["schemas/ntp"]
        assert not if_w_extended_matches.data
        assert if_w_extended_matches.path == os.path.join(FIXTURES_DIR, "hostvars", "eng-london-rt1")
        assert if_w_extended_matches.filename == "ntp.yaml"

    @staticmethod
    def test_get_content(if_w_matches):
        """
        Tests get_content method of InstanceFile object

        Args:
            if_w_matches (InstanceFile): Initialized InstanceFile pytest fixture
        """
        content = if_w_matches.get_content()
        assert content["dns_servers"][0]["address"] == "10.6.6.6"
        assert content["dns_servers"][1]["address"] == "10.7.7.7"

    @staticmethod
    def test_validate(if_w_matches, schema_manager):
        """
        Tests validate method of InstanceFile object

        Args:
            if_w_matches (InstanceFile): Initialized InstanceFile pytest fixture
        """
        errs = [err for err in if_w_matches.validate(schema_manager=schema_manager)]
        strict_errs = [err for err in if_w_matches.validate(schema_manager=schema_manager, strict=True)]

        assert len(errs) == 1
        assert errs[0].result == "PASS"
        assert not errs[0].message
        assert isinstance(errs[0], ValidationResult)

        assert len(strict_errs) == 1
        assert strict_errs[0].result == "FAIL"
        assert strict_errs[0].message == "Additional properties are not allowed ('fun_extr_attribute' was unexpected)"
        assert isinstance(strict_errs[0], ValidationResult)