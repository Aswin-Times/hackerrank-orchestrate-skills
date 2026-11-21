#!/usr/bin/env python3
"""Validate an Orchestrate transcript log (log.txt).

Checks each entry (an entry starts at a line beginning with "## "):
  * exactly one populated tool= line and one populated model= line
    (placeholders, "unknown", generic labels and bare model families fail)
  * optional exact match against --expect-tool / --expect-model
  * required sections in per-turn entries (--require-section, or --profile)
  * timestamps in headings never go backwards (append-only heuristic)
  * no secrets (API keys, tokens, private keys)
  * no progress spam ("processed row 12" style lines)

Exit code 0 when there is no FAIL, 1 otherwise. Standard library only.
"""
import argparse
import json
import re
import sys
from datetime import datetime

GENERIC = {"", "unknown", "ai", "llm", "assistant", "agent", "model", "bot", "n/a", "na",
           "none", "null", "tbd", "todo", "default", "chatbot", "ai assistant"}
MODEL_FAMILIES = {"claude", "gpt", "gemini", "opus", "sonnet", "haiku", "codex", "llama",
                  "mistral", "o1", "o3", "o4", "fable", "chatgpt"}
SECRET_PATTERNS = [
    ("Anthropic key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{10,}")),
    ("OpenAI-style key", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("Private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Bearer token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9_\-\.=]{24,}")),
    ("Key assignment", re.compile(r"(?i)\b(api[_-]?key|secret|password|token)\s*[=:]\s*['\"]?[A-Za-z0-9_\-\/+]{16,}")),
]
SPAM = re.compile(r"(?i)^\s*processed\s+(row|ticket|case|item|request|record)\s*#?\d+")
TS = re.compile(r"\[([0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9:\.]+(?:Z|[+\-][0-9:]+)?)\]")
PROFILES = {
    "generic": {"sections": [], "session_start": False},
    "oct26": {"sections": ["User Prompt", "Agent Response Summary", "Actions", "Context"],
              "session_start": True},
}


def parse_ts(text):
    m = TS.search(text)
    if not m:
        return None
    raw = m.group(1).replace(" ", "T")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None) - (dt.utcoffset() or (dt - dt))
    return dt


def split_entries(lines):
    entries, current = [], None
    for i, line in enumerate(lines, 1):
        if line.startswith("## "):
            current = {"line": i, "title": line[3:].strip(), "body": []}
            entries.append(current)
        elif current is not None:
            current["body"].append((i, line))
    return entries


def field_values(body, key):
    rx = re.compile(r"^\s*[*\-]?\s*" + key + r"\s*=\s*(.*?)\s*$", re.IGNORECASE)
    return [(n, m.group(1)) for n, l in body for m in [rx.match(l)] if m]


def bad_value(value, kind):
    v = value.strip().strip("`\"'")
    low = v.lower()
    if "<" in v and ">" in v:
        return "placeholder value"
    if low in GENERIC:
        return "blank, unknown or generic value"
    if kind == "model" and low in MODEL_FAMILIES:
        return "model family only, need the exact model id"
    if kind == "tool" and re.search(r"(claude|gpt|gemini)-[a-z0-9\-\.]*\d", low):
        return "looks like a model id in tool= (tool is the harness name)"
    return None


def check(path, expect_tool, expect_model, sections, need_session_start, need_tool_model):
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()
    results = []

    def add(level, line, msg):
        results.append({"level": level, "line": line, "message": msg})

    entries = split_entries(lines)
    if not entries:
        add("FAIL", 1, "no entries found (expected headings starting with '## ')")
        return results, 0
    if need_session_start and not any("SESSION START" in e["title"].upper() for e in entries):
        add("FAIL", 1, "no SESSION START entry")

    last_ts = None
    for idx, e in enumerate(entries, 1):
        tag = "entry %d '%s'" % (idx, e["title"][:60])
        if need_tool_model:
            for key in ("tool", "model"):
                vals = field_values(e["body"], key)
                if not vals:
                    add("FAIL", e["line"], "%s: missing %s= line" % (tag, key))
                    continue
                if len(vals) > 1:
                    add("FAIL", vals[1][0], "%s: %d %s= lines, expected exactly one" % (tag, len(vals), key))
                n, v = vals[0]
                why = bad_value(v, key)
                if why:
                    add("FAIL", n, "%s: %s=%r - %s" % (tag, key, v, why))
                expect = expect_tool if key == "tool" else expect_model
                if expect and not why and v.strip().strip("`\"'") != expect:
                    add("FAIL", n, "%s: %s=%r but expected %r" % (tag, key, v, expect))
        is_start = "SESSION START" in e["title"].upper()
        if sections and not is_start:
            text = "\n".join(l for _, l in e["body"]).lower()
            for s in sections:
                if s.lower() not in text:
                    add("FAIL", e["line"], "%s: missing section '%s'" % (tag, s))
        ts = parse_ts(e["title"])
        if ts is None:
            add("WARN", e["line"], "%s: no ISO-8601 timestamp in heading" % tag)
        else:
            if last_ts and ts < last_ts:
                add("WARN", e["line"], "%s: timestamp earlier than previous entry (log rewritten or reordered?)" % tag)
            last_ts = ts
        summary = re.search(r"(?is)agent response summary:\s*(.*?)(?:\n\s*\n[A-Z][^\n]*:|\Z)",
                            "\n".join(l for _, l in e["body"]))
        if summary is not None and len(summary.group(1).split()) < 8:
            add("WARN", e["line"], "%s: response summary under 8 words (be specific: files, decision, evidence)" % tag)

    spam = 0
    for n, line in enumerate(lines, 1):
        for label, rx in SECRET_PATTERNS:
            if rx.search(line):
                add("FAIL", n, "possible secret (%s); redact as [REDACTED]" % label)
                break
        if SPAM.search(line):
            spam += 1
    if spam > 5:
        add("WARN", 1, "%d progress-spam lines ('processed row N'); these score lowest" % spam)
    return results, len(entries)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log", help="path to log.txt")
    ap.add_argument("--expect-tool", help='exact harness name, e.g. "Claude Code"')
    ap.add_argument("--expect-model", help="exact model id, e.g. claude-opus-5-5")
    ap.add_argument("--profile", choices=sorted(PROFILES), default="generic",
                    help="preset of required sections (oct26 = October 2026 format)")
    ap.add_argument("--require-section", action="append", default=[],
                    help="section text each per-turn entry must contain (repeatable)")
    ap.add_argument("--no-tool-model", action="store_true",
                    help="skip tool=/model= checks (editions that do not require them)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    a = ap.parse_args()

    prof = PROFILES[a.profile]
    sections = list(prof["sections"]) + a.require_section
    results, n = check(a.log, a.expect_tool, a.expect_model, sections,
                       prof["session_start"], not a.no_tool_model)
    fails = sum(r["level"] == "FAIL" for r in results)
    warns = sum(r["level"] == "WARN" for r in results)
    if a.json:
        print(json.dumps({"entries": n, "fail": fails, "warn": warns, "results": results}, indent=2))
    else:
        for r in results:
            print("%s line %d: %s" % (r["level"], r["line"], r["message"]))
        print("%s: %d entries, %d FAIL, %d WARN" % ("FAIL" if fails else "PASS", n, fails, warns))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
