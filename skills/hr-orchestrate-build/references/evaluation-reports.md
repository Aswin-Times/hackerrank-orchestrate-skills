# Evaluation reports

October 2026 required both files inside `code.zip` (check the current starter: paths and contents change; one README also mentioned `code/evaluation/`, so resolve conflicts by asking or by following `AGENTS.md`). Even when not required, an evaluation folder raises the code score and gives the interview real numbers.

## evaluation/evaluation_report.md

Required content in October 2026:
- case-level accuracy for the main decision column;
- step-level and field-level accuracy (for structured or JSON columns);
- sequence accuracy (for ordered outputs);
- at least three evaluation cases created by the participant;
- failures found and improvements made.

Suggested structure:

```markdown
# Evaluation report

## Setup
Run id, date, command, model(s), sample size, code commit.

## Results on the public sample (n = 32)
| Metric | Value | How computed |
|---|---|---|
| Case-level accuracy (deletion_status) | 29/32 (90.6%) | exact match |
| Step-level accuracy | ... | step matched on (system_id, resource_id, operation) |
| Field-level accuracy | ... | per field over matched steps |
| Sequence accuracy | ... | order of matched steps equal |

## Custom evaluation cases
| Case | What it tests | Expected | Result |
|---|---|---|---|
| C1 | injection text in request | decision unchanged | pass |
| C2 | restore after delete | INCOMPLETE + restore risk | pass |
| C3 | evidence captured after audit time | not cited | pass |

## Failures found and fixes
| # | Failure (rows) | Cause | Fix | Effect (before -> after) |
|---|---|---|---|---|

## Known limits
...

## Reproduce
`python evaluation/evaluate.py --run runs/sample_<run_id>.csv`
```

Numbers must come from a recorded run. Label anything else UNKNOWN.

## evaluation/usage_report.md

Required content in October 2026, for the final full-dataset run that produced `output.csv`:
- model providers and model names;
- model-call counts;
- input and output tokens;
- total and average tokens per request;
- estimated total and per-request cost;
- per-model and overall totals when several models are used.

Generate it with `scripts/usage_report.py` from `evaluation/usage.jsonl`, filtered to the final run id. If the final run was served partly from the local cache, report both views: tokens attributable to producing the output (original token counts of every call used) and tokens billed during the final run. State price per million tokens, the date and where the prices came from. No API keys or sensitive configuration in the file.
