"""conftest file for pytest"""
import glob
import os
from schema_enforcer.utils import load_file
from schema_enforcer.schemas.jsonschema import JsonSchema


FIXTURES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures", "test_jsonschema")
FORMAT_CHECK_ERROR_MESSAGE_MAPPING = {
    "incorrect_regex_format": "'[' is not a 'regex'",
    "incorrect_date_format": "'2021-111-28' is not a 'date'",
    "incorrect_hostname_format": "'ntc@ntc.com' is not a 'hostname'",
    "incorrect_uri_format": "'sftp//' is not a 'uri'",
    "incorrect_jsonptr_format": "'fakejsonptr' is not a 'json-pointer'",
    "incorrect_email_format": "'networktocode.code.com' is not a 'email'",
    "incorrect_ipv4_format": "'10.1.1.300' is not a 'ipv4'",
    "incorrect_ipv6_format": "'2001:00000:3238:DFE1:63:0000:0000:FEFB' is not a 'ipv6'",
    "incorrect_time_format": "'20:20:33333+00:00' is not a 'time'",
}


def pytest_generate_tests(metafunc):
    """Pytest_generate_tests prehook"""
    if metafunc.function.__name__ == "test_format_checkers":
        schema_files = glob.glob(f"{FIXTURES_DIR}/schema/schemas/incorrect_*.yml")
        schema_instances = []
        for schema_file in schema_files:
            schema_instance = JsonSchema(
                schema=load_file(schema_file),
                filename=os.path.basename(schema_file),
                root=os.path.join(FIXTURES_DIR, "schema", "schemas"),
            )
            schema_instances.append(schema_instance)

        data_files = glob.glob(f"{FIXTURES_DIR}/hostvars/spa-madrid-rt1/incorrect_*.yml")
        data_instances = []
        for data_file in data_files:
            data = load_file(data_file)
            data_instances.append(data)

        metafunc.parametrize(
            "schema_instance,data_instance, expected_error_message",
            [
                (
                    schema_instances[i],
                    data_instances[i],
                    FORMAT_CHECK_ERROR_MESSAGE_MAPPING.get(os.path.basename(schema_files[i])[:-4]),
                )
                for i in range(0, len(schema_instances))
            ],
            ids=[os.path.basename(schema_files[i])[:-4] for i in range(0, len(schema_instances))],
        )
