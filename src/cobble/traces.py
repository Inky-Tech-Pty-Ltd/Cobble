"""Stable identities for Cobble traces."""

from uuid import uuid4


def mint_trace_uri(base_uri: str = "https://cobble.link/t") -> str:
    """Mint a new trace identity independent of storage location."""
    return f"{base_uri.rstrip('/')}/{uuid4()}"
