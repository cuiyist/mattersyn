"""Invented-input navigation regressions; no paper/model/extraction file is read."""
import copy
import unittest
from unittest.mock import patch
import to_site


B_LABEL = 'Ge quantum dots with boron on Ge wetting layer'
B_STEPS = [{'action':'deposit','description':'Deposition of boron','page':2},
           {'action':'deposit','description':'Deposition of Ge top layer','page':2}]


def pair(label, composition='Ge', steps=None):
    return {'product':label,'structure':{'composition':{'value':composition,'page':2}},
            'recipe':{'steps':copy.deepcopy(B_STEPS if steps is None else steps)}}


def record(item):
    return to_site.Builder({'id':'invented','doi':'10.1234/invented-ge-navigation',
                            'authors':'Fixture','year':'2026'}).record(item,1)


class ExplicitGeNavigation(unittest.TestCase):
    def test_named_whole_products_keep_distinct_supported_navigation(self):
        cases=[(B_LABEL,'Ge/B',['Ge','B'],['Ge','B']),
               ('Ge NCs in Ge/SiO2/Si sample','Ge/SiO2/Si',['Ge','Si','O'],['Ge','SiO2','Si']),
               ('Ge quantum dots in amorphous SiO2 matrix','Ge/SiO2',['Ge','Si','O'],['Ge','SiO2'])]
        for label,formula,elements,components in cases:
            with self.subTest(label=label):
                item=pair(label);before=copy.deepcopy(item);actual=record(item)
                self.assertEqual(actual['material'],{'formula':formula,'family':label,'elements':elements,
                                                    'components':components,'architecture':'composite'})
                self.assertEqual(item,before)

    def test_navigation_never_changes_reported_product_or_other_science(self):
        for label in [B_LABEL,'Ge NCs in Ge/SiO2/Si sample','Ge quantum dots in amorphous SiO2 matrix']:
            with self.subTest(label=label):
                item=pair(label);actual=record(item)
                with patch.object(to_site,'_named_ge_product_formula',return_value=None):
                    previous=record(item)
                self.assertEqual(actual['products'],previous['products'])
                self.assertEqual(actual['intended_target'],previous['intended_target'])
                self.assertEqual(actual['products'][0]['composition']['value'],'Ge')
                self.assertEqual(actual['products'][0]['composition']['status'],'reported')
                self.assertEqual(actual['products'][0]['composition']['evidence'][0]['locator'],'Main PDF p.2')
                self.assertEqual(actual['products'][0]['source_sample_label'],label)
                self.assertEqual(actual['products'][0]['phase']['status'],'not_reported')
                self.assertEqual(actual['quality']['review_status'],'source_extracted')
                actual.pop('material');previous.pop('material');self.assertEqual(actual,previous)

    def test_bare_ge_does_not_acquire_matrix_substrate_or_boron_from_operations(self):
        for label in ['Ge','Ge quantum dots','Ge quantum dots on Si substrate']:
            with self.subTest(label=label):
                actual=record(pair(label))
                self.assertEqual(actual['material']['formula'],'Ge')
                self.assertEqual(actual['material']['elements'],['Ge'])
                self.assertEqual(actual['material']['architecture'],'single_material')

    def test_boron_precursor_or_mention_alone_does_not_add_product_component(self):
        item=pair('Ge quantum dots',steps=[{'action':'mix','description':'Boron precursor mentioned','page':2}])
        item['recipe']['chemicals']=[{'name':'boron precursor','role':'reagent','page':2}]
        self.assertEqual(record(item)['material']['components'],['Ge'])
        self.assertIsNone(to_site._named_ge_product_formula(item))
        self.assertIsNone(to_site._named_ge_product_formula(pair('Ge quantum dots with boron')))

    def test_exact_boron_label_requires_both_ordered_deposition_descriptions(self):
        for steps in [[],B_STEPS[:1],B_STEPS[1:],list(reversed(B_STEPS)),
                      [{'action':'deposit','description':'Boron mentioned','page':2},B_STEPS[1]],
                      [B_STEPS[0],{'action':'deposit','description':'Deposition of Ge','page':2}]]:
            with self.subTest(steps=steps):
                item=pair(B_LABEL,steps=steps)
                self.assertIsNone(to_site._named_ge_product_formula(item))
                self.assertEqual(record(item)['material']['formula'],'Ge')
                self.assertEqual(record(item)['material']['components'],['Ge'])

    def test_non_ge_reported_composition_is_never_overridden_by_named_label(self):
        for label in [B_LABEL,'Ge NCs in Ge/SiO2/Si sample','Ge quantum dots in amorphous SiO2 matrix']:
            for stated in ['SiO2','Ge/GeOx','CdSe']:
                with self.subTest(label=label,stated=stated):
                    item=pair(label,composition=stated)
                    self.assertIsNone(to_site._named_ge_product_formula(item))
                    actual=record(item)
                    self.assertEqual(actual['material']['formula'],stated)
                    self.assertEqual(actual['products'][0]['composition']['value'],stated)
                    self.assertEqual(actual['intended_target']['composition']['value'],stated)

    def test_matrix_without_reported_composition_leaves_product_fact_unreported(self):
        item=pair('Ge quantum dots in amorphous SiO2 matrix',composition=None,steps=[])
        item['structure']['composition']=None
        actual=record(item)
        self.assertEqual(actual['material']['formula'],'Ge/SiO2')
        self.assertIsNone(actual['products'][0]['composition']['value'])
        self.assertEqual(actual['products'][0]['composition']['status'],'not_reported')

    def test_existing_embedded_and_compound_navigation_is_preserved(self):
        legacy=record(pair('nanocrystalline Ge embedded in SiO2 matrix',steps=[]))
        self.assertEqual(legacy['material']['formula'],'Ge/SiO2')
        self.assertEqual(legacy['material']['family'],'Ge/SiO2 nanocrystals')
        self.assertEqual(legacy['material']['architecture'],'composite')
        for composition in ['Cd(Te,Se)/ZnSe','(Cs/FA)Pb(Br/I)3','CdSe/ZnS','Cs1-xRbxPbBr3']:
            with self.subTest(composition=composition):
                actual=record(pair(composition,composition=composition,steps=[]))
                self.assertEqual(actual['material']['formula'],composition)
                self.assertEqual(actual['material']['family'],composition+' nanocrystals')
                self.assertEqual(actual['products'][0]['composition']['value'],composition)

    def test_lowercase_element_spelling_does_not_become_chemical_navigation(self):
        for label in ['ge quantum dots in amorphous sio2 matrix',
                      'Ge NCs in Ge/sio2/Si sample',
                      'ge quantum dots with boron on ge wetting layer']:
            with self.subTest(label=label):
                self.assertIsNone(to_site._named_ge_product_formula(pair(label)))


if __name__=='__main__':unittest.main()
