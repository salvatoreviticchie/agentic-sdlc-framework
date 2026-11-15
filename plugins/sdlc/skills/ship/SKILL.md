---
description: Run every stage of an approved CR (or each CR of a feature, in order) on its own, stopping only when a gate is due
argument-hint: CR-NNN | FEAT-NNN
allowed-tools: Read, Glob, Grep, Write, Bash(python3 *scripts/ship.py*), Bash(python3 *scripts/run_agent.py*), Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git branch:*), Bash(git switch:*), Bash(ls:*)
disable-model-invocation: true
---
Ship "$ARGUMENTS": run the next stage, then the next, and keep going without asking, until a gate is due. You never record a gate yourself, and never push, merge or open a pull request; the PO does that. Explain each step in one plain sentence as you go.

`ship.py` (in the plugin) does the exact parts (which stage is next, the timeline, the budgets, the tests). Use its output; don't work the stage out yourself. Run every command from the repo root. Give agent runs the longest Bash timeout (10 minutes); if a run needs longer, run it in the background and wait for it.

## 1. Check
1. "$ARGUMENTS" is a CR ID like CR-005 or a feature ID like FEAT-001 (otherwise list specs/change-requests/CR-*.md and specs/features/FEAT-*.md and stop with "Next: /sdlc:ship CR-NNN").
2. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" state <ID>` with the ID as given. It prints JSON. For a feature it also has "feature", "progress", "mvp_progress", "current_cr" and "replan_offer"; see "Shipping a feature" below. If "action" is:
   - "refuse": say the reason plainly and stop. The fix, as the Next: line: CR not approved → `/sdlc:new-cr` finishes it, or set "Status: Approved (PO, <date>)" yourself; no Risk line → add "Risk: low" or "Risk: high" to the CR (see ${CLAUDE_PLUGIN_ROOT}/templates/change-request.md), commit it, then /sdlc:ship <CR>; Gate 1 → `/sdlc:gate 1 approve "<note>"`.
   - "done": say so. Next: /sdlc:status.
   - "stop" with "stop" gate0 or blocked (features only): go straight to 3. Stop.
3. Say the CR's risk tier in one line: high = Gates 2, 3 and 4 separately; low = specs and design reviewed together at one gate (docs/gates.md, Risk tiers).
4. No uncommitted changes to tracked files except pipeline outputs (specs/proposed/, specs/features/, docs/, runs/): `git status --porcelain --untracked-files=no`. If there are others, list them and stop: "Next: commit or stash them, then /sdlc:ship <CR>".

## 2. Loop: while "action" is "run"
For each step:
1. If "switch_to" is set, `git switch <it>` and say so.
2. Say what is about to happen in one line: the stage, the agent, its prompt version, the slice if any, and the budget left ("budget_usd" minus "spent_usd").
3. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" log <CR> <stage> start --agent <agent> [--slice N]`
4. Run "command_line" exactly as printed (it is the plugin's run_agent.py with the remaining stage budget).
5. Check the result, then log the end. Use `--outcome` for a short result, e.g. "4 specs, 2 open questions":
   - The run printed "BUDGET STOPPED" or exited non-zero: log `stopped` with the reason and go to step 3 (Stop), reason "budget" or "agent error".
   - The agent returned a file as text instead of writing it: save it verbatim with the "saved verbatim by the main session" note (docs/gates.md).
   - specify: specs/proposed/<CR>/summary.md exists and docs/traceability.md has <CR> rows "Proposed". design: docs/design/<CR>.md exists. review: docs/review/<CR>-review.md exists with a "## Verdict:" line. If not, log `failed` and stop, saying what is missing.
   - build: run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" test` yourself (don't rely on the developer's report).
     - Tests fail: log `failed --slice N --outcome "tests fail: <counts>"` and stop: show the failing tests and the developer's explanation.
     - Tests pass: read the deviations the developer added in this run (D-NN in docs/build/<CR>-report.md). A deviation **changes behaviour** if what a user or caller sees differs from the approved specs: an acceptance criterion met differently or not at all, a changed output, message, error, exit code or data format, or a new requirement. File layout, names, refactoring and test structure don't. If one changes behaviour, log `end --slice N --outcome "tests pass; D-NN changes behaviour"` and stop: explain the deviation in plain words and what the spec says instead. Otherwise log `end --slice N --outcome "tests pass (<counts>); deviations: <D-NN list or none>"` and continue.
6. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" state <ID>` again (the same ID: CR or FEAT), and loop.

Low risk: this runs specify and then design back to back, then stops once for the combined gate.

## 3. Stop
When "action" is "stop" (or you stopped above):
1. For a gate ("stop" is gate2, gate3, gate23 or gate4): `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" log <CR> <stop> due`. If "switch_to" is set, switch first so the PO sees the branch.
2. Print, in this order and nothing longer than needed:
   - **Stopped at:** the gate or the reason (budget used up, tests fail, a behaviour-changing deviation, review Blockers), in one line.
   - **Review:** the paths in "review", one per line.
   - **Open questions** (gates only), numbered, each with the agent's proposed default:
     - gate2 / gate23: every item under "Open questions" in specs/proposed/<CR>/REQ-*.md (skip "None") not yet answered under "PO decisions" in the CR.
     - gate3 / gate23: every item in the design's "Risks and open questions".
     - gate4: every deviation D-NN without a PO decision (default: accept) and every Major or Blocker finding in the review.
     If there are none, say "None".
   - **Approve all defaults:** the exact command, e.g. `/sdlc:gate 2 CR-005 approve "defaults accepted"` (gate23: `/sdlc:gate 2 <CR> ...`, it records both gates). Say that to override a default, add the answer under "PO decisions" in the CR first, then approve with your own note; to send it back, use `reject "<what to change>"`.
   - gate4 only: **Pull request:** "pr_command" from the state, to run yourself if you use a remote. Say /sdlc:ship never pushes or merges; `/sdlc:gate 4` records the approval and merges into main locally.
   - **Timeline:** the last lines of docs/build/<CR>-timeline.md for this run.
3. End with exactly these two lines:
   - Next: the single command to run (the approve-defaults command at a gate, followed for a feature by "then /sdlc:ship <FEAT>"; at a non-gate stop, what fixes it, e.g. raise the stage's budget in CLAUDE.md and /sdlc:ship <CR>, or /sdlc:ship <CR> to let the developer try the failing slice again; for a behaviour-changing deviation, decide it under "PO decisions" in the CR, then /sdlc:ship <CR>)
   - Tip: run /clear before the next command to start with a fresh context; /sdlc:ship <ID> picks up from the files. (Write the real ID, the one /sdlc:ship was given: e.g. "/sdlc:ship FEAT-001", never a placeholder.)

Running /sdlc:ship <ID> again after a gate continues from where it stopped.

## Shipping a feature (/sdlc:ship FEAT-NNN)
The feature's CRs (specs/features/FEAT-NNN.md) are shipped one at a time, in the order of its table, exactly as /sdlc:ship CR-NNN does, with the same stops. ship.py picks the CR ("current_cr"): the first one not merged, once the CRs it depends on are merged.
- Start by showing the feature's progress in one line: "<FEAT>: <progress>, <mvp_progress>. Now: <current_cr> <title>."
- In everything below, <CR> means "current_cr"; the Next: lines name the feature (`/sdlc:ship <FEAT>`), not the CR.
- If "replan_offer" is set, a CR was merged since the last re-plan. Say once, before starting the next CR: "<replan_offer> is merged. If it taught you something about the rest of the plan, stop me and run /sdlc:replan <FEAT>; I'll go on with <current_cr>." Then go on.
- At the Gate 4 stop, add after the approve command: "After that: /sdlc:replan <FEAT> (recommended: updates the remaining CRs with what this one taught), or /sdlc:ship <FEAT> for the next CR."
- Stops only features have: gate0 (the plan, or CRs changed by a re-plan, need Gate 0): Next: read the review paths, then /sdlc:gate 0 <FEAT> approve "defaults accepted"; blocked (the next CR waits for a CR that isn't merged): explain, Next: /sdlc:status.
- When every CR is merged ("done"): say so with the progress. Next: /sdlc:status.
