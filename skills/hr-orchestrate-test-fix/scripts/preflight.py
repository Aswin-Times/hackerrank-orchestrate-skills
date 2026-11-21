#!/usr/bin/env python3
"""Check an Orchestrate output.csv against the contract before anyone sees it.

FAIL checks:
  * header equals the template header (or --header) exactly, in order
  * one row per input id: no missing ids, no extra ids, no duplicates
  * every row has the right number of fields
  * enum columns contain only allowed values (--enum col=A|B|C)
  * JSON columns parse (--json-col)
  * required columns are not blank (--required col, or --all-required)
WARN checks:
  * UTF-8 BOM, mixed line endings, no trailing newline
  * JSON object key order differs from the sample output (--sample)
  * values never seen in the sample for low-cardinality columns (--sample)

Exit 0 = no FAIL. Standard library only.
"""
import argparse
import csv
import json
import sys
from collections import Counter

csv.field_size_limit(min(sys.maxsize, 2 ** 31 - 1))


def read_csv(path):
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as fh:
        r = csv.reader(fh)
        header = next(r, [])
        return header, [row for row in r]


def key_orders(value):
    """Return the key order(s) of JSON objects in a value: one tuple per object found."""
    try:
        obj = json.loads(value)
    except (ValueError, TypeError):
        return []
    objs = obj if isinstance(obj, list) else [obj]
    return [tuple(o.keys()) for o in objs if isinstance(o, dict)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("output", help="output.csv to check")
    ap.add_argument("--template", help="blank template CSV whose header is the contract")
    ap.add_argument("--header", help="comma-separated expected header (instead of --template)")
    ap.add_argument("--inputs", help="input CSV that defines the required ids")
    ap.add_argument("--id-col", required=True, help="id column name")
    ap.add_argument("--enum", action="append", default=[], help="col=A|B|C allowed values (repeatable)")
    ap.add_argument("--json-col", action="append", default=[], help="column that must hold valid JSON (repeatable)")
    ap.add_argument("--required", action="append", default=[], help="column that must not be blank (repeatable)")
    ap.add_argument("--all-required", action="store_true", help="no column may be blank")
    ap.add_argument("--sample", help="sample expected output, for key-order and unseen-value warnings")
    a = ap.parse_args()

    fails, warns = [], []
    raw = open(a.output, "rb").read()
    if raw.startswith(b"\xef\xbb\xbf"):
        warns.append("file starts with a UTF-8 BOM")
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as e:
        fails.append("not valid UTF-8: %s" % e)
    crlf, lf = raw.count(b"\r\n"), raw.count(b"\n")
    if crlf and crlf != lf:
        warns.append("mixed line endings (%d CRLF of %d lines)" % (crlf, lf))
    if raw and not raw.endswith(b"\n"):
        warns.append("no trailing newline")

    header, rows = read_csv(a.output)
    expected = None
    if a.template:
        expected = read_csv(a.template)[0]
    elif a.header:
        expected = [h.strip() for h in a.header.split(",")]
    if expected is not None and header != expected:
        fails.append("header %s != expected %s" % (header, expected))
    if a.id_col not in header:
        fails.append("id column %r not in header" % a.id_col)
        report(fails, warns, len(rows))
    idx = {c: i for i, c in enumerate(header)}

    for n, r in enumerate(rows, 2):
        if len(r) != len(header):
            fails.append("line %d: %d fields, expected %d" % (n, len(r), len(header)))
    ids = [r[idx[a.id_col]] if idx[a.id_col] < len(r) else "" for r in rows]
    dups = [k for k, c in Counter(ids).items() if c > 1]
    if dups:
        fails.append("%d duplicated ids, e.g. %s" % (len(dups), dups[:5]))
    if a.inputs:
        ih, irows = read_csv(a.inputs)
        if a.id_col not in ih:
            fails.append("id column %r not in inputs" % a.id_col)
        else:
            want = [r[ih.index(a.id_col)] for r in irows if r]
            missing = sorted(set(want) - set(ids))
            extra = sorted(set(ids) - set(want))
            if missing:
                fails.append("%d input ids missing from output, e.g. %s" % (len(missing), missing[:5]))
            if extra:
                fails.append("%d output ids not in inputs, e.g. %s" % (len(extra), extra[:5]))
            if not missing and not extra and len(rows) != len(want):
                fails.append("row count %d != input count %d" % (len(rows), len(want)))

    def col(name):
        i = idx.get(name)
        if i is None:
            fails.append("column %r not in header" % name)
            return []
        return [(ids[k], r[i] if i < len(r) else "") for k, r in enumerate(rows)]

    for spec in a.enum:
        if "=" not in spec:
            raise SystemExit("bad --enum %r; use col=A|B|C" % spec)
        name, vals = spec.split("=", 1)
        allowed = set(vals.split("|"))
        bad = [(i, v) for i, v in col(name) if v not in allowed]
        if bad:
            fails.append("%s: %d values outside %s, e.g. %s" % (name, len(bad), sorted(allowed), bad[:3]))
    for name in a.json_col:
        bad = []
        for i, v in col(name):
            try:
                json.loads(v)
            except (ValueError, TypeError):
                bad.append(i)
        if bad:
            fails.append("%s: %d values are not valid JSON, e.g. ids %s" % (name, len(bad), bad[:5]))
    req = list(header) if a.all_required else a.required
    for name in req:
        blank = [i for i, v in col(name) if not v.strip()]
        if blank:
            fails.append("%s: %d blank values, e.g. ids %s" % (name, len(blank), blank[:5]))

    if a.sample:
        sh, srows = read_csv(a.sample)
        for name in header:
            if name not in sh or name == a.id_col:
                continue
            si = sh.index(name)
            svals = [r[si] for r in srows if si < len(r)]
            sorders = Counter(o for v in svals for o in key_orders(v))
            if sorders:
                common = sorders.most_common(1)[0][0]
                odd = [i for i, v in col(name) if any(o != common for o in key_orders(v))]
                if odd:
                    warns.append("%s: %d rows use a JSON key order different from the sample's most common %s, e.g. %s"
                                 % (name, len(odd), list(common), odd[:3]))
                if len(sorders) > 1:
                    warns.append("%s: the sample itself uses %d key orders; confirm which the grader expects"
                                 % (name, len(sorders)))
                continue
            seen = set(svals)
            if 0 < len(seen) <= 15 and len(svals) > len(seen):
                unseen = Counter(v for _, v in col(name) if v not in seen)
                if unseen:
                    warns.append("%s: values never seen in the sample: %s" % (name, dict(unseen.most_common(5))))
    report(fails, warns, len(rows))


def report(fails, warns, n):
    for f in fails:
        print("FAIL " + f)
    for w in warns:
        print("WARN " + w)
    print("%s: %d rows, %d FAIL, %d WARN" % ("FAIL" if fails else "PASS", n, len(fails), len(warns)))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
