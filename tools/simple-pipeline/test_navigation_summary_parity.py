import contextlib
import copy
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import summarize_batch as helper
import to_site


class NavigationSummaryParity(unittest.TestCase):
    def checks(self):
        return helper.ProjectChecks(Path(__file__).parents[2])

    def doc(self, labels):
        return {'id': 'synthetic', 'doi': '10.1234/navigation-parity', 'authors': 'Fixture', 'year': '2026',
                'check': helper.CHECK, 'figures': [],
                'pairs': [{'product': label, 'structure': {'composition': {'value': label, 'page': 1}},
                           'recipe': {'steps': [{'action': 'mix', 'description': 'Invented operation', 'page': 1}]}}
                          for label in labels]}

    def compare_commands(self, labels):
        doc = self.doc(labels)
        original = copy.deepcopy(doc)
        checks = self.checks()
        report = helper.summary([(Path('synthetic.pairs.json'), doc)], checks)
        with TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            repo = Path(tmp)
            records = repo / 'recipe-atlas/data/records'
            records.mkdir(parents=True)
            inventory = repo / 'recipe-atlas/data/inventory-evidence.json'
            inventory.write_text(json.dumps({'per_paper': []}), encoding='utf-8')
            pairs = repo / 'pairs'
            pairs.mkdir()
            pairfile = pairs / 'synthetic.pairs.json'
            pairfile.write_text(json.dumps(doc), encoding='utf-8')
            before = pairfile.read_bytes()
            log = io.StringIO()
            with contextlib.redirect_stdout(log):
                to_site.cmd_records(SimpleNamespace(repo=repo, pairs=pairs, replace=True, include_optical=False))
            written = [json.loads(p.read_bytes()) for p in sorted(records.glob('*.json'))]
            self.assertEqual(pairfile.read_bytes(), before)
            actual_inventory = json.loads(inventory.read_bytes())
        self.assertEqual(doc, original)
        predicted = {r['record_id'] for r in report['papers'][0]['records'] if r['eligible']}
        self.assertEqual(predicted, {r['record_id'] for r in written})
        self.assertEqual(report['totals']['eligible_records'], len(written))
        return report, written, actual_inventory, log.getvalue()

    def test_unknown_then_valid_has_same_summary_and_writer_original_index(self):
        for unknown in ['FAPbI3', 'PVA', 'MAPbBr3']:
            with self.subTest(unknown=unknown):
                report, rows, inventory, log = self.compare_commands([unknown, 'CdS'])
                self.assertEqual((report['totals']['generated_records'], report['totals']['eligible_records']), (2, 1))
                self.assertEqual(report['papers'][0]['records'][0]['hold_reasons'], ['technical_unresolved_composition_for_navigation'])
                self.assertEqual(rows[0]['material']['formula'], 'CdS')
                self.assertTrue(rows[0]['record_id'].endswith('-2'))
                self.assertEqual(rows[0]['quality']['review_status'], 'source_extracted')
                self.assertEqual(inventory['per_paper'][0]['record_ids'], [rows[0]['record_id']])
                self.assertIn('technical unresolved composition for navigation', log)
                self.assertNotIn('missing composition', log)

    def test_all_unknown_is_technical_hold_and_no_written_inventory(self):
        report, rows, inventory, log = self.compare_commands(['FAPbI3', 'MAPbBr3'])
        self.assertEqual(rows, [])
        self.assertEqual(inventory['per_paper'], [])
        self.assertEqual(report['totals']['eligible_papers'], 0)
        self.assertTrue(all(r['hold_reasons'] == ['technical_unresolved_composition_for_navigation']
                            for r in report['papers'][0]['records']))

    def test_grouped_known_symbols_stay_eligible_without_expanding_acronym(self):
        report, rows, inventory, log = self.compare_commands(['(Cs/FA)Pb(Br/I)3', 'CdS'])
        self.assertEqual(report['totals']['eligible_records'], 2)
        grouped = next(r for r in rows if r['material']['formula'] == '(Cs/FA)Pb(Br/I)3')
        self.assertEqual(grouped['material']['elements'], ['Cs', 'Pb', 'Br', 'I'])
        self.assertEqual(grouped['material']['components'], ['(Cs/FA)Pb(Br/I)3'])

    def test_explicit_empty_never_calls_atlas_fallback(self):
        record = to_site.records_of(self.doc(['FAPbI3']))[1][0]
        checks = self.checks()
        self.assertEqual(record['material']['elements'], [])
        with patch.object(checks, 'elements', side_effect=AssertionError('fallback must not run')):
            self.assertEqual(checks.errors(record), ['technical_unresolved_composition_for_navigation'])

    def test_prior_schema_and_route_rejections_keep_priority(self):
        record = to_site.records_of(self.doc(['FAPbI3']))[1][0]
        checks = self.checks()
        invalid = copy.deepcopy(record)
        invalid.pop('record_id')
        self.assertEqual(checks.errors(invalid), ['schema_invalid'])
        with patch.object(checks, 'is_route', return_value=False):
            self.assertEqual(checks.errors(record), ['no_synthesis_operation'])


if __name__ == '__main__':
    unittest.main()
