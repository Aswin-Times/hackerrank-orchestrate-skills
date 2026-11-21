#!/usr/bin/env python3
"""Check submission readiness and build submission/ for HackerRank Orchestrate.

Checks (FAIL blocks the build unless --force):
  * required files exist in the repo (README.md plus each --require)
  * output.csv exists; header matches --template; one row per id in --inputs
  * transcript log exists, is non-empty and has tool= lines (run check_log.py for the full check)
  * no secrets in any file that would go into code.zip, nor in the log
  * no .env files, nested archives, datasets, virtualenvs or caches in code.zip
WARN: code.zip over 50 MB, more than 2000 files, no tests folder, no evaluation folder.

Builds submission/ with code.zip, a copy of output.csv, a copy of the log,
optional agent-trace.zip (--trace-dir, secret-scanned), and MANIFEST.md
listing SHA-256 hashes, zip members and check results.
Standard library only.
"""
import argparse
import csv
import fnmatch
import hashlib
import os
import re
import shutil
import sys
import zipfile

csv.field_size_limit(min(sys.maxsize, 2 ** 31 - 1))

# Left out at any depth.
EXCLUDE_DIRS = {".git", ".venv", "venv", "env", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache",
                ".ruff_cache", ".idea", ".vscode", ".cache", ".claude"}
# Left out only at the repo top level (starter data, run outputs, build products).
EXCLUDE_TOP_DIRS = {"dataset", "data", "support_tickets", "submission", "runs", "cache", "dist", "build",
                    "agent-trace"}
EXCLUDE_FILES = ["*.zip", "*.tar", "*.tar.gz", "*.tgz", "*.7z", "*.rar", ".env", ".env.*", "*.pyc", ".DS_Store",
                 "Thumbs.db", "*.sqlite-journal", "log.txt", "output.csv", "*.pem", "*.key", "id_rsa*"]
KEEP_FILES = [".env.example", ".env.sample", ".env.template"]
SECRET_PATTERNS = [
    ("Anthropic key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{10,}")),
    ("OpenAI-style key", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("Private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Key assignment", re.compile(r"(?i)\b(api[_-]?key|secret|password|token)\s*[=:]\s*['\"][A-Za-z0-9_\-\/+]{16,}['\"]")),
]
TEXT_LIMIT = 5 * 1024 * 1024


def excluded(rel, extra_dirs, extra_files):
    parts = [p for p in rel.replace("\\", "/").split("/") if p not in ("", ".")]
    if any(p in EXCLUDE_DIRS or p in extra_dirs for p in parts[:-1]):
        return True
    if len(parts) > 1 and parts[0] in EXCLUDE_TOP_DIRS:
        return True
    name = parts[-1]
    if name in KEEP_FILES:
        return False
    return any(fnmatch.fnmatch(name, pat) for pat in EXCLUDE_FILES + extra_files)


def collect(root, extra_dirs, extra_files):
    files = []
    for d, dirs, names in os.walk(root):
        rel_d = os.path.relpath(d, root)
        dirs[:] = sorted(x for x in dirs if not excluded(os.path.join(rel_d, x, "f"), extra_dirs, extra_files))
        for n in sorted(names):
            rel = os.path.normpath(os.path.join(rel_d, n)) if rel_d != "." else n
            if not excluded(rel, extra_dirs, extra_files):
                files.append(rel.replace("\\", "/"))
    return files


def scan_secrets(path):
    hits = []
    try:
        if os.path.getsize(path) > TEXT_LIMIT:
            return hits
        with open(path, encoding="utf-8", errors="ignore") as fh:
            for n, line in enumerate(fh, 1):
                for label, rx in SECRET_PATTERNS:
                    if rx.search(line):
                        hits.append((n, label))
                        break
    except OSError:
        pass
    return hits


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path):
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as fh:
        r = csv.reader(fh)
        return next(r, []), [row for row in r if row]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="challenge repo root (default .)")
    ap.add_argument("--output", default="output.csv", help="final output CSV, relative to root")
    ap.add_argument("--log", default="log.txt", help="transcript log path (absolute or relative to root)")
    ap.add_argument("--template", help="blank output template CSV (header contract)")
    ap.add_argument("--inputs", help="evaluation input CSV (required ids)")
    ap.add_argument("--id-col", help="id column for --inputs")
    ap.add_argument("--require", action="append", default=[], help="file that must exist in code.zip (repeatable)")
    ap.add_argument("--exclude-dir", action="append", default=[], help="extra directory name to leave out")
    ap.add_argument("--exclude", action="append", default=[], help="extra file glob to leave out")
    ap.add_argument("--trace-dir", help="staged agent-trace folder to zip as agent-trace.zip (secret-scanned)")
    ap.add_argument("--out-dir", default="submission", help="where to build (default submission/ under root)")
    ap.add_argument("--check-only", action="store_true", help="run checks, build nothing")
    ap.add_argument("--force", action="store_true", help="build even with FAIL results")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    root = os.path.abspath(a.root)
    fails, warns = [], []
    files = collect(root, set(a.exclude_dir), a.exclude)
    fileset = set(files)

    for req in ["README.md"] + a.require:
        if req.replace("\\", "/") not in fileset:
            fails.append("required file missing from code.zip: %s" % req)
    if not any(f.startswith(("tests/", "test/", "code/tests/")) for f in files):
        warns.append("no tests/ folder")
    if not any("evaluation/" in f for f in files):
        warns.append("no evaluation/ folder")
    total = sum(os.path.getsize(os.path.join(root, f)) for f in files)
    if total > 50 * 1024 * 1024:
        warns.append("code.zip contents are %.1f MB" % (total / 1048576.0))
    if len(files) > 2000:
        warns.append("%d files in code.zip; check for caches or data" % len(files))
    for f in files:
        for n, label in scan_secrets(os.path.join(root, f)):
            fails.append("possible secret in %s:%d (%s)" % (f, n, label))

    out_path = os.path.join(root, a.output)
    if not os.path.isfile(out_path):
        fails.append("output CSV not found: %s" % a.output)
    else:
        header, rows = read_csv(out_path)
        if a.template:
            th = read_csv(a.template)[0]
            if header != th:
                fails.append("output header %s != template %s" % (header, th))
        if a.inputs:
            if not a.id_col:
                fails.append("--inputs needs --id-col")
            else:
                ih, irows = read_csv(a.inputs)
                if a.id_col not in ih or a.id_col not in header:
                    fails.append("id column %r missing from inputs or output" % a.id_col)
                else:
                    want = {r[ih.index(a.id_col)] for r in irows}
                    got = [r[header.index(a.id_col)] for r in rows if len(r) > header.index(a.id_col)]
                    if set(got) != want or len(got) != len(want):
                        fails.append("output rows do not match input ids: %d rows, %d unique, %d inputs, %d missing"
                                     % (len(got), len(set(got)), len(want), len(want - set(got))))

    log_path = a.log if os.path.isabs(a.log) else os.path.join(root, a.log)
    if not os.path.isfile(log_path) or os.path.getsize(log_path) == 0:
        fails.append("transcript log missing or empty: %s" % log_path)
    else:
        text = open(log_path, encoding="utf-8", errors="replace").read()
        if not re.search(r"(?im)^\s*[*\-]?\s*tool\s*=\s*\S", text):
            warns.append("log has no tool= lines; check the edition's required format with check_log.py")
        for n, label in scan_secrets(log_path):
            fails.append("possible secret in log line %d (%s)" % (n, label))

    trace_files = []
    if a.trace_dir:
        if not os.path.isdir(a.trace_dir):
            fails.append("trace dir not found: %s" % a.trace_dir)
        else:
            for d, _, names in os.walk(a.trace_dir):
                for n in sorted(names):
                    p = os.path.join(d, n)
                    trace_files.append(p)
                    if n in ("auth.json", ".credentials.json", "credentials.json", "config.toml", "settings.json", "settings.local.json"):
                        fails.append("trace contains a settings or credential file: %s" % p)
                    for ln, label in scan_secrets(p):
                        fails.append("possible secret in trace %s:%d (%s)" % (p, ln, label))

    for f in fails:
        print("FAIL " + f)
    for w in warns:
        print("WARN " + w)
    ready = not fails
    print("%s: %d files for code.zip (%.1f MB), %d FAIL, %d WARN"
          % ("READY" if ready else "NOT READY", len(files), total / 1048576.0, len(fails), len(warns)))
    if a.check_only or (fails and not a.force):
        sys.exit(0 if ready else 1)

    out_dir = os.path.join(root, a.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    zpath = os.path.join(out_dir, "code.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(os.path.join(root, f), f)
    built = [("code.zip", zpath)]
    if os.path.isfile(out_path):
        dst = os.path.join(out_dir, os.path.basename(a.output))
        shutil.copyfile(out_path, dst)
        built.append((os.path.basename(a.output), dst))
    if os.path.isfile(log_path):
        dst = os.path.join(out_dir, os.path.basename(log_path))
        shutil.copyfile(log_path, dst)
        built.append((os.path.basename(log_path), dst))
    if trace_files:
        tpath = os.path.join(out_dir, "agent-trace.zip")
        base = os.path.dirname(os.path.abspath(a.trace_dir))
        with zipfile.ZipFile(tpath, "w", zipfile.ZIP_DEFLATED) as z:
            for p in trace_files:
                z.write(p, os.path.relpath(os.path.abspath(p), base))
        built.append(("agent-trace.zip", tpath))

    man = ["# Submission manifest", "", "Status: %s" % ("READY" if ready else "NOT READY (built with --force)"), "",
           "| Artifact | Bytes | SHA-256 |", "|---|---|---|"]
    man += ["| %s | %d | `%s` |" % (n, os.path.getsize(p), sha256(p)) for n, p in built]
    man += ["", "## Checks", ""] + ["- FAIL " + f for f in fails] + ["- WARN " + w for w in warns]
    if not fails and not warns:
        man.append("- all checks passed")
    man += ["", "## code.zip members (%d)" % len(files), ""] + ["- " + f for f in files]
    with open(os.path.join(out_dir, "MANIFEST.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(man) + "\n")
    for n, p in built:
        print("built %s" % os.path.relpath(p, root))
    print("wrote %s" % os.path.relpath(os.path.join(out_dir, "MANIFEST.md"), root))
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
