"""Test validator for JmesPathModelValidation class"""
import jmespath
from schema_enforcer.schemas.validator import JmesPathModelValidation


class CheckInterfaceIPv4(JmesPathModelValidation):  # pylint: disable=too-few-public-methods
    """Test validator for JmesPathModelValidation class"""

    def __init__(self):
        super().__init__()
        self.top_level_properties = ["interfaces"]
        self.id = "CheckInterfaceIPv4"
        self.left = "interfaces.*[@.type=='core'][] | length([?@])"
        self.right = jmespath.compile("interfaces.* | length([?@.type=='core'][].ipv4)")
        self.operator = "eq"
        self.error = "All core interfaces do not have IPv4 addresses"
