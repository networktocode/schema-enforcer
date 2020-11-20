# The `validate` command

The `schema-enforcer validate` command is used to check structured data files for adherence to schema definitions. Inside of examples/example3 exists a basic hierarchy of directories. With no flags passed in, this tool will display a line per each property definition that **fails** schema validation along with contextual information elucidating why a given portion of the structured data failed schema validation, the file in which the structured data failing validation is defined, and the portion of structured data that is failing validation. If all checks pass, `schema-enforcer` will inform the user that all tests have passed.

```cli
bash$ cd examples/example3 && schema-enforcer validate
FAIL | [ERROR] 123 is not of type 'string' [FILE] ./hostvars/fail-tests/ntp.yml [PROPERTY] ntp_servers:1:vrf
FAIL | [ERROR] Additional properties are not allowed ('test_extra_property' was unexpected) [FILE] ./hostvars/fail-tests/ntp.yml [PROPERTY]
```

In addition to printing these messages, `schema-enforcer` *intentionally exits with an error code of 1*. This is done so that the tool can be used in a pipeline or a script and fail the pipeline/script so that further execution is not performed if schema validations do not pass. As an example, if some tool is consuming YAML data you may want to make sure that YAML data is schema valid before passing it into the tool to ensure downstream failures do not occur because the data it's consuming is not a valid input.

If multiple schema validation errors occur in the same file, all errors will be printed to stdout on their own line. This was done in the spirit of a tool like pylint, which informs the user of all errors for a given file so that the user can correct them before re-running the tool.

The default behaviour of the `schema-enforcer validate` command can be modified by passing in one of a few flags.

#### The `--show-checks` flag

The `--show-checks` flag is used to show which structured data files will be validated against which schema definition IDs.

```cli
bash$ cd examples/example3 && schema-enforcer validate --show-checks
Structured Data File                               Schema ID
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

> The structured data file can be mapped to schema definitions in one of a few ways. See the [README in docs/mapping_schemas.md](./mapping_schemas.md) for more information. The [README.md in examples/example2](../examples/example2) also contains detailed examples of schema mappings.

#### The `--show-pass` flag

By default, only portinos of data which fail schema validation are printed to stdout. If you would like to see files which pass schema validation as well as those that fail, you can pass the `--show-pass` flag into `schema-enforcer`.

```cli
bash$ cd examples/example3 && schema-enforcer validate --show-pass                      
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

By default, schema validations defined by JSONSchema are done in a "non-strict" manner. In effect, this means that extra properties are allowed at every level of a schema definition unless the `additionalProperties` key is explicitly set to false for the JSONSchema property. Running the validate command with the `--strict` flag ensures that, if not explicitly set to allowed, additionalProperties are disallowed and structued data files with additional properties will fail schema validation.

```cli
bash$ cd examples/example3 && schema-enforcer validate --strict   
FAIL | [ERROR] 123 is not of type 'string' [FILE] ./hostvars/fail-tests/ntp.yml [PROPERTY] ntp_servers:1:vrf
FAIL | [ERROR] Additional properties are not allowed ('test_extra_item_property' was unexpected) [FILE] ./hostvars/fail-tests/ntp.yml [PROPERTY] ntp_servers:1
FAIL | [ERROR] Additional properties are not allowed ('test_extra_property' was unexpected) [FILE] ./hostvars/fail-tests/ntp.yml [PROPERTY] 
FAIL | [ERROR] Additional properties are not allowed ('test_extra_property' was unexpected) [FILE] ./hostvars/fail-tests/dns.yml [PROPERTY] dns_servers:1
```

> Note: The schema definition `additionalProperties` attribute is part of JSONSchema standard definitions. More information on how to construct these definitions can be found [here](https://json-schema.org/understanding-json-schema/reference/object.html)