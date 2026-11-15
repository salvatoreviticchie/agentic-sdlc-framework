# Stack profile: salesforce
Read together with generic.md. Covers Salesforce DX projects (Apex, LWC, metadata).

## Detect
`Stack: salesforce` in CLAUDE.md, or sfdx-project.json in the app folder or the repo root.

## Options
1. **Org-based codebase (happy soup)**: one source folder (for example `force-app/`) deployed to the org as a whole; the org is the source of truth for what is installed.
2. **One org codebase with folder-per-domain**: still deployed as one unit, but organised into package directories in sfdx-project.json (for example `sales/`, `service/`, `shared/`), as a first step towards packages.
3. **Unlocked packages per domain**: each domain is an unlocked package with its own version (`sf package version create`), installed in dependency order; packages can be namespaced or not.
4. **Org-dependent unlocked packages**: packages that may depend on metadata already in the org without declaring it; easier to carve out of an existing org, but dependencies are checked only at install time.

## Trade-offs in Salesforce terms
- **Dependency order**: unlocked packages must form a graph without cycles (for example `shared` ← `sales` ← `service`); a package can't reference metadata in a package installed after it. Untangling a happy-soup org into that order is the main cost.
- **Namespaces**: a namespace is fixed when the package is created and prefixes every API name (`ns__Field__c`); changing it later means a new package. Most internal packages use no namespace. Packages in the same namespace can share `@namespaceAccessible` Apex.
- **Versioning**: every package version is immutable and has a version number; promoting a version to released needs 75% Apex test coverage for that package alone. Dependent packages pin a version (or LATEST) in sfdx-project.json.
- **Deployment**: an org-based codebase deploys with `sf project deploy`; packages install with `sf package install`, version by version, in dependency order, per org. Metadata deleted from a package version is deprecated, not always removed, in the org.
- **Teams**: packages give each team a clear owner and release unit; a single org codebase lets two teams overwrite each other's metadata unless they agree on folders and a merge process.
- **Testing**: each package is validated in a scratch org with only its dependencies, which proves the boundaries are real but needs scratch-org definitions and seed data per package.

## Common mistakes
- Creating one package per team before the domains are untangled: cycles between packages block every version.
- A namespace on internal packages without a reason (it complicates every reference from outside).
- Moving shared objects (Account, Contact) or shared fields into a domain package instead of a base package that everything depends on.
- Org-dependent packages used forever: they hide the dependencies the packaging was meant to make visible.
- Forgetting per-package test coverage until the first promote fails.
