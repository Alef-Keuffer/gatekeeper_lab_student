# `negated` is a flag on the source sentence, not a NOT on the predicate

The user read `causes` + `negated=True` as "does not cause" and asked why that would be a contradiction. The objection is correct in plain English: my lesson's "self-contradictory" framing was wrong. The lab never defines `negated` in words. Its rule (A2: reject `negated=True` with an `ASSERTED` predicate) and the test `test_negated_unrelated_or_uncertain_ok` only make sense if `negated` marks that *the source sentence is negative*, while the predicate alone states what the record claims. So `causes` in the database always means a positive claim. This is inferred, not stated; the user should confirm it with the professor.

**Implications:**
- The second kind of wrong is now called **inconsistent** (two fields break a rule that links them), not "self-contradictory".
- Any later lesson touching `_negation` or `negation_cue_finding` must state this convention explicitly.
- Being able to name the ambiguity and the reason for the convention (people filter on `predicate`; "not significant" ≠ "does not cause") is strong defense material.
