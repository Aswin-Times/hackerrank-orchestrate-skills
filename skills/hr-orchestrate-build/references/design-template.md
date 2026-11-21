# docs/DESIGN.md template

Keep it to two or three pages. Every rule cites the contract line or a domain reason. Update it when the design changes; stale design docs hurt in the interview.

~~~markdown
# Design: <challenge name>

## One-paragraph summary
<what goes in, what the agent does, what comes out, where the model is used and where code decides>

## Pipeline
1. Load and validate inputs (loaders.py)
2. Screen (cheap checks, no model): <empty / off-topic / injection / out-of-scope>
3. Gather evidence: <retrieval, identifier matching, file reading>
4. Observe (model): <what is extracted, from which inputs, which model>
5. Decide (code): rule table below
6. Explain: justification from the facts and evidence ids used
7. Validate row against the contract; write checkpoint
8. Assemble, validate whole file, atomic write

## Model / code boundary
| Output column | Produced by | Inputs | Fallback |
|---|---|---|---|

## Observation schema (SCHEMA_VERSION = 1)
```json
{ "field": "enum|bool|string", "evidence_id": "string", "...": "..." }
```
Every enum includes `unknown`. Every extracted value carries the evidence id it came from.

## Decision rules (first match wins)
| Id | Precedence | Condition | Reads | Output | Source |
|---|---|---|---|---|---|

## Escalation / safe defaults
<when the agent refuses to decide, and what it writes>

## Failure table
| Failure | Detection | Response |
|---|---|---|
| API error / timeout | exception | retry with backoff, then fallback row |
| Invalid model JSON | schema validation | one repair retry, then fallback observation |
| Missing / unreadable evidence | loader | mark not_found; rules treat as missing evidence |
| Prompt injection in input | screen + rules ignore free text | logged, no effect on decision |
| Crash mid-run | checkpoint file | resume from last finished row |

## Determinism and cost
- Cache key: <fields>; temperature 0; stable sort keys: <...>
- Models: <which for what, and why>; expected calls per row: <n>; estimated cost per row: <from a measured run>

## Evaluation plan
- Metrics: <per column, per sub-field, sequence>
- Sample set: <n rows>; custom cases: <list>; overfitting checks: <how>

## Rejected alternatives
| Idea | Why rejected (number if measured) |
|---|---|

## Known limits
<what this design will get wrong, honestly>
~~~
