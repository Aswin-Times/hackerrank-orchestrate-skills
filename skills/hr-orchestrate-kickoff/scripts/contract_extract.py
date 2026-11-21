#!/usr/bin/env python3
"""Extract a draft output contract from an Orchestrate starter repo.

Scans Markdown/text files (skipping dataset folders, .git, node_modules, venvs)
and prints, with file:line:
  * rule lines (must / never / only / exactly / required / always ...)
  * required files and paths mentioned in backticks
  * candidate CSV headers inside code blocks, plus first lines of CSV files
    whose names suggest outputs or templates
  * candidate allowed-value lists (lines with 3+ backticked tokens)
  * URLs

This is a heuristic starting point for docs/CONTRACT.md, not a substitute
for reading the statement. With --diff OLD NEW it shows rule lines added or
removed between two starter repos (for example two editions).
Standard library only.
"""
import argparse
import os
import re
import sys

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dataset", "data",
             "support_tickets", "evidence", "corpus", "submission", "dist", "build"}
TEXT_EXT = {".md", ".txt", ".mdc", ".rst"}
RULE = re.compile(r"(?i)\b(must(?: not)?|never|do not|don't|required?|requires|only|exactly|always|"
                  r"shall|forbidden|prohibited|mandatory|invalid|at least|no more than)\b")
PATH = re.compile(r"`([A-Za-z0-9_\-./\\]+\.(?:csv|md|txt|zip|json|py|jsonl|yaml|yml|toml))`")
URL = re.compile(r"https?://[^\s)>\]`'\"]+")
TICKS = re.compile(r"`([^`\n]{1,60})`")
HEADER = re.compile(r"^[A-Za-z_][A-Za-z0-9_ ]*(,[A-Za-z_][A-Za-z0-9_ ]*){1,}$")
CSV_HINT = re.compile(r"(?i)(output|sample|template|expected|submission)")


def walk(root, exts):
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x.lower() not in SKIP_DIRS and not x.startswith("."))
        for f in sorted(files):
            if os.path.splitext(f)[1].lower() in exts:
                yield os.path.join(d, f)


def csv_headers(root):
    out = []
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in {".git", "node_modules", ".venv", "venv"})
        for f in sorted(files):
            if f.lower().endswith(".csv") and CSV_HINT.search(f):
                p = os.path.join(d, f)
                try:
                    with open(p, encoding="utf-8-sig", errors="replace") as fh:
                        out.append((os.path.relpath(p, root), fh.readline().strip()))
                except OSError:
                    pass
    return out


def extract(root):
    found = {"rules": [], "paths": {}, "headers": [], "enums": [], "urls": {}}
    for p in walk(root, TEXT_EXT):
        rel = os.path.relpath(p, root)
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()
        except OSError:
            continue
        in_code = False
        for n, raw in enumerate(lines, 1):
            line = raw.strip()
            if line.startswith("```"):
                in_code = not in_code
                continue
            loc = "%s:%d" % (rel, n)
            if in_code and HEADER.match(line):
                found["headers"].append((loc, line))
                continue
            if not line:
                continue
            if RULE.search(line) and not in_code:
                found["rules"].append((loc, line))
            for m in PATH.finditer(line):
                found["paths"].setdefault(m.group(1), loc)
            for m in URL.finditer(line):
                found["urls"].setdefault(m.group(0).rstrip(".,;"), loc)
            ticks = TICKS.findall(line)
            if len(ticks) >= 3 and not in_code:
                found["enums"].append((loc, ", ".join(ticks)))
    found["csv"] = csv_headers(root)
    return found


def clip(s, n=220):
    return s if len(s) <= n else s[: n - 3] + "..."


def report(root):
    f = extract(root)
    out = ["# Contract draft for %s" % os.path.abspath(root), "",
           "Heuristic extraction. Verify every line against the source before relying on it.", ""]
    out += ["## Candidate CSV headers (code blocks)", ""]
    out += ["- `%s` (%s)" % (h, loc) for loc, h in f["headers"]] or ["- none found"]
    out += ["", "## CSV files that look like outputs or templates (first line)", ""]
    out += ["- %s: `%s`" % (p, h) for p, h in f["csv"]] or ["- none found"]
    out += ["", "## Files and paths mentioned", ""]
    out += ["- `%s` (first at %s)" % (p, loc) for p, loc in sorted(f["paths"].items())] or ["- none"]
    out += ["", "## Candidate allowed-value lists", ""]
    out += ["- %s: %s" % (loc, clip(t)) for loc, t in f["enums"]] or ["- none"]
    out += ["", "## Rule lines (%d)" % len(f["rules"]), ""]
    out += ["- %s: %s" % (loc, clip(t)) for loc, t in f["rules"]] or ["- none"]
    out += ["", "## URLs", ""]
    out += ["- %s (%s)" % (u, loc) for u, loc in sorted(f["urls"].items())] or ["- none"]
    return "\n".join(out) + "\n"


def diff(old, new):
    norm = lambda s: re.sub(r"\s+", " ", s.lower()).strip()
    a = {norm(t): (loc, t) for loc, t in extract(old)["rules"]}
    b = {norm(t): (loc, t) for loc, t in extract(new)["rules"]}
    out = ["# Rule diff", "", "## Added in %s" % new, ""]
    out += ["- %s: %s" % (b[k][0], clip(b[k][1])) for k in sorted(set(b) - set(a))] or ["- none"]
    out += ["", "## Removed since %s" % old, ""]
    out += ["- %s: %s" % (a[k][0], clip(a[k][1])) for k in sorted(set(a) - set(b))] or ["- none"]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("starter", nargs="?", help="starter repo directory")
    ap.add_argument("--diff", nargs=2, metavar=("OLD", "NEW"), help="compare rule lines of two starters")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if a.diff:
        sys.stdout.write(diff(*a.diff))
    elif a.starter:
        if not os.path.isdir(a.starter):
            ap.error("not a directory: %s" % a.starter)
        sys.stdout.write(report(a.starter))
    else:
        ap.error("give a starter directory or --diff OLD NEW")


if __name__ == "__main__":
    main()
