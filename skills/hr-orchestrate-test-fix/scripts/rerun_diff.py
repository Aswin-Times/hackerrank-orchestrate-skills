#!/usr/bin/env python3
"""Diff two runs of the agent and give a keep/revert verdict for a change.

Without --expected: blast radius only (rows and columns that changed), which
is also how you measure run-to-run noise (run twice, no code change).
With --expected (sample answers): classify each row of the sample as
  fixed    wrong before, right after
  broken   right before, wrong after
  churned  wrong before and after, but different
and print a verdict:
  KEEP     fixed > 0 and broken == 0
  REVERT   broken > fixed, or broken >= 2
  REVIEW   anything else (for example one fixed and one broken: within noise)
--cols limits the comparison to scored columns. Standard library only.
"""
import argparse
import csv
import json
import sys
from collections import Counter

csv.field_size_limit(min(sys.maxsize, 2 ** 31 - 1))


def read(path, id_col):
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as fh:
        rows = list(csv.DictReader(fh))
    return {r[id_col]: r for r in rows}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--id-col", required=True)
    ap.add_argument("--expected", help="expected outputs (sample) for fixed/broken classification")
    ap.add_argument("--cols", help="comma-separated columns to compare (default: all except id)")
    ap.add_argument("--show", type=int, default=10, help="changed rows to print (default 10)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    b, c = read(a.before, a.id_col), read(a.after, a.id_col)
    allcols = [k for k in (next(iter(b.values())).keys() if b else []) if k != a.id_col]
    cols = a.cols.split(",") if a.cols else allcols
    ids = sorted(set(b) | set(c))
    only_b = sorted(set(b) - set(c))
    only_c = sorted(set(c) - set(b))
    changed, per_col = [], Counter()
    for i in ids:
        if i in b and i in c:
            diff = [k for k in cols if b[i].get(k, "") != c[i].get(k, "")]
            if diff:
                changed.append((i, diff))
                per_col.update(diff)
    out = {"rows_before": len(b), "rows_after": len(c), "only_before": only_b, "only_after": only_c,
           "changed": len(changed), "changed_by_column": dict(per_col),
           "changed_ids": [i for i, _ in changed]}

    if a.expected:
        e = read(a.expected, a.id_col)
        right = lambda run, i: i in run and all(run[i].get(k, "") == e[i].get(k, "") for k in cols if k in e[i])
        fixed = [i for i in e if not right(b, i) and right(c, i)]
        broken = [i for i in e if right(b, i) and not right(c, i)]
        churn = [i for i in e if not right(b, i) and not right(c, i) and i in b and i in c
                 and any(b[i].get(k) != c[i].get(k) for k in cols)]
        before_ok = sum(right(b, i) for i in e)
        after_ok = sum(right(c, i) for i in e)
        if fixed and not broken:
            verdict = "KEEP"
        elif len(broken) > len(fixed) or len(broken) >= 2:
            verdict = "REVERT"
        else:
            verdict = "REVIEW"
        out.update({"sample_right_before": before_ok, "sample_right_after": after_ok, "sample_size": len(e),
                    "fixed": fixed, "broken": broken, "churned": churn, "verdict": verdict})

    if a.json:
        print(json.dumps(out, indent=2))
        return
    print("rows: before %d, after %d" % (len(b), len(c)))
    if only_b or only_c:
        print("ids only in before: %d %s; only in after: %d %s" % (len(only_b), only_b[:5], len(only_c), only_c[:5]))
    print("changed rows: %d of %d" % (len(changed), len(ids)))
    for k, v in per_col.most_common():
        print("  %-24s %d" % (k, v))
    for i, diff in changed[: a.show]:
        print("- %s" % i)
        for k in diff:
            print("    %s: %s  ->  %s" % (k, b[i].get(k, "")[:160], c[i].get(k, "")[:160]))
    if a.expected:
        print("\nsample: %d/%d right before, %d/%d after" % (out["sample_right_before"], out["sample_size"],
                                                            out["sample_right_after"], out["sample_size"]))
        print("fixed:   %d %s" % (len(out["fixed"]), out["fixed"][:10]))
        print("broken:  %d %s" % (len(out["broken"]), out["broken"][:10]))
        print("churned: %d %s" % (len(out["churned"]), out["churned"][:10]))
        print("VERDICT: %s" % out["verdict"])


if __name__ == "__main__":
    main()
