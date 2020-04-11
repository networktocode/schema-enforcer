from ruamel.yaml import YAML


YAML_HANDLER = YAML()


def test_config_definitions_against_schema(hostname, model, validator, hostvars):
    try:
        with open(f"{hostvars}/{hostname}/{model}.yml", encoding="utf-8") as vars_file:
            validator.validate(instance=YAML_HANDLER.load(vars_file))
    except FileNotFoundError:
        pass
