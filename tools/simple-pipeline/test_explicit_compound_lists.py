import copy
import unittest
import to_site

class ExplicitCompoundListTests(unittest.TestCase):
    def pair(self, composition, architecture='heterostructure', product='branched sample'):
        return {'product': product, 'structure': {'composition': {'value': composition, 'page': 2}, 'architecture': {'value': architecture, 'page': 2}}, 'recipe': {}}

    def record(self, pair, ordinal=3):
        return to_site.Builder({'id': 'synthetic', 'doi': '10.1234/synthetic', 'authors': 'Fixture', 'year': '2026'}).record(pair, ordinal)

    def test_explicit_compounds_preserve_all_components_and_reported_fact(self):
        for composition, expected in [('CdSe, CdS', ['CdSe', 'CdS']), ('CdSe, CdTe', ['CdSe', 'CdTe']), ('CdSe, ZnS, SiO2', ['CdSe', 'ZnS', 'SiO2'])]:
            with self.subTest(composition=composition):
                pair = self.pair(composition)
                before = copy.deepcopy(pair)
                record = self.record(pair)
                self.assertEqual(record['material']['formula'], '/'.join(expected))
                self.assertEqual(record['material']['components'], expected)
                self.assertEqual(record['material']['elements'], to_site.elements_of('/'.join(expected)))
                self.assertEqual(record['material']['architecture'], 'heterostructure')
                self.assertEqual(record['intended_target']['composition']['value'], composition)
                self.assertEqual(pair, before)
                self.assertTrue(record['record_id'].endswith('-branched-sample-3'))
                self.assertEqual(record['quality']['review_status'], 'source_extracted')

    def test_only_explicit_multimaterial_architectures_use_the_list(self):
        for architecture in ('core/shell', 'core_shell', 'heterostructure', 'composite', 'phase_mixture'):
            with self.subTest(architecture=architecture):
                self.assertEqual(self.record(self.pair('CdSe, ZnS', architecture))['material']['components'], ['CdSe', 'ZnS'])
        for architecture in (None, '', 'single_material', 'core', 'doped', 'alloy', 'unresolved', 'core/arms'):
            with self.subTest(architecture=architecture):
                self.assertEqual(to_site._composition_from(self.pair('CdSe, ZnS', architecture)), to_site.formula_from('CdSe, ZnS'))

    def test_element_dopant_grouped_and_prose_lists_are_not_expanded(self):
        for composition in ('Cd, Se', 'Mn, ZnS', 'CdSe, Mn', '(Cd,Zn)Se, ZnS', 'Cd1-xZnxSe, ZnS', 'CdSe, CdS nanorods', 'CdSe, CdSe'):
            with self.subTest(composition=composition):
                self.assertEqual(to_site._composition_from(self.pair(composition)), to_site.formula_from(composition))

    def test_missing_product_keeps_existing_identity_fallback(self):
        self.assertEqual(to_site._composition_from(self.pair('CdSe, CdS', product=None)), 'CdSe')

    def test_existing_separators_and_fa_alias_are_unchanged(self):
        for composition in ('CdSe/ZnS', '(Cd,Zn)Se', 'Cu2-xSe', 'FAPbBr3'):
            self.assertEqual(to_site._composition_from(self.pair(composition)), to_site.formula_from(composition))
        self.assertEqual(to_site.elements_of('FAPbBr3'), ['C', 'H', 'N', 'Pb', 'Br'])

if __name__ == '__main__':
    unittest.main()
