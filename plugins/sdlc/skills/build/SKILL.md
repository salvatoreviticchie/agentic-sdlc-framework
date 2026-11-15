---
description: Run the developer agent on a CR whose design passed Gate 3 (optionally one slice)
argument-hint: CR-NNN [slice]
allowed-tools: Read, Glob, Grep, Bash(python3 *scripts/ship.py* agent *), Bash(git status:*), Bash(git log:*), Bash(git branch:*), Bash(git rev-parse:*), Bash(ls:*)
disable-model-invocation: true
---
Stage: Build, for "$ARGUMENTS" (first word: the CR ID; optional second word: the slice). Explain each step in one plain sentence.

## Preconditions (stop politely at the first failure, ending with a "Next:" line)
1. The CR ID is valid and specs/change-requests/<CR>.md exists (otherwise list the CRs; Next: /sdlc:build CR-NNN).
2. Gate 3 is approved: the first line of docs/design/<CR>.md starts with "Gate 3 approved". If not: "Code is written only from an approved design." Next: /sdlc:design <CR> (no design yet) or /sdlc:gate 3 <CR> approve "<note>".
3. Every <CR> row in docs/traceability.md starts with "Approved".
4. If the design has a "Slices:" list and no slice was given: list the slices, and say which ones docs/build/<CR>-report.md already reports as done. Ask which slice to build (suggest the first one not done) and wait.
5. No uncommitted changes to tracked files (`git status --porcelain --untracked-files=no` prints nothing), because the developer switches to branch cr-nnn. If there are, list them. Next: commit or stash them, then /sdlc:build <CR>.
6. Choose the developer: read "Stack:" in CLAUDE.md. "salesforce" → agent `developer-salesforce`; anything else → agent `developer`. Say which one and why in one line.
7. Check the chosen agent's definition: run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" agent <agent>`. If "error" is set, say it plainly and stop (Next: commit the agent file, or `/plugin update sdlc@agentic-sdlc`). Note "prompt_version" and "definition".
8. CLAUDE.md has a "Test command:" line (show it).

## Run
Say: "The <agent> agent is implementing <CR> <slice> on branch cr-nnn (lower case), writing tests and running them with your test command. Your main branch is not touched."
Run the chosen agent (Agent tool, subagent_type "sdlc:developer" or "sdlc:developer-salesforce") with:
"<CR><, slice N if given>. The design is docs/design/<CR>.md (Gate 3 approved). Follow your definition exactly. Report in docs/build/<CR>-report.md."

## After the run
1. Show: the branch (`git branch --show-current`), the new commits (`git log --oneline main..HEAD`), the test result counts and the deviations from the report.
2. Say: "Run: <agent>, <prompt version>, definition <definition>."
3. If the developer stopped without finishing, say why plainly and suggest the fix.
4. Explain: each deviation needs your decision (accept / reject / backlog), written under "PO decisions" in the CR, before Gate 4.

Last line, one of:
Next: /sdlc:build <CR> <next slice>   (if the design has slices not built yet)
Next: /sdlc:review <CR>   (if all slices are built and the tests pass)
