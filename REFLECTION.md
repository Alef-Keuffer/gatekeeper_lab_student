# My overall reflection

I had AI create custom sections for me to understand the project which I felt needed more context to understand the code. These are the Claude lessons in [`learning/`](learning/) (see "Use of AI assistants" below). 

I also have some questions that I got:

1. How is the consequence (LOW/MODERATE/HIGH/CRITICAL) decided? The answer you got was only that the caller passes it to decide(). Nothing in the lab says who chooses it or on what basis.
2. Who adds entries to the entity registry? 
3. Who fills subject_id / object_id on a candidate?
4. What is "Engineering Trust into LLM Pipelines", Chapter 2? What is that book? I googled but didn't find

I asked AI to remind me of the questions I asked when trying to understand the project

> What does negated=True mean? Is it a flag saying "the source sentence was negative", or a NOT applied to the predicate ("does not cause")? The lessons assumed it's a flag on the sentence. That was inferred from rule A2 and test_negated_unrelated_or_uncertain_ok; nothing in the lab confirms it. You raised this yourself: "Wouldn't causes + negated=True just mean it does not cause?"

Gaps I got with AI:

> Gaps found while reading the code, not questions you asked (possible reflection material)
> - decide() fails open: a FAILED finding with a code that no rule names ends up AUTHORITATIVE.
> - No check ever emits AMBIGUOUS_ENTITY_RESOLUTION or EVIDENCE_CONTRADICTS_CLAIM, even though rules 2 and 3 of decide() read them.
> - The REJECT disposition is never returned.

# Reflection: The Gatekeeper

All three candidates below pass the `Relationship` contract: the predicate is in the vocabulary,
`negated=False` with an asserted predicate is allowed, the span offsets and checksum are valid, and
the model reported `uncertainty = low`. Each was run through every check (`span_finding`,
`negation_cue_finding`, `uncertainty_finding`, `causal_claim_finding`) and through `decide()`. The
dispositions listed are the ones my code actually produced.

## 1. Three wrong candidates that pass the contract

### 1.1 Association reported as causation

> Gene A variants were associated with a higher incidence of Disease B.

`subject=Gene A (GENE:A)`, `predicate=causes`, `object=Disease B (DIS:B)`, `negated=false`, quote = whole sentence.

The paper reports a correlation. The candidate claims causation. That is a different kind of error
from Gene X: there is no negation, and the problem is the strength of the claim.

- Parts B to D: nothing fires. Span PASSED, negation-cue PASSED, uncertainty PASSED. Before Part E it
  was AUTHORITATIVE at low, moderate and high consequence.
- Caught by my new check `causal_claim_finding` (`ASSOCIATION_AS_CAUSATION`). With it, `decide()`
  gives PROVISIONAL at low and HUMAN_REVIEW at moderate, high and critical.

### 1.2 Hedged sentence recorded as certain

> Gene C may activate Pathway D in some cell lines.

`subject=Gene C (GENE:C)`, `predicate=activates`, `object=Pathway D (PATH:D)`, `negated=false`, `uncertainty=low`.

The authors hedge ("may", "in some cell lines"), but the candidate records a plain `activates` with
low uncertainty.

- **No check catches it.** It is AUTHORITATIVE at low, moderate and high. At critical it reaches
  HUMAN_REVIEW only through rule 4, which applies to every critical record and says nothing about this one.
- `uncertainty_finding` cannot help, because it reads the model's own `low`. The model's
  self-report hides the hedge. A hedge-cue check on the quote (may, might, could, suggest,
  possibly), built like the negation-cue check, would catch this case.

### 1.3 Wrong entity normalised to a valid identifier

> Gene X7 inhibits Protein P.

Registry: `{"GENE:1": "Gene X", "GENE:7": "Gene X7", ...}`. Candidate: `subject_text="Gene X7"`,
`subject_id="GENE:1"`, `predicate=inhibits`, `object=Protein P (PROT:P)`.

The text is right, but the id points to a different, real gene. The pipeline would record that Gene X
inhibits Protein P.

- **No check catches it.** It is AUTHORITATIVE at low, moderate and high. Rule 2 only asks whether
  `subject_id` is `None`, not whether it is the right id.
- `resolve_entity("Gene X7", registry)` returns `RESOLVED GENE:7`, so the information exists, but no
  check compares it with the candidate's `subject_id`. A check that resolves `subject_text` and
  `object_text` and fails with `ENTITY_ID_MISMATCH` when the ids differ would catch it.

### Other gaps found while probing

- The negation cue list is taken literally from the spec, so "Gene X **didn't** increase..." and
  "a **nonsignificant** trend" are not flagged. A Gene X candidate written with a contraction would
  become AUTHORITATIVE at low consequence.
- `decide()` fails open. A FAILED finding whose code is not named in a rule (for example a future
  `ENTITY_ID_MISMATCH`) is copied into `reason_codes` and the record still becomes AUTHORITATIVE.
  Every new check therefore has to be wired into a rule before it has any effect.
- The Part A contract has two limits of its own: an empty string counts as a present value, and the
  rules are checked only when a record is built. See [`LIMITATIONS.md`](LIMITATIONS.md).

## 2. New check: `causal_claim_finding`

Location: `gatekeeper.py`, Part E. If the predicate is `causes` and the quoted evidence contains
association language (associated with, association(s), correlated with, correlation(s), linked to;
whole words, case-insensitive), the check returns WARNING `ASSOCIATION_AS_CAUSATION`, named
`causal-claim`. In every other case it returns PASSED.

I added `ASSOCIATION_AS_CAUSATION` to the rule-3 codes in `decide()` (`_SEMANTIC_MISMATCH_CODES`).
Without that change the finding would be recorded and then ignored, because `decide()` fails open
(see above).

Tests (`tests/test_extra.py`, 6 tests): flags candidate 1.1; stays quiet when the predicate is
`associated_with`; stays quiet on a plain causal sentence; matches whole words and ignores case
("LINKED TO" flags, "dissociated" does not); a documented false positive; and `decide()` routes the
finding to PROVISIONAL at low and HUMAN_REVIEW at moderate.

**False positive.** In "Gene A causes Disease B, explaining the association reported in 2010." the
causal claim is correct, but the check fires because it only sees association vocabulary, not what
the sentence asserts. The cost is not data loss, since the record is never rejected. A correct fact
is held at PROVISIONAL at low consequence and costs a reviewer's time at moderate and above. The
larger risk is that frequent false positives teach reviewers to approve `causal-claim` warnings
without reading them, and then the check stops protecting anything. It also has false negatives:
"Gene A is a risk factor for Disease B" carries no association keyword and passes.

## 3. Why findings and not one `semantic_confidence` number?

A single number has to blend checks that demand different actions, and once they are blended you can
no longer tell which check fired. In my code the Gene X candidate gets a PASSED `source-span`, a
PASSED `candidate-uncertainty` (the model said `low`) and a WARNING `NEGATION_CUE_MISMATCH`, and an
average of those is mostly "good" and could easily clear a threshold and become AUTHORITATIVE.
Because `decide()` sees the code itself, rule 3 sends Gene X to PROVISIONAL at low consequence and to
HUMAN_REVIEW at high consequence, whatever else passed. The findings also differ in kind, not degree:
`INVALID_EVIDENCE_SPAN` means the quote does not exist in the source and is quarantined at every
consequence (rule 1). A missing `subject_id` is a gap that can be fixed, and it needs review only
when the stakes are high (rule 2). No threshold on one number can say "quarantine" for the first case
and "provisional" for the second. A score also lets the model's self-reported confidence back into
the decision. In my `decide()` the `HIGH_CANDIDATE_UNCERTAINTY` code is recorded in `reason_codes`, but
no rule reads it, and `test_model_confidence_is_not_authority` checks exactly that.

## 4. Where `decide()` is only a recorded status

`decide()` only returns a `Decision` object, so nothing stops a caller from storing a QUARANTINE or
PROVISIONAL record in the same table as authoritative ones, or a consumer from reading records without
looking at `disposition`. The weakest point is `human_review_completed`, a plain boolean that any
caller can set to `True` to make a critical record AUTHORITATIVE without a human ever seeing it.
Enforcement would need storage that keeps the disposition with the record (a NOT NULL column with a
CHECK constraint, or a separate quarantine table), readers granted access only to a view filtered with
`WHERE disposition = 'authoritative'`, and API endpoints that read from that view by default and need
an explicit flag to show provisional data. The review flag would also have to become a stored review
record (reviewer, timestamp, reviewed version) that the write path checks before it promotes a record.

## Use of AI assistants

All of `gatekeeper.py` (Parts A to E), `tests/test_extra.py` and the first draft of this file were
generated with Claude Code (Claude Opus 5.5). The output was checked against the public tests and
a separate probe script that ran extra inputs and the three candidates above.

- **Learning:** to understand the generated solution, I also used Claude to write a short series of
  lessons for me, in [`learning/`](learning/). It holds 4 lessons with quizzes (`learning/lessons/`),
  3 reference pages (the contract, a map of the gatekeeper, and what the lab gave vs. what was built,
  in `learning/reference/`), and learning records that track what I understood and what I didn't
  after each lesson (`learning/learning-records/`). The questions at the top of this file came out
  of those lessons.

- **Changed:** the spec for `verify_span` lists two conditions, a matching checksum and a slice equal
  to the quote. Implemented literally, those conditions accept a span whose `end_offset` runs past
  the end of the text, because Python slicing clamps silently. For example, text `"abc"`,
  quote `"bc"`, offsets 1..10 passes. The implementation adds `end_offset <= len(text)`, and the probe
  confirms that span is now rejected.
- **Found after testing:** all 33 public tests passed on the first run, which shows only that the
  visible examples work. Probing with extra inputs showed that the negation-cue check misses `didn't`
  and `nonsignificant`. The generated code followed the cue list exactly, so the public tests could
  not catch this. I left the behaviour as specified and recorded it above as a gap.
