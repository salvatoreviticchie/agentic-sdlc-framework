# Releasing the sdlc plugin

The checklist for a new plugin version, for contributors. Do the steps in order; stop at the first one that fails and fix it first.

## 1. Run the free self-check

```
python3 plugins/sdlc/tests/check.py
```

It costs nothing and takes a few seconds: no AI, no network. It runs `claude plugin validate` on the plugin and the marketplace, checks every skill (frontmatter, user-invoked only, a "Next:" line at the end), that every `/sdlc:<name>` mentioned is a real command, that every script, template and stack profile referenced exists, that every agent has a "Prompt version:" line and `plugin.json` has a version, and that the published files have no private links, emails or private pilot names. It prints PASS or FAIL per check and exits with 1 on any failure.

## 2. Run the live smoke test

```
python3 plugins/sdlc/tests/smoke.py            # total cap 5 USD; --budget 8 to raise it, --keep to inspect the folder
```

It costs money (Claude Code's estimate at API prices, a few USD) and takes 15-40 minutes. Commit your agent changes first: agents run only from a committed definition. In a temporary folder outside the repo, it runs the whole pipeline headless on `examples/tiny-app` with this checkout as the plugin (`--plugin-dir`): `/sdlc:init --defaults`, `/sdlc:explore`, Gate 1, `/sdlc:decide --defaults`, the ADR gate, `/sdlc:new-cr --defaults` with Risk: low, the CR approval, `/sdlc:ship` to the combined gate, Gates 2+3, and `/sdlc:ship` to Gate 4. After each step it checks the files and statuses that step must leave (specs, system map, ADR Accepted, proposed specs, design note, timeline, a code change with tests that pass, a review verdict). At the end it prints each step's result, cost and duration, and deletes the folder.

`WARN` lines are tool calls a skill doesn't allow, which were denied because there is no person to ask. They don't fail the test, but each one is a permission prompt a real user would see, so fix the skill's `allowed-tools` if it should be allowed.

## 3. Raise the version

Raise `version` in `plugins/sdlc/.claude-plugin/plugin.json` (for example 1.2.0 to 1.3.0). Installed copies update only when the version changes. If you changed an agent's behaviour, raise its `Prompt version:` line too. Commit on your branch, then merge it into main.

## 4. Sync to the public repository

The public repository is `salvatoreviticchie/agentic-sdlc-framework`. Copy only these paths into it, replacing what is there:

- `plugins/` and `.claude-plugin/` (without `__pycache__/`)
- `examples/`
- `README.md`, without the "`docs/`, `specs/` and `pilots/`" line under "Repository layout" (those folders are not published)
- `docs/how-to.md`, `docs/lessons.md`, `docs/cost-and-context.md` and `docs/releasing.md`

Then, in the public repository:

1. Run `python3 plugins/sdlc/tests/check.py` there too. It must pass: no links to the private repository, no email addresses, no private pilot names.
2. Read `git diff`: only the changes you meant to release.
3. Commit with your GitHub no-reply email, as "Release X.Y.Z: <what changed>".

## 5. Push

Push main in both repositories, the public one last.

## 6. Update your own install

```
claude plugin marketplace update agentic-sdlc
claude plugin update sdlc@agentic-sdlc
```

Then type `/reload-plugins` in Claude Code (or restart it), and check the version with `/plugin`.
