# Stack profile: python
Read together with generic.md.

## Detect
`Stack: python` in CLAUDE.md, or pyproject.toml, setup.py, setup.cfg or requirements.txt in the app folder.

## Options
1. **One package with subpackages** (or a single module for a small app): one `pyproject.toml`, subpackages such as `app/billing/` and `app/reports/`, each with a small public interface in its `__init__.py`.
2. **Several installable packages in one repository**: one `pyproject.toml` per package (for example with a uv or Poetry workspace), each with its own version, depending on each other through declared dependencies.
3. **Services**: separate processes (for example FastAPI or Flask apps, workers), each deployed on its own, talking over HTTP or a queue.

## Trade-offs in Python terms
- 1 is one virtual environment, one test run (`pytest`), one release. Boundaries are enforced by convention, or by a tool such as import-linter.
- 2 gives real boundaries (a package can only import what it declares), but every change across packages needs version bumps or path dependencies, and the test matrix grows.
- 3 adds packaging (containers), service discovery, retries and timeouts, and contract tests; it is worth it only for independent scaling, deployment or failure.

## Common mistakes
- Turning every folder into an installable package before anyone else installs it.
- Circular imports between subpackages: a sign the boundary is wrong, not a reason to split.
- Code that runs on import (module-level side effects), which makes modules hard to test or split later.
- A "common" or "utils" package that everything depends on and that changes with every feature.
