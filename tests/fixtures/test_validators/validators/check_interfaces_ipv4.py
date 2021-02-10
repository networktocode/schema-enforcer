"""Test validator for JmesPathModelValidation class"""
import jmespath
from schema_enforcer.schemas.validator import JmesPathModelValidation


class CheckInterfaceIPv4(JmesPathModelValidation):  # pylint: disable=too-few-public-methods
    """Test validator for JmesPathModelValidation class"""

    top_level_properties = ["interfaces"]
    id = "CheckInterfaceIPv4"
    left = "interfaces.*[@.type=='core'][] | length([?@])"
    right = jmespath.compile("interfaces.* | length([?@.type=='core'][].ipv4)")
    operator = "eq"
    error = "All core interfaces do not have IPv4 addresses"
