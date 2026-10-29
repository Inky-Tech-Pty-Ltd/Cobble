"""Cobble memory MCP interface with scoped Arena diagnostic operations.

Use stdio for private development. Do not publish an unauthenticated HTTP
version of this service: memory contents may be sensitive. The fixed Arena
test operation is disabled unless McKay's operator explicitly enables it.
"""
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from cobble.github_memory_access import read_github_discussion as read_archived_discussion
from cobble.remote_ops import (
    arena_status as read_arena_status,
    verify_arena as verify_arena_copy,
    run_arena_tests as run_arena_selftest,
)
from cobble.memory_access import (
    get_trace as read_trace,
    inspect_star as read_star,
    search_memory as find_memory,
)

mcp = FastMCP("Cobble Memory", instructions=(
    "Cobble memory and bounded Arena diagnostics. Village Links are "
    "assertions, not established facts. Remote shell execution is unavailable."
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


@mcp.tool()
def arena_status(name: str = "arena-a") -> dict:
    """Read a named local Arena's budget and population counts (no source text)."""
    return read_arena_status(name)


@mcp.tool()
def verify_arena(name: str = "arena-a") -> dict:
    """Verify the copied Arena's SHA-256 file manifest without changing files."""
    return verify_arena_copy(name)


@mcp.tool()
def run_arena_tests() -> dict:
    """Run the fixed offline Arena tests; opt-in required on McKay.

    Disabled unless COBBLE_MCP_ALLOW_ARENA_TESTS=1 is configured locally.
    No commands, paths, shell arguments or environment variables accepted.
    """
    return run_arena_selftest()


if __name__ == "__main__":
    mcp.run(transport="stdio")
