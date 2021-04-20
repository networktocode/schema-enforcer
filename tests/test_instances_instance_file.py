# pylint: disable=redefined-outer-name
""" Tests instances.py InstanceFile class"""

import os

import pytest

from schema_enforcer.schemas.manager import SchemaManager
from schema_enforcer.instances.file import InstanceFile, InstanceFileManager
from schema_enforcer.validation import ValidationResult
from schema_enforcer.config import Settings

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures", "test_instances")

CONFIG_DATA = {
    "main_directory": os.path.join(FIXTURES_DIR, "schema"),
    # "definitions_directory":
    # "schema_directory": os.path.join(FIXTURES_DIR, "schema", "schemas"),
    "data_file_search_directories": [os.path.join(FIXTURES_DIR, "hostvars")],
    "schema_mapping": {"dns.yml": ["schemas/dns_servers"]},
}


@pytest.fixture
def if_w_extended_matches():
    """
    InstanceFile class with extended matches defined as a `# jsonschema:` decorator in the
    instance file.
    """
    if_instance = InstanceFile(root=os.path.join(FIXTURES_DIR, "hostvars", "eng-london-rt1"), filename="ntp.yaml")

    return if_instance


@pytest.fixture
def if_w_matches():
    """
    InstanceFile class with matches passed in
    """
    if_instance = InstanceFile(
        root=os.path.join(FIXTURES_DIR, "hostvars", "eng-london-rt1"),
        filename="dns.yaml",
        matches={"schemas/dns_servers"},
    )

    return if_instance


@pytest.fixture
def if_wo_matches():
    """
    InstanceFile class without matches passed in and without extended matches denoted in a `# jsonschema`
    decorator in the instance file.
    """
    if_instance = InstanceFile(root=os.path.join(FIXTURES_DIR, "hostvars", "chi-beijing-rt1"), filename="syslog.yml")

    return if_instance


@pytest.fixture
def schema_manager():
    """
    Instantiated SchemaManager class

    Returns:
        SchemaManager
    """
    schema_manager = SchemaManager(config=Settings(**CONFIG_DATA))

    return schema_manager

@pytest.fixture
def ifm():
    """Instance of InstanceFileManager."""
    ifm = InstanceFileManager(config=Settings(**CONFIG_DATA))
    return ifm


def test_init(if_wo_matches, if_w_matches, if_w_extended_matches):
    """
    Tests initialization of InstanceFile object

    Args:
        if_w_matches (InstanceFile): Initialized InstanceFile pytest fixture
        if_wo_matches (InstanceFile): Initialized InstanceFile pytest fixture
        if_w_extended_matches (InstanceFile): Initizlized InstanceFile pytest fixture
    """
    assert if_wo_matches.matches == set()
    assert not if_wo_matches.data
    assert if_wo_matches.path == os.path.join(FIXTURES_DIR, "hostvars", "chi-beijing-rt1")
    assert if_wo_matches.filename == "syslog.yml"

    assert if_w_matches.matches == {
        "schemas/dns_servers",
    }
    assert not if_w_matches.data
    assert if_w_matches.path == os.path.join(FIXTURES_DIR, "hostvars", "eng-london-rt1")
    assert if_w_matches.filename == "dns.yaml"

    assert if_w_extended_matches.matches == {
        "schemas/ntp",
    }
    assert not if_w_extended_matches.data
    assert if_w_extended_matches.path == os.path.join(FIXTURES_DIR, "hostvars", "eng-london-rt1")
    assert if_w_extended_matches.filename == "ntp.yaml"


def test_get_content(if_w_matches):
    """
    Tests get_content method of InstanceFile object

    Args:
        if_w_matches (InstanceFile): Initialized InstanceFile pytest fixture
    """
    content = if_w_matches._get_content()  # pylint: disable=protected-access
    assert content["dns_servers"][0]["address"] == "10.6.6.6"
    assert content["dns_servers"][1]["address"] == "10.7.7.7"

    raw_content = if_w_matches._get_content(structured=False)
    with open (os.path.join(FIXTURES_DIR, "hostvars", "eng-london-rt1", "dns.yaml"), 'r') as fhd:
        assert raw_content == fhd.read()

def test_validate(if_w_matches, schema_manager):
    """
    Tests validate method of InstanceFile object

    Args:
        if_w_matches (InstanceFile): Initialized InstanceFile pytest fixture
        schema_manager (SchemaManager): Initialized SchemaManager object, needed to run "validate" method.
    """
    errs = list(if_w_matches.validate(schema_manager=schema_manager))
    strict_errs = list(if_w_matches.validate(schema_manager=schema_manager, strict=True))

    assert len(errs) == 1
    assert isinstance(errs[0], ValidationResult)
    assert errs[0].result == "PASS"
    assert not errs[0].message

    assert len(strict_errs) == 1
    assert isinstance(strict_errs[0], ValidationResult)
    assert strict_errs[0].result == "FAIL"
    assert strict_errs[0].message == "Additional properties are not allowed ('fun_extr_attribute' was unexpected)"

def test_add_matches_by_property_automap(if_wo_matches, schema_manager):
    """Tests add_matches_by_property_automap method of InstanceFile class."""
    assert not if_wo_matches.matches
    assert if_wo_matches.top_level_properties == {"syslog_servers"}
    if_wo_matches.add_matches_by_property_automap(schema_manager)
    assert if_wo_matches.matches == set(['schemas/syslog_servers'])
