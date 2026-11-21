# Justification quality

Output CSV is worth 30%, and explanation columns are where many teams lose points with correct labels.

## A strong justification
1. States the decision in the column's terms.
2. Names the deciding fact or facts.
3. Cites the real evidence ids (file, activity, audit, document, image ids) that prove each fact, and only ids the agent actually opened in this run.
4. Mentions the rule or policy line applied when the problem has one.
5. Is consistent with the label: never "insufficient evidence" next to a confident verdict.
6. Is short and specific: one to three sentences, no filler, no hedging boilerplate.

Example (weak): "Based on the analysis, the request appears to be complete."

Example (strong): "COMPLETE: deletion verified in all 3 systems. Primary DB snapshot F0192 and replica F0207 show no row for U88 at audit time; backup B12 was purged per activity A5512; no restore or sync after the purge."

## How to build them
- Code chooses which facts matter (from the rule that fired and its inputs). The model, if used at all, only phrases those facts. Prefer templates for structured explanations: they are deterministic and never invent.
- Keep an `opened_ids` set per row; a post-check strips any cited id not in it and logs the violation.
- When evidence is missing, say what was looked for and not found, and what the agent did instead (escalated, used the default).

## Spot-check routine
Pick 10 random evaluation rows (not sample rows). For each, open the cited evidence and confirm it says what the justification claims. Count failures; fix the class, not the single row. Record the count in the evaluation report.
