# Lesson 3: too much at once; gate order did not land

Quiz 7/9. Both misses test the same rule: pydantic runs the model validators only if every field passed first.

- Q4 (empty `subject_text` + `causes` + `negated=True`): picked "a rule fails". Belief: the validator reports even when a field is bad, or the rule wins over the field error. Actual: only `string_too_short`.
- Q5 (`confidence=0.9` on an `ExtractedValue`): picked "a field fails" instead of "an unknown field". This is partly my fault: "a field fails" and "an unknown field" overlap in plain English, since `confidence` is a field and it does fail. It still shows the user didn't connect `extra="forbid"` with "a key the class doesn't declare".

Checklist: 0 of 3 points. Lesson 3 held four gates, three design choices and two limits. That is the lesson-1 pattern again (too dense, 3/6 and 0/5). The six "which gate" questions were answerable by recognition, but a free recall of the whole lesson was not.

**Implications:**
- Lesson 4 repairs one idea only: two passes (pass 1 = every key and value checked, all errors reported together; pass 2 = your rules, only if pass 1 is clean). Use the `loc` / field-name line as the visible cue. Use `ExtractedValue` only, to keep working memory free.
- Quiz labels must not overlap: say "undeclared key" or name the error `type`, never "a field fails" vs "an unknown field".
- Lesson 3's other content (after vs before, `ValueError` vs `assert`, the two limits) is not lost but untested by recall. Bring it back as spaced warm-up questions, one or two per lesson, not re-taught in bulk.
- Lesson size cap: one idea and about six questions. Checklists should have one point until the user reliably hits it.
