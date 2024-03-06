"""Validate interfaces are valid."""

from enum import Enum
from typing import Dict, Optional
from ipaddress import IPv4Address, IPv6Address
from pydantic import BaseModel


class InterfaceTypes(str, Enum):
    """Interface types."""

    access = "access"
    core = "core"


class Interface(BaseModel):
    ipv4: Optional[IPv4Address] = None
    ipv6: Optional[IPv6Address] = None
    peer: Optional[str] = None
    peer_int: Optional[str] = None
    type: Optional[InterfaceTypes] = None


class Interfaces(BaseModel):
    """Validate interfaces are valid."""

    interfaces: Dict[str, Interface]
