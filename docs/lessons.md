# Lessons

Short rules learned from running this pipeline end to end on a real change.

1. **Give every loop a stopping rule.** An agent asked to "resolve open questions" will keep finding new ones. After a fixed number of runs (we use 3), it lists the remaining questions with proposed defaults and stops; a human closes the gate by accepting or overriding them.

2. **Implied isn't answered.** A decision that "follows from" another decision is not a decision. Every open question gets an explicit answer, or an explicit deferral to a named later stage, written in the change request. Agents fill gaps with guesses that look like answers.

3. **Prompt rules aren't controls.** "Never do X" in a prompt is a request, not a guarantee. Anything that matters for security or data correctness is enforced in code on the server (for example, an action checks a server-side flag instead of trusting what the model says happened). Test the case where the model claims the check passed when it didn't.

4. **Blocked models improvise.** When an agent can't do the step you asked for (a tool is blocked, a file can't be written, the design is incomplete), it will often do something else that looks like progress. Tell every agent what to do when blocked: stop and report, or return the output as text. Never "work around it".

5. **AI judges can be fooled.** An LLM that grades another LLM's output can be wrong in systematic ways: it may not know today's date, may reward confident wording, and can be told by the output itself that a check passed. Read its reasons, not only its score, and back important criteria with deterministic tests or manual checks.

6. **Build in slices.** Split a change into slices of related acceptance criteria. Build, test, report and get decisions on each slice before starting the next. Big-bang builds produce reports too large to review and deviations nobody can trace.

7. **Re-test the neighbours.** After a fix, especially a prompt fix, re-run the changed case plus every case on the same feature, topic or language, not only the one that failed. Fixes to one case regularly break the case next to it.
