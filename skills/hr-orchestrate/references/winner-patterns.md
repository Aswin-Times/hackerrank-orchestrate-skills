# Patterns from top-ranked agents

Distilled from public write-ups and repos of top finishers (May 2026 #1, June 2026 #3, August 2026 top 40) and community guides. Use them as defaults; drop one only with a reason you can say out loud.

## 1. One agent, few tools
Reach for multiple agents only when something forces you to. A single agent with one well-designed tool (modes such as `search` to find, `read` to open in full, `grep` to pin an exact token like an id or error code) was enough to win May 2026. Fewer moving parts means fewer failure modes and an easier interview.

## 2. The model describes, code decides
The model returns a typed record of observations: booleans, enums, extracted values, each with the evidence id it came from. Plain code applies the rules and writes every scored value. Benefits:
- Repeatable: cache the observations and re-run the logic offline with no API calls.
- Auditable: each output column traces to a named rule.
- Injection-resistant by structure: text inside an image or ticket can confuse one observation but cannot reach the code that decides.

## 3. Rule table with declared inputs
For decision problems, write rules as an ordered table: precedence, condition, output, and the inputs each rule reads. A rule that never reads free text cannot be talked into anything. Test two properties: injected text cannot change rules that do not read text, and each rule really reads what it declares.

## 4. Cite only what you read
A citation counts only if the agent opened that document or evidence item during this run. A post-check strips or downgrades any claim whose citation was not opened. No reading, no answer: escalate.

## 5. Screen before the model
Cheap checks first: empty input, pleasantries, off-topic, obvious injection attempts (including non-English ones). Handle them without the expensive model. Use a small model for triage and a stronger one only for hard cases, and say so in the usage report.

## 6. When in doubt, escalate or fall back
A confident wrong answer costs more than an honest escalation. Define the safe default for every output column up front.

## 7. Hybrid retrieval when there is a corpus
Keyword search (BM25) catches exact terms; dense embeddings catch meaning; fuse (reciprocal rank fusion) and optionally rerank. Deterministic chunking so the same input retrieves the same passages.

## 8. Decide grouping keys and statistics before writing detectors
(September 2026 lesson.) Classify categories as fixed versus volatile before writing recurrence or aggregation code, and choose the statistic per group type (median for volatile spend, exact for fixed bills). A bad grouping cannot be repaired by later tuning.

## 9. Enumerate candidates, then pick by a stated tie-break
For planning or recommendation outputs, generate all valid candidates in code, score them, and choose with an explicit ordered tie-break. Prove the tie-break with a unit test where every criterion disagrees.

## 10. Simplicity and understanding win
Winners describe understanding the problem deeply, keeping the design simple, and being able to explain every decision. Students made up a majority of the May 2026 top builders: experience matters less than clarity.
