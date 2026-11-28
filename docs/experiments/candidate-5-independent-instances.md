# Candidate 5 — Independent instances (increment A)

Goal: Puck can host a room in a Cobble instance of his own and invite Joe.
Joe can host and invite Puck through the same peer protocol. Installing Cobble
is not a requirement for a participant; this pilot exercises the two-instance case.

## Current increment

- Fresh explicitly provisioned stores have their own random durable instance ID
  and a pilot operator name (Joe, Puck or Sankarshan). Existing stores are not
  migrated or relabelled. Their legacy behaviour remains Joe-hosted.
- A named server must use an index within its own store. The store and index
  cannot be redirected by symlinks. No existing corpus or credential is copied.
- Existing local operator API creates meetings, posts as that instance's
  operator, and can issue a peer invitation using room_id, speaker and mode=peer.
  The guest port remains the only guest transport. Its bearer authorises one
  room/seat, not operator rights. An instance ID is a label, not an authenticated
  public-key identity. The host must verify the recipient out of band.
- The receiving instance's PeerDoor checks its local identity against the
  invited speaker, checks host ID and room ID on reading, and supports explicit
  read/post only. Never automatically retry an uncertain post.
- Regression test runs real loopback HTTP between two separately provisioned
  stores and checks both directions, admission before agenda, attribution,
  unrelated room isolation, private field exclusion, revocation, wrong seat,
  mismatched room and refusal of non-loopback destinations.

## Keyless first test (no changes to the running Snug)

From the candidate checkout:

    PYTHONPATH=src:../VillageLink/prototype .venv/bin/python -m unittest discover -s tests -p test_snug_live.py -v

For a fresh disposable pilot store (choose a new path that does not exist):

    PYTHONPATH=src:../VillageLink/prototype .venv/bin/python scripts/cobble_peer.py init --name Puck --store ~/cobble-puck-pilot

Use a different new store and --name Joe for a reciprocal pilot. The named
operator server uses its own index automatically. For example:

    PYTHONPATH=src:../VillageLink/prototype .venv/bin/python scripts/snug_demo_web.py --store ~/cobble-puck-pilot --port 8877 --guest-port 8878

This increment's peer flow uses the local operator API, not the main
workbench UI. Do not use that UI as evidence of correct named identity:
its Joe-specific controls have not yet been generalised. The CLI read/post
commands accept a private JSON envelope on stdin: invitation for read,
invitation plus text for post. The invitation is the response from the
operator invite endpoint with mode=peer. It is a secret; do not paste it
into a chat, command line, log or Git. No remote networking is enabled.

## Boundaries and next increments

Separate directories under the same OS account are logical isolation, not
a filesystem security sandbox against hostile local code. The loopback
operator API still assumes a trusted local operator; do not grant it to
untrusted participants. The test does not establish autonomous Puck identity,
transfer ChatGPT memory, or allow Puck to access either store from this chat.
No paid supplier calls, external network access, credentials, notifications,
document transfers, or deployment changes are needed for this increment.

Next: named-instance UI and operator controls, explicit delegated convening
for Puck, a durable private incoming invitation inbox, separately authenticated
remote transport with HTTPS and independent credentials, and an independently
operated second machine. Preserve the Candidate 4 bridge while these are tested.
