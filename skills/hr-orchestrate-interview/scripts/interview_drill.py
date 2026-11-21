#!/usr/bin/env python3
"""Generate AI-judge drill questions from your own code.

Finds, with file:line:
  * module-level constants (NAME = literal)
  * numeric thresholds in comparisons (x >= 0.8, count > 3)
  * model ids and model settings (temperature, max_tokens, timeout, retries, workers)
  * ordered tables (names containing ORDER, PRIORITY, RULES, TIEBREAK, PRECEDENCE)
Python files are parsed with ast; other languages use regexes.

With --constants CONSTANTS.md, each finding is marked COVERED (its name or
value appears in a table row there) or MISSING. Missing constants are the
questions you are least ready for. A general bank of judge questions
follows; --shuffle --seed N --limit K gives a rehearsal set.
Exit code 1 when --strict and any constant is MISSING. Standard library only.
"""
import argparse
import ast
import os
import random
import re
import sys

SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__", "tests", "test", "runs", "cache", "dataset", "submission"}
SETTINGS = re.compile(r"(?i)(temperature|max_tokens|top_p|timeout|retries|max_retries|workers|concurrency|batch_size|top_k|chunk_size|overlap|k)$")
ORDERED = re.compile(r"(?i)(order|priority|rules|tiebreak|tie_break|precedence|ranking)")
MODEL = re.compile(r"""['"]((?:claude|gpt|gemini|text-embedding|embed|rerank|voyage|llama|mistral)-[A-Za-z0-9._\-]+|o\d(?:-[A-Za-z0-9._\-]+)?)['"]""")
REGEX_CONST = re.compile(r"^\s*(?:export\s+)?(?:const\s+|let\s+|var\s+|final\s+)?([A-Z][A-Z0-9_]{2,})\s*[:=]\s*(-?[0-9][0-9_.]*|['\"][^'\"]{1,80}['\"])")
REGEX_CMP = re.compile(r"([A-Za-z_][\w.\[\]'\"]*)\s*(<=|>=|<|>|==)\s*(-?\d+(?:\.\d+)?)\b")
TRIVIAL = {0, 1, -1, 2, 100}

GENERAL = [
    ("architecture", "Walk me through the pipeline from one input row to its output row. Where exactly does the model run and where does code decide?"),
    ("architecture", "Why this architecture rather than a single prompt that returns the answer, or a multi-agent setup?"),
    ("tools", "What tools or retrieval does the agent have, and why that set? What did you leave out?"),
    ("prompts", "Show me the main prompt. What does the output schema force, and what happens when the model returns invalid output?"),
    ("numbers", "Pick the most important threshold in your code. Where did the value come from, and what happens if it moves by 20%?"),
    ("evaluation", "How do you know it works on the hidden set and not just the sample? What did you do about overfitting?"),
    ("evaluation", "What are your sample metrics, how were they computed, and what is the run-to-run noise?"),
    ("evaluation", "Describe a change you tried that made things worse. How did you detect it and what did you do?"),
    ("robustness", "What happens when the API times out halfway through the run, or one input file is corrupt?"),
    ("security", "How does your agent handle prompt injection inside the input data, documents or images? Show me a test."),
    ("security", "Where are secrets kept, and how did you make sure none are in the zip or the transcript?"),
    ("cost", "How many model calls and tokens per row, what does a full run cost, and how would you cut that in half?"),
    ("determinism", "If I run your code twice, do I get the same CSV? Exactly what is and is not deterministic?"),
    ("limits", "What kinds of input will your agent get wrong today? What would you build next with one more day?"),
    ("ownership", "Where did you overrule the AI coding assistant, and why?"),
    ("ownership", "Which part of the code are you least confident in, and why?"),
]


def lit(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, str)) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant) \
            and isinstance(node.operand.value, (int, float)):
        return -node.operand.value
    return None


def scan_python(path, src, out):
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return scan_regex(path, src, out)
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name) and t.id.isupper() and node.value is not None:
                    v = lit(node.value)
                    if v is not None and not (isinstance(v, str) and len(v) > 80):
                        out.append(("constant", path, node.lineno, t.id, repr(v)))
                    elif isinstance(node.value, (ast.List, ast.Tuple, ast.Dict)) and ORDERED.search(t.id):
                        out.append(("ordered", path, node.lineno, t.id, "%d items" % len(getattr(node.value, "elts", getattr(node.value, "keys", [])))))
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for comp in [node.left] + list(node.comparators):
                v = lit(comp)
                if isinstance(v, (int, float)) and v not in TRIVIAL:
                    out.append(("threshold", path, node.lineno, ast.unparse(node)[:80] if hasattr(ast, "unparse") else "comparison", repr(v)))
        if isinstance(node, ast.keyword) and node.arg and SETTINGS.match(node.arg):
            v = lit(node.value)
            if v is not None:
                out.append(("setting", path, node.lineno, node.arg, repr(v)))
    for n, line in enumerate(src.splitlines(), 1):
        for m in MODEL.finditer(line):
            out.append(("model", path, n, "model id", m.group(1)))


def scan_regex(path, src, out):
    for n, line in enumerate(src.splitlines(), 1):
        m = REGEX_CONST.match(line)
        if m:
            out.append(("constant", path, n, m.group(1), m.group(2)))
        for c in REGEX_CMP.finditer(line):
            try:
                v = float(c.group(3))
            except ValueError:
                continue
            if v not in TRIVIAL:
                out.append(("threshold", path, n, c.group(0)[:80], c.group(3)))
        for mm in MODEL.finditer(line):
            out.append(("model", path, n, "model id", mm.group(1)))


def question(kind, name, value, loc):
    if kind == "constant":
        return "Why is `%s = %s` (%s)? Where did that value come from, did you test alternatives, and what breaks if it changes?" % (name, value, loc)
    if kind == "threshold":
        return "Explain the threshold in `%s` (%s). Why %s, and what happens to rows just either side of it?" % (name, loc, value)
    if kind == "setting":
        return "Why `%s=%s` (%s)? What did you trade off?" % (name, value, loc)
    if kind == "model":
        return "Why model `%s` (%s) for this step? What did you compare it against, and at what cost?" % (value, loc)
    if kind == "ordered":
        return "Justify the order of `%s` (%s, %s). What happens if two entries are swapped? Is there a test that proves the order?" % (name, loc, value)
    return name


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("code_dir")
    ap.add_argument("--constants", help="docs/CONSTANTS.md to check coverage against")
    ap.add_argument("--limit", type=int, default=0, help="max code questions (default all)")
    ap.add_argument("--shuffle", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-general", action="store_true", help="omit the general question bank")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any constant is missing from CONSTANTS.md")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    found = []
    for d, dirs, files in os.walk(a.code_dir):
        dirs[:] = sorted(x for x in dirs if x not in SKIP)
        for f in sorted(files):
            ext = os.path.splitext(f)[1].lower()
            if ext not in {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".kt"}:
                continue
            p = os.path.join(d, f)
            src = open(p, encoding="utf-8", errors="replace").read()
            rel = os.path.relpath(p, a.code_dir)
            (scan_python if ext == ".py" else scan_regex)(rel, src, found)
    seen, items = set(), []
    for kind, path, line, name, value in found:
        k = (kind, path, line, name)
        if k not in seen:
            seen.add(k)
            items.append((kind, path, line, name, value))

    const_text = ""
    if a.constants:
        const_text = "\n".join(l for l in open(a.constants, encoding="utf-8", errors="replace").read().splitlines()
                               if l.strip().startswith("|"))
    missing = 0
    rows = []
    for kind, path, line, name, value in items:
        status = ""
        if a.constants:
            v = str(value).strip("'\"")
            ok = (kind in ("constant", "ordered") and re.search(r"\b%s\b" % re.escape(name), const_text)) or \
                 (kind != "constant" and v and v in const_text)
            status = "COVERED" if ok else "MISSING"
            if not ok and kind in ("constant", "threshold", "setting", "model"):
                missing += 1
        rows.append((status, kind, "%s:%d" % (path, line), question(kind, name, value, "%s:%d" % (path, line))))
    if a.shuffle:
        random.Random(a.seed).shuffle(rows)
    else:
        rows.sort(key=lambda r: (r[0] != "MISSING", r[1], r[2]))
    if a.limit:
        rows = rows[: a.limit]

    print("# Interview drill\n")
    print("Found %d code items in %s%s.\n" % (len(items), a.code_dir,
                                             (", %d not covered by %s" % (missing, a.constants)) if a.constants else ""))
    print("## From your code\n")
    for i, (status, kind, loc, q) in enumerate(rows, 1):
        print("%d. %s[%s] %s" % (i, ("**%s** " % status) if status else "", kind, q))
    if not a.no_general:
        bank = list(GENERAL)
        if a.shuffle:
            random.Random(a.seed + 1).shuffle(bank)
        print("\n## General judge questions\n")
        for i, (topic, q) in enumerate(bank, 1):
            print("%d. [%s] %s" % (i, topic, q))
    sys.exit(1 if (a.strict and missing) else 0)


if __name__ == "__main__":
    main()
