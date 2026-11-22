# Puck comments on GitHub Discussions

Cobble's MCP tool `puck_comment_on_discussion(repository, number, body)`
creates one top-level comment in a **VillageLink GitHub Discussion** using
GitHub's `addDiscussionComment` GraphQL mutation.

This is a separate credential and capability from reading archived discussions.
It is disabled by default, and never uses `gh`, `GH_TOKEN`, Joe's GitHub
account, the old Puck-Dispatcher GitHub App or supplier API credentials.

## Authorization on McKay

1. Log into GitHub as the dedicated machine user **puck-inky**, and create a
   fine-grained personal access token. Select resource owner
   `Inky-Tech-Pty-Ltd`, repository **VillageLink only**, and repository
   permission **Discussions: Read and write** (Metadata: Read is implicit).
   Choose a short expiry and store it in 1Password. An organization approval
   may be required. Do not create the token under Joe's identity.
2. Provision the secret into a user-owned private file in WSL, for example
   `/home/cobbler/.config/cobble/puck-github-token`. The file must be a
   **regular, nonsymlink** file owned by the MCP service user and readable
   only by that user (`chmod 600`). Do not put the token in the repository,
   scripts, command arguments, chat, workflow logs or a shared systemd unit.
   Use a secret-to-stdin pipeline from 1Password as with live supplier keys.
3. Configure the **Cobble MCP server process** (not merely the Meetings web
   service) with these two environment settings:

   ```sh
   COBBLE_MCP_ALLOW_PUCK_DISCUSSIONS=1
   COBBLE_PUCK_GITHUB_TOKEN_FILE=/home/cobbler/.config/cobble/puck-github-token
   ```

   Restart the MCP server and refresh/reconnect its client if necessary so
   `puck_comment_on_discussion` becomes available. The tool still refuses
   writes if the live GitHub GraphQL `viewer.login` is not `puck-inky`.

## Contract and guardrails

- Only `Inky-Tech-Pty-Ltd/VillageLink`; positive numeric Discussion IDs;
  a nonempty body of at most 12,000 UTF-8 bytes.
- One explicitly called mutation; no unprompted posts, arbitrary GraphQL,
  PR/Issue writes, deletions or impersonation.
- A GraphQL lookup checks repository, Discussion ID and token identity before
  mutation. On success the tool returns the actual new comment URL.
- A timeout/error after the mutation may have occurred: **inspect the
  Discussion before retrying**, to avoid duplicate comments.
- New comments do not automatically enter the local archived corpus.
  Run the normal GitHub conversation sync to ingest the resulting event.

Offline regression test: `PYTHONPATH=src python -m unittest discover -s tests -p test_github_discussion_writer.py -v`.

## Crossing from ChatGPT to Cobble's supplier interface

The native ChatGPT GitHub connector does **not** automatically travel with
an OpenAI API/Claude/Mistral supplier invited to a Cobble meeting. Tools,
credentials and authorization must be owned by Cobble and exposed to the
supplier through a reviewed tool-dispatch protocol. This MCP tool is a
backend building block; **supplier tool calling and trust-boundary review
inside Meetings are not yet implemented**. This means adding this tool
does not immediately let an ordinary Cobble meeting instruct GPT to post.
