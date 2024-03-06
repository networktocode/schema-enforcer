# pylint: disable=redefined-outer-name
"""Test manager.py PydanticManager class"""

import os
import sys
from unittest import mock
import pytest
from click.testing import CliRunner
from schema_enforcer.schemas.manager import SchemaManager
from schema_enforcer.config import Settings
from schema_enforcer.instances.file import InstanceFileManager
from schema_enforcer import cli

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")

sys.path.append(f"{FIXTURE_DIR}/test_validators_pydantic/")

CONFIG = {
    "pydantic_validators": [
        "pydantic_validators.models:manager1",
        "pydantic_validators.models:manager2",
    ],
    "data_file_search_directories": [
        f"{FIXTURE_DIR}/test_validators_pydantic/inventory"
    ],
    "ansible_inventory": f"{FIXTURE_DIR}/test_validators_pydantic/inventory/inventory.yml",
}


@pytest.fixture
def schema_manager_pydantic():
    """
    Instantiated SchemaManager class that imported our pydantic_validator models.

    Returns:
        SchemaManager
    """
    return SchemaManager(config=Settings(**CONFIG))


@pytest.fixture
def instance_file_manager():
    """
    Instantiated SchemaManager class that imported our pydantic_validator models.

    Returns:
        SchemaManager
    """
    return InstanceFileManager(config=Settings(**CONFIG))


@pytest.mark.parametrize(
    "schema",
    [
        "Hostname",
        "Interfaces",
        "pydantic/Hostname",
        "pydantic/Interfaces",
        "pydantic/Dns",
    ],
)
def test_pydantic_manager_validate_correct_schemas(schema, schema_manager_pydantic):
    assert (
        schema in schema_manager_pydantic.schemas
    ), f"Schema {schema} not found in {schema_manager_pydantic.schemas}"
    assert len(schema_manager_pydantic.schemas) == 5, "There should be 5 schemas."


@pytest.mark.parametrize(
    "file",
    [
        # az_phx_pe01
        f"{FIXTURE_DIR}/test_validators_pydantic/inventory/host_vars/az_phx_pe01/base.yml",
        f"{FIXTURE_DIR}/test_validators_pydantic/inventory/host_vars/az_phx_pe01/dns.yml",
        # az_phx_pe02
        f"{FIXTURE_DIR}/test_validators_pydantic/inventory/host_vars/az_phx_pe02/base.yml",
        # co_den_p01
        f"{FIXTURE_DIR}/test_validators_pydantic/inventory/host_vars/co_den_p01/base.yml",
        f"{FIXTURE_DIR}/test_validators_pydantic/inventory/host_vars/co_den_p01/dns.yml",
    ],
)
def test_pydantic_manager_validate_correct_files(file, instance_file_manager):
    paths = [f"{f.full_path}/{f.filename}" for f in instance_file_manager.instances]
    assert file in paths, f"File {file} not found in {paths}"
    # 6 includes the `inventory.yml` for now.
    assert (
        len(instance_file_manager.instances) == 6
    ), "There should be 6 variable files found."


@mock.patch("schema_enforcer.config.load")
def test_pydantic_manager_validate_cli(_load):
    runner = CliRunner()
    with mock.patch("schema_enforcer.config.SETTINGS", Settings(**CONFIG)):
        result = runner.invoke(cli.validate)
    _load.assert_called_once()
    assert result.exit_code == 0
    assert "ALL SCHEMA VALIDATION CHECKS PASSED" in result.output


@mock.patch("schema_enforcer.config.load")
def test_pydantic_manager_validate_correct_checks_mapping_cli_success(_load):
    runner = CliRunner()
    with mock.patch("schema_enforcer.config.SETTINGS", Settings(**CONFIG)):
        result = runner.invoke(cli.validate, ["--show-checks"])
    _load.assert_called_once()
    assert result.exit_code == 0
    expected = """Structured Data File                               Schema ID
--------------------------------------------------------------------------------
/local/tests/fixtures/test_validators_pydantic/inventory/host_vars/az_phx_pe01/base.yml ['Hostname', 'Interfaces', 'pydantic/Hostname', 'pydantic/Interfaces']
/local/tests/fixtures/test_validators_pydantic/inventory/host_vars/az_phx_pe01/dns.yml ['pydantic/Dns']
/local/tests/fixtures/test_validators_pydantic/inventory/host_vars/az_phx_pe02/base.yml ['Hostname', 'Interfaces', 'pydantic/Hostname', 'pydantic/Interfaces']
/local/tests/fixtures/test_validators_pydantic/inventory/host_vars/co_den_p01/base.yml ['Hostname', 'Interfaces', 'pydantic/Hostname', 'pydantic/Interfaces']
/local/tests/fixtures/test_validators_pydantic/inventory/host_vars/co_den_p01/dns.yml ['pydantic/Dns']
/local/tests/fixtures/test_validators_pydantic/inventory/inventory.yml []
"""
    assert expected == result.output


@mock.patch("schema_enforcer.config.load")
def test_pydantic_manager_validate_show_pass_cli(_load):
    runner = CliRunner()
    with mock.patch("schema_enforcer.config.SETTINGS", Settings(**CONFIG)):
        result = runner.invoke(cli.validate, ["--show-pass"])
    _load.assert_called_once()
    assert result.exit_code == 0
    assert (
        "\x1b[32mPASS\x1b[0m | [FILE] /local/tests/fixtures/test_validators_pydantic/inventory/host_vars/az_phx_pe01/base.yml"
        in result.output
    )
    assert (
        "\x1b[32mPASS\x1b[0m | [FILE] /local/tests/fixtures/test_validators_pydantic/inventory/host_vars/az_phx_pe01/base.yml"
        in result.output
    )
    assert (
        "\x1b[32mPASS\x1b[0m | [FILE] /local/tests/fixtures/test_validators_pydantic/inventory/host_vars/az_phx_pe01/base.yml"
        in result.output
    )
    assert (
        "\x1b[32mPASS\x1b[0m | [FILE] /local/tests/fixtures/test_validators_pydantic/inventory/host_vars/az_phx_pe01/base.yml"
        in result.output
    )
    assert (
        "\x1b[32mPASS\x1b[0m | [FILE] /local/tests/fixtures/test_validators_pydantic/inventory/host_vars/az_phx_pe01/dns.yml"
        in result.output
    )
    assert (
        "\x1b[32mPASS\x1b[0m | [FILE] /local/tests/fixtures/test_validators_pydantic/inventory/host_vars/co_den_p01/base.yml"
        in result.output
    )
    assert (
        "\x1b[32mPASS\x1b[0m | [FILE] /local/tests/fixtures/test_validators_pydantic/inventory/host_vars/co_den_p01/base.yml"
        in result.output
    )
    assert (
        "\x1b[32mPASS\x1b[0m | [FILE] /local/tests/fixtures/test_validators_pydantic/inventory/host_vars/co_den_p01/base.yml"
        in result.output
    )
    assert (
        "\x1b[32mPASS\x1b[0m | [FILE] /local/tests/fixtures/test_validators_pydantic/inventory/host_vars/co_den_p01/base.yml"
        in result.output
    )
    assert (
        "\x1b[32mPASS\x1b[0m | [FILE] /local/tests/fixtures/test_validators_pydantic/inventory/host_vars/co_den_p01/dns.yml"
        in result.output
    )
    assert (
        "\x1b[32mPASS\x1b[0m | [FILE] /local/tests/fixtures/test_validators_pydantic/inventory/host_vars/az_phx_pe02/base.yml"
        in result.output
    )
    assert (
        "\x1b[32mPASS\x1b[0m | [FILE] /local/tests/fixtures/test_validators_pydantic/inventory/host_vars/az_phx_pe02/base.yml"
        in result.output
    )
    assert (
        "\x1b[32mPASS\x1b[0m | [FILE] /local/tests/fixtures/test_validators_pydantic/inventory/host_vars/az_phx_pe02/base.yml"
        in result.output
    )
    assert (
        "\x1b[32mPASS\x1b[0m | [FILE] /local/tests/fixtures/test_validators_pydantic/inventory/host_vars/az_phx_pe02/base.yml"
        in result.output
    )
    assert "\x1b[32mALL SCHEMA VALIDATION CHECKS PASSED\x1b[0m" in result.output


@mock.patch("schema_enforcer.config.load")
def test_pydantic_manager_ansible_cli(_load):
    runner = CliRunner()
    with mock.patch("schema_enforcer.config.SETTINGS", Settings(**CONFIG)):
        result = runner.invoke(cli.ansible)
    _load.assert_called_once()
    assert result.exit_code == 0
    expected = """Found 3 hosts in the inventory
\x1b[32mALL SCHEMA VALIDATION CHECKS PASSED\x1b[0m
"""
    assert expected == result.output


@mock.patch("schema_enforcer.config.load")
def test_pydantic_manager_ansible_show_pass_cli(_load):
    runner = CliRunner()
    with mock.patch("schema_enforcer.config.SETTINGS", Settings(**CONFIG)):
        result = runner.invoke(cli.ansible, ["--show-pass"])
    _load.assert_called_once()
    assert result.exit_code == 0
    expected = """Found 3 hosts in the inventory
\x1b[32mPASS\x1b[0m | [HOST] az_phx_pe01 [SCHEMA ID] Hostname
\x1b[32mPASS\x1b[0m | [HOST] az_phx_pe01 [SCHEMA ID] pydantic/Hostname
\x1b[32mPASS\x1b[0m | [HOST] az_phx_pe01 [SCHEMA ID] Interfaces
\x1b[32mPASS\x1b[0m | [HOST] az_phx_pe01 [SCHEMA ID] pydantic/Interfaces
\x1b[32mPASS\x1b[0m | [HOST] az_phx_pe01 [SCHEMA ID] pydantic/Dns
\x1b[32mPASS\x1b[0m | [HOST] az_phx_pe02 [SCHEMA ID] Hostname
\x1b[32mPASS\x1b[0m | [HOST] az_phx_pe02 [SCHEMA ID] pydantic/Hostname
\x1b[32mPASS\x1b[0m | [HOST] az_phx_pe02 [SCHEMA ID] Interfaces
\x1b[32mPASS\x1b[0m | [HOST] az_phx_pe02 [SCHEMA ID] pydantic/Interfaces
\x1b[32mPASS\x1b[0m | [HOST] co_den_p01 [SCHEMA ID] Hostname
\x1b[32mPASS\x1b[0m | [HOST] co_den_p01 [SCHEMA ID] pydantic/Hostname
\x1b[32mPASS\x1b[0m | [HOST] co_den_p01 [SCHEMA ID] Interfaces
\x1b[32mPASS\x1b[0m | [HOST] co_den_p01 [SCHEMA ID] pydantic/Interfaces
\x1b[32mPASS\x1b[0m | [HOST] co_den_p01 [SCHEMA ID] pydantic/Dns
\x1b[32mALL SCHEMA VALIDATION CHECKS PASSED\x1b[0m
"""
    assert expected == result.output


@mock.patch("schema_enforcer.config.load")
def test_pydantic_manager_ansible_show_checks_cli(_load):
    runner = CliRunner()
    with mock.patch("schema_enforcer.config.SETTINGS", Settings(**CONFIG)):
        result = runner.invoke(cli.ansible, ["--show-checks"])
    _load.assert_called_once()
    assert result.exit_code == 0
    expected = """Found 3 hosts in the inventory
Ansible Host              Schema ID
--------------------------------------------------------------------------------
az_phx_pe01               ['Hostname', 'pydantic/Hostname', 'Interfaces', 'pydantic/Interfaces', 'pydantic/Dns']
az_phx_pe02               ['Hostname', 'pydantic/Hostname', 'Interfaces', 'pydantic/Interfaces']
co_den_p01                ['Hostname', 'pydantic/Hostname', 'Interfaces', 'pydantic/Interfaces', 'pydantic/Dns']
"""
    assert expected == result.output


FAIL_CONFIG = {
    "pydantic_validators": [
        "pydantic_validators.models:manager1",
    ],
    "data_file_search_directories": [
        f"{FIXTURE_DIR}/test_validators_pydantic/inventory_fail"
    ],
    "ansible_inventory": f"{FIXTURE_DIR}/test_validators_pydantic/inventory_fail/inventory.yml",
}


@mock.patch("schema_enforcer.config.load")
def test_pydantic_manager_ansible_cli_failure(_load):
    runner = CliRunner()
    with mock.patch("schema_enforcer.config.SETTINGS", Settings(**FAIL_CONFIG)):
        result = runner.invoke(cli.ansible)
    _load.assert_called_once()
    assert result.exit_code == 1
    expected = """Found 3 hosts in the inventory
\x1b[31mFAIL\x1b[0m | [HOST] az_phx_pe01 [SCHEMA ID] Interfaces
      | [ERROR] 1 validation error for Interfaces
interfaces.GigabitEthernet0/0/0/2.ipv4
  Input is not a valid IPv4 address [type=ip_v4_address, input_value='300.123.178.41', input_type=AnsibleUnicode]
\x1b[31mFAIL\x1b[0m | [HOST] az_phx_pe02 [SCHEMA ID] Hostname
      | [ERROR] 1 validation error for Hostname
hostname
  String should match pattern '^[a-z]{2}-[a-z]{3}-[a-z]{1,2}[0-9]{2}$' [type=string_pattern_mismatch, input_value='az-phoenix-pe02', input_type=AnsibleUnicode]
    For further information visit https://errors.pydantic.dev/2.6/v/string_pattern_mismatch
\x1b[31mFAIL\x1b[0m | [HOST] co_den_p01 [SCHEMA ID] Hostname
      | [ERROR] 1 validation error for Hostname
hostname
  String should match pattern '^[a-z]{2}-[a-z]{3}-[a-z]{1,2}[0-9]{2}$' [type=string_pattern_mismatch, input_value='co-denver-p01', input_type=AnsibleUnicode]
    For further information visit https://errors.pydantic.dev/2.6/v/string_pattern_mismatch
\x1b[31mFAIL\x1b[0m | [HOST] co_den_p01 [SCHEMA ID] Interfaces
      | [ERROR] 1 validation error for Interfaces
interfaces.GigabitEthernet0/0/0/4.ipv6
  Input is not a valid IPv6 address [type=ip_v6_address, input_value='2001:db8:16::yo', input_type=AnsibleUnicode]
"""
    assert expected == result.output, result.output


@mock.patch("schema_enforcer.config.load")
def test_pydantic_manager_ansible_show_pass_cli_failure(_load):
    runner = CliRunner()
    with mock.patch("schema_enforcer.config.SETTINGS", Settings(**FAIL_CONFIG)):
        result = runner.invoke(cli.ansible, ["--show-pass"])
    _load.assert_called_once()
    assert result.exit_code == 1
    expected = """Found 3 hosts in the inventory
\x1b[32mPASS\x1b[0m | [HOST] az_phx_pe01 [SCHEMA ID] Hostname
\x1b[31mFAIL\x1b[0m | [HOST] az_phx_pe01 [SCHEMA ID] Interfaces
      | [ERROR] 1 validation error for Interfaces
interfaces.GigabitEthernet0/0/0/2.ipv4
  Input is not a valid IPv4 address [type=ip_v4_address, input_value='300.123.178.41', input_type=AnsibleUnicode]
\x1b[31mFAIL\x1b[0m | [HOST] az_phx_pe02 [SCHEMA ID] Hostname
      | [ERROR] 1 validation error for Hostname
hostname
  String should match pattern '^[a-z]{2}-[a-z]{3}-[a-z]{1,2}[0-9]{2}$' [type=string_pattern_mismatch, input_value='az-phoenix-pe02', input_type=AnsibleUnicode]
    For further information visit https://errors.pydantic.dev/2.6/v/string_pattern_mismatch
\x1b[32mPASS\x1b[0m | [HOST] az_phx_pe02 [SCHEMA ID] Interfaces
\x1b[31mFAIL\x1b[0m | [HOST] co_den_p01 [SCHEMA ID] Hostname
      | [ERROR] 1 validation error for Hostname
hostname
  String should match pattern '^[a-z]{2}-[a-z]{3}-[a-z]{1,2}[0-9]{2}$' [type=string_pattern_mismatch, input_value='co-denver-p01', input_type=AnsibleUnicode]
    For further information visit https://errors.pydantic.dev/2.6/v/string_pattern_mismatch
\x1b[31mFAIL\x1b[0m | [HOST] co_den_p01 [SCHEMA ID] Interfaces
      | [ERROR] 1 validation error for Interfaces
interfaces.GigabitEthernet0/0/0/4.ipv6
  Input is not a valid IPv6 address [type=ip_v6_address, input_value='2001:db8:16::yo', input_type=AnsibleUnicode]
"""
    assert expected == result.output, result.output
