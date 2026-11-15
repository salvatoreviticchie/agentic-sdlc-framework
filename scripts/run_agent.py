#!/usr/bin/env python3
"""
run_agent.py - run one of our Claude Code agents and log what the run cost.

What it does, step by step:
  1. Finds the agent's definition file, .claude/agents/<agent>.md.
  2. Refuses to run if that file has uncommitted changes. Our gates rule
     (docs/gates.md) says an agent runs only from a committed definition.
  3. Reads the "Prompt version:" line from the file, and asks git for the
     short hash of the last commit that changed the file.
  4. Runs Claude Code headless:
        claude -p "<prompt>" --agent <agent> --output-format json --max-budget-usd <budget>
               --permission-mode <mode>
  5. Saves Claude's full JSON answer to runs/<timestamp>-<cr>-<stage>.json.
  6. Adds one row to runs/costs.csv (cost, tokens, time, turns, ...).
  7. Prints a one-line summary.

Example:
  python3 scripts/run_agent.py --agent developer --cr CR-002 --stage build \
      --prompt "Implement CR-002 slice 1" --budget 3.00

It uses only the Python standard library, so there is nothing to install.

About the numbers: total_cost_usd is Claude Code's own client-side estimate
at API prices. On a subscription plan it is not what you are billed.
"""

# "import" loads a module (a library) so we can use its functions.
import argparse      # reads the --agent, --cr, ... options from the command line
import csv           # writes the costs.csv file
import json          # turns Claude's JSON text into Python dictionaries
import re            # "regular expressions": pattern matching in text
import subprocess    # runs other programs (git, claude) and captures their output
import sys           # gives us sys.exit() to stop the script with an error code
from datetime import datetime, timezone   # for the timestamp of the run
from pathlib import Path                  # a friendlier way to work with file paths


# The columns of runs/costs.csv, in order. Keeping them in one list means the
# header row and the data rows can never get out of step.
CSV_COLUMNS = [
    "timestamp",              # when the run started (UTC)
    "cr",                     # change request, e.g. CR-002
    "stage",                  # e.g. explore, specify, architect, build, review
    "agent",                  # e.g. developer
    "prompt_version",         # from the "Prompt version:" line of the agent file
    "definition_commit",      # last commit that changed the agent file
    "session_id",             # Claude Code session id (lets you find the transcript)
    "models",                 # every model the run used, separated by ";"
    "input_tokens",           # tokens sent to the model (not from the cache)
    "output_tokens",          # tokens the model wrote
    "cache_creation_tokens",  # tokens written into the prompt cache
    "cache_read_tokens",      # tokens read back from the prompt cache (cheaper)
    "total_cost_usd",         # Claude Code's estimate, in US dollars
    "duration_s",             # wall-clock time of the run, in seconds
    "num_turns",              # how many back-and-forth turns the agent took
    "budget_usd",             # the --budget we allowed
    "permission_mode",        # the --permission-mode passed to claude (blank for older rows)
    "budget_stopped",         # "yes" if the budget limit ended the run
    "result_subtype",         # Claude's own status, e.g. "success"
]


def run_command(args, cwd):
    """Run a program and return what it printed (stdout) as text.

    'args' is a list such as ["git", "status"]. Passing a list (not one long
    string) means no shell is involved, so quotes or spaces in the prompt
    can't break the command.
    """
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return result


def repo_root():
    """Return the top folder of the git repository we are in."""
    result = run_command(["git", "rev-parse", "--show-toplevel"], cwd=None)
    if result.returncode != 0:
        sys.exit("Error: this must be run inside the git repository.")
    # .strip() removes the newline at the end of git's output.
    return Path(result.stdout.strip())


def read_prompt_version(agent_file):
    """Find the line 'Prompt version: xyz' in the agent file and return 'xyz'."""
    text = agent_file.read_text(encoding="utf-8")
    # ^ = start of a line, \s* = any spaces, (\S+) = capture the next word.
    # re.MULTILINE makes ^ match at the start of every line, not just the file.
    match = re.search(r"^Prompt version:\s*(\S+)", text, re.MULTILINE)
    if match is None:
        sys.exit(f"Error: no 'Prompt version:' line in {agent_file}.")
    return match.group(1)


def check_committed(agent_file, root):
    """Stop if the agent file has uncommitted changes, then return its last commit hash."""
    # 'git status --porcelain -- <file>' prints nothing when the file is clean,
    # and a short code (M = modified, ?? = untracked, ...) when it is not.
    status = run_command(["git", "status", "--porcelain", "--", str(agent_file)], cwd=root)
    if status.stdout.strip():
        sys.exit(f"Error: {agent_file.relative_to(root)} has uncommitted changes. "
                 "Commit it first (gates rule: agents run only from a committed definition).")

    # %h = the short commit hash. "-1" = only the latest commit touching this file.
    log = run_command(["git", "log", "-1", "--format=%h", "--", str(agent_file)], cwd=root)
    commit = log.stdout.strip()
    if not commit:
        sys.exit(f"Error: {agent_file.relative_to(root)} has never been committed.")
    return commit


def token_totals(data):
    """Add up the tokens of the run.

    Claude's JSON has two places with token counts:
      - "modelUsage": one entry per model (the main agent and any subagents
        or helper models), e.g. {"claude-opus-5-5": {"inputTokens": ...}}
      - "usage": a single summary.
    We prefer modelUsage because it includes every model. If it is missing
    we fall back to usage. .get(key, default) returns default when the key
    is not there, so a missing field never crashes the script.
    """
    model_usage = data.get("modelUsage") or {}
    if model_usage:
        totals = {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0}
        for numbers in model_usage.values():
            totals["input"] += numbers.get("inputTokens", 0)
            totals["output"] += numbers.get("outputTokens", 0)
            totals["cache_creation"] += numbers.get("cacheCreationInputTokens", 0)
            totals["cache_read"] += numbers.get("cacheReadInputTokens", 0)
        models = ";".join(sorted(model_usage.keys()))
        return totals, models

    usage = data.get("usage") or {}
    totals = {
        "input": usage.get("input_tokens", 0),
        "output": usage.get("output_tokens", 0),
        "cache_creation": usage.get("cache_creation_input_tokens", 0),
        "cache_read": usage.get("cache_read_input_tokens", 0),
    }
    return totals, data.get("model", "")


def upgrade_csv_header(csv_path):
    """If costs.csv was written with an older list of columns, rewrite it with
    the current CSV_COLUMNS so new rows line up with the header.

    Columns that are new get an empty value in the old rows. We never drop a
    column: if the file has one we no longer know about, we stop instead.
    """
    if not csv_path.exists():
        return
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        old_columns = reader.fieldnames or []
        old_rows = list(reader)
    if old_columns == CSV_COLUMNS:
        return
    unknown = [c for c in old_columns if c not in CSV_COLUMNS]
    if unknown:
        sys.exit(f"Error: {csv_path} has columns this script does not know: {unknown}.")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for old_row in old_rows:
            writer.writerow({c: old_row.get(c, "") for c in CSV_COLUMNS})


def append_csv_row(csv_path, row):
    """Add one row to costs.csv. Write the header first if the file is new."""
    upgrade_csv_header(csv_path)
    is_new = not csv_path.exists()
    # "a" = append: add to the end, never overwrite earlier runs.
    # newline="" is what the csv module asks for, to avoid blank lines on Windows.
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def main():
    # ---- 1. Read the command-line options -------------------------------
    parser = argparse.ArgumentParser(description="Run a Claude Code agent and log its cost.")
    parser.add_argument("--agent", required=True, help="agent name, e.g. developer")
    parser.add_argument("--cr", required=True, help="change request, e.g. CR-002")
    parser.add_argument("--stage", required=True, help="stage, e.g. build or review")
    parser.add_argument("--prompt", required=True, help="the task for the agent")
    parser.add_argument("--budget", type=float, default=2.00,
                        help="maximum spend in USD (default 2.00)")
    # The choices are the modes `claude --help` lists for --permission-mode.
    parser.add_argument("--permission-mode", default="acceptEdits",
                        choices=["acceptEdits", "auto", "bypassPermissions",
                                 "manual", "dontAsk", "plan"],
                        help="permission mode passed to claude -p (default acceptEdits)")
    args = parser.parse_args()

    root = repo_root()
    agent_file = root / ".claude" / "agents" / f"{args.agent}.md"
    if not agent_file.exists():
        sys.exit(f"Error: {agent_file.relative_to(root)} does not exist.")

    # ---- 2 and 3. Gates rule, prompt version, definition commit ---------
    definition_commit = check_committed(agent_file, root)
    prompt_version = read_prompt_version(agent_file)

    # ---- 4. Run Claude Code ---------------------------------------------
    # A UTC timestamp without ":" so it is safe in a file name.
    started = datetime.now(timezone.utc)
    stamp = started.strftime("%Y%m%dT%H%M%SZ")

    command = [
        "claude", "-p", args.prompt,
        "--agent", args.agent,                 # run as this agent, so the logged version is the one used
        "--output-format", "json",             # one JSON object at the end, easy to parse
        "--max-budget-usd", f"{args.budget:.2f}",
        "--permission-mode", args.permission_mode,
    ]
    print(f"Running {args.agent} ({prompt_version} @ {definition_commit}) "
          f"for {args.cr}/{args.stage}, budget ${args.budget:.2f}, "
          f"permission mode {args.permission_mode} ...")
    result = run_command(command, cwd=root)

    # ---- 5. Save the full JSON answer ------------------------------------
    runs_dir = root / "runs"
    runs_dir.mkdir(exist_ok=True)   # create runs/ if needed; no error if it exists
    json_path = runs_dir / f"{stamp}-{args.cr}-{args.stage}.json"

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        # Claude didn't return JSON (for example it failed to start).
        # Keep whatever it printed so the problem can be investigated.
        raw_path = json_path.with_suffix(".txt")
        raw_path.write_text(result.stdout + "\n--- stderr ---\n" + result.stderr, encoding="utf-8")
        sys.exit(f"Error: claude did not return JSON (exit code {result.returncode}). "
                 f"Output saved to {raw_path.relative_to(root)}. No cost row was written.")

    # indent=2 makes the saved file readable for humans.
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # ---- 6. Append the cost row ------------------------------------------
    tokens, models = token_totals(data)
    subtype = data.get("subtype", "")
    # Claude reports a budget stop as an error subtype that mentions the budget
    # (e.g. "error_max_budget_usd"). We check for the word so small naming
    # changes in future Claude Code versions still count.
    budget_stopped = "budget" in subtype.lower()
    cost = data.get("total_cost_usd", 0.0)
    duration_s = data.get("duration_ms", 0) / 1000   # milliseconds -> seconds

    row = {
        "timestamp": started.isoformat(timespec="seconds"),
        "cr": args.cr,
        "stage": args.stage,
        "agent": args.agent,
        "prompt_version": prompt_version,
        "definition_commit": definition_commit,
        "session_id": data.get("session_id", ""),
        "models": models,
        "input_tokens": tokens["input"],
        "output_tokens": tokens["output"],
        "cache_creation_tokens": tokens["cache_creation"],
        "cache_read_tokens": tokens["cache_read"],
        "total_cost_usd": f"{cost:.4f}",
        "duration_s": f"{duration_s:.1f}",
        "num_turns": data.get("num_turns", 0),
        "budget_usd": f"{args.budget:.2f}",
        "permission_mode": args.permission_mode,
        "budget_stopped": "yes" if budget_stopped else "no",
        "result_subtype": subtype,
    }
    append_csv_row(runs_dir / "costs.csv", row)

    # ---- 7. One-line summary ---------------------------------------------
    flag = " BUDGET STOPPED THE RUN" if budget_stopped else ""
    print(f"{args.cr}/{args.stage} {args.agent} {prompt_version}@{definition_commit}: "
          f"${cost:.4f} of ${args.budget:.2f}, "
          f"{tokens['input']} in / {tokens['output']} out / "
          f"{tokens['cache_read']} cache read / {tokens['cache_creation']} cache write tokens, "
          f"{data.get('num_turns', 0)} turns, {duration_s:.0f}s, {subtype}{flag} "
          f"-> {json_path.relative_to(root)}")

    # Pass on a failure as the script's own exit code, so other scripts can notice.
    if data.get("is_error"):
        sys.exit(1)


# This line means: only run main() when the file is started as a script,
# not when another Python file imports it.
if __name__ == "__main__":
    main()
