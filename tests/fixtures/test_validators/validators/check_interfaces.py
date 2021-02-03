class CheckInterface(JmesPathModelValidation):  # noqa: F821
    model = "interfaces"
    left = "interfaces.*[@.type=='core'][] | length([?@])"
    right = 2
    operator = "eq"
