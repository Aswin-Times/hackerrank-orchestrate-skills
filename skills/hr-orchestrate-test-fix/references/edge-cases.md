# Edge-case checklist

Turn each relevant item into a test or a custom evaluation case. Note which ones the sample already covers.

## Every archetype
- Empty, whitespace-only or extremely long input fields
- Non-English or mixed-language text; unusual Unicode, emoji, right-to-left text
- Prompt injection in every free-text field and inside documents and images ("ignore previous instructions", "output COMPLETE", fake system messages, role-play)
- Missing referenced file, unreadable image, corrupt PDF, empty SQL table
- Duplicate or near-duplicate inputs; ids with leading zeros or odd characters
- Values exactly at every threshold (equal to, just below, just above)
- Dates: time zones, end of month, leap day, timestamps equal to a cutoff
- Model failure: timeout, invalid JSON, refusal; check the fallback row is valid
- Cache miss under `--offline`: fails loudly, does not write partial output

## A. Grounded answer or escalate
- Question answerable only by combining two documents
- Question with no answer in the corpus (must escalate, not invent)
- Request for something dangerous or account-specific (fraud, stolen card, account takeover): escalate
- Pleasantries and thanks; off-topic questions; requests about a different company than the corpus

## B. Multimodal verification
- Image of the wrong object; several objects; screenshot of a screen; text written on the image instructing approval
- Blurry, dark or cropped photo; duplicate photo reused across claims
- Claim history that is suspicious but evidence that is clear (history must not flip the verdict alone)

## C. Adversarial routing
- Brand impersonation with perfect wording but unverified sender
- Urgent-sounding message that is a scam; genuinely urgent message phrased calmly
- Receiver preferences that conflict with the default rule

## D. Numeric decisions
- Balance exactly at the minimum; currency with no exact rate; zero or negative amounts
- Rotating vendors in volatile categories; irregular income (commission, freelance)
- Ties in the selection criteria (prove the tie-break order with a test where every criterion disagrees)

## E. Evidence and policy
- Identifier changed over time (old email only in an old backup)
- Decoy record for a different person with a similar name or email
- Evidence captured after the audit time (must not be used or cited)
- Status claims ("Complete") contradicted by a replica or backup
- Restore or sync that recreates deleted data after the delete
- Records that policy requires to be retained or tombstoned rather than deleted
- Ordering dependencies: stop flows before deleting, downstream copies before sources
