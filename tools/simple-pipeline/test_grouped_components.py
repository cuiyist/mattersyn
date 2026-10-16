import copy, re, unittest
from unittest.mock import patch
import to_site

def OLD(composition):
    # Exact former three-line splitter, kept only as an invented-input regression fixture.
    return [x.strip() for x in re.split(r'[/@]|(?<=[A-Za-z0-9)])[-–—−](?=[A-Z])', composition) if x.strip()]

class GroupedComponents(unittest.TestCase):
    def test_mixed_composition_is_one_complete_navigation_label(self):
        formula='(Cs/FA)Pb(Br/I)3'
        self.assertEqual(to_site.components_of(formula),[formula])
        self.assertEqual(OLD(formula),['(Cs','FA)Pb(Br','I)3'])
    def test_every_separator_inside_each_balanced_group_is_preserved(self):
        for left,right in [('(',')'),('[',']'),('{','}')]:
            for sep in ['/', '@', '-', '–', '—', '−']:
                label='Cd'+left+'Se'+sep+'Te'+right
                with self.subTest(label=label):
                    self.assertEqual(to_site.components_of(label),[label])
                    self.assertEqual(to_site.components_of(label+'/ZnS'),[label,'ZnS'])
    def test_mixed_nested_groups_do_not_create_fragments(self):
        for label in ['Cd[Se/(Te@S)]','Cd{Se/[Te–S]}','(Cs/[FA/MA])Pb(Br/I)3']:
            self.assertEqual(to_site.components_of(label+'/ZnS'),[label,'ZnS'])
    def test_unbalanced_or_mismatched_groups_remain_one_opaque_label(self):
        for label in ['Cd(Se/Te/ZnS','Cd[Se/Te)/ZnS','CdSe)/ZnS','Cd{Se/Te]/ZnS']:
            self.assertEqual(to_site.components_of(label),[label])
    def test_top_level_alias_and_variable_cases_keep_parent_results(self):
        labels=['CdSe/CdS/ZnS','Ge/GeOx','Ge/SiO2','Ge/Si','CoO/CoFe2O4','CsPbBr3/PbxBiySz','Cd(Te,Se)/ZnSe','Cd1-xZnxSe','Cs1−xRbxPbBr3','Cu2−xS','SiOx',' / CdSe / / ZnS @ ']
        labels += ['CdSe'+sep+'ZnS' for sep in ['/', '@', '-', '–', '—', '−']]
        for label in labels:
            with self.subTest(label=label):self.assertEqual(to_site.components_of(label),OLD(label))
    def test_old_outer_dash_boundary_is_not_broadened(self):
        for label in ['(CdSe)-ZnS','Cd[Te,Se]-ZnS','Cd{Te,Se}-ZnS','CdSe - ZnS','CdSe-xZnS']:
            self.assertEqual(to_site.components_of(label),OLD(label))
    def test_explicit_architecture_and_all_other_record_fields_stay_exact(self):
        formula='(Cs/FA)Pb(Br/I)3'
        pair={'product':formula,'structure':{'composition':{'value':formula,'page':1},'architecture':{'value':'unresolved','page':1}},'recipe':{}}
        before=copy.deepcopy(pair);doc={'id':'synthetic','doi':'10.1234/grouped','authors':'Fixture','year':'2026'}
        actual=to_site.Builder(doc).record(pair,1)
        with patch.object(to_site,'components_of',OLD): old=to_site.Builder(doc).record(pair,1)
        self.assertEqual(actual['material']['components'],[formula]);self.assertEqual(actual['material']['architecture'],'unresolved')
        # Whole-symbol-run elements change is tested separately; compare all remaining fields.
        for value in [actual,old]:value['material'].pop('components')
        self.assertEqual(actual,old);self.assertEqual(pair,before)

if __name__=='__main__':unittest.main()
