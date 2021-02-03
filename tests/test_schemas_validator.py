import os
import pytest
from schema_enforcer.ansible_inventory import AnsibleInventory
import schema_enforcer.schemas.validator as v

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures", "test_validators")


@pytest.fixture
def inventory():
    """ Fixture for Ansible inventory used in tests """
    inventory_dir = os.path.join(FIXTURE_DIR, "inventory")

    inventory = AnsibleInventory(inventory_dir)  # pylint: disable=redefined-outer-name
    return inventory


@pytest.fixture
def host_vars(inventory):  # pylint: disable=redefined-outer-name
    """ Fixture for providing Ansible host_vars as a consolidated dict """
    hosts = inventory.get_hosts_containing()
    host_vars = dict()  # pylint: disable=redefined-outer-name
    for host in hosts:
        hostname = host.get_vars()["inventory_hostname"]
        host_vars[hostname] = inventory.get_host_vars(host)
    return host_vars


def test_load():
    """
    Test that validator files are loaded and appended to base class validator list
    """
    validator_path = os.path.join(FIXTURE_DIR, "validators")
    v.load(validator_path)
    assert v.JmesPathModelValidation.validators


def test_jmespathvalidation_pass(host_vars):
    validate = getattr(v.JmesPathModelValidation.validators[0], "validate")
    validate(host_vars["az_phx_pe01"])
    assert True


def test_jmespathvalidation_fail(host_vars):
    validate = getattr(v.JmesPathModelValidation.validators[0], "validate")
    with pytest.raises(v.ValidationError):
        validate(host_vars["az_phx_pe02"])


def test_modelvalidation_pass(host_vars):
    validate = getattr(v.ModelValidation.validators[0], "validate")
    validate(host_vars)
    assert True
