---
description: Record a PO gate decision exactly as docs/gates.md says (traceability, summary line, commit)
argument-hint: <0-4> [FEAT-NNN | CR-NNN] approve|reject "<note>"
allowed-tools: Read, Glob, Grep, Edit, Bash(python3 *scripts/ship.py log *), Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git add:*), Bash(git commit:*), Bash(git mv:*), Bash(git switch:*), Bash(git merge:*), Bash(git branch:*), Bash(ls:*), Bash(date:*)
disable-model-invocation: true
---
Record a gate decision: "$ARGUMENTS"
The arguments are: gate number (0-4), the ID (a FEAT-NNN for Gate 0, a CR-NNN for gates 2-4, none for Gate 1), "approve" or "reject", and a note in quotes.
Follow "Risk tiers" and "How each gate is recorded" in docs/gates.md exactly; read it first. <date> is today (`date +%F`). Change nothing else. Explain each step in one plain sentence.

## Check the arguments
- If anything is missing or not valid, show the usage with one example per gate, end with a "Next:" line, and stop:
  `/sdlc:gate 0 FEAT-001 approve "defaults accepted"`, `/sdlc:gate 1 approve "Specs match the code"`, `/sdlc:gate 2 CR-001 approve "Criteria are testable"`,
  `/sdlc:gate 3 CR-001 reject "Option B is simpler"`, `/sdlc:gate 4 CR-001 approve "All deviations decided"`.
- A note is required. If it is missing, ask for it and wait.

## Risk tier (gates 2 and 3)
Read the CR's "Risk:" line. "low" means Gates 2 and 3 are one decision: `/sdlc:gate 2` and `/sdlc:gate 3` both take the combined gate (docs/gates.md, Risk tiers). A missing Risk line means high risk. Say which tier applies in one line.

## Check the gate can be taken (stop politely, with a "Next:" line, if not)
- Gate 0: specs/features/<FEAT>.md exists and every CR in its table has a file in specs/change-requests/ (otherwise Next: /sdlc:new-feature <description> or /sdlc:new-project <idea>). For approve: list the feature's open questions (and, for a new project, those in docs/design/system.md) not answered under "PO decisions" in the feature file, and ask "Approve anyway? (yes/no)"; wait (not with "defaults accepted": record the defaults in the feature file's "PO decisions" instead). Only CRs whose Status starts with "Draft" are approved; say which ones.
- Gate 1: specs/existing/ has REQ-*.md files and docs/system-map.md exists (otherwise Next: /sdlc:explore).
- Gate 2: specs/proposed/<CR>/summary.md exists and the <CR> rows in docs/traceability.md are "Proposed" (otherwise Next: /sdlc:specify <CR>). For approve: list any open question in the proposed specs that is neither answered under "PO decisions" in the CR nor deferred to a named stage, and ask "Approve anyway? (yes/no)"; wait.
- Gate 3: docs/design/<CR>.md exists and Gate 2 is approved (otherwise Next: /sdlc:design <CR>).
- Combined Gates 2+3 (low risk): specs/proposed/<CR>/summary.md and docs/design/<CR>.md both exist, the <CR> rows are "Proposed" (otherwise Next: /sdlc:ship <CR>). For approve, check open questions in both the specs and the design, as for Gate 2.
- "defaults accepted" in an approve note: don't ask "Approve anyway?" for open questions or undecided deviations; record their defaults under "PO decisions" instead (docs/gates.md).
- Gate 4: docs/review/<CR>-review.md exists on branch cr-nnn (otherwise Next: /sdlc:review <CR>). For approve: if the verdict is "Not ready", refuse ("Fix the Blockers first." Next: /sdlc:build <CR>). List deviations in docs/build/<CR>-report.md without a PO decision; if any, ask "Approve with these undecided? (yes/no)" and wait.
- The gate is not already approved (the approval line or commit exists): if it is, say so and stop with Next: /sdlc:status.
- No uncommitted changes to tracked files other than the files this gate records (list them if there are).

## Record it (exactly as docs/gates.md says)
- Gate 0 approve: in each Draft CR file of the feature, set "Status: Approved (PO, <date>, Gate 0 <FEAT>)", and set the same Status in the feature's CR table; set the feature's "Status: Approved (PO, <date>)"; add "Gate 0 approved by PO, <date>: <note>" under "## Gate 0" (replace the template's placeholder line). If the feature's Type is "new project": copy the three lines under "## Project settings" in docs/design/system.md over "App folder:", "Stack:" and "Test command:" in CLAUDE.md (keep the other lines). `git add specs/features/<FEAT>.md specs/change-requests CLAUDE.md` (and docs/product-brief.md docs/design/system.md for a new project); commit "<FEAT>: Gate 0 approved", plus " (new project)" for a new project.
- Gate 0 reject: add "Gate 0 rejected by PO, <date>: <note>" under "## Gate 0"; change nothing else; add and commit the same files as for approve: "<FEAT>: Gate 0 rejected".
- Gate 1 approve: `git add specs/existing docs/system-map.md docs/coverage.md`, then commit "Gate 1 approved: <note>".
- Gate 1 reject: commit with `--allow-empty` "Gate 1 rejected: <note>". Then say: fix the specs by re-running /sdlc:explore, or by noting what is wrong.
- Gate 2 approve: change every <CR> row's Status in docs/traceability.md from "Proposed" to "Approved (PO, <date>)"; append "Gate 2 approved by PO, <date>: <note>" as the last line of specs/proposed/<CR>/summary.md; `git add specs/proposed/<CR> docs/traceability.md`; commit "<CR>: Gate 2 approved".
- Gate 3 approve: insert "Gate 3 approved by PO, <date>: <note>" as the first line of docs/design/<CR>.md (then a blank line); `git add docs/design/<CR>.md`; commit "<CR>: Gate 3 approved".
- Combined Gates 2+3 approve (low risk): do the Gate 2 edits and the Gate 3 edit, each line ending " (Gates 2+3 combined, low risk)"; `git add specs/proposed/<CR> docs/traceability.md docs/design/<CR>.md`; one commit "<CR>: Gates 2+3 approved (low risk)".
- "defaults accepted": before committing, add one line per open question or undecided deviation under "PO decisions" in specs/change-requests/<CR>.md ("<date>: <question or D-NN>: <proposed default> (default accepted at Gate N)") and `git add` the CR too.
- Timeline: if docs/build/<CR>-timeline.md exists, run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" log <CR> gate<N> approved|rejected --note "<note>"` before committing (gate23 for the combined gate) and `git add` the file. For Gate 4, do it on branch cr-nnn before step 5.
- Gate 4 approve, on branch cr-nnn (switch to it first):
  1. Add "Gate 4 approved by PO, <date>: <note>" on its own line right under the "## Verdict" line of docs/review/<CR>-review.md.
  2. `git mv` each specs/proposed/<CR>/REQ-*.md to specs/existing/ (replace the old file of the same name; summary.md stays).
  3. Set the <CR> rows in docs/traceability.md to "Merged".
  4. Set the CR's Status line to "Done (<date>)". If the CR has a "Feature: FEAT-NNN" line, set its Status in that feature's CR table to "Done (<date>)" too, and add specs/features/FEAT-NNN.md to the commit.
  5. `git add` those files; commit "<CR>: Gate 4 approved".
  6. `git switch main` and `git merge --no-ff cr-nnn -m "Merge cr-nnn: <CR> (Gate 4 approved)"`. If the merge has conflicts, stop, show them, and do not resolve them yourself.
- Reject (gates 2-4): put "Gate N rejected by PO, <date>: <note>" where the approval line would go (Gate 2: end of summary.md; Gate 3: first line of the design; Gate 4: under the verdict); change nothing else; commit "<CR>: Gate N rejected". Combined (low risk): both lines, commit "<CR>: Gates 2+3 rejected (low risk)".

## After
Show the commit (`git log --oneline -1`) and, in one sentence, what the gate means.

Last line, by gate and decision. If the CR has a "Feature: FEAT-NNN" line, write /sdlc:ship <FEAT> wherever a line below says /sdlc:ship <CR>, /sdlc:design <CR> or /sdlc:build <CR> after an approval (the feature is shipped as a whole):
- 0 approve → Next: /sdlc:ship <FEAT>   (ships its CRs in order, first: <the first CR in the table>)
- 0 reject → Next: /sdlc:replan <FEAT>   (the planner re-slices with your note)
- 1 approve → Next: /sdlc:new-cr <one-line description of a change you want>  (add one example built from the top risk in docs/system-map.md, e.g. "/sdlc:new-cr Refuse task numbers below 1")
- 2 approve → Next: /sdlc:design <CR>   (if the CR came through /sdlc:ship: /sdlc:ship <CR>)
- combined 2+3 approve → Next: /sdlc:ship <CR>   (or /sdlc:build <CR>)
- 3 approve → Next: /sdlc:build <CR>   (if the CR came through /sdlc:ship: /sdlc:ship <CR>)
- 4 approve → Next: /sdlc:status (and `git push` if you use a remote); for a CR of a feature: Next: /sdlc:replan <FEAT> (recommended), or /sdlc:ship <FEAT> for the next CR
- 1 reject → Next: /sdlc:explore
- 2 reject → Next: answer the note in the CR under "PO decisions", then /sdlc:specify <CR>
- 3 reject → Next: add the note under "PO decisions" in the CR, then /sdlc:design <CR> (or /sdlc:ship <CR>)
- combined 2+3 reject → Next: add the note under "PO decisions" in the CR, then /sdlc:ship <CR>
- 4 reject → Next: /sdlc:build <CR> to fix it, then /sdlc:review <CR>
