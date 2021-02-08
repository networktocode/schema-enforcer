# flake8: noqa
# pylint: skip-file
from typing import Iterable
from schema_enforcer.schemas.validator import ModelValidation
from schema_enforcer.validation import ValidationResult


def ansible_hostname(hostname: str):
    return hostname.replace("-", "_")


def normal_hostname(hostname: str):
    return hostname.replace("_", "-")


class CheckPeers(ModelValidation):
    """
    Validate that peer and peer_int are defined properly on both sides of a connection

    Requires full Ansible host_vars as data
    """

    id = "CheckPeers"

    @classmethod
    def validate(cls, data: dict, strict: bool) -> Iterable[ValidationResult]:
        results = list()
        for host in data:
            for interface, int_cfg in data[host]["interfaces"].items():
                peer = int_cfg.get("peer", None)
                if peer:
                    peer_int = int_cfg.get("peer_int", None)
                    if peer_int:
                        peer = ansible_hostname(peer)
                        # Only validate if peer exists in data
                        if peer in data:
                            peer_match = data[peer]["interfaces"][peer_int]["peer"] == normal_hostname(host)
                            peer_int_match = data[peer]["interfaces"][peer_int]["peer_int"] == interface
                            if not (peer_match and peer_int_match):
                                results.append(
                                    ValidationResult(
                                        result="FAIL",
                                        schema_id=cls.id,
                                        message="Peer interfaces do not match",
                                        instance_hostname=host,
                                        instance_name=peer,
                                    )
                                )
                            else:
                                results.append(
                                    ValidationResult(
                                        result="PASS", schema_id=cls.id, instance_hostname=host, instance_name=peer
                                    )
                                )
                    # If peer is defined, peer_int must also exist
                    else:
                        results.append(
                            ValidationResult(
                                result="FAIL",
                                schema_id=cls.id,
                                message="Peer interface is not defined",
                                instance_hostname=host,
                                instance_name=peer,
                            )
                        )
        return results
