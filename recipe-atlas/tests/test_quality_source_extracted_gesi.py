"""Additional Ge/Si routes must preserve the exact reviewed template inventory."""
import ast
import copy
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import check_quality as quality


def production_reviewed_check(hub, byid):
    # Execute the actual assertion expression, rather than duplicating its logic.
    tree = ast.parse((SCRIPTS / 'check_quality.py').read_text(encoding='utf-8'))
    message = 'Ge/Si: both reviewed template variants must remain direct routes'
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == 'check'
             and len(node.args) == 2 and isinstance(node.args[1], ast.Constant)
             and node.args[1].value == message]
    if len(calls) != 1:
        raise AssertionError('Expected one production Ge/Si reviewed-route assertion')
    expression = ast.Expression(calls[0].args[0])
    return eval(compile(ast.fix_missing_locations(expression), '<quality assertion>', 'eval'),
                vars(quality), {'self': SimpleNamespace(hubs={'Ge/Si': hub}, byid=byid)})


def record(rid, status='source_reviewed'):
    return {'record_id': rid, 'collection': 'reviewed_literature',
            'record_type': 'literature_protocol', 'reader_role': 'synthesis_route',
            'quality': {'review_status': status, 'requested_tasks': []},
            'operations': [{'stage': 'synthesis'}],
            'material': {'formula': 'Ge/Si', 'components': ['Ge', 'Si'],
                         'architecture': 'heterostructure'},
            'lineage': {'source_group': rid},
            'sources': [{'id': rid, 'doi': '10.fixture/' + rid}]}


class GeSiReviewedInventory(unittest.TestCase):
    def setUp(self):
        self.rows = [record(rid) for rid in sorted(quality.HEATH_GE_SI_ROUTES)]
        self.rows += [record('additional-gesi-a', 'source_extracted'),
                      record('additional-gesi-b', 'source_extracted')]
        self.byid = {r['record_id']: r for r in self.rows}
        self.hub = {'formula': 'Ge/Si', 'record_ids': list(self.byid),
                    'direct_record_ids': list(self.byid),
                    'paper_dois': sorted({quality.primary_doi(r) for r in self.rows})}

    def test_additional_extracted_routes_preserve_reviewed_inventory(self):
        self.assertTrue(production_reviewed_check(self.hub, self.byid))
        self.assertEqual([], quality.material_membership_errors(self.hub, self.rows))

    def test_legacy_reviewed_only_hub_still_passes(self):
        self.hub['direct_record_ids'] = sorted(quality.HEATH_GE_SI_ROUTES)
        self.assertTrue(production_reviewed_check(self.hub, self.byid))

    def test_each_missing_heath_direct_route_fails(self):
        for rid in quality.HEATH_GE_SI_ROUTES:
            hub = copy.deepcopy(self.hub)
            hub['direct_record_ids'].remove(rid)
            with self.subTest(rid=rid):
                self.assertFalse(production_reviewed_check(hub, self.byid))

    def test_reviewed_status_cannot_be_demoted(self):
        for rid in quality.HEATH_GE_SI_ROUTES:
            byid = copy.deepcopy(self.byid)
            byid[rid]['quality']['review_status'] = 'source_extracted'
            with self.subTest(rid=rid):
                self.assertFalse(production_reviewed_check(self.hub, byid))

    def test_additional_extracted_route_cannot_be_called_reviewed(self):
        self.byid['additional-gesi-a']['quality']['review_status'] = 'source_reviewed'
        self.assertFalse(production_reviewed_check(self.hub, self.byid))

    def test_general_membership_rejects_unknown_draft_or_wrong_product(self):
        for mutation in ('unknown', 'draft', 'wrong-product', 'missing-extracted'):
            rows, hub = copy.deepcopy(self.rows), copy.deepcopy(self.hub)
            if mutation == 'unknown':
                hub['record_ids'].append('unknown-gesi')
                hub['direct_record_ids'].append('unknown-gesi')
            elif mutation == 'draft':
                rows[-1]['quality']['review_status'] = 'draft'
            elif mutation == 'wrong-product':
                rows[-1]['material']['formula'] = 'Ge/SiO2'
            else:
                hub['direct_record_ids'].remove('additional-gesi-b')
            with self.subTest(mutation=mutation):
                self.assertTrue(quality.material_membership_errors(hub, rows))


if __name__ == '__main__':
    unittest.main()
