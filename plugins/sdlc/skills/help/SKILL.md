---
description: List the /sdlc: commands, explain one command, or answer a question from the how-to guide and the gates
argument-hint: [command name | "question"]
allowed-tools: Read, Glob, Grep, WebFetch(domain:raw.githubusercontent.com), Bash(ls:*)
disable-model-invocation: true
---
Help with: "$ARGUMENTS". Read only: change nothing. Be friendly and short, in plain language; explain any jargon in a few words.

The guide is https://github.com/salvatoreviticchie/agentic-sdlc-framework/blob/main/docs/how-to.md. To read it, use `${CLAUDE_PLUGIN_ROOT}/../../docs/how-to.md` if it exists (a checkout of the repo), otherwise fetch https://raw.githubusercontent.com/salvatoreviticchie/agentic-sdlc-framework/main/docs/how-to.md.
The gates are in `${CLAUDE_PLUGIN_ROOT}/templates/gates.md` (plugins/sdlc/templates/gates.md; `/sdlc:init` copies it to the project's docs/gates.md).
A command's own instructions are in `${CLAUDE_PLUGIN_ROOT}/skills/<name>/SKILL.md`.

Work out which case applies:
- "$ARGUMENTS" is empty → case 1.
- "$ARGUMENTS" is one word that names a command, with or without "/sdlc:" or "/" (init, start, explore, new-project, new-feature, replan, new-cr, ship, specify, design, build, review, gate, status, help) → case 2.
- Anything else → case 3. A single word that is close to a command name (e.g. "gates", "shipping") is case 2 for that command.

## Case 1: the command list
Print this, as it is:

**Getting started**
| Command | What it does |
|---|---|
| `/sdlc:init` | Sets up the folders, `docs/gates.md` and Project settings in `CLAUDE.md` (asks first) |
| `/sdlc:start` | Checks the setup, explains the pipeline and says what to run first |
| `/sdlc:explore` | Reads your existing code and writes what it does today as specs |
| `/sdlc:help [command \| "question"]` | This list, one command explained, or an answer from the guide |

**New project**
| Command | What it does |
|---|---|
| `/sdlc:new-project <idea>` | Interviews you, then plans the idea as small change requests (CRs) |

**Big feature**
| Command | What it does |
|---|---|
| `/sdlc:new-feature <description>` | Plans a change too big for one CR as several small CRs |
| `/sdlc:replan FEAT-NNN` | Updates a feature's remaining CRs after one is merged |

**Single change**
| Command | What it does |
|---|---|
| `/sdlc:new-cr <description>` | Writes a change request with you, one question at a time |

**Running the pipeline**
| Command | What it does |
|---|---|
| `/sdlc:ship CR-NNN` | Runs every stage on its own and stops at each gate |
| `/sdlc:ship FEAT-NNN` | Ships a feature's CRs in order, with the same stops |
| `/sdlc:specify CR-NNN` | Runs only the spec-writer |
| `/sdlc:design CR-NNN` | Runs only the architect |
| `/sdlc:build CR-NNN [slice]` | Runs only the developer, on branch `cr-nnn` |
| `/sdlc:review CR-NNN` | Runs only the reviewer |

**Gates** (where you decide)
| Command | What it does |
|---|---|
| `/sdlc:gate <0-4> [FEAT-NNN \| CR-NNN] approve\|reject "<note>"` | Records your approval or rejection, as a commit |

**Status and cost**
| Command | What it does |
|---|---|
| `/sdlc:status` | Shows every CR, its stage and the next command |

Cost: every agent run is a row in `runs/costs.csv`; ask "run the sdlc cost report" for a table per CR and stage. `/sdlc:ship` stops when a stage's budget in `CLAUDE.md` is used up.

Then: "Not sure where you are? Type /sdlc:status."
Then: "The full guide: https://github.com/salvatoreviticchie/agentic-sdlc-framework/blob/main/docs/how-to.md"
Last line: "Next: /sdlc:status"

## Case 2: one command
Read the command's SKILL.md (and grep the guide for "/sdlc:<name>"), then answer with these five short parts, a few lines each:
1. **What it does**: one or two sentences.
2. **When to use it**: the situation, and when to use another command instead (e.g. /sdlc:ship instead of the single stages).
3. **What it needs first**: what must exist or be approved before it runs (e.g. an approved CR, Gate 2 approved, the app folder set in CLAUDE.md).
4. **Example**: one exact command line with a realistic ID or description, and one line on what you see.
5. **What comes next**: the gate or command that usually follows.
Take every fact from those files; don't invent options. Last line: "Next: " and the example command.

## Case 3: a question
Answer from docs/how-to.md and plugins/sdlc/templates/gates.md only. Grep them for the question's key words, read only the matching sections, and answer in a few lines, with the exact commands to type.
Cite each section you used, as a link: "From [how-to.md: <section heading>](https://github.com/salvatoreviticchie/agentic-sdlc-framework/blob/main/docs/how-to.md#<anchor>)" or "From [gates.md: <section heading>](https://github.com/salvatoreviticchie/agentic-sdlc-framework/blob/main/plugins/sdlc/templates/gates.md#<anchor>)". The anchor is the heading in lower case, spaces as "-", punctuation dropped.
If neither file answers it, say so plainly, suggest the closest section, and don't guess.
Last line: "Next: " and the command the answer points to, or /sdlc:status.
