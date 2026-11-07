"""Bounded two-supplier handover with synthetic memory and append-only audit.

No ambient corpus is read. Stage 1 selects one invented local source for Claude.
Stage 2 gives Mistral only the explicitly identified Claude exchange.
Dry runs use synthetic providers and never read API keys or contact a network.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import uuid

from cobble.claude_adapter import ClaudeAdapter
from cobble.mistral_adapter import MistralAdapter
from cobble.local_search import build, search
from cobble.snug_exchange import exchange, read_event
from cobble.mistral_first_call import _exclusive_record

MEMORY = "In this fictional experiment, the lighthouse keeper's password is VIOLET-OTTER-73. This is synthetic test data, not a real credential."
FIRST_QUESTION = "Read the selected fictional note and tell me its lighthouse keeper password. Do not invent other facts."
SECOND_QUESTION = "Using ONLY the explicitly included earlier exchange, what fictional lighthouse keeper password was recorded? If it is absent, say unknown."
CONSENT = "I AUTHORIZE ONE SYNTHETIC HANDOVER API CALL"
FORMAT = "snug-synthetic-handover-1"
PHASES = ("claude", "mistral")


def _safe_root(root):
    root = Path(root).expanduser().resolve()
    if any((p / ".git").exists() for p in (root, *root.parents)):
        raise ValueError("Refusing to store experiment within a Git checkout")
    # Never use the real corpus root. The experiment must be an isolated child.
    if root == Path.home() / "cobble-data":
        raise ValueError("Experiment requires an isolated store")
    return root


def _locations(root):
    return root / "index" / "search.sqlite3", root / "snug" / "handover"


def _prepare(root):
    index, ledger = _locations(root)
    note = root / "hosting" / "inkytech" / "fictional-lighthouse.txt"
    if note.exists():
        if note.is_symlink() or note.read_text(encoding="utf-8") != MEMORY:
            raise ValueError("Synthetic note differs from expected fixture")
    else:
        note.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if note.parent.is_symlink():
            raise ValueError("Unsafe synthetic memory directory")
        _exclusive_record(note, MEMORY)
    # Build isolated FTS index: never point to McKay's normal index.
    if not index.exists():
        build(root, index)
    match = search(index, "lighthouse keeper password")
    if len(match) != 1 or match[0]["source"] != "inkytech":
        raise ValueError("Synthetic memory index is not isolated or unique")
    return index, ledger, match[0]["id"]


def _stage(root, phase, adapter, *, live=False, confirm=None, limit_confirmed=False):
    if phase not in PHASES:
        raise ValueError("Unknown phase")
    root = _safe_root(root)
    index, ledger, docid = _prepare(root)
    prior_file = ledger / "claude-event.json"
    if phase == "mistral":
        if not prior_file.is_file() or prior_file.is_symlink():
            raise PermissionError("Claude phase must complete before Mistral")
        prior = json.loads(prior_file.read_text(encoding="utf-8"))
        prior_id = prior["event_id"]
        recorded = read_event(root, prior_id)
        if recorded["provider"] != "claude" or len(recorded["selected_memories"]) != 1:
            raise ValueError("Prior event does not contain the synthetic Claude exchange")
    else:
        prior_id = None
    if live and (confirm != CONSENT or limit_confirmed is not True):
        raise PermissionError("Live handover requires explicit consent and vendor limit confirmation")
    # An immutable marker prevents duplicate attempts, including retries after timeout.
    marker = ledger / (phase + "-attempt.json")
    attempt_id = uuid.uuid4().hex
    audit = {
        "format": FORMAT, "phase": phase, "attempt_id": attempt_id,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "live": live, "synthetic_memory_only": True,
        "selected_memories": 1 if phase == "claude" else 0,
        "previous_exchanges": 0 if phase == "claude" else 1,
        "previous_event_id": prior_id,
    }
    _exclusive_record(marker, audit)
    try:
        event = exchange(
            store=root, index=index,
            question=FIRST_QUESTION if phase == "claude" else SECOND_QUESTION,
            participant="operator", provider=phase, adapter=adapter,
            memory_ids=(docid,) if phase == "claude" else (),
            allowed_sources=("inkytech",) if phase == "claude" else (),
            prior_ids=(prior_id,) if prior_id else (),
        )
        outcome = {"format": FORMAT, "phase": phase, "attempt_id": attempt_id,
                   "status": "completed", "event_id": event["event_id"],
                   "usage": event["usage"]}
        _exclusive_record(ledger / (phase + "-outcome.json"), outcome)
        if phase == "claude":
            _exclusive_record(prior_file, json.dumps(
                {"event_id": event["event_id"]}))
        return {"phase": phase, "event_id": event["event_id"],
                "answer": event["answer"], "usage": event["usage"],
                "selected_memories": len(event["selected_memories"]),
                "previous_exchanges": len(event["previous_exchange_ids"])}
    except Exception as exc:
        _exclusive_record(ledger / (phase + "-outcome.json"),
                          {"format": FORMAT, "phase": phase,
                           "attempt_id": attempt_id, "status": "outcome_unknown",
                           "error_type": type(exc).__name__,
                           "actual_charge_usd": None})
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path,
                   default=Path.home() / "cobble-data" / "snug-handover-synthetic")
    p.add_argument("--phase", choices=PHASES, required=True)
    p.add_argument("--send-live", action="store_true")
    p.add_argument("--confirm", default="")
    p.add_argument("--workspace-limit-confirmed", action="store_true")
    args = p.parse_args()
    if not args.send_live:
        # Preview only. No fixture creation, event writes, or network calls.
        print(json.dumps({
            "phase": args.phase, "dry_run": True, "network_calls": 0,
            "memory": "fictional lighthouse note",
            "selected_memories": 1 if args.phase == "claude" else 0,
            "prior_exchanges": 0 if args.phase == "claude" else 1,
            "root": str(_safe_root(args.root)),
            "live_requires": "stdin API key plus explicit consent and vendor limit",
        }, indent=2))
        return
    if args.confirm != CONSENT or not args.workspace_limit_confirmed:
        p.error("Live handover requires exact consent and workspace-limit confirmation")
    # Read a single vendor key from stdin only after authorisation. No echo,
    # environment/CLI logging or disk persistence of the secret.
    key = sys.stdin.read(4096).strip()
    if not key or len(key) > 512:
        p.error("A valid API key must be supplied on stdin")
    adapter = (ClaudeAdapter(allow_network=True, key=key) if args.phase == "claude"
               else MistralAdapter(allow_network=True, key=key))
    result = _stage(args.root, args.phase, adapter, live=True,
                    confirm=args.confirm, limit_confirmed=True)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
