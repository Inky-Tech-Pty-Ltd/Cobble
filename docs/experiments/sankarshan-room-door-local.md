# Candidate 3 — Sankarshan joins one meeting (local Door test)

The **first** of two distinct milestones: Sankarshan enters a meeting Room. This does **not** admit him into McKay's Cobble installation as a peer Room, give him a personal Cobble instance, or grant access to its private corpus.

Status: **local two-browser proof only**. Do not yet send a local invitation URL to someone on another machine. A restricted, authenticated HTTPS transport must be configured and tested separately.

## Start on McKay

In the candidate-3 worktree:

```bash
cd ~/Cobble-screenshot
git fetch origin puck/room-door-sankarshan-1
# Stop the existing server with Ctrl+C before switching.
git switch --detach FETCH_HEAD
PYTHONPATH=src python3 scripts/snug_demo_web.py \
  --store ~/cobble-data --port 8767 --guest-port 8768 \
  --live-gpt --live-claude --live-mistral
```

The operator console remains at `http://127.0.0.1:8767/`; the **separate guest-only** server binds `127.0.0.1:8768`. The latter is not reachable from other machines.

## Two-browser proof

1. In Joe's operator console, choose a **dedicated test meeting**; create a normal opening agenda.
2. Click **Door: invite Sankarshan**, then **Open Door**. Cobble displays a once-only invitation URL. The link's fragment contains a high-entropy bearer secret.
3. Copy the URL and open it in a separate, preferably private/incognito browser window **on McKay**. That restricted page identifies the bearer as **Sankarshan** and displays only the invited meeting, its standing orders and conversation. The first test assumes Joe has verified the identity of the eventual human recipient out of band; a copied bearer token alone does not prove who is using it.
4. Post a message through the guest page. Confirm the operator console displays a **Sankarshan** bubble (refresh the operator page if necessary), and that the next GPT/Claude/Mistral request records `speaker: Sankarshan` in the recent conversation context.
5. The invited browser must **not** reach `/api/live/session`, `/api/search`, other rooms, exact provider payloads or McKay's corpus. It cannot pay for supplier calls or change standing orders.
6. In Joe's console, click **Close Door**. Reloading or posting from the guest page must now be refused.

### Boundary choices

- The invitation permits the holder to see the **entire existing meeting history**, not just outward room output. Invite deliberately; use a clean test room initially.
- Only an invited room is shared; the operator's API is a different loopback server.
- A new invitation for the same room invalidates the previous invitation; invitations expire after seven days and can be revoked.
- Secrets are stored only as SHA-256 digests in `~/cobble-data/snug/doors/invitations.json`; no invitation secrets go into Git or terminal logs.
- Room speech is append-only, separately attributed to Joe or Sankarshan. The guest cannot grant themselves authority to speak *for the room*; the convenor can select that contribution from the operator console.
- Supplier API credentials still belong to the operator's local server. Guests may see supplier replies, **not** their exact request payloads or audit metadata.
- This uses a simple first-person Door, not a universal Star Credential protocol or generic identity management.

## Remote access remains a separate security gate

A browser on Sankarshan's machine cannot use `127.0.0.1:8768` to reach Joe's McKay. Before any real invitation, expose **only the restricted guest surface** using authenticated HTTPS, verify that the token is not logged or disclosed by a reverse proxy, and rerun the negative access tests through that transport. Never publish the operator server/port 8767 or route guest traffic to it.

References: [Issue #82](https://github.com/Inky-Tech-Pty-Ltd/Cobble/issues/82) and [later Cobble-to-Cobble #83](https://github.com/Inky-Tech-Pty-Ltd/Cobble/issues/83).
