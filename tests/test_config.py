""" Test Setting Configuration Parameters"""
import os

import pytest
from jsonschema_testing import config
from jsonschema_testing.exceptions import InvalidConfigAttribute

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures", "test_config")


class TestConfig:
    """
    Tests config global object from config.py
    """

    @staticmethod
    def test_default_load():
        """
        Test load of default config
        """
        config.load()

        assert config.SETTINGS.main_directory == "schema"
        assert config.SETTINGS.definition_directory == "definitions"
        assert config.SETTINGS.schema_directory == "schemas"
        assert config.SETTINGS.test_directory == "tests"
        assert config.SETTINGS.schema_file_extensions == [".json", ".yaml", ".yml"]
        assert config.SETTINGS.schema_file_exclude_filenames == []
        assert config.SETTINGS.instance_search_directories == ["./"]
        assert config.SETTINGS.instance_file_extensions == [".json", ".yaml", ".yml"]
        assert config.SETTINGS.instance_file_exclude_filenames == [".yamllint.yml", ".travis.yml"]
        assert config.SETTINGS.ansible_inventory is None
        assert config.SETTINGS.schema_mapping == {}

    @staticmethod
    def test_custom_load():
        """
        Test load from configuration file
        """
        # Load config file using fixture of config file
        config_file_name = FIXTURES_DIR + "/pyproject.toml"
        config.load(config_file_name=config_file_name)

        assert config.SETTINGS.main_directory == "schema1"
        assert config.SETTINGS.definition_directory == "definitions1"
        assert config.SETTINGS.schema_directory == "schemas1"
        assert config.SETTINGS.test_directory == "tests1"
        assert config.SETTINGS.schema_file_extensions == [".json1", ".yaml1", ".yml1"]
        assert config.SETTINGS.schema_file_exclude_filenames == ["happy_file.yml1"]
        assert config.SETTINGS.instance_search_directories == ["./instance_test/"]
        assert config.SETTINGS.instance_file_extensions == [".json1", ".yaml1", ".yml1"]
        assert config.SETTINGS.instance_file_exclude_filenames == [".yamllint.yml1", ".travis.yml1"]
        assert config.SETTINGS.ansible_inventory == "inventory.inv"
        assert "dns.yml" in config.SETTINGS.schema_mapping.keys()
        assert "syslog.yml" in config.SETTINGS.schema_mapping.keys()
        assert ["schemas/dns_servers"] in config.SETTINGS.schema_mapping.values()
        assert ["schemas/syslog_servers"] in config.SETTINGS.schema_mapping.values()

    @staticmethod
    def test_data_load():
        """
        Test load from python data structure
        """
        data = {
            "main_directory": "schema2",
            "definition_directory": "definitions2",
            "schema_directory": "schemas2",
            "test_directory": "tests2",
            "schema_file_extensions": [".json2", ".yaml2", ".yml2"],
            "schema_file_exclude_filenames": ["happy_file.yml2"],
            "instance_search_directories": ["./instance_test2/"],
            "instance_file_extensions": [".json2", ".yaml2", ".yml2"],
            "instance_file_exclude_filenames": [".yamllint.yml2", ".travis.yml2"],
            "ansible_inventory": "inventory.inv2",
            "schema_mapping": {
                "dns.yml2": ["schemas/dns_servers2"],
                "syslog.yml2": ["schemas/syslog_servers2"],
            },  # noqa: E231
        }
        config.load(config_data=data)

        assert config.SETTINGS.main_directory == "schema2"
        assert config.SETTINGS.definition_directory == "definitions2"
        assert config.SETTINGS.schema_directory == "schemas2"
        assert config.SETTINGS.test_directory == "tests2"
        assert config.SETTINGS.schema_file_extensions == [".json2", ".yaml2", ".yml2"]
        assert config.SETTINGS.schema_file_exclude_filenames == ["happy_file.yml2"]
        assert config.SETTINGS.instance_search_directories == ["./instance_test2/"]
        assert config.SETTINGS.instance_file_extensions == [".json2", ".yaml2", ".yml2"]
        assert config.SETTINGS.instance_file_exclude_filenames == [".yamllint.yml2", ".travis.yml2"]
        assert config.SETTINGS.ansible_inventory == "inventory.inv2"
        assert "dns.yml2" in config.SETTINGS.schema_mapping.keys()
        assert "syslog.yml2" in config.SETTINGS.schema_mapping.keys()
        assert ["schemas/dns_servers2"] in config.SETTINGS.schema_mapping.values()
        assert ["schemas/syslog_servers2"] in config.SETTINGS.schema_mapping.values()

    @staticmethod
    def test_mixed_load():
        """
        Test config load when config_file_name, data, and defaults are all used
        """
        config_file_name = FIXTURES_DIR + "/pyproject2.toml"
        data = {"main_directory": "fake_dir"}

        config.load(config_file_name=config_file_name, config_data=data)

        # Assert main_directory inhered from data passed in
        assert config.SETTINGS.main_directory == "fake_dir"

        # Assert definitions_directory inhered from default, and not from file
        assert config.SETTINGS.definition_directory == "definitions"

    @staticmethod
    def test_invalid_file_load():
        """
        Test config load raises proper error when config file contains invalid attributes
        """
        config_file_name = FIXTURES_DIR + "/pyproject_invalid_attr.toml"
        with pytest.raises(InvalidConfigAttribute) as exc:
            config.load(config_file_name=config_file_name)

        assert (
            str(exc.value)
            == "Configuration not valid, found 1 error(s)  happy_variable | extra fields not permitted (value_error.extra)"
        )
