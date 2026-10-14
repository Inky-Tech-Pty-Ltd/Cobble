# Local trace and star resilience experiment

This small prototype can mint addressable traces, optionally preserve text,
extend an existing star, and recover a local copy with no network access.
Data stays outside Git (default: `~/cobble-data`). It does not ingest
ChatGPT automatically or mirror complete conversations.

With the VillageLink prototype cloned alongside Cobble and the Python
virtual environment activated:

```bash
PYTHONPATH=src:../VillageLink/prototype python -m unittest discover -s tests -v
```

Create a trace with a manually exported UTF-8 excerpt; the selected passage
must be present in that excerpt:

```bash
PYTHONPATH=src python scripts/mint_trace.py \
  'https://chatgpt.com/c/your-conversation' \
  'Memory is the masterpiece.' \
  --copy-file /path/to/saved-excerpt.txt
```

Copy the printed `https://cobble.link/t/...` URI and connect it to an
existing star:

```bash
PYTHONPATH=src:../VillageLink/prototype python scripts/add_ray.py \
  'https://cobble.link/t/STAR-CENTRE-UUID' \
  'https://cobble.link/t/NEW-MEMBER-UUID'
```

Adding the same member twice is a no-op. The centre URI is retained. Inspect
the star using `scripts/inspect_star.py`. Resolve a saved copy *without
contacting the original source*:

```bash
PYTHONPATH=src python scripts/resolve_trace.py \
  'https://cobble.link/t/NEW-MEMBER-UUID'
```

Local copies are only read from paths inside the Cobble store. A trace
without a retained copy cannot be resolved locally. The local snapshot is
not proof that its source remains available or unchanged.

Current limitations: text-only excerpts, manual selection, no automatic
source retrieval or ChatGPT ingestion, no complete multi-file transactional
writes, no simultaneous-writer coordination, and no network failover.
No mandatory provenance history or trust scoring is introduced.
