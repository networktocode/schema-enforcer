"""Custom validator for BGP peer information."""
import requests

from schema_enforcer.schemas.validator import BaseValidation


class CheckARIN(BaseValidation):
    """Verify that BGP peer name matches ARIN ASN information."""

    def validate(self, data, strict):
        """Validate BGP peers for each host."""
        headers = {"Accept": "application/json"}
        for peer in data["bgp_peers"]:
            # pylint: disable=invalid-name
            r = requests.get(f"http://whois.arin.net/rest/asn/{peer['asn']}", headers=headers)
            if r.status_code != requests.codes.ok:  # pylint: disable=no-member
                self.add_validation_error(f"ARIN lookup failed for peer {peer['name']} with ASN {peer['asn']}")
                continue
            arin_info = r.json()
            arin_name = arin_info["asn"]["orgRef"]["@name"]
            if peer["name"] != arin_name:
                self.add_validation_error(
                    f"Peer name {peer['name']} for ASN {peer['asn']} does not match ARIN database: {arin_name}"
                )
            else:
                self.add_validation_pass()