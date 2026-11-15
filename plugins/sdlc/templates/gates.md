# Human gates

| Gate | After stage | Who | Approves | Recorded by |
|---|---|---|---|---|
| Gate 0 | Plan | PO | The slicing of a new project or a big feature into CRs (specs/features/FEAT-NNN.md), before any of its CRs start | Line in the feature file, commit |
| Gate 1 | Explore | PO | Baseline specs in specs/existing/ match the code | Commit "Gate 1 approved" |
| Gate 2 | Specify | PO | Proposed specs for a CR are complete and testable | Traceability rows Proposed -> Approved, line in summary.md, commit |
| Gate 3 | Architect | PO + tech lead | Design note for a CR | Same pattern, in docs/design/CR-NNN.md |
| Gate 4 | Test & quality | Reviewer + PO | Pull request (code, tests, scans) | Line in docs/review/CR-NNN-review.md, then the merge records below; PR approval on GitHub if you use pull requests |
| ADR gate | Decide (any time) | Tech lead or architect | An architecture decision record, docs/adr/ADR-NNN.md (packaging, modularity, monolith or services) | Status Proposed -> Accepted (or Rejected), line under "## Approval", commit |

## Gate 0 (Plan)
A new project (/sdlc:new-project) or a big feature (/sdlc:new-feature) is planned as a feature file, specs/features/FEAT-NNN.md, with one draft CR per slice. The PO approves the slicing at Gate 0, before any of its CRs start:
- the CRs are vertical (each delivers something a user can see), small, ordered by dependency and risk, each with a risk level;
- the MVP line is right (which CRs are needed to be useful);
- for a new project, docs/product-brief.md and the system design in docs/design/system.md.
Only Gate 0 makes the feature's CRs Approved, and so shippable. A CR that /sdlc:replan changes or adds goes back to Draft and needs Gate 0 again.
A new project has no existing code, so it has no Gate 1: approving a new project's plan at Gate 0 takes its place.

## ADR gate (architecture decisions)
An architecture decision (one package or several, monolith or services, how to split into modules) is written as an ADR, docs/adr/ADR-NNN.md, by /sdlc:decide (after a drivers interview) or, for a new project, by the planner. It starts as "Status: Proposed". A tech lead or architect approves or rejects it with `/sdlc:gate adr ADR-NNN approve|reject "<note>"`, at any time; it is not tied to a CR.
- An Accepted ADR is binding: the architect follows every Accepted ADR in every design, and the reviewer reports a change that breaks one as a Major finding.
- A design that needs to break an Accepted ADR says so and proposes a new ADR that supersedes it; it never diverges silently. Gate 3 asks before approving such a design while that ADR is still Proposed.
- An Accepted ADR is never edited. To change it, write a new ADR whose "Supersedes:" line names it; approving the new one marks the old one Superseded.

## Risk tiers
Every CR has a "Risk:" line (the sdlc plugin's change request template). It decides which gates the CR goes through. A CR with no Risk line is treated as high risk.
- **High risk** (security, personal data, money, or anything hard to undo): Gates 1-4 as in the table above.
- **Low risk** (everything else): Gates 2 and 3 are one approval. The spec-writer and the architect run back to back, and the PO reviews the proposed specs and the design together. Gate 4 is unchanged.

How the combined gate works (low risk only):
- The architect may start while the CR's traceability rows are still "Proposed" (it needs "Approved" for high-risk CRs).
- `/sdlc:gate 2 <CR> approve "<note>"` (or `/sdlc:gate 3`, same effect) needs both specs/proposed/<CR>/summary.md and docs/design/<CR>.md. It writes the Gate 2 records and the Gate 3 record below, each note ending "(Gates 2+3 combined, low risk)", in one commit "<CR>: Gates 2+3 approved (low risk)". All later checks see an ordinary Gate 2 and Gate 3.
- A reject writes both rejection lines; the spec-writer and then the architect re-run.

How each gate is recorded (the /sdlc:gate command does exactly this; "<date>" is today, YYYY-MM-DD):
- Gate 0 approve: every CR of the feature whose Status starts with "Draft" gets "Status: Approved (PO, <date>, Gate 0 FEAT-NNN)", in its file and in the feature's CR table; the feature's Status becomes "Approved (PO, <date>)"; the line "Gate 0 approved by PO, <date>: <note>" is added under "## Gate 0" in the feature file. New project only: the "Project settings" lines of docs/design/system.md replace those in CLAUDE.md. Commit the feature, its CRs, CLAUDE.md and (new project) docs/product-brief.md, docs/design/system.md and docs/adr/ (the stack and structure ADRs, still Proposed until the ADR gate): "FEAT-NNN: Gate 0 approved", with " (new project)" added for a new project.
- ADR gate approve: the ADR's Status becomes "Accepted (<date>)" and the line "ADR approved by tech lead or architect, <date>: <note>" goes under "## Approval"; if it supersedes ADR-MMM, that ADR's Status becomes "Superseded by ADR-NNN (<date>)" and its "Superseded by:" line is set; commit "ADR-NNN: approved (ADR gate)". Reject: the ADR's Status becomes "Rejected (<date>): <note>" and the line "ADR rejected by tech lead or architect, <date>: <note>" goes under "## Approval"; nothing else changes (an ADR it would supersede stays as it is); commit "ADR-NNN: rejected (ADR gate)". A Rejected ADR binds nobody; /sdlc:decide ADR-NNN revises it and makes it Proposed again.
- Gate 1 approve: a commit "Gate 1 approved: <note>" that includes specs/existing/, docs/system-map.md and docs/coverage.md.
- Gate 2 approve: every CR-NNN row in docs/traceability.md goes from "Proposed" to "Approved (PO, <date>)"; the line "Gate 2 approved by PO, <date>: <note>" is added at the end of specs/proposed/CR-NNN/summary.md; commit "CR-NNN: Gate 2 approved".
- Gate 3 approve: the line "Gate 3 approved by PO, <date>: <note>" becomes the first line of docs/design/CR-NNN.md; commit "CR-NNN: Gate 3 approved".
- Gate 4 approve: the line "Gate 4 approved by PO, <date>: <note>" goes under the verdict in docs/review/CR-NNN-review.md. Then, on merge: specs/proposed/CR-NNN/REQ-*.md move to specs/existing/ (summary.md stays as the Gate 2 record), the CR-NNN rows in docs/traceability.md become "Merged", and the CR's Status becomes "Done (<date>)"; commit "CR-NNN: Gate 4 approved", then branch cr-NNN is merged into main with a merge commit.
- Approve with "defaults accepted" in the note (gates 2-4): every open question still unanswered (in the proposed specs, the design's "Risks and open questions", and the build report's deviations) is written under "PO decisions" in the CR as "<date>: <question or D-NN>: <the proposed default> (default accepted at Gate N)", and the CR goes into the same commit. A deviation's default is "accept".
- Reject (any gate): the line "Gate N rejected by PO, <date>: <note>" in the same place as the approval line (Gate 0: under "## Gate 0" in the feature file, and the plan's files are committed too; Gate 1: in a commit message only); nothing else changes; commit "CR-NNN: Gate N rejected". The stage is re-run after the note is addressed.
- A CR itself is approved before Gate 2: its Status line becomes "Approved (PO, <date>)".
- Timeline: if docs/build/<CR>-timeline.md exists, every gate decision (gates 2-4) appends a line to it (the plugin's ship.py does it: `ship.py log <CR> gate<N> approved|rejected --note "<note>"`), and the file goes into the gate commit. /sdlc:ship writes the stage lines.

Rules:
- Specs move from specs/proposed/ to specs/existing/ only after Gate 4, when the change is merged. specs/existing/ always describes what the code does today.
- A gate is passed only on agent output. No hand edits to agent output before approval.
- Open questions must be empty, or each one explicitly deferred to a named later stage, before Gate 2.
- Agent output includes text returned by an agent and saved verbatim by the main session, with a note saying so.
- At Gate 2, open questions about implementation detail are deferred to the Architect stage; only questions that change what a customer or associate experiences need a PO answer.
- An agent runs only from a committed definition. Every run report states the prompt version and the definition: the commit hash of the agent file when the sdlc plugin is used from a git checkout, or the plugin version (e.g. sdlc@1.0.0) when it is installed from a marketplace, which can't change without an update.
