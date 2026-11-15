---
description: Show every CR with its current stage, last gate, and the next command to run
allowed-tools: Read, Glob, Grep, Bash(python3 *scripts/ship.py* state *), Bash(git status:*), Bash(git log:*), Bash(git branch:*), Bash(git show:*), Bash(ls:*)
disable-model-invocation: true
---
Show where the project is. Read only: change nothing.

1. Gate 1: approved if some commit message contains "Gate 1 approved", or "Gate 0 approved (new project)" for a new project (show "new project: Gate 0 replaces Gate 1") (`git log --all --grep "Gate 1 approved" --oneline -1`), rejected if the latest gate-1 commit says "Gate 1 rejected". Show one line: "Baseline specs (Gate 1): approved <date> / rejected / not yet (N specs in specs/existing/)".
2. For every specs/change-requests/CR-*.md, work out (files on branch cr-nnn count too: check with `git show cr-nnn:<path>` when the branch exists):
   - Status line and Risk line of the CR (no Risk line = high)
   - Last gate: the highest gate with an approval or rejection line (Gate 2: specs/proposed/<CR>/summary.md; Gate 3: first line of docs/design/<CR>.md; Gate 4: docs/review/<CR>-review.md), with its date
   - Stage and next command, using the first rule that matches:
     | Situation | Stage | Next |
     |---|---|---|
     | Status starts with "Done" | Merged | — |
     | Status "Draft" | CR draft | /sdlc:specify <CR> (asks you to approve it) |
     | No specs/proposed/<CR>/ | CR approved | /sdlc:specify <CR> |
     | Gate 2 rejected | Specify (changes requested) | /sdlc:specify <CR> |
     | Low risk, no "Gate 2 approved" line, no docs/design/<CR>.md | Design (low risk: one gate for specs + design) | /sdlc:ship <CR> or /sdlc:design <CR> |
     | Low risk, no "Gate 2 approved" line | Waiting for Gates 2+3 | /sdlc:gate 2 <CR> approve "<note>" |
     | No "Gate 2 approved" line | Specify, waiting for Gate 2 | /sdlc:gate 2 <CR> approve "<note>" |
     | No docs/design/<CR>.md, or Gate 3 rejected | Design | /sdlc:design <CR> |
     | Design without "Gate 3 approved" | Design, waiting for Gate 3 | /sdlc:gate 3 <CR> approve "<note>" |
     | No branch cr-nnn or no docs/build/<CR>-report.md | Build | /sdlc:build <CR> |
     | Design has slices not yet in the report | Build (slice N next) | /sdlc:build <CR> <N> |
     | No docs/review/<CR>-review.md, or Gate 4 rejected | Review | /sdlc:review <CR> |
     | No "Gate 4 approved" line | Review, waiting for Gate 4 | /sdlc:gate 4 <CR> approve "<note>" |
   If Gate 1 is not approved, the Next for every CR is "/sdlc:gate 1 approve \"<note>\"" first.
3. Print the CRs grouped by feature. For every specs/features/FEAT-*.md, a heading line:
   "**FEAT-NNN <title>** (<Type>): <n> of <m> CRs merged, MVP <x> of <y>; Gate 0 <approved <date> | rejected | not yet>"
   where m counts the CRs in its table except Dropped ones, n those whose CR file has Status "Done", and x of y the same for the CRs with MVP "yes".
   Under it, one markdown table in the feature's table order: CR | Title | MVP | Status | Risk | Stage | Last gate | Next. A CR whose Status starts with "Draft" and has a "Feature:" line: Stage "Planned, waiting for Gate 0", Next "/sdlc:gate 0 <FEAT> approve \"<note>\"". A feature with Gate 0 approved and CRs left: its Next is "/sdlc:ship <FEAT>". Within a feature only one CR is next: the first in table order that isn't merged (`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" state <FEAT>` names it as "current_cr"). Give that CR its Next; for every later CR not yet started, Stage "Planned (after <the CR before it, or the CRs it depends on>)" and Next "—", so nobody starts CRs out of order.
   Then the CRs with no feature (no "Feature:" line, or "Feature: none") in the same table under "**Other CRs**".
   If there are no CRs, say so.
4. Architecture decisions: if docs/adr/ has ADR-*.md files, a table "**ADRs**": ADR | Title | Status | Next. Status is the file's Status line (Proposed, Accepted (<date>), Rejected (<date>): <note>, or Superseded by ADR-MMM (<date>)); show a Rejected ADR's note, shortened to about 60 characters. A "Proposed" ADR with an "ADR rejected" line under "## Approval": if a "Revised by /sdlc:decide" line follows it, show "Proposed (revised after rejection <date>)"; if not, it was rejected by an older plugin version: show "Rejected (<date>)" and treat it as Rejected. Next: Proposed → /sdlc:gate adr <ADR> approve "<note>"; Rejected → /sdlc:decide <ADR> (to revise it), or — if you don't need it; Accepted or Superseded → —. Don't count Proposed ADRs as blocking any CR.
5. One line on the current branch and whether there are uncommitted changes.

Last line: "Next: " followed by the single most useful command (the earliest unfinished stage, /sdlc:ship <FEAT> for a feature in progress; for an empty project: /sdlc:new-project <idea> if the app folder is empty, /sdlc:explore if it has code but specs/existing/ is empty; /sdlc:new-cr <description> or /sdlc:new-feature <description> if every CR is merged).
