"""Validate interfaces are valid."""

from enum import Enum
from ipaddress import IPv4Address, IPv6Address
from typing import Dict, Optional

from pydantic import BaseModel


class InterfaceTypes(str, Enum):
    """Interface types."""

    access = "access"  # pylint: disable=invalid-name
    core = "core"  # pylint: disable=invalid-name


class Interface(BaseModel):
    """Interface Pydantic Model."""

    ipv4: Optional[IPv4Address] = None
    ipv6: Optional[IPv6Address] = None
    peer: Optional[str] = None
    peer_int: Optional[str] = None
    type: Optional[InterfaceTypes] = None


class Interfaces(BaseModel):
    """Validate interfaces are valid."""

    interfaces: Dict[str, Interface]
