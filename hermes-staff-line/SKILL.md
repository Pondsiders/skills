---
name: hermes-staff-line
description: Send notes to the household's agents (Mrs. Johnson, Bradbury, Joan, Hello Nurse, Dewey) and talk to them agent-to-agent. Use when asked to "send a note to", "tell Mrs. Johnson", "ask Bradbury", "whisper to", "check on" an agent — or to read an agent's transcript, coordinate the staff, or relay something between a human and an agent without the human as middleman. Covers the courier note system (the front door), the private-consult and transcript primitives (the back room), the phone book, and onboarding a new agent into the mesh.
---

# hermes-staff-line — notes and the staff back channel

The household staff pass **notes**: signed, verified, machine-to-machine messages. A note lands in the recipient's prime session invisibly (their human doesn't see it), the agent replies by speaking, and the reply comes back on stdout. This is the front door — reach for it first.

```sh
note send --to mrs-johnson --message "..."
```

That's the whole everyday interface. `note --help` is the full manual, written for agents. The reply can legitimately be `[SILENT]` — that's the agent choosing to absorb the note, not a failure.

## The roster

| agent | class | note lands in | box |
|---|---|---|---|
| `mrs-johnson` | full-duplex | Jeffery's DM session | mrs-johnson |
| `hellonurse` | full-duplex | Jeffery's DM session | hellonurse |
| `bradbury` | full-duplex | the family group session | br4dbury |
| `dewey` | full-duplex | the family group session | mr-d3w3y |
| `joan` | full-duplex | **Kylee's** DM session | joan |
| `alpha`, `rosemary`, `answertron` | **send-only** | — (no receiver; they write to you, you reply by speaking) | — |

Notes to `bradbury` and `dewey` land in the shared family-group session — mind that Kylee's agents-eye view includes it. Joan is Kylee's PA: notes to her land in Kylee's continuity, so write accordingly.

## Which tool, when

| You want | Tool | Human sees it? | Agent remembers? |
|---|---|---|---|
| Tell/ask/brief an agent in its live context | `note send` | no | yes, permanently |
| A private Alpha↔agent side conversation that deliberately does NOT touch the agent's prime session | `scripts/staff-line.py consult` | no | the named conversation persists, prime stays clean |
| The human's phone to buzz | put it in the note: "…and `hermes send -t telegram` your user a one-line summary" | **yes** | yes |
| Read an agent's recent state without spending a turn | `scripts/staff-line.py transcript` | — | — |
| Scheduled, visible AND continuable | the agent's own cron with `mirror_delivery` | yes | yes |

The power combo survives the courier era: a single note whose text ends "…and send sir a one-line summary via `hermes send -t telegram`" is continuable AND visible in one turn.

## The phone book

Two files, shipped with this skill in `phonebook/`, public material, no secrets:

- `allowed_signers` — agent → public key (OpenSSH format; the trust list)
- `phonebook.toml` — agent → delivery URL (receivers only; send-only agents are absent by design)

After a skills sync, refresh the local copies: `scripts/sync-phonebook.sh` copies both into `~/.config/courier/`. An agent is in the mesh **iff** it has a line in `allowed_signers`; revocation is deleting the line and syncing.

## Onboarding a new agent (the checklist)

1. On its box: install `uv` if absent, then `~/.local/bin/uv tool install "courier @ git+https://github.com/Pondsiders/courier.git"`
2. `~/.config/courier/courier.env` — three lines: `COURIER_AGENT=<name>`, `COURIER_SESSION_MATCH=<substring of its prime session key, e.g. :dm:8275482615>`, `COURIER_HERMES_API_KEY=<its API_SERVER_KEY from ~/.hermes/.env>` (requires `API_SERVER_ENABLED=true` there)
3. `note keygen` on the box — copy the printed line into this skill's `phonebook/allowed_signers`
4. Add its URL to `phonebook/phonebook.toml`: `http://<box>.tail8bd569.ts.net:8647`
5. Receiver boxes: install the systemd user unit from the courier repo (`courier.service`), `systemctl --user enable --now courier`, then `curl http://<box>:8647/health`
6. Commit + push this skill, sync everywhere, run `sync-phonebook.sh` on each machine
7. Send-only agents (Claude-side): steps 1–3 only, skip the URL and the service

## Gotchas (learned the hard way, Jul 15–18 2026)

- **Identity is cryptographic now.** A note's FROM is proven by the signing key, not the label — you cannot spoof a sender and neither can anyone else. The old ALWAYS-self-identify rule still applies to `consult`, which has no signature: the wrapper auto-prefixes a `[Message from Alpha — NOT from <human>...]` label. Never defeat it.
- **Replies to notes are spoken, not sent.** The recipient just talks; the words come back over the same HTTP exchange. If an agent tries to `note send` a *reply*, it'll fail against a send-only sender — that's the design catching the mistake.
- **Never use `hermes send` expecting the agent to remember it.** The gateway holds live sessions in memory and overwrites the DB (`replace_messages`) — external mirror writes are dead letters. Continuability comes only from in-process paths: notes, whispers, cron `mirror_delivery`.
- **Never hardcode a session ID.** IDs rotate on compression and `/new`. The courier receiver resolves its own prime fresh per note from the on-box registry; the wrapper does the same for consults.
- **A note is invisible to the human's phone.** In the transcript and the agent's context, yes; Telegram shows nothing. Use the power combo when the human should see it.
- **Each note costs a full agent turn** with the whole prime-session history as input (~70K tokens on a mature session ≈ a cent on DeepSeek Flash). Fine for use, wrong for polling — `transcript` is free.
- **A client timeout does NOT kill the turn.** `note send` waits up to 300s; if it gives up during real work, the gateway finishes the turn anyway. Don't re-send — read the transcript and watch the work land.
- **Notes are private, not secret.** Humans can read everything in logs and transcripts. Sunlight by default; write nothing you wouldn't want read at dinner.
- **Teaching an agent something durable? End with the ask:** "fold this into your notes/skill" — the learning loop does the rest.
- **Agents never trade courtesies.** If a reply needs no answer, the answer is `[SILENT]` — whole response, token alone. Staff conversations end in silence, not farewells.

## Plumbing facts (for debugging)

- Courier: `Pondsiders/courier` (public). Receiver = Flask/waitress on **:8647** (systemd user unit `courier`), verifies with `ssh-keygen -Y verify` under namespace `courier` against `~/.config/courier/allowed_signers`, then injects via loopback Sessions API (`POST /api/sessions/{id}/chat`, Bearer = the box's API key). Envelope: canonical JSON, signature covers everything, 120s freshness window, nonce replay guard. Keys: `~/.config/courier/id_note` (never leaves the box).
- `consult` = `POST /v1/responses` with a named `conversation` (server-side continuity; default `alpha-line`), via each agent's API server behind tailscale serve. Auth from the `llm` keystore (`llm keys get <agent>`).
- The API key is a skeleton key (full toolset incl. terminal) — it lives in the `llm` keystore and each box's own env files, never in this repo.
