# Cost and context

How to keep agent runs cheap and the main session's context small.

## Context
- **Run `/clear` between stages.** Every command reads what it needs from the files (the CR, the specs, the design, the reports, the timeline), so nothing is lost. Each `/sdlc:ship` stop ends with this tip.
- **Agents run in their own context.** `/sdlc:ship` runs each agent as a separate `claude -p` session (the plugin's `run_agent.py`), so the agent's file reading doesn't fill your session. Claude Code ignores `.claude/settings.json` in a folder you haven't trusted yet, so open the project with `claude` once and accept the trust dialog before your first `/sdlc:ship`.
- **Don't read large reports whole.** Grep them, or read only the line ranges you need. The reviewer agent does this for build reports over 50 KB.

## Budgets
- Set them in `CLAUDE.md` under "Project settings":
  `- Budgets (USD per stage): specify 1, design 1, build 5, review 1`
  Without that line, `/sdlc:ship` uses these defaults.
- A budget covers every agent run for that CR and stage, re-runs included. Build is one budget for all slices.
- `/sdlc:ship` passes the budget left to the run (`--max-budget-usd`) and stops when a stage's budget is used up. To go on, raise the budget in `CLAUDE.md` and type `/sdlc:ship CR-NNN` again.

## Cost per run
- The plugin's `run_agent.py` adds one row per agent run to `runs/costs.csv`: cost, tokens, time, turns, budget, and whether the budget stopped the run. It saves the full JSON to `runs/<timestamp>-<cr>-<stage>.json`.
- Ask Claude to "run the sdlc cost report": the plugin's `cost_report.py` prints cost and tokens per CR and stage, with a total per CR.
- `docs/build/CR-NNN-timeline.md` shows each stage's time and cost and how long each gate waited for the PO.

## What the plugin itself costs
The sdlc plugin adds about 750 tokens to every session: one short line per command and agent (`claude plugin details sdlc@agentic-sdlc` shows the numbers). A command's full instructions load only when you type it.

## What the numbers mean
The costs are Claude Code's client-side estimates at API prices (`total_cost_usd`). On a subscription plan they are not what you are billed; read them as a measure of relative size.
