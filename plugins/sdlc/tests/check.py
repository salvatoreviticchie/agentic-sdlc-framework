#!/usr/bin/env python3
"""
check.py - the sdlc plugin's free self-test: no AI, no network, a few seconds.

Run it from anywhere:
    python3 plugins/sdlc/tests/check.py

It checks:
  1. `claude plugin validate` passes on the plugin and on the marketplace.
  2. Every skill has frontmatter with a description, is user-invoked only
     (disable-model-invocation: true), and its last line is a "Next:" line.
  3. Every /sdlc:<name> mentioned in the skills, agents, templates, README.md
     and docs/how-to.md is a skill that exists.
  4. Every plugin script, template and stack profile that is referenced exists,
     and every stack /sdlc:init accepts has a profile.
  5. Every agent has a "Prompt version:" line, and plugin.json has a version.
  6. The published files have no private-repo links, no email addresses and no
     names from the private pilot.

It prints PASS or FAIL per check (with the reasons) and exits with 1 if any
check fails. Standard library only.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent          # plugins/sdlc
REPO = PLUGIN.parent.parent                                # the marketplace repo
SKILLS = PLUGIN / "skills"
AGENTS = PLUGIN / "agents"
TEMPLATES = PLUGIN / "templates"

# What a release publishes (docs/releasing.md). Pilot records elsewhere in docs/
# are private and never published, so they are not scanned.
PUBLISHED_DOCS = ["docs/how-to.md", "docs/lessons.md", "docs/cost-and-context.md", "docs/releasing.md"]

PRIVATE_WORDS = ["bike-shop", "Northgrade", "Breitling"]
PRIVATE_REPO = re.compile(r"salvatoreviticchie/agentic-sdlc(?!-framework)")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
ALLOWED_EMAIL = re.compile(r"(noreply@anthropic\.com|@users\.noreply\.github\.com|@example\.(com|org)$)")
TEXT_SUFFIXES = {".md", ".py", ".json", ".txt", ".toml", ".cfg", ".yml", ".yaml", ".sh", ""}

results = []


def report(name, problems):
    results.append((name, problems))
    print(f"{'PASS' if not problems else 'FAIL'}  {name}")
    for problem in problems[:25]:
        print(f"      - {problem}")
    if len(problems) > 25:
        print(f"      ... and {len(problems) - 25} more")


def rel(path):
    return str(path.relative_to(REPO))


def skill_files():
    return sorted(SKILLS.glob("*/SKILL.md"))


def frontmatter(text):
    """The frontmatter lines as a dict, or None if the file doesn't start with one."""
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return None
    fields = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return fields


def check_validate():
    problems = []
    claude = shutil.which("claude")
    if not claude:
        print("SKIP  claude plugin validate (the claude command is not on PATH)")
        return
    targets = [PLUGIN]
    if (REPO / ".claude-plugin" / "marketplace.json").exists():
        targets.append(REPO)
    else:
        problems.append(f"no marketplace manifest at {REPO / '.claude-plugin' / 'marketplace.json'}")
    for target in targets:
        run = subprocess.run([claude, "plugin", "validate", str(target)], capture_output=True, text=True)
        output = (run.stdout + run.stderr).strip()
        if run.returncode != 0 or "Validation passed" not in output:
            problems.append(f"{target}: " + " | ".join(output.splitlines()[-5:]))
    report("claude plugin validate (plugin and marketplace)", problems)


def check_skills():
    problems = []
    for path in skill_files():
        text = path.read_text(encoding="utf-8")
        fields = frontmatter(text)
        if fields is None:
            problems.append(f"{rel(path)}: no frontmatter")
            continue
        if not fields.get("description"):
            problems.append(f"{rel(path)}: no description in the frontmatter")
        if fields.get("disable-model-invocation") != "true":
            problems.append(f"{rel(path)}: not user-invoked only (needs disable-model-invocation: true)")
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines or "Next:" not in lines[-1]:
            problems.append(f"{rel(path)}: the last line is not a \"Next:\" line")
    if not skill_files():
        problems.append(f"no skills in {SKILLS}")
    report(f"skills: frontmatter, user-invoked only, end with Next: ({len(skill_files())} skills)", problems)


def mention_sources():
    files = skill_files() + sorted(AGENTS.glob("*.md")) + sorted(TEMPLATES.rglob("*.md"))
    files += [p for p in (REPO / "README.md", REPO / "docs" / "how-to.md") if p.exists()]
    return files


def check_commands():
    names = {p.parent.name for p in skill_files()}
    problems = []
    for path in mention_sources():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for name in re.findall(r"/sdlc:([a-z][a-z0-9-]*)", line):
                if name not in names:
                    problems.append(f"{rel(path)}:{number}: /sdlc:{name} is not a skill")
    report("every /sdlc:<name> mentioned is a skill", problems)


def check_references():
    problems = []
    pattern = re.compile(r"(?:\$\{CLAUDE_PLUGIN_ROOT\}/|plugins/sdlc/)?\b((?:scripts|templates|tests)/[A-Za-z0-9_./-]*[A-Za-z0-9_-]\.(?:py|md|json))")
    for path in mention_sources() + sorted(PLUGIN.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), 1):
            for match in pattern.finditer(line):
                target = match.group(1)
                # In a project, docs/... and scripts/ of the user's own app are not plugin files:
                # only check references that point into the plugin.
                plugin_ref = match.group(0) != target or target.startswith(("templates/", "tests/")) \
                    or target in {"scripts/" + p.name for p in (PLUGIN / "scripts").glob("*.py")} \
                    or path.is_relative_to(PLUGIN)
                if plugin_ref and not (PLUGIN / target).exists():
                    problems.append(f"{rel(path)}:{number}: {target} does not exist in the plugin")
    # Stacks: every stack /sdlc:init accepts has a profile.
    init = (PLUGIN / "scripts" / "init_project.py").read_text(encoding="utf-8")
    match = re.search(r"^STACKS = \[(.*?)\]", init, re.MULTILINE)
    stacks = re.findall(r'"([a-z]+)"', match.group(1)) if match else []
    if not stacks:
        problems.append("scripts/init_project.py: no STACKS list found")
    for stack in stacks:
        if not (TEMPLATES / "stacks" / f"{stack}.md").exists():
            problems.append(f"stack {stack!r} (init_project.py STACKS) has no templates/stacks/{stack}.md")
    for profile in sorted((TEMPLATES / "stacks").glob("*.md")):
        if profile.stem not in stacks:
            problems.append(f"templates/stacks/{profile.name} is not offered by /sdlc:init (init_project.py STACKS)")
    report("referenced scripts, templates and stack profiles exist", problems)


def check_versions():
    problems = []
    for path in sorted(AGENTS.glob("*.md")):
        if not re.search(r"^Prompt version: \S+", path.read_text(encoding="utf-8"), re.MULTILINE):
            problems.append(f"{rel(path)}: no \"Prompt version:\" line")
    manifest = PLUGIN / ".claude-plugin" / "plugin.json"
    try:
        version = json.loads(manifest.read_text(encoding="utf-8")).get("version", "")
        if not re.fullmatch(r"\d+\.\d+\.\d+", version):
            problems.append(f"{rel(manifest)}: version {version!r} is not like 1.2.0")
    except (OSError, ValueError) as error:
        problems.append(f"{rel(manifest)}: {error}")
    report("agents have a Prompt version, plugin.json has a version", problems)


def published_files():
    files = []
    for folder in ("plugins", "examples"):
        files += [p for p in (REPO / folder).rglob("*") if p.is_file()
                  and "__pycache__" not in p.parts and p.suffix in TEXT_SUFFIXES]
    files += [REPO / name for name in ["README.md", *PUBLISHED_DOCS] if (REPO / name).exists()]
    return sorted(files)


def check_private():
    problems = []
    me = Path(__file__).resolve()
    for path in published_files():
        if path.resolve() == me:
            continue          # this file names the words it looks for
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if PRIVATE_REPO.search(line):
                problems.append(f"{rel(path)}:{number}: private-repo link ({PRIVATE_REPO.search(line).group(0)})")
            for email in EMAIL.findall(line):
                if not ALLOWED_EMAIL.search(email) and not email.startswith(("anthropic-ai/", "types/")):
                    problems.append(f"{rel(path)}:{number}: email address {email}")
            for word in PRIVATE_WORDS:
                if word.lower() in line.lower():
                    problems.append(f"{rel(path)}:{number}: private name {word!r}")
    report(f"no private links, emails or pilot names in published files ({len(published_files())} files)", problems)


def main():
    print(f"sdlc plugin self-check: {PLUGIN}\n")
    check_validate()
    check_skills()
    check_commands()
    check_references()
    check_versions()
    check_private()
    failed = [name for name, problems in results if problems]
    print(f"\n{len(results) - len(failed)} of {len(results)} checks passed.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
