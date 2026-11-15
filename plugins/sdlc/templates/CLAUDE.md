## Project settings
The sdlc plugin's commands and agents read these lines. Change the values for your project.
- App folder: {app}
- Stack: {stack}
- Test command: {test_command}
- Budgets (USD per stage): specify 1, design 1, build 5, review 1

About these settings:
- App folder: the only folder the developer agent may change. The other agents only read it.
- Stack: one of generic, salesforce, java, node, dotnet, python. "salesforce" uses the sdlc:developer-salesforce agent; every other stack uses sdlc:developer. /sdlc:decide, the planner and the architect read the matching stack profile (plugin templates/stacks/); "generic" means any language, with no stack-specific options. The java and dotnet profiles are drafts.
- Test command: runs from the repo root and must exit with 0 when all tests pass.
- Budgets: /sdlc:ship stops when a stage's agent runs for one CR have cost more than this (Claude Code's estimate at API prices, from runs/costs.csv). Build is one budget for all slices.
- The pipeline's rules are in docs/gates.md. Don't edit agent output before its gate, or the records the commands keep (specs/existing/, docs/traceability.md, gate lines, timelines, runs/costs.csv).
