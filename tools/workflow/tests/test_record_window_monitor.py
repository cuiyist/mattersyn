"""Synthetic record-window checks; no scientific audit or sampled production data."""
import copy
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import record_window_monitor as m


def event(number, count=100, findings=0, window='resume'):
    rids = [f'paper-{number}-record-{i:03}' for i in range(count)]
    return {'event_id': f'event-{number:03}', 'window_id': window,
            'sampled_at': '2026-10-07T18:00:00Z', 'primary_source_id': f'paper-{number}',
            'record_ids': rids, 'original_findings': [
                {'finding_id': f'finding-{i}', 'severity': 'S2', 'affected_record_ids': [rids[i]]}
                for i in range(findings)], 'author_id': 'author', 'full_auditor_id': 'full',
            'deep_auditor_id': 'deep', 'frozen_package_sha256': 'a'*64, 'receipt_sha256': 'b'*64}


class RecordWindowTests(unittest.TestCase):
    def test_no_evaluation_below_100_and_strict_threshold(self):
        report = m.monitor([event(1, 99, 3)], 'resume')
        self.assertFalse(report['evaluated']); self.assertFalse(report['stop_required'])
        boundary = m.monitor([event(1, 100, 1)], 'resume')
        self.assertTrue(boundary['evaluated'])
        self.assertEqual(boundary['threshold_per_100'], 1)
        self.assertFalse(boundary['stop_required'])
        self.assertTrue(m.monitor([event(1, 100, 2)], 'resume')['stop_required'])

    def test_strict_threshold_scales_with_record_denominator(self):
        self.assertFalse(m.monitor([event(1, 200, 2)], 'resume')['stop_required'])
        self.assertTrue(m.monitor([event(1, 200, 3)], 'resume')['stop_required'])

    def test_empty_is_unmeasured_not_zero_error(self):
        report = m.monitor([], 'resume')
        self.assertIsNone(report['findings_per_100_sampled_records'])
        self.assertFalse(report['evaluated'])

    def test_exact_last500_and_partial_boundary_disclosure(self):
        first = event(1, 101, 2)
        first['original_findings'][1]['affected_record_ids'] = first['record_ids'][:2]
        report = m.monitor([first] + [event(i) for i in range(2, 6)], 'resume')
        self.assertEqual(report['sampled_records'], 500)
        self.assertEqual(report['all_sampled_records'], 501)
        self.assertEqual(report['s1_s2_findings'], 1)  # removed-only finding leaves window
        self.assertEqual(report['partial_boundary_papers'][0]['excluded_record_ids'], first['record_ids'][:1])
        self.assertEqual(report['ordered_record_ids'][0], first['record_ids'][1])

    def test_grouped_adjudication_counts_once_not_per_record(self):
        sample = event(1, 100)
        sample['original_findings'] = [{'finding_id':'group', 'severity':'S1',
                                        'affected_record_ids':sample['record_ids']}]
        report = m.monitor([sample], 'resume')
        self.assertEqual(report['s1_s2_findings'], 1)
        self.assertEqual(report['findings_per_100_sampled_records'], 1)

    def test_source_order_is_completion_then_event_then_frozen_record_order(self):
        a, b = event(1, 2), event(2, 2)
        a['record_ids'].reverse()
        self.assertEqual(m.monitor([b,a], 'resume')['ordered_record_ids'], a['record_ids']+b['record_ids'])
        b['sampled_at'] = '2026-10-07T12:59:59-05:00'
        self.assertEqual(m.monitor([a,b], 'resume')['ordered_record_ids'], b['record_ids']+a['record_ids'])

    def test_other_window_is_preserved_but_excluded(self):
        old, current = event(1, 100, 10, 'old'), event(2)
        before = copy.deepcopy([old,current])
        report = m.monitor([old,current], 'resume')
        self.assertEqual(report['s1_s2_findings'], 0)
        self.assertEqual([old,current], before)

    def test_correction_cannot_become_new_sample_or_erase_original_findings(self):
        original = event(1, 100, 3)
        corrected = copy.deepcopy(original); corrected['original_findings'] = []
        corrected['event_id'] = 'correction'
        with self.assertRaisesRegex(ValueError, 'duplicate source or correction'):
            m.monitor([original,corrected], 'resume')
        self.assertTrue(m.monitor([original], 'resume')['stop_required'])

    def test_invalid_inputs_fail_closed(self):
        changes = [lambda e:e.pop('original_findings'), lambda e:e['original_findings'][0].pop('affected_record_ids'),
                   lambda e:e['original_findings'][0].update(affected_record_ids=['unrelated']),
                   lambda e:e.update(deep_auditor_id='author'), lambda e:e.update(receipt_sha256='invalid'),
                   lambda e:e.update(sampled_at='2026-10-07T18:00:00'),
                   lambda e:e['record_ids'].append(e['record_ids'][0]),
                   lambda e:e['original_findings'].append(copy.deepcopy(e['original_findings'][0]))]
        for change in changes:
            with self.subTest(change=change):
                sample = event(1, 100, 1); change(sample)
                with self.assertRaises(ValueError): m.monitor([sample], 'resume')
        with self.assertRaisesRegex(ValueError, 'duplicate event'):
            m.monitor([event(1),event(1)], 'resume')

    def test_only_s1_s2_original_findings_count(self):
        sample = event(1, 100, 4)
        sample['original_findings'][2]['severity'] = 'S3'
        sample['original_findings'][3]['severity'] = 'S4'
        self.assertEqual(m.monitor([sample], 'resume')['s1_s2_findings'], 2)


if __name__ == '__main__': unittest.main()
