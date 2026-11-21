#!/usr/bin/env python3
"""Find sample-coupling in agent code: literals copied from the sample data.

Collects values from the sample files (ids and any cell value of at least
--min-len characters, plus whole expected outputs) and searches the code
tree for them verbatim. A hit means the code may special-case a sample row,
which the interview and the hidden evaluation set will expose.

Hits on values that legitimately appear in the problem statement (column
names, enum labels) are expected; pass the statement with --allow-from so
values found there are ignored. Standard library only.
"""
import argparse
import csv
import os
import re
import sys

csv.field_size_limit(min(sys.maxsize, 2 ** 31 - 1))
CODE_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml", ".toml", ".txt", ".md", ".sql", ".go", ".rs", ".java"}
SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__", "dataset", "data", "runs", "cache", ".cache", "submission"}


def sample_values(paths, min_len):
    vals = {}
    for p in paths:
        with open(p, encoding="utf-8-sig", errors="replace", newline="") as fh:
            r = csv.reader(fh)
            header = next(r, [])
            for n, row in enumerate(r, 2):
                for ci, v in enumerate(row):
                    v = v.strip()
                    is_id = ci == 0
                    if (is_id and len(v) >= 3) or len(v) >= min_len:
                        vals.setdefault(v, "%s:%d (%s)" % (os.path.basename(p), n, header[ci] if ci < len(header) else ci))
    return vals


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("code_dir", help="agent code directory (e.g. code/)")
    ap.add_argument("--sample", action="append", required=True, help="sample CSV (inputs and expected outputs; repeatable)")
    ap.add_argument("--min-len", type=int, default=12, help="minimum length of non-id values to look for (default 12)")
    ap.add_argument("--allow-from", action="append", default=[], help="text file whose contents are allowed (e.g. problem_statement.md)")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    vals = sample_values(a.sample, a.min_len)
    allowed = ""
    for p in a.allow_from:
        with open(p, encoding="utf-8", errors="replace") as fh:
            allowed += fh.read()
    vals = {v: src for v, src in vals.items() if v not in allowed}
    pats = {v: re.compile(r"(?<![A-Za-z0-9_])" + re.escape(v) + r"(?![A-Za-z0-9_])") for v in vals}

    hits = 0
    for d, dirs, files in os.walk(a.code_dir):
        dirs[:] = sorted(x for x in dirs if x not in SKIP)
        for f in sorted(files):
            if os.path.splitext(f)[1].lower() not in CODE_EXT:
                continue
            p = os.path.join(d, f)
            try:
                lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
            except OSError:
                continue
            for n, line in enumerate(lines, 1):
                for v, rx in pats.items():
                    if rx.search(line):
                        hits += 1
                        print("HIT %s:%d contains %r from %s" % (p, n, v[:60], vals[v]))
    print("%s: %d hits from %d sample values" % ("WARN" if hits else "PASS", hits, len(vals)))
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
