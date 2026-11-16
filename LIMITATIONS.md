# Known limitations of the Part A contract

Both were confirmed by running `gatekeeper.py` with pydantic 2.14. No public test covers either.

## 1. An empty string counts as a present value

`ExtractedValue(value="", status="present")` is accepted. `_value_matches_status` checks
`self.value is None`, and `""` is not `None`.

Fix: declare the field as `value: str | None = Field(min_length=1)` (pydantic checks the
length only when the value is a string), or test for `not self.value` in the validator.

## 2. The rules hold only when a record is built

Validators run at construction. `Relationship` is neither frozen nor validated on assignment, so
this goes unnoticed:

```python
rel = Relationship(..., predicate="causes", negated=False)  # accepted
rel.negated = True                                           # no error; the record now breaks A2
```

Rebuilding it with `Relationship.model_validate(rel.model_dump())` raises `ValidationError`.

This is the same weakness as `REFLECTION.md` §4, one step earlier: the contract is checked once,
like the disposition is recorded once, and nothing enforces it afterwards.

Fix: `model_config = ConfigDict(extra="forbid", frozen=True)` to forbid changes, or
`validate_assignment=True` to re-run the validators on every change. `frozen=True` also
makes design rule 2 (never rewrite the candidate) enforced by the type, not only by
`test_uncertainty_does_not_mutate`.
