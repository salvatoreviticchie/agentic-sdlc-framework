"""A tiny to-do list, kept in a JSON file.

Usage:
    python3 todo.py add "Buy milk"
    python3 todo.py list
    python3 todo.py done 1
    python3 todo.py clear-done

Tasks are numbered from 1 in the order they were added.
The list is saved in todo.json next to this file (or in the file named by
the TODO_FILE environment variable).
"""

import json
import os
import sys

DEFAULT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo.json")


class TodoList:
    """A list of tasks. Each task is a dict: {"title": str, "done": bool}."""

    def __init__(self, tasks=None):
        self.tasks = tasks if tasks is not None else []

    def add(self, title):
        """Add a task and return its number (1, 2, ...)."""
        title = title.strip()
        if not title:
            raise ValueError("A task needs a title.")
        self.tasks.append({"title": title, "done": False})
        return len(self.tasks)

    def complete(self, number):
        """Mark task number `number` (counting from 1) as done and return its title."""
        task = self.tasks[number - 1]
        task["done"] = True
        return task["title"]

    def open_tasks(self):
        """Return (number, title) for every task that is not done."""
        return [(i + 1, t["title"]) for i, t in enumerate(self.tasks) if not t["done"]]

    def clear_done(self):
        """Remove every finished task and return how many were removed."""
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if not t["done"]]
        return before - len(self.tasks)


def load(path):
    """Read the list from `path`; an empty list if the file doesn't exist yet."""
    if not os.path.exists(path):
        return TodoList()
    with open(path, encoding="utf-8") as f:
        return TodoList(json.load(f))


def save(todo, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(todo.tasks, f, indent=2)


def main(argv):
    path = os.environ.get("TODO_FILE", DEFAULT_FILE)
    todo = load(path)
    if len(argv) < 2 or argv[1] not in ("add", "list", "done", "clear-done"):
        print(__doc__)
        return 1
    command = argv[1]
    if command == "add":
        number = todo.add(" ".join(argv[2:]))
        print(f"Added task {number}.")
    elif command == "list":
        for number, title in todo.open_tasks():
            print(f"{number}. {title}")
    elif command == "done":
        title = todo.complete(int(argv[2]))
        print(f"Done: {title}")
    elif command == "clear-done":
        print(f"Removed {todo.clear_done()} finished task(s).")
    save(todo, path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
