# Change record

One per change, appended to `docs/experiments.md`. Write the top half before touching code.

```markdown
## CR-<n>: <short name>   (<date time>)

Hypothesis: <cause of the error class, in one sentence>
Target rows: <ids>   Error class: <name>   Ceiling: <rows a perfect fix gains>
Could break: <rows or behaviours at risk, and why>
Change: <file::function, what changes>   Constants added: <name = value, provenance>
Metric: <e.g. deletion_status exact on sample; steps F1>
Baseline: <value> (run <id>)

Result: <value> (run <id>)
Sample diff: fixed <ids>, broken <ids>, churned <ids>
Blast radius on evaluation set: <n> rows changed (<columns>)
Noise floor: <n> rows (from two unchanged online runs)
Counterfactual: <switched the new component off: effect disappears? yes/no>
Verdict: KEEP | REVERT | REVIEW -> <final decision and reason>
```

## Verdict rules

| Situation | Verdict |
|---|---|
| Target rows fixed, nothing broken | KEEP |
| Two or more previously correct rows broken | REVERT |
| Broken > fixed | REVERT |
| One fixed, one broken | REVIEW; usually revert unless the broken row's expected answer contradicts the statement |
| Sample unchanged, evaluation set moves a lot | REVIEW; explain the moved rows before keeping |
| Change is smaller than the noise floor | Not proven; do not claim a gain |

A single labeled row is noise. Never accept or reject a change because of one row alone, and never keep a rule whose only justification is one sample row.

## Rejection log

Keep rejected ideas with the number that killed them (`REVERT: broke S004 and S019; F1 0.91 -> 0.88`). The interview asks what you tried that did not work.
