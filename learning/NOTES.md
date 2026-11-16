# Teaching notes

## Preferences
- English. Short lessons, one tangible win each.
- Python solid, pydantic new → explain pydantic mechanics, don't re-teach Python basics beyond the specific traps.
- Size cap: one idea, ~6 questions, one-point checklist. Dense lessons fail free recall (lesson 1: 0/5, lesson 3: 0/3) even when the quiz goes fine (LR 0005).
- Quiz options must not overlap in plain English ("a field fails" vs "an unknown field" did). Prefer naming the error `type`.
- Asks lots of "what does X mean?" questions → define every term in plain language with an example before using it. Label given (professor) vs built (implementation) in every lesson. (LR 0002)

## Workspace facts
- Workspace location: the user chose `gatekeeper_lab_student/learning/` in the main checkout, but the first session was sandboxed to the try-1 worktree, so it was created at `.claude/worktrees/try-1/learning/`. Move it with `mv learning ../../../learning` from the worktree root. Not committed.
- The solution lives on branch `worktree-try-1`, commit `fadcd29`. The main checkout still has the stubs (`NotImplementedError`). Lessons therefore quote code inline; line numbers refer to `fadcd29`.
- System `python3` (3.15) has no pydantic. Tests pass (39/39) in a venv with `pip install 'pydantic>=2'`.
- Gene X through the real code: findings = span PASSED, negation-cue WARNING `NEGATION_CUE_MISMATCH` ('did not'), uncertainty PASSED, causal-claim PASSED → LOW PROVISIONAL; MODERATE/HIGH/CRITICAL HUMAN_REVIEW. Empty report → AUTHORITATIVE at LOW/MODERATE/HIGH.

## Terms in use (pre-glossary)
- Three kinds of wrong: **malformed** (one field), **inconsistent** (fields break a rule linking them), **consistent-but-false** (needs the source). "Self-contradictory" was retired (LR 0003).
- `negated` = flag on the source sentence; the predicate alone carries the claim (inferred, LR 0003).

## Open questions for the user
- Ask the professor: what does `negated` mean in Chapter 2: a flag on the sentence, or NOT applied to the predicate?
- When is the defense / submission, and is it oral?
- Can they share Chapter 2 notes or slides?

## Defense hot spots found while reading the code (feed into later lessons)
- `decide()` fails open: an unknown FAILED code (e.g. `ENTITY_ID_MISMATCH`) → AUTHORITATIVE (verified).
- No check in the code emits `AMBIGUOUS_ENTITY_RESOLUTION` or `EVIDENCE_CONTRADICTS_CLAIM`; `decide()` honours them anyway. `resolve_entity` returns a `ResolutionResult`, not a `Finding`.
- `decide()` never returns `REJECT`: refusal happens earlier via the contract's `ValidationError`.
- Reason codes: the starter spec says rules 2 and 4 *may* append their own code and tests only need the report's codes. The implementation appends them, then rewrote the docstring to say "plus the code of the rule that fired", which is slightly misleading for rules 1, 3 and 5.
- The starter file (`git show 453a596:gatekeeper.py`) specified almost everything: fields, signatures, all rules in docstrings. Choices beyond spec: `verify_span` bound, regex construction, `resolve_entity` candidates on RESOLVED, `ASSOCIATION_AS_CAUSATION` added to rule 3, all of Part E. See `reference/given-vs-built.html`.
- Pydantic lax mode accepts `negated="yes"` as True; `"maybe"` is rejected (verified). Use `"maybe"` as the malformed example.
- `Relationship` is mutable (no `frozen=True`; verified `rel.uncertainty = HIGH` works). Design rule 2 is held only by discipline and `test_uncertainty_does_not_mutate`.
- `ExtractedValue` and `resolve_entity` are standalone: only the tests call them. No resolution result is ever turned into a Finding; `decide()` only checks whether ids are None.
- The registry is an input dict (hand-written in tests); nothing in the lab registers entries. Who fills `subject_id`/`object_id` on a candidate is unspecified (tests pass them in). User asked both.
- "Positive relationship" = affirmative claim that a relationship exists (`inhibits` counts), not "good"/"increasing". User asked.
- Two different AIs in the story: the scenario's extraction LLM (never called; tests hand-build candidates) and Claude Code (wrote the solution). User asked whether the LLM writes Python. It doesn't: it returns JSON, which `model_validate_json` can parse into a `Relationship`.
- `unrelated_to` + `negated=False` on the Gene X sentence triggers NEGATION_CUE_MISMATCH: a possible false positive of the negation check worth discussing later.
- `human_review_completed` is a bare boolean any caller can set (REFLECTION §4).
- Verified (pydantic 2.14): gate 3 (model validator) is skipped when any field error or extra field exists; `ExtractedValue(value="", status="present")` is accepted; omitting `value` gives `missing`.
- Sandbox blocks `git -C`/`cd ..` compound commands; run git from the worktree root with plain commands. Scratchpad venv has pydantic.
- `verify_span` adds `end_offset <= len(text)` because slices clamp (REFLECTION "Changed").

## Curriculum draft (adjust with evidence)
1. The map: Gene X through the four stages ← written; too dense on first try (3/6, 0/5)
2. Foundations: the job, three kinds of wrong, consequence and confidence, given vs built ← written; 8/9, checklist 2.5/3 (LR 0004)
3. The contract: four gates, the two after-validators, ValueError vs assert, unknown is not null, limits (`value=""`, mutation) ← written; 7/9, checklist 0/3: too big (LR 0005)
3b. Two passes: repair of gate order only ← written (`lessons/0004`). Then space lesson 3's leftovers (after vs before, ValueError vs assert, the two limits) as 1–2 warm-ups per lesson.
4. Evidence: SHA-256, offsets, the slice-clamp guard
5. Checks: regex alternation order, `\b`, case; uncertainty never mutated; `resolve_entity`, casefold, NO_MATCH vs NOT_FOUND_IN_SOURCE
6. `decide()`: rule order, reason codes, fail-open, fail-safe defaults
7. Part E: the three adversarial candidates, `causal_claim_finding`, false positives; reflection answers in own words
8. Mock defense: interleaved retrieval across 1–7

## Glossary
Deferred until the user shows they can use the core terms (contract, check, finding, report, disposition, consequence, assurance). Then create `GLOSSARY.md` and hold lessons to it.
