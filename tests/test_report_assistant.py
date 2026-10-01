"""Ensure local model prose cannot add unsupported metrics or citations."""

import unittest

from src.report_assistant import evidence_pack, safe_fallback, validate_draft


class ReportAssistantTest(unittest.TestCase):
    def test_offline_draft_is_valid(self):
        evidence = evidence_pack()
        self.assertEqual(validate_draft(safe_fallback(), evidence), safe_fallback())

    def test_invented_number_is_rejected(self):
        draft = safe_fallback()
        draft["summary"] = "Coverage improved by 99%."
        with self.assertRaisesRegex(ValueError, "numbers"):
            validate_draft(draft, evidence_pack())

    def test_unknown_evidence_id_is_rejected(self):
        draft = safe_fallback()
        draft["actions"][0]["evidence_ids"] = ["E999"]
        with self.assertRaisesRegex(ValueError, "evidence IDs"):
            validate_draft(draft, evidence_pack())

    def test_unsupported_causal_claim_is_rejected(self):
        draft = safe_fallback()
        draft["summary"] = "Missing reports caused by staff shortages."
        with self.assertRaisesRegex(ValueError, "causal"):
            validate_draft(draft, evidence_pack())


if __name__ == "__main__":
    unittest.main()
