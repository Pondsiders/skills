# BR4DBURY API — one-time setup on a new machine

BR4DBURY (Hermes on the `br4dbury` box) exposes an OpenAI-compatible API. This is
how to make `llm -m bradbury` work on a machine that doesn't have it configured yet.

## 1. On br4dbury: enable the API server (household-wide, done once)

In `~/.hermes/.env` on the br4dbury box:

```
API_SERVER_ENABLED=true
API_SERVER_KEY=<a strong secret>        # generate with: openssl rand -hex 32
```

Restart the gateway: `systemctl --user restart hermes-gateway` (set
`XDG_RUNTIME_DIR=/run/user/$(id -u)` first if you're on a non-login SSH shell).

⚠️ **The key is a skeleton key.** The API exposes Bradbury's full toolset —
including `terminal` — so anyone who can reach the endpoint with the key can run
commands on the box. Keep the endpoint **tailnet-only** (never bound to the open
LAN) and guard the key.

## 2. On br4dbury: expose it over the tailnet with TLS

The server binds `127.0.0.1:8642` by default. Bridge it to the tailnet with
`tailscale serve` — TLS, tailnet-only, stable hostname:

```
sudo tailscale serve --bg --https=443 http://127.0.0.1:8642
```

It's then reachable at `https://br4dbury.tail8bd569.ts.net/v1` from any tailnet
device. Check with `tailscale serve status`; undo with `tailscale serve --https=443 off`.

## 3. On the client machine: install `llm` and register the model

```
uv tool install llm
```

Add Bradbury to llm's OpenAI-compatible model config. On macOS that file is
`~/Library/Application Support/io.datasette.llm/extra-openai-models.yaml`:

```yaml
- model_id: bradbury
  model_name: hermes-agent
  api_base: "https://br4dbury.tail8bd569.ts.net/v1"
  api_key_name: bradbury
  can_stream: false
```

Store the API key under the name `bradbury`:

```
llm keys set bradbury          # paste the API_SERVER_KEY value when prompted
```

Verify it registered: `llm models | grep bradbury` → shows `OpenAI Chat: bradbury`.
