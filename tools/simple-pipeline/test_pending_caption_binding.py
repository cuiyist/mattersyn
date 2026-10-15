"""Invented private fixtures only; no real Source, paper, caption or model input."""
import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('candidate_binder',HERE/'prepare_pending_batch_caption_plan.py')
binder=importlib.util.module_from_spec(spec);spec.loader.exec_module(binder)
def encoded(v):return (json.dumps(v,separators=(',',':'))+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()

class SplitBinderTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='mattersyn-caption-bind-')
  self.root=Path(self.temp.name).resolve();self.assertTrue(self.root.is_relative_to(Path(tempfile.gettempdir()).resolve()))
  self.source=self.root/'s';self.primary=self.source/'recipe-atlas/data/reader-presentation-reviewed.json'
  for src,dest in [(HERE/'local_caption_backfill.py','tools/simple-pipeline/local_caption_backfill.py'),(HERE.parents[1]/'recipe-atlas/scripts/reader_presentation_registry.py','recipe-atlas/scripts/reader_presentation_registry.py')]:
   p=self.source/dest;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(Path(src).read_bytes())
  self.figs=[]
  for n in (1,2):
   raw=('invented-crop-'+str(n)).encode();asset='assets/invented/f'+str(n)+'.png';p=self.source/'recipe-atlas/static'/asset;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
   self.figs.append({'id':'f'+str(n),'public_asset':asset,'public_asset_sha256':sha(raw),'source_locator':{'page':n+1,'figure':'Figure '+str(n)},'caption':'Invented locator only','permission_status':'unknown'})
  self.records={}
  for rid,sid,doi,status in [('r1','s','10.1234/test','source_extracted'),('r2','s','10.1234/test','source_extracted'),('audit','old','10.1234/old','source_reviewed'),('old','old2','10.1234/other','source_extracted')]:
   self.records[rid]={'record_id':rid,'quality':{'review_status':status},'lineage':{'source_group':sid},'sources':[{'id':sid,'doi':doi}],'invented_scientific_field':{'value':7,'unit':'nm'}}
   self.write('recipe-atlas/data/records/'+rid+'.json',self.records[rid])
  self.base={'records':{'r1':{'figures':[copy.deepcopy(self.figs[0])]},'audit':{'figures':[]},'old':{'figures':[]}},'materials':{},'figures_by_source':{'old':[]}}
  self.part={'records':{'r2':{'figures':[copy.deepcopy(self.figs[1])]}},'materials':{},'figures_by_source':{'s':copy.deepcopy(self.figs)}}
  self.write_split()
  self.pending={'schema':'public-caption-updates-1','papers':[{'doi':'10.1234/test','source_id':'pending','record_ids':[],'caption_status':'local_model_paraphrase_not_independently_reviewed','figures':[{'figure_key':'pending'+str(n),'figure':'Figure '+str(n),'page':n+1,'public_asset':'','public_asset_sha256':self.figs[n-1]['public_asset_sha256'],'public_caption':'Invented paraphrase '+str(n)} for n in (1,2)]}],'figure_count':2}
  self.updates=self.root/'pending.json';self.updates.write_bytes(encoded(self.pending))
 def tearDown(self):
  self.assertTrue(self.root.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()));self.temp.cleanup()
 def write(self,relative,value):
  p=self.source/relative;self.assertTrue(p.resolve().is_relative_to(self.root));p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(encoded(value))
 def write_split(self):
  raw=encoded(self.part);self.write('recipe-atlas/data/reader-presentation-reviewed.part2.json',self.part)
  self.base['_reader_registry_split']={'schema':'reader-presentation-two-part/1','part':'reader-presentation-reviewed.part2.json','sha256':sha(raw)}
  self.write('recipe-atlas/data/reader-presentation-reviewed.json',self.base)
 def inventory(self):return {p.relative_to(self.source).as_posix():sha(p.read_bytes()) for p in self.source.rglob('*') if p.is_file()}
 def bind(self,name='bound'):
  self.updates.write_bytes(encoded(self.pending))
  with contextlib.redirect_stdout(io.StringIO()):return binder.bind(self.source,self.updates,self.root/name)
 def test_binds_records_and_figures_from_both_parts_without_mutation(self):
  before=self.inventory();r=self.bind();self.assertEqual(r['figure_count'],2);self.assertEqual(r['holds'],[])
  self.assertEqual(r['papers'][0]['record_ids'],['r1','r2']);self.assertEqual({f['figure_key'] for f in r['papers'][0]['figures']},{'f1','f2'})
  self.assertEqual(self.inventory(),before)
 def test_installed_adapter_apply_only_captions_old_canonical_and_audited_unchanged(self):
  r=self.bind();adapter=binder.source_adapter(self.source);side=adapter.read(self.primary);expected=copy.deepcopy(side)
  for rid,n in [('r1',1),('r2',2)]:expected['records'][rid]['figures'][0]['public_caption']='Invented paraphrase '+str(n)
  for n,f in enumerate(expected['figures_by_source']['s'],1):f['public_caption']='Invented paraphrase '+str(n)
  before={p.name:p.read_bytes() for p in (self.source/'recipe-atlas/data/records').glob('*.json')}
  with contextlib.redirect_stdout(io.StringIO()):adapter.apply_updates(self.source,self.root/'bound/public-caption-updates-bound.json')
  self.assertEqual(adapter.read(self.primary),expected);self.assertEqual({p.name:p.read_bytes() for p in (self.source/'recipe-atlas/data/records').glob('*.json')},before)
  self.assertEqual(expected['records']['audit'],side['records']['audit']);self.assertEqual(expected['records']['old'],side['records']['old'])
 def test_three_origins_and_manual_flags_preserved(self):
  for origin in ['accepted','recovered','manual']:
   with self.subTest(origin=origin):
    p=copy.deepcopy(self.pending)
    if origin=='recovered':p['saved_response_recovery']=True
    if origin=='manual':
     p.update(manual_origin=True,manual_paraphrase=True);p['papers'][0].update(caption_status='manual_source_caption_paraphrase_not_independently_reviewed',manual_origin=True,manual_paraphrase=True)
     for f in p['papers'][0]['figures']:f.update(manual_origin=True,manual_paraphrase=True)
    previous=self.pending;self.pending=p;r=self.bind(origin);self.pending=previous
    self.assertEqual(r['papers'][0]['caption_status'],p['papers'][0]['caption_status'])
    if origin=='recovered':self.assertIs(r['saved_response_recovery'],True)
    if origin=='manual':
     for flag in ['manual_origin','manual_paraphrase']:
      self.assertIs(r[flag],True);self.assertIs(r['papers'][0][flag],True);self.assertTrue(all(f[flag] is True for f in r['papers'][0]['figures']))
 def test_missing_and_ambiguous_figure_matches_are_held(self):
  for name,change in [('missing',lambda:self.part['figures_by_source'].__setitem__('s',[])),('ambiguous',lambda:self.part['figures_by_source'].__setitem__('s',[self.figs[0],copy.deepcopy(self.figs[0]),self.figs[1],copy.deepcopy(self.figs[1])]))]:
   with self.subTest(name=name):change();self.write_split();r=self.bind(name);self.assertEqual(r['figure_count'],0);self.assertEqual(len(r['holds']),2)
 def test_page_label_hash_mismatch_never_bound(self):
  original=copy.deepcopy(self.pending)
  for key,value in [('page',99),('figure','Figure 99'),('public_asset_sha256','0'*64)]:
   self.pending=copy.deepcopy(original)
   for f in self.pending['papers'][0]['figures']:f[key]=value
   r=self.bind(key);self.assertEqual(r['figure_count'],0);self.assertEqual(len(r['holds']),2)
 def test_ambiguous_source_group_rejected(self):
  r=copy.deepcopy(self.records['r1']);r['record_id']='r3';r['lineage']['source_group']='different';r['sources'][0]['id']='different';self.write('recipe-atlas/data/records/r3.json',r)
  before=self.inventory();out=self.bind();self.assertEqual(out['figure_count'],0);self.assertEqual(len(out['holds']),1);self.assertEqual(self.inventory(),before)
 def test_wrong_doi_and_audited_only_never_bound(self):
  for rid in ['r1','r2']:
   r=copy.deepcopy(self.records[rid]);r['quality']['review_status']='source_reviewed';self.write('recipe-atlas/data/records/'+rid+'.json',r)
  r=self.bind('audited');self.assertEqual(r['figure_count'],0);self.assertEqual(len(r['holds']),1)
  self.pending['papers'][0]['doi']='10.1234/unrelated';r=self.bind('doi');self.assertEqual(r['figure_count'],0)
 def test_crop_bytes_changed_refused(self):
  (self.source/'recipe-atlas/static'/self.figs[0]['public_asset']).write_bytes(b'changed')
  with self.assertRaisesRegex(ValueError,'Current public crop changed'):self.bind()
 def test_registry_tamper_refused(self):
  (self.primary.with_name('reader-presentation-reviewed.part2.json')).write_bytes(b'{}')
  with self.assertRaisesRegex(ValueError,'checksum'):self.bind()
 def test_registry_module_and_sys_path_restored(self):
  sentinel=types.ModuleType('sentinel');before=sys.path[:]
  with patch.dict(sys.modules,{'reader_presentation_registry':sentinel}):
   adapter=binder.source_adapter(self.source);self.assertIs(sys.modules['reader_presentation_registry'],sentinel);self.assertEqual(sys.path,before);self.assertEqual(len(adapter.read(self.primary)['records']),4)
 def test_no_adjacent_adapter_fallback(self):
  (self.source/'tools/simple-pipeline/local_caption_backfill.py').unlink()
  with self.assertRaises(FileNotFoundError):self.bind()
 def test_unsupported_audit_status_and_nonboolean_origin_rejected(self):
  self.pending['papers'][0]['caption_status']='source_reviewed'
  with self.assertRaisesRegex(ValueError,'Unsupported'):self.bind('status')
  self.pending['papers'][0]['caption_status']='local_model_paraphrase_not_independently_reviewed';self.pending['manual_paraphrase']=1
  with self.assertRaisesRegex(ValueError,'boolean'):self.bind('flag')
 def test_explicit_source_cli_and_explicit_plan_batch(self):
  with patch.object(sys,'argv',['binder','bind','--source',str(self.source),'--updates',str(self.updates),'--out',str(self.root/'cli')]),contextlib.redirect_stdout(io.StringIO()):binder.main()
  self.assertEqual(json.loads((self.root/'cli/public-caption-updates-bound.json').read_bytes())['figure_count'],2)
  with patch.object(sys,'argv',['binder','plan','--source',str(self.source),'--out',str(self.root/'not-made')]),contextlib.redirect_stderr(io.StringIO()):
   with self.assertRaises(SystemExit) as error:binder.main()
   self.assertEqual(error.exception.code,2)
  self.assertFalse((self.root/'not-made').exists())

 def test_registry_presence_and_value_restored_on_success_and_failure(self):
  key='reader_presentation_registry'
  for prior in ('absent','none','module'):
   for failing in (False,True):
    with self.subTest(prior=prior,failing=failing),patch.dict(sys.modules):
     sentinel=None if prior=='none' else types.ModuleType('prior-registry')
     if prior=='absent':sys.modules.pop(key,None)
     else:sys.modules[key]=sentinel
     before_path=sys.path[:];original_spec=binder.importlib.util.spec_from_file_location
     def make_spec(name,path):
      if failing and name=='caption_adapter':raise RuntimeError('invented adapter import failure')
      return original_spec(name,path)
     with patch.object(binder.importlib.util,'spec_from_file_location',side_effect=make_spec):
      if failing:
       with self.assertRaisesRegex(RuntimeError,'invented adapter import failure'):binder.source_adapter(self.source)
      else:binder.source_adapter(self.source)
     self.assertEqual(sys.path,before_path)
     self.assertEqual(key in sys.modules,prior!='absent','registry presence was not restored')
     if prior!='absent':self.assertIs(sys.modules[key],sentinel)

if __name__=='__main__':unittest.main(verbosity=2)
