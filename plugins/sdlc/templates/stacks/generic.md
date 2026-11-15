# Stack profile: generic
Read by /sdlc:decide, the planner and the architect for every stack, together with the matching stack profile (if any).

## Detect
The default. Used alone when no other profile matches.

## Options (from least to most split)
1. **One deployable unit, one codebase**: everything builds, tests and ships together.
2. **Modular monolith**: one deployable unit, with internal modules that have clear boundaries (each module owns its data and exposes a small interface; no reaching into another module's internals).
3. **Several packages or libraries, one deployable**: modules become separately built and versioned units, still shipped together.
4. **Separate services**: each part deploys, scales and fails on its own, and talks to the others over the network.

## Default stance
Start at 1 or 2. Move right only when a named driver justifies it:
- a separate team needs to release on its own schedule;
- a part must scale, deploy or fail independently;
- compliance or data isolation requires a hard boundary;
- a part is reused by another product.
"It feels cleaner" or "we might need it later" is not a driver.

Keep it in proportion to the code. In a small codebase (one or a few files, a few hundred lines), the module boundaries can be classes and functions inside one file: keep the structure as it is, and make "the file grows past a few hundred lines" or "two parts change for different reasons" a revisit trigger. Restructuring code nobody asked to change is a cost too.

## What each split costs
- **Deployment**: more pipelines, a deployment order, and environments to keep in step.
- **Testing**: contract tests between the parts, and end-to-end tests that need all of them running.
- **Versioning**: every interface between parts needs a version and a compatibility rule; breaking changes need a migration plan.
- **Operations**: more things to monitor, log, secure and wake someone up for at 3am; network failures between parts become your problem.

## Common mistakes
- Splitting by technical layer (UI, API, data) instead of by business capability.
- Splitting before the boundaries are known: wrong boundaries are far more expensive to fix across packages or services than inside one codebase.
- A "distributed monolith": separate services that must all be deployed together.
- Shared database tables across modules or services, so the boundary exists only on paper.
