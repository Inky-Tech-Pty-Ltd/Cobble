"""Read-only MCP interface to the local Cobble memory store.

Use stdio for private development. Do not publish an unauthenticated HTTP
version of this service: memory contents may be sensitive.
"""
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from cobble.github_memory_access import read_github_discussion as read_archived_discussion
from cobble.memory_access import (
    get_trace as read_trace,
    inspect_star as read_star,
    search_memory as find_memory,
)

mcp = FastMCP("Cobble Memory", instructions=(
    "Read-only local Cobble memory. Village Links are equivalence assertions, "
    "not established facts. Search is restricted to Cobble traces and retained excerpts."
))


def store() -> Path:
    return Path(os.environ.get("COBBLE_DATA_DIR", "~/cobble-data")).expanduser()


@mcp.tool()
def get_trace(uri: str) -> dict:
    """Retrieve trace metadata and its bounded local text copy (if present)."""
    return read_trace(store(), uri)


@mcp.tool()
def inspect_star(centre_uri: str) -> dict:
    """Inspect a star credential and verify its locally recorded Village Link rays."""
    return read_star(store(), centre_uri)


@mcp.tool()
def search_memory(query: str, limit: int = 10) -> dict:
    """Find traces matching a text query (up to 20 results); no external crawling."""
    return find_memory(store(), query, limit)


@mcp.tool()
def read_github_discussion(repository: str, number: int, offset: int = 0,
                           max_chars: int = 12000) -> dict:
    """Read part of a GitHub Discussion archived in Cobble, including comments.

    Returns bounded text pages and next_offset for continuation; never
    requests GitHub live or changes memory. Import the discussion first.
    """
    return read_archived_discussion(store(), repository, number, offset, max_chars)


if __name__ == "__main__":
    mcp.run(transport="stdio")
