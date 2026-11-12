# Human gates

| Gate | After stage | Who | Approves | Recorded by |
|---|---|---|---|---|
| Gate 1 | Explore | PO | Baseline specs in specs/existing/ match the code | Commit "Gate 1 approved" |
| Gate 2 | Specify | PO | Proposed specs for a CR are complete and testable | Traceability rows Proposed -> Approved, line in summary.md, commit |
| Gate 3 | Architect | PO + tech lead | Design note for a CR | Same pattern, in docs/design/CR-NNN.md |
| Gate 4 | Test & quality | Reviewer | Pull request (code, tests, scans) | PR approval on your Git host |

Rules:
- Specs move from specs/proposed/ to specs/existing/ only after Gate 4, when the change is merged. specs/existing/ always describes what the code does today.
- A gate is passed only on agent output. No hand edits to agent output before approval.
- Open questions must be empty, or each one explicitly deferred to a named later stage, before Gate 2.
- Agent output includes text returned by an agent and saved verbatim by the main session, with a note saying so.
- At Gate 2, open questions about implementation detail are deferred to the Architect stage; only questions that change what a user experiences need a PO answer.
- An agent runs only from a committed definition. Every run report states the prompt version and the commit hash of the definition.
