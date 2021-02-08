class CheckInterface(JmesPathModelValidation):  # noqa: F821
    top_level_properties = ["interfaces"]
    id = "CheckInterface"
    model = "interfaces"
    left = "interfaces.*[@.type=='core'][] | length([?@])"
    right = 2
    operator = "eq"
    error = "Less than two core interfaces"
