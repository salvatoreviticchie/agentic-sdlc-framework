#!/usr/bin/env python3
"""
init_project.py - the exact parts of /sdlc:init: set up a project for the sdlc plugin.

Subcommands:
  check
      Prints JSON: what is already set up and what is missing, plus suggestions
      for the app folder, the stack and the test command. Changes nothing.
  apply --app FOLDER --stack generic|salesforce|java|node|dotnet|python --test-command TEXT
        [--claude-md create|append|skip] [--git-init]
      Creates only what is missing and prints JSON with the files it created or
      changed. Running it again changes nothing.

What a set-up project has:
  specs/, specs/change-requests/, specs/features/, docs/, docs/design/,
  docs/build/, runs/          (each with a .gitkeep, so git keeps the folder)
  the app folder               (an empty one gets a .gitkeep: a new project)
  docs/gates.md                (copied from the plugin; never overwritten)
  CLAUDE.md "## Project settings" (from the plugin's templates/CLAUDE.md)
  .gitignore lines             (full agent run logs stay out of git)
  .claude/settings.json        (agents may write specs/ and docs/ without asking)

Run it from inside the project. Standard library only.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = PLUGIN_ROOT / "templates"

FOLDERS = ["specs", "specs/change-requests", "specs/features",
           "docs", "docs/design", "docs/build", "runs"]
GITIGNORE_LINES = ["runs/*.json", "runs/*.txt", "__pycache__/"]
GITIGNORE_BLOCK_HEADER = "# sdlc plugin: full agent run logs can contain file contents; only runs/costs.csv is kept"
ALLOW_RULES = ["Edit(specs/**)", "Edit(docs/**)", "Write(specs/**)", "Write(docs/**)"]
SETTING_KEYS = ["App folder", "Stack", "Test command"]


def git(*args, cwd):
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip()


def project_root():
    """The git repository's top folder, or the current folder if it isn't one yet."""
    code, out = git("rev-parse", "--show-toplevel", cwd=None)
    return Path(out) if code == 0 else Path.cwd()


def settings_in(text):
    """The Project settings values found in CLAUDE.md text."""
    found = {}
    for key in SETTING_KEYS:
        match = re.search(rf"^- {key}:\s*(.+)$", text, re.MULTILINE)
        if match:
            found[key] = match.group(1).strip()
    return found


def real_files(folder):
    """Files under folder, ignoring .gitkeep, .git and caches."""
    if not folder.is_dir():
        return []
    skip = {".git", "__pycache__", "node_modules", ".sfdx", ".sf"}
    return [p for p in folder.rglob("*")
            if p.is_file() and p.name != ".gitkeep" and not (skip & set(p.relative_to(folder).parts))]


STACKS = ["generic", "salesforce", "java", "node", "dotnet", "python"]

# Build files, first match wins (same order as /sdlc:decide step 1). A Salesforce
# project often has a package.json for its linters, so sfdx-project.json comes first.
BUILD_FILES = [("salesforce", ["sfdx-project.json"]),
               ("java", ["pom.xml", "build.gradle", "build.gradle.kts"]),
               ("dotnet", ["*.sln", "*.csproj", "*.fsproj"]),
               ("python", ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"]),
               ("node", ["package.json"])]
SOURCE_SUFFIXES = {".py": "python", ".ts": "node", ".tsx": "node", ".js": "node",
                   ".java": "java", ".kt": "java", ".cs": "dotnet", ".fs": "dotnet",
                   ".cls": "salesforce", ".trigger": "salesforce"}


def suggest_stack(root, app):
    """The stack profile that fits: a build file in the app folder or the root, else the most
    common source file type in the app folder, else generic."""
    for stack, patterns in BUILD_FILES:
        for place in (root / app, root):
            for pattern in patterns:
                found = sorted(place.glob(pattern)) if place.is_dir() else []
                if found:
                    return stack, f"{found[0].relative_to(root)} exists"
    counts = {}
    for f in real_files(root / app):
        stack = SOURCE_SUFFIXES.get(f.suffix)
        if stack:
            counts[stack] = counts.get(stack, 0) + 1
    if counts:
        stack = max(counts, key=counts.get)
        return stack, f"most source files in {app}/ are {stack} ({counts[stack]} files)"
    return "generic", "no build file or known source files found"


def suggest_test_command(root, app, stack):
    """A test command that fits what is in the app folder (a guess for the user to confirm)."""
    folder = root / app
    if stack == "salesforce":
        return f"cd {app} && sf apex run test --test-level RunLocalTests --wait 30 --result-format human"
    if (folder / "package.json").exists():
        return f"npm --prefix {app} test"
    if (folder / "pom.xml").exists():
        return f"mvn -f {app}/pom.xml test"
    if (folder / "gradlew").exists():
        return f"cd {app} && ./gradlew test"
    if (folder / "build.gradle").exists() or (folder / "build.gradle.kts").exists():
        return f"cd {app} && gradle test"
    if any(folder.glob("*.sln")) or any(folder.glob("*.csproj")) or any(folder.glob("*.fsproj")):
        return f"dotnet test {app}"
    if (folder / "go.mod").exists():
        return f"cd {app} && go test ./..."
    if (folder / "Cargo.toml").exists():
        return f"cargo test --manifest-path {app}/Cargo.toml"
    if any(p.suffix == ".py" for p in real_files(folder)):
        if (folder / "pytest.ini").exists() or (folder / "conftest.py").exists():
            return f"python3 -m pytest {app}"
        return f"python3 -m unittest discover -s {app} -v"
    return ""


def suggest_app(root):
    """app/ if it exists, else the one top-level folder with code, else app."""
    if (root / "app").is_dir():
        return "app"
    ignore = {"specs", "docs", "runs", ".git", ".claude", ".claude-plugin", "node_modules"}
    candidates = [p.name for p in root.iterdir()
                  if p.is_dir() and not p.name.startswith(".") and p.name not in ignore and real_files(p)]
    return candidates[0] if len(candidates) == 1 else "app"


def check(root):
    is_repo = git("rev-parse", "--is-inside-work-tree", cwd=root)[0] == 0
    has_commit = is_repo and git("rev-parse", "--verify", "--quiet", "HEAD", cwd=root)[0] == 0
    branch = git("branch", "--show-current", cwd=root)[1] if is_repo else ""
    has_main = is_repo and git("rev-parse", "--verify", "--quiet", "refs/heads/main", cwd=root)[0] == 0

    claude_md = root / "CLAUDE.md"
    claude_text = claude_md.read_text(encoding="utf-8") if claude_md.exists() else ""
    settings = settings_in(claude_text)
    has_section = bool(re.search(r"^## Project settings\s*$", claude_text, re.MULTILINE))
    if not claude_md.exists():
        claude_state = "missing"
    elif has_section and all(k in settings for k in SETTING_KEYS):
        claude_state = "has project settings"
    else:
        claude_state = "exists without project settings"

    app = settings.get("App folder") or suggest_app(root)
    stack, stack_reason = suggest_stack(root, app)
    if settings.get("Stack"):
        stack, stack_reason = settings["Stack"], "from CLAUDE.md"

    gates = root / "docs" / "gates.md"
    plugin_gates = (TEMPLATES / "gates.md").read_text(encoding="utf-8")
    if not gates.exists():
        gates_state = "missing"
    elif gates.read_text(encoding="utf-8") == plugin_gates:
        gates_state = "same as the plugin"
    else:
        gates_state = "differs from the plugin (left as it is)"

    gitignore = root / ".gitignore"
    ignore_lines = gitignore.read_text(encoding="utf-8").splitlines() if gitignore.exists() else []
    settings_json = root / ".claude" / "settings.json"
    allow = []
    settings_json_error = None
    if settings_json.exists():
        try:
            allow = json.loads(settings_json.read_text(encoding="utf-8")).get("permissions", {}).get("allow", [])
        except json.JSONDecodeError as error:
            settings_json_error = f"not valid JSON ({error}); left as it is"

    app_path = root / app
    app_files = real_files(app_path)
    uncommitted_app = []
    if is_repo and app_path.is_dir():
        code, out = git("status", "--porcelain", "--untracked-files=all", "--", app, cwd=root)
        uncommitted_app = [line[3:] for line in out.splitlines() if line.strip()]

    todo = {
        "git_init": not is_repo,
        "folders": [f for f in FOLDERS if not (root / f).is_dir()],
        "app_folder": not app_path.is_dir(),
        "gates_md": gates_state == "missing",
        "claude_md": claude_state != "has project settings",
        "gitignore_lines": [line for line in GITIGNORE_LINES if line not in ignore_lines],
        "allow_rules": [] if settings_json_error else [r for r in ALLOW_RULES if r not in allow],
    }
    nothing_to_do = not any(todo.values())
    return {
        "root": str(root),
        "nothing_to_do": nothing_to_do,
        "git": {"is_repo": is_repo, "has_commit": has_commit, "branch": branch, "has_main_branch": has_main},
        "claude_md": claude_state,
        "settings": settings,
        "suggested": {"app_folder": app, "stack": stack, "stack_reason": stack_reason,
                      "test_command": settings.get("Test command") or suggest_test_command(root, app, stack)},
        "app_folder": {"name": app, "exists": app_path.is_dir(), "files": len(app_files),
                       "uncommitted": uncommitted_app[:20], "uncommitted_count": len(uncommitted_app)},
        "gates_md": gates_state,
        "settings_json": settings_json_error or ("exists" if settings_json.exists() else "missing"),
        "todo": todo,
    }


def apply(root, args):
    state = check(root)
    changed = []

    def note(path):
        changed.append(str(Path(path).relative_to(root)))

    if state["todo"]["git_init"]:
        if not args.git_init:
            sys.exit("Error: this folder is not a git repository. Pass --git-init to create one.")
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)

    for folder in FOLDERS:
        path = root / folder
        if not path.is_dir():
            path.mkdir(parents=True)
            (path / ".gitkeep").touch()
            note(path / ".gitkeep")

    app = root / args.app
    if not app.is_dir():
        app.mkdir(parents=True)
        (app / ".gitkeep").touch()
        note(app / ".gitkeep")

    gates = root / "docs" / "gates.md"
    if not gates.exists():
        gates.write_text((TEMPLATES / "gates.md").read_text(encoding="utf-8"), encoding="utf-8")
        note(gates)

    section = (TEMPLATES / "CLAUDE.md").read_text(encoding="utf-8").format(
        app=args.app, stack=args.stack, test_command=args.test_command)
    claude_md = root / "CLAUDE.md"
    if state["claude_md"] == "missing" and args.claude_md in ("create", "append"):
        claude_md.write_text("# Project notes for Claude\n\n" + section, encoding="utf-8")
        note(claude_md)
    elif state["claude_md"] == "exists without project settings" and args.claude_md == "append":
        text = claude_md.read_text(encoding="utf-8")
        claude_md.write_text(text.rstrip("\n") + "\n\n" + section, encoding="utf-8")
        note(claude_md)

    missing = state["todo"]["gitignore_lines"]
    if missing:
        gitignore = root / ".gitignore"
        text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
        block = ("\n" if text and not text.endswith("\n") else "") + ("\n" if text else "")
        block += GITIGNORE_BLOCK_HEADER + "\n" + "\n".join(missing) + "\n"
        gitignore.write_text(text + block, encoding="utf-8")
        note(gitignore)

    rules = state["todo"]["allow_rules"]
    if rules:
        settings_json = root / ".claude" / "settings.json"
        data = json.loads(settings_json.read_text(encoding="utf-8")) if settings_json.exists() else {}
        data.setdefault("permissions", {}).setdefault("allow", []).extend(rules)
        settings_json.parent.mkdir(exist_ok=True)
        settings_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        note(settings_json)

    print(json.dumps({"changed": changed, "nothing_changed": not changed}, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Set up a project for the sdlc plugin.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    p_apply = sub.add_parser("apply")
    p_apply.add_argument("--app", required=True)
    p_apply.add_argument("--stack", required=True, choices=STACKS)
    p_apply.add_argument("--test-command", required=True)
    p_apply.add_argument("--claude-md", default="create", choices=["create", "append", "skip"])
    p_apply.add_argument("--git-init", action="store_true")
    args = parser.parse_args()

    root = project_root()
    if (root / ".claude-plugin" / "marketplace.json").exists() and (root / "plugins" / "sdlc").is_dir():
        sys.exit("Error: this is the agentic-sdlc framework repository itself. Run /sdlc:init in your own project.")
    if args.command == "check":
        print(json.dumps(check(root), indent=2))
    else:
        if Path(args.app).is_absolute() or ".." in Path(args.app).parts:
            sys.exit("Error: the app folder must be a folder inside the project, e.g. app or src.")
        apply(root, args)


if __name__ == "__main__":
    main()
