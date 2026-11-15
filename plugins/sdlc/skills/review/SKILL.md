---
description: Run the reviewer agent on a built CR branch before Gate 4
argument-hint: CR-NNN
allowed-tools: Read, Glob, Grep, Bash(python3 *scripts/ship.py* agent *), Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git branch:*), Bash(git switch:*), Bash(ls:*)
disable-model-invocation: true
---
Stage: Review, for "$ARGUMENTS". Explain each step in one plain sentence.

## Preconditions (stop politely at the first failure, ending with a "Next:" line)
1. The CR ID is valid and specs/change-requests/<CR>.md exists.
2. Gate 3 is approved (first line of docs/design/<CR>.md starts with "Gate 3 approved"). If not: Next: /sdlc:gate 3 <CR> approve "<note>".
3. Branch cr-nnn (the CR ID in lower case) exists and has commits that main doesn't (`git log --oneline main..cr-nnn`). If not: "There is nothing to review yet." Next: /sdlc:build <CR>.
4. docs/build/<CR>-report.md exists on that branch.
5. No uncommitted changes to tracked files. Then switch to the branch if needed (`git switch cr-nnn`) and say so.
6. Check the reviewer definition: run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" agent reviewer`. If "error" is set, say it plainly and stop (Next: commit the agent file, or `/plugin update sdlc@agentic-sdlc`). Note "prompt_version" and "definition".

## Run
1. Get the changed files: `git diff --name-only main...cr-nnn`.
2. Say: "The reviewer agent is checking every changed file against the approved specs and design: tests, security, design conformance and code quality. It changes nothing except its review file."
3. Run the `sdlc:reviewer` agent (Agent tool, subagent_type "sdlc:reviewer") with: "<CR>. Changed files: <the list>. Follow your definition exactly."
   If it returns the review as text instead of writing it, save it verbatim to docs/review/<CR>-review.md with the "saved verbatim by the main session" note (docs/gates.md).

## After the run
1. Show the verdict and the findings by severity (one line each).
2. Say: "Run: reviewer, <prompt version>, definition <definition>."
3. List the deviations in docs/build/<CR>-report.md that have no PO decision yet. Explain: decide each one (accept / reject / backlog) under "PO decisions" in the CR, and either fix or accept every Major finding.
Nothing is committed yet; /sdlc:gate 4 commits the review.

Last line, one of:
Next: decide the open deviations and findings, then /sdlc:gate 4 <CR> approve "<note>"   (verdict "Ready to merge" or "Ready with conditions")
Next: /sdlc:build <CR> to fix the Blockers, then /sdlc:review <CR> again   (verdict "Not ready")
