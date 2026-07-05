# LiteLLM gateway — deep reference

Read this when the SKILL.md core isn't enough: the full API surface, model
management recipes, key minting, provider pinning, and the stack layout.

All examples assume:
```sh
B="$LITELLM_PROXY_API_BASE"; K="$LITELLM_PROXY_API_KEY"
# MASTER = the master key from /opt/stacks/litellm/.env on Primer (admin ops only)
MASTER=$(ssh ubuntu@primer.tail8bd569.ts.net 'grep LITELLM_MASTER_KEY /opt/stacks/litellm/.env' | cut -d\" -f2)
```

## The API is a whole platform, not just a gateway

`GET $B/openapi.json` returns **~523 endpoints** across ~90 tags. The ones that
matter to us:

- **chat/completions, completions, embeddings** — the OpenAI surface we actually use.
- **Budget & Spend Tracking** — `/spend/logs`, `/spend/logs/v2`, `/spend/calculate`,
  `/global/spend/*` (the logs live here; see SKILL.md).
- **key management** — `/key/generate`, `/key/info`, `/key/update`, `/key/delete`.
- **model management** — `/model/info`, `/model/new`, `/model/update`, `/model/delete`.
- **health** — `/health/latest`, `/health/readiness/details`.
- **anthropic_passthrough / `/v1/messages`** — native Anthropic protocol (what Claude
  Code speaks). This is the answer to Bifrost's broken Anthropic passthrough, if we
  ever want Claude Code to route through LiteLLM. Not wired as of Jul 5 2026.
- Plus a pile we don't use yet: an **MCP gateway** (33 endpoints), vector_stores,
  guardrails, batch, videos, evals, SCIM, assistants/threads, fine-tuning, and
  per-provider pass-throughs (Vertex, Bedrock, Cohere, Mistral, …).

Map the whole thing yourself when curious:
```sh
curl -s "$B/openapi.json" | python3 -c "
import sys,json
from collections import defaultdict
p=json.load(sys.stdin)['paths']; t=defaultdict(list)
for path,ms in p.items():
    for m,info in ms.items():
        if m in ('get','post','put','delete','patch'):
            t[info.get('tags',['?'])[0]].append(f'{m.upper()} {path}')
for tag in sorted(t,key=lambda x:-len(t[x])): print(f'{len(t[tag]):3} {tag}')
"
```

## Model management

Inspect full stored params (shows `custom_llm_provider`, `api_base`, `model`, and
`model_info` incl. the auto-derived `mode` — note `mode` is derived, not a lever you
set):
```sh
curl -s "$B/model/info" -H "Authorization: Bearer $MASTER" | python3 -c "
import sys,json
for m in json.load(sys.stdin)['data']:
    lp=m['litellm_params']
    print(m['model_name'],'->',lp.get('custom_llm_provider'),'|',lp.get('model'),'|',lp.get('api_base'))
"
```

Add a model (master key). For an OpenAI-compatible endpoint, use the `openai/`
prefix so it routes as provider `openai` (works for chat AND embeddings — see the
big gotcha in SKILL.md):
```sh
curl -s "$B/model/new" -H "Authorization: Bearer $MASTER" -H "Content-Type: application/json" -d '{
  "model_name": "my-model",
  "litellm_params": {
    "model": "openai/Some/Model-Name",
    "api_base": "https://ember.tail8bd569.ts.net/v1",
    "api_key": "noop"
  }
}'   # returns {"model_id": "..."}
```

Delete by id:
```sh
curl -s "$B/model/delete" -H "Authorization: Bearer $MASTER" -H "Content-Type: application/json" \
  -d '{"id":"<model_id>"}'
```

### The throwaway-test pattern (isolate a fix without touching live models)
When a model config is misbehaving, don't mutate the live one and guess. Instead:
1. `/model/new` a `zz-test-*` model with the config you *think* is right.
2. Tickle it (`/v1/chat/completions` or `/v1/embeddings`).
3. If it works, you've proven the fix → apply to the real model or hand the exact
   change to Jeffery. If not, iterate on the throwaway.
4. `/model/delete` the throwaway.

This is how the `custom_openai`→`openai` embedding fix got proven on Jul 5 without
risking the real Qwen model. Facts-first, and no live blast radius.

## Minting an API key

```sh
curl -s "$B/key/generate" -H "Authorization: Bearer $MASTER" -H "Content-Type: application/json" -d '{
  "key_alias": "some-consumer",
  "metadata": {"purpose": "what this key is for"}
}'   # returns {"key": "sk-..."}
```
Optional: `"models": ["deepseek/deepseek-v4-flash"]` to scope a key to specific
models; `"rpm_limit"`, `"max_budget"`, etc. A key with a `key_alias` shows up in the
logs' `key_alias` filter — handy for per-consumer accounting.

## OpenRouter provider pinning

OpenRouter is an aggregator that fans a model out across many upstream providers,
and by default routes price-weighted — so which provider (and thus latency, and
whether you get caching) is a coin flip. To pin, put OpenRouter's provider-routing
controls in the model's `extra_body`:
```json
{
  "model": "deepseek/deepseek-v4-flash",
  "extra_body": {
    "provider": { "order": ["deepseek"], "allow_fallbacks": false }
  }
}
```
- `order: ["deepseek"]` = use the first-party DeepSeek endpoint (the only one that
  auto-caches, and the cheapest cache-reads).
- `allow_fallbacks: false` = *only* that provider (a hard pin, and a single point of
  failure). `true` = prefer it but survive an outage.

**When to pin (household stance, Jul 5 2026):** mostly don't. Caching savings on
DeepSeek are pennies/month (negligible), and free routing gives you automatic
failover. Reach for a pin only for **privacy** (steer a sensitive agent away from a
provider/jurisdiction, e.g. Hello Nurse's health data away from China-hosted
first-party DeepSeek) or a **speed floor** (pin to a fast provider like GMICloud
with `allow_fallbacks: true` if free-routed latency ever actually annoys). Observed
speed spread is real: DeepInfra ~11 tok/s vs GMICloud ~57 tok/s.

## The stack

`/opt/stacks/litellm/` on Primer, a Docker Compose stack (git source of truth,
secrets in a gitignored `.env`):
- **compose.yml** — three services: `tailscale` (sidecar, `hostname: litellm` →
  `litellm.tail8bd569.ts.net`), `db` (postgres:17), `litellm`
  (`ghcr.io/berriai/litellm-database`, bundles prisma). **All three share the
  tailscale netns** (`network_mode: service:tailscale` on db + litellm), so litellm
  reaches Postgres over `127.0.0.1`; Postgres is bound to `listen_addresses=127.0.0.1`
  so it never touches the tailnet.
- **config.yaml** — `model_list` (git-tracked models) + `general_settings`
  (`master_key`, `database_url`, `store_prompts_in_spend_logs: true`) +
  `litellm_settings`.
- **.env** — `LITELLM_MASTER_KEY`, `LITELLM_SALT_KEY` (⚠️ can't change after adding
  models — it encrypts stored credentials), `POSTGRES_PASSWORD`.
- **serve-config.json** — tailscale serve maps 443 → `127.0.0.1:4000`.

Ops:
```sh
ssh ubuntu@primer.tail8bd569.ts.net 'cd /opt/stacks/litellm && sudo docker compose ps'
ssh ubuntu@primer.tail8bd569.ts.net 'cd /opt/stacks/litellm && sudo docker compose restart litellm'   # re-read config.yaml
ssh ubuntu@primer.tail8bd569.ts.net 'cd /opt/stacks/litellm && sudo docker compose logs litellm --since 15m'
```
UI-added models live in Postgres (`STORE_MODEL_IN_DB=True`); config.yaml models are
git. Both appear in `/v1/models`. `docker` needs `sudo` (ubuntu isn't in the docker
group).
