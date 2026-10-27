# Evidence-aware memory graph: experimental contribution

**Status:** Experimental; not a VillageLink protocol amendment.
**Tracking:** Cobble issue #1.
**Scope:** Local, deterministic, no network access, no AI similarity inference.

## Questions

- **H1 (continuity):** Do persistent hypothesis-centred links help a fresh
  process locate relevant memory traces across sessions?
- **H2 (thin memory):** Can relationships and provenance stay in Cobble while
  source contents remain external and need not be copied?
- **H3 (honest degradation):** Can source loss be reported without erasing the
  previous assertion or pretending the source remains retrievable?

H1 and H2 are NOT proven by this prototype. The included G0 inventory is only
an illustrative structural baseline; controlled semantic retrieval experiments
with equally capable G0/G1 retrievers are future work.

## Existing interfaces preserved

The existing `mint_star` method creates a hypothesis-centre trace, an
unchanged `{"type":"StarCredential","A":centre,"B":[...]}` record, and
Village Link rays via the VillageLink codec. These objects *assert* a
relation; they do not prove equivalence or authorize disclosure.

New `observations/<trace-uuid>/<observation-uuid>.json` files record retrieval
outcomes. No existing trace, hypothesis, star, or link is modified.
Observations are append-only through the public API and have independent IDs,
timezone-aware observation times, retrieval status, retrieval method and
`integrity.status=not_checked`. They do not establish source truth,
authenticity or immutable custody. For identical timestamps, order is
deterministically based on ID, **not** a guaranteed causal sequence.
Do not use these files as a security-grade tamper-evident log.

## Run

Clone VillageLink as a sibling of Cobble. From Cobble:

```bash
PYTHONPATH=src:../VillageLink/prototype python3 -m unittest discover -s tests -v
```

Create at least two synthetic local traces using the structure documented in
`docs/first-star.md`, then:

```bash
PYTHONPATH=src:../VillageLink/prototype python3 scripts/mint_star.py \
  'A repeated synthetic idea' TRACE_A TRACE_B --store /tmp/cobble-example
PYTHONPATH=src:../VillageLink/prototype python3 scripts/observe_source.py \
  TRACE_A available --method manual --store /tmp/cobble-example
PYTHONPATH=src:../VillageLink/prototype python3 scripts/observe_source.py \
  TRACE_A unavailable --method manual --store /tmp/cobble-example
PYTHONPATH=src:../VillageLink/prototype python3 scripts/inspect_memory.py \
  CENTRE_URI --baseline --store /tmp/cobble-example
```

Replace placeholders with generated IDs and the centre URI returned by
`mint_star.py`. No CLI command fetches source content. `manual` observations
report a user's stated outcome, not an automated verification.

## Inspectable invariants

1. Stable trace identity is not a source location.
2. W/ray existence does not establish equivalence or truth.
3. Missing observations imply unknown current retrieval status.
4. Later unavailability does not delete earlier availability observations.
5. Missing or inconsistent ray records raise an error rather than implying
   a complete graph; no automatic repairs or silent reconciliation.
6. External source URIs must not be automatically dereferenced by this module.
7. Filesystem access is local and not hardened for untrusted multi-user input.

## Non-goals and risks

This is not a transactional storage engine. Existing `mint_star` writes its
components sequentially; an interrupted mint can leave a partial star.
The inspector detects missing rays but does not recover or purge partial
writes. Concurrency, tamper evidence, access control, source content integrity,
encryption, backup, source consent, contradiction adjudication, similarity
scoring, and platform plugins are out of scope. Do not use actual private
memories for demonstrations. A future prototype should test transaction
semantics before production or untrusted inputs.

## Preliminary evidence

Unit tests exercise initial unknown source status, ordered availability
history, loss of access, invalid observations, ray corruption detection, and
fresh-process read-back. The G0/G1 comparison establishes only that persisted
edges narrow the *structural* candidate set; it is not a controlled retrieval
quality benchmark. Negative outcomes must be recorded in any future report.

## Promotion gate

Keep on an experimental branch until tests pass against actual VillageLink
codec, local demo is reproduced, compatibility is reviewed, and maintainers
agree on ownership of observation metadata versus the primitive.
