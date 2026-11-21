# docs/CONSTANTS.md template

One row per constant, threshold, model setting, model id and ordered table in the code. Use the exact name as it appears in code so `interview_drill.py --constants` can match it.

```markdown
# Constants and their provenance

| Name | Value | Where | Provenance | Evidence / reason | If it changes |
|---|---|---|---|---|---|
| OUTPUT_COLUMNS | case_id,deletion_status,steps_json | code/contract.py:8 | SPEC | problem_statement.md:64 | contract breaks |
| SCHEMA_VERSION | 3 | code/observe.py:12 | JUDGEMENT | bumped on each schema change to invalidate cache | stale cache served |
| MODEL_EXTRACT | claude-haiku-5-5 | code/observe.py:15 | MEASURED | CR-4: same field accuracy as the larger model on 32 samples (97.1% vs 97.4%), about 1/3 the cost | accuracy / cost trade |
| temperature | 0 | code/llm.py:40 | STANDARD | repeatability | more run-to-run churn |
| MAX_RETRIES | 3 | code/llm.py:22 | BOUND | rate-limit backoff; total wait under 30 s | slower failure |
| MATCH_WINDOW_DAYS | 2 | code/rules.py:31 | JUDGEMENT | not tuned; clock skew between systems seen up to 1 day in samples | missed or false matches |
| RULES (order) | 14 rules | code/rules.py:60 | SPEC + JUDGEMENT | R1-R4 follow AGENTS.md §6.1 order; R5-R14 most specific first | test_rule_order.py |
```

Labels: SPEC (cite the line), MEASURED (cite run ids and numbers), STANDARD (conventional default), BOUND (safety limit), JUDGEMENT (reasoned, not tuned). The examples above are illustrations; never copy their numbers.
