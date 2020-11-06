# JSON Schema Testing

This repository provides a framework for building and testing [JSONSchema](https://json-schema.org/understanding-json-schema/index.html) definitions.
[JSONRef](http://jsonref.readthedocs.org/) is used to resolve JSON references within Schema definitions.

## Install

Poetry, a tool used for python package, venv, and python environment management, is used to manage the jsonschema_testing library in this repo. In the root of the repository, a pyproject.toml file exists from which jsonschema_testing can be installed. To do so, first download and install python/python poetry ([instructuions here](https://python-poetry.org/docs/#installation)), then run the following commands from the root of this repository:

```cli
poetry install
poetry shell
```

Once the jsonschema_testing tool has been installed, the `test-schema` command can be used to validate anisble hostvars for adherence to schema, manage schemas, and run schema validations of YAML/JSON instance files against defined schema.

```cli
Usage: test-schema [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  ansible        Validate the hostvar for all hosts within an Ansible...
  schema         Manage your schemas
  validate       Validates instance files against defined schema
```

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

## Using the tool

Once the tool has been installed and configuration settings have been defined (or not if you're using the defaults), you are ready to get started using the tool! Three main commands can be used to execute the tool, `ansible`, `schema`, and `validate`. In addition to these commands, the `--help` flag can be passed in to show a list of available commands/arguments and a description of their purpose

```cli
bash$ test-schema --help
Usage: test-schema [OPTIONS] COMMAND [ARGS]...

  Container for grouping other click commands.

Options:
  --help  Show this message and exit.

Commands:
  ansible   Validate the hostvar for all hosts within an Ansible inventory.
  schema    Manage your schemas.
  validate  Validates instance files against defined schema.
```

The `--help` flag can be passed in after commands are specified to display arguments available to the commands. e.g.

```cli
test-schema validate --help                                
Usage: test-schema validate [OPTIONS]

  Validates instance files against defined schema.

Options:
  --show-checks  Shows the schemas to be checked for each instance file
                 [default: False]

  --strict       Forces a stricter schema check that warns about unexpected
                 additional properties  [default: False]

  --show-pass    Shows validation checks that passed  [default: False]
  --help         Show this message and exit.
```

### The `validate` command

The `validate` command is used to check instace files for adherence to json schema definitions. Inside of examples/example1 exists a basic hierarchy of directories. With no flags passed in, this tool will display a line per each property definition that **FAILs** schema validation, along with contextual information regarding the error message (e.g. why the property failed validation), the file in which the property failing validation is defined, and the property that is failing validation. If all checks pass, it will inform the tool user that all tests have passed.

In addition to printing these messages, the tool *intentionally exits with an error code of 1*. This is done so that the tool can be used in a pipeline or a script and fail the pipeline/script so that further execution is not performed if schema validations do not pass. If some tool is consuming YAML data, for instance, you would want to make sure that YAML data is schema valid before passing it into the tool to ensure downstream failures because data does not adhere to schema do not occur.

If multiple schema validation errors occur in the same file, both errors will be printed to stdout on their own line. This was done in the spirit of a tool like pylint, which informs you of all errors for a given file so that you can correct them before re-running the tool.

```cli
bash$ cd examples/example1 && test-schema validate
FAIL | [ERROR] 123 is not of type 'string' [FILE] ./hostvars/fail-tests/ntp.yml [PROPERTY] ntp_servers:1:vrf
FAIL | [ERROR] Additional properties are not allowed ('test_extra_property' was unexpected) [FILE] ./hostvars/fail-tests/ntp.yml [PROPERTY]
```

The default behaviour of the `validate` command can be modified by passing in one of a few flags.

#### The `--show-checks` flag

The `--show-checks` flag is used to show which instance files will be validated against which schema validations.

```cli
bash$ cd examples/example1 && test-schema validate --show-checks
Instance File                                     Schema
--------------------------------------------------------------------------------
./hostvars/chi-beijing-rt1/dns.yml                 ['schemas/dns_servers']
./hostvars/chi-beijing-rt1/syslog.yml              ['schemas/syslog_servers']
./hostvars/eng-london-rt1/dns.yml                  ['schemas/dns_servers']
./hostvars/eng-london-rt1/ntp.yml                  ['schemas/ntp']
./hostvars/fail-tests/dns.yml                      ['schemas/dns_servers']
./hostvars/fail-tests/ntp.yml                      ['schemas/ntp']
./hostvars/ger-berlin-rt1/dns.yml                  ['schemas/dns_servers']
./hostvars/mex-mxc-rt1/dns.yml                     ['schemas/dns_servers']
./hostvars/mex-mxc-rt1/syslog.yml                  ['schemas/syslog_servers']
./hostvars/usa-lax-rt1/dns.yml                     ['schemas/dns_servers']
./hostvars/usa-lax-rt1/syslog.yml                  ['schemas/syslog_servers']
./hostvars/usa-nyc-rt1/dns.yml                     ['schemas/dns_servers']
./hostvars/usa-nyc-rt1/syslog.yml                  ['schemas/syslog_servers']
./inventory/group_vars/all.yml                     []
./inventory/group_vars/apac.yml                    []
./inventory/group_vars/emea.yml                    []
./inventory/group_vars/lax.yml                     []
./inventory/group_vars/na.yml                      []
./inventory/group_vars/nyc.yml                     []
```

> The instance file can be mapped to schema definitions in one of a few ways. By default the top level property in an instance file is mapped to the top level property in a schema definition. File names can also be mapped to schema definitions by using a `[tool.jsonschema_testing.schema_mapping]` configuration block in a pyproject.toml file, or a decorator at the type of a file in the form of `# jsonschema_testing: <schema_id>` can be used. See the [README.md in examples/example2](https://github.com/networktocode-llc/jsonschema_testing/tree/master/examplesexamples/example2) for more information on the configuration options that are available as well as detailed examples.

#### The `--show-pass` flag

By default, only files which fail schema validation are printed to stdout. If you would like to see files which pass schema validation as well as those that fail, you can pass in the `--show-pass` flag.

```cli
bash$ cd examples/example1 && test-schema validate --show-pass                           
PASS [FILE] ./hostvars/eng-london-rt1/ntp.yml
PASS [FILE] ./hostvars/eng-london-rt1/dns.yml
PASS [FILE] ./hostvars/chi-beijing-rt1/syslog.yml
PASS [FILE] ./hostvars/chi-beijing-rt1/dns.yml
PASS [FILE] ./hostvars/usa-lax-rt1/syslog.yml
PASS [FILE] ./hostvars/usa-lax-rt1/dns.yml
PASS [FILE] ./hostvars/ger-berlin-rt1/dns.yml
PASS [FILE] ./hostvars/usa-nyc-rt1/syslog.yml
PASS [FILE] ./hostvars/usa-nyc-rt1/dns.yml
PASS [FILE] ./hostvars/mex-mxc-rt1/syslog.yml
PASS [FILE] ./hostvars/mex-mxc-rt1/dns.yml
FAIL | [ERROR] 123 is not of type 'string' [FILE] ./hostvars/fail-tests/ntp.yml [PROPERTY] ntp_servers:1:vrf
FAIL | [ERROR] Additional properties are not allowed ('test_extra_property' was unexpected) [FILE] ./hostvars/fail-tests/ntp.yml [PROPERTY] 
PASS [FILE] ./hostvars/fail-tests/dns.yml
```

#### The `--strict` flag

By default, schema validations are done in a "non-strict" manner. In effect, this means that extra properties are allowed at every level of a schema definition unless the `additionalProperties` key is explicitly set to false for the JSONSchema property. Running the validate command with the `--strict` flag ensures that, if not explicitly set to allowed, additionalProperties are disallowed and instance files with additional properties will fail schema validation.

```cli
bash$ cd examples/example1 && test-schema validate --strict   
FAIL | [ERROR] 123 is not of type 'string' [FILE] ./hostvars/fail-tests/ntp.yml [PROPERTY] ntp_servers:1:vrf
FAIL | [ERROR] Additional properties are not allowed ('test_extra_item_property' was unexpected) [FILE] ./hostvars/fail-tests/ntp.yml [PROPERTY] ntp_servers:1
FAIL | [ERROR] Additional properties are not allowed ('test_extra_property' was unexpected) [FILE] ./hostvars/fail-tests/ntp.yml [PROPERTY] 
FAIL | [ERROR] Additional properties are not allowed ('test_extra_property' was unexpected) [FILE] ./hostvars/fail-tests/dns.yml [PROPERTY] dns_servers:1
```

> Note: The schema definition `additionalProperties` attribute is part of JSONSchema standard definitions. More information on how to construct these definitions can be found [here](https://json-schema.org/understanding-json-schema/reference/object.html)


<!-- The below examples assume the following `pyproject.toml` file.

```yaml
[tool.jsonschema_testing]
schema_file_extension = ".json"

instance_file_extension = ".yml"

instance_search_directories = ["./"]

[tool.jsonschema_testing.schema_mapping]
# Map instance filename to schema filename
'dns.yml' = ['schemas/dns_servers', 'http://networktocode.com/schemas/core/base']
'syslog.yml' = ["schemas/syslog_servers"]
``` -->

<!-- #### json_schema_path

Description
***********

Defines the location of all JSON formatted schema files required to build schema definitions. The schema directory structure has subdirectories named `schemas` and `definitions`.

Example
*******

```shell
(.venv) $ ls schema/json/
definitions    schemas
```

#### yaml_schema_path

Description
***********
Defines the location of all YAML formatted schema files required to build schema definitions. The schema directory structure has subdirectories named `schemas` and `definitions`.


Example
*******

```shell
(.venv) $ ls schema/yaml/
definitions    schemas
```

#### json_schema_definitions

Description
***********
Defines the location of all JSON formatted schema definitions.

#### yaml_schema_definitions

Description
***********

Defines the location of all YAML formatted schema definitions.

#### json_full_schema_definitions

Description
***********

Defines the location to place schema definitions in after resolving all `$ref` objects. The schemas defined in **json_schema_definitions** are the authoritative source, but these can be expanded for visualization purposes (See `test-schema resolve-json-refs` below).

#### device_variables

Description
***********

Defines the directory where device variables are located. The directory structure expects subdirectories for each host and YAML files for defining variables per schema. The YAML files must use the `.yml` extension.

Example
*******

```shell
(.venv) $ ls hostvars/
csr1    csr2    eos1    junos1
(.venv) $ ls hostvars/csr1/
ntp.yml   snmp.yml
```

#### inventory_path

Description
***********

Defines the path to Ansible Inventory. This supports Ansible Inventory Practices.

Example
*******

```shell
(.venv) $ ls inventory/
hosts    group_vars/    host_vars/
(.venv) $ ls inventory/group_vars/
all.yml    ios.yml    eos.yml    nyc.yml
```

## Using Invoke


### Defining Schemas

The Schemas can be defined in YAML or JSON, and test-schema CLI tool can be used to replicate between formats. The conversion will overwrite any existing destination format files, but they do not currently remove files that have been deleted.  

Args
****

#### json_schema_path (str)

The path to JSON schema directories. The default is `json_schema_path` defined in the `pyproject.toml` file.

#### yaml_schema_path (str)

The path ot YAML schema directories. The default is `yaml_schema_path` defined in the `pyproject.toml` file.

#### Example

Environment
***********

```shell
(.venv) $ ls schema/yaml/schemas
ntp.yml    snmp.yml

(.venv) $ ls schema/json/schemas
ntp.json   vty.json

(.venv) $ cat schema/yaml/schemas/ntp.yml
---
$schema: "http://json-schema.org/draft-07/schema#"
$id: "schemas/ntp"
description: "NTP Configuration schema."
type: "object"
properties:
  ntp_servers:
    $ref: "../definitions/arrays/ip.json#ipv4_hosts"
  authentication:
    type: "boolean"
  logging:
    type: "boolean"
required: ["ntp_servers"]

(.venv) $ cat schema/json/schemas/ntp.yml
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "description": "NTP Configuration schema.",
    "type": "object",
    "properties": {
        "ntp_servers": {
            "$ref": "../definitions/arrays/ip.json#ipv4_hosts"
        }
    },
    "required": [
        "ntp_servers"
    ]
}
(.venv) $ 
```

The above environment has the following differences:

* The `schema/yaml/schemas` directory does not have the `vty` schema defined in `schema/json/schemas/`
* The `schema/yaml/schemas` directory has schema defined for `snmp` that is not defined in `schema/json/schemas`
* The YAML version of the `ntp` schema has 2 additional properties defined compared ot the JSON version

Converting Schema between formats
************

The CLI command `test-schema convert-yaml-to-json` or `test-schema convert-json-to-yaml` can be used to perform the conversion from your desired source format to the destination format. -->
<!-- 
### Resolving JSON Refs

The JSON Reference specification provides a mechanism for JSON Objects to incorporate reusable fragments defined outside of its own structure. This is done using the `$ref` key, and a value defining the URI to reach the resource definition.

```json
{
    "servers": {
        "$ref": "definitions/arrays/hosts.json#servers"
    }
}
```

The CLI tool can be used to resolve these JSON References used in the project's schema definitions. The resulting expanded Schema Definition will be written to a file. This only works for schemas defined in JSON, so you must use the `test-schema convert-yaml-to-json` method first if your primary source is the schema written in YAML.

Args
****

#### json_schema_path (str)

The path to JSONSchema definintions in JSON format. The defualt is `json_schema_definitions` defined in the `pyproject.toml` file.

#### output_path (str)

The path to write the resulting schema definitions to. The default is `json_full_schema_definitions` defined in the `pyproject.toml` file.

#### Example

Schema References
***********

```shell
(.venv) $ cat schema/json/schemas/ntp.json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "schemas/ntp",
    "description": "NTP Configuration schema.",
    "type": "object",
    "properties": {
        "ntp_servers": {
            "$ref": "../definitions/arrays/ip.json#ipv4_hosts"
        }
    },
    "required": [
        "ntp_servers"
    ]
}
(.venv) $ cat schema/json/definitinos/arrays/ip.json
{
    "definitions": {
        "ipv4_hosts": {
            "type": "array",
            "items": {
                "$ref": "../objects/ip.json#ipv4_host"
            },
            "uniqueItems": true
        }
    }
}
(.venv) $ cat schema/json/definitions/objects/ip.json
{
    "definitions": {
        "ipv4_network": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "network": {
                    "$ref": "../properties/ip.json#ipv4_address"
                },
                "mask": {
                    "$ref": "../properties/ip.json#ipv4_cidr"
                },
                "vrf": {
                    "type": "string"
                }
            },
            "required": [
                "network",
                "mask"
            ]
        }
    }
}
(.venv) $ cat schema/json/definitions/properties/ip.json
{
    "ipv4_address": {
        "type": "string",
        "format": "ipv4"
    },
    "ipv4_cidr": {
        "type": "number",
        "minimum": 0,
        "maximum": 32
    }
}
(.venv) $ 
```

The above environment has the following References:

* `schemas/ntp.json` has ntp_servers which references `"../definitions/arrays/ip.json#ipv4_hosts`
* `definitions/arrays/ip.json#ipv4_hosts` references `../objects/ip.json#ipv4_host` for the arrays items
* `definitions/objects/ip.json#ipv4_host` references both `ipv4_address` and `ipv4_mask` in `../properties/ip.json` -->
<!-- 
### Using test-schema command-line tool

To use the `test-schema` script, the pyproject.toml file must have a tool.jsonschema_testing section that defines some of the required setup variables.  An example of this is in the example/ folder, and this is from where you can also directly run the `test-schema` cli for testing and development purposes.


CLick is used for the CLI tool, and full help is available for the commands and sub-options as follows:

e.g.
```
$ cd example/
$ test-schema --help
Usage: test-schema [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  convert-json-to-yaml       Reads JSON files and writes them to YAML files.
  convert-yaml-to-json       Reads YAML files and writes them to JSON files.
  generate-hostvars          Generates ansible variables and creates a file...
  generate-invalid-expected  Generates expected ValidationError data from...
  resolve-json-refs          Loads JSONSchema schema files, resolves...
  validate-schema            Validates instance files against defined
                             schema...

  view-validation-error      Generates ValidationError from invalid mock...

$ test-schema validate-schema --help
Usage: test-schema validate-schema [OPTIONS]

  Validates instance files against defined schema

  Args:     show_pass (bool): show successful schema validations
  show_checks (bool): show schemas which will be validated against each
  instance file

Options:
  --show-checks  Shows the schemas to be checked for each instance file
                 [default: False]

  --show-pass    Shows validation checks that passed  [default: False]
  --help         Show this message and exit.
  ```


### Validating Instance Data Against Schema

The CLI also provides a sub-command to validate instances against schema. The schema definitions used are pulled from **json_schema_definitions** defined in the `pyproject.toml` file. The network device data used is pulled from **device_variables** defined in the `pyproject.toml` file. 

```
$ test-schema validate-schema --help
Usage: test-schema validate-schema [OPTIONS]

  Validates instance files against defined schema

  Args:     show_pass (bool): show successful schema validations
  show_checks (bool): show schemas which will be validated against each
  instance file

Options:
  --show-checks  Shows the schemas to be checked for each instance file
                 [default: False]

  --show-pass    Shows validation checks that passed  [default: False]
  --help         Show this message and exit.


$ test-schema validate-schema --show-pass
PASS | [SCHEMA] dns_servers | [FILE] hostvars/eng-london-rt1/dns.yml
PASS | [SCHEMA] dns_servers | [FILE] hostvars/usa-lax-rt1/dns.yml
PASS | [SCHEMA] dns_servers | [FILE] hostvars/chi-beijing-rt1/dns.yml
PASS | [SCHEMA] dns_servers | [FILE] hostvars/mex-mxc-rt1/dns.yml
PASS | [SCHEMA] dns_servers | [FILE] hostvars/ger-berlin-rt1/dns.yml
PASS | [SCHEMA] dns_servers | [FILE] hostvars/usa-nyc-rt1/dns.yml
PASS | [SCHEMA] syslog_servers | [FILE] hostvars/usa-lax-rt1/syslog.yml
PASS | [SCHEMA] syslog_servers | [FILE] hostvars/chi-beijing-rt1/syslog.yml
PASS | [SCHEMA] syslog_servers | [FILE] hostvars/mex-mxc-rt1/syslog.yml
PASS | [SCHEMA] syslog_servers | [FILE] hostvars/usa-nyc-rt1/syslog.yml
ALL SCHEMA VALIDATION CHECKS PASSED
```

The --strict flag allows you to quickly override the additionalProperties attribute of schemas and check for any properties that are not defined in the schema:

```
$ test-schema validate-schema  --strict
FAIL | [ERROR] Additional properties are not allowed ('test_extra_item_property' was unexpected) [FILE] hostvars/fail-tests/ntp.yml [PROPERTY] ntp_servers:1 [SCHEMA] ntp.yml
FAIL | [ERROR] Additional properties are not allowed ('test_extra_property' was unexpected) [FILE] hostvars/fail-tests/ntp.yml [SCHEMA] ntp.yml
FAIL | [ERROR] Additional properties are not allowed ('test_extra_property' was unexpected) [FILE] hostvars/fail-tests/dns.yml [PROPERTY] dns_servers:1 [SCHEMA] dns.yml
```

In the above case, the ntp.yml contained "something: extra" as shown below:
```
---
ntp_servers:
  - address: "10.6.6.6"
    name: "ntp1"
  - address: "10.7.7.7"
    name: "ntp1"
    vrf: 123
    extra_item: else
ntp_authentication: False
ntp_logging: True
something: extra
```

-------------------

## Historic usage notes below, some items need to be reviewed/reimplemented in new CLI.
Passing the `--hosts` and `--schema` args resulted in only 4 tests running.

### Generating Host Vars

If the parent project is using Ansible, there is a Task that will build the inventory and write variable files based on the top-level Schema Properties.
This task uses the `ansible-inventory` command to get Ansible's view of the inventory.
The filenames will use the same name as the filename of the Schema definition.
Each file will contain the variable definitions for any top-level schema properties found in the Ansible inventory.

Args
****

#### output_path (str)

The path to store the variable files. The default root directory uses `device_variables` defined in the `pyproject.toml` file. Each host will have their own subdirectory from this value.

#### schema_path (str)

The path where the JSON formatted schema files are located.
The default uses `json_schema_definitions` defined in the `pyproject.toml` file.

#### inventory_path (str)

The path to Ansible Inventory.
The default uses `inventory_path` defined in the `pyproject.toml` file.

#### Example

Environment
***********

**ansible inventory**

```shell
ls inventory/
hosts.ini    group_vars/    host_vars/
```

**empty hostvars**

```shell
(.venv) $ ls hostvars/
(.venv) $
```

**schema definitions**

```
(.venv) $ ls schemas/json/schemas/
ntp.json    snmp.json
(.venv) $ less schemas/json/schemas/ntp.json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "schemas/ntp",
    "description": "NTP Configuration schema.",
    "type": "object",
    "properties": {
        "ntp_servers": {
            "$ref": "../definitions/arrays/ip.json#ipv4_hosts"
        },
        "ntp_authentication": {
            "type": "boolean"
        },
        "ntp_logging": {
            "type": "boolean"
        }
    },
    "required": [
        "ntp_servers"
    ]
}
(.venv) $
```

Using Invoke
************

```shell
(.venv) $ invoke generate-hostvars -o hostvars/ -s schema/json/schemas
Generating var files for host1
-> ntp
-> snmp
Generating var files for host2
-> ntp
(.venv) $ ls hostvars/
host    host2
(.venv) $ ls hostvars/host1/
ntp.yml    snmp.yml
(.venv) $ ls hostvars/host2/
ntp.yml
(.venv) $ less hostvars/host1/ntp.yml
---
ntp_servers:
  - address: "10.1.1.1"
    vrf: "mgmt"
ntp_authentication: true
(.venv) $
```

In the above example, both hosts had directories created:

  * host1 had two files created since it defined variables for both schemas
  * host2 only had one file created since it did not define data matching the snmp schema

Looking at the variables for `host1/ntp.yml`, only two of the three top-level Properties were defined.


### Create Invalid Mock Exceptions

This task is a helper to creating test cases for validating the defined Schemas properly identify invalid data.
Python's JSONSchema implmentation only has a single Exception for failed validation.
In order to verify that invalid data is failing validation for the expected reason, the tests investigate the Exception's attributes against the expected failure reasons.
This task will dynamically load JSON files in the Invalid mock directory (see Testing below), and create corresponding files with the Exception's attributes.
These attributes are stored in a YAML file adjacent to the invalid data files.

This task has one required argument, `schema`, which is used to identify the schema file and mock directory to load files from, and where to store the attribute files.

This uses `json_schema_path` defined in the ``pyproject.toml`` file to look for Schema definitions.
The invalid mock data is expected to be in `tests/mocks/<schema>/invalid/`.
All JSON files in the invalid mock directory will be loaded and have corresponding attribute files created.

Args
****

#### schema (str)

The schema filename to load invalid mock data and test against the Schema in order to generate expected ValidationError attributes. This should not include any file extensions.

#### Example

Environment
***********

```shell
(.venv) $ ls tests/mocks/ntp/invalid/
invalid_format.json    invalid_ip.json
(.venv) $
```

Using Invoke
************

```shell
(.venv) $ python -m invoke create-invalid-expected -s ntp
Writing file to tests/mocks/ntp/invalid/invalid_format.yml
Writing file to tests/mocks/ntp/invalid/invalid_ip.yml
(.venv) $ ls tests/mocks/ntp/invalid/
invalid_format.json    invalid_format.yml    invalid_ip.json
invalid_ip.yml
(.venv) $ less invalid_ip.yml
---
message: "'10.1.1.1000' is not a 'ipv4'"
schema_path: "deque(['properties', 'ntp_servers', 'items', 'properties', 'address', 'format'])"
validator: "format"
validator_value: "ipv4"
(.venv) $
```

## Testing

This project provides 2 testing methodologies for schema validation using PyTest:
  * Validating that the Schema definitions validate and invalidate as expected
  * Validating data against the defined schema

The test files to use are:
  * jsonschema_testing/tests/test_schema_validation.py
  * jsonschema_testing/tests/tests_data_against_schema.py

The mock data for `test_schema_validation` should be placed in the parent project's directory, located in `tests/mocks/<schema>/`.

### Validating Schema Definitions

The schema validation tests will test that each defined schema has both valid and invalid test cases defined.
The tests expect JSON files defining mock data; these files can be named anything, but must use the `.json` extension.
In addition to the JSON files, the invalid tests also requires YAML files with the attributes from the expected ValidationError.
The filenames of the YAML files must match the names used by the JSON files.

#### Example

Environment
***********

**valid test cases**

```shell
(.venv) $ ls tests/mocks/
ntp    snmp
(.venv) $ ls tests/mocks/ntp/valid/
full_implementation.json    partial_implementation.json
(.venv) $ less tests/mocks/ntp/valid/full_implementation.json
{
    "ntp_servers": [
        {
            "name": "ntp-east",
            "address": "10.1.1.1"
        },
        {
            "name": "ntp-west",
            "address": "10.2.1.1",
            "vrf": "mgmt"
        }
    ],
    "authentication": false,
    "logging": true
}
(.venv) $
```

**invalid test cases**

```shell
(.venv) $ ls tests/mocks/
(.venv) $ ls tests/mocks/ntp/invalid/
invalid_ip.json    invalid_ip.yml
(.venv) $ less tests/mocks/ntp/invalid/invalid_ip.json
{
    "ntp_servers": [
        {
            "name": "ntp-east",
            "address": "10.1.1.1000"
        }
    ]
}
(.venv) $ less tests/mocks/ntp/invalid/invalid_ip.yml
---
message: "'10.1.1.1000' is not a 'ipv4'"
schema_path: "deque(['properties', 'ntp_servers', 'items', 'properties', 'address', 'format'])"
validator: "format"
validator_value: "ipv4"
(.venv) $
```

Using Pytest
************

```shell
(.venv) $ pytest tests/test_schema_validation.py 
============================= test session starts ==============================
platform linux -- Python 3.7.5, pytest-5.3.2, py-1.8.0, pluggy-0.13.1
collected 6 items                                                             

tests/test_schema_validation.py ......                                    [100%]
(.venv) $
```


### Validating Data Against Schema

> The Invoke `validate` task provides a wrapper for this test.

The data validation test validates that inventory data conforms to the defined Schemas.
Each host must have its variable data stored in its own directory, and each YAML file inside the directory must use the same filename as the Schema definition file, and use the `.yml` extension.
Only variables defined in the corresponding Schema definition file will be validated.
Having additional variables defined will not cause an issue, but those variables will not be validated.
Any host that does not have data defined for the Schema will be silently ignored for that Schema validation check.

#### Optional Vars

##### Schema (list)

The list of Schemas to validate against. Passing multiple schemas is done by passing multiple schema flags: `--schema=ntp --schema=dns`.
The default will use all Schemas defined in `json_schema_definitions` in the ``pyproject.toml`` file.

##### hostvars (str)

The directory where all hosts define their variable data. The default uses `device_variables` defined in the ``pyproject.toml`` file.

##### hosts (list)

The list of hosts that should have data validated against the Schema. This variable is used by passing a single host flag with a comma separated string of hosts: `--hosts=host1,host2`.
The default will use all the directory names from the directories under the `hostvars` option.

#### Example

Environment
***********

**schemas**

```shell
(.venv) $ ls schema/json/schemas/
ntp.json    snmp.json
(.venv) $ less schema/json/schemas/ntp.json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "schemas/ntp",
    "description": "NTP Configuration schema.",
    "type": "object",
    "properties": {
        "ntp_servers": {
            "$ref": "../definitions/arrays/ip.json#ipv4_hosts"
        },
        "ntp_authentication": {
            "type": "boolean"
        },
        "ntp_logging": {
            "type": "boolean"
        }
    },
    "required": [
        "ntp_servers"
    ]
}
(.venv) $
```

**hostvars**
```shell
(.venv) $ ls hostvars/
host1    host2    host3
(.venv) $ ls hostvars/host1/
ntp.yml    snmp.yml
(.venv) $ ls hostvars/host2/
ntp.yml
(.venv) $ less hostvars/host1/ntp.yml
---
ntp_servers:
  - address: "10.1.1.1"
    vrf: "mgmt"
ntp_authentication: true
(.venv) $
```

Using Pytest
************

```shell
(.venv) $ pytest tests/test_data_against_schema.py --hosts=host1,host2
============================= test session starts ==============================
platform linux -- Python 3.7.5, pytest-5.3.2, py-1.8.0, pluggy-0.13.1
collected 3 items                                                             

tests/test_schema_validation.py ...                                       [100%]
(.venv) $
``` -->
