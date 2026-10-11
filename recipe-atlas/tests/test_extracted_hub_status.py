import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_quality import hub_publication_status_matches


class ExtractedHubStatusTest(unittest.TestCase):
    def setUp(self):
        self.records = [
            {'record_id': 'audited', 'quality': {'review_status': 'source_reviewed'}},
            {'record_id': 'extracted', 'quality': {'review_status': 'source_extracted'}},
            {'record_id': 'pending', 'quality': {'review_status': 'pending'}},
        ]

    def check_hub(self, ids, status):
        return hub_publication_status_matches({'record_ids': ids, 'publication_status': status}, self.records)

    def test_extracted_hub_cannot_claim_verified_status(self):
        self.assertTrue(self.check_hub(['extracted'], 'source_extracted_contribution'))
        self.assertFalse(self.check_hub(['extracted'], 'verified_synthesis_contribution'))

    def test_audited_and_mixed_hubs_keep_existing_status(self):
        for ids in (['audited'], ['audited', 'extracted']):
            self.assertTrue(self.check_hub(ids, 'verified_synthesis_contribution'))
            self.assertFalse(self.check_hub(ids, 'source_extracted_contribution'))

    def test_missing_pending_and_empty_memberships_fail(self):
        for ids in ([], ['missing'], ['pending'], ['extracted', 'missing'], ['audited', 'pending']):
            for status in ('source_extracted_contribution', 'verified_synthesis_contribution'):
                self.assertFalse(self.check_hub(ids, status))


if __name__ == '__main__':
    unittest.main()
