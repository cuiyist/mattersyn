import unittest
import to_site

class ComponentsTests(unittest.TestCase):
    def record(self, formula, architecture=None):
        structure = {'composition': {'value': formula, 'page': 1}}
        if architecture is not None: structure['architecture'] = {'value': architecture, 'page': 1}
        return to_site.Builder({'id':'synthetic','doi':'10.1234/synthetic','authors':'Example','year':'2026'}).record({'product': formula, 'structure': structure, 'recipe':{}}, 1)

    def test_explicit_compound_separators_preserve_variable_components(self):
        for sep in ('/', '@', '-', '–', '—', '−'):
            formula = 'CsPbBr3' + sep + 'PbxBiySz'
            self.assertEqual(to_site.components_of(formula), ['CsPbBr3', 'PbxBiySz'])
            self.assertEqual(self.record(formula)['material']['formula'], formula)
            self.assertEqual(self.record(formula)['material']['elements'], ['Cs','Pb','Br','Bi','S'])

    def test_stoichiometric_minus_is_not_a_component_separator(self):
        for formula in ('Cs1−xRbxPbBr3', 'Cs1-xRbxPbBr3', 'Cd1–xZnxSe', 'Cu2−xS', 'SiOx'):
            self.assertEqual(to_site.components_of(formula), [formula])

    def test_unicode_cdse_zns_components_display_in_parallel(self):
        for sep in ('–','−'):
            self.assertEqual(self.record('CdSe'+sep+'ZnS')['material']['components'], ['CdSe','ZnS'])

    def test_component_punctuation_does_not_assert_core_shell_architecture(self):
        for formula in ('CdSe/ZnS','CdSe–ZnS','CsPbBr3−PbxBiySz'):
            self.assertEqual(self.record(formula)['material']['architecture'],'unresolved')

    def test_explicit_checked_architecture_is_preserved(self):
        for supplied, expected in [('core/shell','core_shell'), ('core_shell','core_shell'), ('heterostructure','heterostructure'), ('composite','composite'), ('alloy','alloy'), ('phase_mixture','phase_mixture')]:
            self.assertEqual(self.record('CdSe/ZnS', supplied)['material']['architecture'], expected)

    def test_single_composition_default_is_unchanged(self):
        self.assertEqual(self.record('CdSe')['material']['architecture'],'single_material')

if __name__ == '__main__': unittest.main()
