""" Test Setting Configuration Parameters"""
from re import I
from unittest import mock
import os

import pytest
from schema_enforcer import config

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures", "test_config")


def test_load_default():
    """
    Test load of default config
    """
    config.load()

    assert config.SETTINGS.main_directory == "schema"


def test_load_custom():
    """
    Test load from configuration file
    """
    # Load config file using fixture of config file
    config_file_name = FIXTURES_DIR + "/pyproject.toml"
    config.load(config_file_name=config_file_name)

    assert config.SETTINGS.main_directory == "schema1"


def test_load_data():
    """
    Test load from python data structure
    """
    data = {
        "main_directory": "schema2",
    }
    config.load(config_data=data)

    assert config.SETTINGS.main_directory == "schema2"


def test_load_mixed():
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


def test_load_and_exit_invalid_data():
    """
    Test config load raises proper error when config file contains invalid attributes
    """
    config_file_name = FIXTURES_DIR + "/pyproject_invalid_attr.toml"
    with pytest.raises(SystemExit):
        config.load_and_exit(config_file_name=config_file_name)


def test_load_environment_vars():
    """
    Test load from environment variables
    """

    # WWrite test to mock os.environ to test pydantic BaseSettings
    with mock.patch.dict(
        os.environ, {"jsonschema_directory": "schema_env", "jsonschema_definition_directory": "definitions_env"}
    ):
        config.load()

    assert config.SETTINGS.main_directory == "schema_env"
    assert config.SETTINGS.definition_directory == "definitions_env"
