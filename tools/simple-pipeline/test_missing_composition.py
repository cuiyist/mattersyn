"""Synthetic conversion/CLI regressions; no paper or model input is read."""
import copy
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('to_site_missing_composition', Path(__file__).with_name('to_site.py'))
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)


def pair(product, composition=None, reactor='vial'):
    return {'product': product, 'structure': {'composition': composition},
            'recipe': {'chemicals': [{'name': 'water', 'role': 'solvent', 'amount': 2, 'unit': 'mL', 'page': 2}],
                       'steps': [{'action': 'mix', 'description': 'Mix', 'time': 3, 'page': 2}],
                       'reactor': {'value': reactor, 'page': 2}}}


def document(pairs):
    return {'id': 'invented', 'doi': '10.1234/invented', 'authors': 'Example', 'year': '2026',
            'check': 'two passes agree, quotes found', 'pairs': pairs}


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


class MissingCompositionTests(unittest.TestCase):
    def convert(self, item, index=1):
        return converter.Builder(document([item])).record(item, index)

    def test_sample_label_without_composition_cannot_become_material(self):
        for composition in (None, {'value': None, 'page': 2}, {'value': '', 'page': 2}, {'value': '  ', 'page': 2}):
            with self.subTest(composition=composition):
                self.assertIsNone(self.convert(pair('Sample B', composition)))
        self.assertIsNone(self.convert(pair('SampleB')))

    def test_product_formula_fallbacks_remain_valid_without_composition(self):
        for product in ('PbSe/Pb1-xEuxTe', 'InGaAs/InP', 'CdSe'):
            with self.subTest(product=product):
                record = self.convert(pair(product))
                self.assertEqual(record['material']['formula'], product)
                self.assertEqual(record['quality']['review_status'], 'source_extracted')
                self.assertIsNone(record['products'][0]['composition']['value'])

    def test_existing_complex_formula_parser_and_text_fallback_are_preserved(self):
        for product, expected in (('Cd(Te, Se)/ZnSe quantum dots', 'Cd(Te,Se)/ZnSe'),
                                  ('Cd[Te, Se]/ZnSe quantum dots', 'Cd[Te,Se]/ZnSe'),
                                  ('Cs1-xRbxPbBr3 nanocrystals', 'Cs1-xRbxPbBr3'),
                                  ('Cu2−xS nanocrystals', 'Cu2−xS')):
            with self.subTest(product=product):
                self.assertEqual(self.convert(pair(product))['material']['formula'], expected)
                self.assertEqual(converter.formula_from(product), expected)
        for text in ('Sample B', '  cadmium selenide  ', 'unidentified material'):
            self.assertEqual(converter.formula_from(text), text.strip())

    def test_explicit_composition_including_chemical_name_is_not_newly_validated(self):
        for explicit in ('InAs', 'cadmium selenide'):
            with self.subTest(explicit=explicit):
                record = self.convert(pair('Sample A', {'value': explicit, 'page': 2}))
                self.assertEqual(record['material']['formula'], explicit)
                self.assertEqual(record['products'][0]['composition']['value'], explicit)
                self.assertEqual(record['products'][0]['composition']['evidence'][0]['locator'], 'Main PDF p.2')

    def test_omission_preserves_original_ordinals_and_other_science(self):
        doc = document([pair('CdSe'), pair('Sample B'), pair('InAs', reactor='flask')])
        builder, records = converter.records_of(doc)
        self.assertEqual(builder.omitted_composition_indices, [2])
        self.assertEqual([r['record_id'].rsplit('-', 1)[-1] for r in records], ['1', '3'])
        self.assertEqual([r['material']['formula'] for r in records], ['CdSe', 'InAs'])
        self.assertEqual(records[1], self.convert(copy.deepcopy(doc['pairs'][2]), 3))
        self.assertEqual(records[1]['materials'][0]['quantities']['volume']['value'], 2)
        self.assertEqual(records[1]['operations'][0]['parameters']['duration']['value'], 3)

    def setup_repo(self, repo, doc):
        atlas = repo / 'recipe-atlas'
        (atlas / 'data/records').mkdir(parents=True)
        put(atlas / 'data/inventory-evidence.json', {'per_paper': []})
        pairs = repo / 'pairs'
        put(pairs / 'invented.pairs.json', doc)
        return atlas, pairs

    def run_records(self, repo, pairs, replace=True):
        schema = ModuleType('schema_definition'); schema.SCHEMA = {}
        validator = SimpleNamespace(iter_errors=lambda record: [])
        output = io.StringIO()
        with mock.patch.dict(sys.modules, {'schema_definition': schema}), mock.patch('jsonschema.Draft202012Validator', return_value=validator), redirect_stdout(output):
            converter.cmd_records(SimpleNamespace(repo=repo, pairs=pairs, replace=replace, include_optical=False))
        return output.getvalue()

    def test_records_cli_omits_only_generic_pair_with_reason_and_count(self):
        with TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            repo = Path(tmp)
            doc = document([pair('Sample B'), pair('PbSe/Pb1-xEuxTe'), pair('InGaAs/InP'), pair('CdSe')])
            atlas, pairs = self.setup_repo(repo, doc)
            before = (pairs / 'invented.pairs.json').read_bytes()
            output = self.run_records(repo, pairs)
            records = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((atlas / 'data/records').glob('*.json'))]
            self.assertEqual(len(records), 3)
            self.assertEqual({r['record_id'].rsplit('-', 1)[-1] for r in records}, {'2', '3', '4'})
            self.assertIn('pair 1 left out: missing composition and no chemical formula in product', output)
            self.assertIn('1 pairs left out: missing composition and no chemical formula in product', output)
            self.assertEqual((pairs / 'invented.pairs.json').read_bytes(), before)
            row = json.loads((atlas / 'data/inventory-evidence.json').read_text())['per_paper'][0]
            self.assertEqual(set(row['record_ids']), {r['record_id'] for r in records})

    def test_all_missing_composition_adds_no_paper_inventory_entry(self):
        with TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            repo = Path(tmp); atlas, pairs = self.setup_repo(repo, document([pair('Sample B')]))
            self.run_records(repo, pairs)
            self.assertEqual(list((atlas / 'data/records').iterdir()), [])
            self.assertEqual(json.loads((atlas / 'data/inventory-evidence.json').read_text())['per_paper'], [])

    def test_replace_never_deletes_omitted_existing_or_overwrites_audited(self):
        with TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            repo = Path(tmp); doc = document([pair('Sample B'), pair('CdSe')]); atlas, pairs = self.setup_repo(repo, doc)
            sid = converter.Builder(doc).source_id
            stale = atlas / 'data/records' / f'{sid}-sample-b-1.json'
            put(stale, {'record_id': stale.stem, 'quality': {'review_status': 'source_extracted'}})
            audited = self.convert(doc['pairs'][1], 2); audited['quality']['review_status'] = 'source_reviewed'
            target = atlas / 'data/records' / f'{audited["record_id"]}.json'; put(target, audited)
            before = {p.name:p.read_bytes() for p in (stale,target)}
            self.run_records(repo, pairs, replace=True)
            self.assertEqual({p.name:p.read_bytes() for p in (stale,target)}, before)

    def test_sync_reactor_mapping_stays_with_original_retained_pair(self):
        with TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            repo = Path(tmp); doc = document([pair('Sample B', reactor='wrong omitted vessel'), pair('CdSe', reactor='retained vial')])
            atlas, pairs = self.setup_repo(repo, doc)
            retained = self.convert(doc['pairs'][1], 2)
            put(atlas / 'data/records' / f'{retained["record_id"]}.json', retained)
            put(atlas / 'data/reader-presentation-reviewed.json', {'records': {}, 'figures_by_source': {}, 'materials': {}})
            (atlas / 'static/assets/protocol').mkdir(parents=True)
            (atlas / 'static/data/protocol-art-bindings').mkdir(parents=True)
            with mock.patch.object(converter, 'bind_chemicals', return_value=(0,0)), mock.patch.object(converter, 'step_svg', wraps=converter.step_svg) as svg, redirect_stdout(io.StringIO()):
                converter.cmd_sync(SimpleNamespace(repo=repo,pairs=pairs,dist=None,include_optical=False))
            self.assertEqual(svg.call_count, 1)
            self.assertEqual(svg.call_args.args[1], 'retained vial')
            side = json.loads((atlas / 'data/reader-presentation-reviewed.json').read_text())
            self.assertEqual(set(side['records']), {retained['record_id']})

    def test_summary_fields_follow_retained_original_pair_after_omission(self):
        import summarize_batch
        omitted = pair('Sample B')
        complete = pair('Sample A', {'value': 'InAs', 'page': 2})
        complete['recipe']['chemicals'][0]['role'] = 'metal source'
        complete['recipe']['reaction_temperature'] = {'value': 100, 'unit': 'degC', 'page': 2}
        complete['recipe']['reaction_time'] = {'value': 3, 'unit': 'min', 'page': 2}
        checks = SimpleNamespace(errors=lambda record: [], material_id=lambda formula: formula)
        report = summarize_batch.summary([(Path('invented.pairs.json'), document([omitted, complete]))], checks)
        self.assertEqual(report['totals']['eligible_records'], 1)
        self.assertEqual(report['totals']['five_field_complete_records'], 1)
        row = report['papers'][0]['records'][0]
        self.assertTrue(row['record_id'].endswith('-2'))
        self.assertTrue(all(row['five_fields_present'].values()))

    def test_records_cli_exact_checked_gate_remains_required(self):
        with TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            repo=Path(tmp); doc=document([pair('CdSe')]); doc['check']='one pass, quotes found'
            atlas,pairs=self.setup_repo(repo,doc)
            with mock.patch.object(converter, 'records_of') as convert:
                self.run_records(repo,pairs)
                convert.assert_not_called()
            self.assertEqual(list((atlas / 'data/records').iterdir()), [])


if __name__ == '__main__':
    unittest.main()
