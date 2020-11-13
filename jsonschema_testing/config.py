"""settings definition for the config file."""
import sys
import os
import os.path
from pathlib import Path
from typing import Dict, List, Optional

import toml
from pydantic import BaseSettings, ValidationError

SETTINGS = None


class Settings(BaseSettings):  # pylint: disable=too-few-public-methods
    """Main Settings Class for the project.

    The type of each setting is defined using Python annotations
    and is validated when a config file is loaded with Pydantic.

    Most input files specific to this project are expected to be located in the same directory
    schema/
     - definitions
     - schemas
    """

    # Main directory names
    main_directory: str = "schema"
    definition_directory: str = "definitions"
    schema_directory: str = "schemas"
    test_directory: str = "tests"

    # Settings specific to the schema files
    schema_file_extensions: List[str] = [".json", ".yaml", ".yml"]  # Do we still need that ?
    schema_file_exclude_filenames: List[str] = []

    # settings specific to search and identify all instance file to validate
    instance_search_directories: List[str] = ["./"]
    instance_file_extensions: List[str] = [".json", ".yaml", ".yml"]
    instance_file_exclude_filenames: List[str] = [".yamllint.yml", ".travis.yml"]

    ansible_inventory: Optional[str]
    schema_mapping: Dict = dict()

    class Config:  # pylint: disable=too-few-public-methods
        """Additional parameters to automatically map environment variable to some settings."""

        fields = {
            "main_directory": {"env": "jsonschema_directory"},
            "definition_directory": {"env": "jsonschema_definition_directory"},
        }


def load(config_file_name="pyproject.toml", config_data=None):
    """Load a configuration file in pyproject.toml format that contains the settings.

    The settings for this app are expected to be in [tool.json_schema_testing] in TOML
    if nothing is found in the config file or if the config file do not exist, the default values will be used.

    Args:
        config_file_name (str, optional): Name of the configuration file to load. Defaults to "pyproject.toml".
        config_data (dict, optional): dict to load as the config file instead of reading the file. Defaults to None.
    """
    global SETTINGS  # pylint: disable=global-statement

    if config_data:
        SETTINGS = Settings(**config_data)
        return
    if os.path.exists(config_file_name):
        config_string = Path(config_file_name).read_text()
        config_tmp = toml.loads(config_string)

        if "tool" in config_tmp and "jsonschema_testing" in config_tmp.get("tool", {}):
            try:
                SETTINGS = Settings(**config_tmp["tool"]["jsonschema_testing"])
            except ValidationError as exc:
                print(f"Configuration not valid, found {len(exc.errors())} error(s)")
                for error in exc.errors():
                    print(f"  {'/'.join(error['loc'])} | {error['msg']} ({error['type']})")
                sys.exit(1)
            return

    SETTINGS = Settings()
