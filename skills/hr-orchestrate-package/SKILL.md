---
name: hr-orchestrate-package
description: HackerRank Orchestrate final gate and packaging - verify the repo against the edition's exact submission rules (output.csv header and row coverage, required README and evaluation reports, transcript log format, no secrets, no dataset or caches in the zip), do a clean run from an empty checkout, then build submission/ with code.zip, output.csv, log.txt, optional agent-trace.zip and a SHA-256 manifest. Use in the final hours, whenever someone asks "are we ready to submit?", and before uploading anything.
---

# Orchestrate package and submit (hours 20-24)

Goal: every artifact the edition asks for, verified, with time to spare. No new features from here on. `$P` means this skill's directory; sibling skills are referenced by name.

## Step 1. Re-read the submission rules

Open `docs/CONTRACT.md` and re-read the submission section of `AGENTS.md` and `problem_statement.md` (rules change between editions). List the artifacts, required files inside the zip, exclusions, the log path, and the submission URL if one is given. If AGENTS.md says to give an exact URL when asked where to submit, give exactly that URL.

## Step 2. Freeze and final run

1. Freeze code. Record the commit or a hash of `code/`.
2. Run the full evaluation input once more with the frozen code. This run produces the final `output.csv` and its `run_id`.
3. Regenerate `evaluation/usage_report.md` from that run id (`hr-orchestrate-build/scripts/usage_report.py`) and update `evaluation/evaluation_report.md` if numbers changed.
4. Compare with the banked output: `hr-orchestrate-test-fix/scripts/rerun_diff.py submission/output.banked.csv output.csv --id-col <id>`. Explain any change before accepting it.

## Step 3. Clean-run check

Copy the would-be zip contents to a fresh temporary folder (or unzip a `--check-only` build), follow only the README, and run it on a few rows (`--limit 5`, or `--offline` if the cache is excluded and the API key is not available). Fix the README until a stranger could run it. Confirm the run reads inputs from the documented location and writes the output where the contract says.

## Step 4. Check, then build

```
python $P/scripts/package.py --root . --output output.csv --log log.txt \
  --template <blank template csv> --inputs <eval input csv> --id-col <id> \
  --require evaluation/evaluation_report.md --require evaluation/usage_report.md --check-only
```

Fix every FAIL. Then build:

```
python $P/scripts/package.py ...same flags without --check-only...
```

This writes `submission/code.zip`, `submission/output.csv`, `submission/log.txt` and `submission/MANIFEST.md` (hashes, members, checks). Read the member list: no dataset, no `.env`, no caches, no nested zips, nothing private.

Also run the specialised checks one last time:
- `hr-orchestrate-kickoff/scripts/check_log.py <log> --expect-tool "Claude Code" --expect-model <model id>` (with `--profile oct26` or `--require-section` flags if the edition's format needs them)
- `hr-orchestrate-test-fix/scripts/preflight.py output.csv ...` with the contract's enums and JSON columns
- `hr-orchestrate-interview/scripts/interview_drill.py code/ --constants docs/CONSTANTS.md --strict`

## Step 5. Agent trace (when the edition asks for it)

For Claude Code, the raw session files are JSONL files under `~/.claude/projects/<folder named after the repo path>/` (Windows: `%USERPROFILE%\.claude\projects\`). The participant also runs `/export` in each session for a readable transcript. Stage only this challenge's session files in a folder such as `agent-trace/claude-code/`, have the participant review them for secrets and private data, then:

```
python $P/scripts/package.py ...same flags... --trace-dir <path to agent-trace>
```

It refuses settings and credential files and scans for secrets. Never include `auth.json`, settings files or whole home folders.

## Step 6. Submit

The participant uploads the artifacts on the challenge page; you never upload or submit for them. Afterwards, update `docs/STATUS.md` with the submitted hashes from MANIFEST.md, and switch to `hr-orchestrate-interview` for a final rehearsal while the interview window is open.

## Release checklist

Full list: `references/release-checklist.md`. The short version:
- [ ] `package.py` READY; MANIFEST.md reviewed
- [ ] `check_log.py` PASS with the exact tool and model
- [ ] `preflight.py` PASS on the final output
- [ ] Clean run from the zip contents works by following the README
- [ ] Evaluation and usage reports match the final run
- [ ] Interview numbers re-verified against the final run
- [ ] Submitted with at least 30 minutes to spare

## References
- `references/release-checklist.md`: the full pre-submission checklist
