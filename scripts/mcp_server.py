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
    arena_catalogue as read_arena_catalogue,
    arena_list_sources as read_arena_list_sources,
    arena_read_source as read_arena_source_text,
    run_lab_suite as execute_lab_suite,
    lab_add_note as append_lab_note,
    lab_recent_notes as get_lab_notes,
)
from cobble.puck_github_writer import submit_write as dispatch_puck_write
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
def arena_catalogue(name: str = "arena-a") -> dict:
    """Report copied-source counts and bytes by category; no source content."""
    return read_arena_catalogue(name)


@mcp.tool()
def arena_list_sources(name: str = "arena-a", category: str = "all",
                       offset: int = 0, limit: int = 25, query: str = "") -> dict:
    """Page file paths and hashes from Snug's saved corpus manifest, not text.

    Returned paths may be sensitive; call only when a user has authorised
    inspection of that Arena. No historical archive reads or network calls.
    """
    return read_arena_list_sources(name, category, offset, limit, query)


@mcp.tool()
def arena_read_source(name: str = "arena-a", path: str = "",
                      offset: int = 0, max_bytes: int = 8000) -> dict:
    """Read one verified source-text page from an inherited Arena file.

    Intended for authorised lab workers, not public visitors or Snug's
    metered senses. Requires COBBLE_MCP_ALLOW_SOURCE_READS=1 on McKay.
    Return at most 12000 source bytes; follow next_offset for continuation.
    """
    return read_arena_source_text(name, path, offset, max_bytes)


@mcp.tool()
def run_lab_suite(suite: str = "arena") -> dict:
    """Run a fixed offline lab test suite: arena, remote, console or lab.

    Requires COBBLE_MCP_ALLOW_LAB_TESTS=1 on McKay. Never accepts paths,
    shell commands or an external network request.
    """
    return execute_lab_suite(suite)


@mcp.tool()
def lab_add_note(kind: str, text: str, arena: str = "arena-a") -> dict:
    """Append an attributed operator observation to the private lab journal.

    Requires COBBLE_MCP_ALLOW_LAB_NOTES=1. Notes never modify source,
    Arena state or Snug's experimental resource ledger.
    """
    return append_lab_note(kind, text, arena)


@mcp.tool()
def lab_recent_notes(limit: int = 10) -> dict:
    """Read the most recent operator journal entries, no filesystem browsing."""
    return get_lab_notes(limit)


@mcp.tool()
def run_arena_tests() -> dict:
    """Run the fixed offline Arena tests; opt-in required on McKay.

    Disabled unless COBBLE_MCP_ALLOW_ARENA_TESTS=1 is configured locally.
    No commands, paths, shell arguments or environment variables accepted.
    """
    return run_arena_selftest()


@mcp.tool()
def puck_submit_write(path: str, content: str, message: str) -> dict:
    """Submit a bounded writing request to the existing Puck-GPT Actions writer.

    Requires a dedicated, non-Joe service identity with Actions dispatch
    permission; never uses McKay's GitHub CLI login or the Puck App private key.
    Disabled unless COBBLE_MCP_ALLOW_PUCK_DISPATCH=1 is set.
    """
    return dispatch_puck_write(path, content, message)

if __name__ == "__main__":
    mcp.run(transport="stdio")
