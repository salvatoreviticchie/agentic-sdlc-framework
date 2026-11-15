---
description: Run the explorer agent on the app folder to write the system map and baseline specs
allowed-tools: Read, Glob, Grep, Bash(python3 *scripts/ship.py* agent *), Bash(python3 *scripts/ship.py* cochange*), Bash(git status:*), Bash(git log:*), Bash(ls:*)
disable-model-invocation: true
---
You are running stage 1 of the pipeline (Explore) for the user. Explain each step in one plain sentence as you go.

## Preconditions (stop politely at the first one that fails, with a "Next:" line that fixes it)
1. CLAUDE.md has "App folder:" under "Project settings", and that folder exists and has files. If not: "Next: copy your code into <folder>, or set App folder: in CLAUDE.md".
2. Check the explorer definition: run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" agent explorer`. If "error" is set, say it plainly and stop (Next: commit the agent file, or `/plugin update sdlc@agentic-sdlc`). Note "prompt_version" and "definition". Our gate rule: an agent runs only from a committed definition.
3. If specs/existing/ already has REQ-*.md files, or docs/system-map.md exists: tell the user the explorer will overwrite them, and ask "Run the explorer again and overwrite them? (yes/no)". Stop and wait for the answer. Continue only on yes.

## Run
Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ship.py" cochange` to get the files that change together (from git history; its "note" says if there is none). Say in one line how many commits it read.
Say: "The explorer agent is now reading every file in <app folder>. It writes a system map, one spec per capability, and a coverage list. This takes a few minutes."
Run the `sdlc:explorer` agent (Agent tool, subagent_type "sdlc:explorer") with this prompt:
"Explore the app folder named in CLAUDE.md. Follow your definition exactly. Co-change list for the Structure section: <the JSON from cochange>"

If the agent returns a file's content as text instead of writing it, save the text verbatim to that file and add a first line: "> Note: saved verbatim by the main session from the explorer's returned text, <date>, per docs/gates.md."

## After the run
1. Check that docs/system-map.md, docs/coverage.md and at least one specs/existing/REQ-*.md exist. If not, say what is missing and stop.
2. Show a short summary: the number of specs and their titles, the top 3 risks from the system map (one line each), and the suggested natural boundaries from its Structure section (one line; they are suggestions: /sdlc:decide "<question>" makes a decision).
3. Say: "Run: explorer, <prompt version>, definition <definition>."
4. Explain Gate 1 in one sentence: "Gate 1 is where you, the PO, confirm the specs describe what the code does today, including the bad parts."
5. Nothing is committed yet; /sdlc:gate 1 commits the files.

Last line, exactly:
Next: read docs/system-map.md and the files in specs/existing/, then type /sdlc:gate 1 approve "<what you checked>" (or /sdlc:gate 1 reject "<what is wrong>")
