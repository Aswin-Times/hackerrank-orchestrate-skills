# Problem archetypes

Each past edition fits one of these. New editions usually combine two. Pick the closest, then adapt; say so in CONTRACT.md.

## A. Grounded answer or escalate (May 2026: support triage)
- Inputs: free-text requests, a local document corpus.
- Model: understand the request, choose tool calls, draft the reply from opened documents only.
- Code: pre-screen (empty, pleasantry, off-topic, injection), retrieval (keyword + dense, deterministic chunks), citation guard (only opened docs), hard escalation rules (fraud, outage, refunds, account security), output validation.
- Risks: hallucinated policy, citing unopened docs, multilingual inputs, injection in tickets.
- Metrics: decision accuracy (answer vs escalate), category accuracy, citation validity rate.

## B. Multimodal evidence verification (June 2026: damage claims)
- Inputs: images, conversation, history, minimum evidence requirements.
- Model (vision): describe what is visible as typed fields (object type, damage present, location, severity, image quality, signs of manipulation), each tied to an image id.
- Code: requirement checks, consistency between claim and observations, history as a caution signal that cannot flip a verdict alone, verdict + explanation template.
- Risks: instructions hidden in images, low-quality photos, overconfident vision output.
- Metrics: verdict accuracy, per-field accuracy, explanation-evidence consistency.

## C. Adversarial classification or routing (August 2026: notification router)
- Inputs: messages (text, image posters, voice notes), receiver profile and context.
- Model: classify content type candidates and extract claims (sender claims to be a bank, contains link, asks for OTP).
- Code: ordered rule table with declared inputs per rule; verification and domain state decide impersonation, not message text.
- Risks: scams that talk to the model, persona-specific rules, audio transcription errors.
- Metrics: per-column accuracy, confusion matrix on the action column, injection test pass rate.

## D. Numeric simulation and decision (September 2026: buy or wait)
- Inputs: transactions, balances, requests, payment options, messages and images with facts.
- Model: read messages and images for facts (income change, upcoming expense); write the explanation.
- Code: state reconstruction, currency normalisation, recurrence detection with grouping keys chosen up front, forward simulation, candidate enumeration, ordered tie-break, exact formatting.
- Risks: recurrence grouping that drops volatile categories, truthy checks on model text, stale assumptions.
- Metrics: decision accuracy, numeric error per field, tie-break unit tests.

## E. Evidence linking, policy engine, ordered plan (October 2026: deletion audit)
- Inputs: requests, identity snapshot plus change history, global activity stream, policy table, evidence manifest with PDFs, screenshots, logs, JSON, SQL snapshots.
- Model: extract facts from documents and images (identifiers present, record type, timestamps), each with the evidence id.
- Code: identifier reconstruction (current + historical), evidence matching by identifiers and hashes, time filtering (nothing after the audit time), policy application per data category, dependency-ordered remediation (stop flows and restores before dependent records; downstream before source), verification steps, deterministic JSON.
- Risks: decoy records for other people, trusting status claims, replica drift, citing post-audit evidence, step ordering.
- Metrics: case status accuracy, step-level and field-level accuracy, sequence accuracy.

## Common to all
- Typed model output validated against a schema; one retry; safe fallback row.
- Cache model calls by input hash for determinism and cheap re-runs.
- Justification columns built from the evidence ids the decision used.
