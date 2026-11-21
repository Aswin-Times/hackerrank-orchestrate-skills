# Constants and their provenance (demo)

Deliberately incomplete so `interview_drill.py --constants` shows what is MISSING.

| Name | Value | Where | Provenance | Evidence / reason | If it changes |
|---|---|---|---|---|---|
| UNOPENED_DAYS | 30 | code/rules.py:8 | SPEC | problem_statement.md P1 | P1 approvals shift |
| OPENED_DAYS | 14 | code/rules.py:9 | SPEC | problem_statement.md P2 | P2 approvals shift |
| OPENED_AMOUNT_LIMIT | 200 | code/rules.py:10 | SPEC | problem_statement.md P2, inclusive | more escalations |
| RULE_ORDER | P4, P1, P2, P3 | code/rules.py:14 | SPEC | "P4 is checked first" | fraud cases approved |
