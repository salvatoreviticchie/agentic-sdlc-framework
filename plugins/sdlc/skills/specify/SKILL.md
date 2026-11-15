---
description: Run the spec-writer agent on an approved CR (needs Gate 1)
argument-hint: CR-NNN
allowed-tools: Read, Glob, Grep, Bash(python3 *scripts/ship.py* agent *), Edit, Bash(git status:*), Bash(git log:*), Bash(git add:*), Bash(git commit:*), Bash(ls:*)
disable-model-invocation: true
---
Stage: Specify, for "$ARGUMENTS". Explain each step in one plain sentence.

## Preconditions (stop politely at the first failure, ending with a "Next:" line that fixes it)
1. "$ARGUMENTS" is a CR ID like CR-001 and specs/change-requests/<CR>.md exists. If not: list the CRs that exist and say "Next: /sdlc:specify CR-NNN" (or "/sdlc:new-cr <description>" if there are none).
2. Gate 1 is approved: some commit message contains "Gate 1 approved", or "Gate 0 approved (new project)" for a new project, which has no code to explore (`git log --all --grep "Gate [01] approved" --oneline`). If not: "The baseline specs must be approved first, because new specs are written as changes to them." Next: /sdlc:gate 1 approve "<note>".
3. The CR's Status starts with "Approved". If it is "Draft" and the CR has a "Feature: FEAT-NNN" line: stop, "This CR is part of a plan; it is approved with the plan at Gate 0." Next: /sdlc:gate 0 <FEAT> approve "<note>". If it is "Draft" otherwise: show the CR's Problem and Acceptance criteria, ask "Do you approve this CR as the PO? (yes/no)" and wait. On yes, set "Status: Approved (PO, <today>)" and commit only that file ("<CR>: approved by PO"); on no, stop with "Next: edit specs/change-requests/<CR>.md, then /sdlc:specify <CR>".
4. If the CR's Status starts with "Done": stop, "This CR is already merged." Next: /sdlc:status.
5. Check the spec-writer definition: run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" agent spec-writer`. If "error" is set, say it plainly and stop (Next: commit the agent file, or `/plugin update sdlc@agentic-sdlc`). Note "prompt_version" and "definition".
6. If specs/proposed/<CR>/ already exists, say this is a re-run and the files will be updated.

## Run
Say: "The spec-writer agent is turning <CR> into updated specs in specs/proposed/<CR>/."
Run the `sdlc:spec-writer` agent (Agent tool, subagent_type "sdlc:spec-writer") with: "<CR>. Follow your definition exactly."
If it returns a file's content as text instead of writing it, save it verbatim with a first line "> Note: saved verbatim by the main session from the spec-writer's returned text, <date>, per docs/gates.md."

## After the run
1. Check that specs/proposed/<CR>/summary.md exists and docs/traceability.md has rows for <CR> with Status "Proposed".
2. Summarise: the specs changed or added, and every open question with its proposed default.
3. Say: "Run: spec-writer, <prompt version>, definition <definition>."
4. Explain Gate 2 in one sentence: you confirm the proposed specs are complete and testable. Open questions must be answered in the CR (under PO decisions) or deferred to a named later stage first.
Nothing is committed yet; /sdlc:gate 2 commits the files.

Last line:
Next: read specs/proposed/<CR>/, then /sdlc:gate 2 <CR> approve "<note>" (or /sdlc:gate 2 <CR> reject "<what to change>")
