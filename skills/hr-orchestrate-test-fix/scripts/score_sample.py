#!/usr/bin/env python3
"""Score a predicted CSV against expected outputs (the public sample).

Per column: exact-match accuracy and the wrong ids.
For JSON list-of-object columns (--json-col), also:
  * step-level: precision / recall / F1 of steps matched on --step-key fields
  * field-level: per-field accuracy over matched steps
  * sequence: share of rows whose list of step keys equals the expected list in order
--confusion COL prints a confusion matrix for one column.
--show N prints the first N wrong rows per column (expected vs predicted).
--json writes the metrics as JSON (for experiment records).
Standard library only.
"""
import argparse
import csv
import json
import sys
from collections import Counter, defaultdict

csv.field_size_limit(min(sys.maxsize, 2 ** 31 - 1))


def read(path, id_col):
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if rows and id_col not in rows[0]:
        raise SystemExit("%s has no column %r" % (path, id_col))
    return {r[id_col]: r for r in rows}


def steps(value):
    try:
        obj = json.loads(value)
    except (ValueError, TypeError):
        return None
    if isinstance(obj, list) and all(isinstance(x, dict) for x in obj):
        return obj
    return None


def match_steps(pred, exp, key_fields):
    """Greedy multiset match on key fields, in expected order. Returns list of (exp_step, pred_step)."""
    key = lambda s: tuple(str(s.get(k, "")) for k in key_fields)
    pool = defaultdict(list)
    for i, p in enumerate(pred):
        pool[key(p)].append(i)
    pairs = []
    for e in exp:
        bucket = pool.get(key(e))
        if bucket:
            pairs.append((e, pred[bucket.pop(0)]))
    return pairs


def pct(a, b):
    return "n/a" if not b else "%d/%d (%.1f%%)" % (a, b, 100.0 * a / b)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("predicted")
    ap.add_argument("expected")
    ap.add_argument("--id-col", required=True)
    ap.add_argument("--json-col", action="append", default=[], help="JSON list-of-objects column (repeatable)")
    ap.add_argument("--step-key", help="comma-separated fields that identify a step (default: all fields except "
                                       "step_no/evidence_id of the first expected step)")
    ap.add_argument("--confusion", help="column for a confusion matrix")
    ap.add_argument("--show", type=int, default=0, help="print first N wrong rows per column")
    ap.add_argument("--json", action="store_true", help="print metrics as JSON")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    pred, exp = read(a.predicted, a.id_col), read(a.expected, a.id_col)
    ids = sorted(exp)
    missing = [i for i in ids if i not in pred]
    cols = [c for c in (next(iter(exp.values())).keys() if exp else []) if c != a.id_col]
    metrics = {"rows": len(ids), "missing": missing, "columns": {}}

    for c in cols:
        wrong = [i for i in ids if i in pred and pred[i].get(c, "") != exp[i].get(c, "")]
        ok = len(ids) - len(missing) - len(wrong)
        metrics["columns"][c] = {"exact": ok, "of": len(ids), "wrong_ids": wrong}

    for c in a.json_col:
        tp = fp = fn = seq_ok = parsed = 0
        field_ok, field_n = Counter(), Counter()
        key_fields = a.step_key.split(",") if a.step_key else None
        for i in ids:
            e = steps(exp[i].get(c, ""))
            p = steps(pred[i].get(c, "")) if i in pred else None
            if e is None:
                continue
            if p is None:
                fn += len(e)
                continue
            parsed += 1
            if key_fields is None:
                sample = e[0] if e else (p[0] if p else {})
                key_fields = [k for k in sample if k not in ("step_no", "evidence_id")]
            pairs = match_steps(p, e, key_fields)
            tp += len(pairs)
            fp += len(p) - len(pairs)
            fn += len(e) - len(pairs)
            kf = lambda s: tuple(str(s.get(k, "")) for k in key_fields)
            if [kf(s) for s in p] == [kf(s) for s in e]:
                seq_ok += 1
            for es, ps in pairs:
                for f in es:
                    field_n[f] += 1
                    field_ok[f] += str(es.get(f)) == str(ps.get(f))
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        metrics["columns"][c]["steps"] = {
            "key_fields": key_fields, "tp": tp, "fp": fp, "fn": fn,
            "precision": round(prec, 4), "recall": round(rec, 4), "f1": round(f1, 4),
            "sequence_exact": seq_ok, "rows_parsed": parsed,
            "field_accuracy": {f: [field_ok[f], field_n[f]] for f in field_n}}

    if a.confusion:
        cm = Counter((exp[i].get(a.confusion, ""), pred[i].get(a.confusion, "")) for i in ids if i in pred)
        metrics["confusion"] = {"%s -> %s" % k: v for k, v in sorted(cm.items())}

    if a.json:
        print(json.dumps(metrics, indent=2))
        return
    print("rows: %d   missing from predicted: %d %s" % (len(ids), len(missing), missing[:5] if missing else ""))
    for c, m in metrics["columns"].items():
        print("\n%s: exact %s" % (c, pct(m["exact"], m["of"])))
        if m["wrong_ids"]:
            print("  wrong: %s%s" % (", ".join(m["wrong_ids"][:20]), " ..." if len(m["wrong_ids"]) > 20 else ""))
        s = m.get("steps")
        if s:
            print("  steps matched on %s: precision %.3f recall %.3f F1 %.3f (tp %d fp %d fn %d)"
                  % (s["key_fields"], s["precision"], s["recall"], s["f1"], s["tp"], s["fp"], s["fn"]))
            print("  sequence exact: %s" % pct(s["sequence_exact"], len(ids)))
            for f, (ok, n) in sorted(s["field_accuracy"].items()):
                print("  field %-14s %s" % (f, pct(ok, n)))
        for i in m["wrong_ids"][: a.show]:
            print("  - %s\n      expected:  %s\n      predicted: %s" % (i, exp[i].get(c, "")[:300], pred[i].get(c, "")[:300]))
    if a.confusion:
        print("\nconfusion (%s, expected -> predicted):" % a.confusion)
        for k, v in metrics["confusion"].items():
            print("  %-40s %d" % (k, v))


if __name__ == "__main__":
    main()
