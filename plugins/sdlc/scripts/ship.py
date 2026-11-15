#!/usr/bin/env python3
"""
ship.py - the bookkeeping behind the /sdlc:ship command.

/sdlc:ship runs the pipeline stages one after another and stops at each gate.
The parts that must be exact (which stage is next, the timeline file, the
budgets, the tests) are here, so they are the same on every run. The /sdlc:ship
skill (skills/ship/SKILL.md in the sdlc plugin) does the parts that need judgment.

Subcommands:
  state CR-NNN | FEAT-NNN
      For a feature: picks its next CR (table order, dependencies merged) and adds
      the feature's progress, then the CR's state as below.
      Prints JSON: the CR's risk tier, the next action ("run", "stop",
      "refuse" or "done"), and for "run" the exact run_agent.py command.
  log CR-NNN <stage> <event> [--agent A] [--slice N] [--outcome TEXT] [--note TEXT]
      Appends one line to docs/build/CR-NNN-timeline.md (creates it if needed).
      stage: specify, design, build, review, gate2, gate3, gate23 (low risk), gate4
      event: start, end, failed, due, approved, rejected, stopped
  test
      Runs the "Test command:" from CLAUDE.md and exits with its exit code.
  agent NAME
      Prints JSON about the agent's definition: prompt version, the definition
      (commit hash, or plugin@version when installed) and an error if it must not run.
  cochange [--commits N]
      Prints JSON: the pairs of files in the app folder that most often change in
      the same commit (last N commits, default 300; commits touching more than 30
      files are skipped as bulk changes). The explorer's "Structure" section uses it.

Run it from inside your project (any folder of its git repository). The plugin
is the folder above this script, so the skills call it as
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" state CR-005

Examples:
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" state CR-005
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" log CR-005 specify start --agent spec-writer
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" log CR-005 gate23 approved --note "defaults accepted"
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" agent explorer

Standard library only.
"""

import argparse
import csv
import json
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# run_agent.py sits next to this file; it knows where the plugin's agents are.
from run_agent import PLUGIN_ROOT, definition_info

# Stage -> the agent that runs it. Build depends on the Stack (see agent_for).
AGENTS = {"specify": "spec-writer", "design": "architect", "review": "reviewer"}
# Default budgets in USD per stage, used when CLAUDE.md has no "Budgets:" line.
DEFAULT_BUDGETS = {"specify": 1.0, "design": 1.0, "build": 5.0, "review": 1.0}
TIMELINE_HEADER = ("# {cr} timeline\n\n"
                   "One line per stage start, stage end and gate, appended by /sdlc:ship and /sdlc:gate.\n"
                   "Times are UTC. \"took\" is the stage's run time; \"waited\" is how long the gate waited for the PO.\n\n"
                   "| Time (UTC) | Stage | Event | Agent | Prompt version | Outcome |\n"
                   "|---|---|---|---|---|---|\n")


# ---------------------------------------------------------------- helpers

def git(*args, root):
    """Run git and return (exit code, output)."""
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    return result.returncode, result.stdout.strip()


def repo_root():
    code, out = git("rev-parse", "--show-toplevel", root=None)
    if code != 0:
        sys.exit("Error: run this inside the git repository.")
    return Path(out)


def now():
    return datetime.now(timezone.utc)


def parse_time(text):
    """Read '2026-11-13T17:52:03Z' or '...+00:00' as a UTC datetime (None if unreadable)."""
    try:
        return datetime.fromisoformat(text.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def human(seconds):
    """3725 -> '1h02m', 75 -> '1m15s'."""
    seconds = int(seconds)
    if seconds >= 3600:
        return f"{seconds // 3600}h{(seconds % 3600) // 60:02d}m"
    return f"{seconds // 60}m{seconds % 60:02d}s"


class Project:
    """Reads the project's files: the working tree, or branch cr-nnn when the file is only there."""

    def __init__(self, root, cr):
        self.root = root
        self.cr = cr
        self.branch = cr.lower()
        self.current = git("branch", "--show-current", root=root)[1]
        self.branch_exists = git("rev-parse", "--verify", "--quiet", self.branch, root=root)[0] == 0

    def read(self, relative):
        """The file's text, or None if it doesn't exist here or on branch cr-nnn."""
        path = self.root / relative
        if path.exists():
            return path.read_text(encoding="utf-8")
        if self.branch_exists and self.current != self.branch:
            code, out = git("show", f"{self.branch}:{relative}", root=self.root)
            if code == 0:
                return out
        return None

    def settings(self):
        """The 'Project settings' lines of CLAUDE.md as a dict, e.g. {'Test command': '...'}."""
        text = self.read("CLAUDE.md") or ""
        found = {}
        for match in re.finditer(r"^- ([A-Za-z ()]+?):\s*(.+)$", text, re.MULTILINE):
            found.setdefault(match.group(1).strip(), match.group(2).strip())
        return found

    def budgets(self):
        """Budgets from 'Budgets (USD per stage): specify 1, design 1, build 5, review 1'."""
        budgets = dict(DEFAULT_BUDGETS)
        for key, value in self.settings().items():
            if key.lower().startswith("budgets"):
                for stage, amount in re.findall(r"(specify|design|build|review)\s*:?\s*\$?([\d.]+)", value):
                    budgets[stage] = float(amount)
        return budgets

    def spent(self, stage):
        """USD spent so far on this CR and stage, from runs/costs.csv."""
        path = self.root / "runs" / "costs.csv"
        if not path.exists():
            return 0.0
        with open(path, newline="", encoding="utf-8") as f:
            return sum(float(row.get("total_cost_usd") or 0) for row in csv.DictReader(f)
                       if row.get("cr") == self.cr and row.get("stage") == stage)

    def last_cost_row(self, stage):
        path = self.root / "runs" / "costs.csv"
        if not path.exists():
            return None
        with open(path, newline="", encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if r.get("cr") == self.cr and r.get("stage") == stage]
        return rows[-1] if rows else None

    # ---- timeline

    def timeline_path(self):
        return self.root / "docs" / "build" / f"{self.cr}-timeline.md"

    def timeline(self):
        """Timeline rows as dicts: time, stage, event, agent, version, outcome (oldest first)."""
        text = self.read(f"docs/build/{self.cr}-timeline.md") or ""
        rows = []
        for line in text.splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 6 and parse_time(cells[0]):
                rows.append(dict(zip(["time", "stage", "event", "agent", "version", "outcome"], cells)))
        return rows

    def last_index(self, rows, stage=None, event=None, startswith=None):
        """Index of the last row matching stage/event (stage may be a tuple), or -1."""
        for i in range(len(rows) - 1, -1, -1):
            row = rows[i]
            stages = stage if isinstance(stage, tuple) else (stage,)
            if stage and row["stage"].split(" ")[0] not in stages:
                continue
            if event and row["event"] != event:
                continue
            if startswith and not row["stage"].startswith(startswith):
                continue
            return i
        return -1


def agent_for(project, stage):
    if stage == "build":
        return "developer-salesforce" if project.settings().get("Stack", "").lower() == "salesforce" else "developer"
    return AGENTS[stage]


def prompt_version(root, agent):
    """The agent's "Prompt version:" from the plugin's agents/ folder ('' if unknown)."""
    return definition_info(agent)["prompt_version"]


def field(text, name):
    """The value of a 'Name: value' line, or None."""
    match = re.search(rf"^{name}:\s*(.*)$", text or "", re.MULTILINE)
    return match.group(1).strip() if match else None


def last_gate_line(text, gate):
    """'approved', 'rejected' or None: the last 'Gate N approved/rejected' line in text."""
    found = re.findall(rf"^Gate {gate} (approved|rejected)", text or "", re.MULTILINE)
    return found[-1] if found else None


def pr_title(text):
    """The title in double quotes, readable even with an apostrophe (shlex.quote turns ' into '"'"')."""
    for char in '\\"$`':
        text = text.replace(char, "\\" + char)
    return f'"{text}"'


def slices_in_design(design):
    """Slice numbers listed under a 'Slices:' line or heading of the design, e.g. [1, 2]."""
    lines = (design or "").splitlines()
    numbers = []
    inside = False
    for line in lines:
        bare = line.strip().lstrip("#").strip().strip("*").strip()
        if re.match(r"(?i)^slices\b", bare):
            inside = True
            numbers += [int(n) for n in re.findall(r"(?i)\bslice\s+(\d+)", line)]
            continue
        if inside:
            if line.startswith("#") and not re.search(r"(?i)\bslice\s+\d+", line):
                break
            numbers += [int(n) for n in re.findall(r"(?i)\bslice\s+(\d+)", line)]
    return sorted(set(numbers))


# ---------------------------------------------------------------- state

def baseline_approved(root):
    """Gate 1 approved, or a new project's plan approved at Gate 0 (it has no code to explore)."""
    for pattern in ("Gate 1 approved", r"Gate 0 approved (new project)"):
        if git("log", "--all", "--fixed-strings", "--grep", pattern, "--oneline", "-1", root=root)[1]:
            return True
    return False


def feature_rows(text):
    """The CR table of a feature file: dicts with cr, title, risk, depends, mvp, status."""
    rows = []
    for line in (text or "").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 7 and re.fullmatch(r"CR-\d{3}", cells[0]):
            rows.append({"cr": cells[0], "title": cells[1], "risk": cells[3],
                         "depends": re.findall(r"CR-\d{3}", cells[4]),
                         "mvp": cells[5].lower().startswith("y"), "table_status": cells[6]})
    return rows


def feature_state(root, feat):
    """Which CR of the feature to ship next, with the feature's progress."""
    project = Project(root, feat)
    text = project.read(f"specs/features/{feat}.md")
    if text is None:
        return {"feature": feat, "action": "refuse", "reason": f"specs/features/{feat}.md does not exist."}
    rows = feature_rows(text)
    for row in rows:
        cr_text = project.read(f"specs/change-requests/{row['cr']}.md")
        row["status"] = (field(cr_text, "Status") or "missing") if cr_text else "missing"
        row["done"] = row["status"].startswith("Done")
        row["dropped"] = row["status"].startswith("Dropped")
    live = [r for r in rows if not r["dropped"]]
    mvp = [r for r in live if r["mvp"]]
    info = {"feature": feat, "type": field(text, "Type") or "",
            "progress": f"{sum(r['done'] for r in live)} of {len(live)} CRs merged",
            "mvp_progress": f"MVP {sum(r['done'] for r in mvp)} of {len(mvp)}",
            "crs": [{k: r[k] for k in ("cr", "title", "risk", "mvp", "status", "depends")} for r in rows]}
    gate0 = last_gate_line(text, 0)
    if not rows:
        return {**info, "action": "refuse", "reason": "The feature file has no CR table."}
    if gate0 != "approved":
        return {**info, "action": "stop", "stop": "gate0",
                "reason": "Gate 0 is due: approve the plan before any of its CRs start."
                          if gate0 is None else "Gate 0 was rejected: re-plan first.",
                "review": [f"specs/features/{feat}.md"]}
    drafts = [r["cr"] for r in live if r["status"].startswith("Draft")]
    todo = [r for r in live if not r["done"]]
    if not todo:
        return {**info, "action": "done", "reason": "Every CR of the feature is merged."}
    if drafts:
        return {**info, "action": "stop", "stop": "gate0", "drafts": drafts,
                "reason": f"{', '.join(drafts)} changed in a re-plan and {'needs' if len(drafts) == 1 else 'need'} Gate 0 again.",
                "review": [f"specs/features/{feat}.md"] + [f"specs/change-requests/{c}.md" for c in drafts]}
    done = {r["cr"] for r in live if r["done"]}
    # The next CR is the first in table order (the build order) that isn't merged.
    nxt = todo[0]
    waiting = [d for d in nxt["depends"] if d not in done]
    if waiting:
        return {**info, "action": "stop", "stop": "blocked",
                "reason": f"{nxt['cr']} depends on {', '.join(waiting)}, which is not merged yet."}
    merged_before = [r["cr"] for r in live if r["done"]]
    replan_after = merged_before[-1] if merged_before and merged_before[-1] not in (
        re.findall(r"after (CR-\d{3})", text.split("## Replan log", 1)[-1])) else None
    return {**info, "current_cr": nxt["cr"], "replan_offer": replan_after, **state(root, nxt["cr"])}


def state(root, cr):
    project = Project(root, cr)
    result = {"cr": cr, "branch": project.current, "action": None}

    def finish(action, reason, **extra):
        result.update(action=action, reason=reason, **extra)
        return result

    cr_text = project.read(f"specs/change-requests/{cr}.md")
    if cr_text is None:
        return finish("refuse", f"specs/change-requests/{cr}.md does not exist.")
    status = field(cr_text, "Status") or ""
    risk = (field(cr_text, "Risk") or "").split()[0].lower() if field(cr_text, "Risk") else ""
    result.update(status=status, risk=risk or "missing", title=(cr_text.splitlines()[0].split(":", 1)[-1].strip()))
    if status.startswith("Done"):
        return finish("done", "This CR is already merged.")
    if not status.startswith("Approved"):
        return finish("refuse", f"The CR's Status is \"{status}\", not Approved.")
    if risk not in ("low", "high"):
        return finish("refuse", "The CR has no \"Risk: low\" or \"Risk: high\" line.")
    if not baseline_approved(root):
        return finish("refuse", "Gate 1 (baseline specs) is not approved yet.")

    rows = project.timeline()
    trace = project.read("docs/traceability.md") or ""
    trace_rows = [line for line in trace.splitlines() if re.match(rf"^\|\s*{cr}\s*\|", line)]
    summary = project.read(f"specs/proposed/{cr}/summary.md")
    design = project.read(f"docs/design/{cr}.md")
    design_first = (design or "").splitlines()[0] if design else ""
    gate2 = last_gate_line(summary, 2)
    gate3 = last_gate_line(design_first, 3)
    combined = risk == "low"

    def ended_after(stage, other_index):
        """True if the timeline has an 'end' of stage after row other_index."""
        return project.last_index(rows, stage, "end") > other_index

    def rerun_after_reject(stage, gates):
        """A gate was rejected and the stage has not ended since."""
        reject = max((project.last_index(rows, g, "rejected") for g in gates), default=-1)
        return reject >= 0 and not ended_after(stage, reject)

    def stale(stage, upstream):
        """The upstream stage ended (in the timeline) after this stage last ended."""
        up = project.last_index(rows, upstream, "end")
        return up >= 0 and project.last_index(rows, stage, "end") < up

    def run(stage, prompt, slice_number=None, switch_to=None):
        agent = agent_for(project, stage)
        budget = project.budgets()[stage]
        spent = project.spent(stage)
        remaining = round(budget - spent, 2)
        common = dict(stage=stage, agent=agent, prompt_version=prompt_version(root, agent),
                      slice=slice_number, budget_usd=budget, spent_usd=round(spent, 4))
        if remaining < 0.05:
            return finish("stop", f"The {stage} budget is used up: ${spent:.2f} of ${budget:.2f} "
                                  f"(Budgets line in CLAUDE.md).", stop="budget", **common)
        command = ["python3", str(PLUGIN_ROOT / "scripts" / "run_agent.py"), "--agent", agent, "--cr", cr,
                   "--stage", stage, "--budget", f"{remaining:.2f}",
                   "--permission-mode", "acceptEdits", "--prompt", prompt]
        if stage == "build":
            test_command = project.settings().get("Test command", "")
            tools = ["Bash(git status:*)", "Bash(git switch:*)", "Bash(git checkout:*)",
                     "Bash(git branch:*)", "Bash(git add:*)", "Bash(git commit:*)",
                     "Bash(git log:*)", "Bash(git diff:*)", "Bash(git rev-parse:*)"]
            if test_command:
                tools += [f"Bash({test_command})", f"Bash({test_command}:*)"]
            command += ["--allowed-tools", *tools]
        return finish("run", f"Next stage: {stage}" + (f", slice {slice_number}" if slice_number else ""),
                      switch_to=switch_to, command=command,
                      command_line=" ".join(shlex.quote(word) for word in command), **common)

    # ---- Specify
    spec_needed = (summary is None or not trace_rows
                   or (gate2 != "approved" and rerun_after_reject("specify", ("gate2", "gate23"))))
    if spec_needed:
        return run("specify", f"{cr}. Follow your definition exactly.")

    # ---- Gate 2 (high risk), or design + combined gate (low risk)
    if gate2 != "approved":
        if not combined:
            return finish("stop", "Gate 2 is due: review the proposed specs.", stop="gate2",
                          review=[f"specs/proposed/{cr}/", "docs/traceability.md"])
        if design is None or rerun_after_reject("design", ("gate23", "gate3")) or stale("design", "specify"):
            return run("design", f"{cr}. Risk is low: the specs in specs/proposed/{cr}/ are still "
                                 "Proposed, because the PO approves them together with your design. "
                                 "Follow your definition exactly.")
        return finish("stop", "Gates 2+3 (combined, low risk) are due: review the specs and the design together.",
                      stop="gate23", review=[f"specs/proposed/{cr}/", f"docs/design/{cr}.md"])

    # ---- Design and Gate 3 (high risk; low risk passed both above)
    if gate3 != "approved":
        if design is None or rerun_after_reject("design", ("gate3", "gate23")):
            return run("design", f"{cr}. Follow your definition exactly.")
        return finish("stop", "Gate 3 is due: review the design.", stop="gate3", review=[f"docs/design/{cr}.md"])

    # ---- Build, slice by slice
    report = project.read(f"docs/build/{cr}-report.md")
    review_text = project.read(f"docs/review/{cr}-review.md")
    gate4 = last_gate_line(review_text, 4)
    if gate4 == "approved":
        return finish("done", "Gate 4 is approved.")

    reject4 = project.last_index(rows, "gate4", "rejected")
    if reject4 >= 0 and not ended_after("build", reject4):
        note = rows[reject4]["outcome"]
        return run("build", f"{cr}. The design is docs/design/{cr}.md (Gate 3 approved). The PO rejected "
                            f"Gate 4: {note}. Fix that and nothing else. Follow your definition exactly. "
                            f"Report in docs/build/{cr}-report.md under a new heading '# Gate 4 fix'.")

    slices = slices_in_design(design)
    # A slice is done when its last timeline line says the tests passed. Slices the
    # timeline doesn't know (built with /sdlc:build) count as done if the report has a heading for them.
    last_outcome = {}
    for row in rows:
        match = re.match(r"build \(slice (\d+)\)", row["stage"])
        if match and row["event"] in ("end", "failed", "stopped"):
            last_outcome[int(match.group(1))] = row["event"] == "end" and row["outcome"].startswith("tests pass")
    done = {n for n, passed in last_outcome.items() if passed}
    for match in re.finditer(r"^#+ .*?\bslice (\d+)", report or "", re.MULTILINE | re.IGNORECASE):
        if int(match.group(1)) not in last_outcome:
            done.add(int(match.group(1)))
    result.update(slices=slices, slices_done=sorted(done & set(slices)) if slices else [])
    if slices:
        todo = [n for n in slices if n not in done]
        if todo:
            n = todo[0]
            return run("build", f"{cr}, slice {n}. The design is docs/design/{cr}.md (Gate 3 approved). "
                                f"Follow your definition exactly. Report in docs/build/{cr}-report.md "
                                f"under the heading '# Slice {n}'.", slice_number=n)
    elif report is None or not project.branch_exists:
        return run("build", f"{cr}. The design is docs/design/{cr}.md (Gate 3 approved). "
                            f"Follow your definition exactly. Report in docs/build/{cr}-report.md.")

    # ---- Review, then Gate 4
    switch = project.branch if project.current != project.branch else None
    if review_text is None or stale("review", "build"):
        code, changed = git("diff", "--name-only", f"main...{project.branch}", root=root)
        files = ", ".join(changed.split()) if code == 0 and changed else "(none found)"
        return run("review", f"{cr}. Changed files: {files}. Follow your definition exactly.", switch_to=switch)
    verdict = (re.search(r"^## Verdict:\s*(.+)$", review_text, re.MULTILINE) or [None, ""])[1].strip()
    result.update(verdict=verdict)
    if verdict.lower().startswith("not ready"):
        return finish("stop", "The reviewer says Not ready: there are Blockers to fix.", stop="blockers",
                      review=[f"docs/review/{cr}-review.md"])
    pr = (f"git push -u origin {project.branch} && gh pr create --base main --head {project.branch} "
          f"--title {pr_title(cr + ': ' + result['title'])} --body-file docs/review/{cr}-review.md")
    return finish("stop", "Gate 4 is due: review the branch, the build report and the review.", stop="gate4",
                  switch_to=switch, pr_command=pr,
                  review=[f"docs/review/{cr}-review.md", f"docs/build/{cr}-report.md",
                          f"git diff main...{project.branch}"])


# ---------------------------------------------------------------- log

def log(root, cr, stage, event, agent=None, slice_number=None, outcome="", note=""):
    project = Project(root, cr)
    path = project.timeline_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(TIMELINE_HEADER.format(cr=cr), encoding="utf-8")
    rows = project.timeline()
    stamp = now()
    label = f"{stage} (slice {slice_number})" if slice_number else stage
    if event == "due" and rows and rows[-1]["stage"] == label and rows[-1]["event"] == "due":
        print("Already logged: this gate is still due.")
        return
    extra = []
    if event in ("end", "failed", "stopped") and stage in DEFAULT_BUDGETS:
        start = project.last_index(rows, stage, "start")
        if start >= 0:
            started = parse_time(rows[start]["time"])
            extra.append(f"took {human((stamp - started).total_seconds())}")
            cost = project.last_cost_row(stage)
            if cost and parse_time(cost["timestamp"]) and parse_time(cost["timestamp"]) >= started.replace(microsecond=0):
                extra.append(f"${float(cost['total_cost_usd'] or 0):.2f}")
    if event in ("approved", "rejected"):
        due = project.last_index(rows, stage, "due")
        if due >= 0:
            extra.append(f"waited {human((stamp - parse_time(rows[due]['time'])).total_seconds())}")
    text = "; ".join(part for part in [outcome, note and f"note: {note}", *extra] if part)
    text = text.replace("|", "/").replace("\n", " ")
    version = prompt_version(root, agent) if agent else ""
    line = f"| {stamp.strftime('%Y-%m-%dT%H:%M:%SZ')} | {label} | {event} | {agent or '-'} | {version or '-'} | {text or '-'} |\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
    print(line.strip())


# ---------------------------------------------------------------- test

def cochange(root, commits=300, top=20, bulk=30):
    app = Project(root, "CR-000").settings().get("App folder", "").strip().strip("/")
    result = {"app_folder": app, "commits_read": 0, "commits_skipped_bulk": 0, "pairs": [], "note": ""}
    if not app:
        result["note"] = "CLAUDE.md has no App folder line."
        return result
    code, out = git("log", f"-n{commits}", "--no-merges", "--name-only", "--format=format:@@commit", "--", app, root=root)
    if code != 0 or not out:
        result["note"] = "No git history for the app folder."
        return result
    counts, changes = {}, {}
    for block in out.split("@@commit")[1:]:
        files = sorted({line.strip() for line in block.splitlines() if line.strip()})
        if not files:
            continue
        if len(files) > bulk:
            result["commits_skipped_bulk"] += 1
            continue
        result["commits_read"] += 1
        for f in files:
            changes[f] = changes.get(f, 0) + 1
        for i, a in enumerate(files):
            for b in files[i + 1:]:
                counts[(a, b)] = counts.get((a, b), 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
    result["pairs"] = [{"files": [a, b], "together": n, "changes": [changes[a], changes[b]]} for (a, b), n in ranked if n > 1]
    if not result["pairs"]:
        result["note"] = "No two files changed together more than once."
    return result


def test(root):
    command = Project(root, "CR-000").settings().get("Test command")
    if not command:
        sys.exit("Error: CLAUDE.md has no 'Test command:' line.")
    print(f"$ {command}")
    result = subprocess.run(command, shell=True, cwd=root, capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip().splitlines()
    print("\n".join(output[-40:]))
    print(f"exit code {result.returncode}: {'tests pass' if result.returncode == 0 else 'TESTS FAIL'}")
    sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description="Bookkeeping for /sdlc:ship.")
    sub = parser.add_subparsers(dest="command", required=True)
    p_state = sub.add_parser("state")
    p_state.add_argument("cr")
    p_log = sub.add_parser("log")
    p_log.add_argument("cr")
    p_log.add_argument("stage", choices=["specify", "design", "build", "review", "gate2", "gate3", "gate23", "gate4"])
    p_log.add_argument("event", choices=["start", "end", "failed", "due", "approved", "rejected", "stopped"])
    p_log.add_argument("--agent")
    p_log.add_argument("--slice", type=int)
    p_log.add_argument("--outcome", default="")
    p_log.add_argument("--note", default="")
    sub.add_parser("test")
    p_agent = sub.add_parser("agent")
    p_agent.add_argument("name")
    p_co = sub.add_parser("cochange")
    p_co.add_argument("--commits", type=int, default=300)
    args = parser.parse_args()

    if args.command == "agent":
        info = definition_info(args.name)
        print(json.dumps(info, indent=2))
        sys.exit(1 if info["error"] else 0)

    root = repo_root()
    if args.command == "state":
        if re.fullmatch(r"FEAT-\d{3}", args.cr):
            print(json.dumps(feature_state(root, args.cr), indent=2))
        elif re.fullmatch(r"CR-\d{3}", args.cr):
            print(json.dumps(state(root, args.cr), indent=2))
        else:
            sys.exit("Error: the ID looks like CR-005 or FEAT-001.")
    elif args.command == "cochange":
        print(json.dumps(cochange(root, args.commits), indent=2))
    elif args.command == "log":
        log(root, args.cr, args.stage, args.event, args.agent, args.slice, args.outcome, args.note)
    else:
        test(root)


if __name__ == "__main__":
    main()
