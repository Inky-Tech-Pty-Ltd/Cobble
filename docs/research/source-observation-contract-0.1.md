# Experimental source-observation contract 0.1

**Status:** Experimental, local to Cobble. It does not modify VillageLink.

## Claim boundary

A source observation records what Cobble knows about a retrieval attempt and
when that knowledge was recorded. It does **not** establish that the source is
authoritative, semantically correct, unchanged, current beyond the recorded
time, or true.

## Retrieval states

| State | Meaning |
| --- | --- |
| `available` | An attempted retrieval succeeded at `retrieved_at`. |
| `unavailable` | An attempted retrieval failed because the source could not be obtained. |
| `restricted` | Retrieval was attempted but access controls prevented obtaining the source. |
| `moved` | Retrieval or external evidence indicates the prior location is no longer the current location; the new location is not inferred by this state. |
| `not_checked` | No retrieval attempt is claimed for this observation. |
| `unknown` | The observation cannot determine a more specific retrieval state. |

None of these states means `verified`, `trusted`, or `true`.

## Time semantics

- `observed_at`: when this observation record was made.
- `retrieved_at`: when the retrieval attempt represented by the state occurred; null for `not_checked` and may be null for `unknown`.
- `source_event_at`: optional time at which the source-side event is known to have occurred. It is never inferred from `observed_at` or `retrieved_at`.

All timestamps are timezone-aware ISO 8601 values. Ordering observations by
`observed_at` gives deterministic presentation, not guaranteed causal order.

## Integrity

Integrity is orthogonal to retrieval availability:

- `not_checked`
- `matches_recorded_digest`
- `differs_from_recorded_digest`
- `unknown`

An available source may fail an integrity comparison. An unavailable source may
have a prior integrity result. The current prototype does not calculate
digests; it only represents the state supplied by the caller.

## Lifecycle behavior

Observations are append-only through the Cobble API. New observations do not
rewrite earlier ones. A transition such as `available -> unavailable` means
only that two bounded observations exist at different times. It does not imply
revocation, deletion, falsity, or supersession of the underlying trace.

## Security and privacy limits

The observation directory is not a tamper-evident audit log. It has no
authentication, authorization, retention policy, encryption, or multi-user
concurrency guarantees. The existence and timing of observations may itself
reveal sensitive activity. These limitations block promotion to a production
source-state registry.
