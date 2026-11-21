# log.txt: locations, formats, common mistakes

The transcript is graded from `log.txt`. The current `AGENTS.md` is the only authority on where it lives and what each entry contains. Re-read it each edition.

## Locations seen so far

| Edition | Path |
|---|---|
| May-June 2026 | `$HOME/hackerrank_orchestrate/log.txt` (Windows: `%USERPROFILE%\hackerrank_orchestrate\log.txt`) |
| October 2026 | `log.txt` in the repo root, next to `AGENTS.md`, resolved relative to that file (no hardcoded user path) |

## October 2026 shape (example of a strict edition)

Session start entry: heading `## [ISO-8601 timestamp] SESSION START`, then `tool=`, `model=`, repo root, branch, worktree, parent agent, language, time remaining.

Per-turn entry: heading `## [ISO-8601 timestamp] <short title>`, then sections `User Prompt (verbatim, secrets redacted):`, `Agent Response Summary:` (2-5 sentences), `Actions:` (bullets), `Context:` with `tool=`, `model=`, `branch=`, `repo_root=`, `worktree=`, `parent_agent=`.

Rules in that edition:
- Exactly one populated `tool=` and one populated `model=` per entry.
- Invalid: missing, blank, placeholder (`<...>`), `unknown`, a generic label (`AI`, `LLM`, `assistant`), only a model family (`claude`), a model name in `tool=`, or a different harness.
- Re-read the appended entry before replying and correct it if wrong.
- Sub-agents log to the same file with `parent_agent=` set; worktrees share the one log.
- Never log secrets, credentials, real personal data, or whole large files.
- Append only: never rewrite earlier entries.

## Values for Claude Code

- `tool=Claude Code`
- `model=` the exact model id from your runtime (for example `claude-opus-5-5`), not "Opus" or "Claude".
- If a sub-agent writes entries, it uses the same values and sets `parent_agent=` to the parent's name.

## Validation

```
python scripts/check_log.py log.txt --expect-tool "Claude Code" --expect-model claude-opus-5-5
```

Optional flags: `--require-section "User Prompt" --require-section "Agent Response Summary"` (applied to per-turn entries), `--json` for machine-readable output. Exit code 1 means at least one FAIL.

## Common mistakes

- Logging only at session start and forgetting per-turn entries after a long build step.
- Summaries that say "made changes" with no files, decisions or evidence.
- Paraphrasing the participant's prompt instead of copying it verbatim.
- Pasting an API key from an error message into the log.
- Writing the log to the old home-directory path in an edition that wants the repo root.
