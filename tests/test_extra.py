"""Part E: tests for causal_claim_finding (association reported as causation)."""
import unittest

import gatekeeper as g
from models import CheckStatus, Consequence, Disposition, Predicate, Report
from tests.test_gatekeeper import make_rel, make_span

ASSOC = "Gene A variants were associated with a higher incidence of Disease B."


def rel_for(text, predicate=Predicate.CAUSES):
    return make_rel(evidence=make_span(text=text), predicate=predicate)


class CausalClaim(unittest.TestCase):
    def test_flags_association_reported_as_causation(self):
        f = g.causal_claim_finding(rel_for(ASSOC))
        self.assertEqual(f.check_name, "causal-claim")
        self.assertEqual(f.status, CheckStatus.WARNING)
        self.assertEqual(f.issue_code, "ASSOCIATION_AS_CAUSATION")

    def test_quiet_when_predicate_matches_evidence(self):
        f = g.causal_claim_finding(rel_for(ASSOC, Predicate.ASSOCIATED_WITH))
        self.assertEqual(f.status, CheckStatus.PASSED)

    def test_quiet_on_plain_causal_sentence(self):
        f = g.causal_claim_finding(rel_for("Gene A causes Disease B in knockout mice."))
        self.assertEqual(f.status, CheckStatus.PASSED)

    def test_whole_words_case_insensitive(self):
        self.assertEqual(
            g.causal_claim_finding(rel_for("Gene A is LINKED TO Disease B.")).status, CheckStatus.WARNING
        )
        self.assertEqual(
            g.causal_claim_finding(rel_for("Gene A causes dissociated Disease B.")).status,
            CheckStatus.PASSED,
        )

    def test_false_positive_real_causal_claim_mentioning_association(self):
        # The sentence really does assert causation; the check still fires because it only
        # sees association vocabulary. Known false positive, documented in REFLECTION.md.
        text = "Gene A causes Disease B, explaining the association reported in 2010."
        f = g.causal_claim_finding(rel_for(text))
        self.assertEqual(f.status, CheckStatus.WARNING)

    def test_decide_routes_the_finding_by_consequence(self):
        rel = rel_for(ASSOC)
        r = Report(findings=[g.causal_claim_finding(rel)])
        self.assertEqual(g.decide(rel, r, Consequence.LOW).disposition, Disposition.PROVISIONAL)
        self.assertEqual(g.decide(rel, r, Consequence.MODERATE).disposition, Disposition.HUMAN_REVIEW)
        self.assertIn("ASSOCIATION_AS_CAUSATION", g.decide(rel, r, Consequence.MODERATE).reason_codes)


if __name__ == "__main__":
    unittest.main()
