import copy, unittest
from unittest.mock import patch
import to_site

class PolytypeImporterRegression(unittest.TestCase):
    def test_importer_keeps_polytype_whole_without_changing_other_record_fields(self):
        for formula in ('3C-SiC','6H-SiC','2H-MoS2'):
            with self.subTest(formula=formula):
                pair={'product':formula+' nanocrystals','structure':{'composition':{'value':formula,'page':1},'architecture':{'value':'unresolved','page':1},'phase':{'value':'reported fixture label','page':1}},'recipe':{}}
                original=copy.deepcopy(pair)
                doc={'id':'synthetic','doi':'10.1234/polytype','authors':'Fixture','year':'2026'}
                # The old importer split this prefix into a separate component.
                with patch.object(to_site,'components_of',return_value=formula.split('-')):
                    before=to_site.Builder(doc).record(pair,1)
                actual=to_site.Builder(doc).record(pair,1)
                self.assertEqual(actual['material']['components'],[formula])
                self.assertEqual(actual['material']['formula'],formula)
                self.assertEqual(actual['material']['architecture'],'unresolved')
                before['material'].pop('components');actual['material'].pop('components')
                self.assertEqual(actual,before)
                self.assertEqual(pair,original)
        for formula, expected in [('CdSe/ZnS',['CdSe','ZnS']),('CdSe-ZnS',['CdSe','ZnS']),('CsPbBr3-PbxBiySz',['CsPbBr3','PbxBiySz']),('Cs1-xRbxPbBr3',['Cs1-xRbxPbBr3']),('3C-SiC/ZnS',['3C','SiC','ZnS']),('3X-SiC',['3X','SiC']),('0C-SiC',['0C','SiC']),('3C-Protein',['3C','Protein'])]:
            with self.subTest(unchanged=formula):
                self.assertEqual(to_site.components_of(formula),expected)

if __name__=='__main__':unittest.main()
