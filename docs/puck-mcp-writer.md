# Puck GitHub writer: first McKay MCP slice (31 October 2026)

This code is **staged for testing**. It is not a completed identity boundary.
VillageLink Issue #5 remains open.

The new tools are `puck_create_branch(name)` and
`puck_write_file(branch, path, content, message)`. They use GitHub's HTTPS
API directly and never invoke `gh`, `git`, subprocess, credential helper,
or `~/.config/gh/hosts.yml`.

For this first cut:
- Repository is fixed to `Inky-Tech-Pty-Ltd/Cobble`.
- Branch must start `puck/work/`, and files must be **new** Markdown files
  under `docs/experiments/`.
- Both actor/committer fields are fixed to `puck-gpt[bot]`.
- Token must be `PUCK_GITHUB_INSTALLATION_TOKEN` (GitHub App installation
  token, normally beginning `ghs_`) and switch
  `COBBLE_MCP_ALLOW_PUCK_WRITES=1` must be enabled.
- The token is checked against the GitHub App installation repositories API,
  which rejects personal OAuth credentials.
- The token is never returned to the caller or persisted by the tool.
- A bogus or unavailable token fails closed. There is no Joe fallback.

**This is not sufficient to prove the token belongs to the Puck-GPT App**:
a token from *another* GitHub App installation with Cobble access might also
pass the repository test. Nor does it prevent the MCP process, if running as
Joe's `cobbler` user, from accessing Joe's home directory outside these
individual tool functions. The final implementation needs a broker issuing
tokens specifically for App 4708095 and an OS-level isolated runtime, then
must disable the connected Joe-authenticated mutation route.

## Safe activation requirements

Do NOT put Joe's `gho_` token, the Puck App private key, or a persistent
App token into the Cobble tunnel's shell profile. Do NOT set the write switch
until a dedicated token broker and isolated runtime are established.

The current tunnel wrapper intentionally does **not** set the write switch.
The tools should therefore appear but refuse all writes after refresh. This
is expected and is a meaningful, limited negative test.

Run offline tests before any credential setup:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_lab_puck_writer.py' -v
```

The next implementation milestone is the separately credentialed broker,
which must never expose Joe's credential to the MCP process. Only after it
exists can the positive remote write and the full no-impersonation denial
test be run.

## Review correction: credential identity

GitHub's REST API does not permit treating a repository-access check as
proof of a specific GitHub App identity. The `GET /app` endpoint cannot
serve as a reliable identity check for an installation token: the
authenticated-app operation requires a GitHub App JWT. We deliberately
rejected that approach during review rather than publishing a broken
credential check.

The secure invariant is **provenance at token issuance**: a trusted,
separately authorised broker must use only the known Puck-GPT App
private key (App ID 4708095), mint a repository-restricted installation
token and deliver it only to the isolated writer process. The writer's
repository check is defence in depth, not identity proof.

The existing GitHub Actions writer already has the correct bot credential
and has made a real attributed write. A McKay broker is **not built** yet.
The connected Joe-authenticated ChatGPT GitHub plugin remains a bypass
until replaced or disconnected; therefore the full negative test is not
yet satisfied.
