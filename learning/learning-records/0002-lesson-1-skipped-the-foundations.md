# Lesson 1 skipped the foundations

Lesson 1 assumed the user already knew what the gatekeeper is for and what "contract", "finding" and "disposition" mean. They did not. They also couldn't tell which parts of the solution the professor gave and which the implementation built.

**Evidence:** quiz 3/6. They missed Q1 (why the contract accepts Gene X), Q2 (checks return a `Finding`) and Q6 (removing the negation check makes Gene X AUTHORITATIVE). They hit 0/5 checklist points. Their questions: what the "two mistakes" are; what self-contradictory and malformed candidates are; what the gatekeeper is for; what model confidence is used for; how consequence is determined; and given vs built.

**Implications:**
- Define every term in plain language, with a concrete example, before using it.
- Say in every lesson which parts are given (professor) and which are built (implementation).
- Lesson 2 rebuilds the base (the job; malformed / self-contradictory / consistent-but-false; consequence is a caller input; confidence is recorded, not acted on; given vs built). Don't start pydantic mechanics until the user scores well on lesson 2 and can do its three-point checklist.
- Retake lesson 1's quiz a day later as a spaced check.
