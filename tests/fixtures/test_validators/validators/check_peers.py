"""Test validator for ModelValidation class"""
from typing import Iterable
from schema_enforcer.schemas.validator import ModelValidation
from schema_enforcer.validation import ValidationResult


def ansible_hostname(hostname: str):
    """Convert hostname to ansible format"""
    return hostname.replace("-", "_")


def normal_hostname(hostname: str):
    """Convert ansible hostname to normal format"""
    return hostname.replace("_", "-")


class CheckPeers(ModelValidation):  # pylint: disable=too-few-public-methods
    """
    Validate that peer and peer_int are defined properly on both sides of a connection

    Requires full Ansible host_vars as data which is currently unsupported in schema-enforcer
    """

    id = "CheckPeers"

    @classmethod
    def validate(cls, data: dict, strict: bool) -> Iterable[ValidationResult]:
        results = list()
        for host in data:
            for interface, int_cfg in data[host]["interfaces"].items():
                if "peer" not in int_cfg:
                    continue
                peer = int_cfg["peer"]
                if "peer_int" not in int_cfg:
                    results.append(
                        ValidationResult(
                            result="FAIL",
                            schema_id=cls.id,
                            message="Peer interface is not defined",
                            instance_hostname=host,
                            instance_name=peer,
                        )
                    )
                    continue
                peer_int = int_cfg["peer_int"]
                peer = ansible_hostname(peer)
                if peer not in data:
                    continue
                peer_match = data[peer]["interfaces"][peer_int]["peer"] == normal_hostname(host)
                peer_int_match = data[peer]["interfaces"][peer_int]["peer_int"] == interface
                if peer_match and peer_int_match:
                    results.append(
                        ValidationResult(result="PASS", schema_id=cls.id, instance_hostname=host, instance_name=peer)
                    )
                else:
                    results.append(
                        ValidationResult(
                            result="FAIL",
                            schema_id=cls.id,
                            message="Peer information does not match.",
                            instance_hostname=host,
                            instance_name=peer,
                        )
                    )
        return results
