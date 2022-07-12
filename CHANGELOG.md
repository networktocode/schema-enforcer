# Changelog

## v1.1.4 - TBD

### Adds

- Add format_nongpl extra to jsonschema install. This ensures draft7 format checkers validate format adherence as expected while also ensuring GPL-Licenced transitive dependencies are not installed.

### Changes

- Update jsonschema version dependency so that only versions greater than 4.7 are supported.
- Update ansible version dependency so that only versions greater than 4.2 are supported. This is done to remediate CVE-2021-3583

### Removes

- Automatic support for `iri` and `iri-reference` format checkers. This was removed because these format checkers require the `rfc3987` library, which is licensed under GPL. If you require these checkers, you can manually install `rfc3987` or install this package as `jsonschema[rfc3987]`.

## v1.1.3 - 2022-05-31

### Changes

- jinja2 version dependency specification modified such that versions in the 3.x release are supported

## v1.1.2 - 2022-01-10

### Changes

- Update dependencies
- Switch from slim to full python docker base image

## v1.1.1 - 2021-12-23

### Changes

- Minor updates to documentation
- Update CI build environment to use github actions instead of Travis CI
- Update version of ruamel from 0.16 to 0.17

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
