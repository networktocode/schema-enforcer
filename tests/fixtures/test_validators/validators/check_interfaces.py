# flake8: noqa
# pylint: skip-file
from schema_enforcer.schemas.validator import JmesPathModelValidation


class CheckInterface(JmesPathModelValidation):
    top_level_properties = ["interfaces"]
    id = "CheckInterface"
    left = "interfaces.*[@.type=='core'][] | length([?@])"
    right = 2
    operator = "eq"
    error = "Less than two core interfaces"
