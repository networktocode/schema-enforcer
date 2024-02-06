"""Validate hostname is valid."""

from enum import Enum
from typing import Dict, Optional
from ipaddress import IPv4Address, IPv6Address
from pydantic import BaseModel


class InterfaceTypes(str, Enum):
    """Interface types."""

    core = "core"


class Interface(BaseModel):
    ipv4: IPv4Address
    ipv6: Optional[IPv6Address] = None
    peer: Optional[str] = None
    peer_int: Optional[str] = None
    type: Optional[InterfaceTypes] = None


class Interfaces(BaseModel):
    """Validate hostname is valid."""

    interfaces: Dict[str, Interface]
