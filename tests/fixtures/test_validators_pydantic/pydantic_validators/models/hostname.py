"""Validate hostname is valid."""

from pydantic import BaseModel, Field


class Hostname(BaseModel):
    """Validate hostname is valid."""

    hostname: str = Field(pattern=f"^[a-z]{2}-[a-z]{3}-[a-z]+-[0-9]{2}$")
