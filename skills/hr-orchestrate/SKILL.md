---
name: hr-orchestrate
description: START HERE for HackerRank Orchestrate, the 24-hour AI-agent hackathon scored on code zip, output CSV, AI judge interview and chat transcript (log.txt). Master plan - scoring, phase order and exit gates, the 24-hour clock, which hr-orchestrate-* skill to run next, failure routing, hard rules, and transcript discipline. Use when the user mentions HackerRank Orchestrate, opens a starter repo with AGENTS.md + problem_statement.md + log.txt logging, asks what to do next in the challenge, or when any step fails. Not for other hackathons or ordinary coding work.
---

# HackerRank Orchestrate: master plan

You (Claude) build the agent directly in the participant's starter repo. The participant owns the decisions; you propose, build, measure and report. Final score = 0.30 code zip + 0.30 output CSV + 0.30 AI interview + 0.10 transcript. Balance wins: past winners were strong in all four, and a peak in one section does not carry the rank.

**Precedence.** This edition's `AGENTS.md`, `problem_statement.md` and live challenge page override everything in these skills. The contract changes every edition (log location, required log fields, required report files). When a skill and the starter disagree, follow the starter and say so.

## The suite

| Skill | Run it when | Exit gate (do not move on until true) |
|---|---|---|
| `hr-orchestrate` (this) | Start, lost, or something failed | You know the next skill |
| `hr-orchestrate-kickoff` | Starter repo just arrived | `docs/CONTRACT.md` written, `log.txt` entries pass `check_log.py`, sample data profiled, archetype chosen |
| `hr-orchestrate-build` | Contract written | `docs/DESIGN.md` written; one command writes a valid `output.csv` for every sample row, then for every evaluation row |
| `hr-orchestrate-test-fix` | Full CSV exists | Wrong rows classified, fixes kept only with a change record, two runs agree, `evaluation/` reports filled |
| `hr-orchestrate-interview` | From about hour 14, in parallel | `docs/CONSTANTS.md` covers every number; drill answered from real code |
| `hr-orchestrate-package` | Output is final | `package.py` reports READY and `submission/` holds every required artifact |

## Working files in the challenge repo

Create these as you go; they keep the work recoverable after a context reset and feed the interview.

- `docs/STATUS.md`: current phase, last gate passed, latest measured numbers, next step. Update it at every gate.
- `docs/CONTRACT.md`: the output contract, from kickoff.
- `docs/DESIGN.md`: architecture and decision rules, from build.
- `docs/experiments.md`: one change record per change, from test-fix.
- `docs/CONSTANTS.md`: provenance of every constant, from interview.

Never edit the starter's `AGENTS.md`. If `CLAUDE.md` is only `@AGENTS.md`, keep that line and append below it.

## 24-hour clock (adjust once the problem is known)

| Hours | Work | Skill |
|---|---|---|
| 0-1 | Read everything, verify logging, write CONTRACT.md, profile samples | kickoff |
| 1-3 | DESIGN.md: model/code boundary, decision rules, escalation, failure table | build |
| 3-8 | Thin end-to-end slice first, then fill in. First valid full CSV by hour 8 | build |
| 8-14 | Score on samples, trace wrong rows, one-change loops, edge cases | test-fix |
| 14-18 | Justification quality, determinism, custom eval cases, evaluation reports | test-fix |
| 14-20 | CONSTANTS.md, drill, rehearsal | interview |
| 20-22 | Clean run from an empty checkout, security pass, usage report from the final run | package |
| 22-24 | Buffer. No new features. Submit with time to spare | package |

## Failure routing

| Symptom | Go to |
|---|---|
| Log entry missing, `tool=`/`model=` wrong | kickoff: `references/log-format.md`, re-run `check_log.py` |
| Unsure what a column or value means | kickoff: re-read the statement, record the reading in CONTRACT.md as an assumption |
| Run crashes partway | build: `references/guardrails.md` (failure handling, checkpointing) |
| Invalid label, bad JSON, wrong header | build: guardrails (schema); test-fix: `preflight.py` |
| Same input, different output | test-fix: determinism section; build: caching |
| Great on samples, unsure it generalises | test-fix: overfitting checks |
| Wrong row, cause unknown | test-fix: trace one input end to end |
| Right value, weak justification | test-fix: `references/justification.md` |
| Prompt injection got through | build: guardrails (injection) |
| Cannot defend a number | interview: CONSTANTS.md |
| Behind schedule | `references/behind-schedule.md` |

## Hard rules

1. **Contract first.** Exact columns and order, one row per input id, allowed values, serialization, required files. Read it fresh each edition.
2. **Model describes, code decides.** The model returns typed observations (booleans, enums, extracted values with the source id). Plain, tested code turns them into every scored value. Never branch on whether a free-text model field is empty.
3. **Ground every claim.** A justification may cite only evidence the agent actually opened in this run, by its real id. No evidence, no claim: escalate or fall back.
4. **Samples motivate or falsify; the domain justifies.** Never add a rule or constant whose only reason is that it fixes a sample row. Never iterate until one sample number matches.
5. **One change at a time, with a change record**, and diff the whole output, not just the target row. Keep the change only if the target improves and no previously correct row breaks.
6. **One bad row never kills the run.** Validate, retry once, then write a safe fallback row. Never write a partial `output.csv`; write to a temp file and rename.
7. **Deterministic given the cache.** Cache every model call by input hash; temperature 0 where supported; stable sort orders and JSON serialization.
8. **Secrets from environment variables only.** Never in code, logs, prompts or the zip.
9. **Never invent numbers.** Label every figure you report VERIFIED (checked against files or a run now), MEASURED (from a recorded run), INFERRED or UNKNOWN. A skipped check is UNKNOWN, never a pass.
10. **Keep a banked submission.** Once a valid full CSV exists, copy it to `submission/output.banked.csv` and refresh it only with a better verified run.

## Transcript discipline

The transcript is the starter's `log.txt`. It records the participant's prompts verbatim and your response summaries, so both sides count. Community-reported sub-weights: direction and ownership 35%, specificity 25%, iteration and verification 25%, safety awareness 15%. Details: `references/transcript.md`.

- Before building, state the plan: what you will read, produce, where the model reasons and where code enforces.
- Each response summary names the files changed, the decision taken and why, and the evidence (command output, row ids, counts).
- After a failure, quote the real error or wrong row, state the suspected cause, then the fix.
- When the participant's prompt is vague, ask one sharp question or state the assumption you are making, so the log shows direction.
- Push back when something over-builds or risks overfitting, and say why.
- Write the log entry exactly as the starter's `AGENTS.md` specifies, every turn, then re-read it.

## References

- `references/rubric.md`: what each of the four sections rewards and how to raise it
- `references/winner-patterns.md`: patterns from top-ranked agents
- `references/editions.md`: past problems and how the contract changed
- `references/transcript.md`: transcript scoring and good versus weak entries
- `references/behind-schedule.md`: what to cut, in order
