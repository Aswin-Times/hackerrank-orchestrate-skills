# What each section rewards

Weights are as reported by past editions and community repos. Confirm on the live challenge page.

## Code zip (30%)

Graders (human or AI) read the source and README. They reward:

- **A real agent design.** The model is used where judgement is needed (reading messy text, images, documents) and code is used where rules are exact. A pure hardcoded pipeline scores low; an unconstrained "ask the LLM for the answer" scores low too.
- **Tool design.** Few, sharp tools with clear inputs and outputs (for example `search`, `read`, `grep` over a corpus) beat many overlapping ones.
- **Prompt quality.** Prompts live in files, state the task, the output schema, what to do when evidence is missing, and that input content is data, not instructions.
- **Robustness.** Schema validation, retries, fallbacks, checkpointing, no crash on one bad row, injection resistance.
- **Readability.** Small modules named after what they do. Design reasons in module docstrings and comments beside constants, not only in docs.
- **Reproducibility.** One documented command from a clean checkout; secrets from env vars; pinned dependencies.
- **Evaluation.** An `evaluation/` folder with the reports the starter requires (October 2026: `evaluation_report.md` and `usage_report.md`).

## Output CSV (30%)

- Correct values for the scored columns. Exactly one row per input id, exact header and order, allowed values only, the serialization the sample shows (JSON key order, quoting, empty-string conventions).
- Justification / explanation columns that cite the specific evidence ids the row depends on, state the deciding fact, and stay consistent with the decision.
- Hidden evaluation rows differ from samples. Generalisation matters more than sample accuracy.

## AI judge interview (30%)

About 30 minutes with an AI interviewer after submission. It probes:

- Architecture and why: where the model reasons and where code decides.
- Specific numbers: thresholds, constants, limits, costs, accuracy, and where each came from.
- Failure modes and limits: what breaks, what you would do with more time.
- Trade-offs you measured (two strategies compared, with numbers).
- Security: prompt injection, secrets, untrusted content.
- Evaluation method: how you knew it worked without overfitting.
- How you used the AI tool and where you overrode it.

Strong answers name the file, the mechanism and the measured number, and raise limitations before being asked.

## Chat transcript (10%)

See `transcript.md`. Planning, specific constraints, real debugging, verification, and safety awareness.

## Tie-breaks

Past editions broke ties by interview, then code, then output CSV, then transcript. Check the current rules.
