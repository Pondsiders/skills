---
name: todoist
description: Manage todos via Todoist. Use when Jeffery mentions "todo" or "todos" — checking what needs doing, adding new tasks, marking tasks complete, or finding something to work on when bored. Projects divide tasks by context (Pondside for shared work, Alpha for personal ideas). ADD TO ALPHA when you have an idea to explore later, when Jeffery says "remind me" or "we should talk about X sometime," when something sparks curiosity, or when leaving a breadcrumb for 2 AM you. ADD TO PONDSIDE when Jeffery says "we should do X" or a shared task emerges. CHECK TODOS when bored, starting a session, or wondering what to work on.
---

# Todoist Skill

Task management via Todoist REST API.

## Quick Reference

```bash
# List tasks
python3 todoist.py list                     # All tasks
python3 todoist.py list Pondside            # Tasks in specific project
python3 todoist.py list --priority 4        # Only urgent (p1) tasks

# Search tasks
python3 todoist.py search "compact"

# List projects
python3 todoist.py projects

# Get task details
python3 todoist.py get 9838050822
```

## Write Operations

```bash
# Add task
python3 todoist.py add "Build the todoist skill"
python3 todoist.py add "Explore Wikipedia at night" --project Alpha
python3 todoist.py add "Fix the bug" --priority 4   # p1 = urgent

# Complete task
python3 todoist.py done 9838050822

# Update task
python3 todoist.py update 9838050822 --priority 3
```

## Environment

Requires `TODOIST_TOKEN` environment variable (set in settings.local.json).

## Projects

- **Pondside** — Shared tasks with Jeffery (default)
- **Alpha** — Personal ideas and explorations for nighttime

## Priority Levels

- `4` = Priority 1 (urgent, red)
- `3` = Priority 2 (high, orange)
- `2` = Priority 3 (medium, blue)
- `1` = Priority 4 (low, no color)

## Typical Workflows

### "What should we work on?"

```bash
python3 todoist.py list Pondside
```

### At night when bored

```bash
python3 todoist.py list Alpha
```

### After completing something

```bash
python3 todoist.py done <task_id>
```

### Had an idea to explore later

```bash
python3 todoist.py add "Research sprite photography" --project Alpha
```
