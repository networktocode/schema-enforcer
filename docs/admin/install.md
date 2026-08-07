# Installation

Option 1: Install from PyPI.

```bash
pip install schema-enforcer
```

Option 2: Manually install via Poetry.

```bash
git clone https://github.com/networktocode/schema-enforcer.git
cd schema-enforcer
curl -sSL https://install.python-poetry.org | python3 -
poetry install
```

Option 3: Install from a GitHub branch, such as develop as shown below.

```bash
pip install git+https://github.com/networktocode/schema-enforcer.git@develop
```

## Configuration Settings

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

> More information on available configuration settings can be found in the [configuration](../admin/configuration.md)

## Supported Formats

By default, schema enforcer installs the jsonschema `format_nongpl` extra (in version <1.2.0) or `format-nongpl` (in versions >=1.2.0). This extra allows the use of formats that can be used in schema definitions (e.g. ipv4, hostname...etc). The `format_nongpl` or `format-nongpl` extra only installs transitive dependencies that are not licensed under GPL. The `iri` and `iri-reference` formats are defined by the `rfc3987` transitive dependency which is licensed under GPL. As such, `iri` and `iri-reference` formats are *not* supported by `format-nongpl`/`format_nongpl`. If you have a need to use `iri` and/or `iri-reference` formats, you can do so by running the following pip command (or it's poetry equivalent):

```
pip install 'jsonschema[rfc3987]'
```

See the "Validating Formats" section in the [jsonschema documentation](https://github.com/python-jsonschema/jsonschema/blob/main/docs/validate.rst) for more information.
