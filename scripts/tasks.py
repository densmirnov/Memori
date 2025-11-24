#!/usr/bin/env python3
"""Generate a simple markdown board from tasks.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
TASKS_JSON = ROOT / "tasks.json"
BOARD_MD = ROOT / "tasks_board.md"


def format_tags(tags: Iterable[str]) -> str:
    return ", ".join(tags) if tags else "-"


def format_row(task: dict) -> str:
    return "| {id} | {title} | {status} | {owner} | {priority} | {tags} |".format(
        id=task.get("id", "-"),
        title=task.get("title", "-"),
        status=task.get("status", "-"),
        owner=task.get("owner", "-"),
        priority=task.get("priority", "-"),
        tags=format_tags(task.get("tags", [])),
    )


def main() -> None:
    if not TASKS_JSON.exists():
        raise SystemExit(f"{TASKS_JSON} not found")

    data = json.loads(TASKS_JSON.read_text())
    tasks = data.get("tasks", [])

    lines = [
        "# Task Status Board",
        "",
        "| ID | Title | Status | Owner | Priority | Tags |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    lines += [format_row(task) for task in tasks]
    lines.append("")

    BOARD_MD.write_text("\n".join(lines))
    print(f"Rewrote {BOARD_MD.relative_to(ROOT)} with {len(tasks)} tasks.")


if __name__ == "__main__":
    main()
