# First live OpenAI hello (one-shot)

Default is keyless, read-only and offline:

```sh
PYTHONPATH=src python3 scripts/first_live_openai.py
PYTHONPATH=src python3 scripts/first_live_openai.py --status
```

The live path must be separately authorised by the operator, after
confirming the OpenAI project spending limit and securely piping the API key
from a credential manager into standard input. It sends a **fixed, harmless
greeting only**; no corpus, previous exchange or memory is sent. The CLI
does not log the credential and the attempt marker is durably written
before making a network call. If the call fails or times out, the marker
blocks a second attempt until a human reviews the outcome.

Exact live authorisation string: `I AUTHORIZE ONE OPENAI API CALL`.
The CLI flags are `--send-live --confirm ... --project-limit-confirmed`.
Never type a key directly in a terminal command or chat message.

The vendor may have retention even with `store:false`. Estimated token costs
are not guaranteed bill ceilings. Inspect the final event and billed usage
after the first call.
