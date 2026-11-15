---
description: Run the architect agent on a CR whose specs passed Gate 2
argument-hint: CR-NNN
allowed-tools: Read, Glob, Grep, Bash(python3 *scripts/ship.py* agent *), Bash(git status:*), Bash(git log:*), Bash(ls:*)
disable-model-invocation: true
---
Stage: Design, for "$ARGUMENTS". Explain each step in one plain sentence.

## Preconditions (stop politely at the first failure, ending with a "Next:" line)
1. "$ARGUMENTS" is a CR ID and specs/change-requests/<CR>.md exists (otherwise list the CRs; Next: /sdlc:design CR-NNN).
2. Gate 2 is approved: specs/proposed/<CR>/summary.md contains "Gate 2 approved" and every <CR> row in docs/traceability.md starts with "Approved". If not: "The design is built on approved specs." Next: /sdlc:specify <CR> (if there are no proposed specs) or /sdlc:gate 2 <CR> approve "<note>".
   Exception: if the CR's "Risk:" line is "low", proposed specs (rows "Proposed") are enough, because Gates 2 and 3 are taken together (docs/gates.md, Risk tiers). Say so.
3. Check the architect definition: run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" agent architect`. If "error" is set, say it plainly and stop (Next: commit the agent file, or `/plugin update sdlc@agentic-sdlc`). Note "prompt_version" and "definition".
4. If docs/design/<CR>.md exists: if its first line starts with "Gate 3 approved", stop ("Already approved." Next: /sdlc:build <CR>); otherwise say this is a re-run that overwrites it.

## Run
Say: "The architect agent is writing a design note: options, the chosen design, every file to change, and a test plan."
Run the `sdlc:architect` agent (Agent tool, subagent_type "sdlc:architect") with: "<CR>. Follow your definition exactly."
If it returns the note as text instead of writing it, save it verbatim to docs/design/<CR>.md with the "saved verbatim by the main session" note (docs/gates.md).

## After the run
1. Check docs/design/<CR>.md exists.
2. Summarise in at most 6 lines: the decision, the Accepted ADRs it follows, the files it will change, the slices (if any), and the open questions with defaults. If the architect proposed a superseding ADR, say so first: the design breaks an Accepted ADR, and a tech lead or architect should decide that ADR (/sdlc:gate adr ADR-NNN) before Gate 3.
3. Say: "Run: architect, <prompt version>, definition <definition>."
4. Explain Gate 3 in one sentence: you (and a tech lead, if you have one) approve the design before any code is written.
Nothing is committed yet; /sdlc:gate 3 commits it.

Last line, one of (the second for a low-risk CR: one gate for the specs and the design):
Next: read docs/design/<CR>.md, then /sdlc:gate 3 <CR> approve "<note>" (or /sdlc:gate 3 <CR> reject "<what to change>")
Next: read specs/proposed/<CR>/ and docs/design/<CR>.md, then /sdlc:gate 2 <CR> approve "<note>" (Gates 2+3 together, low risk)
