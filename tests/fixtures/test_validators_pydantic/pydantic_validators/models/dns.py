"""Validate DNS servers is valid."""

from typing import List
from pydantic import BaseModel, Field
from pydantic.networks import IPvAnyAddress


class Dns(BaseModel):
    """Validate DNS is valid."""

    dns_servers: List[IPvAnyAddress] = Field(description="DNS servers")
