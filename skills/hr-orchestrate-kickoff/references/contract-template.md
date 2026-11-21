# docs/CONTRACT.md template

Copy into the challenge repo as `docs/CONTRACT.md`. Cite a source for every line (`problem_statement.md:42`, `AGENTS.md §6.1`).

```markdown
# Contract: <challenge name>, <edition>

## Task in one paragraph
<what the agent decides, for whom, from which inputs>

## Inputs
| File | Rows | Key columns | Notes | Source |
|---|---|---|---|---|

## Output
- Path: <e.g. output.csv at repo root>
- Header, exact order: `<col1,col2,...>`
- One row per: <id column> in <eval input file> (<N> rows)
- Per column:
| Column | Type | Allowed values / format | Empty allowed? | Source |
|---|---|---|---|---|
- Serialization: <JSON key order, quoting, date format, decimal places, empty-string conventions>

## Decision rules stated by the problem
1. <rule> (source)

## Evidence and data rules
- <e.g. only participant-facing files; never cite evidence after audit_at> (source)

## Required files and submission
| Artifact | Contents | Source |
|---|---|---|
| code.zip | ... | |
| output.csv | ... | |
| transcript | log.txt at <path> | |
| other | e.g. evaluation/evaluation_report.md, evaluation/usage_report.md, agent-trace.zip | |
- Must NOT be in code.zip: <dataset, venvs, secrets, ...>
- Submission URL (if AGENTS.md specifies one, copy it exactly): <url>

## Logging
- Path: <...>   Format: <session start / per-turn fields>   tool=<...>   model=<...>

## Constraints
- Runtime, language, network, determinism, secrets (source)

## Worked examples
| Sample id | Expected output | Why (domain reasoning) |
|---|---|---|

## Assumptions (ambiguities and the reading we chose)
| # | Ambiguity | Our reading | Why | Confirmed by participant? |
|---|---|---|---|---|

## Archetype
<A-E from archetypes.md, or "none fits" + why>
```
