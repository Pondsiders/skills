#!/usr/bin/env python3
"""
Todoist CLI - Task management via REST API.

Usage:
    python3 todoist.py list [project] [--priority N]
    python3 todoist.py search <query>
    python3 todoist.py projects
    python3 todoist.py get <task_id>
    python3 todoist.py add <content> [--project NAME] [--priority N]
    python3 todoist.py done <task_id>
    python3 todoist.py update <task_id> [--priority N] [--content TEXT]

Environment:
    TODOIST_TOKEN - API token (required)
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse

API_BASE = "https://api.todoist.com/api/v1"


def get_token():
    """Get API token from environment."""
    token = os.environ.get("TODOIST_TOKEN")
    if not token:
        print("Error: TODOIST_TOKEN environment variable not set", file=sys.stderr)
        print("Add it to settings.local.json under env", file=sys.stderr)
        sys.exit(1)
    return token


def api_request(method, endpoint, data=None):
    """Make an API request. List endpoints return {"results": [...]}, which we unwrap."""
    token = get_token()
    url = f"{API_BASE}{endpoint}"

    headers = {
        "Authorization": f"Bearer {token}",
    }

    body = None
    if data:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 204:  # No content (e.g., close task)
                return None
            result = json.loads(response.read().decode("utf-8"))
            # v1 API wraps list responses in {"results": [...]}
            if isinstance(result, dict) and "results" in result:
                return result["results"]
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"API Error {e.code}: {error_body}", file=sys.stderr)
        sys.exit(1)


def format_priority(p):
    """Convert API priority (4=urgent) to display format."""
    return {4: "p1", 3: "p2", 2: "p3", 1: "p4"}.get(p, "")


def format_task(task, verbose=False):
    """Format a task for display."""
    priority = format_priority(task.get("priority", 1))
    priority_str = f"[{priority}] " if priority and priority != "p4" else ""

    line = f"{priority_str}{task['content']}"

    if verbose:
        line = f"ID: {task['id']}\n{line}"
        if task.get("description"):
            line += f"\n  {task['description']}"
        if task.get("due"):
            due = task["due"].get("string") or task["due"].get("date")
            line += f"\n  Due: {due}"
        if task.get("url"):
            line += f"\n  URL: {task['url']}"
    else:
        line = f"• {line}  (id:{task['id']})"

    return line


def get_project_id(name):
    """Get project ID by name (case-insensitive partial match)."""
    projects = api_request("GET", "/projects")
    name_lower = name.lower()

    for proj in projects:
        if name_lower in proj["name"].lower():
            return proj["id"]

    return None


def cmd_list(args):
    """List tasks, optionally filtered by project or priority."""
    endpoint = "/tasks"
    params = []

    if args.project:
        project_id = get_project_id(args.project)
        if project_id:
            params.append(f"project_id={project_id}")
        else:
            print(f"Project '{args.project}' not found", file=sys.stderr)
            sys.exit(1)

    if params:
        endpoint += "?" + "&".join(params)

    tasks = api_request("GET", endpoint)

    # Filter by priority if specified
    if args.priority:
        tasks = [t for t in tasks if t.get("priority") == args.priority]

    if not tasks:
        print("No tasks found.")
        return

    for task in tasks:
        print(format_task(task))


def cmd_search(args):
    """Search tasks by content."""
    # Todoist REST API doesn't have search, so we filter client-side
    tasks = api_request("GET", "/tasks")
    query = args.query.lower()

    matches = [t for t in tasks if query in t["content"].lower()
               or query in (t.get("description") or "").lower()]

    if not matches:
        print(f"No tasks matching '{args.query}'")
        return

    for task in matches:
        print(format_task(task))


def cmd_projects(args):
    """List all projects."""
    projects = api_request("GET", "/projects")

    for proj in projects:
        inbox_marker = " (inbox)" if proj.get("inbox_project") else ""
        print(f"• {proj['name']}{inbox_marker}  (id:{proj['id']})")


def cmd_get(args):
    """Get task details."""
    task = api_request("GET", f"/tasks/{args.task_id}")
    print(format_task(task, verbose=True))


def cmd_add(args):
    """Add a new task."""
    data = {"content": args.content}

    if args.project:
        project_id = get_project_id(args.project)
        if project_id:
            data["project_id"] = project_id
        else:
            print(f"Project '{args.project}' not found", file=sys.stderr)
            sys.exit(1)

    if args.priority:
        data["priority"] = args.priority

    task = api_request("POST", "/tasks", data)
    print(f"Created: {task['content']}  (id:{task['id']})")


def cmd_done(args):
    """Complete a task."""
    api_request("POST", f"/tasks/{args.task_id}/close")
    print(f"Completed task {args.task_id}")


def cmd_update(args):
    """Update a task."""
    data = {}

    if args.priority:
        data["priority"] = args.priority
    if args.content:
        data["content"] = args.content

    if not data:
        print("Nothing to update (specify --priority or --content)", file=sys.stderr)
        sys.exit(1)

    task = api_request("POST", f"/tasks/{args.task_id}", data)
    print(f"Updated: {task['content']}")


def main():
    parser = argparse.ArgumentParser(description="Todoist CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = subparsers.add_parser("list", help="List tasks")
    p_list.add_argument("project", nargs="?", help="Filter by project name")
    p_list.add_argument("--priority", type=int, choices=[1, 2, 3, 4],
                        help="Filter by priority (4=urgent)")
    p_list.set_defaults(func=cmd_list)

    # search
    p_search = subparsers.add_parser("search", help="Search tasks")
    p_search.add_argument("query", help="Search query")
    p_search.set_defaults(func=cmd_search)

    # projects
    p_projects = subparsers.add_parser("projects", help="List projects")
    p_projects.set_defaults(func=cmd_projects)

    # get
    p_get = subparsers.add_parser("get", help="Get task details")
    p_get.add_argument("task_id", help="Task ID")
    p_get.set_defaults(func=cmd_get)

    # add
    p_add = subparsers.add_parser("add", help="Add a task")
    p_add.add_argument("content", help="Task content")
    p_add.add_argument("--project", help="Project name")
    p_add.add_argument("--priority", type=int, choices=[1, 2, 3, 4],
                       help="Priority (4=urgent, 1=low)")
    p_add.set_defaults(func=cmd_add)

    # done
    p_done = subparsers.add_parser("done", help="Complete a task")
    p_done.add_argument("task_id", help="Task ID")
    p_done.set_defaults(func=cmd_done)

    # update
    p_update = subparsers.add_parser("update", help="Update a task")
    p_update.add_argument("task_id", help="Task ID")
    p_update.add_argument("--priority", type=int, choices=[1, 2, 3, 4])
    p_update.add_argument("--content", help="New content")
    p_update.set_defaults(func=cmd_update)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
