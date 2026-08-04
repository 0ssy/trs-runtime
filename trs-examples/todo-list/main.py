from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import client, commitment, intention, observation


def main() -> None:
    c = client()
    subject = "todo-board:alpha"
    board = observation(author="example-todo", subject=subject, value={"title": "Alpha Board"})
    c.submit(board)

    task_a = intention(
        author="alice",
        subject=subject,
        goal="write docs",
        horizon="this-week",
        causes=[board["id"]],
    )
    task_b = intention(
        author="bob",
        subject=subject,
        goal="add tests",
        horizon="this-week",
        causes=[board["id"]],
    )
    c.submit(task_a)
    c.submit(task_b)

    done_a = commitment(
        author="alice",
        subject=subject,
        action="complete-task",
        due_by="2027-01-01",
        causes=[board["id"], task_a["id"]],
        extra={"task": task_a["id"], "status": "done"},
    )
    c.submit(done_a)

    intentions = c.query({"type": "Intention"})
    board_intentions = [item["id"] for item in intentions if item.get("subject") == subject]
    print({"board": subject, "tasks": len(board_intentions), "completed": done_a["id"]})


if __name__ == "__main__":
    main()
