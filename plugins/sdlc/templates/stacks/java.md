# Stack profile: java
Draft profile, not yet tested on a real project. Corrections welcome.

Read together with generic.md. Covers Java and other JVM languages built with Maven or Gradle.

## Detect
`Stack: java` in CLAUDE.md, or pom.xml, build.gradle or build.gradle.kts in the app folder.

## Options
1. **Modular monolith in one module**: one Maven module or Gradle project, packages per business module (for example `com.acme.billing`), boundaries checked with ArchUnit or Spring Modulith, or with JPMS (module-info.java).
2. **Multi-module build**: one parent pom (or Gradle settings with several subprojects), one module per business area, still built and deployed as one application.
3. **Microservices**: each module is its own deployable (for example a Spring Boot service), with its own database and pipeline.

## Trade-offs in Java terms
- 1 is one build, one artifact, one test run. Package-private classes and an architecture test keep the boundaries honest.
- 2 makes the compiler enforce dependencies between modules (a module can only use what it depends on), at the cost of a longer build, a parent pom or version catalog to keep in step, and more build configuration.
- 3 gives independent deployment and scaling, at the cost of network calls instead of method calls, distributed transactions (or sagas), service discovery, tracing, and one database per service.

## Common mistakes
- One Maven module per technical layer (`-dao`, `-service`, `-web`) instead of per business area.
- Microservices sharing one database schema.
- Synchronous chains of service calls, so one slow service makes every service slow.
- Snapshot dependencies between modules or services that make builds unrepeatable.
