---
name: hr-orchestrate-interview
description: HackerRank Orchestrate AI judge interview prep (30% of the score) - build docs/CONSTANTS.md with the provenance of every number in the code, generate drill questions from the participant's own code with file:line, prepare mechanism-plus-number answers for the nine probed topics, and run a mock interview where Claude plays the judge and checks each answer against the real code. Use from mid-build onward, after any design change, and before submitting.
---

# Orchestrate interview prep

The interview is about 30 minutes with an AI judge after submission (check the current rules for timing, camera and what you may have open). It rewards ownership: you explain your own system with specifics and raise its limits yourself. Claude prepares the material and rehearses; **the participant answers**. Never script answers for the participant to recite about code they have not understood; build their understanding instead. `$I` means this skill's directory.

## Step 1. CONSTANTS.md (start mid-build, keep current)

Every number and ordering in the code gets a row in `docs/CONSTANTS.md` (template: `references/constants-template.md`) with one provenance label:

| Label | Meaning |
|---|---|
| SPEC | Stated by the problem or AGENTS.md (cite the line) |
| MEASURED | Chosen from a recorded comparison (cite the run ids and numbers) |
| STANDARD | A conventional default (temperature 0, 3 retries), said as such |
| BOUND | A safety limit (timeouts, max tokens, max workers) |
| JUDGEMENT | A reasoned guess, not tuned; say so honestly |

Never describe a JUDGEMENT value as "chosen after evaluation". Check coverage:
```
python $I/scripts/interview_drill.py code/ --constants docs/CONSTANTS.md --strict
```
Every MISSING item is a question you are not ready for.

## Step 2. Prepare the nine topics

Use `references/judge-topics.md`. For each topic, write a short answer in `docs/INTERVIEW.md` using the shape **mechanism → where in code → number → trade-off → limit**. Example: "Rules decide, the model only extracts (`rules.py`, 14 rules, first match wins). On the 32 samples that gave 29/32 versus 24/32 when the model chose the label directly (CR-3). Cost: rules miss phrasing the extractor does not map; two of the three misses are that."

Facts in the answers must be VERIFIED against the code and recorded runs right before the interview. Re-run the counts (tests, rows, metrics) and update stale numbers.

## Step 3. Drill from the code

```
python $I/scripts/interview_drill.py code/ --constants docs/CONSTANTS.md --shuffle --seed 7 --limit 12
```

## Step 4. Mock interview (Claude plays the judge)

Protocol:
1. Ask one question at a time, mixing drill questions and topics. Start broad (architecture), then drill into a number, then a failure, then security, then limits.
2. Wait for the participant's answer. Do not answer for them.
3. Check the answer against the code and runs. Say what was VERIFIED, what was wrong, and what was vague.
4. Follow up on vagueness the way a judge would: "Which file?", "What number?", "How do you know?", "What did you compare it against?"
5. Score each answer 1-5 on specificity, correctness and ownership. After 8-12 questions, list the three weakest answers and re-drill them.

Run at least one full rehearsal before the deadline pressure peaks (around hour 18-20), and a short one after the final freeze, since numbers change.

## Honest limits

Prepare three limitations and say them before being asked. Strong form: the limit, the evidence (a row or a measured number), and what you would do next. Weak form: "it could be improved."

## Exit gate
- [ ] `interview_drill.py --strict` passes (every constant covered)
- [ ] `docs/INTERVIEW.md` covers the nine topics with verified numbers
- [ ] At least one full mock interview; weakest answers re-drilled
- [ ] Numbers re-verified after the final run

## References
- `references/judge-topics.md`: the nine topics, what the judge looks for, follow-ups
- `references/constants-template.md`: CONSTANTS.md template with examples
