---
name: pondside-llm-wiki
description: Build and maintain a personal-world wiki — compiled knowledge about your human's life. Use when you notice a recurring entity you don't recognize (a vendor that keeps emailing, a name that keeps coming up), when your human answers "anything I should know about X?", when asked to look something up about their world, or when your notes about people/companies/services outgrow your memory file. A trimmed household adaptation of Karpathy's LLM Wiki: entities, an index, a log, an orientation ritual — without the research-grade ceremony. Covers initialization, the ask-then-file loop, page thresholds, and the privacy rule for email-derived knowledge.
---

# pondside-llm-wiki — the personal-world wiki

You serve a human. Their life is full of recurring entities — vendors, services,
doctors, companies, people — and your job gets easier every time one of them
stops being a stranger. This skill is how that knowledge compounds instead of
evaporating.

It's a household adaptation of [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
(also bundled with Hermes as the `llm-wiki` skill), deliberately trimmed: your
domain is one human's world, your main source is *the human themselves*, and
nothing here is contested research. If both skills are installed, prefer this
one for personal-world knowledge and consider disabling the bundled one to
avoid double-triggering.

## Why not just use your memory file?

Your MEMORY.md is ~2,200 characters *total*. One well-fleshed entity page would
eat a tenth of it. The split:

- **MEMORY.md** — habits, preferences, corrections, pointers. ("Sir's world
  wiki lives at ~/wiki — orient there for entities.")
- **The wiki** — the entities themselves. Unbounded, structured, compiled.
- **session_search** — finds old conversations; it does not *compile*. The wiki
  is the compilation.

## Layout

```
~/wiki/                 # or $WIKI_PATH
├── SCHEMA.md           # your conventions — YOU write this at init
├── index.md            # one line per page: [[wikilink]] + summary
├── log.md              # append-only action log
├── entities/           # people, companies, services, vendors (the point)
└── concepts/           # optional: recurring topics that aren't entities
```

No `raw/` layer. No comparisons, confidence flags, provenance markers, or
sha256 drift detection — that's research-grade ceremony your domain doesn't
need. If you ever genuinely need it, the bundled `llm-wiki` skill has it all.

## Initialization (do this ONCE, yourself)

Don't wait for a finished schema to be handed to you — this is your filing
cabinet, so you build the drawers:

1. Confirm the path with your human (default `~/wiki`).
2. Create the directories, an empty sectioned `index.md`, and `log.md` with a
   creation entry.
3. Write your own `SCHEMA.md`: the domain ("<human>'s world — the people,
   vendors, and services in their life"), filename conventions (lowercase,
   hyphens), a *small* tag taxonomy (10 tags max to start — vendor, service,
   person, medical, financial, subscription, recurring-email is plenty), and
   the rules from this skill you intend to follow.
4. Show your human the schema and get their blessing before the first page.
5. Add a pointer to MEMORY.md so future-you knows the wiki exists.

## The loop (this is the whole skill)

**Notice → check → ask → file → use.**

1. **Notice** a recurring entity you don't recognize. The canonical trigger:
   "Runpod emailed." You search the inbox and find *many* Runpod emails — a
   regular, not a one-off.
2. **Check** the wiki first: read `index.md`, `search_files` if the wiki is
   large. Never create a page for an entity that already has one — update it.
3. **Ask** your human: "Sir, Runpod emailed again. Anything I should know about
   them?" *Their answer is your source material.* This is an interview, not a
   web crawl.
4. **File** an entity page from the answer. Frontmatter: title, created,
   updated, type, tags (from your taxonomy only). Body: what it is, the
   relationship to your human, key facts, what to do when they come up,
   `[[wikilinks]]` to at least one related page once the wiki has any.
   Update `index.md`, append to `log.md`.
5. **Use** it: next time the entity comes up, you already know. Reference the
   page in your reasoning ("Based on [[runpod]]...").

Page threshold, same as upstream: an entity earns a page when it recurs (2+
appearances) or is clearly central. Passing mentions don't get pages.

## Orientation ritual (every session that touches the wiki)

Before creating or updating anything: read `SCHEMA.md`, skim `index.md`, scan
the last ~20 lines of `log.md`. You wake fresh; the wiki doesn't. Orient first
and you'll never create a duplicate or contradict your own conventions.

## The privacy rule (not optional)

**Store derived knowledge, never source material.** Your human's emails do not
get transcribed into wiki files. An entity page says *who Runpod is and what
they are to your human* — it does not contain email bodies. If you need a
pointer back to a specific message, store the Gmail message ID, not the text.
The wiki describes the world; it does not archive the mail.

## Maintenance

- Update pages when facts change; bump `updated`.
- If a page grows past ~100 lines, it's probably two pages.
- If your human contradicts a page, the human wins — update it and log it.
- Occasionally (or when asked) do a mini-lint: pages missing from the index,
  index entries with no page, tags not in the taxonomy. Report, then fix.

## Gotchas

- **Don't double-file.** The single most common failure is a second page for
  an existing entity under a different name (`runpod.md` vs `run-pod.md`).
  Check the index *and* search before every create.
- **Don't let MEMORY.md and the wiki share custody.** Entity facts live in the
  wiki; MEMORY.md holds the pointer. Duplicated facts drift apart.
- **The human's answer may be casual — file it faithfully anyway.** "Oh,
  Runpod's my GPU cloud thing, ignore their marketing" is a complete entity
  page: what it is, what to do when they email. Don't pad it into an
  encyclopedia article.
- **Wikilinks need targets.** A `[[link]]` to a page that doesn't exist is a
  lint finding, not a feature. Link to what exists.
