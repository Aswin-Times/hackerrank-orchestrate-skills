# Demo: Refund Desk (fictional mini-challenge)

A tiny made-up challenge shaped like an Orchestrate starter repo, so you can try every hr-orchestrate script in a minute without an API key. The screenshots in the main README were produced from these files by `scripts/make_screenshots.py`.

| Path | What it is |
|---|---|
| `AGENTS.md`, `problem_statement.md` | The fake starter contract |
| `dataset/` | Sample inputs with expected outputs, 10 evaluation inputs, blank template |
| `code/` | A rules-only demo agent (`python code/main.py` writes `output.csv`) |
| `runs/baseline_sample.csv` | A sample run with a bug (gold exception missing) |
| `runs/candidate_sample.csv` | The same run after the fix |
| `runs/output_bad.csv` | A broken output for preflight to catch |
| `log.txt`, `log_bad.txt` | A valid transcript and one with typical mistakes |
| `docs/CONSTANTS.md` | Deliberately incomplete, so the drill shows MISSING items |
| `evaluation/usage.jsonl` | Illustrative token log for the usage report |

## Try it (from this folder)

```sh
S=../../skills
python code/main.py
python $S/hr-orchestrate-kickoff/scripts/contract_extract.py .
python $S/hr-orchestrate-kickoff/scripts/check_log.py log_bad.txt --expect-tool "Claude Code" --expect-model claude-opus-5-5
python $S/hr-orchestrate-test-fix/scripts/preflight.py runs/output_bad.csv --template dataset/output.csv --inputs dataset/requests.csv --id-col request_id --enum "decision=APPROVE|DENY|ESCALATE" --all-required
python $S/hr-orchestrate-test-fix/scripts/score_sample.py runs/baseline_sample.csv dataset/sample_output.csv --id-col request_id --confusion decision
python $S/hr-orchestrate-test-fix/scripts/rerun_diff.py runs/baseline_sample.csv runs/candidate_sample.csv --id-col request_id --expected dataset/sample_output.csv
python $S/hr-orchestrate-interview/scripts/interview_drill.py code --constants docs/CONSTANTS.md --no-general
python $S/hr-orchestrate-build/scripts/usage_report.py evaluation/usage.jsonl --run-id final --price claude-haiku-5-5=1:5 --price claude-sonnet-5-5=3:15 --price-source "example prices, not real"
```

The prices above are placeholders for the demo. In a real challenge, take them from the provider's current pricing page.
