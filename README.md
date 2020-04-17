# JSON Schema Testing

This repository provides a framework for building and testing [JSONSchema](https://json-schema.org/understanding-json-schema/index.html) definitions.
[JSONRef](http://jsonref.readthedocs.org/) is used to resolve JSON references within Schema definitions.
This project also uses [Invoke](http://docs.pyinvoke.org/) to provide a user interface for project builds.
Invoke is similar to GNU Make, but is written in Python.
Finally, [Pytest](https://docs.pytest.org/) is used to validate data against the defined schemas, and to validate schemas behave as expected.

## Project Build

The invoke file can be used to create and build a python virtual environment for the project. The build task first creates the environment in a directory named `.venv` using `virtualenv`. Once the `.venv` environment is created, that environment's pip executable is used to install the packages listed in `requirements.txt`. The build task does require `virtualenv` and `invoke` to be available already.

### Example

```shell
$ python3 -m invoke build
Using base prefix '/usr'
New python executable in /home/user/test/netschema/.venv/bin/python3
Also creating executable in /home/user/test/netschema/.venv/bin/python
Installing setuptools, pip, wheel...
done.
Collecting jsonref ...
Collecting invoke ...
Collecting pytest ...
Collecting jsonschema ...
Collecting ruamel.yaml ...
Collecting wcwidth ...
Collecting py>=1.5.0 ...
Collecting attrs>=17.4.0 ...
Collecting packaging ... 
Collecting more-itertools>=4.0.0 ...
Collecting importlib-metadata>=0.12; python_version < "3.8" ...
Collecting pluggy<1.0,>=0.12 ...
Collecting six>=1.11.0 ...
Processing /home/user/.cache/pip/wheels/83/89/d3/1712b9c33c9b9c0911b188a86aeff2a9a05e113f986cf79d92/pyrsistent-0.15.6-cp37-cp37m-linux_x86_64.whl
Collecting ruamel.yaml.clib>=0.1.2; platform_python_implementation == "CPython" and python_version < "3.8" ...
Collecting pyparsing>=2.0.2 ...
Collecting zipp>=0.5 ...
Installing collected packages: jsonref, invoke, wcwidth, py, attrs, pyparsing, six, packaging, more-itertools, zipp, importlib-metadata, pluggy, pytest, pyrsistent, jsonschema, ruamel.yaml.clib, ruamel.yaml
Successfully installed attrs-19.3.0 importlib-metadata-1.3.0 invoke-1.3.0 jsonref-0.2 jsonschema-3.2.0 more-itertools-8.0.2 packaging-19.2 pluggy-0.13.1 py-1.8.0 pyparsing-2.4.5 pyrsistent-0.15.6 pytest-5.3.2 ruamel.yaml-0.16.5 ruamel.yaml.clib-0.2.0 six-1.13.0 wcwidth-0.1.7 zipp-0.6.0
$
```

Once the environment is built, it must be activated to ensure the project behaves as expected.

Linux:
```shell
$ source .venv/bin/activate
(.venv) $ 
```

Windows:
```shell
> .venv\Scripts\Activate.bat
(.venv) >
```

### Building the Environment in the Parent Project

Currently, Invoke has some challenges being used within a subproject.
The solution provided below creates a new `tasks.py` file, and creates a `Collection` from the `tasks.py` file in this project.
The install task is overwritten to install the requirements file defined here, and a requirements file defined in the local project.
This can be changed based on the parent project's design.

```python
"""Tasks used by Invoke."""
from invoke import Collection
from jsonschema_testing import tasks as schema_tasks


schema_tasks.SCHEMA_TEST_DIR = "jsonschema_testing/tests"


@schema_tasks.task
def install(context):
    """Installs ``requirements.txt`` into Python Environment."""
    context.run(f"{schema_tasks.PIP_EXE} install -r requirements.txt")
    context.run(
        f"{schema_tasks.PIP_EXE} install -r jsonschema_testing/requirements.txt"
    )


ns = Collection.from_module(schema_tasks)
ns.tasks["build"].post = [install]
```

## Customizing Project Config

This project uses a YAML file named `schema.cfg` to customize the project's settings. There is an example settings file defined in `examples/schema.cfg`, which works with the provided examples. This file should be copied to the Schema's project root directory, and updated per the Project's settings.

### Variables

The below examples assume the following `schema.cfg` file.

```yaml
---
json_schema_path: "schema/json"
yaml_schema_path: "schema/yaml"

json_schema_definitions: "schema/json/schemas"
yaml_schema_definitions: "schema/yaml/schemas"

json_full_schema_definitions: "schema/json/full_schemas"

```

#### json_schema_path

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
Defines the location of all JSON formatted schema specifications. This directory should only contain schema specifications, and should not contain schema defintion files.

Example
*******

```shell
(.venv) $ ls schema/json/schemas/
ntp.json    snmp.json
```

#### yaml_schema_definitions

Description
***********

Defines the location of all YAML formatted schema specifications. This directory should only contain schema specifications, and should not contain schema defintion files. All files should use the `.yml` extension.

Example
*******

```shell
(.venv) $ ls schema/yaml/schemas/
ntp.yml    snmp.yml
```

#### json_full_schema_definitions

Description
***********

Defines the location to place schema definitions in after resolving all `$ref` objects. The schemas defined in **json_schema_definitions** are the authoritative source, but these can be expanded for visualization purposes.

Example
*******

```shell
(.venv) $ ls schema/json/full_schemas/`
ntp.json    snmp.json
```

#### device_variables

Description
***********

Defines the directory where device variables are located. The directory structure expects subdirectories for each host and YAML files for defining variables per schema. The YAML files must use the `.yml` extension.

Example
*******

```shell
(.venv) $ ls examples/hostvars/
csr1    csr2    eos1    junos1
(.venv) $ ls examples/hostvars/csr1/
ntp.yml   snmp.yml
```

## Using Invoke


### Defining Schemas

The Schemas can be defined in YAML or JSON, and Invoke can be used to replicate between formats. The conversion scripts will overwrite any existing files, but they do not currently remove files that have been deleted. YAML files must use the `yml` extension.

Args
****

#### json_path (str)

The path to JSON schema directories. The default is `json_schema_path` defined in the schema.cfg file.

#### yaml_path (str)

The path ot YAML schema directories. The defautl is `yaml_schema_path` defined in the schema.cfg file.

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

Using Invoke
************

Invoking the `convert-yaml-to-json` script, the expected outcome is:

* The JSON `vty` schema will remain unchanged
* The YAML `snmp` schema will be added to the JSON directory
* The JSON `ntp` schema will be updated with the additional properties

```shell
(.venv) $ invoke convert-yaml-to-json
Converting schema/yaml/schemas/ntp.yml -> schema/json/schemas/ntp.json
Converting schema/yaml/schemas/snmp.yml -> schema/json/schemas/snmp.json

(.venv) $ ls schema/json/schemas
ntp.json    snmp.json    vty.json

(.venv) $ cat schema/json/schemas/ntp.json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "schemas/ntp",
    "description": "NTP Configuration schema.",
    "type": "object",
    "properties": {
        "ntp_servers": {
            "$ref": "../definitions/arrays/ip.json#ipv4_hosts"
        },
        "authentication": {
            "type": "boolean"
        },
        "logging": {
            "type": "boolean"
        }
    },
    "required": [
        "ntp_servers"
    ]
}
(.venv) $
```

### Resolving JSON Refs

The JSON Reference specification provides a mechanism for JSON Objects to incorporate reusable fragments defined outside of its own structure. This is done using the `$ref` key, and a value defining the URI to reach the resource definition.

```json
{
    "servers": {
        "$ref": "definitions/arrays/hosts.json#servers"
    }
}
```

Invoke can be used to resolve the JSON References used in the project's schema definitions. The resulting Schema Definition will be written to a file. This only works for schemas defined in JSON, so use the `convert-yaml-to-json` method first if defining schema in YAML.

Args
****

#### json_schema_path (str)

The path to JSONSchema definintions in JSON format. The defualt is `json_schema_definitions` defined in the schema.cfg file.

#### output_path (str)

The path to write the resulting schema definitions to. The default is `json_full_schema_definitions` defined in the schema.cfg file.

#### Example

Environment
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
* `definitions/objects/ip.json#ipv4_host` references both `ipv4_address` and `ipv4_mask` in `../properties/ip.json`

Using Invoke
************

Invoking the `resolve-json-refs` task will resolve all References recursively and write the output to a file in schema/json/full_schemas; the name of the file will correspond to the name of the schema file.

```shell
(.venv) $ invoke resolve-json-refs

(.venv) $ cat schema/json/full_schemas/ntp.json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "schemas/ntp",
    "description": "NTP Configuration schema.",
    "type": "object",
    "properties": {
        "ntp_servers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "address": {
                        "type": "string",
                        "format": "ipv4"
                    },
                    "vrf": {
                        "type": "string"
                    }
                },
                "required": [
                    "address"
                ]
            },
            "uniqueItems": true
        },
        "authentication": {
            "type": "boolean"
        },
        "logging": {
            "type": "boolean"
        }
    },
    "required": [
        "ntp_servers"
    ]
}
```

### Validating Data Against Schema

Invoke also provides a task to validate data against schema. The schema definitions used are pulled from **json_schema_definitions** defined in the schema.cfg file. The network device data used is pulled from **device_variables** defined in the schema.cfg file. This directory can also be overwritten by passing the `--vars_dir` argument.

Args
****

#### schema (list)

The subset of schemas to execute tests against. The default is all schemas defined in the `json_schema_definitions` directory in the schema.cfg file.

#### vars_dir (str)

The directory where all hosts' variables are defined. The default is to use Pytest settings, which uses the `device_variables` setting defined in the schema.cfg file.

#### hosts (str)

The subset of hosts to execute tests against. The default is to use each host directory defined in the `device_variables` directory in the schema.cfg file.

#### Example

Environment
***********

```shell
(.venv) $ ls schema/json/schemas/
bgp.yml    ntp.yml    snmp.yml
(.venv) $ ls examples/hostvars/
csr1    eos1    junos1
(.venv) $ ls examples/hostvars/csr1/
ntp.yml    snmp.yml
```

Since **csr1** does not define data for BGP, the validation task will skip validation and report it as *passed*.

Using Invoke
************

Invoking `validate` with the default settings will validate all three schemas for all three hosts.

```shell
(.venv) $ invoke validate
python -m pytest tests/test_data_against_schema.py -vv
============================= test session starts =============================

tests/test_data_against_schema.py::test_config_definitions_against_schema[csr1-bgp-validator0] PASSED [ 11%]
tests/test_data_against_schema.py::test_config_definitions_against_schema[csr1-ntp-validator1] PASSED [ 22%]
tests/test_data_against_schema.py::test_config_definitions_against_schema[csr1-snmp-validator2] PASSED [ 33%]
tests/test_data_against_schema.py::test_config_definitions_against_schema[eos1-bgp-validator0] PASSED [ 44%]
tests/test_data_against_schema.py::test_config_definitions_against_schema[eos1-ntp-validator1] PASSED [ 56%]
tests/test_data_against_schema.py::test_config_definitions_against_schema[eos1-snmp-validator2] PASSED [ 67%]
tests/test_data_against_schema.py::test_config_definitions_against_schema[junos1-bgp-validator0] PASSED [ 78%]
tests/test_data_against_schema.py::test_config_definitions_against_schema[junos1-ntp-validator1] PASSED [ 89%]
tests/test_data_against_schema.py::test_config_definitions_against_schema[junos1-snmp-validator2] PASSED [100%]

============================== 9 passed in 0.70s ==============================
(vevn) $ 
```

In order to limit the hosts and schemas to test, use the `--hosts` and `--schema` respectively.

```shell
(.venv) $ invoke validate --hosts csr1,eos1 --schema ntp --schema snmp
python -m pytest tests/test_data_against_schema.py -vv
============================= test session starts =============================

tests/test_data_against_schema.py::test_config_definitions_against_schema[csr1-ntp-validator0] PASSED [ 25%]
tests/test_data_against_schema.py::test_config_definitions_against_schema[csr1-snmp-validator1] PASSED [ 50%]
tests/test_data_against_schema.py::test_config_definitions_against_schema[eos1-ntp-validator0] PASSED [ 75%]
tests/test_data_against_schema.py::test_config_definitions_against_schema[eos1-snmp-validator1] PASSED [100%]

============================== 4 passed in 0.33s ==============================
(vevn) $ 
```

Passing the `--hosts` and `--schema` args resulted in only 4 tests running.

### Generating Host Vars

If the parent project is using Ansible, there is a Task that will build the inventory and write variable files based on the top-level Schema Properties.
This task uses the `ansible-inventory` command to get Ansible's view of the inventory.
The filenames will use the same name as the filename of the Schema definition.
Each file will contain the variable definitions for any top-level schema properties found in the Ansible inventory.

Args
****

#### output_path (str)

The path to store the variable files. The default root directory uses `device_variables` defined in the schema.cfg file. Each host will have their own subdirectory from this value.

#### schema_path (str)

The path where the JSON formatted schema files are located.
The default uses `json_schema_definitions` defined in the schema.cfg file.

#### inventory_path (str)

The path to pass to the `ansible-inventory` command to specify the path to the inventory to load.
The default is to not specify an inventory and leave it to an `ansible.cfg` file or Environment settings.

#### Example

Environment
***********

**ansible.cfg**

```ini
[defaults]
inventory = inventory/
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

This uses `json_schema_path` defined in the `schema.cfg` file to look for Schema definitions.
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
The default will use all Schemas defined in `json_schema_definitions` in the `schema.cfg` file.

##### hostvars (str)

The directory where all hosts define their variable data. The default uses `device_variables` defined in the `schema.cfg` file.

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
```
