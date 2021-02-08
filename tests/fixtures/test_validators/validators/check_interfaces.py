# flake8: noqa
# pylint: skip-file
class CheckInterface(JmesPathModelValidation):
    model = "interfaces"
    left = "interfaces.*[@.type=='core'][] | length([?@])"
    right = 2
    operator = "eq"
