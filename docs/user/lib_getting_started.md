# Getting Started with the Library

This document provides a step-by-step tutorial on how to get the library going and how to use it.

## Install the Library

To install the library, please follow the instructions detailed in the [Installation Guide](../admin/install.md).

## First steps with the Library

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
> Note: The line `# jsonschema: schemas/dns_servers` tells `schema-enforcer` the ID of the schema which the structured data defined in the file should be validated against. The schema ID is defined by the `$id` top level key in a schema definition. More information on how the structured data is mapped to a schema ID to which it should adhere can be found in the [mapping_schemas README](../user/mapping_data_files_to_schemas.md)

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

## What are the next steps?

You can check out the [Use Cases](./lib_use_cases.md) section for more examples.
