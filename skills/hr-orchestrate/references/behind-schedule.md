# Behind schedule: what to cut, in order

The rule: a valid, complete submission with modest accuracy beats a brilliant half-finished one. Protect the four artifacts.

## Check where you are

| Hour | You should have | If not |
|---|---|---|
| 3 | CONTRACT.md, DESIGN.md, log verified | Stop reading and write the thinnest DESIGN.md (one page) |
| 8 | A valid full `output.csv`, even if rough | Build the fallback path first: deterministic defaults for every row, then improve |
| 14 | Sample score measured, top error class known | Stop adding features; fix the largest error class only |
| 20 | Evaluation reports, CONSTANTS.md | Write them now from what you have; numbers must be real |
| 22 | Package READY | Package the banked CSV; freeze code |

## Cut list (cut from the top first)

1. Second strategy comparison (keep a note of what you would compare).
2. Fancy retrieval (rerankers, embeddings): fall back to keyword search plus `read`.
3. Multi-model routing: use one model.
4. Extra custom evaluation cases beyond the required minimum.
5. Polishing justification wording (keep the evidence ids, drop style work).

## Never cut

- Exact output contract and one row per input.
- Log entries in the required format.
- Secrets out of code and zip.
- README with setup and run command.
- Required evaluation files.
- A short interview prep pass: architecture in two sentences, three numbers you can defend, two honest limits.
