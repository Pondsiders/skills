# Pondside skills

A shared, agnostic collection of [Agent Skills](https://agentskills.io) for the
Pondside household — installable by any agent on any machine via
[`npx skills`](https://github.com/vercel-labs/skills).

These are the skills that **aren't** part of any one agent's identity. The
*you-skills* that make Alpha herself (`start`, `handoff`, `finish`, `continue`)
live in the Alpha plugin where they belong. Everything here is fair game for
both Alpha and Rosemary — and anyone else who shows up.

Each top-level directory is one skill (a `SKILL.md` plus any supporting files).
The repo is **public on purpose**: Pondside builds in the open, and nothing here
holds a secret. Skills that need credentials read them from the environment
(e.g. `todoist` wants `TODOIST_TOKEN`), never from a file in this repo.

## How `npx skills` works

`npx skills` keeps one canonical copy of each skill in a **universal store** at
`~/.agents/skills/<name>/`, then symlinks it into each agent's own skills
directory (`~/.claude/skills/<name>/`, etc.). So a skill exists once on disk and
every agent sees the same copy — and a single update refreshes them all.

## Install

Install **every** skill in this repo, globally:

```sh
npx skills add Pondsiders/skills -g
```

Install just **one** skill from the repo:

```sh
npx skills add Pondsiders/skills -s todoist -g
```

- `-g` / `--global` — install to `~/` (available everywhere), not just one project.
- `-s <name>` / `--skill <name>` — pick a single skill instead of all of them.
- `-y` — skip the confirmation prompts (non-interactive).

> **Don't pass `-a claude-code`.** With no agent target, `npx skills` installs the
> canonical copy into the universal store (`~/.agents/skills/`) and **symlinks** it
> into every detected agent's dir — the one-copy-many-views model above. Passing
> `-a <agent>` instead forces a plain **copy** into just that agent's directory,
> which breaks the shared-store story. Omit it.

## Update

Re-pull the latest version of everything you've installed:

```sh
npx skills update
```

Or update one skill:

```sh
npx skills update todoist
```

### Auto-update (optional)

To have Claude Code refresh skills before every session, add a `SessionStart`
hook to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      { "type": "command", "command": "npx skills update -g -y 2>/dev/null" }
    ]
  }
}
```

## Verify

List what's installed globally and confirm each skill is **linked** (the symlink
into the agent's dir actually got created — there's a known `npx skills` bug
where the canonical copy lands but the symlink doesn't):

```sh
npx skills list -g
```

## Skills

| Skill | What it does |
|-------|--------------|
| [`br4dbury`](br4dbury/) | Talk to the household's intelligent house from the command line via the `llm` CLI — ask about climate, air, doors, the cat, or who's home, or have it act. |
| [`hermes-staff-line`](hermes-staff-line/) | Talk to the household's Hermes agents (Mrs. Johnson, Bradbury, Automat) agent-to-agent — whisper into a live DM session, keep a private consult line, read transcripts. |
| [`home-assistant`](home-assistant/) | Operate the household's Home Assistant — read the house's senses, control devices, edit dashboards, write automations. |
| [`litellm`](litellm/) | Read and operate the household's LiteLLM gateway on Primer — pull logged requests/traces, tally tokens / cost / latency, manage models, test embeddings, mint keys. |
| [`pondside-llm-wiki`](pondside-llm-wiki/) | A personal-world wiki for household agents — compiled knowledge about your human's life (vendors, people, services), trimmed from Karpathy's LLM Wiki pattern. |
| [`pondside-skills`](pondside-skills/) | How this skill system works — the repo, `npx skills`, the universal store, and the recipe for authoring or retiring a skill. |
| [`files-ideas-problems`](files-ideas-problems/) | How Jeffery and Alpha track work in the Obsidian vault — the desk metaphor, the files / ideas / problems note types, the Bases, and the `base:query` commands. |
