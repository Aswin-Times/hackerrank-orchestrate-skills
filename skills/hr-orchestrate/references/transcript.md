# Transcript (log.txt)

The transcript is the `log.txt` the starter's `AGENTS.md` tells the coding agent to append to. It is the conversation with your coding tool, not your agent's runtime logs.

## Community-reported sub-weights

| Signal | Weight | Looks like |
|---|---|---|
| Direction and ownership | 35% | The human sets goals and constraints, accepts or rejects proposals with reasons |
| Specificity | 25% | Prompts and summaries name files, functions, schemas, thresholds, row ids |
| Iteration and verification | 25% | Real errors and wrong rows quoted; hypothesis, fix, re-run, measured result |
| Safety awareness | 15% | Secrets, injection, untrusted content, data rules discussed and handled |

## Strong versus weak entries

Weak summary: "Updated the code and fixed bugs."

Strong summary: "Changed `code/rules.py::decide_status` so a restore event after the delete re-opens the case (rule R7). Sample accuracy 27/32 → 29/32; rows S014 and S021 fixed, no previously correct row changed (`rerun_diff.py`: 2 rows differ). Rejected the alternative of trusting workflow status because AGENTS.md §6.6 says statuses are claims."

Weak prompt (participant): "make it better"

Strong prompt: "Rows S014 and S021 are wrong: we mark COMPLETE but a backup restore at 2026-10-02 re-created the email. Add a rule for restore-after-delete; don't touch the tombstone logic; show me the diff of the whole sample output."

## How you help

- If the participant's prompt is vague, ask one specific question or state the assumption you are taking, so the log shows direction.
- Suggest specific phrasings when useful, but never rewrite or fabricate what the participant said: the log records their prompt verbatim.
- Never paste raw progress spam ("processed row 1", "processed row 2") into the log.
- Redact secrets as `[REDACTED]` in the logged prompt.
- Re-read each appended entry and fix it before replying if it breaks the starter's format.
