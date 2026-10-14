# Independent and adversarial memory retrieval benchmark

**Status:** Experimental evidence for Cobble issue #1.  
**Purpose:** Replace the earlier label-leaking sanity check with a stricter benchmark.

## Design

The benchmark separates three artifacts: synthetic trace text, seeded graph memberships, and independently stored relevance annotations. Graph membership is intentionally imperfect. It contains false-positive links and omits some relevant traces. This prevents the evaluation from treating the graph as ground truth.

The same lexical scorer, candidate pool and retrieval budget are used in A0 and A1. A1 receives only the additional graph-neighbor bonus already used by the earlier harness.

## Adversarial cases

- `B04` is about portable storage, not portable AI memory, but is deliberately linked into the B01 star.
- `B10` concerns popularity/ranking and is deliberately linked into the source-provenance star.
- `B11` and `B12` are relevant to historical provenance/change but omitted from that star.
- `B06` is relevant to continuity across model replacement but omitted from the B16 star.

These cases test both benefit and harm from graph structure.

## Claims this benchmark can support

It can show whether hand-seeded but imperfect relationships change deterministic retrieval under independently maintained relevance labels. It can expose retrieval gains, no-effect cases, and false-link promotion.

It cannot show that Cobble can automatically discover correct relationships, that real user memories behave similarly, or that a graph establishes semantic truth or agent continuity.

## Reproduce

```sh
PYTHONPATH=src:../VillageLink/prototype python3 -m unittest discover -s tests -v
python3 scripts/evaluate_independent_benchmark.py
```

Promotion of graph-based retrieval should require mixed-case results to remain visible. A false-positive relationship that improves one metric while promoting irrelevant evidence is not an unqualified success.
