---
description: Check the setup, explain the pipeline, and say what to run first
allowed-tools: Read, Glob, Grep, Bash(python3 *scripts/ship.py agent *), Bash(git status:*), Bash(git log:*), Bash(git rev-parse:*), Bash(ls:*)
disable-model-invocation: true
---
You are helping a first-time user. Be friendly and short. Use plain language; explain any jargon in a few words.

## 1. Check the setup
Check each item and show the result as a checklist (✅ / ❌ with one line of explanation each):
1. This is a git repository with at least one commit (`git rev-parse HEAD`).
2. CLAUDE.md has a "Project settings" section with the three lines "App folder:", "Stack:" and "Test command:". Show their values.
3. The app folder exists (Glob it; count the files). An empty folder (or only .gitkeep) is fine: it means a new project.
4. The agents: for each of planner, explorer, spec-writer, architect, developer (and developer-salesforce if Stack is salesforce), reviewer, run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" agent <name>` and show its "prompt_version" ("error" set = ❌). They come with the sdlc plugin, as sdlc:<name>.
5. The plugin's templates exist: ${CLAUDE_PLUGIN_ROOT}/templates/change-request.md.
6. docs/gates.md exists.

If anything is ❌, say exactly how to fix it, end with a "Next:" line that names the fix, and stop. The usual fixes: items 2, 3 or 6 → Next: /sdlc:init (it sets up the folders, docs/gates.md and CLAUDE.md, asking first); item 1 → Next: /sdlc:init (it offers git init); items 4 or 5 → reinstall the plugin: `/plugin install sdlc@agentic-sdlc`, then /reload-plugins.

## 2. Explain the pipeline (exactly 5 short lines)
Explain the flow like this, in your own words:
1. **Explore**: an agent reads your code and writes what it does today as specs (requirements) in specs/existing/. You check them at Gate 1.
2. **Change request**: you describe one change you want (a CR) with /sdlc:new-cr; it is approved by you, the product owner (PO). A new project (/sdlc:new-project) or a big feature (/sdlc:new-feature) is first planned as several small CRs, approved at Gate 0.
3. **Specify, design**: agents turn the CR into updated specs (Gate 2) and a design note (Gate 3).
4. **Build**: a developer agent implements the design on a branch, with tests.
5. **Review and merge**: a reviewer agent checks it against the specs; you approve at Gate 4 and it is merged.
Add one line: "Agents do the work; you decide at every gate. /sdlc:status shows where each CR is."

## 3. Say what to run first
Work out where the project is:
- The app folder is empty and there is no docs/product-brief.md → "Next: /sdlc:new-project <your idea in one line>" (the planner interviews you and slices the idea into small CRs; e.g. /sdlc:new-project a command-line habit tracker in Python)
- docs/product-brief.md exists → "Next: /sdlc:status" (a new project; Gate 0 replaces Gate 1)
- No specs in specs/existing/ (no REQ-*.md files) → "Next: /sdlc:explore"
- Specs exist but no commit message contains "Gate 1 approved" (`git log --all --grep "Gate 1 approved" --oneline`) → "Next: read docs/system-map.md and the specs in specs/existing/, then type /sdlc:gate 1 approve \"<what you checked>\" (or /sdlc:gate 1 reject \"<what is wrong>\")"
- Gate 1 approved → "Next: /sdlc:status to see your change requests, /sdlc:new-cr <one-line description> to start one, or /sdlc:new-feature <description> for something bigger than one CR"

End with that "Next:" line as the very last line.
