---
name: hr-orchestrate-test-fix
description: HackerRank Orchestrate test and fix phase - validate output.csv against the contract, score the run on the public sample (per column, step-level, field-level, sequence), classify wrong rows into error classes, trace one row end to end, check overfitting and determinism, build custom evaluation cases, and fix rows in one-change loops with a change record and a whole-output diff that gives a KEEP/REVERT verdict. Use once the agent writes a full CSV, whenever rows are wrong or weakly justified, and before filling evaluation_report.md.
---

# Orchestrate test and fix (hours 8-18)

Input: a run that writes a valid CSV. Output: fewer wrong rows, stable output, a filled `evaluation/evaluation_report.md`, and `docs/experiments.md` with every change and its measured effect. `$T` means this skill's directory.

## Part A. Find what is wrong

### A1. Contract check every run
```
python $T/scripts/preflight.py output.csv --template <template csv> --inputs <eval input csv> --id-col <id> \
  --enum "<col>=A|B|C" --json-col <json col> --all-required --sample <sample expected csv>
```
Any FAIL blocks everything else. Read the WARNs: a JSON key order that differs from the sample, or values the sample never uses, are often silent score losses.

### A2. Score on the sample
```
python $T/scripts/score_sample.py runs/sample_<run>.csv <sample expected csv> --id-col <id> \
  --json-col <json col> --step-key <fields that identify a step> --confusion <main col> --show 3
```
Record the numbers in `docs/STATUS.md` as MEASURED with the run id.

### A3. Classify wrong rows
Put every wrong row into an error class in `docs/experiments.md`:

| Class | Rows | First wrong stage | Suspected cause | Ceiling (rows a perfect fix gains) |
|---|---|---|---|---|

Stages: load → screen → evidence gathering → observation (model) → rule → explanation → serialization. Attack the class with the largest ceiling first. If a class has zero headroom, do not build for it.

### A4. Trace one row end to end
Run `python code/main.py --ids <id>` and read its checkpoint record (rule ids fired, evidence ids opened, observation JSON from the cache). Find the first stage whose output is wrong. Fix that stage, not a later one. Quote the evidence in the log: the row id, the wrong value, the stage, the cause.

### A5. Overfitting checks
- `python $T/scripts/coupling_scan.py code/ --sample <sample inputs> --sample <sample expected> --allow-from problem_statement.md`: any sample id or long sample value in code is a red flag.
- Every rule and constant must have a reason that is not "it fixed sample row X". If you cannot state the domain reason, remove it.
- Hold-out check: develop on part of the sample, measure on the rest. A big gap means overfitting.
- Look at the distribution of outputs on the evaluation set (counts per enum value). A distribution far from the sample's, without a reason, is a warning.

### A6. Determinism and noise
Run the sample twice with no code change and compare:
```
python $T/scripts/rerun_diff.py runs/a.csv runs/b.csv --id-col <id>
```
Offline (cache-served) re-runs must show 0 changed rows. Online re-runs show the noise floor: a later change that moves fewer rows than the noise floor proves nothing.

### A7. Edge cases and custom cases
Work through `references/edge-cases.md`. Write at least three custom cases (October 2026 required three) under `evaluation/cases/` with inputs, expected output and what each tests. Injection, missing evidence and boundary values are the usual minimum.

## Part B. Fix loop (one change at a time)

1. Bank the current output (`runs/baseline_<run>.csv`); commit if using git.
2. Write the change record first (`references/change-record.md`): hypothesis, target rows, rows it could break, metric, ceiling.
3. Make one change.
4. Re-run the sample and the full evaluation set (cache makes unchanged calls free).
5. Diff both:
   ```
   python $T/scripts/rerun_diff.py runs/baseline_sample.csv runs/new_sample.csv --id-col <id> --expected <sample expected csv>
   python $T/scripts/rerun_diff.py output.baseline.csv output.csv --id-col <id>
   ```
   The first gives fixed / broken / churned and a verdict. The second is the blast radius on hidden rows: a change meant to fix 2 rows that moves 120 evaluation rows needs an explanation.
6. KEEP only when target rows improve and no previously correct row breaks; REVERT when two or more rows break or broken exceeds fixed; REVIEW (inspect, usually revert) when it is one for one. Record the verdict and numbers.
7. Stop when the next change is within the noise floor. Spend remaining time on justifications, evaluation reports and the interview.

## Part C. Justification quality
For explanation columns, follow `references/justification.md`: cite the real evidence ids the decision used, state the deciding fact, stay consistent with the label, no claims from unopened evidence. Spot-check 10 random evaluation rows, not only sample rows.

## Part D. Evaluation report
Fill `evaluation/evaluation_report.md` (structure in `hr-orchestrate-build/references/evaluation-reports.md`) from recorded runs only: sample metrics from `score_sample.py --json`, custom case results, and the failures-and-fixes table from `docs/experiments.md`.

## Exit gate
- [ ] preflight PASS on the full output
- [ ] Sample metrics recorded with run id; error classes listed with ceilings
- [ ] Offline re-run: 0 changed rows; online noise floor measured
- [ ] coupling_scan clean or every hit explained
- [ ] ≥3 custom cases with results
- [ ] Every kept change has a change record with numbers
- [ ] `evaluation/evaluation_report.md` filled; banked submission refreshed

Next: `hr-orchestrate-package` (and finish `hr-orchestrate-interview`).

## References
- `references/change-record.md`: change record template and verdict rules
- `references/edge-cases.md`: edge-case checklist by archetype
- `references/justification.md`: what a strong justification looks like
