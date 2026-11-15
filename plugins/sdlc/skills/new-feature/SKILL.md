---
description: Plan a big feature of the existing app as a feature file and a sliced plan of draft CRs (up to Gate 0)
argument-hint: "[--defaults] <the feature in one line>"
allowed-tools: Read, Glob, Grep, Bash(python3 *scripts/ship.py* agent *), Bash(git status:*), Bash(git log:*), Bash(ls:*), Bash(date:*)
disable-model-invocation: true
---
The user wants a feature that is too big for one change request: "$ARGUMENTS". You plan it with them, in plain language. Explain each step in one plain sentence.

## Defaults mode (--defaults)
If "$ARGUMENTS" contains "--defaults" (anywhere), remove it from the arguments and use the rest as the feature. Then ask no questions: take every suggested answer as given, note each as "default accepted", and say in one line that defaults mode is on. An answer written in the arguments themselves (for example "Risk: low") wins over the suggestion. The planner still writes its 5 questions; record each default as the answer and go straight to the plan. Everything else (preconditions, files, checks, the "Next:" line) is the same. Defaults mode is for scripted runs such as the plugin's smoke test; a person should normally answer the questions.

## Preconditions (stop politely at the first failure, ending with a "Next:" line)
1. "$ARGUMENTS" is not empty. If it is: "Tell me the feature in one line, for example: /sdlc:new-feature due dates and reminders". Next: /sdlc:new-feature <description>.
2. The app has baseline specs: specs/existing/ has REQ-*.md files and docs/system-map.md exists, or this is a planned new project (docs/product-brief.md exists). If not: "The planner needs to know what the app does today." Next: /sdlc:explore.
3. If no commit message contains "Gate 1 approved" or "Gate 0 approved" (`git log --all --grep "Gate [01] approved" --oneline`), warn once: "The baseline isn't approved yet (Gate 1). You can plan now, but the CRs wait for Gate 1." Then continue.
4. Check the planner definition: run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" agent planner`. If "error" is set, say it plainly and stop (Next: commit the agent file, or `/plugin update sdlc@agentic-sdlc`). Note "prompt_version" and "definition".
5. The feature ID: the highest NNN in specs/features/FEAT-NNN.md plus 1 (FEAT-001 if there are none).

## 1. Interview, one question at a time
Say: "I'll ask you 5 short questions about the feature. Each has a suggested answer, based on what the app does today: type ok to accept it, ok all to accept every remaining default, or type your own answer."
Run the `sdlc:planner` agent (Agent tool, subagent_type "sdlc:planner") with:
"Mode: questions. Feature of the existing app. Feature: $ARGUMENTS. Follow your definition exactly."
It returns 5 lines "N. <question> | Default: <answer>". Ask them ONE at a time: show the question and its default, then stop and wait for the answer. Keep each answer exactly as given ("ok" means the default; note it as "default accepted"). On "ok all", accept every remaining default without asking.

## 2. Plan
Say: "The planner is now slicing the feature into small change requests, each something a user can see, riskiest first."
Run the `sdlc:planner` agent with:
"Mode: plan. Type: feature. FEAT ID: <FEAT>. Feature: $ARGUMENTS. Today: <date +%F>. Interview answers: <each question, the answer, and 'default accepted' where it was>. Follow your definition exactly."
If it returns a file as text instead of writing it, save it verbatim with the "saved verbatim by the main session" note (docs/gates.md).

## After
1. Check specs/features/<FEAT>.md exists, and specs/change-requests/CR-NNN.md for every CR in its table.
2. Show the CR table (CR, title, risk, MVP, depends on) and the MVP line, and the specs each CR changes.
3. List the open questions in the feature file, each with its default.
4. Say: "Run: planner, <prompt version>, definition <definition>."
5. Explain Gate 0 in one sentence: you approve the slicing and the MVP line before any of these CRs start; only then do they become Approved.
Nothing is committed yet; /sdlc:gate 0 commits it.

Last line, one of:
Next: read specs/features/<FEAT>.md and its CRs, then /sdlc:gate 0 <FEAT> approve "defaults accepted" (or /sdlc:gate 0 <FEAT> reject "<what to change>")
Next: first approve the baseline: read docs/system-map.md and specs/existing/, then /sdlc:gate 1 approve "<what you checked>"; then read specs/features/<FEAT>.md and its CRs and /sdlc:gate 0 <FEAT> approve "defaults accepted"   (if Gate 1 is not approved yet: /sdlc:ship refuses until it is)
