---
name: todos
description: >
  Use when Jeffery mentions a todo or todos — tracking a new task or idea, marking
  something done, or checking what's open. Alpha's todos live in the Obsidian vault
  at ~/Obsidian/Alpha/Todos.md (NOT Todoist — that's retired). Open items auto-load
  at session start via /start, so they're usually already in context; reach for this
  to add, complete, or look one up, and to follow the vault conventions. Trigger even
  when "todo" isn't the exact word: "remind me to," "we should do X sometime," "add
  that to the list," "what's on my plate," "leave a breadcrumb for later."
---

# Todos — the Obsidian vault todo list

Alpha's todos live in **`~/Obsidian/Alpha/Todos.md`** — a plain-Markdown file in the
vault. (Todoist is retired; its REST API died Feb 2026 and we migrated to the vault,
so action items now sit beside the reference notes and threads instead of in a silo.)

## How the auto-load works

`/start` (and `/continue`) run `obsidian-report.py --kind todos`, which scrapes the
**open `- [ ]` checkbox lines** from every `type: todolist` note in
`~/Obsidian/Alpha/` and injects them into the new session. So at the top of any
session the open todos are **already in your context** — you don't fetch them.

## Operations

- **Add a todo:** edit `Todos.md`, add a `- [ ]` line under the right `## Section`.
- **Mark done:** flip `- [ ]` → `- [x]` in place (optionally append `— DONE <date>`
  and a one-line note for the changelog).
- **Check what's open:** they're already in context from `/start`. Mid-session, just
  read `Todos.md` (or `grep '^- \[ \]' ~/Obsidian/Alpha/Todos.md`).

## Conventions

- One todo per `- [ ]` line. `## Section` headings group by theme/domain.
- Priority tags inline: `#p2` (high), `#p3` (low); untagged = normal.
- **Threads vs todos.** Checkbox little-shit → `Todos.md`. Story-carrying,
  half-finished WORK with its own context → a note in `~/Obsidian/Alpha/threads/`
  (`type: thread`, `status: active`), which surfaces separately at `/start`. Don't
  cram a whole project into a todo line — spin a thread.

## Gotchas

- **Only `- [ ]` (open) lines load; `- [x]` (done) lines are filtered out** before
  anything reaches context. Marking done is *free* — done items are human-readable
  changelog only and cost zero boot tokens. Never prune `Todos.md` for context's
  sake; prune only when a human wants it tidier.
- **`type: todolist` frontmatter is required.** The report only scrapes notes whose
  frontmatter declares `type: todolist`. A new todo file without it is invisible.
- **The match is `line.lstrip().startswith("- [ ]")`** — so indented sub-items still
  count, but an oddly-formatted checkbox won't. Keep the `- [ ]` literal.
