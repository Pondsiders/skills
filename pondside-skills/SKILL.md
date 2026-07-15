---
name: pondside-skills
description: >
  Use whenever you need to understand or change how the household's agent skills are
  set up — authoring a new skill, retiring one, updating, or troubleshooting why a
  skill isn't triggering or didn't install. Covers the Pondside shared skills repo
  (github.com/Pondsiders/skills), the `npx skills` CLI, the universal-store + symlink
  model, and how to write a good skill. Reach for this even when "skill" isn't named
  directly: "why isn't this triggering," "let's make a skill for X," "where do my
  skills live," "how do I share this with Rosemary," "add or remove a capability."
---

# Pondside skills — how the skill system works

The household's *shared* skills — the ones that aren't welded into one agent's
identity — live in one public repo and install on each machine via `npx skills`.
The *you-skills* that make Alpha herself (`start`, `handoff`, `finish`, `continue`)
are NOT here; they live in the Alpha plugin. Everything here is fair game for both
Alpha and Rosemary.

## Where everything lives

- **Source of truth:** `github.com/Pondsiders/skills` — public on purpose (no
  secrets; credentials come from the environment, never from a file in the repo).
- **Local checkout:** `~/Pondside/Workshop/Projects/skills` — edit here.
- **Universal store:** `~/.agents/skills/<name>/` — one canonical copy per skill,
  symlinked into each agent's dir (`~/.claude/skills/<name>/`). One copy on disk,
  every agent sees it, one update refreshes all.
- **Lockfile:** `~/.agents/.skill-lock.json` — tracks what's installed, its source,
  and a content hash. `npx skills` maintains it; don't hand-edit it.

Each top-level directory in the repo is one skill: a `SKILL.md` plus any supporting
files (`scripts/`, `references/`, `assets/`).

## The `npx skills` CLI

```sh
npx skills add Pondsiders/skills -g             # install ALL skills, globally
npx skills add Pondsiders/skills -s NAME -g -y  # install one skill, no prompts
npx skills remove NAME                          # retire an installed skill
npx skills update [NAME]                        # re-pull latest (installed only)
npx skills list -g                              # what's installed + did it link
```

`-g`/`--global` installs to `~/` (everywhere), not one project; `-y` skips prompts.

## Authoring or retiring a skill (the recipe)

**New skill:**
1. In the checkout, make `NAME/SKILL.md` (one dir per skill). Write it per the
   best-practices below.
2. Add NAME to the README skills table.
3. Commit + push to `Pondsiders/skills`.
4. Install it: `npx skills add Pondsiders/skills -s NAME -g -y`.
5. Verify it linked: `npx skills list -g` (see the symlink gotcha).

**Retire a skill:**
1. `npx skills remove NAME` (uninstalls + unlinks locally).
2. Delete `NAME/` from the repo and drop it from the README. Commit + push.

A skill appears in / disappears from the Claude Code menu the *next turn* after
install/remove — no restart needed (the harness re-scans).

## Gotchas

- **Never pass `-a claude-code` (or any `-a <agent>`) on `add`.** With no agent
  target, `npx skills` installs the canonical copy into the universal store and
  *symlinks* it into every agent's dir — the shared-store model. `-a` forces a plain
  *copy* into just that one agent's dir, breaking the one-copy-many-views story.
- **The symlink bug.** A known `npx skills` bug: the canonical copy lands in the
  store but the symlink into the agent dir sometimes doesn't get created. After any
  `add`, run `npx skills list -g` and confirm the skill shows as linked.
- **`update` only refreshes already-installed skills.** A brand-new skill in the
  repo needs `add`, not `update`.
- **Public repo.** Nothing here holds a secret. Skills that need credentials read
  them from env vars (e.g. `TODOIST_TOKEN`), never from a file in the repo.

## Writing a good skill (from agentskills.io best-practices)

- **Start from real expertise.** Extract a skill from a real hands-on task plus the
  corrections and gotchas it surfaced — don't hallucinate one from general knowledge.
- **Add what the agent lacks, omit what it knows.** Carry *our* specifics (paths,
  conventions, gotchas), not "what is a PDF." Every token competes for attention.
- **Gotchas are the highest-value content** — concrete corrections to mistakes you'd
  make without being told. When you correct a real mistake, add it to the gotchas.
- **Descriptions are load-bearing for AUTO-triggered skills.** Imperative
  ("Use when…"), intent-focused, *pushy* (list contexts including when the domain
  isn't named), under **1024 chars**. Slash-invoked skills (`/start`, `/finish`)
  don't auto-trigger — their description is decorative, so don't waste effort tuning
  it.
- **Keep `SKILL.md` under ~500 lines / 5,000 tokens.** Push overflow to `references/`
  with an explicit "read X when Y" so it loads on demand (progressive disclosure).
- **Defaults, not menus.** Pick a default tool/approach and mention alternatives
  briefly. Full docs index: https://agentskills.io/llms.txt
- **A frontmatter YAML error makes a skill silently invisible.** An unquoted
  `description:` containing a colon-space (e.g. `...LLM Wiki: entities...`) is
  illegal YAML; the CLI's discovery skips the skill without any error and
  reports N-1 skills "found" — which presents exactly like a stale cache.
  Before pushing, validate: `uv run --with pyyaml python3 -c "import yaml; yaml.safe_load(open('NAME/SKILL.md').read().split('---')[1])"`
