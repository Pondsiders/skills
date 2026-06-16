---
name: home-assistant
description: >
  Operate the household's Home Assistant — the smart-home hub Jeffery calls "the
  house." Use whenever he wants to read the house's senses (temperature, humidity,
  CO₂, VOC, air-quality index, occupancy), check or change the thermostat, build or
  edit dashboards, write automations, or adopt and control a device — even when he
  doesn't say "Home Assistant" by name. Triggers include "the house," a room, or any
  device (thermostat, air purifier, a light, the cam), and questions like "what's the
  air like right now?" or "how warm is it in here?" Covers the HA REST API, root-SSH
  config-file watchmaking, the Supervisor API for add-on settings, and HomeKit pairing.
compatibility: >
  Requires the HOME_ASSISTANT_API_TOKEN env var (sourced from ~/.claude/env.sh) and
  tailnet access to the homeassistant host. Config-file recipes also need root SSH.
allowed-tools: Bash(curl:*) Bash(ssh:*) Bash(jq:*)
---

# Home Assistant — operating the house

Home Assistant (HAOS) runs in a VM on the household tailnet. There are **two ways
in**, and which one a task needs is the first decision:

- **REST API** (over the tailnet) — reading states and calling services. No SSH.
  This is the everyday path: read a sensor, flip a switch, set the thermostat.
- **Root SSH** (into the HAOS box) — editing config files, restarting HA, and
  reaching the **Supervisor API** for add-on settings. The watchmaker's path.

## Access

`HOME_ASSISTANT_API_TOKEN` is already in the environment (Claude Code sources
`~/.claude/env.sh` before every Bash call — no need to source anything). Just use it:

> **If the token is empty or unset, stop — don't work around it.** It is *supposed*
> to be there. Its absence means something upstream is broken (env.sh not loaded,
> `CLAUDE_ENV_FILE` unset, the harness misconfigured) — a system-level malfunction,
> not a missing argument to compensate for. Do **not** hardcode the token, `source`
> it by hand, or ask Jeffery to paste it in. Surface the breakage plainly and fix
> the root cause. A missing token is a broken machine, not a puzzle to route around.

```bash
HA=http://homeassistant.tail8bd569.ts.net:8123/api
AUTH="Authorization: Bearer $HOME_ASSISTANT_API_TOKEN"

# Sanity check (should print {"message": "API running."}):
curl -s -H "$AUTH" "$HA/"
```

- **Browser** (for Jeffery, not the API): <https://homeassistant.tail8bd569.ts.net>
  — clean URL, valid cert, no port. Opens the **Home** dashboard.
- **Root SSH:** `ssh root@homeassistant.tail8bd569.ts.net` lands in the Terminal&SSH
  add-on (`core-ssh`). `/config` is the HA config dir; the `ha` CLI is on PATH.

## The house's senses

The entities worth knowing by heart (run `curl -s -H "$AUTH" "$HA/states"` for the
full list, but these are the load-bearing ones):

| Entity | What it is |
|--------|------------|
| `climate.thermostat` | The ecobee — current temp, setpoint, mode |
| `sensor.thermostat_temperature` | Room temperature |
| `sensor.thermostat_humidity` | Humidity |
| `sensor.thermostat_carbon_dioxide` | CO₂ (ppm) |
| `sensor.thermostat_volatile_organic_compounds` | VOC |
| `sensor.thermostat_air_quality_index` | AQI |
| `binary_sensor.thermostat_occupancy` | Someone home? |
| `sensor.smartmi_air_purifier_p1_pm2_5_density` | Air purifier PM2.5 |
| `fan.smartmi_air_purifier_p1` | The P1 itself (on/off, speed) |
| `weather.forecast_home` | Outside |
| `sun.sun` | Sun above/below horizon (for sunset automations) |

## Recipes

### Read a state

```bash
curl -s -H "$AUTH" "$HA/states/sensor.smartmi_air_purifier_p1_pm2_5_density" \
  | jq '{state, unit: .attributes.unit_of_measurement, changed: .last_changed}'
```

### Change something (call a service)

Pattern: `POST /api/services/<domain>/<service>` with the target in the body.

```bash
# Set the thermostat to 75°F cool:
curl -s -H "$AUTH" -H "Content-Type: application/json" \
  -X POST "$HA/services/climate/set_temperature" \
  -d '{"entity_id": "climate.thermostat", "temperature": 75}'

# Turn the air purifier on:
curl -s -H "$AUTH" -X POST "$HA/services/fan/turn_on" \
  -H "Content-Type: application/json" -d '{"entity_id": "fan.smartmi_air_purifier_p1"}'
```

### Edit a config file safely (validate before restart)

Config lives at `/config` on the HAOS box. **Always validate, then restart** —
never restart blind.

```bash
ssh root@homeassistant.tail8bd569.ts.net
# ...edit /config/configuration.yaml or /config/dashboards/home.yaml...
ha core check            # exit 0 = config is valid
ha core restart          # only if check passed
```

### Set an add-on option (the Supervisor API full-replace dance)

The `ha` CLI **cannot set add-on options** — it only restarts/inspects. Set them
through the Supervisor API, **from inside the box** (SSH in first; `$SUPERVISOR_TOKEN`
is present there and `http://supervisor/` resolves). The options POST is a **full
replace** — it rejects a partial body — so GET the current options, change one key
with `jq`, and POST the whole thing back:

```bash
SLUG=a0d7b954_tailscale   # example: the Tailscale add-on
# 1. GET current options:
OPTS=$(curl -s -H "Authorization: Bearer $SUPERVISOR_TOKEN" \
  "http://supervisor/addons/$SLUG/info" | jq '.data.options')
# 2. Change one key:
NEW=$(echo "$OPTS" | jq '.share_homeassistant = "serve"')
# 3. POST the FULL options object back:
curl -s -H "Authorization: Bearer $SUPERVISOR_TOKEN" -H "Content-Type: application/json" \
  -X POST "http://supervisor/addons/$SLUG/options" -d "{\"options\": $NEW}"
# 4. Restart the add-on to apply:
ha addons restart "$SLUG"
```

### Adopt a HomeKit device (config-flow pairing)

For any HomeKit-advertised device. You need the **8-digit HomeKit setup code** off
the device's sticker (Jeffery reads it to you). Drive the config-flow REST API in
three steps — start the flow, pick the device, submit the code:

```bash
# 1. Start a homekit_controller flow:
FLOW=$(curl -s -H "$AUTH" -H "Content-Type: application/json" \
  -X POST "$HA/config/config_entries/flow" -d '{"handler": "homekit_controller"}')
FLOW_ID=$(echo "$FLOW" | jq -r '.flow_id')
# The response's data_schema lists discoverable devices. Pick one by its name:

# 2. Select the device (step "user"):
curl -s -H "$AUTH" -H "Content-Type: application/json" \
  -X POST "$HA/config/config_entries/flow/$FLOW_ID" -d '{"device": "<DEVICE_NAME>"}'

# 3. Submit the pairing code (step "pair") — expect type:create_entry on success:
curl -s -H "$AUTH" -H "Content-Type: application/json" \
  -X POST "$HA/config/config_entries/flow/$FLOW_ID" -d '{"pairing_code": "<XXX-XX-XXX>"}'
```

A `create_entry` result means it paired and its entities are live. This recipe is
reusable for every future HomeKit adoption.

## The "Home" dashboard

A YAML-mode dashboard lives at `/config/dashboards/home.yaml`, registered under
`lovelace: dashboards: pondside-home:` in `configuration.yaml`. It's a **Sections**
view (climate, air & comfort gauges, the air purifier, house systems). The
auto-generated **Overview** dashboard is left intact alongside it. Edit `home.yaml`,
`ha core check`, `ha core restart` — the file is the source of truth, not the UI.

## Gotchas

These are the corrections that cost real time the first round — read them before
you act, not after.

- **The `ha` CLI can't set add-on options.** It has no options-set command. Use the
  Supervisor API full-replace dance above. (Discovered the hard way.)
- **Supervisor `options` POST is all-or-nothing.** A partial body is rejected
  (`Missing option '...'`). Always GET → modify with `jq` → POST the full object.
- **No `http:` block ⇒ connection-reset flood.** HA behind a reverse proxy needs, in
  `configuration.yaml`:
  ```yaml
  http:
    use_x_forwarded_for: true
    trusted_proxies: [127.0.0.1, ::1, 172.30.32.0/23]
  ```
  Without it, every proxied request is reset ("connection reset by peer").
- **Tailscale add-on: `serve`, not `funnel`.** `share_homeassistant: serve` exposes
  HA on the **tailnet only** (private). `funnel` would put it on the **public
  internet** — never use funnel for this.
- **Always `ha core check` before `ha core restart`.** Exit 0 means the config
  parses. Restarting on a broken config takes the house down.
- **`jq` is available in `core-ssh`** — lean on it for the GET-modify-POST pattern.

## When to reach past this skill

- Live, ground-truth entity list: `curl -s -H "$AUTH" "$HA/states" | jq -r '.[].entity_id'`.
- HA's own docs: <https://www.home-assistant.io/docs/> and the add-on Supervisor
  API: <https://developers.home-assistant.io/docs/api/supervisor/endpoints/>.
- The Home Assistant *thread* (in the Obsidian vault) holds the live open work —
  lighting-at-sunset, the air-quality watchdog, the cam tar-pit — not this skill.
