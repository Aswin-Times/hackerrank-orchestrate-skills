# hackerrank-orchestrate-skills

Six Claude Code skills for **HackerRank Orchestrate**, the 24-hour AI-agent hackathon scored on code zip (30%), output CSV (30%), AI judge interview (30%) and chat transcript (10%).

With these installed, Claude reads the starter contract, gets `log.txt` logging exactly right, designs and builds the agent in your repo, scores and fixes it with measured one-change loops, prepares you for the judge interview from your own code, and packages a verified submission.

Unofficial; not affiliated with HackerRank. The starter's own `AGENTS.md` and problem statement always take precedence over these skills.

## The skills

| Skill | When | What you get |
|---|---|---|
| [`hr-orchestrate`](skills/hr-orchestrate/SKILL.md) | Start here; when lost; when something fails | Scoring, phase gates, 24-hour clock, failure routing, hard rules, transcript discipline, winner patterns, past editions |
| [`hr-orchestrate-kickoff`](skills/hr-orchestrate-kickoff/SKILL.md) | Starter repo just dropped | `docs/CONTRACT.md`, verified logging, data profile, archetype choice |
| [`hr-orchestrate-build`](skills/hr-orchestrate-build/SKILL.md) | Contract written | `docs/DESIGN.md`, cached + validated LLM client, rule table, guardrails, a valid full `output.csv`, usage report |
| [`hr-orchestrate-test-fix`](skills/hr-orchestrate-test-fix/SKILL.md) | Full CSV exists | Sample scores, error classes, overfitting and determinism checks, change records with KEEP/REVERT verdicts, evaluation report |
| [`hr-orchestrate-interview`](skills/hr-orchestrate-interview/SKILL.md) | From mid-build | `docs/CONSTANTS.md` provenance, drill questions from your code, mock interview |
| [`hr-orchestrate-package`](skills/hr-orchestrate-package/SKILL.md) | Final hours | Readiness checks, clean-run check, `submission/` with code.zip, output.csv, log.txt, manifest |

## Install

Windows (PowerShell):

```powershell
git clone https://github.com/Aswin-Times/hackerrank-orchestrate-skills.git
```

```powershell
.\hackerrank-orchestrate-skills\scripts\install.ps1
```

macOS / Linux:

```sh
git clone https://github.com/Aswin-Times/hackerrank-orchestrate-skills.git
./hackerrank-orchestrate-skills/scripts/install.sh
```

This copies the skills to `~/.claude/skills/`. To install into one challenge repo only, pass `-Project <repo>` (PowerShell) or `--project <repo>` (sh).

The `hr-` prefix keeps these from clashing with other Orchestrate skill sets you may have installed.

## Use during the challenge

1. Clone the starter repo and open Claude Code in it.
2. First message: `Use hr-orchestrate. The starter repo is here; run kickoff.`
3. Follow the gates. Claude keeps `docs/STATUS.md` current, so after a context reset say `Read docs/STATUS.md and continue with hr-orchestrate`.
4. From about hour 14: `Use hr-orchestrate-interview and start CONSTANTS.md`.
5. Final hours: `Use hr-orchestrate-package and check if we are ready to submit`.

You stay in charge: Claude proposes and builds, you decide. Your prompts go into the graded transcript verbatim, so be specific about goals, constraints and what you accept or reject.

## Bundled scripts

Python 3.9+ standard library only; every script takes paths and column names as arguments and embeds no dataset. Run any with `--help`.

| Script | Checks |
|---|---|
| `kickoff/scripts/check_log.py` | Every log entry: one exact `tool=` and `model=`, required sections, timestamps, no secrets, no progress spam |
| `kickoff/scripts/contract_extract.py` | MUST/NEVER lines, CSV headers, required files, allowed values, URLs with file:line; `--diff` between editions |
| `kickoff/scripts/profile_data.py` | Rows, enums, JSON shapes and key orders, header mismatches, id overlap |
| `build/scripts/usage_report.py` | `evaluation/usage_report.md` from a per-call JSONL log (calls, tokens, cost, per request, cache hits) |
| `test-fix/scripts/preflight.py` | Output contract: header, one row per id, enums, JSON validity, blanks, key order vs sample |
| `test-fix/scripts/score_sample.py` | Per-column accuracy, step-level P/R/F1, field-level and sequence accuracy, confusion matrix |
| `test-fix/scripts/rerun_diff.py` | Blast radius between runs; fixed/broken/churned rows and a KEEP/REVERT/REVIEW verdict |
| `test-fix/scripts/coupling_scan.py` | Sample ids or values copied into code (overfitting) |
| `interview/scripts/interview_drill.py` | Judge questions from your constants, thresholds, model settings and ordered tables; CONSTANTS.md coverage |
| `package/scripts/package.py` | Submission readiness, secret scan, builds code.zip / output.csv / log.txt / agent-trace.zip + SHA-256 manifest |

(`kickoff/` is short for `skills/hr-orchestrate-kickoff/`, and so on.)

## How this differs from existing Orchestrate skills

See [RESEARCH.md](RESEARCH.md) for the full survey. In short: Claude builds directly (rather than drafting prompts for another agent); the suite covers the October 2026 contract (repo-root log with `tool=`/`model=` rules, mandatory evaluation and usage reports, agent trace); each skill is short and loads references only when needed; no separate CLI to install; and the defaults come from top-ranked agents (typed model observations, code-owned decisions, cite only what was opened, cached calls).

## Tests

```sh
python -m unittest discover -s tests -v
```

The suite checks every SKILL.md (frontmatter, length, that each linked reference exists) and runs every script against fixtures. CI runs it on Linux and Windows with Python 3.10 and 3.12.

## Credits

Built after studying [NITISH-R-G/hackerrank-orchestrate-skills](https://github.com/NITISH-R-G/hackerrank-orchestrate-skills), [santheesh73/Orchestrate-skill](https://github.com/santheesh73/Orchestrate-skill), the public repos and write-ups of top finishers, and HackerRank's official starter repos. All text and code here are original.
