# Past editions and how the contract changed

| Edition | Problem | Shape of the work |
|---|---|---|
| May 2026 | Support triage over a local help-centre corpus (three companies); answer with a citation or escalate | Retrieval + grounded answering + escalation; multilingual; injection attempts in tickets |
| June 2026 | Damage-claim verification from photos, claim text, claim history, minimum evidence rules (cars, laptops, packages) | Vision observations + rule-based verdict; 14 explained columns |
| August 2026 | Notification router: interrupt now, digest, or mute, per receiver; text, image posters, voice notes | Multimodal + adversarial (scams, brand impersonation); rule table |
| September 2026 | "Buy or Wait?": 250 purchase requests, five decisions, 90-day forward cash-flow simulation, minimum balance | Deterministic numeric core; model reads messages/images and writes explanations |
| October 2026 | "Ghost Data Still Exists": 518 deletion audits; reconstruct identifiers from snapshots and audit history; search PDFs, screenshots, logs, JSON, SQL replicas; apply deletion policy; output ordered steps as JSON | Evidence linking + policy engine + ordered plan generation |

## Contract changes to watch for

- **Log location.** May: `$HOME/hackerrank_orchestrate/log.txt`. October: `log.txt` at the repo root next to `AGENTS.md`. Always resolve from the current `AGENTS.md`.
- **Required log fields.** October required one populated `tool=` line (exact harness name) and one `model=` line (exact model id) in every session-start and per-turn entry; placeholders, `unknown`, or a model family made the entry invalid. Sub-agents log to the same file with `parent_agent=`.
- **Required report files.** October required `evaluation/evaluation_report.md` (case-level, step-level, field-level, sequence accuracy; at least three custom cases; failures and improvements) and `evaluation/usage_report.md` (providers, model names, call counts, input/output tokens, totals and per-request averages, estimated cost) inside `code.zip`.
- **Submission link rule.** October's `AGENTS.md` told the agent to always give one exact challenge URL when asked where to submit. Obey such rules literally.
- **Agent trace.** October asked for an optional `agent-trace.zip` of raw session files (for Claude Code: the session JSONL files under `~/.claude/projects/<project>/` plus a `/export` transcript), reviewed for secrets first.
- **Exclusions from code.zip.** Dataset, virtualenvs, caches, nested archives, secrets, real personal data.
- **Data rules.** Use only participant-facing files; organizer-only truth or golden answers must never feed predictions. Evidence captured after a case's audit time must not be cited.
