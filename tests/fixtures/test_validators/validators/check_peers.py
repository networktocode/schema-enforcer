# flake8: noqa
# pylint: skip-file
def ansible_hostname(hostname: str):
    return hostname.replace("-", "_")


def normal_hostname(hostname: str):
    return hostname.replace("_", "-")


class CheckPeers(ModelValidation):
    """
    Validate that peer and peer_int are defined properly on both sides of a connection

    Requires full Ansible host_vars as data
    """

    def validate(cls, data: dict):
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
                                raise ValidationError
                    # If peer is defined, peer_int must also exist
                    else:
                        raise ValidationError
