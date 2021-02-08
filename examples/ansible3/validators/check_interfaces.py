# flake8: noqa
# pylint: skip-file
class CheckInterface(JmesPathModelValidation):
    top_level_properties = ["interfaces"]
    id = "CheckInterface"
    model = "interfaces"
    left = "interfaces.*[@.type=='core'][] | length([?@])"
    right = 2
    operator = "eq"
    error = "Less than two core interfaces"
