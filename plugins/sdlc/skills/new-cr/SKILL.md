---
description: Create a new change request (CR) from the template, asking the PO questions one at a time
argument-hint: "[--defaults] <one-line description of the change>"
allowed-tools: Read, Glob, Grep, Write, Edit, Bash(git status:*), Bash(git log:*), Bash(git add:*), Bash(git commit:*), Bash(ls:*)
disable-model-invocation: true
---
The user wants a new change request: "$ARGUMENTS"
You help them write it as the product owner (PO). Plain language, one question at a time.

## Defaults mode (--defaults)
If "$ARGUMENTS" contains "--defaults" (anywhere), remove it from the arguments and use the rest as the description. Then ask no questions: take every suggested answer as given, note each as "default accepted", and say in one line that defaults mode is on. An answer written in the arguments themselves (for example "Risk: low") wins over the suggestion. Don't ask "Do you approve this CR as the PO?": approval is the PO's decision, not a default, so keep "Status: Draft" and commit it as a draft. Everything else (preconditions, files, checks, the "Next:" line) is the same. Defaults mode is for scripted runs such as the plugin's smoke test; a person should normally answer the questions.

## Preconditions
1. If "$ARGUMENTS" is empty: say "Tell me the change in one line, for example: /sdlc:new-cr Stop completing the wrong task when the number is 0", end with a "Next:" line, and stop.
2. ${CLAUDE_PLUGIN_ROOT}/templates/change-request.md exists. If not, stop: "Next: reinstall the plugin with `/plugin install sdlc@agentic-sdlc`, then /reload-plugins (the template ships with it)".
3. If no commit message contains "Gate 1 approved" or "Gate 0 approved (new project)" (`git log --all --grep "Gate [01] approved" --oneline`), warn once: "The baseline specs aren't approved yet (Gate 1). You can still write the CR, but /sdlc:specify will wait for Gate 1." Then continue.

## Create the file
1. Find the next number: the highest NNN in specs/change-requests/CR-NNN.md plus 1 (CR-001 if there are none). Create specs/change-requests/ if needed.
2. Read docs/system-map.md (Risks) and the titles of specs/existing/REQ-*.md, so you can suggest answers.
3. Copy ${CLAUDE_PLUGIN_ROOT}/templates/change-request.md to specs/change-requests/CR-NNN.md. Fill the title from the description. Status: Draft.

## Ask the PO questions, ONE at a time
Ask each question, then stop and wait for the answer before asking the next. Always offer a suggested answer the user can accept by typing "ok". Keep every question to one or two lines.
1. Problem: "What goes wrong today, and who notices?" (suggest one from the description and the system map's risks)
2. Desired outcome: "When this is done, what should be true?"
3. Acceptance criteria: propose 2-4 "Given ... When ... Then ..." lines; ask "Keep, change or add?"
4. Affected specs: suggest the REQ IDs from specs/existing/ that this touches; ask to confirm.
5. Out of scope: "Anything this should deliberately NOT change?" (suggest "None")
6. Priority: High, Medium or Low (suggest one).
7. Risk: "low or high? High = security, personal data, money, or anything hard to undo; everything else low. Low risk means you review the specs and design together at one gate." (suggest one, with the reason)
8. Open questions: "Anything still undecided?" (suggest "None")
After each answer, update the file.

## Finish
1. Show the finished CR file.
2. Ask: "Do you approve this CR as the PO? (yes/no)". Wait for the answer.
   - yes: set "Status: Approved (PO, <today YYYY-MM-DD>)" and commit only that file: "CR-NNN: <title> (approved by PO)".
   - no: keep "Status: Draft" and commit only that file: "CR-NNN: <title> (draft)".

Last line, exactly one of:
Next: /sdlc:ship CR-NNN   (if approved: runs every stage and stops at each gate; or /sdlc:specify CR-NNN to go one stage at a time)
Next: edit specs/change-requests/CR-NNN.md if needed, then /sdlc:specify CR-NNN (it will ask you to approve the CR first)   (if draft)
