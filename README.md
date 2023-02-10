# Schema Enforcer

Schema Enforcer provides a framework for testing structured data against schema definitions. Right now, [JSONSchema](https://json-schema.org/understanding-json-schema/index.html) is the only schema definition language supported, but we are thinking about adding other schema definition languages at some point in the future.

## Getting Started

### Install

Schema Enforcer is a python library which is available on PyPi. It requires a python version of 3.7 or greater. Once a supported version of python is installed on your machine, pip can be used to install the tool by using the command `python -m pip install schema-enforcer`.

```cli
bash$ python --version
Python 3.7.9

bash$ pip --version
pip 20.1.1 from /usr/local/lib/python3.7/site-packages/pip (python 3.7)

python -m pip install schema-enforcer
```

> Note: To determine the version of python your system is using, the command `python --version` can be run from a terminal emulator

> Note: Pip is a package manager for python. While most recent versions of python come with pip installed, some do not. You can determine if pip is installed on your system using the command `pip --version`. If it is not, the instructions for installing it, once python has been installed, can be found [here](https://pip.pypa.io/en/stable/installing/)

### Overview

Schema Enforcer requires that two different elements be defined by the user:

- Schema Definition Files: These are files which define the schema to which a given set of data should adhere.
- Structured Data Files: These are files which contain data that should adhere to the schema defined in one (or multiple) of the schema definition files.

> Note: Data which needs to be validated against a schema definition can come in the form of Structured Data Files or Ansible host vars. Ansible is not installed by default when schema-enforcer is installed. In order to use Ansible features, ansible must already be available or must be declared as an optional dependency when schema-enforcer upon installation. In the interest of brevity and simplicity, this README.md contains discussion only of Structured Data Files -- for more information on how to use `schema-enforcer` with ansible host vars, see [the ansible_command README](docs/ansible_command.md)

When `schema-enforcer` runs, it assumes directory hierarchy which should be in place from the folder in which the tool is run.

- `schema-enforcer` will search for **schema definition files** nested inside of `./schema/schemas/` which end in `.yml`, `.yaml`, or `.json`.
- `schema-enforcer` will do a recursive search for **structured data files** starting in the current working diretory (`./`). It does this by searching all directories (including the current working directory) for files ending in `.yml`, `.yaml`, or `.json`. The `schema` folder and it's subdirectories are excluded from this search by default.

```cli
bash$ cd examples/example1
bash$ tree
.
├── chi-beijing-rt1
│   ├── dns.yml
│   └── syslog.yml
├── eng-london-rt1
│   ├── dns.yml
│   └── ntp.yml
└── schema
    └── schemas
        ├── dns.yml
        ├── ntp.yml
        └── syslog.yml

4 directories, 7 files
```

In the above example, `chi-beijing-rt1` is a directory with structured data files containing some configuration for a router named `chi-beijing-rt1`. There are two structured data files inside of this folder, `dns.yml` and `syslog.yml`. Similarly, the `eng-london-rt1` directory contains definition files for a router named `eng-london-rt1` -- `dns.yml` and `ntp.yml`.

The file `chi-beijing-rt1/dns.yml` defines the DNS servers `chi-beijing.rt1` should use. The data in this file includes a simple hash-type data structure with a key of `dns_servers` and a value of an array. Each element in this array is a hash-type object with a key of `address` and a value which is the string of an IP address.

```yaml
bash$ cat chi-beijing-rt1/dns.yml
# jsonschema: schemas/dns_servers
---
dns_servers:
  - address: "10.1.1.1"
  - address: "10.2.2.2"
```
> Note: The line `# jsonschema: schemas/dns_servers` tells `schema-enforcer` the ID of the schema which the structured data defined in the file should be validated against. The schema ID is defined by the `$id` top level key in a schema definition. More information on how the structured data is mapped to a schema ID to which it should adhere can be found in the [mapping_schemas README](./docs/mapping_schemas.md)

The file `schema/schemas/dns.yml` is a schema definition file. It contains a schema definition for ntp servers written in JSONSchema. The data in `chi-beijing-rt1/dns.yml` and `eng-london-rt1/dns.yml` should adhere to the schema defined in this schema definition file.

```yaml
bash$ cat schema/schemas/dns.yml
---
$schema: "http://json-schema.org/draft-07/schema#"
$id: "schemas/dns_servers"
description: "DNS Server Configuration schema."
type: "object"
properties:
  dns_servers:
    type: "array"
    items:
      type: "object"
      properties:
        name:
          type: "string"
        address:
          type: "string"
          format: "ipv4"
        vrf:
          type: "string"
      required:
        - "address"
      uniqueItems: true
required:
  - "dns_servers"
```

> Note: The cat of the schema definition file may be a little scary if you haven't seen JSONSchema before. Don't worry too much if it is difficult to parse right now. The important thing to note is that this file contains a schema definition to which the structured data in the files `chi-beijing-rt1/dns.yml` and `eng-london-rt1/dns.yml` should adhere.

### Basic usage

Once schema-enforcer has been installed, the `schema-enforcer validate` command can be used run schema validations of YAML/JSON instance files against the defined schema.

```shell
bash$ schema-enforcer --help
Usage: schema-enforcer [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  ansible        Validate the hostvar for all hosts within an Ansible...
  schema         Manage your schemas
  validate       Validates instance files against defined schema
```

To run the schema validations, the command `schema-enforcer validate` can be run.

```shell
bash$ schema-enforcer validate
schema-enforcer validate
ALL SCHEMA VALIDATION CHECKS PASSED
```

To acquire more context regarding what files specifically passed schema validation, the `--show-pass` flag can be passed in.

```shell
bash$ schema-enforcer validate --show-pass
PASS [FILE] ./eng-london-rt1/ntp.yml
PASS [FILE] ./eng-london-rt1/dns.yml
PASS [FILE] ./chi-beijing-rt1/syslog.yml
PASS [FILE] ./chi-beijing-rt1/dns.yml
ALL SCHEMA VALIDATION CHECKS PASSED
```

If we modify one of the addresses in the `chi-beijing-rt1/dns.yml` file so that it's value is the boolean `true` instead of an IP address string, then run the `schema-enforcer` tool, the validation will fail with an error message.

```yaml
bash$ cat chi-beijing-rt1/dns.yml
# jsonschema: schemas/dns_servers
---
dns_servers:
  - address: true
  - address: "10.2.2.2"
```
```shell
bash$ test-schema validate
FAIL | [ERROR] True is not of type 'string' [FILE] ./chi-beijing-rt1/dns.yml [PROPERTY] dns_servers:0:address
bash$ echo $?
1
```

When a structured data file fails schema validation, `schema-enforcer` exits with a code of 1.

### Configuration Settings

Schema enforcer will work with default settings, however, a `pyproject.toml` file can be placed at the root of the path in which `schema-enforcer` is run in order to override default settings or declare configuration for more advanced features. Inside of this `pyproject.toml` file, `tool.schema_enforcer` sections can be used to declare settings for schema enforcer. Take for example the `pyproject.toml` file in example 2.

```shell
bash$ cd examples/example2 && tree -L 2
.
├── README.md
├── hostvars
│   ├── chi-beijing-rt1
│   ├── eng-london-rt1
│   └── ger-berlin-rt1
├── invalid
├── pyproject.toml
└── schema
    ├── definitions
    └── schemas

8 directories, 2 files
```

In this toml file, a schema mapping is declared which tells schema enforcer which structured data files should be checked by which schema IDs.


```shell
bash$ cat pyproject.toml
[tool.schema_enforcer.schema_mapping]
# Map structured data filename to schema IDs
'dns_v1.yml' = ['schemas/dns_servers']
'dns_v2.yml' = ['schemas/dns_servers_v2']
'syslog.yml' = ['schemas/syslog_servers']
```

> More information on available configuration settings can be found in the [configuration README](docs/configuration.md)

### Supported Formats

By default, schema enforcer installs the jsonschema `format-nongpl` extra which allows the use of formats that can be used in schema definitions (e.g. ipv4, hostname...etc). The `format-nongpl` extra only installs transitive dependencies that are not licensed under GPL. The `iri` and `iri-reference` formats are defined by the `rfc3987` transitive dependency which is licensed under GPL. As such, `iri` and `iri-reference` formats are *not* supported by `format-nongpl`. If you have a need to use `iri` and/or `iri-reference` formats, you can do so by running the following pip command (or it's poetry equivalent):

```
pip install 'jsonschema[rfc3987]'
```

See the "Validating Formats" section in the [jsonschema documentation](https://github.com/python-jsonschema/jsonschema/blob/main/docs/validate.rst) for more information.

### Custom Error Message Support

Schema enforcer is able to handle and return custom error messages that are defined in the JSON Schema itself using reserved keywords. These custom error messages override the default messages returned by JSON Schema. For example consider the following JSON Schema:

```
type: object
additionalProperties: false
properties:
  data:
    type: object
    properties:
      name:
        $ref: "#/$defs/regex_sub_schema"
      aliases:
        type: array
        items:
          $ref: "#/$defs/regex_sub_schema"

$defs:
  regex_sub_schema:
    type: string
    pattern: regex
    err_message: "'$instance' is not valid. Please see docs."
```
When validating against test data with invalid entries for `name` and `aliases`, the custom error is returned:

```
FAIL | [ERROR] 'host' is not valid. Please see docs. [FILE] .//test.yml [PROPERTY] data:name
FAIL | [ERROR] 'alias-1' is not valid. Please see docs. [FILE] .//test.yml [PROPERTY] data:aliases:0
FAIL | [ERROR] 'alias-2' is not valid. Please see docs. [FILE] .//test.yml [PROPERTY] data:aliases:1
```
The error messages returned contain the instance data that was being validated at the time of failure. This is achieved by using the `$instance` variable within the custom error message. All occurences of this variable will be replaced with the instance data being validated.

Please bear in mind that custom errors defined at the `root` level of the schema are ignored. For example if we add a custom error at the root level:

```
type: object
additionalProperties: false
err_message: This error message will be ignored.
properties:
  data:
    [...]
```
Then validate against data with an additional property at the root level, for example:
```
data:
  name: host
  aliases:
    - etc...
data2:
  name: host2
```
The error returned will be the default JSON Schema error:
```
FAIL | [ERROR] Additional properties are not allowed ('data2' was unexpected) [FILE] .//test.yml [PROPERTY]
```

### Where To Go Next

Detailed documentation can be found in the README.md files inside of the `docs/` directory.
- ["Introducing Schema Enforcer" blog post](https://blog.networktocode.com/post/introducing_schema_enforcer/)
- [Using a pyproject.toml file for configuration](docs/configuration.md)
- [Mapping Structured Data Files to Schema Files](docs/mapping_data_files_to_schemas.md)
- [The `ansible` command](docs/ansible_command.md)
- [The `validate` command](docs/validate_command.md)
- [The `schema` command](docs/schema_command.md)
- [Implementing custom validators](docs/custom_validators.md)
