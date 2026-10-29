# Snug's first browser console

**Status:** experimental offline interface (30 October 2026). This is the
beginning of a prompt/response UI, *not* an intelligent Snug, a multi-provider
conversation, or an authenticated collaboration service.

## Start locally

Requirements: Python 3.11+, an existing populated Arena One, and a browser.
No packages beyond the Python standard library, provider keys, web service
accounts or public network ports are needed.

```sh
cd ~/Cobble
git pull --ff-only
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_snug_console.py' -v

PYTHONPATH=src python3 scripts/snug_web.py \
  --arena ~/cobble-arenas/arena-a --port 8765
```

On the **same machine as McKay**, open `http://127.0.0.1:8765/` in a
browser. On a Windows machine with WSL2 localhost forwarding enabled,
Windows Chrome should reach the WSL loopback service at the same URL.
Otherwise inspect WSL's forwarding configuration; **do not change this
script to bind `0.0.0.0` or forward the port publicly** just to make
it reachable. Press Ctrl+C to stop the service.

The chat UI accepts a prompt and displays a response. The following
offline prompts have real, deterministic results:

- `hello` — introduction.
- `status` — full-corpus file count and byte total from the saved manifest.
- `sources` — the category breakdown (GitHub conversations, Git objects,
  traces, hypotheses, ChatGPT and other source groups).
- `who are you` — the current experimental identity boundary.
- `help` — capability list.

Other prompts receive an explicit statement that the inference interface is
not connected. **There is no fabricated general-purpose conversation.**

The browser sends the prompt solely to the local HTTP listener; it is
processed in memory and **not retained as a new event**, not written
into the Arena, and not sent to any model or third party. The response
does not quote original GitHub or ChatGPT content. No external JavaScript,
stylesheets or tracking dependencies are used.

## Current trust boundary

This is an **operator-only local development UI**. Its server binds to
`127.0.0.1` and serves only two endpoints: the static home page and
a bounded `/api/ask` plus a health endpoint. Same-origin and a custom
header are required for POSTs; suspicious Host headers are rejected.
There is no login system because **there is no network-facing listener**.
A program running on the same machine may still attempt local requests;
the server is not a defense against a compromised McKay.

The source manifest is read through Cobble's existing `arena_catalogue`
logic. API responses expose counts and categories, not per-file paths,
content or credentials. No shell invocation, corpus mutation, paid
intelligence call, Village Link publication or remote API is available.

**This is not how we should invite Sankarshan in.** The private
`~/cobble-data` and `~/cobble-arenas` stores contain information
beyond the public repository. Before a shared Snug is offered, design an
explicitly selected **permitted corpus**, authentication, participant
identity, access logs, interaction quotas and provider spending limits.
A per-researcher *local* Arena built from public synthetic or permitted
real corpora is currently the safer independent path.

## The next increment

A provider-neutral, resource-metered **hemisphere API** should be added
behind the same prompt/response contract. It will make the prompt a
recorded experience, retrieve permitted source passages, send only
authorised material to an explicitly selected **OpenAI or Kimi** provider,
and record usage, source identifiers, disagreements and costs. We must
distinguish operator diagnostics from Snug's charged senses.

Do not assume a live interface has established personhood, an enduring
AI identity, independent hypotheses or self-governance. The challenge
is to build an experiment that could eventually test those properties
without programming an imitation of them.
