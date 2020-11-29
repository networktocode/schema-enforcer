# The `ansible` command

The `ansible` command is used to check ansible inventory for adherence to a schema definition. An example exists in the `examples/ansible` folder. With no flags passed in, schema-enforcer will display a line for each property definition that **fails** schema validation along with contextual information elucidating why a given portion of the ansible inventory failed schema validation, the host for which schema validation failed, and the portion of structured data that is failing validation. If all checks pass, `schema-enforcer` will inform the user that all tests have passed.

## How the inventory is loaded

When the `schema-enforcer ansible` command is run, an ansible inventory is constructed. Each host's properties are extracted from the ansible inventory then validated against schema. Take the following example

```cli
bash $ cd examples/ansible && schema-enforcer ansible
Found 4 hosts in the inventory
FAIL | [ERROR] True is not of type 'string' [HOST] spine1 [PROPERTY] dns_servers:0:address
FAIL | [ERROR] True is not of type 'string' [HOST] spine2 [PROPERTY] dns_servers:0:address
```

The `schema-enforcer ansible` command validates adherence to schema on a **per host** basis. In the example above, both `spine1` and `spine2` devices belong to a group called `spine`

```ini
[nyc:children]
spine
leaf

[spine]
spine1
spine2

[leaf]
leaf1
leaf2
```

The property `dns_servers` is defined only at the `spine` group level in ansible and not at the host level. Below is the `spine.yml` group_vars file.

```yaml
cat group_vars/spine.yaml
---
dns_servers:
  - address: true
  - address: "10.2.2.2"
interfaces:
  swp1:
    role: "uplink"
  swp2:
    role: "uplink"

schema_enforcer_schema_ids:
  - "schemas/dns_servers"
  - "schemas/interfaces"
```

Though the invalid property (the boolean true for a DNS address) is defined only once, two validation errors are flagged because two different hosts belong to to the `spine` group.

## Command Arguments

### The `--show-checks` flag

The `--show-checks` flag is used to show which ansible inventory hosts will be validated against which schema definition IDs.

```cli
Found 4 hosts in the inventory
Ansible Host              Schema ID
--------------------------------------------------------------------------------
leaf1                     ['schemas/dns_servers']
leaf2                     ['schemas/dns_servers']
spine1                    ['schemas/dns_servers', 'schemas/interfaces']
spine2                    ['schemas/dns_servers', 'schemas/interfaces']
```

> Note: The ansible inventory hosts can be mapped to schema definition ids in one of a few ways. This is discussed in the Schema Mapping section below

### The `--show-pass` flag

The `--show-pass` flag is used to show what schema definition ids each host passes in addition to the schema definition ids each host fails.

```cli
bash$ schema-enforcer ansible --show-pass  
Found 4 hosts in the inventory
FAIL | [ERROR] True is not of type 'string' [HOST] spine1 [PROPERTY] dns_servers:0:address
PASS | [HOST] spine1 [SCHEMA ID] schemas/interfaces
FAIL | [ERROR] True is not of type 'string' [HOST] spine2 [PROPERTY] dns_servers:0:address
PASS | [HOST] spine2 [SCHEMA ID] schemas/interfaces
PASS | [HOST] leaf1 [SCHEMA ID] schemas/dns_servers
PASS | [HOST] leaf2 [SCHEMA ID] schemas/dns_servers
```

In the above example, the leaf switches are checked for adherence to the `schemas/dns_servers` definition and the spine switches are checked for adherence to two schema ids; the `schemas/dns_servers` schema id and the `schemas/interfaces` schema id. A PASS statement is printed to stdout for each validation that passes and a FAIL statement is printed for each validation that fails.

### The `--host` flag

The `--host` flag can be used to limit schema validation to a single ansible inventory host. `-h` can also be used as shorthand for `--host`

```cli
bash$ schema-enforcer ansible -h spine2 --show-pass  
Found 4 hosts in the inventory
FAIL | [ERROR] True is not of type 'string' [HOST] spine2 [PROPERTY] dns_servers:0:address
PASS | [HOST] spine2 [SCHEMA ID] schemas/interfaces
```

### The `--inventory` flag

The `--inventory` flag (or `-i`) specifies the inventory file which should be used to determine the ansible inventory. The inventory file can be specified in one of two ways:

1) The `--inventory` flag (or `-i`) can be used to pass in the location of an ansible inventory file
2) A `pyproject.toml` file can contain a `[tool.schema_enforcer]` config block setting the `ansible_inventory` paramer. This `pyproject.toml` file must be inside the repository from which the tool is run.

```toml
bash$ cat pyproject.toml
[tool.schema_enforcer]
ansible_inventory = "inventory.ini"
```

If the inventory is set in both ways, the -i flag will take precedence.

> Note: Dynamic inventory sources can not currently be parsed for schema adherence.

## Inventory Variables and Schema Mapping

`schema-enforcer` will check ansible hosts for adherence to defined schema ids in one of two ways.

- By using a list of schema ids defined by the `schema_enforcer_schema_ids` command
- By automatically mapping a schema's top level property to ansible variable keys.

### Using The `schema_enforcer_schema_ids` ansible inventory variable

This variable can be used to declare which schemas a given host/group of hosts should be checked for adherence to. The value of this variable is a list of the schema ids.

Take for example the `spine` group in our `ansible` exmple. In this example, the schema ids `schemas/dns_servers` and `schemas/interfaces` are declared.

```yaml
bash$ cat group_vars/spine.yml
---
dns_servers:
  - address: true
  - address: "10.2.2.2"
interfaces:
  swp1:
    role: "uplink"
  swp2:
    role: "uplink"

schema_enforcer_schema_ids:
  - "schemas/dns_servers"
  - "schemas/interfaces"
```

The `$id` property in the following schema definition file is what is being declared by spine group var file above.

```yaml
bash$ cat schema/schemas/interfaces.yml
---
$schema: "http://json-schema.org/draft-07/schema#"
$id: "schemas/interfaces"
description: "Interfaces configuration schema."
type: "object"
properties:
  interfaces:
    type: "object"
    patternProperties:
      ^swp.*$:
        properties:
          type:
            type: "string"
          description:
            type: "string"
          role:
            type: "string"
```

### Using the `schema_enforcer_automap_default` ansible inventory variable

This variable specifies whether or not to use automapping. It defaults to true. When automapping is in use, schema enforcer will automatically map schema IDs to host variables if the variable's name matches a top level property defined in the schema. This happens by default when no `schema_enforcer_schema_ids` property is declared.

The leaf group in the included ansible example does not declare any schemas per the `schema_enforcer_schema_ids` property. 

```yaml
bash$ cat group_vars/leaf.yml
---
dns_servers:
  - address: "10.1.1.1"
  - address: "10.2.2.2"
```

Yet when schema enforcer is run against one of the leaf hosts, we can see it's host vars are checked for adherence to the dns_servers.yml schema.

```cli
schema-enforcer ansible -h leaf1 --show-pass
Found 4 hosts in the inventory
PASS | [HOST] leaf1 [SCHEMA ID] schemas/dns_servers
ALL SCHEMA VALIDATION CHECKS PASSED
```

This is done because `schema-enforcer` maps the `dns_servers` key in the `group_vars/leaf.yml` to the `dns_servers` top level property in the `schema/schemas/dns.yml` schema definition file.

```yaml
cat schema/schemas/dns.yml   
---
$schema: "http://json-schema.org/draft-07/schema#"
$id: "schemas/dns_servers"
description: "DNS Server Configuration schema."
type: "object"
properties:
  dns_servers:
    $ref: "../definitions/arrays/ip.yml#ipv4_hosts"
required:
  - "dns_servers"
```

> Note: The order listed above is the order in which the options for mapping schema ids to variables occurs.
> Note: Schema ID to host property mapping methods are **mutually exclusive**. This means that if a `schema_definition_schema_ids` variable is declared in an ansible hosts/groups file, automatic mapping of schema IDs to variables will not occur.

The `schema_enforcer_automap_default` variable can be declared in an ansible host or group file. This variable defaults to true if not set. If set to false, the automapping behaviour described above will not occur. For instance, if we change the `schema_enforcer_automap_default` variable for leaf switches to false then re-run schema validation, no checks will be performed because automapping is disabled.

```yaml
bash$ cat group_vars/leaf.yml
---
dns_servers:
  - address: "10.1.1.1"
  - address: "10.2.2.2"

schema_enforcer_automap_default: false
```

```yaml
bash$ schema-enforcer ansible -h leaf1 --show-checks
Found 4 hosts in the inventory
Ansible Host              Schema ID
--------------------------------------------------------------------------------
leaf1                     []
```

## Advanced Options

### The `schema_enforcer_strict` variable

The `schema_enforcer_strict` variable can be declared in an ansible host or group file. This variable defaults to false if not set. If set to true, the `schema-enforcer` tool checks for `strict` adherence to schema. This means that no additional host vars can exist beyond those that are defined in the schema.

From a design pattern perspective, when strict enforcment is used, all host variables are evaulated against a single schema id. This is in contrast to a design patern where a different schema id is defined for each top level host var/property. To this end, when strict enforcement is used, a single schema should be defined with references to schemas for all properties which are defined for a given host. The ids for such schema definitions are better named by role instead of host variable. For instance `schemas/spines` or `schemas/leafs` makes more sense with this design pattern than `schemas/dns_servers`.

Two major caveats apply to using the `schema_enforcer_strict` variable.

1) If the `schema_enforcer_strict` variable is set to true, the `schema_enforcer_schema_ids` variabe **MUST** be defined as a list of one and only one schema ID. If it is either not defined at all or defined as something other than a list with one element, an error will be printed to the screen and the tool will exit before performing any validations.
2) The schema ID referenced by `schema_enforcer_schema_ids` **MUST** include all variables defined for the ansible host/group. If an ansible variable not defined in the schema is defined for a given host, schema validation will fail as, when strict mode is run, properties not defined in the schema are not allowed.

> Note: If either of these conditions are not met, an error message will be printed to stdout and the tool will stop execution before evaluating host variables against schema.

In the following example, the `spine.yml` ansible group has been defined to use strict enforcement in checking against the `schemas/spine` schema ID.

```yaml
bash$ cd examples/ansible2 && cat group_vars/spine.yml
---
dns_servers:
  - address: "10.1.1.1"
  - address: "10.2.2.2"
interfaces:
  swp1:
    role: "uplink"
  swp2:
    role: "uplink"

schema_enforcer_strict: true
schema_enforcer_schema_ids:
  - schemas/spines
```

The `schemas/spines` schema definition includes two properties -- dns_servers and interfaces. Both of these properties are required by the schema.

```yaml
---
$schema: "http://json-schema.org/draft-07/schema#"
$id: "schemas/spines"
description: "Spine Switches Schema"
type: "object"
properties:
  dns_servers:
    type: object
    $ref: "../definitions/arrays/ip.yml#ipv4_hosts"
  interfaces:
    type: "object"
    patternProperties:
      ^swp.*$:
        properties:
          type:
            type: "string"
          description:
            type: "string"
          role:
            type: "string"
required:
  - dns_servers
  - interfaces
```

When `schema-enforcer` is run, it shows checks passing as expected

```cli
bash$ schema-enforcer ansible -h spine1 --show-pass
Found 4 hosts in the inventory
PASS | [HOST] spine1 [SCHEMA ID] schemas/spines
ALL SCHEMA VALIDATION CHECKS PASSED
```

If we add another property to the spine switches group, we see that spine1 fails validation. This is because properties outside of the purview of those defined by the schema are not allowed when `schema_enforcer_strict` is set to true.

```yaml
bash$ cat group_vars/spine.yml
---
dns_servers:
  - address: true
  - address: "10.2.2.2"
interfaces:
  swp1:
    role: "uplink"
  swp2:
    role: "uplink"
bogus_property: true

schema_enforcer_schema_ids:
  - "schemas/dns_servers"

schema_enforcer_strict: true
```

```cli
bash$ schema-enforcer ansible -h spine1            
Found 4 hosts in the inventory
FAIL | [ERROR] Additional properties are not allowed ('bogus_property' was unexpected) [HOST] spine1 [PROPERTY]
```
