## Overview

This README.md describes behaviour not yet implemented. As such, it has been commented out and will be modified when the behaviour is implemented.

<!-- ## Overview

This example shows a use case for versioned schemas. There are 3 ways in which the mapping of instance data to schema file occurs:

1) The top level property of an instance file is evaluated against the schema definitions top level property in order to dynamically resolve which schema should be used to validate instance data.
2) The instance's file name is mapped to a schema ID in the `[tool.jsonschema_testing.schema_mapping]` section of a `pyproject.toml` file from which the test-schema command is run.
3) The instance file is decorated with a comment in the form `# jsonschema: <schema_id>`.

### What problem is being solved

The first mapping works great so long as differing instance files with the same top level properties don't need to adhere to different schemas. If schema applied to the data in one instance file for a given top level property differs from another instance file which has the same top level property but adheres to a different schema, however, another level of resolution is necessary. This can happen when two different versions of a schema for a given data type need to exist in tandem while migrating from one version of the schema to another.

On `eng-london-rt1`, for example, the instance data could be defined as follows

```yaml
---
dns_servers:
  - address: "10.6.6.6"
  - address: "10.7.7.7"
```

A new schema may be rolled out which renames the `address` key to `host`. Take `ger-berlin-rt1` for example:

```yaml
---
dns_servers:
  - host: "10.6.6.6"
  - host: "10.7.7.7"
```
In real life this could be something like creating another required property which isn't yet required on the old schema.

Because many different tools create and consume this data, it is sometimes beneficial to create versioned schemas so that different tools can consume different versions of the data while the tools are being migrated to consume data in the format of the new schema.

### Examples

#### Filename to Schema ID mapping

The DNS entries in `eng-london-rt1`'s `dns_v1.yml` and `ger-berlin-rt1`'s `dns_v2.yml` files showcase solution #2 described in the section above. In the `[tool.schema_enforcer.schema_mapping]` section of the `pyproject.toml` file (at the same location as this readme), file hostnames are mapped to a list of schema IDs which should be validated against them as follows:

```toml
[tool.schema_enforcer.schema_mapping]
'dns_v1.yml' = ['schemas/dns_servers']
'dns_v2.yml' = ['schemas/dns_servers_v2']
```

When the `test-schema validate` command is run with the `--show-checks` flag passed in, it shows that the `dns_v1.yml` and `dns_v2.yml` files in `eng-london-rt1` and `ger-berlin-rt1` will both be mapped to the appropriate schema, per their filename, as expected.

```cli
bash$ test-schema validate --show-checks | grep 'Instance\|--------\|eng-london-rt1/dns\|ger-berlin-rt1/dns'
Instance File                                     Schema
--------------------------------------------------------------------------------
./hostvars/eng-london-rt1/dns_v1.yml               ['schemas/dns_servers']
./hostvars/ger-berlin-rt1/dns_v2.yml               ['schemas/dns_servers_v2']
```

>Note: grep used to pull only dns schema mappings from devices eng-london-rt1 and ger-berlin-rt1 as well as headers for clarity and brevity.

When the schem validations are run, you can see that instance files adhere to schema as expected.

```cli
bash$ test-schema validate --show-pass | grep 'eng-london-rt1/dns\|ger-berlin-rt1/dns'
PASS [FILE] ./hostvars/eng-london-rt1/dns_v1.yml
PASS [FILE] ./hostvars/ger-berlin-rt1/dns_v2.yml
```

Further examination of the dns_v1.yml file in eng-london-rt1 shows that it is using the `address` k/v pair to indicate dns addresses, where the dns_v2.yml file in ger-berlin-rt1 is using the `host` k/v pair to indicate dns addresses.

```cli
bash$ cat ./hostvars/eng-london-rt1/dns_v1.yml                                       
---
dns_servers:
  - address: "10.6.6.6"
  - address: "10.7.7.7"

bash$ cat ./hostvars/ger-berlin-rt1/dns_v2.yml
---
dns_servers:
  - host: "10.6.6.6"
  - host: "10.7.7.7"
```
#### Instance file decorated with `#jsonschema: <schema_id>` decorator

`chi-beijing-rt1`'s `dns.yml` files showcase solution #3 described in the Overview section. In this case, `dns.yml` files are defined in nested `v1` and `v2` directories

```cli
bash$ tree hostvars/chi-beijing-rt1
├── dns
│   ├── v1
│   │   └── dns.yml
│   └── v2
│       └── dns.yml
└── syslog.yml

3 directories, 3 files
```

The dns file in the v1 directory has a decorator at the top specifying the file should be adherent with the schema who's ID is `schemas/dns_servers`

```cli
bash$ cat hostvars/chi-beijing-rt1/dns/v1/dns.yml
# jsonschema: schemas/dns_servers
---
dns_servers:
  - address: "10.1.1.1"
  - address: "10.2.2.2"
```

The dns file in the v2 directory has a decorator at the top specifying the file should be adherent with the schema who's ID is `schemas/dns_servers_v2`

```cli
bash$ cat hostvars/chi-beijing-rt1/dns/v2/dns.yml
# jsonschema: schemas/dns_servers_v2
---
dns_servers:
  - host: "10.1.1.1"
  - host: "10.2.2.2"
```

When the `test-schema` command is run in `validate` mode with the `--show-checks` flag checked in, it shows chi-beijing-rt1's dns files being mapped to the right schema IDs, even though the actual file name (dns.yml) is the same for both instance files.

```cli
bash$ test-schema validate --show-checks | grep 'Instance\|--------\|chi-beijing-rt1/dns'
Instance File                                     Schema
--------------------------------------------------------------------------------
./hostvars/chi-beijing-rt1/dns/v1/dns.yml          ['schemas/dns_servers']
./hostvars/chi-beijing-rt1/dns/v2/dns.yml          ['schemas/dns_servers_v2']
```

>Note: grep used to pull only dns schema mappings from devices chi-beijing-rt1 as well as headers for clarity and brevity.

When the schema validations are run, you can see that instance files adhere to schema as expected.

```cli
bash$ test-schema validate --show-pass | grep chi-beijing-rt1/dns                     
PASS [FILE] ./hostvars/chi-beijing-rt1/dns/v1/dns.yml
PASS [FILE] ./hostvars/chi-beijing-rt1/dns/v2/dns.yml
```

Further examination of the files (already cat'd out above) shows the v1 schema using the `address` property and the v2 schema using the `host` property to define dns servers. -->
