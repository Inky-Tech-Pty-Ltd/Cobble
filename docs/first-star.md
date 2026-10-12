# Hypothesis-centred star experiment

A new thought from the Cobbler is stored as text in the local memory system
and receives its own minted Cobble trace URI. The star credential follows
the Village Link minimal form: type=StarCredential, A=centre URI, B=evidence
trace URI list. Every centre-to-member ray is an ordinary vl: link.

From the Cobble directory, with VillageLink cloned alongside:

    PYTHONPATH=src:../VillageLink/prototype python3 -m unittest discover -s tests -v

Then, with at least two existing local trace records:

    PYTHONPATH=src:../VillageLink/prototype python3 scripts/mint_star.py \
      'Memory is the masterpiece.' TRACE_A TRACE_B

Replace TRACE_A and TRACE_B with existing trace URIs. Use the printed
centre URI to inspect and verify the result:

    PYTHONPATH=src:../VillageLink/prototype python3 scripts/inspect_star.py CENTRE_URI

Data stays outside Git, under ~/cobble-data: hypotheses/ (source texts),
traces/ (centre and evidence records), stars/ (credentials), links/ (rays).

This does not publicly publish the trace URIs or contents. The credential
asserts equivalence, not factual truth. No confidence/reputation is inferred,
and writes are not yet transaction-safe.
