#!/usr/bin/env python3
"""Regenerate the README terminal screenshots from real script runs on examples/demo.

Each screenshot is an SVG "terminal window" holding the actual output of one
command, so the images never drift from what the scripts really print.
Run from anywhere:  python scripts/make_screenshots.py
Standard library only.
"""
import os
import re
import subprocess
import sys
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(ROOT, "examples", "demo")
OUT = os.path.join(ROOT, "assets", "screenshots")
S = os.path.join(ROOT, "skills")

SHOTS = [
    ("check-log", "Transcript check: catches a placeholder tool=, a model family, a leaked key, reordered entries",
     "check_log.py log_bad.txt --expect-tool \"Claude Code\" --expect-model claude-opus-5-5",
     [os.path.join(S, "hr-orchestrate-kickoff", "scripts", "check_log.py"), "log_bad.txt",
      "--expect-tool", "Claude Code", "--expect-model", "claude-opus-5-5"]),
    ("preflight", "Output contract check before submitting",
     "preflight.py runs/output_bad.csv --template dataset/output.csv --inputs dataset/requests.csv \\\n    --id-col request_id --enum \"decision=APPROVE|DENY|ESCALATE\" --all-required",
     [os.path.join(S, "hr-orchestrate-test-fix", "scripts", "preflight.py"), "runs/output_bad.csv",
      "--template", "dataset/output.csv", "--inputs", "dataset/requests.csv", "--id-col", "request_id",
      "--enum", "decision=APPROVE|DENY|ESCALATE", "--all-required"]),
    ("score", "Scoring a run against the public sample",
     "score_sample.py runs/baseline_sample.csv dataset/sample_output.csv --id-col request_id --confusion decision",
     [os.path.join(S, "hr-orchestrate-test-fix", "scripts", "score_sample.py"), "runs/baseline_sample.csv",
      "dataset/sample_output.csv", "--id-col", "request_id", "--confusion", "decision"]),
    ("rerun-diff", "One change, whole-output diff, KEEP/REVERT verdict",
     "rerun_diff.py runs/baseline_sample.csv runs/candidate_sample.csv --id-col request_id \\\n    --expected dataset/sample_output.csv",
     [os.path.join(S, "hr-orchestrate-test-fix", "scripts", "rerun_diff.py"), "runs/baseline_sample.csv",
      "runs/candidate_sample.csv", "--id-col", "request_id", "--expected", "dataset/sample_output.csv"]),
    ("interview-drill", "Judge questions generated from your own code",
     "interview_drill.py code --constants docs/CONSTANTS.md --no-general",
     [os.path.join(S, "hr-orchestrate-interview", "scripts", "interview_drill.py"), "code",
      "--constants", "docs/CONSTANTS.md", "--no-general"]),
]

BG, BAR, FG, DIM = "#0d1117", "#161b22", "#e6edf3", "#8b949e"
COLORS = [("FAIL", "#ff7b72"), ("NOT READY", "#ff7b72"), ("REVERT", "#ff7b72"), ("**MISSING**", "#ff7b72"),
          ("WARN", "#e3b341"), ("HIT", "#e3b341"), ("REVIEW", "#e3b341"),
          ("PASS", "#3fb950"), ("READY", "#3fb950"), ("VERDICT: KEEP", "#3fb950"), ("**COVERED**", "#3fb950"),
          ("fixed:", "#3fb950"), ("broken:", "#ff7b72")]
CHAR_W, LINE_H, PAD, MAX_COLS, MAX_LINES = 8.4, 19, 18, 112, 26


def color_for(line):
    s = line.lstrip()
    if re.match(r"(fixed|broken|churned):\s+0\b", s):
        return DIM
    for prefix, col in COLORS:
        if (prefix in s) if prefix.startswith("**") else s.startswith(prefix):
            return col
    if s.startswith("#"):
        return "#79c0ff"
    return FG


def wrap(text):
    """Wrap long lines at word boundaries, indenting continuation lines."""
    out = []
    for line in text.splitlines():
        line = line.replace("\t", "    ")
        indent = " " * (len(line) - len(line.lstrip()) + 4)
        while len(line) > MAX_COLS:
            cut = line.rfind(" ", len(indent), MAX_COLS)
            if cut <= len(indent):
                cut = MAX_COLS
            out.append(line[:cut].rstrip())
            line = indent + line[cut:].lstrip()
        out.append(line)
    return out


def render(title, cmd, output):
    cmd_lines = ["$ python " + cmd.split("\n")[0]] + cmd.split("\n")[1:]
    body = []
    for l in wrap(output.rstrip()):
        if l.strip() or (body and body[-1].strip()):
            body.append(l)
    if len(body) > MAX_LINES:
        body = body[:MAX_LINES - 1] + ["..."]
    lines = [(l, "#d2a8ff") for l in wrap("\n".join(cmd_lines))] + [("", FG)] + [(l, color_for(l)) for l in body]
    cols = max(len(l) for l, _ in lines + [(title, "")])
    width = int(max(720, cols * CHAR_W + 2 * PAD))
    height = int(44 + PAD + len(lines) * LINE_H + PAD)
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-label="%s">'
        % (width, height, width, height, escape(title, {'"': "&quot;"})),
        '<rect width="%d" height="%d" rx="10" fill="%s"/>' % (width, height, BG),
        '<path d="M0 10a10 10 0 0 1 10-10h%d a10 10 0 0 1 10 10v26H0z" fill="%s"/>' % (width - 20, BAR),
        '<circle cx="20" cy="18" r="6" fill="#ff5f57"/><circle cx="40" cy="18" r="6" fill="#febc2e"/>'
        '<circle cx="60" cy="18" r="6" fill="#28c840"/>',
        '<text x="%d" y="23" fill="%s" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="13" '
        'text-anchor="middle">%s</text>' % (width // 2, DIM, escape(title)),
        '<g font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, \'Liberation Mono\', monospace" font-size="14">',
    ]
    y = 44 + PAD + 12
    for text, col in lines:
        if text:
            parts.append('<text x="%d" y="%d" fill="%s" xml:space="preserve">%s</text>' % (PAD, y, col, escape(text)))
        y += LINE_H
    parts += ["</g>", "</svg>"]
    return "\n".join(parts) + "\n"


def main():
    os.makedirs(OUT, exist_ok=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    for name, title, shown, argv in SHOTS:
        p = subprocess.run([sys.executable] + argv, cwd=DEMO, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        out = (p.stdout + p.stderr).replace(ROOT + os.sep, "").replace("\\", "/")
        path = os.path.join(OUT, name + ".svg")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render(title, shown, out))
        print("wrote %s (exit %d, %d lines)" % (os.path.relpath(path, ROOT), p.returncode, len(out.splitlines())))


if __name__ == "__main__":
    main()
