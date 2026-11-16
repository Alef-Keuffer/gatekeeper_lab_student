# Lesson 2: the foundations mostly landed; "given vs built" and the job are still soft

Quiz 8/9. The miss was Q8: which part did the implementation write rather than receive (answer: the causal-claim check, Part E). Checklist: 2 of 3 points cleanly; point 1 (the gatekeeper's job: sits between LLM and database, gives each record a disposition, labels and never fixes) only "kind of".

Compared with lesson 1 (3/6, 0/5), the three kinds of wrong, consequence-as-caller-input and confidence-is-recorded-not-acted-on are now solid.

**Implications:**
- The foundations gate is passed: start pydantic mechanics (lesson 3, the contract).
- Space the two weak spots: open lesson 3 with retrieval questions on the job and on given vs built, and keep labelling given vs built per function. The contract is the clearest case: the professor gave every field and `Field` limit; the implementation wrote only the two validator bodies.
- Still owed: the lesson 1 quiz retake (spaced check).
