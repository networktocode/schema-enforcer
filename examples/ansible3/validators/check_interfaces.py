"""Example validator plugin."""
from schema_enforcer.schemas.validator import JmesPathModelValidation


class CheckInterface(JmesPathModelValidation):  # pylint: disable=too-few-public-methods
    """Check that each device has at least two core uplinks."""

    top_level_properties = ["interfaces"]
    id = "CheckInterface"
    model = "interfaces"
    left = "interfaces.*[@.type=='core'][] | length([?@])"
    right = 2
    operator = "gte"
    error = "Less than two core interfaces"
