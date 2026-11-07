# OpenAI third intelligence supplier (offline adapter)

The OpenAI Responses API adapter is the third supplier for Cobble. It keeps
provider state outside the model's hosted conversation system by sending a
self-contained request with `store: false`, no tools, and no
`previous_response_id`. The locally retained Snug exchange and explicitly
selected context are the sole source of history.

Current model: `gpt-6-luna`. Standard short-context indicative USD token
rates: $0.05/million input; $0.25/million output. Check current billing before
live use; the local 16 KB preflight limit, 256 output-token cap and $0.01
estimate threshold are NOT account spending guarantees.

Run completely offline:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_openai_adapter.py' -v
```

A keyless preview can be made from Python:

```sh
PYTHONPATH=src python3 - <<'PY'
from cobble.openai_adapter import OpenAIAdapter
from cobble.snug_exchange import ExchangeRequest
request = ExchangeRequest(participant="operator", question="Hello GPT",
                          selected_memories=(), previous_exchanges=())
print(OpenAIAdapter().preview(request))
PY
```

No CLI live call is introduced by this increment. Before a real call,
create a dedicated Cobble project with independent API key and spending
controls, configure usage permissions, confirm data-processing and retention
settings, and add an audited one-shot live runner analogous to the existing
Claude/Mistral gates.

The API does not use customer data for model training by default, but
provider-side retention and abuse monitoring still need evaluation. An
explicit `store: false` does not mean zero retention.

Official references:
- https://developers.openai.com/api/docs/guides/your-data
- https://developers.openai.com/api/reference/resources/responses/methods/create
- https://platform.openai.com/pricing
