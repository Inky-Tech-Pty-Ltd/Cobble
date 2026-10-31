# Puck Actions dispatcher — implementation slice (31 October 2026)

**Prototype, not production-authorised.** VillageLink Issue #5 remains open.

Puck's actual GitHub **writer** is GitHub Actions in InkyTech.
The workflow alone creates a repository-scoped GitHub App token from
`PUCK_GPT_PRIVATE_KEY` and commits as `puck-gpt[bot]`.

The new Cobble MCP tool `puck_submit_write(path, content, message)`
only *requests* an Actions run using the InkyTech workflow_dispatch API.
The submitted request is a base64-encoded JSON object. GitHub Actions
validates the resulting JSON, limits it to one **new** Markdown file under
`docs/experiments/`, creates `puck/work-<run_id>` from Cobble main,
and uses the Puck App installation token for the actual push.
The workflow also retains its earlier manually staged branch mode.

## Identity separation

**Do not use Joe's credentials as the dispatcher.** The MCP process requires
two opt-ins: `COBBLE_MCP_ALLOW_PUCK_DISPATCH=1` and
`PUCK_DISPATCH_TOKEN=<short-lived Puck-Dispatcher App installation token>`.
The credential issuer must use App ID **5549836** and installation ID
**177074425**, and restrict the token to **InkyTech** with Actions write
permission (and only required read permissions).

Before dispatch the tool calls GitHub `GET /installation/repositories`
with that same token and requires exactly one repository: InkyTech.
This check alone **does not prove which App issued the token**;
that assurance belongs to the isolated issuer. It does not read `GH_TOKEN`, `GITHUB_TOKEN`, `gh auth`, the `git`
credential helper or any GitHub App private key.

The Puck-Dispatcher App installation must have narrowly limited GitHub
Actions dispatch permission on InkyTech. The exact permissions and identity must be
verified during provisioning; do not assume a generic PAT is safely scoped.
Importantly, this token is still a secret that needs protected storage
and rotation. Avoid setting it in McKay's general interactive shell or
the existing memory MCP process if it also has access to Joe's home.
A separate restricted OS identity/service is the intended deployment.
The installation repository check inside Python is defence in depth;
**OS-level separation and deauthorisation of the Joe GitHub connector
are still essential** to the full impersonation-negative-test.

As shipped the MCP tool is **disabled**: the existing `lab_tunnel.sh`
does not opt into dispatch or load a dispatch token. No active remote
writer is added until an independent service identity is provisioned.

## Testing

Offline:
```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_lab_puck_writer.py' -v
```

Then inspect the InkyTech Actions workflow changes. Publish the workflow
through Puck's established process. The complete end-to-end test requires
a dedicated service identity and restricted execution context; no
Joe-authenticated fallback is acceptable.

## Current boundaries

- Supported: bounded new Cobble Markdown file request; Puck-attributed
  Actions commit after successful dispatch.
- Not supported: arbitrary files, edits or shell commands; publication
  to main; direct Puck private-key access on McKay.
- Not yet proven: service-principal provisioning, isolated runtime,
  operation through the live MCP tunnel, removal of Joe-authenticated
  GitHub mutations, or the full end-to-end negative impersonation test.
