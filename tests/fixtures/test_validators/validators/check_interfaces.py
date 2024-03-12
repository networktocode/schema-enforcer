"""Test validator for JmesPathModelValidation class"""
from schema_enforcer.schemas.validator import JmesPathModelValidation


class CheckInterface(JmesPathModelValidation):  # pylint: disable=too-few-public-methods
    """Test validator for JmesPathModelValidation class"""

    top_level_properties = {"interfaces"}
    id = "CheckInterface"  # pylint: disable=invalid-name
    left = "interfaces.*[@.type=='core'][] | length([?@])"
    right = 2
    operator = "gte"
    error = "Less than two core interfaces"
