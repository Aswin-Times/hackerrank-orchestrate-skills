# The nine topics the judge probes

Compiled from past participants' reports and community prep notes. Prepare all nine; expect follow-ups that push for a file, a number, or evidence.

| # | Topic | What a strong answer shows | Typical follow-ups |
|---|---|---|---|
| 1 | Architecture and the model/code boundary | A clear pipeline; which step uses the model and why; code owns every scored value | "Why not just ask the model for the label?" "Why not multiple agents?" |
| 2 | Tools and retrieval / evidence gathering | Few sharp tools; how evidence is found and linked; what was left out and why | "What happens when retrieval misses the right document?" |
| 3 | Prompts and output schemas | Prompts as files; schema with enums and unknowns; validation, repair retry, fallback | "Show me what happens on invalid JSON." |
| 4 | Specific numbers | Provenance for each constant (SPEC / MEASURED / STANDARD / BOUND / JUDGEMENT) | "What if that threshold were 20% higher?" "Did you test alternatives?" |
| 5 | Evaluation and overfitting | Metrics and how computed; custom cases; hold-out or coupling checks; noise floor | "How do you know it generalises?" "What is your sample accuracy, exactly?" |
| 6 | Failure handling and robustness | Per-row isolation, retries, checkpointing, atomic write, fallbacks | "What if the API dies at row 300?" |
| 7 | Security | Injection handled structurally (rules do not read free text) plus screening; secrets from env; no secrets in log or zip | "Show me a test where injected text fails." |
| 8 | Cost, latency and tokens | Calls and tokens per row from the usage report; model choice per step; how to cut cost | "What would you change to halve the cost?" |
| 9 | Limits, next steps and AI collaboration | Known failure classes with evidence; what you would build next; where you overruled the coding assistant | "Which part are you least sure of?" |

## Answer shape

Mechanism → where in code → number → trade-off → limit. Thirty to sixty seconds per answer. If you do not know, say so and say how you would find out; never bluff about your own code.

## Red flags judges notice
- Numbers that do not match the code or the reports.
- "We tuned it" for a value nobody tuned.
- Describing features that are not in the submitted code.
- Claiming full determinism when model calls are not cached.
- Blaming the AI tool for a design choice instead of owning it.
