#!/usr/bin/env python3
"""
smoke.py - the sdlc plugin's live end-to-end test. It runs real agents, so it
COSTS MONEY (Claude Code's estimate at API prices; a few USD) and takes
15-40 minutes.

    python3 plugins/sdlc/tests/smoke.py [--budget 5] [--keep] [--model <model>]

In a new temporary folder outside the repo it copies examples/tiny-app into
app/ and runs, headless (claude -p --plugin-dir <this checkout>
--permission-mode acceptEdits), the pipeline a person would run:

   1. /sdlc:init --defaults
   2. /sdlc:explore
   3. /sdlc:gate 1 approve
   4. /sdlc:decide --defaults "one package or several?"
   5. /sdlc:gate adr ADR-001 approve
   6. /sdlc:new-cr --defaults "reject an empty to-do item. Risk: low"
   7. the PO approves the CR (this script sets its Status line and commits,
      as docs/gates.md allows)
   8. /sdlc:ship CR-001            (specify and design, to the combined gate)
   9. /sdlc:gate 2 CR-001 approve  (Gates 2+3, low risk)
  10. /sdlc:ship CR-001            (build and review, to Gate 4)

After each step it checks the files and statuses that step must leave, and it
stops at the first failure. At the end it prints a summary (each step's result,
cost and duration), deletes the folder (unless --keep) and exits with 1 on any
failure.

The budget is a cap on the total: the Claude sessions above plus the agent
runs /sdlc:ship starts (runs/costs.csv). Each session gets what is left as its
--max-budget-usd, and the project's per-stage budgets are set from the total.
Tool calls the plugin's skills don't allow are denied (there is no person to
ask); they are listed as warnings, not failures.

Standard library only.
"""

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
REPO = PLUGIN.parent.parent
TINY_APP = REPO / "examples" / "tiny-app"
STEP_TIMEOUT_S = 40 * 60

# Share of the total budget for each /sdlc:ship stage (the project's Budgets line).
STAGE_SHARES = {"specify": 0.12, "design": 0.14, "build": 0.30, "review": 0.12}


class StepFailed(Exception):
    pass


class Smoke:
    def __init__(self, folder, budget, model):
        self.folder = folder
        self.budget = budget
        self.model = model
        self.session_cost = 0.0
        self.steps = []        # (name, ok, cost, seconds, note)
        self.warnings = []

    # ---- helpers -------------------------------------------------------
    def git(self, *args, check=True):
        result = subprocess.run(["git", *args], cwd=self.folder, capture_output=True, text=True)
        if check and result.returncode != 0:
            raise StepFailed(f"git {' '.join(args)} failed: {result.stderr.strip()}")
        return result.stdout.strip()

    def read(self, path):
        file = self.folder / path
        if not file.exists():
            raise StepFailed(f"{path} does not exist")
        return file.read_text(encoding="utf-8")

    def agent_cost(self):
        """What the agent runs started by /sdlc:ship have cost (runs/costs.csv)."""
        path = self.folder / "runs" / "costs.csv"
        if not path.exists():
            return 0.0
        with path.open(encoding="utf-8") as f:
            return sum(float(row.get("total_cost_usd") or 0) for row in csv.DictReader(f))

    def spent(self):
        return self.session_cost + self.agent_cost()

    def claude(self, prompt):
        """Run one headless Claude Code session in the project; return its final reply."""
        left = self.budget - self.spent()
        if left < 0.05:
            raise StepFailed(f"budget used up: ${self.spent():.2f} of ${self.budget:.2f}")
        command = ["claude", "-p", prompt, "--plugin-dir", str(PLUGIN), "--output-format", "json",
                   "--permission-mode", "acceptEdits", "--max-budget-usd", f"{left:.2f}"]
        if self.model:
            command += ["--model", self.model]
        try:
            run = subprocess.run(command, cwd=self.folder, capture_output=True, text=True,
                                 timeout=STEP_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            raise StepFailed(f"no answer after {STEP_TIMEOUT_S // 60} minutes")
        try:
            data = json.loads(run.stdout)
        except ValueError:
            raise StepFailed(f"claude did not return JSON (exit {run.returncode}): "
                             f"{(run.stderr or run.stdout).strip()[:300]}")
        self.session_cost += float(data.get("total_cost_usd") or 0)
        for denial in data.get("permission_denials") or []:
            command_text = (denial.get("tool_input") or {}).get("command") or denial.get("tool_name")
            self.warnings.append(f"{prompt.split()[0]}: denied {str(command_text)[:150]}")
        if data.get("subtype") == "error_max_budget_usd":
            raise StepFailed(f"budget used up during the step: ${self.spent():.2f} of ${self.budget:.2f}")
        if data.get("is_error"):
            raise StepFailed(f"the session ended with an error: {data.get('subtype')} {str(data.get('result'))[:300]}")
        return data.get("result") or ""

    def step(self, name, action):
        start, cost_before = time.time(), self.spent()
        print(f"... {name}", flush=True)
        try:
            note = action() or ""
            ok = True
        except StepFailed as error:
            note, ok = str(error), False
        self.steps.append((name, ok, self.spent() - cost_before, time.time() - start, note))
        print(f"{'PASS' if ok else 'FAIL'}  {name}  (${self.spent() - cost_before:.2f}, "
              f"{time.time() - start:.0f}s){': ' + note if note else ''}", flush=True)
        if not ok:
            raise StepFailed(name)

    def last_commit(self):
        return self.git("log", "-1", "--format=%s")

    def expect_commit(self, pattern):
        subjects = self.git("log", "--all", "--format=%s")
        if not re.search(pattern, subjects, re.MULTILINE):
            raise StepFailed(f"no commit matching {pattern!r} (last: {self.last_commit()!r})")

    def clean_tree(self):
        dirty = self.git("status", "--porcelain", "--untracked-files=no")
        if dirty:
            raise StepFailed(f"uncommitted changes to tracked files: {dirty[:200]}")

    def setting(self, key):
        match = re.search(rf"^- {key}:\s*(.+)$", self.read("CLAUDE.md"), re.MULTILINE)
        return match.group(1).strip() if match else ""

    # ---- the steps -----------------------------------------------------
    def init(self):
        self.claude("/sdlc:init --defaults")
        for key, want in [("App folder", "app"), ("Stack", "python")]:
            if self.setting(key) != want:
                raise StepFailed(f"CLAUDE.md {key}: {self.setting(key)!r}, expected {want!r}")
        if not self.setting("Test command"):
            raise StepFailed("CLAUDE.md has no Test command")
        for path in ["docs/gates.md", "specs/change-requests", ".claude/settings.json"]:
            if not (self.folder / path).exists():
                raise StepFailed(f"{path} was not created")
        if not self.git("ls-files", "app"):
            raise StepFailed("app/ is not committed")
        self.clean_tree()
        # Per-stage budgets that fit inside the total.
        text = self.read("CLAUDE.md")
        line = "- Budgets (USD per stage): " + ", ".join(
            f"{stage} {self.budget * share:.2f}" for stage, share in STAGE_SHARES.items())
        text, count = re.subn(r"^- Budgets \(USD per stage\):.*$", line, text, flags=re.MULTILINE)
        if count != 1:
            raise StepFailed("CLAUDE.md has no Budgets line")
        (self.folder / "CLAUDE.md").write_text(text, encoding="utf-8")
        self.git("commit", "-qam", "Smoke test: per-stage budgets")
        return f"Stack {self.setting('Stack')}, tests: {self.setting('Test command')}"

    def explore(self):
        self.claude("/sdlc:explore")
        specs = list((self.folder / "specs" / "existing").glob("REQ-*.md"))
        if not specs:
            raise StepFailed("no specs in specs/existing/")
        if "## " not in self.read("docs/system-map.md"):
            raise StepFailed("docs/system-map.md has no sections")
        if "structure" not in self.read("docs/system-map.md").lower():
            raise StepFailed("docs/system-map.md has no Structure section")
        return f"{len(specs)} specs, system map written"

    def gate1(self):
        self.claude('/sdlc:gate 1 approve "Smoke test: specs match the code"')
        self.expect_commit(r"^Gate 1 approved")
        self.clean_tree()

    def decide(self):
        self.claude('/sdlc:decide --defaults "one package or several?"')
        status = re.search(r"^Status: (.*)$", self.read("docs/adr/ADR-001.md"), re.MULTILINE)
        if not status or not status.group(1).startswith("Proposed"):
            raise StepFailed(f"ADR-001 Status is {status.group(1) if status else 'missing'!r}, expected Proposed")
        return "ADR-001 Proposed"

    def adr_gate(self):
        self.claude('/sdlc:gate adr ADR-001 approve "Smoke test: defaults accepted"')
        text = self.read("docs/adr/ADR-001.md")
        if not re.search(r"^Status: Accepted \(\d{4}-\d\d-\d\d\)", text, re.MULTILINE):
            raise StepFailed("ADR-001 is not Accepted")
        if "ADR approved by tech lead or architect" not in text:
            raise StepFailed("ADR-001 has no approval line")
        self.expect_commit(r"^ADR-001: approved")
        self.clean_tree()
        return "ADR-001 Accepted"

    def new_cr(self):
        self.claude('/sdlc:new-cr --defaults "reject an empty to-do item. Risk: low"')
        text = self.read("specs/change-requests/CR-001.md")
        risk = re.search(r"^Risk: (\w+)", text, re.MULTILINE)
        if not risk or risk.group(1) != "low":
            raise StepFailed(f"CR-001 Risk is {risk.group(1) if risk else 'missing'!r}, expected low")
        if not re.search(r"^Status: Draft", text, re.MULTILINE):
            raise StepFailed("CR-001 is not a Draft (--defaults must not approve it)")
        if "Given" not in text:
            raise StepFailed("CR-001 has no acceptance criteria")
        return "CR-001 Draft, Risk low"

    def approve_cr(self):
        path = self.folder / "specs" / "change-requests" / "CR-001.md"
        today = time.strftime("%Y-%m-%d")
        text, count = re.subn(r"^Status: Draft.*$", f"Status: Approved (PO, {today})",
                              path.read_text(encoding="utf-8"), count=1, flags=re.MULTILINE)
        if count != 1:
            raise StepFailed("CR-001 has no Draft Status line")
        path.write_text(text, encoding="utf-8")
        self.git("add", str(path))
        self.git("commit", "-qm", "CR-001: approved by PO (smoke test)")

    def ship_to_gate23(self):
        self.claude("/sdlc:ship CR-001")
        if "Proposed" not in self.read("docs/traceability.md"):
            raise StepFailed("docs/traceability.md has no Proposed rows")
        if not list((self.folder / "specs" / "proposed" / "CR-001").glob("REQ-*.md")):
            raise StepFailed("no proposed specs in specs/proposed/CR-001/")
        self.read("specs/proposed/CR-001/summary.md")
        design = self.read("docs/design/CR-001.md")
        if "ADR-001" not in design:
            self.warnings.append("design: docs/design/CR-001.md doesn't name ADR-001 (the Accepted ADR)")
        timeline = self.read("docs/build/CR-001-timeline.md")
        for stage in ("specify", "design"):
            if not re.search(rf"\|\s*{stage}\s*\|\s*end", timeline):
                raise StepFailed(f"the timeline has no '{stage} end' line")
        if not re.search(r"gate23\s*\|\s*due", timeline):
            raise StepFailed("the timeline doesn't say the combined gate is due")
        return "specs, design note and timeline written; combined gate due"

    def gate23(self):
        self.claude('/sdlc:gate 2 CR-001 approve "defaults accepted"')
        self.expect_commit(r"^CR-001: Gates 2\+3 approved")
        if not re.search(r"^Gate 3 approved", self.read("docs/design/CR-001.md"), re.MULTILINE):
            raise StepFailed("docs/design/CR-001.md has no Gate 3 approval line")
        if "Approved (PO" not in self.read("docs/traceability.md"):
            raise StepFailed("traceability rows are not Approved")

    def ship_to_gate4(self):
        self.claude("/sdlc:ship CR-001")
        branches = self.git("branch", "--format=%(refname:short)").split()
        if "cr-001" not in branches:
            raise StepFailed(f"no branch cr-001 (branches: {branches})")
        changed = self.git("diff", "--name-only", "main...cr-001").split()
        code = [f for f in changed if f.startswith("app/")]
        if not code:
            raise StepFailed("cr-001 changes nothing in app/")
        if not any("test" in Path(f).name for f in code):
            raise StepFailed(f"no test file changed in app/ (changed: {code})")
        self.git("switch", "-q", "cr-001")
        # Pipeline outputs (docs/, specs/, runs/) wait for Gate 4; anything else should be committed.
        stray = [line for line in self.git("status", "--porcelain", "--untracked-files=no").splitlines()
                 if not line[3:].startswith(("docs/", "specs/", "runs/"))]
        if stray:
            self.warnings.append(f"ship: uncommitted changes left on cr-001: {stray[:5]}")
        tests = subprocess.run(self.setting("Test command"), shell=True, cwd=self.folder,
                               capture_output=True, text=True, timeout=600)
        if tests.returncode != 0:
            raise StepFailed("the tests fail on cr-001: " + (tests.stderr or tests.stdout)[-400:])
        review = self.read("docs/review/CR-001-review.md")
        verdict = re.search(r"^## Verdict:\s*(.+)$", review, re.MULTILINE)
        if not verdict:
            raise StepFailed("docs/review/CR-001-review.md has no '## Verdict:' line")
        if not re.search(r"gate4\s*\|\s*due", self.read("docs/build/CR-001-timeline.md")):
            raise StepFailed("the timeline doesn't say Gate 4 is due")
        counts = (tests.stderr or tests.stdout).strip().splitlines()
        return f"{len(code)} app files changed, tests pass ({counts[-1] if counts else 'ok'}), verdict: {verdict.group(1).strip()}"

    def run(self):
        steps = [("1 /sdlc:init --defaults", self.init),
                 ("2 /sdlc:explore", self.explore),
                 ("3 /sdlc:gate 1 approve", self.gate1),
                 ("4 /sdlc:decide --defaults", self.decide),
                 ("5 /sdlc:gate adr ADR-001 approve", self.adr_gate),
                 ("6 /sdlc:new-cr --defaults (Risk: low)", self.new_cr),
                 ("7 PO approves CR-001", self.approve_cr),
                 ("8 /sdlc:ship CR-001 (to Gates 2+3)", self.ship_to_gate23),
                 ("9 /sdlc:gate 2 CR-001 approve (2+3)", self.gate23),
                 ("10 /sdlc:ship CR-001 (to Gate 4)", self.ship_to_gate4)]
        for name, action in steps:
            self.step(name, action)


def main():
    parser = argparse.ArgumentParser(description="Live end-to-end test of the sdlc plugin (costs money).")
    parser.add_argument("--budget", type=float, default=5.0, help="total cap in USD (default 5)")
    parser.add_argument("--keep", action="store_true", help="keep the temporary folder for inspection")
    parser.add_argument("--model", help="model for the sessions that run the commands (default: yours)")
    args = parser.parse_args()

    if not shutil.which("claude"):
        sys.exit("Error: the claude command is not on PATH.")
    if not TINY_APP.is_dir():
        sys.exit(f"Error: {TINY_APP} not found.")
    dirty = subprocess.run(["git", "status", "--porcelain", "--", str(PLUGIN / "agents")],
                           cwd=REPO, capture_output=True, text=True).stdout.strip()
    if dirty:
        sys.exit("Error: plugins/sdlc/agents has uncommitted changes; agents run only from a "
                 "committed definition (docs/gates.md). Commit them first.")

    folder = Path(tempfile.mkdtemp(prefix="sdlc-smoke-")).resolve()
    if folder.is_relative_to(REPO):
        sys.exit(f"Error: the temporary folder {folder} is inside the repo.")
    project = folder / "todo"
    project.mkdir()
    shutil.copytree(TINY_APP, project / "app")
    print(f"sdlc smoke test in {project}\nplugin: {PLUGIN}\nbudget: ${args.budget:.2f}\n", flush=True)

    smoke = Smoke(project, args.budget, args.model)
    started = time.time()
    try:
        smoke.run()
    except StepFailed:
        pass
    except KeyboardInterrupt:
        smoke.steps.append(("interrupted", False, 0.0, 0.0, "Ctrl-C"))
    finally:
        failed = [s for s in smoke.steps if not s[1]]
        passed = len(smoke.steps) - len(failed)
        print("\n== Summary")
        for name, ok, cost, seconds, note in smoke.steps:
            print(f"{'PASS' if ok else 'FAIL'}  {name:<40} ${cost:5.2f} {seconds:6.0f}s  {note[:140]}")
        for warning in smoke.warnings:
            print(f"WARN  {warning}")
        print(f"\n{'PASSED' if not failed and len(smoke.steps) == 10 else 'FAILED'}: {passed} of 10 steps passed. "
              f"Cost ${smoke.spent():.2f} (sessions ${smoke.session_cost:.2f}, agent runs ${smoke.agent_cost():.2f}) "
              f"of ${args.budget:.2f}. Took {(time.time() - started) / 60:.1f} min.")
        if args.keep:
            print(f"Kept: {project}")
        else:
            shutil.rmtree(folder, ignore_errors=True)
            print(f"Deleted {folder}")
    sys.exit(0 if not failed and len(smoke.steps) == 10 else 1)


if __name__ == "__main__":
    main()
