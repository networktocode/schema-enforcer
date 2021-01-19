# """Unit tests for cli.py"""
# import pytest
# from click.testing import CliRunner

# from schema_enforcer import cli

# def test_ansible_import(capsys):
#     """Tests ansible command exits when ansible is not installed on the host system."""
#     runner = CliRunner()
#     with pytest.raises(SystemExit) as fuck_you:
#         runner.invoke(cli.ansible, ["--show-checks"])
#     assert fuck_you.value.code == 1
#     captured = capsys.readouterr()
#     print(captured)


#     # assert pytest_wrapped_exit.type == SystemExit
#     # assert pytest_wrapped_exit.value.code == 1
#     assert "ansible package not found, you can run the command 'pip install schema-enforcer[ansible]' to install the latest schema-enforcer sanctioned version." in captured.out
