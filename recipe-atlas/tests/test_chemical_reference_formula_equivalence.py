import importlib.util,pathlib,unittest
P=pathlib.Path(__file__).parents[1]/'scripts/formula_equivalence.py'
spec=importlib.util.spec_from_file_location('formula_equivalence_proposal',P);f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)

class FormulaEquivalenceTests(unittest.TestCase):
    def test_actual_H_integer_group_and_element_order_cases(self):
        for left,right in [('Zn(CH3COO)2','C4H6O4Zn'),('PbBr2','Br2Pb'),('AgC2H3O2','C2H3AgO2'),('N2H4','H4N2'),('Pb(NO3)2','N2O6Pb')]:
            with self.subTest(left=left,right=right):self.assertTrue(f.formula_equivalent(left,right));self.assertTrue(f.formula_equivalent(right,left))
    def test_nested_groups(self):self.assertTrue(f.formula_equivalent('K4[Fe(CN)6]','C6FeK4N6'))
    def test_hydrate_expanded_molecular_formula(self):self.assertTrue(f.formula_equivalent('CuSO4\u00b75H2O','CuH10O9S'))
    def test_parenthesized_hydrate(self):self.assertTrue(f.formula_equivalent('Zn(CH3COO)2\u00b72(H2O)','C4H10O6Zn'))
    def test_ascii_dot_hydrate_with_no_decimal_ambiguity(self):self.assertTrue(f.formula_equivalent('CuSO4.H2O','CuH2O5S'))
    def test_spaced_ascii_hydrate_separates_coefficient(self):self.assertTrue(f.formula_equivalent('CuSO4 . 5H2O','CuH10O9S'))
    def test_wrong_hydrate_count_is_not_equal(self):self.assertFalse(f.formula_equivalent('CuSO4\u00b75H2O','CuSO4\u00b7H2O'))
    def test_unhydrated_is_not_hydrate(self):self.assertFalse(f.formula_equivalent('Zn(CH3COO)2','C4H10O6Zn'))
    def test_stoichiometry_conflict_is_not_equal(self):self.assertFalse(f.formula_equivalent('PbBr2','PbBr4'))
    def test_positive_polyatomic_charge(self):self.assertTrue(f.formula_equivalent('NH4+','H4N^+'))
    def test_negative_polyatomic_charge(self):self.assertTrue(f.formula_equivalent('SO4^2-','O4S-2'))
    def test_explicit_charge_magnitude_formats(self):self.assertTrue(f.formula_equivalent('Fe+3','Fe^3+'))
    def test_charge_conflict_not_equal(self):self.assertFalse(f.formula_equivalent('Fe^3+','Fe^2+'))
    def test_missing_charge_not_equal(self):self.assertFalse(f.formula_equivalent('NH4+','H4N'))
    def test_component_coefficients_multiply_explicit_charge(self):self.assertTrue(f.formula_equivalent('[Fe(CN)6]^3-\u00b73K+','K3Fe(CN)6'))
    def test_explicit_isotope_order(self):self.assertTrue(f.formula_equivalent('[13C]H4','H4[13C]'))
    def test_isotope_difference_not_equal(self):self.assertFalse(f.formula_equivalent('[13C]H4','CH4'))
    def test_isotope_mass_difference_not_equal(self):self.assertFalse(f.formula_equivalent('[13C]H4','[12C]H4'))
    def test_deuterium_explicit_isotope(self):self.assertTrue(f.formula_equivalent('[2H]2O','O[2H]2'))
    def test_Ac_and_OAc_ambiguous_shorthand_not_expanded(self):
        for left,right in [('Zn(OAc)2','C4H6O4Zn'),('AcOH','C2H4O2'),('OAc','C2H3O2')]:
            with self.subTest(left=left):self.assertIsNone(f.parse_formula(left));self.assertFalse(f.formula_equivalent(left,right))
    def test_exact_unsupported_strings_remain_equal_without_normalized_fallback(self):
        for value in ['Zn(OAc)2','Cd0.5Zn0.5S','Fe3+','CuSO4.5H2O','CdSe(x)']:
            with self.subTest(value=value):self.assertTrue(f.formula_equivalent(value,value))
        self.assertFalse(f.formula_equivalent('Zn(OAc)2',' Zn(OAc)2 '))
    def test_fractional_and_variable_counts_rejected(self):
        for value in ['Cd0.5Zn0.5S','Cd1/2Zn1/2S','CdSe(x)','CdSex','C(n)H(2n)','CuSO4.5H2O']:
            with self.subTest(value=value):self.assertIsNone(f.parse_formula(value))
    def test_ambiguous_unmarked_charge_not_interpreted(self):
        for value in ['Fe3+','O2+','[Fe(CN)6]3-']:
            with self.subTest(value=value):self.assertIsNone(f.parse_formula(value))
        self.assertFalse(f.formula_equivalent('Fe3+','Fe^3+'))
    def test_malformed_counts_or_groups_rejected(self):
        for value in ['H0','H02','Pb(NO3','Pb()2','Pb(NO3))2','H2O\u00b7','H2O..H2O','(H2O]','[13C','C2 H6 O','13CH4','NH4++','SO4^0-','X2','D2O']:
            with self.subTest(value=value):self.assertIsNone(f.parse_formula(value))
    def test_invalid_types_and_blank_inputs(self):
        for left,right in [(None,None),('', ''),(' ',' '),(123,'H2O'),('H2O',None)]:
            with self.subTest(left=left,right=right):self.assertFalse(f.formula_equivalent(left,right))
    def test_original_inputs_not_mutated(self):
        a='  Pb(NO3)2  ';b='N2O6Pb';self.assertTrue(f.formula_equivalent(a,b));self.assertEqual(a,'  Pb(NO3)2  ');self.assertEqual(b,'N2O6Pb')
    def test_no_graph_or_isomer_identity_output(self):
        # Shared composition is only a consistency check; there is no CID/name
        # selection or connectivity model in this API.
        key=f.parse_formula('C2H6O');self.assertIsInstance(key,f.FormulaKey);self.assertEqual(key.charge,0);self.assertFalse(hasattr(key,'cid'));self.assertFalse(hasattr(key,'bonds'))
    def test_input_and_integer_bounds(self):
        for value in ['H'+('2'*513),'('*18+'H'+')'*18,'H1000001','(H1000000)2']:
            with self.subTest(value=value):self.assertIsNone(f.parse_formula(value))
if __name__=='__main__':unittest.main()
