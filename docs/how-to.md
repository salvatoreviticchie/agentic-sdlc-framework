# How to use the sdlc plugin

This guide is for someone using the plugin for the first time. Every command is written exactly as you type it.
Lines that start with `/` are typed into Claude Code. Other commands are typed into your terminal.

**The idea in one paragraph.** Agents do the work: they read your code, write specs, design a change, build it with tests and review it.
You decide: after each stage there is a *gate*, where you approve, change or reject what the agent did.
Every reply ends with a **Next:** line, the command to type next. If you only remember one thing, remember that: follow the Next: line.

Contents: [Install](#install-and-update) · [A: one change](#walkthrough-a-an-existing-codebase-one-change) · [B: a big feature](#walkthrough-b-a-big-feature) · [C: a new project](#walkthrough-c-a-new-project) · [Gates](#approve-change-or-reject-at-each-gate) · [Architecture decisions](#architecture-decisions) · [Risk tiers](#risk-tiers) · [Cost](#cost-and-context-tips) · [Add a stack profile](#add-a-stack-profile) · [Known limitations](#known-limitations-120) · [Troubleshooting](#troubleshooting) · [FAQ](#faq)

## Install and update

You need [Claude Code](https://claude.com/claude-code), git and Python 3.

**Install.** Open Claude Code (`claude` in a terminal) and type these two commands:

```
/plugin marketplace add salvatoreviticchie/agentic-sdlc-framework
/plugin install sdlc@agentic-sdlc
```

The first adds this repository as a *marketplace* (a list of plugins). The second installs the plugin from it.
If the commands don't show up when you type `/sdlc`, type `/reload-plugins`.

**Set up a project.** Open Claude Code in your project folder and type:

```
/sdlc:init
```

It asks where your code is, whether it is a Salesforce project and how you run the tests, one question at a time, each with a suggested answer (type `ok` to accept it).
It creates the folders the pipeline uses, `docs/gates.md` (the rules for each gate) and a "Project settings" section in `CLAUDE.md`.
If you already have a `CLAUDE.md`, it asks before adding to it. Then it commits the setup.
Running it again changes nothing, so it is safe to run whenever you're unsure.

**Update.** In your terminal, type:

```
claude plugin marketplace update agentic-sdlc
claude plugin update sdlc@agentic-sdlc
```

Then restart Claude Code: type `/restart` in a running session (or `/exit`, then `claude`).

The update changes the agents and commands, never your project files. Your `docs/gates.md` is kept as it is. To take the new version, delete `docs/gates.md` and type `/sdlc:init`.

## Walkthrough A: an existing codebase, one change

This uses the small example app that comes with the repository, so you can try everything in about 15 minutes. For your own code, skip step 1.

**1. Make a practice project** (in your terminal):

```
mkdir ~/code/my-first-sdlc && cd ~/code/my-first-sdlc
git init -b main
git clone https://github.com/salvatoreviticchie/agentic-sdlc-framework.git /tmp/agentic-sdlc-framework
cp -R /tmp/agentic-sdlc-framework/examples/tiny-app app
claude
```

When Claude Code asks whether you trust this folder, say yes.

**2. Set up.**

```
/sdlc:init
```

Type `ok` to each suggestion: app folder `app`, not Salesforce, test command `python3 -m unittest discover -s app -v`.
Say `yes` when it offers to commit your code with the setup.

**3. Explore.**

```
/sdlc:explore
```

The explorer agent reads every file in `app/` and writes:
- `docs/system-map.md`: what the code is made of, and a numbered list of **risks** (things that look wrong);
- `specs/existing/REQ-001.md` and up: one *spec* (a requirement) per thing a user can do, describing what the code does **today**, bad parts included;
- `docs/coverage.md`: which files it read.

**4. Gate 1: check the specs.** Read `docs/system-map.md` and a few specs. You are checking one thing: do they describe what the code does today? (Not what it should do; that comes next.)

```
/sdlc:gate 1 approve "Specs match the code; the done 0 bug is in REQ-003"
```

**5. Describe one change.**

```
/sdlc:new-cr Refuse task numbers below 1
```

This writes a *change request* (CR) with you. It asks 8 short questions, one at a time: the problem, the outcome, the acceptance criteria ("Given ... When ... Then ..."), the specs it touches, what's out of scope, priority, risk and open questions. Each has a suggestion; type `ok` to accept it.
At the end it asks whether you approve the CR. Say `yes`.

**6. Ship it.**

```
/sdlc:ship CR-001
```

`/sdlc:ship` runs the stages one after another (specify, design, build, review) and stops when a gate is due. It never pushes or merges. Each stop prints:
- **Stopped at:** which gate;
- **Review:** the files to read;
- **Open questions**, each with the agent's proposed default;
- **Approve all defaults:** the exact command to accept them all;
- **Next:** what to type.

**7. The gates.** If you chose `low` risk in step 5 (the usual answer for this change), there are two stops:

- **Gates 2+3 together** (specs and design). Read `specs/proposed/CR-001/` and `docs/design/CR-001.md`, then:
  ```
  /sdlc:gate 2 CR-001 approve "defaults accepted"
  /sdlc:ship CR-001
  ```
- **Gate 4** (the code). `/sdlc:ship` built the change on a branch `cr-001`, ran your tests and had the reviewer check it. Read `docs/review/CR-001-review.md` and the changes (`git diff main...cr-001`), then:
  ```
  /sdlc:gate 4 CR-001 approve "Reviewed the diff; tests pass"
  ```
  This records the approval and merges `cr-001` into `main` on your machine.

A high-risk CR stops three times instead: Gate 2 (specs), Gate 3 (design) and Gate 4. See [Risk tiers](#risk-tiers).

**8. Pull request (optional).** If you use GitHub, open the pull request at the Gate 4 stop, **before** you approve. The stop prints the command to copy, like this:

```
git push -u origin cr-001 && gh pr create --base main --head cr-001 --title "CR-001: Refuse task numbers below 1" --body-file docs/review/CR-001-review.md
```

When the PR is approved, type `/sdlc:gate 4 CR-001 approve "PR approved"`, then `git push` to send the merge to GitHub.

**9. See where everything is.**

```
/sdlc:status
```

## Walkthrough B: a big feature

Use this when a change is too big for one CR, such as "due dates" for the to-do app. You need the explore step (Walkthrough A, steps 2 to 4) done first.

**1. Plan it.**

```
/sdlc:new-feature due dates
```

**2. The planner interview.** The planner agent asks you 5 questions, one at a time, each with a suggested answer based on what the app does today:

1. Who is it for?
2. What are the main journeys (3-5, most important first)?
3. Constraints (platform, language, data, rules)?
4. Non-goals: what should it deliberately not do, for now?
5. What does "useful" mean: the smallest result worth using?

Type `ok` to accept a suggestion, `ok all` to accept every remaining one, or type your own answer. Question 5 matters most: it decides the MVP.

**3. Read the slicing table.** The planner writes `specs/features/FEAT-001.md` and one draft CR per row of this table:

| CR | Title | Value (what a user can see) | Risk | Depends on | MVP | Status |
|---|---|---|---|---|---|---|
| CR-001 | Add a task with a due date and see it in the list | `add ... --due` stores a date that `list` shows | low | - | yes | Draft |
| CR-002 | Flag overdue tasks in the list | `list` marks tasks whose date has passed | low | CR-001 | yes | Draft |
| CR-003 | Set, change or remove a task's due date | a new `due` command | low | CR-001 | no | Draft |

Check four things:
- **Each row is something a user can see.** A row like "data model" or "tests" is a bad slice; reject it.
- **Each row is small**: about a day of work, 2-4 acceptance criteria.
- **The order**: dependencies first, then the riskiest (what you're least sure about), so you learn early.
- **The MVP line**: the rows marked `yes` are the smallest set worth using. Usually 2 to 4.

Under the table are the open questions, each with a default.

**4. Gate 0: approve the plan.**

```
/sdlc:gate 0 FEAT-001 approve "defaults accepted"
```

Only now are the CRs approved. If Gate 1 isn't approved yet, approve it first (`/sdlc:gate 1 approve "..."`); `/sdlc:ship` refuses until it is.

**5. Ship the feature.**

```
/sdlc:ship FEAT-001
```

It ships the CRs one at a time, in table order, with the same gate stops as in Walkthrough A. After each gate, type `/sdlc:ship FEAT-001` again; it picks up where it stopped.

**6. Re-plan after each merge.** After a CR is merged, the Gate 4 stop suggests:

```
/sdlc:replan FEAT-001
```

The planner reads what the merged CR taught (its build report, review and your decisions) and updates the CRs that haven't started. It never changes a CR that is being built or is done.
A CR it changes or adds goes back to Draft and needs Gate 0 again (`/sdlc:gate 0 FEAT-001 approve "..."`); unchanged CRs keep their approval.

**7. Check progress.**

```
/sdlc:status
```

It shows each feature as "2 of 4 CRs merged, MVP 2 of 2", with one line per CR and the single next command.

## Walkthrough C: a new project

Use this when there is no code yet.

**1. Set up an empty project.**

```
mkdir ~/code/habit-tracker && cd ~/code/habit-tracker
git init -b main
claude
```

```
/sdlc:init
```

Accept `app` as the app folder (it stays empty for now) and "none yet" for the test command.

**2. Plan the project.**

```
/sdlc:new-project a command-line habit tracker in Python
```

The planner asks the same 5 questions as in Walkthrough B. Then it writes:
- `docs/product-brief.md`: who it's for, the journeys, the non-goals, what "useful" means;
- `docs/design/system.md`: **two stack options** and a recommendation, the folder structure, the test approach, and the exact "Project settings" lines (app folder, stack, test command);
- `specs/features/FEAT-001.md` and its draft CRs.

**3. The walking skeleton.** The first CR is always a *walking skeleton*: the thinnest version that runs end to end, such as one command that works, with one test and the test command wired up.
It looks too small on purpose. It proves the stack, the folders and the tests work before anything else is built on them.

**4. The stack decision.** The *stack* is the language, framework and tools. Decide it before Gate 0:
- The best moment is the interview: name your stack in question 3 (constraints), for example "Python 3.12, standard library only".
- At Gate 0, read both options in `docs/design/system.md`. Approving Gate 0 approves the recommended one and copies its "Project settings" lines into `CLAUDE.md`.
- If you want the other option, don't approve. Nothing is committed yet: delete `docs/product-brief.md`, `docs/design/system.md`, `specs/features/FEAT-001.md` and the new files in `specs/change-requests/`, then run `/sdlc:new-project` again and name the stack in question 3.

**5. Gate 0, then ship.** A new project has no code to explore, so Gate 0 takes the place of Gate 1:

```
/sdlc:gate 0 FEAT-001 approve "Python stack, defaults accepted"
/sdlc:ship FEAT-001
```

From here it is Walkthrough B, step 5.

## Approve, change or reject at each gate

At every gate you do one of three things:
- **Approve**: you accept the work, with a short note saying what you checked. `"defaults accepted"` in the note accepts every open question's proposed default, and records each one under "PO decisions" in the CR.
- **Change**: you want something different, but the work is mostly right. Write your answer under `## PO decisions` at the end of the CR file (`specs/change-requests/CR-NNN.md`), for example `- 2026-11-15: Q2: show "Task 0 does not exist" and exit 1`. Then approve with your own note. Don't edit the agent's files yourself.
- **Reject**: send it back with a note saying what to change. The agent runs again and reads your note.

| Gate | What you check | Approve | Change | Reject |
|---|---|---|---|---|
| 0 Plan | the slices, the order, the MVP line (new project: the stack) | `/sdlc:gate 0 FEAT-001 approve "defaults accepted"` | add answers under "PO decisions" in the feature file, then approve | `/sdlc:gate 0 FEAT-001 reject "Merge CR-003 into CR-001"`, then `/sdlc:replan FEAT-001` |
| 1 Explore | the specs describe today's code, bad parts included | `/sdlc:gate 1 approve "Specs match the code"` | (no change step: reject instead) | `/sdlc:gate 1 reject "REQ-004 misses the clear-done command"`, then `/sdlc:explore` |
| 2 Specify | the new specs are complete, and each criterion is testable | `/sdlc:gate 2 CR-001 approve "defaults accepted"` | answer the open questions under "PO decisions" in the CR, then `/sdlc:gate 2 CR-001 approve "Q1 answered"` | `/sdlc:gate 2 CR-001 reject "Criterion 3 can't be tested"`, then `/sdlc:ship CR-001` |
| 3 Design | the chosen option, the list of files to change, the test plan | `/sdlc:gate 3 CR-001 approve "Option A, smallest change"` | write the decision under "PO decisions", then approve | `/sdlc:gate 3 CR-001 reject "Use option B: no new file format"`, then `/sdlc:ship CR-001` |
| 4 Review | the diff, the test results, the review's findings, each *deviation* (a place where the developer did something the design didn't say) | `/sdlc:gate 4 CR-001 approve "All deviations accepted"` | decide each deviation under "PO decisions": `- 2026-11-15: D-01: accept` (or reject, or backlog), then approve | `/sdlc:gate 4 CR-001 reject "D-02: keep the old error message"`, then `/sdlc:ship CR-001` |

Low-risk CRs take Gates 2 and 3 as one: `/sdlc:gate 2 CR-001 approve "..."` records both.
If a gate has open questions you haven't answered, it lists them and asks "Approve anyway? (yes/no)".
Every decision is a commit, such as `CR-001: Gate 2 approved`. The exact records are in `docs/gates.md`.

## Architecture decisions

Some questions are bigger than one CR: one package or several? A monolith or services? `/sdlc:decide` answers one with you and writes it down as an *ADR* (architecture decision record: one file per decision, with the options, the choice, and when to revisit it).

```
/sdlc:decide "one package or several?"
```

1. It picks the *stack profile* (the packaging options for your language) from the `Stack:` line in `CLAUDE.md` or your build files, and says which one it used.
2. It asks 6 questions, one at a time, each with a suggested answer: teams, what changes often, what must scale or deploy on its own, compliance, release cadence, and who runs it at 3am. It recommends nothing until you have answered.
3. It starts from one deployable unit with clear internal modules, and recommends a split only when one of your answers justifies it, saying what the split costs.
4. It writes `docs/adr/ADR-001.md` with Status Proposed, including the triggers that would make you revisit it.

A tech lead or architect then decides:

```
/sdlc:gate adr ADR-001 approve "One team, one release: one package with clear modules"
```

The ADR becomes Accepted, in a commit `ADR-001: approved (ADR gate)`. From then on the architect follows it in every design, and the reviewer reports any change that breaks it as Major. To change your mind later, run `/sdlc:decide` again: the new ADR supersedes the old one when it is approved. A reject sets its Status to Rejected, with the date and your note, and it binds nobody; `/sdlc:decide ADR-001` revises it with your note and makes it Proposed again.

For existing code, `/sdlc:explore` adds a "Structure" section to `docs/system-map.md` (modules, dependencies, files that change together, suggested boundaries), which `/sdlc:decide` reads. For a new project, the planner writes the stack and structure ADRs for you.

## Risk tiers

Every CR has `Risk: low` or `Risk: high`; `/sdlc:new-cr` and the planner suggest one, and you decide.
**High** means security, personal data, money, or anything hard to undo: you approve the specs (Gate 2), the design (Gate 3) and the code (Gate 4) separately.
**Low** is everything else: you approve the specs and the design together at one gate, then the code at Gate 4. A CR with no Risk line counts as high.

## Cost and context tips

- **Type `/clear` between stages.** Every command reads what it needs from the files, so nothing is lost. A fresh context is cheaper and makes fewer mistakes. Each `/sdlc:ship` stop reminds you.
- **Agents run in their own context.** `/sdlc:ship` runs each agent as a separate session, so the agent's reading doesn't fill yours.
- **Budgets.** `CLAUDE.md` has a line `- Budgets (USD per stage): specify 1, design 1, build 5, review 1`. `/sdlc:ship` stops when a stage's runs for one CR have used up its budget. Raise a number to allow more.
- **See what it cost.** Every agent run is a row in `runs/costs.csv`. Ask Claude "run the sdlc cost report" for a table per CR and stage. `docs/build/CR-NNN-timeline.md` shows each stage's time and cost and how long each gate waited for you.
- **The plugin itself** adds about 750 tokens to every session (one short line per command and agent). A command's full instructions load only when you type it.
- **On a subscription**, the costs are Claude Code's estimates at API prices, not what you pay. Read them as relative sizes.
- **Build big changes in slices.** When the architect lists "Slices:", the developer builds one slice at a time, and `/sdlc:ship` runs the tests after each one.

More in [cost-and-context.md](cost-and-context.md).

## Add a stack profile

A stack profile is one short Markdown file in `plugins/sdlc/templates/stacks/`, for example `go.md`, that tells `/sdlc:decide`, the planner and the architect the packaging options for that stack. `generic.md` is always read first; the profile adds the stack's own terms.

The plugin has six: `generic`, `salesforce`, `java`, `node`, `dotnet` and `python`; `/sdlc:init` offers all six and writes your choice to the `Stack:` line in `CLAUDE.md`. `java.md` and `dotnet.md` are draft profiles, not yet tested on a real project. Corrections welcome.

1. Copy `python.md` as a starting point and keep its four sections: **Detect** (the `Stack:` value and the build files that identify the stack), **Options** (from least to most split, in the stack's own words), **Trade-offs in <stack> terms** (deployment, testing, versioning, operations), and **Common mistakes**.
2. Keep it under about 40 lines, and write only facts you can check in the stack's own documentation.
3. Add the build file to the detection list in `plugins/sdlc/skills/decide/SKILL.md` (step 1).
4. Try it: set `Stack: <name>` in a test project's `CLAUDE.md`, run `/sdlc:decide "one package or several?"`, and check it says "Using the <name> profile".
5. Open a pull request.

## Known limitations (1.2.0)

- The reviewer's check for ADR violations (a change that breaks an Accepted ADR is reported as Major) is not yet tested end to end.
- The ADR reject path (`/sdlc:gate adr ADR-NNN reject "<note>"`, Status Rejected, then `/sdlc:decide ADR-NNN` to revise it) is not yet tested end to end.
- The Java and .NET stack profiles (`java.md`, `dotnet.md`) are drafts, not yet tested on a real project. Corrections welcome.

## Troubleshooting

**An agent is not found**, for example `--agent 'sdlc:spec-writer' not found. Available agents: ...` during `/sdlc:ship`, or a stage saying the `sdlc:explorer` agent doesn't exist.
The plugin's agents load when a session starts. Type `/reload-plugins`. If it is still not found, type `/restart` (or `/exit`, then `claude` again).
Still missing? Type `/plugin`, open the **Installed** tab and check that `sdlc` is installed and enabled for this project.

**`/sdlc:...` commands don't appear.** Same fix: `/reload-plugins`, then check `/plugin`. The commands always start with `/sdlc:`; the old names without the prefix (`/ship`, `/gate`) don't exist.

**A gate is refused.** The gate checks its preconditions first and says which one failed, followed by a Next: line that fixes it. The usual ones:
- "Fix the Blockers first": the reviewer's verdict is "Not ready". Type `/sdlc:ship CR-001` to let the developer fix them; the review runs again.
- "Already approved": nothing to do. Type `/sdlc:status`.
- An earlier gate isn't approved (for example, Gate 3 needs Gate 2). Approve that one first.
- "Uncommitted changes": you changed tracked files. Commit or stash them (`git stash`), then try again.
- "Approve anyway? (yes/no)": open questions or deviations have no decision yet. Answer `no`, add the decisions under "PO decisions" in the CR, and approve again. Or put `defaults accepted` in your note.

**A budget stop.** `/sdlc:ship` says something like "The build budget is used up: $5.02 of $5.00". The agent stopped, and its work so far is kept. Raise that stage's number on the `Budgets` line in `CLAUDE.md`, commit it, and type `/sdlc:ship CR-001` again. A budget stop often means the CR is too big; consider splitting it.

**Permission prompts.** Claude Code asks before an agent changes a file or runs a command. `/sdlc:init` lets the agents write `specs/` and `docs/` without asking (in `.claude/settings.json`). Changes to your code still ask, on purpose.
- If a prompt repeats for something you trust, choose "Yes, and don't ask again", or add a rule with `/permissions`.
- If `/sdlc:ship` stops with "Ignoring 4 permissions.allow entries from .claude/settings.json: this workspace has not been trusted", open Claude Code in the project once with `claude` and accept the trust question. Agent runs inside `/sdlc:ship` can't ask you anything, so they rely on those rules.

**"The pipeline merges into a branch called main".** The pipeline expects your main branch to be called `main`. To rename it, type `git branch -m master main` in the terminal.

**Files you never edit by hand.** The commands write these, and the gates check them:
- `specs/existing/`: changes only when a CR is merged at Gate 4;
- `docs/traceability.md`: the Proposed → Approved → Merged status of each spec;
- the gate lines: the first line of `docs/design/CR-NNN.md`, the last line of `specs/proposed/CR-NNN/summary.md`, and the line under "## Verdict" in `docs/review/CR-NNN-review.md`;
- `docs/build/CR-NNN-timeline.md` and `runs/costs.csv`;
- any agent output before its gate (`specs/proposed/`, `docs/design/`, `docs/build/`, `docs/review/`, `specs/features/`). To change it, write your decision under "PO decisions" in the CR, or reject the gate.

You may edit: a CR before it is approved, the "PO decisions" section of a CR or feature file at any time, the "Project settings" in `CLAUDE.md`, and `docs/gates.md` if your team agrees different rules.

## FAQ

**What can the agents do, and what can't they?**

| Agent | Writes | Never |
|---|---|---|
| planner | the product brief, the system design, feature files, draft CRs | writes code, or changes a CR that is being built or is done |
| explorer | `docs/system-map.md`, `docs/coverage.md`, `specs/existing/` | changes your code |
| spec-writer | `specs/proposed/CR-NNN/`, `docs/traceability.md` | writes code or changes `specs/existing/` |
| architect | `docs/design/CR-NNN.md` | writes code or changes specs |
| developer | code and tests in the app folder, on branch `cr-nnn`, and the build report | commits on main, pushes, or changes specs or the design |
| developer-salesforce | the same, plus checks against your Salesforce org | the same, plus destructive org actions |
| reviewer | `docs/review/CR-NNN-review.md` | changes code, specs or the design |

No agent pushes, opens a pull request or merges. Only you approve a gate, and only `/sdlc:gate 4` merges, on your machine.
The "Never" column is written in each agent's instructions, and the tools each agent gets limit what it can do (the planner, explorer, spec-writer, architect and reviewer can't run commands). Instructions are not a hard control, so the gates are where you check.

**Where are decisions recorded?**
- **Git commits**: every gate is a commit named after it, e.g. `CR-001: Gate 4 approved`. `git log --oneline --grep Gate` lists them.
- **"PO decisions"** in each CR and feature file: your answers to open questions and deviations, with dates.
- **`docs/traceability.md`**: which spec each CR changed, and its status.
- **`docs/build/CR-NNN-timeline.md`**: every stage and gate, with times, costs and how long each gate waited.
- **`runs/costs.csv`**: every agent run, with the agent's prompt version and definition.

**How do I use it with a team?**
- **Install it for the whole project.** In the project folder, type in your terminal:
  ```
  claude plugin marketplace add salvatoreviticchie/agentic-sdlc-framework --scope project
  claude plugin install sdlc@agentic-sdlc --scope project
  ```
  Then commit `.claude/settings.json`. Teammates who open the project are asked to install the same plugin.
- **Agree on roles.** The product owner (PO) takes Gates 0, 1 and 2. A tech lead joins Gate 3. Gate 4 can be your normal pull-request review: open the PR at the Gate 4 stop, then the PO runs `/sdlc:gate 4` once the PR is approved.
- **One person ships a given CR at a time**, and pushes its branch (`git push -u origin cr-001`) so others can see it. Different CRs can move in parallel.
- **Everything is in git**, so teammates see decisions with `git pull` and `/sdlc:status`.
- So far the pipeline has been tested end to end by one person, not yet by a team.
