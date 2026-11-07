# Mistral supplier adapter

**Status:** offline-tested adapter with explicit opt-in HTTPS capability. This
branch does not create keys, purchase credits or transmit any private memories.

Mistral uses the documented Chat Completions endpoint,
`POST https://api.mistral.ai/v1/chat/completions`, with bearer-key
authentication. The adapter selects `mistral-small-latest` and requests a
maximum of 256 output tokens; it uses no tools, agents, web search, or hosted
Mistral memory. Only expressly selected source passages and previous exchange
events enter the request. The default constructor refuses network calls.

The key is read from `MISTRAL_API_KEY` on McKay only after an explicit
`MistralAdapter(allow_network=True)` is constructed. No credentials are
stored in Git or recorded in exchange events.

## Offline acceptance on McKay

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_mistral_adapter.py' -v
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_claude_adapter.py' -v
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_snug_exchange.py' -v
```

A keyless, memory-free preview in Python:

```sh
PYTHONPATH=src python3 - <<'PY'
from cobble.snug_exchange import ExchangeRequest
from cobble.mistral_adapter import MistralAdapter
request = ExchangeRequest(
    participant="operator", question="Hello Snug",
    selected_memories=(), previous_exchanges=())
print(MistralAdapter().preview(request))
PY
```

Previews show metadata, never the selected text or the API key.

## Before live activation

Use workspace spending controls on Mistral Studio and a scoped, locally
stored key. Check your Mistral API data-use/training terms and workspace
settings before sending any private content. The model alias may rotate.
The local estimated tariff (USD 0.15/M input tokens and USD 0.60/M output
tokens, reflecting published Small 4 standard prices in November 2026) is
only indicative and **not** a vendor billing cap. The 16 KB payload ceiling,
256 output tokens, and $0.01 preflight threshold are local estimates and
cannot replace platform-side limits.

No automatic live operation is included in the CLI. When running a live
trial, start memory-free, record every attempt before transmission, and
do not retry ambiguous failures without reviewing the usage ledger.

API reference: https://docs.mistral.ai/api/endpoint/chat
Pricing: https://docs.mistral.ai/inference/pricing
