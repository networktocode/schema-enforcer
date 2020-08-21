import os
import os.path
import toml
from pathlib import Path
from typing import Set, Dict, List, Optional

from pydantic import (
    BaseModel,
    BaseSettings,
    ValidationError
)

SETTINGS = None

class Settings(BaseSettings):

    main_directory: str = "schema"
    definition_directory: str = "definitions"
    schema_directory: str = "schemas"

    instance_file_extensions: List[str] = [".json", ".yaml", ".yml"]
    instance_exclude_filenames: List[str] = [".yamllint.yml", ".travis.yml"]
    instance_search_directories: List[str] = ["./"]

    schema_file_extensions: List[str] = [".json", ".yaml", ".yml"]  # Do we still need that ?
    schema_file_exclude_filenames: List[str] = []

    schema_mapping: Dict = dict()

    class Config:
        # env_prefix = 'my_prefix_'  # defaults to no prefix, i.e. ""
        fields = {
            "main_directory": {"env": "jsonschema_directory"},
            "definition_directory": {"env": "jsonschema_definition_directory"},
        }


def load(config_file_name="pyproject.toml", config_data=None):
    """
    
    Args:
        config_file_name (str, optional): Name of the configuration file to load. Defaults to "pyproject.toml".
        config_data (dict, optional): dict to load as the config file instead of reading the file. Defaults to None.
    """
    global SETTINGS

    if config_data:
        SETTINGS = Settings(**config_data)
        return 
    if os.path.exists(config_file_name):
        config_string = Path(config_file_name).read_text()
        config_tmp = toml.loads(config_string)

        if "tool" in config_tmp and "jsonschema_testing" in config_tmp.get("tool", {}):
            try:
                SETTINGS = Settings(**config_tmp["tool"]["jsonschema_testing"])
            except ValidationError as e:
                print(f"Configuration not valid, found {len(e.errors())} error(s)")
                for error in e.errors():
                    print(f"  {'/'.join(error['loc'])} | {error['msg']} ({error['type']})")
                exit(0)
            return

    SETTINGS = Settings()

# CONFIG_DEFAULTS = {
# 
# "schema_search_directories": ["schema/schemas/"],
# "schema_file_extensions": [".json", ".yml"],
# "instance_exclude_filenames": [".yamllint.yml", ".travis.yml"],
# "instance_search_directories": ["hostvars/"],
# "instance_file_extensions": [".json", ".yml"],
# "yaml_schema_path": "schema/yaml/schemas/",   REMOVED
# "json_schema_path": "schema/json/schemas/",   REMOVED
# Define location to place schema definitions after resolving ``$ref``
# "json_schema_definitions": "schema/json/definitions", REPLACED with schema_definitions_directory
# "yaml_schema_definitions": "schema/yaml/definitions", REPLACE with schema_definitions_directory
# "json_full_schema_definitions": "schema/json/full_schemas", REMOVED
# Define network device variables location
# "device_variables": "hostvars/",    REMOVED
# Define path to inventory
# "inventory_path": "inventory/",     REMOVED
# "schema_mapping": {},               DONE
# }
