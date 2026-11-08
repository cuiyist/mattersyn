"""Fixed field-standard names: pure identity/reference tests; no network/RDKit."""
import copy,json,pathlib,sys,unittest
S=pathlib.Path(__file__).resolve().parents[1]/'scripts';sys.path.insert(0,str(S))
import chemical_reference_identity as identity
PROOF=json.loads((S/'chemical_standard_abbreviation_pins.json').read_text(encoding='utf-8'))
class StandardAbbreviations(unittest.TestCase):
 def fixture(self,eid,p):
  e={'id':eid,'name':p['reported_name'],'depictionKind':'formula','formula':''};named=p['named_identity_entry'];entries={named['id']:copy.deepcopy(named)};entries.setdefault(eid,e);return e,copy.deepcopy(p['reference']),entries
 def test_all17_standard_names_reuse_exact_qualified_references(self):
  self.assertEqual(len(PROOF['entries']),17)
  for eid,p in PROOF['entries'].items():
   with self.subTest(eid=eid):
    e,ref,entries=self.fixture(eid,p);before=copy.deepcopy((e,ref,entries));self.assertIsNone(identity.context_reason(e));self.assertEqual(identity.standard_abbreviation_reference_errors(e,ref,p,entries),[]);self.assertEqual((e,ref,entries),before)
 def test_wrong_bare_database_hits_cannot_override_named_APTMS_or_CTAC(self):
  for eid,cid in [('name-card-aptms',87067127),('name-card-ctac',20011)]:
   p=PROOF['entries'][eid];e,ref,entries=self.fixture(eid,p);e['pubchemCid']=cid;self.assertTrue(identity.standard_abbreviation_reference_errors(e,ref,p,entries))
 def test_identity_formula_model_hash_and_reference_scope_are_exact(self):
  for eid,p in PROOF['entries'].items():
   e,ref,entries=self.fixture(eid,p)
   for field,value in [('referencePubchemCid',999),('referenceFormula','H2O'),('referenceName','Another compound'),('trainingEligible',True),('caption','Measured sample coordinates')]:
    with self.subTest(eid=eid,field=field):self.assertTrue(identity.standard_abbreviation_reference_errors(e,ref|{field:value},p,entries))
   changed=copy.deepcopy(p);changed['reference']['referencePubchemCid']=999;self.assertTrue(identity.standard_abbreviation_reference_errors(e,changed['reference'],changed,entries))
   self.assertTrue(identity.standard_abbreviation_reference_errors(e|{'formula':'H2O'},ref,p,entries))
 def test_mixture_specimen_stock_and_isomers_still_hold(self):
  for eid,p in PROOF['entries'].items():
   e,ref,entries=self.fixture(eid,p)
   for change in [{'depictionKind':'mixture'},{'depictionKind':'specimen'},{'depictionKind':'polymer'},{'depictionKind':'support'},{'name':e['name']+' stock'},{'name':e['name']+' mixed isomers'}]:
    with self.subTest(eid=eid,change=change):self.assertIsNotNone(identity.context_reason(e|change));self.assertTrue(identity.standard_abbreviation_reference_errors(e|change,ref,p,entries))
 def test_25_unfixed_or_distribution_codes_remain_flat(self):
  for name in HELD_CODES:
   with self.subTest(name=name):self.assertEqual(identity.context_reason({'id':'held','name':name,'depictionKind':'formula'}),'unresolved_abbreviation')
HELD_CODES=['TDPA', 'OAM', 'DDT', 'MEH-PPV', 'NP-5', 'TOPS', 'FITC', 'MPTS', 'TGA', 'TOA', 'ACHN', 'ANO', 'APBA', 'DDAB', 'DOTAP', 'MPS', 'OD', 'OPA', 'OPV', 'P3HT', 'PBG', 'PDDA', 'PFBT', 'SMCC', 'USY']
if __name__=='__main__':unittest.main()
