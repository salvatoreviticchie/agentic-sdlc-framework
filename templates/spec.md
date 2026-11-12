# Spec templates

Two forms. The explorer writes the baseline form into specs/existing/.
The spec-writer writes the proposed form into specs/proposed/CR-NNN/.
After Gate 4 the proposed spec replaces the baseline one in specs/existing/.

## Baseline form (specs/existing/REQ-NNN.md)

```markdown
# REQ-NNN: <title>
Purpose: <one line>
Actor: <end user | internal user | admin | system>
Acceptance criteria:
- Given ... When ... Then ...
Evidence:
- <path from repo root>
Assumptions:
- [ASSUMPTION] <what you inferred and why>   (or "- None")
```

## Proposed form (specs/proposed/CR-NNN/REQ-XXX.md)

```markdown
# REQ-XXX: <title>
Version: <old version + 1, or 1 for new specs>
Changed by: CR-NNN
Purpose: <one line>
Actor: <end user | internal user | admin | system>
Acceptance criteria:
- Given ... When ... Then ...   (mark each one [NEW], [CHANGED] or [UNCHANGED])
Removed criteria:
- <criteria from the old version that no longer hold, with the reason> (or "- None")
Evidence:
- <path from repo root, for unchanged behaviour>
Open questions:
- <anything the PO or the architect must decide> (or "- None")
```

Rules
- Describe behaviour, not implementation.
- Write every criterion so a tester could check it without reading the code.
- One spec per capability, not one per class or file.
