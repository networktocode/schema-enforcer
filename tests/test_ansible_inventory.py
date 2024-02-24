# pylint: disable=redefined-outer-name
"""Unit Tests for ansible_inventory.py"""

import pytest

from schema_enforcer.ansible_inventory import AnsibleInventory


INVENTORY_DIR = "tests/mocks/inventory"


@pytest.fixture(scope="module")
def ansible_inv():  # pylint: disable=unused-argument
    """Ansible inventory fixture."""
    return AnsibleInventory(INVENTORY_DIR)


def test_init_hosts(ansible_inv):
    """Test initialization of hosts."""
    expected = {"host3", "host4"}
    actual = set(ansible_inv.inv_mgr.hosts)
    assert actual == expected


def test_init_groups(ansible_inv):
    """Test initialization of groups."""
    expected = {
        "ios": ["host3"],
        "eos": ["host4"],
        "na": ["host3"],
        "emea": ["host4"],
        "nyc": ["host3"],
        "lon": ["host4"],
    }
    ansible_vars = ansible_inv.var_mgr.get_vars()
    actual = ansible_vars["groups"]
    actual.pop("all")
    actual.pop("ungrouped")
    assert actual == expected


def test_get_hosts_containing_no_var(ansible_inv):
    expected = ["host3", "host4"]
    all_hosts = ansible_inv.get_hosts_containing()
    actual = [host.name for host in all_hosts]
    assert actual == expected, str(dir(actual[0]))


def test_get_hosts_containing_var(ansible_inv):
    expected = ["host3"]
    filtered_hosts = ansible_inv.get_hosts_containing(var="os_dns")
    actual = [host.name for host in filtered_hosts]
    assert actual == expected


def test_get_host_vars(ansible_inv):
    expected = {
        "dns_servers": [{"address": "10.7.7.7", "vrf": "mgmt"}, {"address": "10.8.8.8"}],
        "group_names": ["ios", "na", "nyc"],
        "inventory_hostname": "host3",
        "ntp_servers": [{"address": "10.3.3.3"}],
        "os_dns": [{"address": "10.7.7.7", "vrf": "mgmt"}, {"address": "10.8.8.8"}],
        "region_dns": [{"address": "10.1.1.1", "vrf": "mgmt"}, {"address": "10.2.2.2"}],
    }

    filtered_hosts = ansible_inv.get_hosts_containing(var="os_dns")
    host3 = [host for host in filtered_hosts if host.name == "host3"][0]
    host3_vars = ansible_inv.get_host_vars(host3)
    interesting_keys = [
        "dns_servers",
        "group_names",
        "inventory_hostname",
        "ntp_servers",
        "os_dns",
        "region_dns",
    ]
    actual = {key: host3_vars[key] for key in interesting_keys}
    assert actual == expected


def test_get_clean_host_vars(ansible_inv):
    expected = {
        "dns_servers": [{"address": "10.7.7.7", "vrf": "mgmt"}, {"address": "10.8.8.8"}],
        "os_dns": [{"address": "10.7.7.7", "vrf": "mgmt"}, {"address": "10.8.8.8"}],
        "region_dns": [{"address": "10.1.1.1", "vrf": "mgmt"}, {"address": "10.2.2.2"}],
        "ntp_servers": [{"address": "10.3.3.3"}],
    }
    host3 = ansible_inv.inv_mgr.get_host("host3")
    host3_cleaned_vars = ansible_inv.get_clean_host_vars(host3)
    assert expected == host3_cleaned_vars

    # Test setting magic_vars_to_evaluate
    host3.set_variable("magic_vars_to_evaluate", ["inventory_hostname"])
    expected["inventory_hostname"] = host3.name
    host3_cleaned_vars = ansible_inv.get_clean_host_vars(host3)
    assert expected == host3_cleaned_vars

    # Test invalid magic_vars_to_evaluate setting
    host3.set_variable("magic_vars_to_evaluate", "inventory_hostname")
    with pytest.raises(TypeError):
        host3_cleaned_vars = ansible_inv.get_clean_host_vars(host3)
