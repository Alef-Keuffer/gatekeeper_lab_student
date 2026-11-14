# Take-home lab: The Gatekeeper

**Course:** Advanced Software Construction Techniques  
**Topic:** Contracts and validation architecture for LLM-generated data (book, Chapter 2)  
**Estimated effort:** 3 to 4 hours  **Language:** Python 3.11+, `pydantic` v2, standard library only

## The scenario

An LLM pipeline extracts relationships from scientific papers. For the sentence

> Gene X did not significantly increase the risk of Disease Y.

the model returned `predicate = causes`, `negated = false`. The API call succeeded, the JSON is valid,
every field is present, and the predicate is in the allowed vocabulary. **It is still wrong.**

Your job is to build the *gatekeeper* that stands between that candidate and the database. You will
not call any LLM. The candidates are given as data, so everything you build is deterministic and testable.

## Files

| File | Role |
|---|---|
| `models.py` | Given vocabulary and types. **Do not edit.** |
| `gatekeeper.py` | **Your work.** Every `TODO` raises `NotImplementedError` until you implement it. |
| `tests/test_gatekeeper.py` | Public tests. **Do not edit.** |
| `REFLECTION.md` | You create this (Part E). |

```
python -m unittest -v tests.test_gatekeeper
```

## Parts

**Part A: Contract (lecture §2.1).** `ExtractedValue` (unknown is not null) and `Relationship`
(negation consistency). Tests: `PartA`.

**Part B: Evidence (lecture §2.2).** SHA-256 helper, span verification, and a finding that says whether
the quotation really occurs in the declared text. Tests: `PartB`.

**Part C: Semantic findings (lecture §2.4).** Negation-cue heuristic, candidate-uncertainty signal,
and registry-based entity resolution. Tests: `PartC`.

**Part D: Acceptance policy (lecture §2.5).** Map consequence to required assurance, then implement
`decide()` as an ordered rule list. Tests: `PartD`.

Design rules you must respect (they are tested):

1. Validators return **findings**. Only `decide()` returns a **disposition**.
2. A validator never rewrites the candidate (in particular, never overwrite `uncertainty`).
3. The model's own confidence must not change the disposition. Consequence of error does.
4. `NO_MATCH` (registry) is not the same thing as `NOT_FOUND_IN_SOURCE` (extraction).

**Part E: Adversarial thinking and reflection (not auto-graded).** Create `REFLECTION.md`:

1. Write **three new candidates** that pass your `Relationship` contract and are still wrong
   relative to the source. At least one must be different in kind from Gene X (for example:
   association reported as causation, wrong entity normalised to a valid identifier, or a
   hedged sentence recorded as certain). For each, state which of your checks catches it, or that
   none does.
2. Add **one new check** (a function returning a `Finding`) that catches one of those cases, with at
   least three tests of your own in a separate file `tests/test_extra.py`. Include a case where your
   check produces a **false positive**, and say what that costs.
3. Answer in 5 to 8 sentences: *Why does the book insist that `decide()` consumes findings instead of
   one `semantic_confidence` number?* Use a concrete example from your own code.
4. Answer in 3 to 5 sentences: *Name one place where your `decide()` is only a recorded
   status and not an enforced boundary. What would enforcement require (storage, views, API filters)?*

## Using AI assistants

You may use them. The course theme applies to you too: **generated code is untrusted input.**
In `REFLECTION.md`, add a short section stating which parts, if any, were generated, and one thing
the generated code got wrong or that you changed after testing.

## Grading (100 points)

| Part | Points |
|---|---|
| A. Contract | 15 |
| B. Evidence | 15 |
| C. Semantic findings | 20 |
| D. Acceptance policy | 25 |
| E. Reflection, adversarial cases, new check with tests | 25 |

Parts A to D are graded by the public tests plus a hidden set of similar edge cases, so do not
special-case the visible examples.

## Stretch (optional, +5)

Implement `check_provenance_completeness(...)`: a record may not become `AUTHORITATIVE` unless it
carries a model identifier, a prompt version and a validator version. Decide where this rule belongs
(contract, validator, or policy) and defend the choice in `REFLECTION.md`.
