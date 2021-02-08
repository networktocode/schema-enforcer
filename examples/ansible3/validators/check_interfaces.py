"""Example validator plugin."""
# flake8: noqa
# pylint: skip-file
from schema_enforcer.schemas.validator import JmesPathModelValidation


class CheckInterface(JmesPathModelValidation):
    """Check that each device has at least two core uplinks."""

    top_level_properties = ["interfaces"]
    id = "CheckInterface"
    model = "interfaces"
    left = "interfaces.*[@.type=='core'][] | length([?@])"
    right = 2
    operator = "eq"
    error = "Less than two core interfaces"
