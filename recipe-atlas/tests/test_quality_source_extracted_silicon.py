"""Synthetic Si route fixtures keep reviewed protections separate from extraction."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_quality import (
    HEATH_GE_SI_ROUTES, LITTAU_SI_ROUTES, hub_publication_status_matches,
    material_membership_errors, primary_doi, silicon_reviewed_regression_checks,
)

STIGER_ID = 'stiger-1999-electrodeposition'
DIRECT_ID = 'synthetic-source-extracted-si'
COMPONENT_ID = 'synthetic-source-extracted-au-si'
LEGACY_IDS = LITTAU_SI_ROUTES | HEATH_GE_SI_ROUTES | {STIGER_ID}


def record(rid, formula, doi, status='source_reviewed'):
    return {
        'record_id': rid, 'collection': 'reviewed_literature',
        'record_type': 'literature_protocol', 'reader_role': 'synthesis_route',
        'quality': {'review_status': status, 'requested_tasks': []},
        'operations': [{'stage': 'synthesis'}],
        'material': {'formula': formula, 'components': [] if formula == 'Si' else ['Si'],
                     'architecture': 'single_material' if formula == 'Si' else 'unresolved'},
        'lineage': {'source_group': rid}, 'sources': [{'id': rid, 'doi': doi}],
    }


def fixtures():
    rows = [record(rid, 'Si/SiOx', '10.1021/j100108a019') for rid in sorted(LITTAU_SI_ROUTES)]
    rows += [record(rid, 'Ge/Si', '10.1021/jp951903v') for rid in sorted(HEATH_GE_SI_ROUTES)]
    rows += [record(STIGER_ID, 'Ag/Si', '10.1021/la980800b')]
    rows += [record(DIRECT_ID, 'Si', '10.fixture/extracted', 'source_extracted'),
             record(COMPONENT_ID, 'Au/Si', '10.fixture/extracted', 'source_extracted')]
    hub = {'formula': 'Si', 'record_ids': [r['record_id'] for r in rows],
           'direct_record_ids': [DIRECT_ID], 'component_only': False,
           'paper_dois': sorted({primary_doi(r) for r in rows}),
           'publication_status': 'verified_synthesis_contribution'}
    return rows, hub


class SiliconExtractedStatusRegression(unittest.TestCase):
    def setUp(self):
        self.rows, self.hub = fixtures()
        self.byid = {r['record_id']: r for r in self.rows}

    def checks(self):
        return [ok for ok, _ in silicon_reviewed_regression_checks(self.hub, self.byid)]

    def test_two_extracted_routes_pass_three_legacy_checks(self):
        self.assertEqual(self.checks(), [True, True, True])

    def test_complete_canonical_membership_passes(self):
        self.assertEqual(material_membership_errors(self.hub, self.rows), [])

    def test_mixed_hub_status_matches_canonical_review_statuses(self):
        self.assertTrue(hub_publication_status_matches(self.hub, self.rows))

    def test_reviewed_only_legacy_component_hub_still_passes(self):
        self.hub.update(record_ids=sorted(LEGACY_IDS), direct_record_ids=[], component_only=True)
        self.assertEqual(self.checks(), [True, True, True])

    def test_littau_component_never_becomes_direct(self):
        self.hub['direct_record_ids'].append(sorted(LITTAU_SI_ROUTES)[0])
        self.assertFalse(self.checks()[0])

    def test_heath_component_never_becomes_direct(self):
        self.hub['direct_record_ids'].append(sorted(HEATH_GE_SI_ROUTES)[0])
        self.assertFalse(self.checks()[0])

    def test_stiger_component_never_becomes_direct(self):
        self.hub['direct_record_ids'].append(STIGER_ID)
        self.assertFalse(self.checks()[0])

    def test_missing_legacy_reviewed_route_fails(self):
        self.hub['record_ids'].remove(sorted(LITTAU_SI_ROUTES)[0])
        self.assertFalse(self.checks()[1])

    def test_degrading_legacy_review_status_fails(self):
        self.byid[sorted(LITTAU_SI_ROUTES)[0]]['quality']['review_status'] = 'source_extracted'
        self.assertFalse(self.checks()[1])

    def test_new_direct_route_cannot_masquerade_as_reviewed(self):
        self.byid[DIRECT_ID]['quality']['review_status'] = 'source_reviewed'
        self.assertEqual(self.checks(), [False, False, False])

    def test_new_component_route_cannot_masquerade_as_reviewed(self):
        self.byid[COMPONENT_ID]['quality']['review_status'] = 'source_reviewed'
        self.assertFalse(self.checks()[1])
        self.assertFalse(self.checks()[2])

    def test_changed_legacy_reviewed_doi_fails(self):
        self.byid[sorted(LITTAU_SI_ROUTES)[0]]['sources'][0]['doi'] = '10.fixture/wrong-legacy-doi'
        self.assertFalse(self.checks()[2])

    def test_draft_route_rejected_by_general_membership_and_status(self):
        self.byid[DIRECT_ID]['quality']['review_status'] = 'draft'
        self.assertTrue(material_membership_errors(self.hub, self.rows))
        self.assertFalse(hub_publication_status_matches(self.hub, self.rows))

    def test_title_only_doi_rejected_by_general_membership(self):
        self.hub['paper_dois'].append('10.fixture/title-only')
        self.assertIn('Si: complete canonical paper_dois membership mismatch',
                      material_membership_errors(self.hub, self.rows))

    def test_unknown_route_rejected_by_general_membership_and_status(self):
        self.hub['record_ids'].append('synthetic-unknown')
        self.assertTrue(material_membership_errors(self.hub, self.rows))
        self.assertFalse(hub_publication_status_matches(self.hub, self.rows))

    def test_erasing_legacy_component_product_identity_breaks_direct_membership(self):
        rid = sorted(LITTAU_SI_ROUTES)[0]
        self.byid[rid]['material'] = {'formula': 'Si', 'components': [], 'architecture': 'single_material'}
        self.assertIn('Si: complete canonical direct_record_ids membership mismatch',
                      material_membership_errors(self.hub, self.rows))


if __name__ == '__main__':
    unittest.main()
