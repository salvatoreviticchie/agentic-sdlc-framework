# ADR-NNN: <the decision, as a short statement, e.g. "One package with internal modules">
<!-- Status is one of: Proposed | Accepted (<date>) | Rejected (<date>): <note> | Superseded by ADR-MMM (<date>). Only /sdlc:decide and /sdlc:gate adr change it. -->
Status: Proposed
Date: <YYYY-MM-DD>
Question: <the question as asked, e.g. "one package or several?">
Stack profile used: <generic.md + python.md | generic.md only (no profile matched)>
Supersedes: <ADR-MMM | none>
Superseded by: <ADR-MMM | none>

## Context
<3-5 lines: what the system is today (from docs/system-map.md "Structure", or docs/design/system.md for a new project), and why the question comes up now>

## Decision drivers
The answers given in /sdlc:decide ("default accepted" where the proposed default was taken):
- Teams: <team size and how many teams>
- Change rate: <which parts change often, which rarely>
- Independence: <which parts must scale, deploy or fail independently>
- Compliance and data isolation: <needs, or "none">
- Release cadence: <e.g. monthly>
- Budget and operations: <budget, operational skills, who runs it at 3am>

## Options
### Option A: <name in the stack's own terms>
- Pros: ...
- Cons: ...
- Cost: <deployment, testing, versioning and operations cost, S/M/L>
- Risk: ...
### Option B: <name>
- Pros: ...
- Cons: ...
- Cost: ...
- Risk: ...
<2-4 options in all>

## Decision
<the option chosen, and why, naming the drivers that decide it. Default stance: one deployable unit with clear internal module boundaries; split only when a named driver justifies it.>

## Consequences
- <what becomes easier>
- <what becomes harder, and what it costs from now on>
- <what the next CRs must follow, e.g. "module X never imports module Y">

## What would make us revisit this
Concrete triggers, each something you can observe:
- <e.g. "a second team starts working on the billing module">
- <e.g. "the reporting module needs a different release cadence from the rest">

## Approval
<filled in by /sdlc:gate adr ADR-NNN approve|reject "<note>">
