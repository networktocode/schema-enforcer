"""Unit tests for cli.py when ansible is installed"""
from click.testing import CliRunner

from schema_enforcer import cli


def test_ansible_import_when_exists():
    """Tests ansible command exits when ansible is installed on the host system but message indicates the exit is because 'No schemas were loaded'."""
    runner = CliRunner()
    raised_error = runner.invoke(cli.ansible, ["--show-checks"])
    # For whatever reason, the raised error does not exactly match SystemExit(1). The diff output by pylint shows no
    # differences between the objects name or type, so the assertion converts to string before matching as this
    # effectively accomplishes the same thing.
    assert str(raised_error.exception) == str(SystemExit(1))
    assert raised_error.exit_code == 1
    assert raised_error.output == "\x1b[31m  ERROR |\x1b[0m No schemas were loaded\n"
