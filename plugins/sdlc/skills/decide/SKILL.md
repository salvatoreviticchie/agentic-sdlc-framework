---
description: Make an architecture decision (packaging, modularity, monolith or services) with you - a drivers interview, options in your stack's terms, and an ADR (Proposed) for the tech lead to approve
argument-hint: '"<question>" | ADR-NNN'
allowed-tools: Read, Glob, Grep, Write, Edit, Bash(git status:*), Bash(git log:*), Bash(git shortlog:*), Bash(ls:*), Bash(date:*)
disable-model-invocation: true
---
The user wants an architecture decision: "$ARGUMENTS". You work it out with them and write it down as an ADR (architecture decision record: one file per decision, with the options, the choice, and when to revisit it). Plain language, one question at a time; explain any jargon in a few words. Explain each step in one plain sentence.

## Preconditions (stop politely at the first failure, ending with a "Next:" line)
1. "$ARGUMENTS" is not empty. If it is: "Tell me the question, for example: /sdlc:decide \"one package or several?\" or /sdlc:decide \"monolith or microservices?\"". Next: /sdlc:decide "<your question>".
2. CLAUDE.md has "Project settings" (otherwise Next: /sdlc:init).
3. ${CLAUDE_PLUGIN_ROOT}/templates/adr.md and ${CLAUDE_PLUGIN_ROOT}/templates/stacks/generic.md exist. If not: Next: `/plugin update sdlc@agentic-sdlc`, then /reload-plugins.
4. If "$ARGUMENTS" is an ADR ID (ADR-NNN): docs/adr/<ADR>.md exists and its Status is "Proposed" or starts with "Rejected" (an Accepted ADR is changed by a new ADR that supersedes it: Next: /sdlc:decide "<the new question>"). This is a revision: read its Approval section (a rejection note, if any) and use its drivers as the suggested answers below. Keep its number.

## 1. Stack profile
Find the stack, in this order, and say in one line which you used and why:
1. The "Stack:" line in CLAUDE.md, if it is salesforce, python, node, java or dotnet.
2. Otherwise (generic or missing), the build files in the app folder (and the repo root), first match wins: sfdx-project.json → salesforce; pom.xml, build.gradle or build.gradle.kts → java; *.sln, *.csproj or *.fsproj → dotnet; pyproject.toml, setup.py, setup.cfg or requirements.txt → python; package.json → node. (A Salesforce project often has a package.json for its linters; sfdx-project.json wins.)
3. No build file: the most common source file type in the app folder: *.py → python; *.ts, *.tsx, *.js → node; *.java, *.kt → java; *.cs, *.fs → dotnet; *.cls, *.trigger → salesforce.
4. For a new project with no code: the "Stack:" line under "## Project settings" in docs/design/system.md.
Read ${CLAUDE_PLUGIN_ROOT}/templates/stacks/generic.md and ${CLAUDE_PLUGIN_ROOT}/templates/stacks/<stack>.md. If no profile matches, use generic.md alone and say: "No stack profile matches <stack>, so I'm using the generic profile only."
Say: "Using the <stack> profile (<reason>)."

## 2. What exists today
Read, if they exist: the "Structure" section of docs/system-map.md, docs/design/system.md, docs/product-brief.md, and every docs/adr/ADR-*.md (title and Status). If an Accepted ADR already answers this question, say so and ask "Make a new ADR that would supersede <ADR>? (yes/no)"; wait. On no, stop: Next: /sdlc:status.
Run `git shortlog -sn --all` (if there are commits) to suggest a team size.

## 3. Drivers interview, ONE question at a time
Say: "I'll ask you 6 short questions about what drives this decision. Each has a suggested answer: type ok to accept it, ok all to accept every remaining one, or type your own."
Ask each question, then stop and wait for the answer before the next. Suggest an answer from what you read in step 2 (and, for a revision, the ADR's own drivers). Keep each to one or two lines. Note "default accepted" where the user typed ok.
1. Teams: "How many people work on this, and in how many teams?"
2. Change rate: "Which parts change often, and which rarely?"
3. Independence: "Does any part need to scale, deploy or fail on its own?" (suggest "No" unless something you read says otherwise)
4. Compliance: "Any compliance or data-isolation need, e.g. data that must be kept apart?" (suggest "None")
5. Release cadence: "How often do you release, and does every part release together?"
6. Budget and operations: "What is the budget for running it, and who runs it at 3am if it breaks?"
Make no recommendation, and name no favourite option, before all 6 are answered.

## 4. Options and recommendation
Pick 2-4 options from the stack profile that fit the question, named in the stack's own terms. For each: pros, cons, cost (deployment, testing, versioning, operations) and risk.
Recommend using the default stance: one deployable unit with clear internal module boundaries (a modular monolith) first. Recommend a split into separate packages or services only when a driver the user gave justifies it, and name that driver. Say what each split would cost. Keep it in proportion to the code (generic.md, Default stance): for a small codebase, recommend keeping today's structure unless a driver says otherwise, and make growth a revisit trigger. Check the profile's "Common mistakes" against the recommendation.
Write 2-4 concrete revisit triggers: things the team could observe that would reopen the decision (for example "a second team starts owning the billing module"), each tied to a driver.

## 5. Write the ADR
1. The number: for a revision, the same one; otherwise the highest NNN in docs/adr/ADR-NNN.md plus 1 (ADR-001 if there are none). Create docs/adr/ if needed.
2. Copy ${CLAUDE_PLUGIN_ROOT}/templates/adr.md to docs/adr/ADR-NNN.md and fill every section: Status: Proposed, Date: today (`date +%F`), Question, Stack profile used (for example "generic.md + python.md"), the drivers with the answers, the options, the decision and why, consequences, revisit triggers. Supersedes: the Accepted ADR it replaces (from step 2), or "none". Superseded by: none. Leave the Approval section's placeholder line; for a revision, keep any earlier rejection line in it, add the line "Revised by /sdlc:decide, <date>." after it, and set the Status back to "Proposed" (a Rejected ADR becomes Proposed again when revised).
3. Show the decision, the drivers that decided it, and the revisit triggers (at most 8 lines).
4. Explain the ADR gate in one sentence: a tech lead or architect approves the ADR; then the architect agent must follow it in every design, and the reviewer flags any change that breaks it.
Nothing is committed yet; /sdlc:gate adr commits it.

Last line:
Next: read docs/adr/ADR-NNN.md, then /sdlc:gate adr ADR-NNN approve "<note>" (or /sdlc:gate adr ADR-NNN reject "<what to change>")
