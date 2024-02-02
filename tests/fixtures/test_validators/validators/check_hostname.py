"""Validate hostname is valid."""
from pydantic import BaseModel


class CheckHostname(BaseModel):
    """Validate hostname is valid."""

    hostname: str
