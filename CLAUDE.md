# Project notes for Claude

- The target codebase lives in app/. Only the developer agent changes it, on a cr-NNN branch.
- Follow docs/gates.md: agents run only from committed definitions, and gates pass only on agent output.
- Large reports (build reports in particular) can be tens of thousands of tokens. Don't read them whole: Grep them, or Read only the line ranges you need with `offset`/`limit`.
- Run agents through scripts/run_agent.py when you want the run's cost logged in runs/costs.csv.
