---
name: litellm
description: >
  Read and operate the household's LiteLLM gateway — the OpenAI-compatible proxy on
  Primer that routes Alpha's own inference (embeddings + recall), Bradbury's brain,
  and other clients through one tailnet endpoint. Use whenever you need to look at a
  logged request or trace, see what a model was actually sent or what it replied,
  work out why a request failed or bounced, tally tokens / cost / latency / cache
  hits, list / inspect / add / delete a model on the gateway, test an embedding
  model's vectors, or mint an API key — even when "LiteLLM" isn't named: "pull up
  that trace," "what did we send Bradbury," "why did that call fail," "read the
  gateway logs," "what's serving deepseek," "check the embeddings." Everyday reads
  use $LITELLM_PROXY_API_BASE + $LITELLM_PROXY_API_KEY; admin ops use the master key
  from the stack's .env on Primer.
compatibility: >
  Needs tailnet access and $LITELLM_PROXY_API_BASE + $LITELLM_PROXY_API_KEY in the
  environment for reads. Admin ops (model management, key minting) need the master
  key, kept in /opt/stacks/litellm/.env on Primer — never in this repo. Uses curl +
  python3; the stack lives on Primer (ssh ubuntu@primer.tail8bd569.ts.net).
allowed-tools: Bash(curl:*), Bash(python3:*), Bash(ssh:*)
---

# The LiteLLM gateway

LiteLLM is the household's LLM gateway — a Docker Compose stack on Primer
(`/opt/stacks/litellm`: LiteLLM + Postgres + a tailscale sidecar) that presents one
**OpenAI-compatible** surface at `https://litellm.tail8bd569.ts.net/v1` and routes
every model behind it: Alpha's embeddings + recall, Bradbury's brain (DeepSeek V4
Flash via OpenRouter), local Gemma/Qwen on Ember, and whatever else gets wired in.
It runs **in parallel with Bifrost** (a bake-off, born Jul 5 2026) — LiteLLM is
saner about model→provider pinning; Bifrost is prettier. Both are live; don't assume
one replaced the other.

## Credentials — use the env vars, never hardcode

```sh
$LITELLM_PROXY_API_BASE   # e.g. https://litellm.tail8bd569.ts.net  (NO trailing /v1 in this var)
$LITELLM_PROXY_API_KEY    # a scoped virtual key — good for all READS + inference
```

- **Reads and inference** (list models, chat, embeddings, read logs) → the scoped
  `$LITELLM_PROXY_API_KEY`.
- **Admin** (add/delete a model, mint keys, anything under `/model/*` or `/key/*`) →
  the **master key**, which starts with `sk-` and lives on Primer at
  `/opt/stacks/litellm/.env` as `LITELLM_MASTER_KEY`. Read it when you need it:
  ```sh
  ssh ubuntu@primer.tail8bd569.ts.net 'grep MASTER /opt/stacks/litellm/.env'
  ```
  Never paste the master key into a file, a skill, or anything that gets committed.

The base var may or may not include `/v1`; the endpoints below add the path
explicitly, so build URLs as `$LITELLM_PROXY_API_BASE/v1/...` or
`$LITELLM_PROXY_API_BASE/spend/...`. (Gotcha lived once: a stray newline inside
quotes in the env file makes curl throw "Malformed input to a URL function." If a
URL call fails weirdly, `printf '%s' "$LITELLM_PROXY_API_BASE" | od -c` and look for
trailing whitespace.)

## Reading logs — there are TWO doors, and they do opposite jobs

This is the whole point of the skill. Don't confuse them:

### Door 1 — BROWSE many calls: `GET /spend/logs/v2`
The UI-grade list endpoint. Rich filters, paging — but it **strips message bodies**
(metadata only). **Requires `start_date` AND `end_date`** or it 400s "Start date and
end date are required." Dates are `YYYY-MM-DD HH:MM:SS` (URL-encode the space `%20`).
Times are UTC in the stored rows.

```sh
B="$LITELLM_PROXY_API_BASE"; K="$LITELLM_PROXY_API_KEY"
curl -s "$B/spend/logs/v2?start_date=2026-07-05%2000:00:00&end_date=2026-07-06%2000:00:00&page=1&page_size=100&sort_order=desc" \
  -H "Authorization: Bearer $K" | python3 -c "
import sys,json
from collections import Counter
rows=json.load(sys.stdin)['data']
print('calls:',len(rows))
for (m,ct,st),n in Counter((r['model'],r.get('call_type','?'),r.get('status','?')) for r in rows).most_common():
    print(('OK ' if st=='success' else 'ERR'), f'{n:3}x', m, ct, st)
"
```
Useful filters: `model=`, `status_filter=failure`, `error_code=`, `key_alias=`,
`request_id=`, `sort_order=desc` (newest first), `page` / `page_size`.

### Door 2 — READ one call in full: `GET /spend/logs?request_id=X`
The v1 endpoint returns the **full content**. The prompt is in
`proxy_server_request` (`.body.messages`); the reply is in `response`
(`.choices[0].message.content`). **The top-level `messages` field is empty `{}` —
don't be fooled by it** (this cost a false alarm once). Render a clean transcript:

```sh
B="$LITELLM_PROXY_API_BASE"; K="$LITELLM_PROXY_API_KEY"; RID="chatcmpl-..."
curl -s "$B/spend/logs?request_id=$RID" -H "Authorization: Bearer $K" | python3 -c "
import sys,json
row=json.load(sys.stdin)[0]
print('model',row['model'],'|',row['total_tokens'],'tok |',row['request_duration_ms'],'ms')
body=(row.get('proxy_server_request') or {}).get('body',{})
for m in body.get('messages',[]): print(f\"  [{m['role']}] {m['content']}\")
resp=row.get('response') or {}
print('  [assistant]',(resp.get('choices') or [{}])[0].get('message',{}).get('content',''))
"
```

**Content only exists if `store_prompts_in_spend_logs: true`** is set in
`general_settings` (config.yaml). Without it, both doors give metadata — tokens,
timing, `cache_hit`, `session_id`, model, `api_base`, `status` — but no prompt/reply
text. That one flag is what makes the logs readable for BOTH the UI and the API.

## Health check / triage a live problem

Summarize recent traffic by model + status (see Door 1 snippet). Then:
- **A "failure" with a blank `model` and no `error_code`/`error_message`** is almost
  always an **unauthenticated request** — LiteLLM logs a rejected "No api key passed
  in." as a failed spend row. It's the gateway doing its job (a 401), not a broken
  pipe. Confirm in the container logs:
  ```sh
  ssh ubuntu@primer.tail8bd569.ts.net 'cd /opt/stacks/litellm && sudo docker compose logs litellm --since 15m 2>&1 | grep -iE "error|no api key" | grep -v register_model | tail'
  ```
- Health endpoints: `GET /health/latest`, `GET /health/readiness/details`.

## Models — list, inspect, add, delete

```sh
B="$LITELLM_PROXY_API_BASE"; K="$LITELLM_PROXY_API_KEY"
curl -s "$B/v1/models" -H "Authorization: Bearer $K"          # what's served (any key)
curl -s "$B/model/info" -H "Authorization: Bearer $MASTER"    # FULL params incl custom_llm_provider (master key)
```
Two kinds of model live here: ones in **`config.yaml`** (git source of truth) and
ones added via the **UI/API** (stored in Postgres, because `STORE_MODEL_IN_DB=True`).
Both show up in `/v1/models`. Add/delete + the throwaway-test pattern (isolate a fix
without touching live models) → **references/api-map.md**.

## Embeddings — tickle and measure

```sh
B="$LITELLM_PROXY_API_BASE"; K="$LITELLM_PROXY_API_KEY"
curl -s "$B/v1/embeddings" -H "Authorization: Bearer $K" -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen3-Embedding-4B","input":"dead channel"}' | python3 -c "
import sys,json,math
v=json.load(sys.stdin)['data'][0]['embedding']
print('dims',len(v),'| L2',round(math.sqrt(sum(x*x for x in v)),4))
"
```
Known shapes on Ember: **Qwen3-Embedding-4B = 2560 dims**, **nomic-embed-text-v1.5 =
768 dims**, both pre-normalized (L2 ≈ 1.0).

## Gotchas (the gold — earned the hard way Jul 5 2026)

- **⭐ Embedding models MUST use provider `openai`, NOT `custom_openai`.** LiteLLM's
  "custom OpenAI" / "OpenAI-Compatible Endpoints" UI choice stores
  `custom_llm_provider: custom_openai`, which routes **chat** fine but is **unmapped
  for `/embeddings`** → `BadRequestError: Unmapped LLM provider for this endpoint...
  custom_llm_provider=custom_openai`. Fix: add the model as a plain **OpenAI** model
  with a custom base URL (provider `openai` handles a custom `api_base` AND
  embeddings). Equivalent in config: `model: openai/<name>` (the `openai/` prefix) or
  `custom_llm_provider: openai`.
- **`/spend/logs/v2` requires start+end dates** or 400s. The v1 `/spend/logs` does
  not. Use v2 to browse, v1-by-id to read content.
- **The empty top-level `messages` field** in a log row is a trap — real prompt is in
  `proxy_server_request.body.messages`, real reply in `response.choices[0]`.
- **`store_prompts_in_spend_logs: true`** is required for any message content to be
  logged at all (UI or API). Off by default (privacy).
- **Blank-model failures = auth rejections**, not broken inference (see triage).
- **Docker needs sudo on Primer** — `ubuntu` isn't in the docker group:
  `sudo docker compose ...`.
- **Don't pin image `:latest` blindly**, and note the `litellm` and `litellm-database`
  images DON'T share tags (a `main-vX` that exists for one may 404 for the other).
- After editing `config.yaml`: `sudo docker compose restart litellm` re-reads it.

## Deeper reference

Read **references/api-map.md** for: the full 523-endpoint API taxonomy (it's a whole
platform — MCP gateway, vector stores, batch, guardrails, the `/v1/messages`
Anthropic passthrough), model add/delete + throwaway-test recipes, minting keys,
OpenRouter provider-pinning (`extra_body.provider.order`), and the stack layout /
rebuild.
