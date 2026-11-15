"""Gatekeeper lab. Do not edit models.py or the tests.

Run the tests with:   python -m unittest -v tests.test_gatekeeper tests.test_extra
"""
from __future__ import annotations

import hashlib
import re

from pydantic import BaseModel, ConfigDict, Field, model_validator

from models import (
    ASSERTED,
    Assurance,
    Candidate,
    CheckStatus,
    Consequence,
    Decision,
    Disposition,
    EvidenceSpan,
    Finding,
    Predicate,
    Report,
    ResolutionResult,
    ResolutionStatus,
    Uncertainty,
    ValueStatus,
)

# ------------------------------------------------------------------ Part A: contract


class ExtractedValue(BaseModel):
    """A value that says WHY it may be empty.

    Status PRESENT requires a non-None value; any other status forbids a value.
    """

    model_config = ConfigDict(extra="forbid")

    value: str | None
    status: ValueStatus
    reason: str | None = None

    @model_validator(mode="after")
    def _value_matches_status(self) -> "ExtractedValue":
        if self.status == ValueStatus.PRESENT and self.value is None:
            raise ValueError("status present requires a value")
        if self.status != ValueStatus.PRESENT and self.value is not None:
            raise ValueError(f"status {self.status.value} forbids a value")
        return self


class Relationship(BaseModel):
    """A candidate relationship extracted from a source text.

    A negated candidate may not carry a predicate in ASSERTED.
    """

    model_config = ConfigDict(extra="forbid")

    subject_text: str = Field(min_length=1)
    subject_id: str | None = None
    predicate: Predicate
    object_text: str = Field(min_length=1)
    object_id: str | None = None
    negated: bool
    evidence: EvidenceSpan
    uncertainty: Uncertainty

    @model_validator(mode="after")
    def _negation(self) -> "Relationship":
        if self.negated and self.predicate in ASSERTED:
            raise ValueError(f"negated=True contradicts asserted predicate {self.predicate.value}")
        return self


# ------------------------------------------------------------------ Part B: evidence


def sha256_text(text: str) -> str:
    """Hex SHA-256 of the UTF-8 encoding of text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_span(span: EvidenceSpan, normalized_text: str) -> bool:
    """True only if the checksum matches AND the offsets slice out exactly the quote."""
    return (
        sha256_text(normalized_text) == span.normalized_text_checksum
        # slicing clamps silently, so an end_offset past the text would otherwise pass
        and span.end_offset <= len(normalized_text)
        and normalized_text[span.start_offset : span.end_offset] == span.quoted_text
    )


def span_finding(rel: Relationship, normalized_text: str) -> Finding:
    """PASSED "source-span" if the span verifies, else FAILED with INVALID_EVIDENCE_SPAN."""
    if verify_span(rel.evidence, normalized_text):
        return Finding(check_name="source-span", status=CheckStatus.PASSED)
    return Finding(
        check_name="source-span",
        status=CheckStatus.FAILED,
        issue_code="INVALID_EVIDENCE_SPAN",
        detail="quoted_text does not occur at the declared offsets of the declared text",
    )


# ------------------------------------------------------------------ Part C: semantic findings

# Longest cues first so the reported cue is the most specific one.
_NEGATION_CUE = re.compile(
    r"\b(?:no\s+evidence\s+of|no\s+significant|non-significant|did\s+not|failed\s+to|not|no)\b",
    re.IGNORECASE,
)


def negation_cue_finding(rel: Relationship) -> Finding:
    """WARNING NEGATION_CUE_MISMATCH when the quote has a negation cue but negated is False."""
    m = _NEGATION_CUE.search(rel.evidence.quoted_text)
    if m and not rel.negated:
        return Finding(
            check_name="negation-cue",
            status=CheckStatus.WARNING,
            issue_code="NEGATION_CUE_MISMATCH",
            detail=f"evidence contains {m.group(0)!r} but negated is False",
        )
    return Finding(check_name="negation-cue", status=CheckStatus.PASSED)


def uncertainty_finding(rel: Relationship) -> Finding:
    """WARNING HIGH_CANDIDATE_UNCERTAINTY when uncertainty is HIGH or UNKNOWN. Never modifies rel."""
    if rel.uncertainty in (Uncertainty.HIGH, Uncertainty.UNKNOWN):
        return Finding(
            check_name="candidate-uncertainty",
            status=CheckStatus.WARNING,
            issue_code="HIGH_CANDIDATE_UNCERTAINTY",
            detail=f"model reported uncertainty {rel.uncertainty.value}",
        )
    return Finding(check_name="candidate-uncertainty", status=CheckStatus.PASSED)


def resolve_entity(entity_text: str, registry: dict[str, str]) -> ResolutionResult:
    """registry maps identifier -> canonical label; labels match exactly after strip()+casefold()."""
    key = entity_text.strip().casefold()
    matches = [
        Candidate(identifier=identifier, label=label)
        for identifier, label in registry.items()
        if label.strip().casefold() == key
    ]
    if not matches:
        return ResolutionResult(entity_text=entity_text, status=ResolutionStatus.NO_MATCH)
    if len(matches) > 1:
        return ResolutionResult(
            entity_text=entity_text, status=ResolutionStatus.AMBIGUOUS, candidates=matches
        )
    return ResolutionResult(
        entity_text=entity_text,
        status=ResolutionStatus.RESOLVED,
        normalized_id=matches[0].identifier,
        candidates=matches,
    )


# ------------------------------------------------------------------ Part D: acceptance policy

_REQUIRED_ASSURANCE = {
    Consequence.LOW: Assurance.BASIC,
    Consequence.MODERATE: Assurance.STANDARD,
    Consequence.HIGH: Assurance.STRONG,
    Consequence.CRITICAL: Assurance.HUMAN_CONFIRMED,
}

# Findings that say the claim may misstate its evidence (rule 3).
_SEMANTIC_MISMATCH_CODES = (
    "EVIDENCE_CONTRADICTS_CLAIM",
    "NEGATION_CUE_MISMATCH",
    "ASSOCIATION_AS_CAUSATION",  # Part E: causal_claim_finding
)


def required_assurance(consequence: Consequence) -> Assurance:
    """LOW->BASIC, MODERATE->STANDARD, HIGH->STRONG, CRITICAL->HUMAN_CONFIRMED."""
    return _REQUIRED_ASSURANCE[consequence]


def decide(
    rel: Relationship,
    report: Report,
    consequence: Consequence,
    human_review_completed: bool = False,
) -> Decision:
    """First matching rule wins.

    1. report has INVALID_EVIDENCE_SPAN                      -> QUARANTINE
    2. unresolved entity: subject_id or object_id is None,
       or report has AMBIGUOUS_ENTITY_RESOLUTION
         assurance STRONG or HUMAN_CONFIRMED                 -> HUMAN_REVIEW
         otherwise                                           -> PROVISIONAL
    3. report has a semantic mismatch (_SEMANTIC_MISMATCH_CODES)
         assurance BASIC                                     -> PROVISIONAL
         otherwise                                           -> HUMAN_REVIEW
    4. assurance HUMAN_CONFIRMED and not human_review_completed -> HUMAN_REVIEW
    5. otherwise                                             -> AUTHORITATIVE

    reason_codes are the report's issue codes in order, plus the code of the rule that fired.
    rel.uncertainty (the model's own confidence) is deliberately never read here.
    """
    assurance = required_assurance(consequence)
    codes = [f.issue_code for f in report.findings if f.issue_code is not None]

    if report.has("INVALID_EVIDENCE_SPAN"):
        return Decision(disposition=Disposition.QUARANTINE, reason_codes=codes)

    if rel.subject_id is None or rel.object_id is None or report.has("AMBIGUOUS_ENTITY_RESOLUTION"):
        if assurance in (Assurance.STRONG, Assurance.HUMAN_CONFIRMED):
            return Decision(
                disposition=Disposition.HUMAN_REVIEW,
                reason_codes=codes + ["ENTITY_RESOLUTION_REQUIRES_REVIEW"],
            )
        return Decision(disposition=Disposition.PROVISIONAL, reason_codes=codes + ["UNRESOLVED_ENTITY"])

    if any(report.has(code) for code in _SEMANTIC_MISMATCH_CODES):
        if assurance == Assurance.BASIC:
            return Decision(disposition=Disposition.PROVISIONAL, reason_codes=codes)
        return Decision(disposition=Disposition.HUMAN_REVIEW, reason_codes=codes)

    if assurance == Assurance.HUMAN_CONFIRMED and not human_review_completed:
        return Decision(
            disposition=Disposition.HUMAN_REVIEW, reason_codes=codes + ["HUMAN_CONFIRMATION_REQUIRED"]
        )

    return Decision(disposition=Disposition.AUTHORITATIVE, reason_codes=codes)


# ------------------------------------------------------------------ Part E: extra check

_ASSOCIATION_CUE = re.compile(
    r"\b(?:associated\s+with|associations?|correlated\s+with|correlations?|linked\s+to)\b",
    re.IGNORECASE,
)


def causal_claim_finding(rel: Relationship) -> Finding:
    """WARNING ASSOCIATION_AS_CAUSATION when the predicate is CAUSES but the quoted evidence
    uses association language. Name the check "causal-claim".
    """
    m = _ASSOCIATION_CUE.search(rel.evidence.quoted_text)
    if rel.predicate == Predicate.CAUSES and m:
        return Finding(
            check_name="causal-claim",
            status=CheckStatus.WARNING,
            issue_code="ASSOCIATION_AS_CAUSATION",
            detail=f"predicate causes, but evidence says {m.group(0)!r}",
        )
    return Finding(check_name="causal-claim", status=CheckStatus.PASSED)
