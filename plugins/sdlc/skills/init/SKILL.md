---
description: Set up this project for the sdlc pipeline - folders, docs/gates.md, the Project settings in CLAUDE.md (asks first) - and say what to run next
allowed-tools: Read, Glob, Grep, Bash(python3 *scripts/init_project.py*), Bash(git status:*), Bash(git log:*), Bash(git add:*), Bash(git commit:*), Bash(git rev-parse:*), Bash(ls:*)
argument-hint: "[--defaults]"
disable-model-invocation: true
---
Set up this project for the sdlc pipeline. The user may be new to it: be friendly and short, use plain language, and explain each step in one plain sentence.
Running this twice must change nothing: the script creates only what is missing.

The script is `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/init_project.py"` (below: `init_project.py`). Run it from the project folder. It prints JSON.

## Defaults mode (--defaults)
If "$ARGUMENTS" contains "--defaults", ask no questions: answer yes to git init (question 1), ok to every suggestion (questions 2-4; an empty app folder gets `echo "no tests yet"`), yes to the CLAUDE.md question (append), and yes to committing the code (question 6). Say in one line that defaults mode is on. Everything else is the same. It is for scripted runs such as the plugin's smoke test.

## 1. Look
Run `init_project.py check`.
- If it exits with "this is the agentic-sdlc framework repository itself", say so and stop. Next: open Claude Code in your own project folder, then /sdlc:init
- If "nothing_to_do" is true: say "This project is already set up. Nothing changed." Show the three settings from "settings" (App folder, Stack, Test command). If "gates_md" says it differs from the plugin, add one line: "Your docs/gates.md differs from the plugin's version and was left as it is; to take the plugin's version, delete docs/gates.md and run /sdlc:init again." Then go to 5. Next.

## 2. Ask, ONE question at a time (skip a question whose answer CLAUDE.md already has under "settings")
Each question offers the suggested answer from "suggested"; the user types ok to accept it or their own answer. Wait for each answer before the next.
1. Git (only if "git"."is_repo" is false): "This folder isn't a git repository yet. The pipeline records every decision as a commit, so it needs one. Create it now (git init)? (yes/no)". On no: stop. Next: run `git init`, then /sdlc:init
2. App folder: "Where is your code? Suggested: <app_folder>/ (<files> files in it). Type ok, or the folder name, e.g. src." Explain: it is the only folder the developer agent may change. If the user has no code yet, say: "Leave it empty for a new project; /sdlc:new-project plans one."
   If the answer differs from the suggestion, run `init_project.py check` again after step 3 is answered and use its new suggestions for the test command.
3. Stack: "Which stack is this? Suggested: <suggested stack> (<stack_reason>). Type ok, or one of: generic, salesforce, java, node, dotnet, python." Explain in one line: the stack picks the developer agent (salesforce → the Salesforce developer agent and Apex tests; every other stack → the general developer agent) and the stack profile /sdlc:decide and the architect use for packaging options (plugin templates/stacks/); generic means any language, with no stack-specific options. If the user picks java or dotnet, add: "That profile is a draft, not yet tested on a real project." Accept only those six values; for anything else (e.g. go), suggest generic and say a profile can be added (docs/how-to.md, "Add a stack profile").
4. Test command: "How do you run all the tests, from this folder? Suggested: `<test_command>`." If there is no suggestion: an empty app folder → offer "none yet" (write `echo "no tests yet"`; /sdlc:new-project sets the real one at Gate 0); otherwise ask for it. It must exit with 0 when all tests pass.
5. CLAUDE.md, only if "claude_md" is "exists without project settings": show the section that will be added (from ${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md, with the answers filled in) and ask: "Your CLAUDE.md exists. Add this 'Project settings' section at the end of it? Nothing else in it changes. (yes/no)". yes → `--claude-md append`; no → `--claude-md skip`, and say the commands need those three lines, so add them yourself before /sdlc:explore. If "claude_md" is "missing": a new CLAUDE.md is created (`--claude-md create`); say so, no question.
6. Uncommitted code, only if "app_folder"."uncommitted_count" > 0, or if "git"."is_repo" was false and "app_folder"."files" > 0 (a new repository: none of the code is committed): "Your code in <app>/ isn't committed yet (<count> files). The agents work on branches, so it must be. Commit it together with the setup? (yes/no)".

## 3. Apply
Run `init_project.py apply --app <folder> --stack <generic|salesforce|java|node|dotnet|python> --test-command "<command>" --claude-md <create|append|skip>` (add `--git-init` if the user said yes in question 1). Quote the test command exactly.
Show the "changed" list as a short checklist, one line each, with what it is for:
- specs/..., docs/..., runs/ (.gitkeep): the folders for specs, change requests, features, designs, build reports and cost logs
- docs/gates.md: the rules for each gate (who approves what, and how it is recorded)
- CLAUDE.md: the Project settings every agent reads
- .gitignore: keeps full agent run logs out of git (only runs/costs.csv is kept)
- .claude/settings.json: lets the agents write specs/ and docs/ without asking each time; changes to your code still ask

## 4. Commit
If "changed" is not empty (or the user said yes in question 6): `git add` exactly the paths in "changed" (and `<app>` if the user said yes in question 6), then commit "Set up the sdlc pipeline (/sdlc:init)". Show `git log --oneline -1`. Say why in one line: the pipeline starts from a clean, committed state.
If "changed" is empty and there is nothing to commit, say "Nothing changed."
If the user said no in question 6, say: "Commit your code before /sdlc:explore (git add <app> && git commit -m 'Add the app')."
If "git"."has_main_branch" is false and the repo has commits on another branch (e.g. master): warn once that the pipeline merges into a branch called main (`git branch -m <branch> main` renames it).

## 5. Next
Explain the pipeline in two lines: agents explore, specify, design, build and review; you approve at each gate, and every reply ends with a "Next:" line to follow. Then end with exactly one "Next:" line, the very last line:
- The app folder has code → Next: /sdlc:explore   (an agent reads your code and writes what it does today as specs; you check them at Gate 1)
- The app folder is empty → Next: /sdlc:new-project <your idea in one line>   (e.g. /sdlc:new-project a command-line habit tracker in Python)
- The project was already set up → Next: /sdlc:status
