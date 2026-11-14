"""Gatekeeper lab: STARTER FILE. Implement every TODO. Do not edit models.py or the tests.

Run the tests with:   python -m unittest -v tests.test_gatekeeper
"""
from __future__ import annotations

import hashlib  # noqa: F401  (you will need it in Part B)
import re  # noqa: F401  (you will need it in Part C)

from pydantic import BaseModel, ConfigDict, Field, model_validator  # noqa: F401

from models import (  # noqa: F401
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

    TODO A1: add a model validator so that
      - status PRESENT requires a non-None value, and
      - any other status forbids a value.
    """

    model_config = ConfigDict(extra="forbid")

    value: str | None
    status: ValueStatus
    reason: str | None = None


class Relationship(BaseModel):
    """A candidate relationship extracted from a source text.

    TODO A2: add a model validator rejecting a candidate that is negated=True
    while its predicate is in ASSERTED (see models.py).
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


# ------------------------------------------------------------------ Part B: evidence


def sha256_text(text: str) -> str:
    """TODO B1: hex SHA-256 of the UTF-8 encoding of text."""
    raise NotImplementedError


def verify_span(span: EvidenceSpan, normalized_text: str) -> bool:
    """TODO B2: True only if BOTH
    - the checksum of normalized_text equals span.normalized_text_checksum, and
    - normalized_text[start_offset:end_offset] equals span.quoted_text.
    """
    raise NotImplementedError


def span_finding(rel: Relationship, normalized_text: str) -> Finding:
    """TODO B3: PASSED finding named "source-span" if the span verifies; otherwise a
    FAILED finding named "source-span" with issue_code "INVALID_EVIDENCE_SPAN".
    """
    raise NotImplementedError


# ------------------------------------------------------------------ Part C: semantic findings


def negation_cue_finding(rel: Relationship) -> Finding:
    """TODO C1: WARNING "NEGATION_CUE_MISMATCH" when the quoted evidence contains a
    negation cue (not, no, did not, failed to, no significant, no evidence of,
    non-significant; whole words, case-insensitive) but rel.negated is False.
    Otherwise PASSED. Name the check "negation-cue".
    """
    raise NotImplementedError


def uncertainty_finding(rel: Relationship) -> Finding:
    """TODO C2: WARNING "HIGH_CANDIDATE_UNCERTAINTY" when uncertainty is HIGH or UNKNOWN,
    otherwise PASSED. Name the check "candidate-uncertainty". Never modify rel.
    """
    raise NotImplementedError


def resolve_entity(entity_text: str, registry: dict[str, str]) -> ResolutionResult:
    """TODO C3: registry maps identifier -> canonical label.
    Match labels exactly after strip() and casefold().
      one match  -> RESOLVED with normalized_id
      >1 matches -> AMBIGUOUS with all candidates (no normalized_id)
      no match   -> NO_MATCH
    """
    raise NotImplementedError


# ------------------------------------------------------------------ Part D: acceptance policy


def required_assurance(consequence: Consequence) -> Assurance:
    """TODO D1: LOW->BASIC, MODERATE->STANDARD, HIGH->STRONG, CRITICAL->HUMAN_CONFIRMED."""
    raise NotImplementedError


def decide(
    rel: Relationship,
    report: Report,
    consequence: Consequence,
    human_review_completed: bool = False,
) -> Decision:
    """TODO D2: first matching rule wins.

    1. report has INVALID_EVIDENCE_SPAN                      -> QUARANTINE
    2. unresolved entity: subject_id or object_id is None,
       or report has AMBIGUOUS_ENTITY_RESOLUTION
         assurance STRONG or HUMAN_CONFIRMED                 -> HUMAN_REVIEW
         otherwise                                           -> PROVISIONAL
    3. report has EVIDENCE_CONTRADICTS_CLAIM or NEGATION_CUE_MISMATCH
         assurance BASIC                                     -> PROVISIONAL
         otherwise                                           -> HUMAN_REVIEW
    4. assurance HUMAN_CONFIRMED and not human_review_completed -> HUMAN_REVIEW
    5. otherwise                                             -> AUTHORITATIVE

    reason_codes: every non-None issue_code in the report, in order (rules 2 and 4 may
    append "ENTITY_RESOLUTION_REQUIRES_REVIEW" / "UNRESOLVED_ENTITY" /
    "HUMAN_CONFIRMATION_REQUIRED" respectively; the tests only require that the report's
    codes are included).
    The model's own `uncertainty` must NOT influence the disposition.
    """
    raise NotImplementedError
