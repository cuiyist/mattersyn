"""Pin reviewed Tirosh routes while validating every later canonical contribution."""
import ast
import copy
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import check_quality as quality

# Exercise the actual production assertion, not a copied predicate. Keep the
# historical expected set and component-only test connected to Audit.materials.
tree = ast.parse(Path(quality.__file__).read_text(encoding='utf-8'))
materials = next(method for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'Audit'
                 for method in node.body if isinstance(method, ast.FunctionDef) and method.name == 'materials')
start = next(i for i, node in enumerate(materials.body) if isinstance(node, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == 'ferrite' for t in node.targets))
expected_node = materials.body[start + 1]
check_node = materials.body[start + 2]
if (not isinstance(expected_node, ast.Assign) or
        not isinstance(expected_node.targets[0], ast.Name) or expected_node.targets[0].id != 'tirosh_direct' or
        not isinstance(check_node, ast.Expr) or not isinstance(check_node.value, ast.Call) or
        not isinstance(check_node.value.func, ast.Attribute) or check_node.value.func.attr != 'check' or
        check_node.value.args[1].value != 'CoFe2O4: the three reviewed Tirosh Method-A temperature routes must be direct contributions'):
    raise AssertionError('Historical ferrite assertion shape changed')
TIROSH = ast.literal_eval(expected_node.value)
PREDICATE = compile(ast.Expression(check_node.value.args[0]), str(quality.__file__), 'eval')
SAHA = 'saha-2019-coo-cofe2o4-seeded-growth'


def record(rid, formula='CoFe2O4', components=None, status='source_reviewed'):
    return {'record_id': rid, 'collection': 'reviewed_literature',
            'record_type': 'literature_protocol', 'reader_role': 'synthesis_route',
            'quality': {'review_status': status, 'requested_tasks': []},
            'operations': [{'stage': 'synthesis'}],
            'material': {'formula': formula, 'components': components or []},
            'lineage': {'source_group': rid},
            'sources': [{'id': rid, 'doi': '10.fixture/' + rid}]}


class FerriteReviewedInventory(unittest.TestCase):
    def setUp(self):
        self.rows = [record(rid) for rid in sorted(TIROSH)] + [
            record(SAHA, 'CoO/CoFe2O4', ['CoO', 'CoFe2O4']),
            record('new-direct', status='source_extracted'),
            record('new-component', 'CoFe2O4/PbS', ['CoFe2O4', 'PbS'], 'source_extracted')]
        self.hub = {'formula': 'CoFe2O4', 'component_only': False,
                    'publication_status': 'verified_synthesis_contribution',
                    'record_ids': [r['record_id'] for r in self.rows],
                    'direct_record_ids': sorted(TIROSH) + ['new-direct'],
                    'paper_dois': ['10.fixture/' + r['record_id'] for r in self.rows]}

    def historical_matches(self, hub=None, rows=None):
        hub = self.hub if hub is None else hub
        rows = self.rows if rows is None else rows
        return eval(PREDICATE, vars(quality), {'ferrite': hub, 'tirosh_direct': TIROSH,
                    'self': SimpleNamespace(byid={r['record_id']: r for r in rows})})

    def test_exact_historical_three_ids_remain_pinned(self):
        self.assertEqual({'tirosh-2006-cofe2o4-method-a-230c',
                          'tirosh-2006-cofe2o4-method-a-250c',
                          'tirosh-2006-cofe2o4-method-a-270c'}, TIROSH)

    def test_extracted_direct_and_component_routes_are_allowed(self):
        self.assertTrue(self.historical_matches())
        self.assertEqual([], quality.material_membership_errors(self.hub, self.rows))
        self.assertTrue(quality.hub_publication_status_matches(self.hub, self.rows))

    def test_each_missing_tirosh_direct_route_is_rejected(self):
        for rid in TIROSH:
            hub = copy.deepcopy(self.hub)
            hub['direct_record_ids'].remove(rid)
            with self.subTest(rid=rid):
                self.assertFalse(self.historical_matches(hub))
                self.assertTrue(quality.material_membership_errors(hub, self.rows))

    def test_tirosh_demotion_is_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['quality']['review_status'] = 'source_extracted'
        self.assertFalse(self.historical_matches(rows=rows))

    def test_extra_reviewed_direct_is_rejected(self):
        rows = self.rows + [record('extra-reviewed')]
        hub = copy.deepcopy(self.hub)
        hub['record_ids'].append('extra-reviewed')
        hub['direct_record_ids'].append('extra-reviewed')
        hub['paper_dois'].append('10.fixture/extra-reviewed')
        self.assertEqual([], quality.material_membership_errors(hub, rows))
        self.assertFalse(self.historical_matches(hub, rows))

    def test_extracted_direct_cannot_be_promoted_to_reviewed(self):
        rows = copy.deepcopy(self.rows)
        next(r for r in rows if r['record_id'] == 'new-direct')['quality']['review_status'] = 'source_reviewed'
        self.assertFalse(self.historical_matches(rows=rows))

    def test_reviewed_component_cannot_be_promoted_to_direct(self):
        hub = copy.deepcopy(self.hub)
        hub['direct_record_ids'].append(SAHA)
        self.assertFalse(self.historical_matches(hub))
        self.assertTrue(quality.material_membership_errors(hub, self.rows))

    def test_extracted_component_promotion_still_fails_general_membership(self):
        hub = copy.deepcopy(self.hub)
        hub['direct_record_ids'].append('new-component')
        self.assertTrue(self.historical_matches(hub))
        self.assertTrue(quality.material_membership_errors(hub, self.rows))

    def test_unknown_direct_and_component_ids_still_fail_general_checks(self):
        for direct in (False, True):
            hub = copy.deepcopy(self.hub)
            hub['record_ids'].append('unknown')
            if direct:
                hub['direct_record_ids'].append('unknown')
            with self.subTest(direct=direct):
                self.assertTrue(self.historical_matches(hub))
                self.assertTrue(quality.material_membership_errors(hub, self.rows))
                self.assertFalse(quality.hub_publication_status_matches(hub, self.rows))

    def test_component_only_false_remains_required(self):
        for value in (True, None):
            hub = copy.deepcopy(self.hub)
            hub['component_only'] = value
            with self.subTest(value=value):
                self.assertFalse(self.historical_matches(hub))

    def test_pending_or_unknown_status_still_fails_general_checks(self):
        for status in ('pending', 'unknown'):
            rows = copy.deepcopy(self.rows)
            next(r for r in rows if r['record_id'] == 'new-direct')['quality']['review_status'] = status
            with self.subTest(status=status):
                self.assertTrue(self.historical_matches(rows=rows))
                self.assertTrue(quality.material_membership_errors(self.hub, rows))
                self.assertFalse(quality.hub_publication_status_matches(self.hub, rows))

    def test_noncanonical_direct_formula_still_fails_membership(self):
        rows = copy.deepcopy(self.rows)
        next(r for r in rows if r['record_id'] == 'new-direct')['material']['formula'] = 'different'
        self.assertTrue(self.historical_matches(rows=rows))
        self.assertTrue(quality.material_membership_errors(self.hub, rows))


if __name__ == '__main__':
    unittest.main()
