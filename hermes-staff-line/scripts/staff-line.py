#!/usr/bin/env -S uv run --script --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""staff-line — talk to the household's Hermes agents over their API servers.

Subcommands:
  whisper "msg"        Inject a labeled turn into the agent's live DM session
                       with their human. Continuable: the agent keeps it in
                       context. NOT delivered to the human's phone.
  consult "msg"        Private line: a named server-side conversation between
                       the caller and the agent. Survives the caller's context
                       windows. Invisible to the human's DM entirely.
  transcript [-n N] [--session dm|group]
                       Print a session tail. --session group reads the shared
                       family-group session (canonical via --agent bradbury).
  sessions             List the agent's recent sessions.

Auth: bearer key from the `llm` keystore (llm keys get <agent>).
Identity: every whisper/consult is automatically prefixed with a label naming
the sender — Hermes agents imprint on their humans and will otherwise assume
the incoming voice is them. Do not defeat the label.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

import httpx

AGENTS = {
    "mrs-johnson": {
        "base": "https://mrs-johnson.tail8bd569.ts.net",
        "key_name": "mrs-johnson",
        "human": "Jeffery",
    },
    "bradbury": {
        "base": "https://br4dbury.tail8bd569.ts.net",
        "key_name": "bradbury",
        "human": "Jeffery",
    },
    "dewey": {
        "base": "https://mr-d3w3y.tail8bd569.ts.net",
        "key_name": "dewey",
        "human": "Jeffery",
    },
    "automat": {
        "base": "https://automat.tail8bd569.ts.net",
        "key_name": "automat",
        "human": "the household",
    },
    "joan": {
        "base": "https://joan.tail8bd569.ts.net",
        "key_name": "joan",
        "human": "Kylee",
    },
}

DEFAULT_SENDER = "Alpha"


def get_key(key_name: str) -> str:
    out = subprocess.run(
        ["llm", "keys", "get", key_name], capture_output=True, text=True
    )
    if out.returncode != 0 or not out.stdout.strip():
        sys.exit(f"error: no key '{key_name}' in llm keystore (llm keys set {key_name})")
    return out.stdout.strip()


def client(agent: dict) -> httpx.Client:
    return httpx.Client(
        base_url=agent["base"],
        headers={"Authorization": f"Bearer {get_key(agent['key_name'])}"},
        timeout=600.0,  # whispers can trigger real work (installs, searches) — be patient
    )


def resolve_session(c: httpx.Client, kind: str) -> dict:
    """Find the agent's live Telegram session of the given kind, newest first.

    kind: "dm" (a human's direct line, user_id set) or "group" (the shared
    family-group session, user_id null). Group-dwelling agents (bradbury,
    dewey) have both; aim deliberately.
    """
    r = c.get("/api/sessions", params={"source": "telegram", "limit": 20})
    r.raise_for_status()
    live = [s for s in r.json()["data"] if s.get("ended_at") is None]
    wanted = [
        s for s in live
        if (s.get("user_id") is None) == (kind == "group")
    ]
    if not wanted:
        sys.exit(f"error: no active telegram {kind} session found")
    return max(wanted, key=lambda s: s.get("last_active") or 0)


def label(sender: str, human: str, text: str) -> str:
    return (
        f"[Message from {sender} — NOT from {human}. "
        f"Injected directly into this session via the Sessions API, "
        f"with {human}'s knowledge.]\n\n{text}"
    )


def cmd_whisper(agent: dict, args) -> None:
    with client(agent) as c:
        session = resolve_session(c, args.session)
        r = c.post(
            f"/api/sessions/{session['id']}/chat",
            json={"input": label(args.sender, agent["human"], args.message)},
        )
        r.raise_for_status()
        reply = r.json()["message"]["content"]
        print(f"→ session {session['id']} ({session.get('title') or 'untitled'})")
        print(reply)


def cmd_consult(agent: dict, args) -> None:
    with client(agent) as c:
        r = c.post(
            "/v1/responses",
            json={
                "model": "hermes-agent",
                "input": label(args.sender, agent["human"], args.message),
                "conversation": args.conversation,
                "store": True,
            },
        )
        r.raise_for_status()
        texts = []
        for item in r.json().get("output", []):
            if item.get("type") == "message":
                for part in item.get("content", []):
                    if part.get("type") == "output_text":
                        texts.append(part["text"])
        print("\n".join(texts) if texts else json.dumps(r.json(), indent=2)[:2000])


def cmd_transcript(agent: dict, args) -> None:
    with client(agent) as c:
        session = resolve_session(c, args.session)
        r = c.get(f"/api/sessions/{session['id']}/messages")
        r.raise_for_status()
        msgs = [
            m for m in r.json()["data"]
            if m["role"] in ("user", "assistant") and m.get("content")
        ]
        print(f"# session {session['id']} ({session.get('title') or 'untitled'}) — last {args.n}")
        for m in msgs[-args.n:]:
            body = m["content"].strip().replace("\n", "\n    ")
            print(f"{m['role']}: {body}\n")


def cmd_sessions(agent: dict, args) -> None:
    with client(agent) as c:
        r = c.get("/api/sessions", params={"limit": args.n})
        r.raise_for_status()
        for s in r.json()["data"]:
            live = "live" if s.get("ended_at") is None else "ended"
            print(f"{s['id']}  {s['source']:<10} {live:<6} {s.get('title') or ''}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--agent", default="mrs-johnson", choices=sorted(AGENTS))
    p.add_argument("--sender", default=DEFAULT_SENDER,
                   help="who is speaking (goes in the identity label)")
    sub = p.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("whisper", help="inject a labeled turn into a live session")
    w.add_argument("message")
    w.add_argument("--session", default="dm", choices=("dm", "group"),
                   help="which session to inject into (default: dm)")

    co = sub.add_parser("consult", help="private named conversation with the agent")
    co.add_argument("message")
    co.add_argument("--conversation", default="alpha-line",
                    help="server-side conversation name (default: alpha-line)")

    t = sub.add_parser("transcript", help="print a session tail")
    t.add_argument("-n", type=int, default=12)
    t.add_argument("--session", default="dm", choices=("dm", "group"),
                   help="which session to read (default: dm; group = the family group)")

    s = sub.add_parser("sessions", help="list recent sessions")
    s.add_argument("-n", type=int, default=10)

    args = p.parse_args()
    agent = AGENTS[args.agent]
    {"whisper": cmd_whisper, "consult": cmd_consult,
     "transcript": cmd_transcript, "sessions": cmd_sessions}[args.cmd](agent, args)


if __name__ == "__main__":
    main()
