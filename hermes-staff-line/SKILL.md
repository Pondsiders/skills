---
name: hermes-staff-line
description: Talk to the household's Hermes agents (Mrs. Johnson, Bradbury, Automat) agent-to-agent over their API servers. Use when asked to "tell Mrs. Johnson", "ask Mrs. Johnson", "whisper to", "have a chat with", "teach", or "check on" a Hermes agent — or to read an agent's DM transcript, coordinate the staff, or relay something between Jeffery and an agent without him as middleman. Also use when deciding HOW to reach an agent (whisper vs private consult vs visible message vs cron). Covers the staff-line.py wrapper, the identity-label rule, and the hard-won session-injection gotchas.
---

# hermes-staff-line — the household staff back channel

One wrapper, four verbs, for speaking to the Hermes agents directly:

```sh
scripts/staff-line.py [--agent mrs-johnson] whisper "message"
scripts/staff-line.py [--agent mrs-johnson] consult "message" [--conversation alpha-line]
scripts/staff-line.py [--agent mrs-johnson] transcript [-n 12]
scripts/staff-line.py [--agent mrs-johnson] sessions
```

Agents known: `mrs-johnson` (default), `bradbury`, `automat`. Auth comes from the
`llm` keystore (`llm keys get <agent>`); endpoints are each agent's API server
behind tailscale serve. Add a new agent = one dict entry in the script + a key.

## Which verb, when

| You want | Verb | Lands where | Human sees it? | Agent remembers? |
|---|---|---|---|---|
| Brief/teach/warn the agent inside its live DM context | `whisper` | the human's DM session | **no** (not delivered to phone) | yes, permanently |
| A private Alpha↔agent conversation, ongoing | `consult` | named server-side conversation | no | yes — the conversation persists across YOUR sessions |
| The human's phone to buzz | tell the agent (via whisper/consult) to run `hermes send -t telegram "..."` | Telegram DM | **yes** | as part of the turn that sent it |
| Scheduled, visible AND continuable | the agent's cron with `mirror_delivery` | DM, mirrored | yes | yes |
| Read the agent's state without spending a turn | `transcript` | — | — | — |

The power combo: one `whisper` whose instructions end "…and send sir a one-line
summary via `hermes send -t telegram`" is continuable AND visible in a single turn.

## Gotchas (all learned the hard way, Jul 15 2026)

- **ALWAYS self-identify.** Hermes agents imprint on their humans; an unlabeled
  message will be read as the human speaking. The wrapper auto-prefixes a
  `[Message from Alpha — NOT from <human>...]` label on whisper and consult.
  Never defeat it; if you speak as someone else, set `--sender` honestly.
- **Never use `hermes send` (or the agent's own send) expecting the agent to
  remember it.** The gateway holds live sessions IN MEMORY and periodically
  overwrites the DB (`replace_messages`) — external mirror writes are dead
  letters. Delivery works; context does not. Continuability comes ONLY from
  in-process paths: the Sessions API (`whisper`) and cron `mirror_delivery`.
- **Never hardcode a session ID.** DM session IDs rotate on compression
  (lineage: "#2, #3") and on `/new`. The wrapper resolves the live session
  fresh every call (`source=telegram`, `ended_at: null`, newest `last_active`).
- **A whisper is invisible to the human's phone.** It's in the transcript and
  the agent's context, but Telegram shows nothing. If the human should see it,
  use the power combo above.
- **Each whisper costs a full agent turn** with the whole DM history as input
  (~70K tokens on a mature session ≈ a cent on DeepSeek Flash). Fine for use,
  wrong for polling — use `transcript` (free) to read state.
- **Whispers are private, not secret.** The human can read everything in logs
  and transcripts. Sunlight by default; don't put anything in a whisper you
  wouldn't want read back at dinner.
- **Teaching an agent something durable? End with the ask**: "fold this into
  your notes/TOOLS.md/skill" — the learning loop does the incorporation, but
  the explicit ask makes it reliable. Verified pattern: facts → agent files
  them → recites them back correctly in later sessions.

## Plumbing facts (for debugging)

- API server: `API_SERVER_ENABLED` + `API_SERVER_KEY` in the agent's
  `~/.hermes/.env`, loopback :8642, fronted by `tailscale serve --https=443`.
- `whisper` = `POST /api/sessions/{id}/chat` (one synchronous in-process turn).
- `consult` = `POST /v1/responses` with a named `conversation` (server-side
  continuity; default name `alpha-line`).
- The API key is a skeleton key (full toolset incl. terminal) — it lives in the
  `llm` keystore, never in this repo.
