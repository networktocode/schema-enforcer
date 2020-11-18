# The `validate` command

The `validate` command is used to check structured data files for adherence to json schema definitions. Inside of examples/example1 exists a basic hierarchy of directories. With no flags passed in, this tool will display a line per each property definition that **FAILs** schema validation, along with contextual information regarding the error message (e.g. why the property failed validation), the file in which the property failing validation is defined, and the property that is failing validation. If all checks pass, it will inform the tool user that all tests have passed.

In addition to printing these messages, the tool *intentionally exits with an error code of 1*. This is done so that the tool can be used in a pipeline or a script and fail the pipeline/script so that further execution is not performed if schema validations do not pass. If some tool is consuming YAML data, for instance, you would want to make sure that YAML data is schema valid before passing it into the tool to ensure downstream failures because data does not adhere to schema do not occur.

If multiple schema validation errors occur in the same file, both errors will be printed to stdout on their own line. This was done in the spirit of a tool like pylint, which informs you of all errors for a given file so that you can correct them before re-running the tool.

```cli
bash$ cd examples/example1 && test-schema validate
FAIL | [ERROR] 123 is not of type 'string' [FILE] ./hostvars/fail-tests/ntp.yml [PROPERTY] ntp_servers:1:vrf
FAIL | [ERROR] Additional properties are not allowed ('test_extra_property' was unexpected) [FILE] ./hostvars/fail-tests/ntp.yml [PROPERTY]
```

The default behaviour of the `validate` command can be modified by passing in one of a few flags.

#### The `--show-checks` flag

The `--show-checks` flag is used to show which instance files will be validated against which schema validations.

```cli
bash$ cd examples/example1 && test-schema validate --show-checks
Instance File                                     Schema
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
./inventory/group_vars/all.yml                     []
./inventory/group_vars/apac.yml                    []
./inventory/group_vars/emea.yml                    []
./inventory/group_vars/lax.yml                     []
./inventory/group_vars/na.yml                      []
./inventory/group_vars/nyc.yml                     []
```

> The instance file can be mapped to schema definitions in one of a few ways. By default the top level property in an instance file is mapped to the top level property in a schema definition. File names can also be mapped to schema definitions by using a `[tool.jsonschema_testing.schema_mapping]` configuration block in a pyproject.toml file, or a decorator at the type of a file in the form of `# jsonschema_testing: <schema_id>` can be used. See the [README.md in examples/example2](https://github.com/networktocode-llc/jsonschema_testing/tree/master/examplesexamples/example2) for more information on the configuration options that are available as well as detailed examples.

#### The `--show-pass` flag

By default, only files which fail schema validation are printed to stdout. If you would like to see files which pass schema validation as well as those that fail, you can pass in the `--show-pass` flag.

```cli
bash$ cd examples/example1 && test-schema validate --show-pass                           
PASS [FILE] ./hostvars/eng-london-rt1/ntp.yml
PASS [FILE] ./hostvars/eng-london-rt1/dns.yml
PASS [FILE] ./hostvars/chi-beijing-rt1/syslog.yml
PASS [FILE] ./hostvars/chi-beijing-rt1/dns.yml
PASS [FILE] ./hostvars/usa-lax-rt1/syslog.yml
PASS [FILE] ./hostvars/usa-lax-rt1/dns.yml
PASS [FILE] ./hostvars/ger-berlin-rt1/dns.yml
PASS [FILE] ./hostvars/usa-nyc-rt1/syslog.yml
PASS [FILE] ./hostvars/usa-nyc-rt1/dns.yml
PASS [FILE] ./hostvars/mex-mxc-rt1/syslog.yml
PASS [FILE] ./hostvars/mex-mxc-rt1/dns.yml
FAIL | [ERROR] 123 is not of type 'string' [FILE] ./hostvars/fail-tests/ntp.yml [PROPERTY] ntp_servers:1:vrf
FAIL | [ERROR] Additional properties are not allowed ('test_extra_property' was unexpected) [FILE] ./hostvars/fail-tests/ntp.yml [PROPERTY] 
PASS [FILE] ./hostvars/fail-tests/dns.yml
```

#### The `--strict` flag

By default, schema validations are done in a "non-strict" manner. In effect, this means that extra properties are allowed at every level of a schema definition unless the `additionalProperties` key is explicitly set to false for the JSONSchema property. Running the validate command with the `--strict` flag ensures that, if not explicitly set to allowed, additionalProperties are disallowed and instance files with additional properties will fail schema validation.

```cli
bash$ cd examples/example1 && test-schema validate --strict   
FAIL | [ERROR] 123 is not of type 'string' [FILE] ./hostvars/fail-tests/ntp.yml [PROPERTY] ntp_servers:1:vrf
FAIL | [ERROR] Additional properties are not allowed ('test_extra_item_property' was unexpected) [FILE] ./hostvars/fail-tests/ntp.yml [PROPERTY] ntp_servers:1
FAIL | [ERROR] Additional properties are not allowed ('test_extra_property' was unexpected) [FILE] ./hostvars/fail-tests/ntp.yml [PROPERTY] 
FAIL | [ERROR] Additional properties are not allowed ('test_extra_property' was unexpected) [FILE] ./hostvars/fail-tests/dns.yml [PROPERTY] dns_servers:1
```

> Note: The schema definition `additionalProperties` attribute is part of JSONSchema standard definitions. More information on how to construct these definitions can be found [here](https://json-schema.org/understanding-json-schema/reference/object.html)