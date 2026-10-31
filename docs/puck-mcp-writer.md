# Puck GitHub Actions broker — staged prototype

Puck-GPT's private key stays in GitHub Actions. A separate
Puck-Dispatcher App (ID 5549836, installation 177074425) is installed
on **InkyTech only** with Actions write, Metadata read and no Contents write.

The new `puck_dispatch_broker.py` is designed to run as a dedicated OS
account. It holds the dispatcher private key, signs a short-lived App JWT
with OpenSSL, exchanges it for a GitHub installation token restricted to
InkyTech and Actions write, and triggers only the existing
`puck-writer-v1.yml` workflow.

Cobble's `puck_submit_write` tool now talks over a Unix-domain socket
under `/run/puck-dispatch/`. It never sees a GitHub token or private key.
The broker independently validates each bounded Markdown request before
minting a credential.

**Do not deploy yet.** We have not verified tests on McKay and have not
built the OS account, protected runtime directory, key-loading procedure,
service unit or live installation-token exchange. In particular, socket
filesystem ownership/mode must be configured so Cobble can connect but
cannot read the key or broker process memory. The existing tunnel should
remain without `COBBLE_MCP_ALLOW_PUCK_DISPATCH=1`.

Once the offline tests and OS isolation are reviewed, deployment requires
provisioning the key *from 1Password directly to the restricted service
account*, with permissions 0600, outside source checkouts and chat.
Do not put it in `~/.bashrc`, project files, environment variables, or
a command visible in shell history. The broker should be managed by an
isolated service supervisor, not started from Joe's interactive session.

Offline tests:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_lab_puck_writer.py' -v
```

Full Issue #5 closure additionally requires (1) a live authenticated
dispatch made from the Cobble MCP tool, (2) Puck-attributed commit verified,
(3) removal of the connected Joe-authenticated GitHub mutation path and
a failed impersonation attempt, and (4) a check of Discussion read and
Discussion → Issue → PR → Commit provenance.
