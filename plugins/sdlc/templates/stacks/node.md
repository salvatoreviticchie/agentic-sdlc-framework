# Stack profile: node
Read together with generic.md. Covers JavaScript and TypeScript.

## Detect
`Stack: node` in CLAUDE.md, or package.json (with or without tsconfig.json) in the app folder.

## Options
1. **Single package**: one package.json, folders per module (for example `src/api/`, `src/web/`, `src/shared/`), one build and one test command.
2. **Monorepo with workspaces**: npm, pnpm or Yarn workspaces (optionally with Nx or Turborepo), one package.json per package, for example `packages/api`, `packages/web`, `packages/shared`.
3. **Separate services**: each package is deployed as its own service (for example an API service and a static front end on a CDN), with its own pipeline.

## Trade-offs in Node terms
- 1 is one `node_modules`, one lockfile, one `npm test`. Shared TypeScript types are a plain import. Boundaries are kept by convention or a lint rule (for example eslint import restrictions).
- 2 gives each package its own dependencies and build, and lets a front end and an API use different toolchains (for example Vite and Node). The cost: workspace configuration, TypeScript project references or path aliases, build order, and deciding whether internal packages are versioned or always used at their latest.
- 3 lets the front end and the API deploy on their own, which is often true anyway (a static site and a server). It adds CORS, API versioning between them, and two pipelines.

## Common mistakes
- Adding workspaces for one team and two folders: the configuration costs more than it saves.
- Publishing internal packages to a registry when they are only used inside the repository.
- A `shared` package that holds everything, so every change rebuilds everything.
- Different versions of the same dependency (React, TypeScript) in different workspaces.
