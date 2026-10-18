"""Invented-input regressions for named multilayer and superlattice routes."""
import copy
import unittest
from unittest.mock import patch

import to_site


def make_pair(label, composition):
    return {'product': label,
            'structure': {'composition': {'value': composition, 'page': 2},
                          'architecture': {'value': 'heterostructure', 'page': 2}},
            'recipe': {'steps': [{'action': 'grow', 'description': 'Grow the named product', 'page': 2}]}}


def record(pair):
    return to_site.Builder({'id': 'fixture', 'doi': '10.1234/stack-fixture',
                            'authors': 'Fixture', 'year': '2026'}).record(pair, 1)


class NamedGeStacks(unittest.TestCase):
    def test_exact_whole_products_have_separate_navigation_and_preserve_science(self):
        for label, composition, components, elements in [
                ('Ge nanocrystals in SiOx:Ge/SiOx multilayers', None, ['Ge', 'SiOx'], ['Ge', 'Si', 'O']),
                ('nanocrystalline Ge precipitates in SiO2 matrix', None, ['Ge', 'SiO2'], ['Ge', 'Si', 'O']),
                ('Ge nanocrystals in 4H–SiC', 'Ge', ['Ge', 'SiC'], ['Ge', 'Si', 'C']),
                ('Ge quantum dot (QD) in SiO2 matrix', 'Ge', ['Ge', 'SiO2'], ['Ge', 'Si', 'O']),
                ('Ge/Si QDSL', 'Ge/Si', ['Ge', 'Si'], ['Ge', 'Si'])]:
            with self.subTest(label=label):
                pair = make_pair(label, composition)
                before = copy.deepcopy(pair)
                actual = record(pair)
                self.assertEqual(actual['material'], {'formula': label, 'family': label,
                    'components': components, 'elements': elements, 'architecture': 'heterostructure'})
                with patch.object(to_site, '_explicit_ge_matrix_navigation', return_value=None):
                    previous = record(pair)
                actual.pop('material')
                previous.pop('material')
                self.assertEqual(actual, previous)
                self.assertEqual(pair, before)
                self.assertEqual(actual['products'][0]['composition']['value'], composition)

    def test_labels_do_not_override_conflicting_composition_or_infer_device_components(self):
        for label, composition in [
                ('Ge/Si QDSL', 'CdSe'), ('Ge/Si QDSL device', 'Ge/Si'),
                ('Ge nanocrystals in SiOx:Ge/SiOx multilayers', 'CdSe'),
                ('nanocrystalline Ge precipitates in SiO2 matrix', 'CdSe'),
                ('Ge nanocrystals in 4H–SiC', 'CdSe'),
                ('Ge quantum dot (QD) in SiO2 matrix', 'CdSe'),
                ('Ge', 'Ge'), ('6 nm Ge NC FET', 'Ge'),
                ('Ge nanocrystals on a substrate', 'Ge')]:
            with self.subTest(label=label, composition=composition):
                pair = make_pair(label, composition)
                self.assertIsNone(to_site._explicit_ge_matrix_navigation(pair))
                self.assertEqual(record(pair)['products'][0]['composition']['value'], composition)


if __name__ == '__main__':
    unittest.main()
