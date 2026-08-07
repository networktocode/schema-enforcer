# Implementing custom validators

With custom validators, you can implement business logic in Python. Schema-enforcer will automatically
load your plugins from the `validator_directory` and run them against your host data.

The validator plugin provides a few base classes: BaseValidation, JmesPathModelValidation, and PydanticValidation. BaseValidation can be used when you want to implement all logic, JmesPathModelValidation can be used as a shortcut for jmespath validation, and PydanticValidation will validate data against a specific Pydantic model.

## BaseValidation

Use this class to implement arbitrary validation logic in Python. In order to work correctly, your Python script must meet
the following criteria:

1. Exist in the `validator_directory` dir.
2. Include a subclass of the BaseValidation class to correctly register with schema-enforcer.
3. Ensure you call `super().__init__()` in your class `__init__` if you override.
4. Provide a class method in your subclass with the following signature:
`def validate(data: dict, strict: bool):`

   * Data is a dictionary of variables on a per-host basis.
   * Strict is set to true when the strict flag is set via the CLI. You can use this to offer strict validation behavior
   or ignore it if not needed.

The name of your class will be used as the schema-id for mapping purposes. You can override the default schema ID
by providing a class-level `id` variable.

Helper functions are provided to add pass/fail results:

```python
def add_validation_error(self, message: str, **kwargs):
    """Add validator error to results.
    Args:
      message (str): error message
      kwargs (optional): additional arguments to add to ValidationResult when required
    """

def add_validation_pass(self, **kwargs):
    """Add validator pass to results.
    Args:
      kwargs (optional): additional arguments to add to ValidationResult when required
    """
```

In most cases, you will not need to provide kwargs. However, if you find a use case that requires updating other fields
in the ValidationResult, you can send the key/value pairs to update the result directly. This is for advanced users only.

## JmesPathModelValidation

Use this class for basic validation using [jmespath](https://jmespath.org/) expressions to query specific values in your data. In order to work correctly, your Python script must meet
the following criteria:

1. Exist in the `validator_directory` dir.
2. Include a subclass of the JmesPathModelValidation class to correctly register with schema-enforcer.
3. Provide the following class level variables:

   * `top_level_properties`: Field for mapping of validator to data
   * `id`: Schema ID to use for reporting purposes (optional - defaults to class name)
   * `left`: Jmespath expression to query your host data
   * `right`: Value or a compiled jmespath expression
   * `operator`: Operator to use for comparison between left and right hand side of expression
   * `error`: Message to report when validation fails

### Supported operators

The class provides the following operators for basic use cases:

```
"gt": int(left) > int(right),
"gte": int(left) >= int(right),
"eq": left == right,
"lt": int(left) < int(right),
"lte": int(left) <= int(right),
"contains": right in left,
```

If you require additional logic or need to compare other types, use the BaseValidation class and create your own validate method.

### Examples

#### Basic

```python
from schema_enforcer.schemas.validator import JmesPathModelValidation

class CheckInterface(JmesPathModelValidation):  # pylint: disable=too-few-public-methods
    top_level_properties = ["interfaces"]
    id = "CheckInterface"  # pylint: disable=invalid-name
    left = "interfaces.*[@.type=='core'][] | length([?@])"
    right = 2
    operator = "gte"
    error = "Less than two core interfaces"
```

#### With compiled jmespath expression

```python
import jmespath
from schema_enforcer.schemas.validator import JmesPathModelValidation


class CheckInterfaceIPv4(JmesPathModelValidation):  # pylint: disable=too-few-public-methods
    top_level_properties = ["interfaces"]
    id = "CheckInterfaceIPv4"  # pylint: disable=invalid-name
    left = "interfaces.*[@.type=='core'][] | length([?@])"
    right = jmespath.compile("interfaces.* | length([?@.type=='core'][].ipv4)")
    operator = "eq"
    error = "All core interfaces do not have IPv4 addresses"
```

## PydanticValidation

Schema Enforcer supports utilizing Pydantic models for validation. Pydantic models can be loaded two different ways.

1. Store your models in your `validator_directory`.
2. Load from a separate library using the `schema_enforcer.schemas.PydanticManager`. These must be defined within the `schema_enforcer` configuration file.
   1. `pydantic_validators` requires a list of library paths to a `PydanticManager` instance.

Both methods will replace the Pydantic `BaseModel` with the `PydanticValidation` class that provides the required `validate` method that uses the `model_validate` method to validate data. The model is set to the original Pydantic model to validate data against.

### Pydantic Models in External Libraries

```python
class PydanticValidation(BaseValidation):
    """Basic wrapper for Pydantic models to be used as validators."""

    model: BaseModel

    def validate(self, data: dict, strict: bool = False):
        """Validate data against Pydantic model.

        Args:
            data (dict): variables to be validated by validator
            strict (bool): true when --strict cli option is used to request strict validation (if provided)

        Returns:
            None

        Use add_validation_error and add_validation_pass to report results.
        """
        try:
            self.model.model_validate(data, strict=strict)
            self.add_validation_pass()
        except ValidationError as err:
            self.add_validation_error(str(err))
```

### Pydantic Models in Validators Directory

The Pydantic models can be located in any Python file within this directory (new or existing). The only requirement is these are valid Pydantic `BaseModel` subclasses.

These will be loaded and can be referenced by their class name. For example, `CheckHostname` will show up as `CheckHostname`.

```python
"""Validate hostname is valid."""
from pydantic import BaseModel


class CheckHostname(BaseModel):
    """Validate hostname is valid."""

    hostname: str
```

```yaml
# jsonschema: Hostname
---
hostname: "az-phx-rtr01"
```

### Load from External Library

As an example, we will look at models that are within our `my_custom_pydantic_models.manager`. If a **prefix** is defined, you can reference the validators like `f"{prefix}/{model.__name__}`.

```python
"""Load our models to be used for Schema Enforcer."""
from pydantic import BaseModel
from schema_enforcer.schemas.manager import PydanticManager


class Hostname(BaseModel):
    hostname: str = Field(pattern="^[a-z]{2}-[a-z]{3}-[a-z]{1,2}[0-9]{2}$")


# Prefix is optional and will default to a blank string, aka no prefix.
# Models is required to pass in custom Pydantic models.
manager = PydanticManager(prefix="custom", models=[Hostname])
```

```toml
[tool.schema_enforcer]
pydantic_validators = [
  "my_custom_pydantic_models.manager"
]
```

An example YAML file schema correlation would look like:

```yaml
# jsonschema: custom/Hostname
---
hostname: "az-phx-pe01"
```

## Running validators

Custom validators are run with `schema-enforcer validate` and `schema-enforcer ansible` commands.

You map validators to keys in your data with `top_level_properties` in your subclass or with `schema_enforcer_schema_ids`
in your data. Schema-enforcer uses the same process to map custom validators and schemas. Refer to the "Mapping Schemas" documentation
for more details.

### Example - top_level_properties

The CheckInterface validator has a top_level_properties of "interfaces":

```
class CheckInterface(JmesPathModelValidation):  # pylint: disable=too-few-public-methods
    top_level_properties = ["interfaces"]
```

With automapping enabled, this validator will apply to any host with a top-level `interfaces` key in the Ansible host_vars data:

```
---
hostname: "az-phx-pe01"
pair_rtr: "az-phx-pe02"
interfaces:
  MgmtEth0/0/CPU0/0:
    ipv4: "172.16.1.1"
  Loopback0:
    ipv4: "192.168.1.1"
    ipv6: "2001:db8:1::1"
  GigabitEthernet0/0/0/0:
    ipv4: "10.1.0.1"
    ipv6: "2001:db8::"
    peer: "az-phx-pe02"
    peer_int: "GigabitEthernet0/0/0/0"
    type: "core"
  GigabitEthernet0/0/0/1:
    ipv4: "10.1.0.37"
    ipv6: "2001:db8::12"
    peer: "co-den-p01"
    peer_int: "GigabitEthernet0/0/0/2"
    type: "core"
```

### Example - manual mapping

Alternatively, you can manually map a validator in your Ansible host vars or other data files.

```
schema_enforcer_automap_default: false
schema_enforcer_schema_ids:
  - "CheckInterface"
```
