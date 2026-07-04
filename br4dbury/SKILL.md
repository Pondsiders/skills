---
name: br4dbury
description: >
  Talk to BR4DBURY — the household's intelligent house — from the command line.
  Use whenever you want to ask the apartment about itself or have it act: how the
  house is doing, whether it's warm / stuffy / about to overheat, the air quality,
  which doors or windows are open, where Kylee or Miss Mittenhaver (the cat) are,
  who's home — or to turn lights / fans / the thermostat on or off. Trigger on "ask
  the house," "how's it at home," "is it hot in here," "where's the cat," "close the
  blinds," a weather-aware comfort question, or any question a smart house that can
  read its own sensors would answer — even when BR4DBURY isn't named. Reach him
  through the `llm` CLI as the model `bradbury`.
compatibility: >
  Requires the `llm` CLI with the `bradbury` model configured, plus tailnet access
  to the br4dbury host. First-time setup (install + model config + tailscale-serve
  bridge) is in references/setup.md. No secret lives in this repo — the API key is
  kept in llm's local key store.
allowed-tools: Bash(llm:*)
---

# Talking to BR4DBURY

BR4DBURY is the household's intelligent house — a Hermes agent on the `br4dbury`
box with live Home Assistant **senses** (climate, air quality, doors and windows,
the cat, everyone's location) and **hands** (lights, fans, thermostat). He's exposed
as an OpenAI-compatible API (tailnet-only) and wired into the `llm` CLI as the model
`bradbury`. This skill is how you talk to him from the command line.

## Talk to him

One-shot question:

```
llm -m bradbury "How's the house right now?"
```

Every reply is **grounded** — a curated block of live sensor readings is injected
into his context each turn, so ask natural questions and take his *conclusions*, not
raw numbers:

- "Is it going to get hot in here this afternoon?" → a forecast-aware verdict
- "Where's Kylee?" / "Where's Miss Mittenhaver?" → from the device / cat trackers
- "Is the air okay?" → CO₂ / PM2.5 / AQI, characterized rather than dumped
- "Turn off the bedroom lights." / "Set the living-room fan to low." → he actuates via HA

Continue the thread (llm resends history client-side):

```
llm -c "...and close the guest-room door if it's open"
```

Interactive REPL: `llm chat -m bradbury`. Everything is logged in llm's own SQLite
log (`llm logs`).

## Good to know

- Each `llm -m bradbury` call is a **stateless** chat completion — the whole
  conversation is sent per call (that's why `llm -c` works: it resends history).
  Bradbury's own long-term memory persists server-side regardless.
- API-Bradbury is the **same agent** as Telegram-Bradbury — shared memory and skills,
  just a different conversation window. Ask him the way you'd ask in the family chat.
- Streaming is off for this model (`can_stream: false` in the config). Hermes's
  streamed responses carry custom events; plain non-streaming is simplest for a CLI
  and just as fast here.

## First time on this machine?

If `llm -m bradbury` reports an unknown model, `llm` isn't set up here yet — read
**references/setup.md** for the one-time install, model registration, and the
`tailscale serve` bridge.
