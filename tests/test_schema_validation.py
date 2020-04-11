import os
import json
from ruamel.yaml import YAML
from collections import deque  # noqa F401

import pytest
from jsonschema.exceptions import ValidationError


YAML_HANDLER = YAML()


def build_deque_path(path):
    path_formatted = [
        f"'{entry}'" if isinstance(entry, str) else str(entry) for entry in path
    ]
    return f"deque([{', '.join(path_formatted)}])"


def test_schema_valid_mock_data_exists(valid_mock_dir):
    assert os.listdir(valid_mock_dir)


def test_schema_invalid_mock_data_exists(invalid_mock_dir):
    assert os.listdir(invalid_mock_dir)


def test_schema_against_valid_mock_data(model, validator, valid_mock):
    with open(f"tests/mocks/{model}/valid/{valid_mock}.json", encoding="utf-8") as fh:
        validator.validate(instance=json.load(fh))


def test_schema_against_invalid_mock_data(model, validator, invalid_mock):
    mock_path = f"tests/mocks/{model}/invalid/{invalid_mock}"
    mock_data = f"{mock_path}.json"
    mock_errors = f"{mock_path}.yml"
    with pytest.raises(ValidationError) as invalid, open(mock_data) as fh:  # noqa F841
        validator.validate(instance=json.load(fh))

    with open(mock_errors) as fh:
        errors = YAML_HANDLER.load(fh)

    for attribute, expected in errors.items():
        actual = getattr(invalid.value, attribute)
        assert str(actual) == expected
