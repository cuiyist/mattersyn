"""Extracted Ag contributions cannot change the pinned audited inventory."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_quality import material_membership_errors, reviewed_silver_record_ids


def record(rid, formula='Ag', components=None, status='source_reviewed'):
    return {
        'record_id': rid, 'collection': 'reviewed_literature',
        'record_type': 'literature_protocol', 'reader_role': 'synthesis_route',
        'quality': {'review_status': status, 'requested_tasks': []},
        'operations': [{'stage': 'synthesis'}],
        'material': {'formula': formula, 'components': components or []},
        'lineage': {'source_group': rid},
        'sources': [{'id': rid, 'doi': '10.fixture/' + rid}],
    }


class SilverReviewedInventory(unittest.TestCase):
    def setUp(self):
        self.rows = [record('legacy-ag'),
                     record('legacy-composite', 'Ag/Si', ['Ag', 'Si']),
                     record('new-extracted', 'NHC-Ag', ['Ag'], 'source_extracted')]
        self.hub = {'formula': 'Ag', 'record_ids': [r['record_id'] for r in self.rows],
                    'direct_record_ids': ['legacy-ag'],
                    'paper_dois': ['10.fixture/' + r['record_id'] for r in self.rows]}

    def reviewed_checks_pass(self, rows):
        byid = {r['record_id']: r for r in rows}
        return (reviewed_silver_record_ids(self.hub, byid, 'direct_record_ids') == {'legacy-ag'}
                and reviewed_silver_record_ids(self.hub, byid, 'record_ids') ==
                {'legacy-ag', 'legacy-composite'})

    def test_extracted_component_preserves_exact_reviewed_inventory(self):
        self.assertTrue(self.reviewed_checks_pass(self.rows))
        self.assertEqual([], material_membership_errors(self.hub, self.rows))

    def test_extracted_component_cannot_be_relabelled_reviewed(self):
        bad = copy.deepcopy(self.rows)
        bad[-1]['quality']['review_status'] = 'source_reviewed'
        self.assertFalse(self.reviewed_checks_pass(bad))

    def test_legacy_reviewed_route_cannot_be_demoted(self):
        for index in (0, 1):
            bad = copy.deepcopy(self.rows)
            bad[index]['quality']['review_status'] = 'source_extracted'
            with self.subTest(index=index):
                self.assertFalse(self.reviewed_checks_pass(bad))

    def test_complete_membership_still_rejects_unsupported_and_unknown_routes(self):
        bad = copy.deepcopy(self.rows)
        bad[-1]['material']['components'] = []
        self.assertTrue(material_membership_errors(self.hub, bad))
        for mutation in ('unknown', 'component-as-direct', 'missing'):
            hub = copy.deepcopy(self.hub)
            if mutation == 'unknown':
                hub['record_ids'].append('invented')
            elif mutation == 'component-as-direct':
                hub['direct_record_ids'].append('new-extracted')
            else:
                hub['record_ids'].remove('new-extracted')
            with self.subTest(mutation=mutation):
                self.assertTrue(material_membership_errors(hub, self.rows))


if __name__ == '__main__':
    unittest.main()
