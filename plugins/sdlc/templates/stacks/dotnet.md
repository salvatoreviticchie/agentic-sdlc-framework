# Stack profile: dotnet
Draft profile, not yet tested on a real project. Corrections welcome.

Read together with generic.md. Covers C# and F# on .NET.

## Detect
`Stack: dotnet` in CLAUDE.md, or a *.sln, *.csproj or *.fsproj file in the app folder.

## Options
1. **Projects in one solution**: one .sln with one project per business module (or one project with folders), referenced with ProjectReference, deployed as one application.
2. **NuGet packages**: modules built and versioned as NuGet packages (from an internal feed), consumed with PackageReference by one or more applications.
3. **Services**: each module is its own deployable (for example an ASP.NET Core service), with its own pipeline and data store.

## Trade-offs in .NET terms
- 1 is one `dotnet build`, one `dotnet test`. Project references make dependencies explicit and the compiler blocks the ones you didn't declare; `internal` keeps a module's details private.
- 2 gives independent versioning and reuse across products, at the cost of a package feed, version bumps for every change, and diamond-dependency problems between package versions.
- 3 gives independent deployment and scaling, at the cost of HTTP or messaging between parts, configuration per service, and distributed tracing.

## Common mistakes
- Packaging modules as NuGet packages when only one application uses them: every change becomes a publish-and-update cycle.
- Projects per technical layer (`.Data`, `.Business`, `.Web`) instead of per business area.
- Circular project references worked around with a shared "Common" project that grows forever.
- Services that share one database.
