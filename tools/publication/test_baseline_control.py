"""Generation must not turn old scientific or task changes into new approvals."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import baseline_control as baseline


class BaselineControlTests(unittest.TestCase):
    def setUp(self):
        self.old = {'record_id': 'old', 'record_sha256': 'a' * 64,
                    'eligibility': {'partial_protocol': {'eligible': False}},
                    'title': 'Older approved record'}
        self.new = {'record_id': 'new', 'record_sha256': 'b' * 64,
                    'eligibility': {'partial_protocol': {'eligible': True}},
                    'title': 'New reviewed record'}
        self.previous = {'schema_version': '1.0.0', 'record_count': 1,
                         'records': [copy.deepcopy(self.old)]}
        self.projected = {'schema_version': '1.0.0', 'record_count': 2,
                          'records': [copy.deepcopy(self.old), copy.deepcopy(self.new)]}
        self.raw = {baseline.RECORD_PREFIX + rid + '.json': json.dumps({'record_id': rid}).encode()
                    for rid in ('old', 'new')}

    def generate(self, approved=None, reviews=None, previous_approved=None):
        with patch.object(baseline, 'dataset_manifest', return_value=copy.deepcopy(self.projected)):
            return baseline.generate(Path('.'), self.raw, self.previous,
                                     approved or {}, reviews or {}, previous_approved or {})

    def test_additive_membership_and_count_are_derived(self):
        result = self.generate()
        self.assertEqual(result['record_count'], 2)
        self.assertEqual([row['record_id'] for row in result['records']], ['old', 'new'])
        self.assertEqual(result['records'][0]['record_sha256'], 'a' * 64)

    def test_prior_digest_needs_exact_override_and_changed_file_review(self):
        self.projected['records'][0]['record_sha256'] = 'c' * 64
        with self.assertRaisesRegex(ValueError, 'digest changed without exact approval'):
            self.generate()
        with self.assertRaisesRegex(ValueError, 'digest changed without exact approval'):
            self.generate({'old': 'c' * 64})
        with self.assertRaisesRegex(ValueError, 'digest changed without exact approval'):
            self.generate({}, {baseline.RECORD_PREFIX + 'old.json': {'decision': 'allow'}})
        result = self.generate({'old': 'c' * 64},
                               {baseline.RECORD_PREFIX + 'old.json': {'decision': 'allow'}})
        self.assertEqual(result['records'][0]['record_sha256'], 'a' * 64)
        # A correction approved in an earlier commit remains valid in later
        # additive releases without fabricating a fresh review receipt.
        result = self.generate({'old': 'c' * 64}, previous_approved={'old': 'c' * 64})
        self.assertEqual(result['records'][0]['record_sha256'], 'a' * 64)

    def test_prior_eligibility_change_fails_even_with_digest_approval(self):
        self.projected['records'][0]['record_sha256'] = 'c' * 64
        self.projected['records'][0]['eligibility']['partial_protocol']['eligible'] = True
        with self.assertRaisesRegex(ValueError, 'task eligibility changed'):
            self.generate({'old': 'c' * 64},
                          {baseline.RECORD_PREFIX + 'old.json': {'decision': 'allow'}})

    def test_deletion_and_unknown_digest_are_explicit(self):
        self.raw.pop(baseline.RECORD_PREFIX + 'old.json')
        self.projected['records'] = [self.new]
        with self.assertRaisesRegex(ValueError, 'count or canonical membership differs'):
            self.generate()
        self.projected['record_count'] = 1
        with self.assertRaisesRegex(ValueError, 'removed without exact deletion review'):
            self.generate()
        result = self.generate(reviews={baseline.RECORD_PREFIX + 'old.json': {'decision': 'delete'}})
        self.assertEqual(result['record_count'], 1)
        with self.assertRaisesRegex(ValueError, 'noncanonical record'):
            self.generate({'ghost': 'd' * 64},
                          {baseline.RECORD_PREFIX + 'old.json': {'decision': 'delete'}})


if __name__ == '__main__':
    unittest.main()
