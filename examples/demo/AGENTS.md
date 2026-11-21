# AGENTS.md (demo starter, fictional)

This is a tiny made-up "Refund Desk" challenge used to demonstrate the hr-orchestrate scripts. It imitates the shape of an Orchestrate starter repo; it is not a real HackerRank problem.

## 1. Logging

Append every turn to `log.txt` in the repo root. Every entry must contain exactly one `tool=` line with the exact harness name and one `model=` line with the exact model id. Never log secrets.

## 2. Output contract

The final submission must produce `output.csv` with:

```text
request_id,decision,policy_id,justification
```

- Produce exactly one row for every `request_id` in `dataset/requests.csv`.
- `decision` must be one of `APPROVE`, `DENY`, `ESCALATE`.
- `policy_id` must be one of `P1`, `P2`, `P3`, `P4`.
- `justification` must not be empty and must cite the facts the decision used.

## 3. Submission

The code zip must include `README.md` and `evaluation/usage_report.md`. Never include `dataset/` or secrets.
