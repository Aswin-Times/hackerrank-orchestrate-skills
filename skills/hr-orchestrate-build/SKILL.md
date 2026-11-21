---
name: hr-orchestrate-build
description: HackerRank Orchestrate design and build phase - turn docs/CONTRACT.md into docs/DESIGN.md (model/code boundary, typed observation schema, ordered decision rules, fallbacks, failure table), then build the agent in the starter repo - a cached, schema-validated LLM client with usage logging, pure rule code, evidence-grounded justifications, checkpointing and atomic CSV writes - until one command writes a valid output.csv for every row. Use after hr-orchestrate-kickoff, whenever the architecture is being chosen or changed, and when the run crashes or the model output is invalid.
---

# Orchestrate design and build (hours 1-8)

Input: `docs/CONTRACT.md` and the archetype from kickoff. Output: `docs/DESIGN.md`, working code, a valid full `output.csv`. `$B` means this skill's directory.

## Step 1. Write DESIGN.md before code (30-60 minutes, no longer)

Fill `references/design-template.md` into `docs/DESIGN.md`. The decisions that matter most:

1. **Model/code boundary.** List every output column and who produces it. Scored values come from code. The model produces typed observations (booleans, enums, extracted values, each with the evidence id it came from) and, at most, the wording of a justification built around facts code selected.
2. **Observation schema.** The exact JSON the model returns, with enums spelled out and an `unknown`/`not_found` option for every field. Version it (`SCHEMA_VERSION`) so the cache invalidates when it changes.
3. **Decision rules as an ordered table:** id, precedence, condition, inputs read, output, source (statement line or domain reason). A rule that reads no free text cannot be steered by injected text.
4. **Fallback for every column** when evidence is missing or the model fails, and the escalation conditions.
5. **Failure table:** what can fail (API error, timeout, invalid JSON, missing file, unreadable image, rate limit), detection, response.
6. **Rejected alternatives**, one line each with the reason. The interview asks.

Show the participant a 10-line summary and get agreement or changes before building. Their decision belongs in the log.

## Step 2. Lay out the code

Follow `references/architecture.md`. In short:

```
code/
  main.py          # CLI: --input --output --limit --ids --offline --workers
  contract.py      # columns, enums, serialization, validate_row()
  loaders.py       # read every input file into typed records
  llm.py           # one client: cache, retries, schema validation, usage log
  observe.py       # prompts in -> typed observations out (the only module that calls llm.py)
  rules.py         # pure functions: observations + data -> decisions (no I/O, no model)
  explain.py       # justification text from the facts and evidence ids rules used
  prompts/         # prompt files, versioned
evaluation/        # evaluate.py + the reports the starter requires
tests/             # rules, contract, injection, tie-breaks
```

When writing Anthropic SDK code, load the `claude-api` skill if it is available, and use only models and providers the problem statement allows. Default split when allowed: a small fast model for screening and simple extraction, a stronger model for hard reading, and never a model for arithmetic or final labels.

## Step 3. Thin slice first

1. Make `python code/main.py --limit 3` produce three valid rows end to end, even with crude rules.
2. Run on all sample rows; validate with `hr-orchestrate-test-fix`'s `preflight.py`.
3. Run on the full evaluation input. As soon as it is valid, copy it to `submission/output.banked.csv`.
4. Only then deepen: better observations, more rules, better justifications.

## Step 4. The LLM client (`llm.py`) must

- Cache every call on disk keyed by a hash of (model, system prompt, user content, schema version, parameters). Re-runs are free and identical; `--offline` serves only from cache.
- Request structured output (tool use or JSON schema) and validate against the schema; on failure, one repair retry with the validation error; then return a typed fallback, never raise into the row loop.
- Use temperature 0 where supported, timeouts, bounded concurrency, exponential backoff on rate limits.
- Append one JSON line per call to `evaluation/usage.jsonl`: `run_id`, `row_id`, `provider`, `model`, `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cached` (served from local cache), `latency_ms`. `usage_report.py` turns this into the required report.
- Read the API key from the environment only.

## Step 5. Guardrails

Read `references/guardrails.md` and apply all of it: input content is data, not instructions (delimit it, say so in the prompt, and keep decision rules from reading free text); per-row try/except with a fallback row; checkpoint each finished row to a JSONL so a crash resumes; write `output.csv` to a temp file, validate, then rename; stable ordering and JSON serialization exactly as the sample shows.

## Step 6. Evaluation scaffolding

Create `evaluation/evaluate.py` that compares a run against the sample expected outputs per column (and per sub-field for JSON columns) and prints accuracy plus the list of wrong ids. Required report contents are in `references/evaluation-reports.md`. Generate the usage report from the final run:

```
python $B/scripts/usage_report.py evaluation/usage.jsonl --run-id <final run id> --price <model>=<usd per M input>:<usd per M output> --out evaluation/usage_report.md
```

Look up current prices (the `claude-api` skill lists them) and state the date and source in the report. Never invent prices.

## Exit gate

- [ ] `docs/DESIGN.md` written and agreed
- [ ] `python code/main.py` writes a valid `output.csv` for all evaluation rows (preflight passes)
- [ ] Banked copy in `submission/`
- [ ] Re-run with `--offline` reproduces the same CSV byte for byte
- [ ] `evaluation/usage.jsonl` populated; README has setup and run commands
- [ ] `docs/STATUS.md` updated

Next: `hr-orchestrate-test-fix`. Start `hr-orchestrate-interview` notes now: every constant you add gets a CONSTANTS.md line.

## References
- `references/design-template.md`: DESIGN.md skeleton
- `references/architecture.md`: layout, module contracts, code patterns (cached client, rule table, atomic write)
- `references/guardrails.md`: failure handling, injection, secrets, determinism, checkpointing
- `references/evaluation-reports.md`: what evaluation_report.md and usage_report.md must contain
