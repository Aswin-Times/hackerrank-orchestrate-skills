# Architecture and code patterns

Language is free; Python is the usual choice. Patterns below are Python sketches to adapt, not code to paste unread. Write the participant's code fresh in the session.

## Module contracts

| Module | Does | Never does |
|---|---|---|
| `main.py` | parse args, run rows (bounded workers), resume from checkpoint, assemble and write | business logic |
| `contract.py` | column list, enums, `validate_row`, `serialize_row` (exact JSON key order, separators) | read data |
| `loaders.py` | read inputs into dataclasses; index evidence by every identifier | call the model |
| `llm.py` | the single model client (cache, retries, schema validation, usage log) | know about the problem |
| `observe.py` | build prompts from files in `prompts/`, call `llm.py`, return typed observations | decide outputs |
| `rules.py` | pure functions from data + observations to decisions; the rule table | I/O, model calls, randomness |
| `explain.py` | build justification text from rule results and evidence ids | introduce facts not in the evidence |

Comments beside each constant say where its value came from (statement line, measurement, standard, judgement). Module docstrings state the module's job and the design reason. Graders read source.

## CLI shape

```
python code/main.py                      # full evaluation input -> output.csv at the contract path
python code/main.py --sample             # sample input -> runs/sample_<run_id>.csv
python code/main.py --ids S003,S014      # selected rows, for tracing
python code/main.py --offline            # cache only; fails loudly on a cache miss
python code/main.py --workers 8 --limit 20
```

Each run gets a `run_id` (timestamp) used in file names and in `usage.jsonl`.

## Cached, validated client (sketch)

```python
def call(model, system, user, schema, *, row_id, run_id, max_tokens=1024):
    key = sha256(json.dumps([model, system, user, schema, SCHEMA_VERSION], sort_keys=True))
    hit = cache.get(key)
    if hit is None:
        if OFFLINE:
            raise CacheMiss(row_id)
        resp = with_backoff(lambda: client_request(model, system, user, schema, max_tokens))
        data, usage = parse_structured(resp)
        errors = validate(data, schema)
        if errors:  # one repair attempt
            resp = with_backoff(lambda: client_request(model, system, user + repair_note(errors), schema, max_tokens))
            data, usage2 = parse_structured(resp); usage = add(usage, usage2)
            if validate(data, schema):
                data = fallback(schema)
        hit = {"data": data, "usage": usage}
        cache.put(key, hit)
        log_usage(run_id, row_id, model, hit["usage"], cached=False)
    else:
        log_usage(run_id, row_id, model, hit["usage"], cached=True)
    return hit["data"]
```

Cache on disk as one JSON file per key (simple, diff-able) or SQLite. Keep the cache out of `code.zip` unless the statement allows it.

## Rule table (sketch)

```python
RULES = [
    # id,  reads,                              predicate,                                output
    ("R1", {"request.is_deletion_request"},    lambda f: not f.is_deletion_request,     Decision("NOT_APPLICABLE")),
    ("R2", {"evidence.post_audit_only"},       lambda f: f.only_post_audit_evidence,    Decision("ESCALATE")),
    ...
]

def decide(facts):
    for rule_id, reads, pred, out in RULES:
        if pred(facts.restrict(reads)):   # rule only sees the fields it declares
            return out.with_rule(rule_id)
    return DEFAULT.with_rule("DEFAULT")
```

Test that each rule sees only its declared fields and that changing free-text fields never changes a decision for rules that do not read them.

## Evidence-grounded justification

Track evidence the agent actually opened (`opened_ids`). `explain.py` may cite only ids in that set; anything else is stripped and logged. Justifications state the deciding fact and the id, for example: "COMPLETE: replica `db_eu_2` snapshot `F0192` shows the email column null for user U88 at 2026-09-14; no restore event after the delete (A5512)."

## Atomic write

```python
tmp = out_path.with_suffix(".tmp")
write_csv(tmp, rows)                 # exact header, contract order, one row per input id
problems = validate_file(tmp, inputs)
if problems:
    raise SystemExit(f"refusing to write {out_path}: {problems[:5]}")
os.replace(tmp, out_path)
```

## Concurrency

Bounded thread pool (4-8 workers); results collected by id, then sorted into input order before writing, so output order never depends on timing.
