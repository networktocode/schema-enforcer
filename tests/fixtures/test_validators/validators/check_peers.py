"""Test validator for ModelValidation class"""
from schema_enforcer.schemas.validator import BaseValidation


def ansible_hostname(hostname: str):
    """Convert hostname to ansible format"""
    return hostname.replace("-", "_")


def normal_hostname(hostname: str):
    """Convert ansible hostname to normal format"""
    return hostname.replace("_", "-")


class CheckPeers(BaseValidation):  # pylint: disable=too-few-public-methods
    """
    Validate that peer and peer_int are defined properly on both sides of a connection

    Requires full Ansible host_vars as data which is currently unsupported in schema-enforcer
    """

    id = "CheckPeers"
    top_level_properties = set()

    def validate(self, data: dict, strict: bool):
        for host in data:
            for interface, int_cfg in data[host]["interfaces"].items():
                if "peer" not in int_cfg:
                    continue
                peer = int_cfg["peer"]
                if "peer_int" not in int_cfg:
                    self.add_validation_error("Peer interface is not defined")
                    continue
                peer_int = int_cfg["peer_int"]
                peer = ansible_hostname(peer)
                if peer not in data:
                    continue
                peer_match = data[peer]["interfaces"][peer_int]["peer"] == normal_hostname(host)
                peer_int_match = data[peer]["interfaces"][peer_int]["peer_int"] == interface
                if peer_match and peer_int_match:
                    self.add_validation_pass()
                else:
                    self.add_validation_error("Peer information does not match.")
