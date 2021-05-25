# Changelog

## v1.1.0 - 2021-05-25

### Adds

- [Custom Validators](docs/custom_validators.md)
- [Automatic mapping of schemas to data files](docs/mapping_data_files_to_schemas.md)
- Automatic implementation of draft7 format checker to support [IPv4 and IPv6 format declarations](https://json-schema.org/understanding-json-schema/reference/string.html#id12) in a JSON Schema definition [#94](https://github.com/networktocode/schema-enforcer/issues/94)

### Changes

- Removes Ansible as a mandatory dependency [#90](https://github.com/networktocode/schema-enforcer/issues/90)
- `docs/mapping_schemas.md` renamed to `docs/mapping_data_files_to_schemas.md`
- Simplifies the invoke tasks used for development
- Schema enforcer now exits if an invalid schema is found while loading schemas [#99](https://github.com/networktocode/schema-enforcer/issues/99)

## v1.0.0 - 2021-01-26

Schema Enforcer Initial Release
