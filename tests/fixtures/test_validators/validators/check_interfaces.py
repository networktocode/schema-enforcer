"""Test validator for JmesPathModelValidation class"""
from schema_enforcer.schemas.validator import JmesPathModelValidation


class CheckInterface(JmesPathModelValidation):  # pylint: disable=too-few-public-methods
    """Test validator for JmesPathModelValidation class"""

    def __init__(self):
        super().__init__()
        self.top_level_properties = ["interfaces"]
        self.id = "CheckInterface"  # pylint: disable=invalid-name
        self.left = "interfaces.*[@.type=='core'][] | length([?@])"
        self.right = 2
        self.operator = "gte"
        self.error = "Less than two core interfaces"
