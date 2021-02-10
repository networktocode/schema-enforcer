"""Tests for validator plugin support."""
# pylint: disable=redefined-outer-name
import os
import pytest
from schema_enforcer.ansible_inventory import AnsibleInventory
import schema_enforcer.schemas.validator as v

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures", "test_validators")


@pytest.fixture
def inventory():
    """Fixture for Ansible inventory used in tests."""
    inventory_dir = os.path.join(FIXTURE_DIR, "inventory")

    inventory = AnsibleInventory(inventory_dir)
    return inventory


@pytest.fixture
def host_vars(inventory):
    """Fixture for providing Ansible host_vars as a consolidated dict."""
    hosts = inventory.get_hosts_containing()
    host_vars = dict()
    for host in hosts:
        hostname = host.get_vars()["inventory_hostname"]
        host_vars[hostname] = inventory.get_host_vars(host)
    return host_vars


@pytest.fixture(scope="session")
def validators():
    """Test that validator files are loaded and appended to base class validator list."""
    validator_path = os.path.join(FIXTURE_DIR, "validators")
    return v.load_validators(validator_path)


def test_jmespathvalidation_pass(host_vars, validators):
    """
    Validator: "interfaces.*[@.type=='core'][] | length([?@])" gte 2
    Test expected to pass for az_phx_pe01 with two core interfaces:
        interfaces:
          GigabitEthernet0/0/0/0:
              type: "core"
          GigabitEthernet0/0/0/1:
              type: "core"
    """
    validate = getattr(validators["CheckInterface"], "validate")
    result = validate(host_vars["az_phx_pe01"], False)
    assert result[0].passed()


def test_jmespathvalidation_fail(host_vars, validators):
    """
    Validator: "interfaces.*[@.type=='core'][] | length([?@])" gte 2
    Test expected to fail for az_phx_pe02 with one core interface:
        interfaces:
          GigabitEthernet0/0/0/0:
              type: "core"
          GigabitEthernet0/0/0/1:
              type: "access"
    """
    validate = getattr(validators["CheckInterface"], "validate")
    result = validate(host_vars["az_phx_pe02"], False)
    assert not result[0].passed()


def test_modelvalidation_pass(host_vars, validators):
    """
    Validator: Checks that peer and peer_int match between peers
    Test expected to pass for az_phx_pe01/az_phx_pe02:

    az_phx_pe01:
      GigabitEthernet0/0/0/0:
       peer: "az-phx-pe02"
       peer_int: "GigabitEthernet0/0/0/0"

    az_phx_pe02:
      GigabitEthernet0/0/0/0:
        peer: "az-phx-pe01"
        peer_int: "GigabitEthernet0/0/0/0"
    """
    validate = getattr(validators["CheckPeers"], "validate")
    result = validate(host_vars, False)
    assert result[0].passed()
    assert result[2].passed()


def test_modelvalidation_fail(host_vars, validators):
    """
    Validator: Checks that peer and peer_int match between peers

    Test expected to fail for az_phx_pe01/co_den_p01:

    az_phx_pe01:
      GigabitEthernet0/0/0/1:
        peer: "co-den-p01"
        peer_int: "GigabitEthernet0/0/0/2"

    co_den_p01:
      GigabitEthernet0/0/0/2:
        peer: ut-slc-pe01
        peer_int: GigabitEthernet0/0/0/2
    """
    validate = getattr(validators["CheckPeers"], "validate")
    result = validate(host_vars, False)
    assert not result[1].passed()
