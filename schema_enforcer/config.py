"""Tests config Settings class."""
import os
import os.path
import sys
from pathlib import Path
from typing import Dict, List, Optional
from typing_extensions import Annotated

import toml
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

SETTINGS = None


class Settings(BaseSettings):  # pylint: disable=too-few-public-methods
    """Main Settings Class for the project.

    The type of each setting is defined using Python annotations
    and is validated when a config file is loaded with Pydantic.

    Most input files specific to this project are expected to be located in the same directory. e.g.
    schema/
     - definitions
     - schemas
    """

    model_config = SettingsConfigDict(populate_by_name=True, env_prefix="jsonschema_")

    # Main directory names
    main_directory: str = Field("schema", alias="jsonschema_directory")
    definition_directory: str = "definitions"
    schema_directory: str = "schemas"
    validator_directory: str = "validators"
    pydantic_validators: Optional[List[Annotated[str, Field(pattern="^.*:.*$")]]] = Field(default_factory=list)
    test_directory: str = "tests"

    # Settings specific to the schema files
    schema_file_extensions: List[str] = [
        ".json",
        ".yaml",
        ".yml",
    ]  # Do we still need that ?
    schema_file_exclude_filenames: List[str] = []

    # settings specific to search and identify all instance file to validate
    data_file_search_directories: List[str] = ["./"]
    data_file_extensions: List[str] = [".json", ".yaml", ".yml"]
    data_file_exclude_filenames: List[str] = [".yamllint.yml", ".travis.yml"]
    data_file_automap: bool = True

    ansible_inventory: Optional[str] = None
    schema_mapping: Dict = {}


def load(config_file_name="pyproject.toml", config_data=None):
    """Load configuration.

    Configuration is loaded from a file in pyproject.toml format that contains the settings,
    or from a dictionary of those settings passed in as "config_data"

    The settings for this app are expected to be in [tool.json_schema_testing] in TOML
    if nothing is found in the config file or if the config file do not exist, the default values will be used.

    config_data can be passed in to override the config_file_name. If this is done, a combination of the data
    specified and the defaults for parameters not specified will be used, and settings in the config file will
    be ignored.

    Args:
        config_file_name (str, optional): Name of the configuration file to load. Defaults to "pyproject.toml".
        config_data (dict, optional): dict to load as the config file instead of reading the file. Defaults to None.
    """
    global SETTINGS  # pylint: disable=global-statement

    if config_data:
        SETTINGS = Settings(**config_data)
        return
    if os.path.exists(config_file_name):
        config_string = Path(config_file_name).read_text(encoding="utf-8")
        config_tmp = toml.loads(config_string)

        if "tool" in config_tmp and "schema_enforcer" in config_tmp.get("tool", {}):
            SETTINGS = Settings(**config_tmp["tool"]["schema_enforcer"])
            return

    SETTINGS = Settings()


def load_and_exit(config_file_name="pyproject.toml", config_data=None):
    """Calls load, but wraps it in a try except block.

    This is done to handle a ValidationErorr which is raised when settings are specified but invalid.
    In such cases, a message is printed to the screen indicating the settings which don't pass validation.

    Args:
        config_file_name (str, optional): [description]. Defaults to "pyproject.toml".
        config_data (dict, optional): [description]. Defaults to None.
    """
    try:
        load(config_file_name=config_file_name, config_data=config_data)
    except ValidationError as err:
        print(f"Configuration not valid, found {len(err.errors())} error(s)")
        for error in err.errors():
            print(f"  {'/'.join(error['loc'])} | {error['msg']} ({error['type']})")
        sys.exit(1)
