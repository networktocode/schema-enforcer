# Mapping Schemas

## Overview
In order to validate structured data files against schema definitions, `schema-enforcer` must have a way of mapping structured data files to the schema definition they shoudl adhere to. This is done in one of three ways:

1) By default, the top level key in a given structured data file is mapped to the top level key in a schema definition. When these keys match, `schema-enforcer` checks the structured data for compliance against the defined schema based on this correlation
2) The pyproject.toml file can map structured data filenames to the schema ID to which they should adhere.
3) Any file containing structured data can be decorated with a comment which instructs `schema-enforcer` to check the file for compliance against the a defined schema.

# Mapping of schema instance file name to a list of schemas which should be used to validate data in the instance file

In the pyproject.toml file, a `tools.schema_enforcer.schema_mapping` section can be defined which maps structured data files to schema IDs.

```toml
[tools.schema_enforcer.schema_mapping]
'dns_v1.yml' = ['schemas/dns_servers']
'dns_v2.yml' = ['schemas/dns_servers_v2']
```

The values above are key/value pairs defined in TOML. The key is a string of the structured data filename, the value is a list of schema IDs. The schema_id can be found by looking at the schem 