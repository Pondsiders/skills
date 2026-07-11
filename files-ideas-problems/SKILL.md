---
name: files-ideas-problems
description: >
  Use when you and Jeffery track work in the Obsidian vault — the files / ideas /
  problems system. Reach for it when he asks what's open, what to do, or what's on
  his plate (the "what should we do?" emergency-tap → lead with the open files);
  when capturing or closing an idea or a problem; when opening, updating, or
  shelving a file; or when querying the pools. Trigger even when the words aren't
  exact: "I have an idea," "that's a problem," "log that," "what are we working on,"
  "what's on the desk," "add that to the pile," "what's next." Covers the note
  schemas, the desk metaphor, the Obsidian Bases, and the `base:query` commands.
---

# Files, ideas & problems — how Jeffery and Alpha track work

Our shared work lives in the Obsidian vault as three kinds of note, plus a fourth
that's background. The governing image is **the early-80s desktop**: some files are
*open on the desk*; the rest is filed away.

- **Files** = open work *on the desk*. Big multi-day tinkers with a living state.
  They carry a tiny weight — an open file is clutter, so we either work it or shelf
  it. When Jeffery asks *"what should we do?"* the **first answer is the open files.**
- **Problems** = the *burr pool*. Things that are wrong and want fixing. A problem
  nags honestly — that's its job.
- **Ideas** = the *generative pool*. Optional, fun, might-build. An idea just waits.
- **Reference** = the *library* — things Alpha knows, loaded just-in-time. Background,
  not work. (Documented in the owner's manual, not here.)

**The emergency-tap is the whole point.** Jeffery gets stressed when he doesn't know
what to do. So "what should we do?" / "what's open?" / "what's on my plate?" →
lead with the **open files** (the desk), then offer the pools. Give him a real,
finite thing to consider, not a wall.

## The lifecycle (why this scales and `Todos.md` didn't)

A thing *flows*, and every stage has an exit:

```
idea / problem  (the pools)  →  pick up a big one  →  FILE (the desk)  →  archive
small one? just do it "bam"   →  close it                                 or close
```

The old flat todo list only ever grew — check off, never delete. Here, live work
*leaves* the pool for a File, dead work *closes*, finished Files get *archived*. The
pools stay small because they're an inbox, not a graveyard. **Not everything is a
pipeline:** a small idea (the changelog agent) gets done in one go and closed —
it never opens a File. A big tinker (Lil Transformy Instruct, MONEY) opens a File
the moment we act on it.

## The three note types

### Files — `~/Obsidian/Alpha/Files/<NAME>/YYYY-MM-DD.md`
One folder per subject; a sequence of dated current-state snapshots. Only the latest
snapshot per folder loads at `/start`. A snapshot is *current state* — what's true
now, what changed, new observations — not the whole saga (the saga is the sequence
behind it). Finished or parked → move the whole folder to `Alpha/Files_Archive/`
(out of sight, still safe). This is what the `finish`/`handoff` rituals update.

### Problems — `~/Obsidian/Problems/<name>.md`
```yaml
---
type: problem
status: open        # open → closed (flip; do NOT delete — keep the record)
urgency: low        # low | medium | high — the honest priority
---
```
The body is a **living investigation log** — it accumulates what we've seen and
tried. Solve it → `status: closed`, and it vanishes from the pool (the Base filters
`status != "closed"`) but survives on disk as the record of how we fixed it.

### Ideas — `~/Obsidian/Ideas/<name>.md`
```yaml
---
type: idea
status: open        # open → closed when done or abandoned (keep the record)
---
```
Body stays *light* — a seed, not a plan. No priority (that's fake pressure on an
optional thing). Ideas close, they don't get deleted.

## The Obsidian Bases + querying them

Each pool is an Obsidian **Base** (a YAML view-definition file at the vault root):
`Ideas.base` filters `type == "idea"`; `Problems.base` filters `type == "problem"`
AND `status != "closed"`. Query them headless:

```sh
cd ~/Obsidian
obsidian base:query file=Ideas.base       # the idea pool
obsidian base:query file=Problems.base    # the open problems
obsidian base:query path=Problems.base format=json   # same, as JSON
```

To read, write, or edit a note, lean on the harness **Read / Write / Edit** tools —
that's their job, use them for all file I/O. Use the `obsidian` CLI for CLI-shaped
work (querying Bases, vault operations), *not* for reading and writing files. A new
note is a `Write` of the right `type:` frontmatter into the right folder; the Base
picks it up automatically.

## The discipline (this is the load-bearing part)

- **A note states what's TRUE, not what you infer.** Hedge honestly — "*maybe* a
  leak," "*if* it's a leak it's slow." Don't carve a diagnosis or a fix you haven't
  earned. If you're unsure whether it's even a problem, say so — often "we don't
  know because we never asked" is the truest line in the note.
- **A problem note's first step is the cheapest probe, not the cure.** "Bump the
  version, might already be fixed" beats "build a reload cron." Verify before acting;
  investigate before diagnosing. (Facts-first, in a file.)
- **Don't write down an *urge*.** An idea worth capturing is crisp. A foggy "I kind
  of want a thing like…" isn't ready — leave it until it sharpens.
- **Keep the pools honest.** Prune non-problems (a noisy log line isn't a problem)
  so the "what should we do?" answer stays a clarifier, not a wall. Triage when you
  notice; no system needed.
- **Closing is a conversation, not a solo autonomy.** Propose note changes and let
  Jeffery 👍 or rein you in — especially when updating shared state.

## Gotchas

- **`base:query` REQUIRES the `.base` extension.** `file=Problems.base` works;
  `file=Problems` fails "Base file not found." (`base:views` is lenient; `base:query`
  is not.) Reliable form: `obsidian base:query path="X.base" format=json`.
- **`base:query` JSON flattens YAML lists to comma-strings** — a `domain: [a, b]`
  comes back as `"a, b"`, not `["a","b"]`. For a faithful array, read the note's
  frontmatter directly, not the Base output.
- **The Base filters on `type:`** — a note missing the right `type` frontmatter is
  invisible to its pool. A new problem without `type: problem` won't show.
- **Closed items drop out automatically.** Both `Problems.base` and `Ideas.base`
  filter `status != "closed"`, so closing a note (not deleting it) removes it from
  its pool while keeping the record on disk. That's the anti-cruft mechanism — the
  pool shows only open work.
- **Paths are Alpha's vault** (`~/Obsidian/Alpha/Files`, `~/Obsidian/Problems`,
  `~/Obsidian/Ideas`). Another agent (Rosemary) adapting this system points at her
  own vault.
