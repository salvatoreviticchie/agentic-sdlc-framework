---
description: Plan a new project from an idea - interview, product brief, system design, and a sliced plan of draft CRs (up to Gate 0)
argument-hint: <the idea in one line>
allowed-tools: Read, Glob, Grep, Bash(python3 *scripts/ship.py agent *), Bash(git status:*), Bash(git log:*), Bash(ls:*), Bash(date:*)
disable-model-invocation: true
---
The user wants to start a new project: "$ARGUMENTS". You plan it with them, in plain language. Explain each step in one plain sentence.

## Preconditions (stop politely at the first failure, ending with a "Next:" line)
1. "$ARGUMENTS" is not empty. If it is: "Tell me the idea in one line, for example: /sdlc:new-project a command-line habit tracker in Python". Next: /sdlc:new-project <your idea>.
2. The app folder (the "App folder:" line in CLAUDE.md) is empty or holds only .gitkeep. If it has code: "This project already has code, so plan a feature of it instead." Next: /sdlc:new-feature <description>.
3. docs/product-brief.md doesn't exist. If it does: show its first lines and say the project is already planned. Next: /sdlc:status.
4. Check the planner definition: run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" agent planner`. If "error" is set, say it plainly and stop (Next: commit the agent file, or `/plugin update sdlc@agentic-sdlc`). Note "prompt_version" and "definition".
5. The feature ID is FEAT-001 (or the next free number in specs/features/).

## 1. Interview, one question at a time
Say: "I'll ask you 5 short questions. Each has a suggested answer: type ok to accept it, ok all to accept every remaining default, or type your own answer."
Run the `sdlc:planner` agent (Agent tool, subagent_type "sdlc:planner") with:
"Mode: questions. New project. Idea: $ARGUMENTS. Follow your definition exactly."
It returns 5 lines "N. <question> | Default: <answer>". Ask them ONE at a time: show the question and its default, then stop and wait for the answer. Keep each answer exactly as given ("ok" means the default; note it as "default accepted"). On "ok all", accept every remaining default without asking.

## 2. Plan
Say: "The planner is now writing the product brief, a system design with two stack options, and the plan: small change requests, each something you can see work, walking skeleton first."
Run the `sdlc:planner` agent with:
"Mode: plan. Type: new project. FEAT ID: <FEAT>. Idea: $ARGUMENTS. Today: <date +%F>. Interview answers: <each question, the answer, and 'default accepted' where it was>. Follow your definition exactly."
If it returns a file as text instead of writing it, save it verbatim with the "saved verbatim by the main session" note (docs/gates.md).

## After
1. Check these exist: docs/product-brief.md, docs/design/system.md, specs/features/<FEAT>.md, and specs/change-requests/CR-NNN.md for every CR in the feature's table. Say what is missing, if anything.
2. Show: the recommended stack in one line (and the other option), then the CR table (CR, title, risk, MVP, depends on) and the MVP line.
3. List the open questions from the feature file and docs/design/system.md, each with its default.
4. Say: "Run: planner, <prompt version>, definition <definition>."
5. Explain Gate 0 in one sentence: you approve the plan (the slicing, the MVP line and the stack) before any CR starts; only then do its CRs become Approved. A new project has no code to explore, so Gate 0 takes the place of Gate 1.
Nothing is committed yet; /sdlc:gate 0 commits it.

Last line:
Next: read docs/product-brief.md, docs/design/system.md and specs/features/<FEAT>.md, then /sdlc:gate 0 <FEAT> approve "defaults accepted" (or /sdlc:gate 0 <FEAT> reject "<what to change>")
