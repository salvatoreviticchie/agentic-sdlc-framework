---
description: Update a feature's plan after one of its CRs is merged (or after a Gate 0 rejection)
argument-hint: FEAT-NNN
allowed-tools: Read, Glob, Grep, Bash(python3 *scripts/ship.py agent *), Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(ls:*), Bash(date:*)
disable-model-invocation: true
---
Re-plan "$ARGUMENTS". Explain each step in one plain sentence.

## Preconditions (stop politely at the first failure, ending with a "Next:" line)
1. "$ARGUMENTS" is a FEAT ID and specs/features/<FEAT>.md exists (otherwise list the features; Next: /sdlc:replan FEAT-NNN).
2. Work out why: the last line under "## Gate 0" is "Gate 0 rejected" (re-plan with that note), or some CR in the table has Status "Done" and there is no "Replan log" line after it yet (re-plan after that CR). If neither, say there is nothing new to learn from, and ask "Re-plan anyway? (yes/no)"; wait.
3. Check the planner definition: run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" agent planner`. If "error" is set, say it plainly and stop (Next: commit the agent file, or `/plugin update sdlc@agentic-sdlc`). Note "prompt_version" and "definition".

## Run
Say: "The planner is reading what was learned from <CR or the Gate 0 note> and updating the CRs that haven't started. It never changes a CR that is being built or is done."
Run the `sdlc:planner` agent (Agent tool, subagent_type "sdlc:planner") with:
"Mode: replan. FEAT ID: <FEAT>. Today: <date +%F>. <After: CR-NNN, merged | Gate 0 rejected: <note>>. Follow your definition exactly."

## After
1. Show the new "Replan log" lines, and the CR table before and after (`git diff specs/features/<FEAT>.md`).
2. Say: "Run: planner, <prompt version>, definition <definition>."
3. If any CR now has a Status starting with "Draft": explain that changed or new CRs need Gate 0 again, and unchanged ones keep their approval.
Nothing is committed yet; /sdlc:gate 0 commits it.

Last line, one of:
Next: read specs/features/<FEAT>.md, then /sdlc:gate 0 <FEAT> approve "<note>"   (if any CR is Draft)
Next: /sdlc:ship <FEAT>   (no change: the line is in the Replan log; it is committed with the next gate)
