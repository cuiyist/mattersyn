"""Synthetic caption adapter regression tests; no model requests or real sources."""
import copy, importlib.util, json, subprocess, sys, tempfile, unittest
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('caption_adapter',HERE/'local_caption_backfill.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def figure(key='paper-figure-1',page=2):return {'figure_key':key,'figure':'Figure 1','page':page,'public_asset':'assets/paper-reviews/paper/figure-1.png','public_asset_sha256':m.sha(b'crop'),'private_caption':'Raw private figure caption describing the original synthesized particle image.'}
def reply(figures,caption='Microscopy depicts the particles and their arrangement in this source figure.'):
 return json.dumps({'captions':[{'figure_key':f['figure_key'],'page':f['page'],'public_caption':caption} for f in figures]})
class AdapterTests(unittest.TestCase):
 def test_portable_source_default_comes_from_repository_layout(self):
  self.assertEqual(m.SOURCE, (HERE/'local_caption_backfill.py').resolve().parents[2])
 def test_plan_requires_explicit_saved_input_run_directory(self):
  result=subprocess.run([sys.executable,'-B',str(HERE/'local_caption_backfill.py'),'plan','--out',str(HERE/'not-written')],capture_output=True,text=True)
  self.assertEqual(result.returncode,2);self.assertIn('plan requires explicit --run',result.stderr);self.assertFalse((HERE/'not-written').exists())
 def test_remote_http_refused(self):
  with self.assertRaises(ValueError):m.endpoint('http://example.org/v1')
 def test_credentials_refused(self):
  with self.assertRaises(ValueError):m.endpoint('http://secret@127.0.0.1:8080/v1')
 def test_local_url_retained(self):self.assertEqual(m.endpoint('http://127.0.0.1:8080/v1'),'http://127.0.0.1:8080/v1/chat/completions')
 def test_exact_figure_and_page_required(self):
  f=figure()
  with self.assertRaises(ValueError):m.validate_reply(reply([figure(page=3)]),[f])
  with self.assertRaises(ValueError):m.validate_reply(reply([figure(key='other')]),[f])
 def test_duplicate_keys_refused(self):
  with self.assertRaises(ValueError):m.validate_reply(reply([figure(),figure()]),[figure()])
 def test_full_caption_copy_refused(self):
  f=figure()
  with self.assertRaises(ValueError):m.validate_reply(reply([f],f['private_caption']),[f])
 def test_long_passage_copy_refused(self):
  f=figure();f['private_caption']=' '.join('word'+str(i) for i in range(30))
  with self.assertRaises(ValueError):m.validate_reply(reply([f],'New prefix '+ ' '.join('word'+str(i) for i in range(15))),[f])
 def test_empty_caption_left_out(self):self.assertEqual(m.validate_reply(reply([figure()],''),[figure()]),[])
 def test_public_payload_has_no_raw_caption_or_local_paths(self):
  f=figure();f['saved_metadata_path']='private/work/file';safe=m.validate_reply(reply([f]),[f]);self.assertNotIn('private_caption',safe[0]);self.assertNotIn('saved_metadata_path',safe[0]);self.assertNotIn(f['private_caption'],json.dumps(safe))
 def test_request_is_separate_prompt_and_schema_constrained(self):
  b=m.request_body([figure()],'qwen3-32b');self.assertEqual(b['response_format']['type'],'json_schema');self.assertEqual(b['temperature'],0);self.assertEqual(b['reasoning_effort'],'none');self.assertEqual(b['max_tokens'],4096);self.assertIn('/no_think',b['messages'][1]['content'])
 def test_packets_stay_bounded_and_oversized_not_truncated(self):
  figs=[figure(key='paper-figure-'+str(i)) for i in range(10)]
  for f in figs:f['private_caption']='x'*7000
  chunks,held=m.packets(figs,'qwen3-32b');self.assertGreater(len(chunks),1);self.assertFalse(held)
  for c in chunks:self.assertLessEqual(len(json.dumps(m.request_body(c,'qwen3-32b'),ensure_ascii=False).encode('utf8')),m.MAX_BODY_BYTES)
  large=figure();large['private_caption']='x'*30000;self.assertEqual(m.packets([large],'qwen3-32b'),([],[large['figure_key']]))
 def test_response_rows_bounded(self):
  chunks,held=m.packets([figure(key='f'+str(i)) for i in range(43)],'qwen3-32b');self.assertEqual([len(c) for c in chunks],[20,20,3]);self.assertFalse(held)
 def test_failures_continue_serially_and_partial_updates_safe(self):
  with tempfile.TemporaryDirectory(dir=HERE) as td:
   out=Path(td);papers=[]
   for i in range(3):
    f=out/f'in-{i}.json';m.write(f,{'source_id':f'p{i}','doi':f'10.1234/p{i}','record_ids':[f'r{i}'],'figures':[figure(key=f'p{i}-figure-1')]});papers.append({'private_input':str(f),'private_input_sha256':m.sha(f.read_bytes())})
   p=out/'plan.json';m.write(p,{'papers':papers});state={'active':0,'peak':0,'calls':0}
   def mock(url,body):
    state['active']+=1;state['peak']=max(state['peak'],state['active']);state['calls']+=1
    try:
     if state['calls']==1:raise RuntimeError('private source not disclosed')
     figs=json.loads(body['messages'][1]['content'].split('\n/no_think')[0])['figures']
     return {'choices':[{'finish_reason':'stop','message':{'content':reply(figs)}}]}
    finally:state['active']-=1
   before={x['private_input']:m.sha(Path(x['private_input']).read_bytes()) for x in papers};r=m.generate(p,out,'http://127.0.0.1:8080/v1','qwen3-32b',call=mock)
   self.assertEqual(state['peak'],1);self.assertEqual(r['figure_count'],2);self.assertEqual(len(r['failures']),1);self.assertEqual(r['failures'][0]['error_type'],'RuntimeError');self.assertNotIn('private source not disclosed',json.dumps(r));self.assertEqual(before,{x['private_input']:m.sha(Path(x['private_input']).read_bytes()) for x in papers});self.assertTrue((out/'public-caption-updates.json').exists())
 def test_apply_only_optional_reader_field_and_never_audited(self):
  with tempfile.TemporaryDirectory(dir=HERE) as td:
   s=Path(td);asset=s/'recipe-atlas/static'/figure()['public_asset'];asset.parent.mkdir(parents=True);asset.write_bytes(b'crop')
   rec={'quality':{'review_status':'source_extracted'},'lineage':{'source_group':'paper'},'sources':[{'doi':'10.1234/p'}]};rp=s/'recipe-atlas/data/records/r.json';m.write(rp,rec)
   fig={'id':figure()['figure_key'],'public_asset':figure()['public_asset'],'public_asset_sha256':figure()['public_asset_sha256'],'source_locator':{'page':2,'figure':'Figure 1'},'caption':'Source citation stays','copyright_permission_verified':False,'sample_scope':'No sample match'}
   side={'records':{'r':{'figures':[copy.deepcopy(fig)]}},'figures_by_source':{'paper':[copy.deepcopy(fig)]}};sp=s/'recipe-atlas/data/reader-presentation-reviewed.json';m.write(sp,side);before_record=rp.read_bytes()
   up=s/'updates.json';m.write(up,{'papers':[{'source_id':'paper','doi':'10.1234/p','record_ids':['r'],'figures':m.validate_reply(reply([figure()]),[figure()])}]});m.apply_updates(s,up);after=m.read(sp)
   for view in [after['records']['r']['figures'][0],after['figures_by_source']['paper'][0]]:
    self.assertTrue(view.pop('public_caption'));self.assertEqual(view,fig)
   self.assertEqual(rp.read_bytes(),before_record);rec['quality']['review_status']='source_reviewed';m.write(rp,rec)
   with self.assertRaises(ValueError):m.apply_updates(s,up)
if __name__=='__main__':unittest.main(verbosity=2)
