# Candidate 4 — Puck at a meeting (local bridge)

First increment of a shared invitation/seat protocol. Existing Sankarshan
invitations are independent of Puck invitations. The convenor opens or closes
Puck's Door under Membrane → Doors, scoped to the selected meeting. No new public listener, supplier calls,
or access to the operator console is introduced.

**Deployment is a separate security decision.** The existing private MCP
tunnel has no per-chat authenticated identity. Anyone authorised to invoke
its tools could act as the Puck seat if they know its room ID and the local
opt-in is enabled. This is an attributed seat, not cryptographic proof of
a particular ChatGPT conversation or model. Keep the tunnel private.

The operator server stores the Puck bearer in a separate local 0600 binding
under the existing private store (snug/doors/puck-seats). The invitation
registry itself still retains only token digests. Closing a Door revokes
the token and removes its binding. Expired bindings cannot admit a guest.
Treat backups of the private store as sensitive. Do not paste the token
into chat or commit it. Use a clean test meeting; an invitation shares the
entire table, not only room output.

Local proof:
1. Start the meetings server offline with a separate loopback guest port.
2. Convene a clean test meeting, post an agenda, open Membrane → Doors and click Invite Puck.
3. After explicit local approval, enable COBBLE_MCP_ALLOW_PUCK_MEETINGS=1
   in the existing private MCP subprocess environment, restart the tunnel
   and refresh its tool definitions. No new OpenAI API key is required.
4. Open a dedicated ChatGPT conversation in the connected Cobble project.
   Ask Puck to call puck_meeting_read with the room ID shown in the console.
   Ask Puck to table a deliberate contribution using puck_meeting_post.
5. Confirm it appears in the meeting as Puck; only the convenor may select
   it for room voice. Post a response and ask Puck to read again.
6. Close Puck's Door and verify read and post are refused. Disable the opt-in
   after the experiment.

This candidate is human-assisted: no automatic chat creation, continuous
polling, background responses, external invitation delivery, or remote
Cobble-to-Cobble transport is implemented. The existing local guest server
remains the single authority for posting. A lost response must not trigger
automatic retry. Puck may only table deliberate content, not private
ChatGPT memories or conversations by default.
