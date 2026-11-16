# Gatekeeper Lab Resources

## Knowledge

### The spec
- Lab `README.md` (repo root, both branches)
  The assignment: parts A–E, the four tested design rules, grading. Use for: "what exactly was asked" — the professor grades against this.
- Course book, Chapter 2 of _Engineering Trust into LLM Pipelines_ (§2.1 contract, §2.2 evidence, §2.4 semantic findings, §2.5 acceptance policy)
  The source of the lab's vocabulary. Not publicly findable online; only via the course. Use for: the professor's own framing of every concept.

### Python and pydantic mechanics
- [Pydantic docs: Validators — model validators](https://pydantic.dev/docs/validation/latest/concepts/validators/#model-validators)
  `mode="after"` validators "run after the whole model has been validated" and return the instance. Use for: `ExtractedValue._value_matches_status`, `Relationship._negation`.
- [Pydantic docs: Raising validation errors](https://pydantic.dev/docs/validation/latest/concepts/validators/#raising-validation-errors)
  `ValueError` raised in a validator surfaces as `ValidationError`; `assert` is skipped under `-O`. Use for: why the code raises `ValueError`, not `assert`.
- [Pydantic API: `ConfigDict.extra`](https://pydantic.dev/docs/validation/latest/api/pydantic/config/#pydantic.config.ConfigDict.extra)
  `extra="forbid"` turns unknown fields into `extra_forbidden` errors. Use for: every `model_config` in the lab.
- [Python docs: `re` — alternation `|`](https://docs.python.org/3/library/re.html#re-syntax-vertical-bar)
  "The `'|'` operator is never greedy": the first branch that matches wins. Use for: why `_NEGATION_CUE` lists longest cues first.
- [Python docs: `re` — `\b`](https://docs.python.org/3/library/re.html#b) and [`re.search`](https://docs.python.org/3/library/re.html#re.search)
  Word boundaries and first-match search. Use for: whole-word cue matching ("nominal" does not trigger "no").
- [Python docs: common sequence operations, note 4](https://docs.python.org/3/library/stdtypes.html#common-sequence-operations)
  "If i or j is greater than len(s), use len(s)": slices clamp silently. Use for: the extra `end_offset <= len(text)` guard in `verify_span`.
- [Python docs: `str.casefold`](https://docs.python.org/3/library/stdtypes.html#str.casefold)
  Aggressive lowercasing for caseless matching. Use for: `resolve_entity`.

### Design ideas behind the lab
- [Alexis King, "Parse, don't validate" (2019)](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/)
  "Make illegal states unrepresentable." Use for: why the contract rejects at construction instead of checking later.
- [OWASP Top 10 for LLM Applications 2025 — LLM05 Improper Output Handling](https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/)
  "Treat the model as any other user, adopting a zero-trust approach." Use for: why model output and model confidence are untrusted input.
- [OWASP Top 10 for LLM Applications 2025 — LLM09 Misinformation](https://genai.owasp.org/llmrisk/llm092025-misinformation/)
  "False or misleading information that appears credible"; recommends human review and automatic validation for high-stakes outputs. Use for: Gene X, consequence-based routing.
- [Saltzer & Schroeder, "The Protection of Information in Computer Systems" (1975)](https://en.wikipedia.org/wiki/The_Protection_of_Information_in_Computer_Systems)
  Fail-safe defaults: "base access decisions on permission rather than exclusion." Use for: `decide()` failing open on unknown FAILED findings.

### Where the heuristics come from
- [Chapman et al., "A simple algorithm for identifying negated findings and diseases in discharge summaries", J Biomed Inform 34(5), 2001 (NegEx)](https://www.dbmi.pitt.edu/wp-content/uploads/2022/10/A-simple-algorithm-for-identifying-negated-findings-and-diseases-in-discharge-summaries.pdf)
  The classic regex negation-cue algorithm, with scope limits and pseudo-negation filters. Use for: what `negation_cue_finding` does and doesn't do.
- [Farkas et al., "The CoNLL-2010 Shared Task: Learning to Detect Hedges and their Scope in Natural Language Text"](https://aclanthology.org/W10-3001/)
  Hedge-cue detection in biomedical text. Use for: reflection candidate 1.2 (hedged sentence recorded as certain).
- [Sumner et al., "The association between exaggeration in health related science news and academic press releases", BMJ 2014;349:g7015](https://orca.cardiff.ac.uk/id/eprint/68310/1/bmj.g7015.full.pdf)
  33% of press releases turned correlational findings into causal claims. Use for: why `ASSOCIATION_AS_CAUSATION` is a real failure mode.

- [Altman & Bland, "Absence of evidence is not evidence of absence", BMJ 1995;311:485](https://pmc.ncbi.nlm.nih.gov/articles/PMC2550545)
  A non-significant result usually shows only that a difference wasn't detected, not that there is none. Use for: why "did not significantly increase" ≠ "does not cause" (Gene X).

- [HGNC gene nomenclature guidelines](https://www.genenames.org/about/old-guidelines/) and [CASRAI gene notation guide](https://casrai.org/guides/gene-notation)
  Human gene symbols are all uppercase (BRCA1); mouse symbols capitalise only the first letter (Brca1). Use for: why a case-insensitive registry lookup can be legitimately AMBIGUOUS.

## Wisdom (Communities)
- The professor (office hours / course forum)
  The actual audience. Use for: "which parts of the solution would you probe?" — the cheapest way to calibrate the defense.
- A classmate for a mock defense
  Swap solutions and grill each other on `decide()` and the reflection. Use for: rehearsing explanations out loud under questioning.
- [Pydantic GitHub Discussions](https://github.com/pydantic/pydantic/discussions)
  Active (posts through Nov 2026), "Question" and "Pydantic V2" categories. Use for: pydantic mechanics questions the docs don't settle.

## Gaps
- The course book chapter isn't available online. If you can share §2.1–2.5 notes or slides, lessons can quote the professor's own wording.
