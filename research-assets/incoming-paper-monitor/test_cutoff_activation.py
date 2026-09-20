"""Selection safety tests; no real papers or production ledger are mutated."""
import copy
import json
import unittest
import monitor as m
import test_batch as fixtures
from activate_screened_cutoff import build_policy


class CutoffActivationTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.BatchTests()
        self.f.setUp()
        self.addCleanup(self.f.tearDown)
        self.ledger = m.read_ledger(self.f.path)
        self.included = self.f.order[:3]
        self.later = self.f.order[3:]
        self.partition = {'included_canonical_group_ids': self.included,
                          'later_arrival_group_ids': self.later,
                          'unmapped_cutoff_files': [], 'missing_current_cutoff_scope_ids': []}
        self.report = {'scientific_review_performed': False,
                       'counts': {'per_file_dispositions': 7, 'snapshot_present_files': 7,
                                  'actual_source_hashes_computed': 7},
                       'scopes': [{'group_id': k} for k in self.f.order],
                       'screened_at': '2026-09-20T04:00:00+00:00',
                       'rankings': [{'group_id': k, 'score': i, 'source_generation': 1}
                                    for i, k in enumerate(self.f.order)]}
        self.path = self.f.root / 'ranked-scopes.json'
        self.path.write_text(json.dumps(self.report))

    def policy(self):
        return build_policy(self.ledger, self.report, self.partition, self.path)

    def test_higher_scoring_later_papers_cannot_be_claimed(self):
        policy, held = self.policy()
        self.assertEqual(held, [])
        m.set_priority(self.f.path, policy)
        with self.assertRaisesRegex(RuntimeError, 'current source screening'):
            m.claim(self.f.path, 'root', self.later[-1], now=self.f.now)
        batch = self.f.claim()
        self.assertEqual([p['group_id'] for p in batch['papers']], list(reversed(self.included)))

    def test_source_updates_stay_included_but_require_new_screen(self):
        self.ledger['groups'][self.included[0]]['generation'] = 2
        policy, held = self.policy()
        self.assertEqual(held, [self.included[0]])
        self.assertNotIn(self.included[0], {r['group_id'] for r in policy['rankings']})

    def test_incomplete_or_missing_source_coverage_rejected(self):
        for field in ('per_file_dispositions', 'actual_source_hashes_computed'):
            with self.subTest(field=field):
                prior = copy.deepcopy(self.report)
                self.report['counts'][field] = 6
                with self.assertRaises(ValueError): self.policy()
                self.report = prior
        self.report['scopes'] = self.report['scopes'][1:]
        with self.assertRaisesRegex(ValueError, 'no screening disposition'): self.policy()

    def test_unmapped_cutoff_members_are_not_silently_dropped(self):
        self.partition['unmapped_cutoff_files'] = [{'path': 'unknown.pdf'}]
        with self.assertRaisesRegex(ValueError, 'unmapped'): self.policy()

    def test_existing_batch_statuses_and_original_order_are_preserved(self):
        self.f.claim()
        before = m.read_ledger(self.f.path)
        policy, _ = self.policy()
        m.set_priority(self.f.path, policy)
        after = m.read_ledger(self.f.path)
        for field in ('groups', 'files', 'current_paper', 'current_batch'):
            self.assertEqual(before[field], after[field])
        self.assertTrue(self.f.claim()['resumed'])

    def test_rolling_admission_preserves_closed_member_and_respects_cutoff(self):
        policy, _ = self.policy()
        m.set_priority(self.f.path, policy)
        first = self.f.claim(size=2)
        closed = first['papers'][0]['group_id']
        self.f.complete(closed)
        before = m.read_ledger(self.f.path)
        result = m.claim_batch(self.f.path, 'root', size=2, now=self.f.now, refill=True)
        after = m.read_ledger(self.f.path)
        self.assertEqual(len(result['active_papers']), 2)
        self.assertEqual(len(result['papers']), 3)
        self.assertEqual(before['groups'][closed], after['groups'][closed])
        self.assertEqual(result['batch_id'], first['batch_id'])
        self.assertEqual(len(result['admissions']), 1)
        self.assertFalse({p['group_id'] for p in result['papers']} & set(self.later))
        again = m.claim_batch(self.f.path, 'root', size=2, now=self.f.now, refill=True)
        self.assertEqual(again['papers'], result['papers'])


if __name__ == '__main__': unittest.main()
