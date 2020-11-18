
## Customizing Project Config

The CLI tool uses a configuration section beginning with `tool.jsonschema_testing` in a `pyproject.toml` file to configure settings. There are examples of the configuration file in `examples/example1/pyproject.toml` and `examples/example2/pyproject.toml` folders, which work with the files inside of the `examples/example1/` and `examples/example2/` directories/subdirectories (respectively).

```shell
bash$ cd examples/example1
bash$ tree -L 2
.
├── hostvars
│   ├── chi-beijing-rt1
│   ├── eng-london-rt1
│   ├── fail-tests
│   ├── ger-berlin-rt1
│   ├── mex-mxc-rt1
│   ├── usa-lax-rt1
│   └── usa-nyc-rt1
├── inventory
│   ├── group_vars
│   ├── host_vars
│   └── inventory
├── pyproject.toml
└── schema
    ├── definitions
    ├── schemas
    └── tests
```

Here is output from the `examples/example1/pyproject.toml` which serves as an example.

```toml
[tool.jsonschema_testing]
schema_file_exclude_filenames = []

definition_directory = "definitions"
schema_directory = "schemas"

instance_file_exclude_filenames = ['.yamllint.yml', '.travis.yml']
# instance_search_directories = ["hostvars/"]

[tool.jsonschema_testing.schema_mapping]
# Map instance filename to schema id which should be used to check the instance data contained in the file
'dns.yml' = ['schemas/dns_servers']
'syslog.yml' = ["schemas/syslog_servers"]
```

> Note: In the root of this project is a pyproject.toml file without a `[tool.jsonschema_testing]` configuration block. This is used for the jsonschema_testing tools package management and not for configuration of the jsonschema_testing tool. If you run the tool from the root of this repository, the tool will fail because there are no `tool.jsonschema_testing` blocks which define how the tool should behave, and the default configuration settings include a directory structure that does not exist starting at the root of the project but rather from the base path of the examples/example1 and/or examples/example2 folder(s).

### Configuration Settings

The following parameters can be specified within the pyproject.toml file used to configure the jsonschema_testing tool. The below text snippet lists the default for each of these configuration parameters. If a pyproject.toml file defines a subset of the available parameters, this susbset defined will override the defaults. Any parameter not defined in the pyproject.toml file will fall back to it's default value (as listed below).

```toml
[tools.jsonschema_testing]

# Main Directory Names
main_directory = "schema"
definition_directory = "definitions"
schema_directory = "schemas"
test_directory = "tests"

# Settings specific to the schema files
schema_file_extensions [".json", ".yaml", ".yml"]
schema_file_exclude_filenames = []

# settings specific to search and identify all instance file to validate
instance_search_directories = ["./"]
instance_file_extensions = [".json", ".yaml", ".yml"]
instance_file_exclude_filenames = [".yamllint.yml", ".travis.yml"]

ansible_inventory = None

# Mapping of schema instance file name to a list of schemas which should be used to validate data in the instance file
[tools.jsonschema_testing.schema_mapping]
```