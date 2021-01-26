# Configuration

Various settings can be configured in [TOML format](https://toml.io/en/) by use of a pyproject.toml file in the folder from which the tool is run. A set of intuitive default configuration values exist. If a pyproject.toml file is defined, it will override the defaults for settings it declares, and leave the defaults in place for settings it does not declare.

## Customizing Project Config

The CLI tool uses a configuration section beginning with `tool.schema_enforcer` in a `pyproject.toml` file to configure settings. There are examples of the configuration file in `examples/example2/pyproject.toml` and `examples/example3/pyproject.toml` folders, which work with the files inside of the `examples/example2/` and `examples/example3/` directories/subdirectories (respectively).

### Default Configuration Settings

The following parameters can be specified within the pyproject.toml file used to configure the `schema enforcer` tool. The below text snippet lists the default for each of these configuration parameters. If a pyproject.toml file defines a subset of the available parameters, this susbset defined will override the defaults. Any parameter not defined in the pyproject.toml file will fall back to it's default value (as listed below).

```toml
[tools.schema_enforcer]

# Main Directory Names
main_directory = "schema"
definition_directory = "definitions"
schema_directory = "schemas"
test_directory = "tests"

# Settings specific to the schema files
schema_file_exclude_filenames = []

# settings specific to search and identify all instance file to validate
data_file_search_directories = ["./"]
data_file_extensions = [".json", ".yaml", ".yml"]
data_file_exclude_filenames = [".yamllint.yml", ".travis.yml"]

ansible_inventory = None

[tools.schema_enforcer.schema_mapping]
```

### Overriding the Default Configuration

The table below enumerates each individual setting, it's expected type, it's default, and a description.

| Configuration Setting | Type | Default | description |
|---|---|---|---|
| main_directory | string | "schema" | The directory in which to start searching for schema and definition files |
| definition_directory | string | "definitions" | The directory in which to search for schema definition references. These definitions are can be referenced by the schema files in the "schema_directory". This directory should be nested in the "main_directory" |
| schema_directory | string | "schemas" | The directory in which to search for schemas. This directory should be nested in the "main_directory" |
| test_directory | string | "tests" | The directory in which to search for valid and invalid unit tests for schemas |
| schema_file_extensions | list | [".json", ".yaml", ".yml"] | The extensions to use when searching for schema definition files |
| schema_file_exclude_filenames | list | [] | The list of filenames to exclude when searching for schema files in the `schema_directory` directory |
| data_file_search_directories | list | ["./"] The paths at which to start searching for files with structured data in them to validate against defined schemas. This path is relative to the directory in which `schema-enforcer` is executed.
| data_file_extensions | list | [".json", ".yaml", ".yml"] | The extensions to use when searching for structured data files |
| data_file_exclude_filenames | list | [".yamllint.yml", ".travis.yml"] | The list of filenames to exclude when searching for structured data files |
| ansible_inventory | str | None | The ansible inventory file to use when building an inventory of hosts against which to check for schema adherence |
| schema_mapping | dict | {} | A mapping of structured data file names (keys) to lists of schema IDs (values) against which the data file should be checked for adherence |