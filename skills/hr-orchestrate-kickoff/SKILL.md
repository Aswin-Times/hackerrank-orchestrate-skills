---
name: hr-orchestrate-kickoff
description: HackerRank Orchestrate first hour - read the starter repo (AGENTS.md, CLAUDE.md, problem_statement.md, dataset), get log.txt transcript logging exactly right (location, tool= and model= lines), extract the output contract into docs/CONTRACT.md, profile the sample and evaluation data, and pick an architecture archetype. Use as soon as an Orchestrate starter repo is opened or a problem_statement.md is pasted, and whenever the contract or logging is in doubt.
---

# Orchestrate kickoff (hour 0-1)

Goal: before writing any agent code, know exactly what must be produced, prove logging works, and understand the data. Mistakes here cost points in every section.

Scripts are in this skill's `scripts/` folder (Python 3.9+ standard library). Run each with `--help` for options. Below, `$K` means this skill's directory.

## Step 1. Read everything, in this order

1. `AGENTS.md` in full. It is the contract for you, the coding agent. Obey it literally.
2. `CLAUDE.md` (usually just `@AGENTS.md`). Never remove that import; append below it if needed. Never edit `AGENTS.md`.
3. `README.md`, `problem_statement.md`, any evaluation-criteria file, any trace or submission instructions.
4. List the dataset tree with file sizes. Do not read huge files whole; sample them.

Then tell the participant in 5-8 lines: the task, the output columns, the number of evaluation rows, the required files, and anything surprising.

## Step 2. Logging (do this before anything else is built)

1. Find the log path and entry format in `AGENTS.md` (it moved between editions; see `references/log-format.md`).
2. Determine the exact harness name and model id from your runtime (system prompt, session metadata). Never guess. For Claude Code the harness is `Claude Code` and the model id looks like `claude-opus-5-5`.
3. Append the session-start entry, then a per-turn entry for every participant message, exactly in the starter's format.
4. Validate:
   ```
   python $K/scripts/check_log.py <log path> --expect-tool "Claude Code" --expect-model <model id>
   ```
   Fix every FAIL before continuing. Re-run after each turn when unsure.

## Step 3. Extract the contract

```
python $K/scripts/contract_extract.py <starter dir> > docs/contract_draft.md
```

The script finds MUST/NEVER/only/exactly lines, CSV headers, required files, URLs and allowed-value lists with `file:line`. It is a heuristic: read the statement yourself too. Then write `docs/CONTRACT.md` from `references/contract-template.md`. Every line cites its source (`problem_statement.md:42`). Ambiguities go in the Assumptions section with your chosen reading; ask the participant about anything that changes the design.

## Step 4. Profile the data

```
python $K/scripts/profile_data.py <sample input csv> <sample output csv> <eval input csv> <output template csv> --id-col <id column>
```

It reports row counts, columns, blanks, low-cardinality columns (likely enums) with their values, JSON-looking columns, header mismatches between the template and the sample output, and id overlap between files. Record in CONTRACT.md: enum values seen versus allowed, serialization conventions (JSON key order, empty strings, quoting), and whether evaluation ids overlap sample ids (they should not).

## Step 5. Work 5-10 sample rows by hand

For a spread of output values, read the inputs and explain why the expected output is what it is, using domain reasoning and the statement, not pattern matching. Write these as "Worked examples" in CONTRACT.md. Rows you cannot explain are the first risks to raise.

## Step 6. Choose the archetype

Open `references/archetypes.md`, pick the closest archetype (or say none fits and why), and note it in CONTRACT.md. It fixes the model/code boundary that `hr-orchestrate-build` turns into DESIGN.md.

## Step 7. Repo hygiene

- `.gitignore` covers `.env`, virtualenvs, caches, `submission/`, model-call caches if large.
- `.env.example` lists variable names only. Check that the API key variable is set without printing it.
- Commit the starter state before building, if the participant uses git.
- Create `docs/STATUS.md` with phase = kickoff done, the gate results, and the next step.

## Exit gate

- [ ] `check_log.py` passes with the exact tool and model
- [ ] `docs/CONTRACT.md` complete, every rule cited, assumptions listed
- [ ] Data profiled; enums and serialization recorded
- [ ] Worked examples written; unexplained rows flagged
- [ ] Archetype chosen
- [ ] `docs/STATUS.md` updated

Next: `hr-orchestrate-build`.

## References
- `references/log-format.md`: log locations and formats by edition, and common invalid entries
- `references/contract-template.md`: CONTRACT.md skeleton
- `references/archetypes.md`: five problem archetypes from past editions with their model/code split
