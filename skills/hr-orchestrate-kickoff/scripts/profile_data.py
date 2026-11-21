#!/usr/bin/env python3
"""Profile Orchestrate CSV files before designing anything.

For each CSV: row count, columns, blanks per column, distinct counts,
low-cardinality columns (likely enums) with value counts, JSON-looking
columns with their key orders, numeric columns with min/max, max length.
Across files: header comparison for files with overlapping columns, and
id overlap / duplicates when --id-col is given.
Standard library only.
"""
import argparse
import csv
import re
import json
import os
import sys
from collections import Counter

csv.field_size_limit(min(sys.maxsize, 2 ** 31 - 1))
DATEISH = re.compile(r"^\d{4}-\d{2}-\d{2}([T ][0-9:\.]+Z?)?$")


def read(path):
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as fh:
        r = csv.reader(fh)
        header = next(r, [])
        rows = [row for row in r]
    return header, rows


def as_float(v):
    try:
        return float(v)
    except ValueError:
        return None


def json_shape(v):
    try:
        obj = json.loads(v)
    except (ValueError, TypeError):
        return None
    if isinstance(obj, dict):
        return "object{" + ",".join(obj.keys()) + "}"
    if isinstance(obj, list):
        if obj and isinstance(obj[0], dict):
            return "list[object{" + ",".join(obj[0].keys()) + "}] len=%d" % len(obj)
        return "list len=%d" % len(obj)
    return type(obj).__name__


def profile(path, enum_max, show, label):
    header, rows = read(path)
    out = ["## %s" % label, "", "- rows: %d" % len(rows), "- columns (%d): `%s`" % (len(header), ",".join(header))]
    bad = [i + 2 for i, r in enumerate(rows) if len(r) != len(header)]
    if bad:
        out.append("- WARNING: %d rows with wrong field count (first at line %d)" % (len(bad), bad[0]))
    out.append("")
    for ci, col in enumerate(header):
        vals = [r[ci] if ci < len(r) else "" for r in rows]
        blanks = sum(1 for v in vals if not v.strip())
        nonblank = [v for v in vals if v.strip()]
        distinct = Counter(nonblank)
        desc = ["blank=%d" % blanks, "distinct=%d" % len(distinct)]
        if nonblank:
            desc.append("maxlen=%d" % max(len(v) for v in nonblank))
        nums = [as_float(v) for v in nonblank]
        if nonblank and all(x is not None for x in nums):
            desc.append("numeric min=%g max=%g" % (min(nums), max(nums)))
        line = "- `%s`: %s" % (col, ", ".join(desc))
        js = [v for v in nonblank if v.lstrip()[:1] in "[{"]
        if js and len(js) >= 0.5 * len(nonblank):
            shapes = Counter(s for s in (json_shape(v) for v in js) if s)
            invalid = len(js) - sum(shapes.values())
            line += "\n  - JSON column (%d invalid). Shapes: %s" % (
                invalid, "; ".join("%s x%d" % (s, c) for s, c in shapes.most_common(4)))
        elif (0 < len(distinct) <= enum_max and len(nonblank) > len(distinct)
              and not all(DATEISH.match(k) for k in distinct)):
            line += "\n  - likely enum: " + ", ".join("`%s` x%d" % (k, c) for k, c in distinct.most_common())
        out.append(line)
    if show:
        out += ["", "First %d rows:" % show, "", "```"]
        out += [",".join(r) for r in rows[:show]]
        out.append("```")
    return header, rows, out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="+", help="CSV files (sample inputs, sample outputs, eval inputs, template)")
    ap.add_argument("--id-col", help="id column used to compare files (overlap, duplicates)")
    ap.add_argument("--enum-max", type=int, default=15, help="max distinct values to report as enum (default 15)")
    ap.add_argument("--show", type=int, default=0, help="also print the first N rows of each file")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    for p in a.csv:
        if not os.path.isfile(p):
            ap.error("not a file: %s" % p)
    base = os.path.commonpath([os.path.abspath(p) for p in a.csv]) if len(a.csv) > 1 else ""
    if base and os.path.isfile(base):
        base = os.path.dirname(base)
    data = {}
    for p in a.csv:
        label = os.path.relpath(os.path.abspath(p), base) if base else p
        header, rows, out = profile(p, a.enum_max, a.show, label)
        data[label] = (header, rows)
        print("\n".join(out) + "\n")

    print("## Header comparison\n")
    paths = list(data)
    any_pair = False
    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            h1, h2 = data[paths[i]][0], data[paths[j]][0]
            common = set(h1) & set(h2)
            if not common or len(common) < 0.5 * min(len(h1), len(h2)):
                continue
            any_pair = True
            if h1 == h2:
                verdict = "identical header and order"
            elif set(h1) == set(h2):
                verdict = "same columns, DIFFERENT ORDER"
            else:
                verdict = "only in first: %s; only in second: %s" % (
                    sorted(set(h1) - set(h2)) or "-", sorted(set(h2) - set(h1)) or "-")
            print("- %s vs %s: %s" % (paths[i], paths[j], verdict))
    if not any_pair:
        print("- no files with overlapping headers")

    if a.id_col:
        print("\n## Ids (%s)\n" % a.id_col)
        ids = {}
        for p, (h, rows) in data.items():
            if a.id_col not in h:
                print("- %s: no column %s" % (p, a.id_col))
                continue
            ci = h.index(a.id_col)
            col = [r[ci] for r in rows if ci < len(r)]
            dup = [k for k, c in Counter(col).items() if c > 1]
            ids[p] = set(col)
            print("- %s: %d ids, %d duplicated%s" % (p, len(set(col)), len(dup),
                                                     (" e.g. %s" % dup[:3]) if dup else ""))
        keys = list(ids)
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                ov = ids[keys[i]] & ids[keys[j]]
                print("- overlap %s & %s: %d" % (keys[i], keys[j], len(ov)))


if __name__ == "__main__":
    main()
