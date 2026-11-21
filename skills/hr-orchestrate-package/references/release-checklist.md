# Release checklist

Tick each item from evidence produced now (a command output or a file you just opened), not from memory.

## Output CSV
- [ ] Exact header and column order from the template
- [ ] Exactly one row per evaluation input id; no duplicates, no extras
- [ ] Only allowed values in enum columns; JSON columns parse; serialization matches the sample (key order, separators, empty strings)
- [ ] Justification columns cite real evidence ids; 10 random rows spot-checked
- [ ] Produced by the frozen code in one documented run (run id recorded)

## Code zip
- [ ] README: what it does, setup, environment variables (names only), exact run command, where output goes, how to run evaluation
- [ ] Runnable from a clean checkout by following the README
- [ ] Prompts and configuration included; design reasons in module docstrings and constant comments
- [ ] Required files present (October 2026: `evaluation/evaluation_report.md`, `evaluation/usage_report.md`)
- [ ] Tests included and passing
- [ ] Excluded: dataset, virtualenvs, caches, nested archives, `.env`, keys, real personal data, organizer-only files
- [ ] No hardcoded labels or sample ids (`coupling_scan.py` clean or explained)
- [ ] Dependencies pinned (requirements.txt / package-lock)

## Transcript
- [ ] Log at the path AGENTS.md specifies; every entry in the required format
- [ ] `tool=` and `model=` exact in every entry (when required)
- [ ] No secrets; prompts verbatim with `[REDACTED]` where needed
- [ ] The log shows planning, specific constraints, debugging with real errors, verification, and safety decisions

## Evaluation and usage reports
- [ ] Metrics computed by `evaluation/evaluate.py` from a recorded run; numbers match the report
- [ ] At least the required number of custom cases, with results
- [ ] Failures found and fixes, with before/after numbers
- [ ] Usage report from the final run: providers, models, calls, input/output tokens, totals, per-request averages, estimated cost, price source and date

## Interview
- [ ] CONSTANTS.md covers every constant (`interview_drill.py --strict`)
- [ ] INTERVIEW.md: nine topics, verified numbers, three honest limits
- [ ] One full mock interview done; weakest answers re-drilled

## Submission
- [ ] `package.py` READY; MANIFEST hashes recorded in STATUS.md
- [ ] Agent trace staged and reviewed (if requested)
- [ ] Uploaded by the participant with time to spare; confirmation saved
