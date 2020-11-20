# Mapping Schemas

## Overview
In order to validate structured data files against schema definitions, `schema-enforcer` must have a way of mapping structured data files to the schema definition they should adhere to. This is done in one of two ways:

1) The pyproject.toml file can map structured data filenames to the schema ID to which they should adhere.
2) Any file containing structured data can be decorated with a comment which instructs `schema-enforcer` to check the file for compliance against the a defined schema.

To check which structured data files will be examined by which schemas, the `schema-enforcer validate --show-checks` command can be run.

```cli
bash$ cd examples/example3/
bash$ schema-enforcer validate --show-checks
Strucutred Data File                               Schema ID
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
```

## Using the pyproject.toml file to map schemas

In the pyproject.toml file, a `tools.schema_enforcer.schema_mapping` section can be defined which maps structured data files to schema IDs.

```toml
[tools.schema_enforcer.schema_mapping]
'dns_v1.yml' = ['schemas/dns_servers']
'dns_v2.yml' = ['schemas/dns_servers_v2']
```

The values above are key/value pairs defined in TOML. The key is a string of the structured data filename, the value is a list of schema IDs. The schema_id must be defined in the schema definition file. The below text snippet from a YAML file shows the schema ID to which the structured data file `dns_v1.yml` above is being mapped.

```yaml
---
$schema: "http://json-schema.org/draft-07/schema#"
$id: "schemas/dns_servers"
```

> Note: Output truncated for brevity.

If multiple schema IDs are defined in the list, the structured data file will be checked for adherence to all defined schema ids.

## Using a decorator to map schemas

A decorator can be used to map structured data files to the schemas they should be validated against. This can be done by adding a comment at the top of a YAML file which defines structured data in the form `# jsonschema: <schema_id>`. Multiple schemas can be defined here by separating schema IDs with a comma.

```yaml
# jsonschema: schemas/ntp,schemas/ntpv2
---
ntp_servers:
  - address: "10.6.6.6"
    name: "ntp1"
  - address: "10.7.7.7"
    name: "ntp1"
ntp_authentication: false
ntp_logging: true
```

```cli
bash$ schema-enforcer validate --show-checks

Instance File                                     Schema
--------------------------------------------------------------------------------
./hostvars/eng-london-rt1/ntp.yml                  ['schemas/ntp', 'schemas/ntpv2']
```

> Note: This option only works for structured data files defined in YAML. This is because inline coments are not supported by JSON.

## Multiple Definitions

In the event that a configuration section exists in the pyproject.toml file **and** a decorator exists in the structured data file, `schema-enforcer` will check the structured data files for adherenece to both schema IDs. In to following case, for instance, `schema-enforcer` will ensure that the structured data file `ntp.yml` adheres to both the `schemas/ntp` and `schemas/ntp2` schema definitions.

```toml
[tools.schema_enforcer.schema_mapping]
'ntp.yml' = ['schemas/ntp2']
```

```yaml
bash$ cat ntp.yml
# jsonschema: schemas/ntp
---
ntp_servers:
  - address: "10.6.6.6"
    name: "ntp1"
  - address: "10.7.7.7"
    name: "ntp1"
ntp_authentication: false
ntp_logging: true
```

```cli
bash$ schema-enforcer validate --show-checks
Instance File                                     Schema
--------------------------------------------------------------------------------
./hostvars/eng-london-rt1/ntp.yml                  ['schemas/ntp2', 'schemas/ntp']
```
