"""Finite source-bound temperature-glyph regressions; no papers/pairs/model/site writes."""
import ast,copy,json,os,re,sys,unicodedata,unittest
from pathlib import Path
P=Path(os.environ.get('MATTERSYN_TO_SITE_TEST_MODULE',Path(__file__).with_name('to_site.py')))
def api(path):
 tree=ast.parse(Path(path).read_bytes());body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef,ast.Assign,ast.AnnAssign))];ns={'re':re,'json':json,'sys':sys,'unicodedata':unicodedata,'Path':Path};exec(compile(ast.Module(body=body,type_ignores=[]),str(path),'exec'),ns);return ns
API=api(P)
CASES=(('10.1021/cm900710q',180,'˚C',2),('10.1038/nature03832',310,'8C',4),('10.1038/nature03832',260,'8C',4),('10.1002/pssa.200925636',600,'8C',2))
def record(k):
 doi,value,unit,page=k;doc={'id':'fixture','doi':doi,'year':2026,'authors':'Example Author','title':'Fixture'};pair={'product':'ZnSe','structure':{'composition':{'value':'ZnSe','page':page}},'recipe':{'steps':[{'action':'heat','description':'Synthetic heat step','temperature':value,'temperature_unit':unit,'page':page}]}};return doc,pair
class TemperatureContextGlyphs(unittest.TestCase):
 def test_exact_tokens_in_separate_numeric_temperature(self):
  for value in (180,310,260,600,25.5):
   for unit in ('8C','˚C',' 8C '):
    with self.subTest(value=value,unit=unit):self.assertEqual(API['temperature_unit_name'](unit,value),'°C')
 def test_nonnumeric_bool_and_nontokens_preserved(self):
  for value in (None,True,'310'):
   for unit in ('8C','˚C'):self.assertEqual(API['temperature_unit_name'](unit,value),unit)
  for unit in ('8 C','C','8C/s','8C chemical','degC','K','°C','W',None):self.assertEqual(API['temperature_unit_name'](unit,310),unit)
 def test_generic_unit_name_and_other_dimensions_unchanged(self):
  self.assertEqual(API['unit_name']('8C'),'8C');self.assertEqual(API['unit_name']('˚C'),'˚C')
  b=API['Builder']({'id':'fixture','authors':'Example Author','doi':'10.0000/fixture','year':2026})
  self.assertEqual(b.quantity(8,'8C',2)['unit'],'8C')
 def test_numeric_operation_temperature_normalizes_regardless_of_doi(self):
  for k in (*CASES,('10.0000/new',95,'8C',3)):
   doc,pair=record(k);before=copy.deepcopy(pair);r=API['Builder'](doc).record(pair,1);self.assertEqual(r['operations'][0]['parameters']['temperature']['unit'],'degC');self.assertEqual(pair,before);self.assertEqual(r['operations'][0]['description'],'Synthetic heat step');self.assertEqual(r['quality']['review_status'],'source_extracted')
 def test_only_reaction_temperature_note_uses_temperature_context(self):
  doc,pair=record(('10.0000/new',95,'8C',3));pair['recipe']['reaction_temperature']={'value':95,'unit':'8C','page':3};pair['recipe']['reaction_time']={'value':8,'unit':'8C','page':3};r=API['Builder'](doc).record(pair,1)
  self.assertEqual(r['products'][0]['notes'],['Reaction temperature: 95 degC (Main PDF p.3).','Reaction time: 8 8C (Main PDF p.3).'])
 def test_narrative_non_temperature_literal_is_not_rewritten(self):
  doc,pair=record(('10.0000/new',95,'8C',3));pair['recipe']['steps'][0]['description']='Sample 8C heated';r=API['Builder'](doc).record(pair,1);self.assertEqual(r['operations'][0]['label'],'Sample 8C heated');self.assertEqual(r['operations'][0]['description'],'Sample 8C heated')
if __name__=='__main__':unittest.main()
