"""Invented-input tests only; no paper, model, pair payload or source evidence is read."""
import copy
import importlib.util
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SOURCE / 'recipe-atlas/scripts'))
CANDIDATE = Path(os.environ.get('MATTERSYN_TO_SITE_CANDIDATE', Path(__file__).with_name('to_site.py')))
spec = importlib.util.spec_from_file_location('to_site_named_composite_candidate', CANDIDATE)
to_site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(to_site)
RAW = 'nc-(Ti,Al)N12x/a-SiNy composite film'
NAMED = 'nc-(Ti,Al)N1−x/a-SiNy composite film'
EXPECTED = {'formula': NAMED, 'family': NAMED, 'elements': ['Ti', 'Al', 'N', 'Si'],
            'components': ['nc-(Ti,Al)N1−x', 'a-SiNy'], 'architecture': 'composite'}


def pair(label=RAW, composition='Ti,Al,N,Si', architecture='composite'):
    item = {'product': label, 'structure': {'composition': {'value': composition, 'page': 2}},
            'recipe': {'steps': [{'action': 'cool', 'description': 'Cool in vacuum', 'page': 2}]}}
    if architecture is not None:
        item['structure']['architecture'] = {'value': architecture, 'page': 2}
    return item


def record(item):
    return to_site.Builder({'id': 'invented', 'doi': '10.1234/invented-named-composite',
                            'authors': 'Fixture', 'year': '2026'}).record(item, 1)


class ExactNamedCompositeNavigation(unittest.TestCase):
    def test_exact_whole_product_labels_and_reported_composition(self):
        for label in [RAW, NAMED, '  ' + RAW.replace(' composite ', '  composite  ') + '  ']:
            for composition in ['Ti,Al,N,Si', ' Ti, Al, N, Si ']:
                with self.subTest(label=label, composition=composition):
                    item = pair(label, composition); before = copy.deepcopy(item)
                    self.assertEqual(to_site._explicit_tialn_siny_navigation(item), EXPECTED)
                    self.assertEqual(record(item)['material'], EXPECTED)
                    self.assertEqual(item, before)

    def test_only_navigation_changes_and_identity_and_science_stay_exact(self):
        item = pair(); before = copy.deepcopy(item); actual = record(item)
        with patch.object(to_site, '_explicit_tialn_siny_navigation', return_value=None):
            previous = record(item)
        self.assertEqual(actual['record_id'], previous['record_id'])
        self.assertIn('n12x', actual['record_id'])
        self.assertEqual(actual['products'], previous['products'])
        self.assertEqual(actual['intended_target'], previous['intended_target'])
        self.assertEqual(actual['products'][0]['composition']['value'], 'Ti,Al,N,Si')
        self.assertEqual(actual['products'][0]['composition']['status'], 'reported')
        self.assertEqual(actual['products'][0]['composition']['evidence'][0]['locator'], 'Main PDF p.2')
        self.assertEqual(actual['products'][0]['source_sample_label'], RAW)
        self.assertEqual(actual['quality']['review_status'], 'source_extracted')
        self.assertEqual(actual['structure_assets'], [])
        actual.pop('material'); previous.pop('material'); self.assertEqual(actual, previous)
        self.assertEqual(item, before)

    def test_partial_device_contradictory_or_missing_facts_never_trigger(self):
        for label in ['Si', 'nc-(Ti,Al)N1−x', RAW + ' device', RAW + ' on Si substrate',
                      RAW.replace('N12x', 'N2x'), RAW.lower()]:
            with self.subTest(label=label):
                self.assertIsNone(to_site._explicit_tialn_siny_navigation(pair(label)))
        for composition in [None, '', 'Si', 'TiAlN', 'Ti,N,Al,Si', 'Ti,Al,N,Si,O']:
            with self.subTest(composition=composition):
                self.assertIsNone(to_site._explicit_tialn_siny_navigation(pair(composition=composition)))
        missing = pair(); missing['structure']['composition'] = None
        self.assertIsNone(to_site._explicit_tialn_siny_navigation(missing))
        for architecture in ['core_shell', 'heterostructure', 'alloy', 'single_material']:
            with self.subTest(architecture=architecture):
                self.assertIsNone(to_site._explicit_tialn_siny_navigation(pair(architecture=architecture)))

    def test_no_pure_silicon_component_or_measured_structure_is_inferred(self):
        for architecture in [None, 'unresolved', 'composite']:
            actual = record(pair(architecture=architecture))
            self.assertEqual(actual['material'], EXPECTED)
            self.assertNotIn('Si', actual['material']['components'])
            self.assertNotEqual(actual['material']['formula'], 'Si')
            self.assertEqual(actual['structure_assets'], [])
            self.assertEqual(actual['products'][0]['phase']['status'], 'not_reported')

    def test_existing_ge_and_normal_compounds_are_unchanged(self):
        for label, composition in [('Ge nanocrystals embedded in GeO2 matrix', 'Ge'),
                                   ('Ge/Si QDSL', 'Ge/Si'), ('CdSe', 'CdSe'), ('Si', 'Si')]:
            with self.subTest(label=label):
                item = pair(label, composition, architecture=None); actual = record(item)
                with patch.object(to_site, '_explicit_tialn_siny_navigation', return_value=None):
                    previous = record(item)
                self.assertEqual(actual, previous)


if __name__ == '__main__':
    unittest.main(verbosity=2)
