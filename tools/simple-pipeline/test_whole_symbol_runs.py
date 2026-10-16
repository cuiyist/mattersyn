import copy, unittest
import to_site

class WholeSymbolRuns(unittest.TestCase):
    def test_unknown_acronyms_do_not_leak_partial_elements(self):
        for token in ['FA','PVA','PANi','MWNT','FAX']:
            with self.subTest(token=token):self.assertEqual(to_site.elements_of(token),[])
    def test_mixed_group_keeps_known_symbols_without_expanding_acronym(self):
        self.assertEqual(to_site.elements_of('(Cs/FA)Pb(Br/I)3'),['Cs','Pb','Br','I'])
        self.assertEqual(to_site.elements_of('CsPbBr3/PVA'),['Cs','Pb','Br'])
        self.assertEqual(to_site.elements_of('FA/Ge'),['Ge'])
    def test_real_formula_groups_and_phase_labels_are_preserved(self):
        for formula,expected in [('CdSe',['Cd','Se']),('CsPbBr3',['Cs','Pb','Br']),('Ca(OH)2',['Ca','O','H']),('K4[Fe(CN)6]',['K','Fe','C','N']),('TiO2(B)/C',['Ti','O','C']),('B(OH)3',['B','O','H']),('C6H12N3P',['C','H','N','P'])]:
            with self.subTest(formula=formula):self.assertEqual(to_site.elements_of(formula),expected)
    def test_existing_coefficient_variables_and_components_are_preserved(self):
        for formula,expected in [('Cs1−xRbxPbBr3',['Cs','Rb','Pb','Br']),('Cd1-xZnxSe',['Cd','Zn','Se']),('Cu2−xS',['Cu','S']),('SiOx',['Si','O']),('Ge1−xSix',['Ge','Si']),('PbxBiySz',['Pb','Bi','S']),('Ge/GeOx',['Ge','O']),('Ge/SiO2',['Ge','Si','O']),('CdSe/ZnS',['Cd','Se','Zn','S'])]:
            with self.subTest(formula=formula):self.assertEqual(to_site.elements_of(formula),expected)
    def test_no_reported_fact_or_architecture_is_rewritten(self):
        formula='(Cs/FA)Pb(Br/I)3';pair={'product':formula,'structure':{'composition':{'value':formula,'page':1},'architecture':{'value':'unresolved','page':1}},'recipe':{}};before=copy.deepcopy(pair)
        r=to_site.Builder({'id':'fixture','doi':'10.1234/acronym','authors':'Fixture','year':'2026'}).record(pair,1)
        self.assertEqual(r['material']['elements'],['Cs','Pb','Br','I']);self.assertEqual(r['material']['formula'],formula);self.assertEqual(r['material']['architecture'],'unresolved');self.assertEqual(r['products'][0]['composition']['value'],formula);self.assertEqual(r['quality']['review_status'],'source_extracted');self.assertEqual(pair,before)
    def test_tokenizable_opaque_labels_are_not_claimed_to_be_resolved(self):
        # A plain symbol string can also be an acronym; this patch cannot decide source identity.
        self.assertEqual(to_site.elements_of('PVP'),['P','V'])
        self.assertEqual(to_site.elements_of('W2'),['W'])

    def test_undelimited_unknown_runs_are_conservatively_opaque(self):
        # No boundary licenses stripping an unknown acronym then guessing its residue.
        for label in ['FAPbI3', 'MAPbBr3', 'CdE']:
            with self.subTest(label=label):self.assertEqual(to_site.elements_of(label),[])

class NavigationCommandBoundary(unittest.TestCase):
    def run_case(self, labels):
        import contextlib, io, json, tempfile
        from pathlib import Path
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            repo=Path(tmp);atlas=repo/'recipe-atlas';records=atlas/'data/records';records.mkdir(parents=True)
            inventory=atlas/'data/inventory-evidence.json';inventory.write_text(json.dumps({'per_paper':[]}),encoding='utf-8')
            pairs=repo/'pairs';pairs.mkdir();doc={'id':'synthetic','doi':'10.1234/technical-navigation','authors':'Fixture','year':'2026','check':'two passes agree, quotes found','pairs':[{'product':label,'structure':{'composition':{'value':label,'page':1}},'recipe':{'steps':[{'action':'mix','description':'Synthetic operation','page':1}]}} for label in labels]}
            source=pairs/'synthetic.pairs.json';source.write_text(json.dumps(doc),encoding='utf-8');original=source.read_bytes();output=io.StringIO()
            with contextlib.redirect_stdout(output):to_site.cmd_records(SimpleNamespace(repo=repo,pairs=pairs,replace=True,include_optical=False))
            actual=[json.loads(p.read_bytes()) for p in sorted(records.glob('*.json'))]
            self.assertEqual(source.read_bytes(),original)
            return actual,json.loads(inventory.read_bytes()),output.getvalue()
    def test_actual_records_command_omits_unknown_then_writes_next_original_index(self):
        for unknown in ['PVA','MAPbBr3','FAPbI3']:
            with self.subTest(label=unknown):
                rows,inventory,log=self.run_case([unknown,'CdS'])
                self.assertEqual(len(rows),1);self.assertTrue(rows[0]['record_id'].endswith('-2'));self.assertEqual(rows[0]['material']['formula'],'CdS');self.assertEqual(rows[0]['quality']['review_status'],'source_extracted')
                self.assertEqual(inventory['per_paper'][0]['record_ids'],[rows[0]['record_id']]);self.assertIn('technical unresolved composition for navigation',log);self.assertNotIn('missing composition',log)
    def test_actual_records_command_all_unknown_leaves_no_canonical_or_paper(self):
        rows,inventory,log=self.run_case(['PVA','MAPbBr3'])
        self.assertEqual(rows,[]);self.assertEqual(inventory['per_paper'],[]);self.assertEqual(log.count('technical unresolved composition for navigation'),2)

if __name__=='__main__':unittest.main()
