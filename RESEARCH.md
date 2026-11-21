# Research notes: existing HackerRank Orchestrate skills and winning patterns

Compiled 2026-11-21, before the December 2026 edition (starts 2026-12-12, 07:30 EST; live AI evaluations 14-15 Dec; results 15 Dec, per the official event page).

Everything here is a summary written in our own words. Figures are what the cited sources say; re-check them before you quote them anywhere.

## 1. What Orchestrate is

A recurring 24-hour HackerRank hackathon in which you design, build and ship an AI agent using any AI coding tool. Each edition has a new starter repo with:

- `AGENTS.md`: rules for the coding agent, including **mandatory transcript logging to `log.txt`**
- `CLAUDE.md`: usually just `@AGENTS.md` (this import is what makes Claude Code follow the logging rules)
- `problem_statement.md`, a `dataset/` (or similar) with sample inputs plus expected outputs, and the evaluation inputs
- a blank `output.csv` template

Scoring (as reported by the community repos and earlier editions; check the live page each time):

| Artifact | Weight | What it rewards |
|---|---|---|
| Code zip | 30% | A real agent design (not a hardcoded pipeline), tool design, prompt quality, robustness, readable reasoning in source |
| Output CSV | 30% | Correct values plus evidence-anchored justifications per row |
| AI judge interview | 30% | 30 minutes; depth, ownership and honest limits |
| Chat transcript (`log.txt`) | 10% | Planning, specific constraints, real debugging dialogue, verification, safety awareness |

The community consensus: balance beats a peak in one section.

## 2. Editions so far

| Edition | Problem | Output shape | Notes |
|---|---|---|---|
| May 2026 | Support triage agent over a local corpus (HackerRank, Claude, Visa help centres) | answer or escalate, with citations | 12,885 registered, 2,002 shipped, 1,349 interviewed. Log lived at `$HOME/hackerrank_orchestrate/log.txt` |
| June 2026 | Multi-modal damage-claim verification (cars, laptops, packages) from images plus claim history | 14 explained columns | Vision-heavy |
| August 2026 | Message notification router (interrupt now / digest / mute), text, image posters, voice notes | 6 columns | Adversarial content (scams, injections) |
| September 2026 | "Buy or Wait?" — 250 purchase requests; decide full/partial/installments/wait/not_recommended from a 90-day cash-flow simulation | decision + explanation | Deterministic numeric core |
| October 2026 | "Ghost Data Still Exists" — 518 deletion-audit cases; reconstruct identifiers, search PDFs/screenshots/logs/SQL evidence, apply deletion policy | `case_id,deletion_status,steps_json` | `log.txt` moved to the **repo root**; every entry needs exact `tool=` and `model=` lines; `code.zip` must contain `evaluation/evaluation_report.md` and `evaluation/usage_report.md`; optional `agent-trace.zip` |

Trend: the contract gets stricter every edition (log location, required fields, required report files). **Read the starter contract fresh every time.**

## 3. Existing community skills

### NITISH-R-G/hackerrank-orchestrate-skills ("orchestrate-kit")
- 8 skills: `orchestrate` (router), `-build`, `-test-fix`, `-submit`, `-interview`, `-package`, `-score`, `-reference`, about 70 reference files, plus a Python CLI (`orchestrate evaluate|certify|score|interview|mentor|memory|release`).
- Strengths: phase order and 24-hour clock, failure-routing table, change-record loop, "model describes, code decides", constants provenance for the interview, transcript sub-weights, release checklist, score estimator.
- Weaknesses for our use: very large (hard to load into context quickly); much of it depends on the separate CLI; lessons are tied to the author's own September run; predates parts of the October contract (repo-root log, `tool=`/`model=` rules, mandatory evaluation reports).

### santheesh73/Orchestrate-skill
- One playbook skill (`hackerrank-orchestrate`) plus design / evidence / package / practice / toolkit sub-skills and stdlib checker scripts (contract extractor, log checker, CSV preflight, rerun diff, experiment record, usage report, interview drill, dataset-literal detector, claim audit). Behaviour evals with fixture starters.
- Strengths: "first 15 minutes" contract check, VERIFIED/MEASURED/INFERRED/UNKNOWN labelling of every figure, scripts that take schemas as arguments.
- Weaknesses for our use: default role is "draft prompts, the user's agent builds", whereas we want Claude to build directly; many version-history docs.

### Winning and top-ranked agents (not skills, but the best evidence of what scores)
- **#1 May 2026 (saai-syvendra/hackerrank-orchestrate):** one agent, one tool (`search` / `read` / `grep` over the corpus); hybrid BM25 + dense retrieval with rerank; prompt-injection screening before the model; a citation counts only if the agent actually opened that file in the turn; cheap model for trivial tickets, stronger model for hard ones; "when in doubt, escalate".
- **#3 June 2026, #37 August 2026 (swayam-mishra/hackerrank-orchestrate):** the model only describes what it sees and returns a typed record; plain code makes every scored decision. In August, a fixed-precedence rule table where each rule declares which inputs it reads, so injected text cannot reach the rules that do not read text; tests prove both properties. Model observations are cached so the decision logic re-runs offline.
- **Community guide (Medium, three editions):** understand before coding, avoid over-engineering, test continuously, be able to explain every design choice to the judge, never let the AI run unsupervised.

## 4. Gaps this suite fills

1. **Claude builds directly**, with the starter contract as the first artifact (`CONTRACT.md`) and checks that run against it.
2. **Current contract coverage**: repo-root `log.txt`, `tool=`/`model=` validation, evaluation and usage reports, agent-trace zip, submission-link rules.
3. **Small, self-contained skills**: each `SKILL.md` stays short and links to references only when needed; every script is Python standard library only and takes paths/columns as arguments (no dataset is embedded).
4. **Winner patterns as defaults**: typed model observations, code-owned decisions, cite-only-what-you-read, cached model calls, escalate on doubt.
5. **Interview prep from your own code**: a drill script that pulls constants, thresholds and orderings with `file:line`.

## Sources
- https://github.com/NITISH-R-G/hackerrank-orchestrate-skills
- https://github.com/santheesh73/Orchestrate-skill
- https://github.com/saai-syvendra/hackerrank-orchestrate and https://saai.syvendra.com/myspace/hackerrank-orchestrate
- https://github.com/swayam-mishra/hackerrank-orchestrate
- https://github.com/interviewstreet/hackerrank-orchestrate-may26 (also `-june26`, `-august26`, `-september26`, `-october26`)
- https://medium.com/@shreesh.exe22/hackerrank-orchestrate-3268f0d710a5
- https://www.hackerrank.com/hackerrank-orchestrate-december26
