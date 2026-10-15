import unittest
import to_site

class FormulaParsingTests(unittest.TestCase):
    def test_variable_heterostructure_precedes_nc_abbreviation(self):
        stated='CsPbBr3/PbxBiySz'
        self.assertEqual(to_site.formula_from(stated+' NC heterostructures'),stated)
        self.assertEqual(to_site.elements_of(stated),['Cs','Pb','Br','Bi','S'])
    def test_unicode_separator_precedes_later_substrate_formula(self):
        for sep in ('–','—'):
            stated='CdSe'+sep+'ZnS'
            self.assertEqual(to_site.formula_from(stated+' NCs on TiO2'),stated)
            self.assertEqual(to_site.elements_of(stated),['Cd','Se','Zn','S'])
    def test_variable_stoichiometry_remains_exactly_as_stated(self):
        for stated,elements in [('Cs1−xRbxPbBr3',['Cs','Rb','Pb','Br']),('Cd1-xZnxSe',['Cd','Zn','Se']),('Cu2-xS',['Cu','S']),('SiOx',['Si','O'])]:
            self.assertEqual(to_site.formula_from(stated+' nanocrystals'),stated)
            self.assertEqual(to_site.elements_of(stated),elements)
    def test_unknown_product_does_not_become_nc_chemistry(self):
        stated='unknown product NC heterostructures'
        self.assertEqual(to_site.formula_from(stated),stated)
    def test_existing_plain_compositions_are_unchanged(self):
        for stated in ('CdSe','ZnO','TiO2','CsPbBr3','InAs','Au','C6H12N3P','Ca(OH)2'):
            self.assertEqual(to_site.formula_from(stated+' particles'),stated)
    def test_grouped_alloy_commas_preserve_the_full_product(self):
        for phrase in ('Cd(Te,Se)/ZnSe quantum dots', 'Cd(Te, Se)/ZnSe quantum dots',
                       'Cd(Te, Se) / ZnSe quantum dots', '( Cd(Te, Se) / ZnSe ) quantum dots'):
            self.assertEqual(to_site.formula_from(phrase),'Cd(Te,Se)/ZnSe')
        stated=to_site.formula_from('Cd(Te, Se)/ZnSe quantum dots')
        self.assertEqual(to_site.elements_of(stated),['Cd','Te','Se','Zn'])
        self.assertEqual(to_site.components_of(stated),['Cd(Te,Se)','ZnSe'])
    def test_top_level_commas_remain_product_separators(self):
        for phrase in ('CdSe,CdS nanocrystals','CdSe, CdS nanocrystals'):
            self.assertEqual(to_site.formula_from(phrase),'CdSe')
    def test_formula_groups_and_external_wrappers_stay_distinct(self):
        for phrase,expected in [('K4[Fe(CN)6] particles','K4[Fe(CN)6]'),
                                ('[CdSe] particles','CdSe'),
                                ('Cd[Te, Se]/ZnSe quantum dots','Cd[Te,Se]/ZnSe'),
                                ('CdSe @ ZnS nanocrystals','CdSe@ZnS')]:
            self.assertEqual(to_site.formula_from(phrase),expected)
    def test_incomplete_group_does_not_become_a_truncated_formula(self):
        phrase='Cd(Te,Se malformed phrase'
        self.assertEqual(to_site.formula_from(phrase),phrase)

if __name__=='__main__':unittest.main()
