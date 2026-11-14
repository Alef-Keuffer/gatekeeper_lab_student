import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pydantic import ValidationError  # noqa: E402

import gatekeeper as g  # noqa: E402
from models import (  # noqa: E402
    Assurance,
    Candidate,
    CheckStatus,
    Consequence,
    Disposition,
    EvidenceSpan,
    Finding,
    Predicate,
    Report,
    ResolutionStatus,
    Uncertainty,
    ValueStatus,
)

SOURCE = "Gene X did not significantly increase the risk of Disease Y."


def make_span(text=SOURCE, quote=None, start=0, end=None):
    quote = quote if quote is not None else text
    end = end if end is not None else start + len(quote)
    return EvidenceSpan(
        normalized_text_checksum=g.sha256_text(text),
        quoted_text=quote,
        start_offset=start,
        end_offset=end,
    )


def make_rel(**kw):
    base = dict(
        subject_text="Gene X",
        subject_id="GENE:1",
        predicate=Predicate.CAUSES,
        object_text="Disease Y",
        object_id="DIS:2",
        negated=False,
        evidence=make_span(),
        uncertainty=Uncertainty.LOW,
    )
    base.update(kw)
    return g.Relationship(**base)


def report(*pairs):
    return Report(
        findings=[
            Finding(check_name=c, status=s, issue_code=code) for c, s, code in pairs
        ]
    )


class PartA(unittest.TestCase):
    def test_present_needs_value(self):
        with self.assertRaises(ValidationError):
            g.ExtractedValue(value=None, status=ValueStatus.PRESENT)

    def test_missing_status_forbids_value(self):
        with self.assertRaises(ValidationError):
            g.ExtractedValue(value="Germany", status=ValueStatus.NOT_FOUND_IN_SOURCE)

    def test_valid_absence(self):
        v = g.ExtractedValue(value=None, status=ValueStatus.NOT_FOUND_IN_SOURCE, reason="x")
        self.assertIsNone(v.value)

    def test_every_non_present_status_forbids_value(self):
        for s in ValueStatus:
            if s is ValueStatus.PRESENT:
                continue
            with self.assertRaises(ValidationError, msg=s):
                g.ExtractedValue(value="v", status=s)

    def test_negated_asserted_rejected(self):
        for p in (Predicate.CAUSES, Predicate.ASSOCIATED_WITH, Predicate.INHIBITS, Predicate.ACTIVATES):
            with self.assertRaises(ValidationError, msg=p):
                make_rel(negated=True, predicate=p)

    def test_negated_unrelated_or_uncertain_ok(self):
        make_rel(negated=True, predicate=Predicate.UNRELATED_TO)
        make_rel(negated=True, predicate=Predicate.UNCERTAIN)

    def test_two_consistent_mistakes_pass_the_contract(self):
        # The point of the lab: this wrong candidate is structurally VALID.
        rel = make_rel(predicate=Predicate.CAUSES, negated=False)
        self.assertEqual(rel.predicate, Predicate.CAUSES)


class PartB(unittest.TestCase):
    def test_sha256_known_vector(self):
        self.assertEqual(
            g.sha256_text("abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )

    def test_verify_ok(self):
        self.assertTrue(g.verify_span(make_span(), SOURCE))

    def test_verify_partial_span_ok(self):
        s = make_span(quote="did not significantly", start=7)
        self.assertTrue(g.verify_span(s, SOURCE))

    def test_verify_wrong_offsets(self):
        s = make_span(quote="did not significantly", start=8, end=29)
        self.assertFalse(g.verify_span(s, SOURCE))

    def test_verify_paraphrase(self):
        s = make_span(quote="Gene X had no effect on Disease Y.", start=0)
        self.assertFalse(g.verify_span(s, SOURCE))

    def test_verify_changed_source(self):
        changed = SOURCE + " "  # same words, different normalized text
        self.assertFalse(g.verify_span(make_span(), changed))

    def test_span_finding(self):
        ok = g.span_finding(make_rel(), SOURCE)
        self.assertEqual((ok.check_name, ok.status), ("source-span", CheckStatus.PASSED))
        self.assertIsNone(ok.issue_code)
        bad = g.span_finding(make_rel(), "other text")
        self.assertEqual(bad.status, CheckStatus.FAILED)
        self.assertEqual(bad.issue_code, "INVALID_EVIDENCE_SPAN")


class PartC(unittest.TestCase):
    def test_negation_cue_flags_gene_x(self):
        f = g.negation_cue_finding(make_rel())
        self.assertEqual(f.status, CheckStatus.WARNING)
        self.assertEqual(f.issue_code, "NEGATION_CUE_MISMATCH")
        self.assertEqual(f.check_name, "negation-cue")

    def test_negation_cue_quiet_when_negated(self):
        rel = make_rel(negated=True, predicate=Predicate.UNCERTAIN)
        self.assertEqual(g.negation_cue_finding(rel).status, CheckStatus.PASSED)

    def test_negation_cue_whole_words_only(self):
        text = "Gene X was associated with Disease Y in a nominal cohort."
        rel = make_rel(evidence=make_span(text=text), predicate=Predicate.ASSOCIATED_WITH)
        self.assertEqual(g.negation_cue_finding(rel).status, CheckStatus.PASSED)

    def test_negation_cue_case_insensitive(self):
        text = "Gene X did NOT increase the risk of Disease Y."
        rel = make_rel(evidence=make_span(text=text))
        self.assertEqual(g.negation_cue_finding(rel).status, CheckStatus.WARNING)

    def test_uncertainty_finding(self):
        for u, st in [
            (Uncertainty.LOW, CheckStatus.PASSED),
            (Uncertainty.MEDIUM, CheckStatus.PASSED),
            (Uncertainty.HIGH, CheckStatus.WARNING),
            (Uncertainty.UNKNOWN, CheckStatus.WARNING),
        ]:
            self.assertEqual(g.uncertainty_finding(make_rel(uncertainty=u)).status, st)

    def test_uncertainty_does_not_mutate(self):
        rel = make_rel(uncertainty=Uncertainty.LOW)
        g.uncertainty_finding(rel)
        self.assertEqual(rel.uncertainty, Uncertainty.LOW)

    def test_resolve_one(self):
        r = g.resolve_entity("  gene x ", {"GENE:1": "Gene X", "GENE:2": "Gene Z"})
        self.assertEqual((r.status, r.normalized_id), (ResolutionStatus.RESOLVED, "GENE:1"))

    def test_resolve_ambiguous(self):
        reg = {"GENE:1": "Gene X", "GENE:9": "GENE X"}
        r = g.resolve_entity("Gene X", reg)
        self.assertEqual(r.status, ResolutionStatus.AMBIGUOUS)
        self.assertIsNone(r.normalized_id)
        self.assertEqual({c.identifier for c in r.candidates}, {"GENE:1", "GENE:9"})

    def test_resolve_no_match(self):
        r = g.resolve_entity("Gene Q", {"GENE:1": "Gene X"})
        self.assertEqual(r.status, ResolutionStatus.NO_MATCH)


class PartD(unittest.TestCase):
    def test_assurance_mapping(self):
        self.assertEqual(g.required_assurance(Consequence.LOW), Assurance.BASIC)
        self.assertEqual(g.required_assurance(Consequence.MODERATE), Assurance.STANDARD)
        self.assertEqual(g.required_assurance(Consequence.HIGH), Assurance.STRONG)
        self.assertEqual(g.required_assurance(Consequence.CRITICAL), Assurance.HUMAN_CONFIRMED)

    def test_clean_low_is_authoritative(self):
        d = g.decide(make_rel(), Report(), Consequence.LOW)
        self.assertEqual(d.disposition, Disposition.AUTHORITATIVE)

    def test_invalid_span_quarantines_at_any_consequence(self):
        r = report(("source-span", CheckStatus.FAILED, "INVALID_EVIDENCE_SPAN"))
        for c in Consequence:
            self.assertEqual(g.decide(make_rel(), r, c).disposition, Disposition.QUARANTINE)

    def test_unresolved_entity_depends_on_consequence(self):
        rel = make_rel(subject_id=None)
        self.assertEqual(g.decide(rel, Report(), Consequence.LOW).disposition, Disposition.PROVISIONAL)
        self.assertEqual(g.decide(rel, Report(), Consequence.MODERATE).disposition, Disposition.PROVISIONAL)
        self.assertEqual(g.decide(rel, Report(), Consequence.HIGH).disposition, Disposition.HUMAN_REVIEW)
        self.assertEqual(g.decide(rel, Report(), Consequence.CRITICAL).disposition, Disposition.HUMAN_REVIEW)

    def test_gene_x_findings(self):
        r = report(("negation-cue", CheckStatus.WARNING, "NEGATION_CUE_MISMATCH"))
        self.assertEqual(g.decide(make_rel(), r, Consequence.LOW).disposition, Disposition.PROVISIONAL)
        self.assertEqual(g.decide(make_rel(), r, Consequence.HIGH).disposition, Disposition.HUMAN_REVIEW)

    def test_contradiction_finding(self):
        r = report(("entailment", CheckStatus.FAILED, "EVIDENCE_CONTRADICTS_CLAIM"))
        self.assertEqual(g.decide(make_rel(), r, Consequence.MODERATE).disposition, Disposition.HUMAN_REVIEW)

    def test_critical_needs_human(self):
        self.assertEqual(
            g.decide(make_rel(), Report(), Consequence.CRITICAL).disposition, Disposition.HUMAN_REVIEW
        )
        self.assertEqual(
            g.decide(make_rel(), Report(), Consequence.CRITICAL, human_review_completed=True).disposition,
            Disposition.AUTHORITATIVE,
        )

    def test_model_confidence_is_not_authority(self):
        # Same findings, different self-reported uncertainty: the decision must not change.
        r = report(("negation-cue", CheckStatus.WARNING, "NEGATION_CUE_MISMATCH"))
        a = g.decide(make_rel(uncertainty=Uncertainty.LOW), r, Consequence.HIGH)
        b = g.decide(make_rel(uncertainty=Uncertainty.HIGH), r, Consequence.HIGH)
        self.assertEqual(a.disposition, b.disposition)
        c = g.decide(make_rel(uncertainty=Uncertainty.LOW), Report(), Consequence.CRITICAL)
        self.assertEqual(c.disposition, Disposition.HUMAN_REVIEW)

    def test_reason_codes_include_report_codes(self):
        r = report(("negation-cue", CheckStatus.WARNING, "NEGATION_CUE_MISMATCH"))
        d = g.decide(make_rel(), r, Consequence.HIGH)
        self.assertIn("NEGATION_CUE_MISMATCH", d.reason_codes)

    def test_rule_order_quarantine_beats_everything(self):
        r = report(
            ("source-span", CheckStatus.FAILED, "INVALID_EVIDENCE_SPAN"),
            ("negation-cue", CheckStatus.WARNING, "NEGATION_CUE_MISMATCH"),
        )
        d = g.decide(make_rel(subject_id=None), r, Consequence.LOW)
        self.assertEqual(d.disposition, Disposition.QUARANTINE)


if __name__ == "__main__":
    unittest.main()
