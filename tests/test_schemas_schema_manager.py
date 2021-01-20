# pylint: disable=redefined-outer-name
""" Test manager.py SchemaManager class """
import os
import pytest
from schema_enforcer.schemas.manager import SchemaManager
from schema_enforcer.config import Settings

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures", "test_instances")

CONFIG = {
    "main_directory": os.path.join(FIXTURE_DIR, "schema"),
    "data_file_search_directories": [os.path.join(FIXTURE_DIR, "hostvars")],
    "schema_mapping": {"dns.yml": ["schemas/dns_servers"]},
}


@pytest.fixture
def schema_manager():
    """
    Instantiated SchemaManager class

    Returns:
        SchemaManager
    """
    schema_manager = SchemaManager(config=Settings(**CONFIG))

    return schema_manager


def test_dump(capsys, schema_manager):
    """ Test validates schema dump for all schemas when no schema-id is provided. """

    print_string = """{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "schemas/dns_servers",
  "description": "DNS Server Configuration schema.",
  "type": "object",
  "properties": {
    "dns_servers": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string"
          },
          "address": {
            "type": "string",
            "format": "ipv4"
          },
          "vrf": {
            "type": "string"
          }
        },
        "required": [
          "address"
        ]
      },
      "uniqueItems": true
    }
  },
  "required": [
    "dns_servers"
  ]
}
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "schemas/ntp",
  "description": "NTP Configuration schema.",
  "type": "object",
  "properties": {
    "ntp_servers": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string"
          },
          "address": {
            "type": "string",
            "format": "ipv4"
          },
          "vrf": {
            "type": "string"
          }
        },
        "required": [
          "address"
        ]
      },
      "uniqueItems": true
    },
    "ntp_authentication": {
      "type": "boolean"
    },
    "ntp_logging": {
      "type": "boolean"
    }
  },
  "additionalProperties": false,
  "required": [
    "ntp_servers"
  ],
  "something": "extra"
}
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "schemas/syslog_servers",
  "description": "Syslog Server Configuration schema.",
  "type": "object",
  "properties": {
    "syslog_servers": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string"
          },
          "address": {
            "type": "string",
            "format": "ipv4"
          },
          "vrf": {
            "type": "string"
          }
        },
        "required": [
          "address"
        ]
      },
      "uniqueItems": true
    }
  },
  "required": [
    "syslog_servers"
  ]
}
"""
    schema_manager.dump_schema(None)
    captured = capsys.readouterr()
    assert captured.out == print_string


def test_dump_with_id(capsys, schema_manager):
    """ Test validates schema dump for a single schema when schema-id is provided. """

    print_string = """{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "schemas/dns_servers",
  "description": "DNS Server Configuration schema.",
  "type": "object",
  "properties": {
    "dns_servers": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string"
          },
          "address": {
            "type": "string",
            "format": "ipv4"
          },
          "vrf": {
            "type": "string"
          }
        },
        "required": [
          "address"
        ]
      },
      "uniqueItems": true
    }
  },
  "required": [
    "dns_servers"
  ]
}
"""
    schema_id = "schemas/dns_servers"
    schema_manager.dump_schema(schema_id)
    captured = capsys.readouterr()
    assert captured.out == print_string
