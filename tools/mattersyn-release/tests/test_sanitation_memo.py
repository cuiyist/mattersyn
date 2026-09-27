import copy,json,os,sys,tempfile,unittest,threading,concurrent.futures
from pathlib import Path
from unittest.mock import patch
W=Path(__file__).resolve().parent
guard_path=os.environ.get('MATTERSYN_GUARD_MODULE')
if guard_path:sys.path.insert(0,str(Path(guard_path).parent))
elif (W/'candidate').is_dir():sys.path.insert(0,str(W/'candidate'))
else:sys.path.insert(0,str(W.parent))
import public_release_guard as g
SRC=Path(os.environ['MATTERSYN_SOURCE_ROOT']) if os.environ.get('MATTERSYN_SOURCE_ROOT') else Path(__file__).resolve().parents[3]
sys.path.insert(0,str(SRC/'tools/mattersyn-release/tests'))
from test_public_release_guard import make_config,allow_entry,blob_approval,make_allowlist,user_directed_figure,synthetic_cod_uri

def cod_fixture():
 path='assets/crystal-references/9016056.cif';raw=('data_COD\n#$URL: '+synthetic_cod_uri('9016056')+' $\n_cell_length_a 3.5\n').encode();ex={'repo':'mattersyn-site','path':path,'sha256':g.sha256(raw),'bytes':len(raw),'cod_id':'9016056','pattern_id':'cod_archive_annotation_v1','review_status':'approved','reviewer':'synthetic-fixture','source_refs':[{'citation_id':'COD-9016056','url':'https://www.crystallography.net/cod/9016056.html'}]};c=make_config();c['structure_path_exceptions']=[ex];c['path_rules'][0]['content_class']='structure_data';return path,raw,c,allow_entry(path,raw,content_class='structure_data',refs=ex['source_refs'])

class MemoTests(unittest.TestCase):
 def setUp(self):g.sanitation_memo_state(clear=True,enabled=True)
 def tearDown(self):g.sanitation_memo_state(clear=True,enabled=True)
 def test_cold_warm_exact_results_and_one_semantic_scan(self):
  raw=b'{"record":{"value":3,"unit":"nm"}}\n';c=make_config()
  with patch.object(g,'_sanitize_content_uncached',wraps=g._sanitize_content_uncached) as scan:
   cold=g._sanitize_content('data/a.json',raw,c,'mattersyn-site');warm=g._sanitize_content('data/a.json',raw,c,'mattersyn-site')
   self.assertEqual(cold,warm);self.assertEqual(scan.call_count,1);self.assertEqual(g.sanitation_memo_state()['hits'],1)
 def test_mixed_cold_warm_and_disabled_results_identical(self):
  fixtures=[('a.json',b'{"x":1}'),('b.json',b'{"evidence_quote":"private full source passage"}'),('c.json',b'{"x":1,"x":2}'),('d.json',b'{"nested":"{\\"excerpt\\":\\"source words\\"}"}'),('e.json',b'{"x":"\\ud800"}'),('a.pdf',b'%PDF-1.5 secret'),('a.md',b'normal prose'),('a.png',b'PNG fixture'),('secret.txt',(b'-----BEGIN ' + b'PRIVATE KEY-----'))]
  for path,raw in fixtures:
   c=make_config();g.sanitation_memo_state(enabled=False);expected=g._sanitize_content(path,raw,c,'mattersyn-site');g.sanitation_memo_state(enabled=True)
   self.assertEqual(expected,g._sanitize_content(path,raw,c,'mattersyn-site'));self.assertEqual(expected,g._sanitize_content(path,raw,c,'mattersyn-site'))
 def test_returned_stats_are_not_mutable_cache_state(self):
  raw=b'{"excerpt":"source"}';c=make_config();first=g._sanitize_content('x.json',raw,c,'mattersyn-site');first[2]['source_text_fields_removed']=999;second=g._sanitize_content('x.json',raw,c,'mattersyn-site');self.assertNotEqual(second[2]['source_text_fields_removed'],999)
 def test_same_size_byte_change_misses(self):
  c=make_config();g._sanitize_content('a.json',b'{"x":1}',c,'mattersyn-site');g._sanitize_content('a.json',b'{"x":2}',c,'mattersyn-site');self.assertEqual(g.sanitation_memo_state()['misses'],2)
 def test_path_repo_guard_and_pins_separate_keys(self):
  c=make_config();raw=b'{}';g._sanitize_content('a.json',raw,c,'mattersyn-site');g._sanitize_content('b.json',raw,c,'mattersyn-site');g._sanitize_content('a.json',raw,c,'mattersyn');c['policy_sha256']='1'*64;g._sanitize_content('a.json',raw,c,'mattersyn-site');c['asset_rights_registry_sha256']='2'*64;g._sanitize_content('a.json',raw,c,'mattersyn-site')
  with patch.object(g,'_SANITATION_GUARD_VERSION','different-reviewed-implementation'):g._sanitize_content('a.json',raw,c,'mattersyn-site')
  self.assertEqual(g.sanitation_memo_state()['misses'],6)
 def test_in_place_content_exception_mutation_misses_even_with_stale_pins(self):
  c=make_config();c['structure_path_exceptions']=[{'path':'a.cif','sha256':'x','review_status':'approved'}]
  with patch.object(g,'_sanitize_content_uncached',wraps=g._sanitize_content_uncached) as scan:
   g._sanitize_content('a.cif',b'data_test\n',c,'mattersyn-site');c['structure_path_exceptions'][0]['review_status']='rejected';g._sanitize_content('a.cif',b'data_test\n',c,'mattersyn-site');self.assertEqual(scan.call_count,2)
  self.assertEqual(g.sanitation_memo_state()['entries'],0)
 def test_raced_structure_exception_cannot_poison_denied_context(self):
  path,raw,c,entry=cod_fixture();approved=copy.deepcopy(c['structure_path_exceptions']);c['structure_path_exceptions']=[];entered=threading.Event();resume=threading.Event();original=g._sanitize_content_uncached
  def delayed(path,raw,config,repo):
   entered.set()
   if not resume.wait(5):raise RuntimeError('test synchronization timeout')
   return original(path,raw,config,repo)
  with patch.object(g,'_sanitize_content_uncached',side_effect=delayed):
   with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
    future=pool.submit(g.validate_allowlist_entry,path,raw,entry,c,'mattersyn-site');self.assertTrue(entered.wait(5));c['structure_path_exceptions']=approved;resume.set();future.result(timeout=5)
  c['structure_path_exceptions']=[];self.assertEqual(g.validate_allowlist_entry(path,raw,entry,c,'mattersyn-site'),(None,'local_path_in_structure_data'));self.assertEqual(g.sanitation_memo_state()['entries'],0)
 def test_exception_tuple_cannot_reuse_approved_list(self):
  path,raw,c,entry=cod_fixture();self.assertEqual(g.validate_allowlist_entry(path,raw,entry,c,'mattersyn-site'),(raw,None));c['structure_path_exceptions']=tuple(c['structure_path_exceptions']);self.assertEqual(g.validate_allowlist_entry(path,raw,entry,c,'mattersyn-site'),(None,'local_path_in_structure_data'));self.assertEqual(g.sanitation_memo_state()['entries'],0)
 def test_nested_source_refs_tuple_cannot_reuse_approved_list(self):
  path,raw,c,entry=cod_fixture();self.assertEqual(g.validate_allowlist_entry(path,raw,entry,c,'mattersyn-site'),(raw,None));c['structure_path_exceptions'][0]['source_refs']=tuple(c['structure_path_exceptions'][0]['source_refs']);self.assertEqual(g.validate_allowlist_entry(path,raw,entry,c,'mattersyn-site'),(None,'local_path_in_structure_data'));self.assertEqual(g.sanitation_memo_state()['entries'],0)
 def test_path_rule_revocation_is_checked_on_cache_hit(self):
  raw=b'{}';c=make_config(approvals=[blob_approval('a.json',raw)]);self.assertEqual(g.history_project('mattersyn-site','a.json',raw,c)['action'],'allow');c['path_rules'][0]['decision']='omit';self.assertEqual(g.history_project('mattersyn-site','a.json',raw,c)['action'],'omit')
 def test_exact_review_and_blob_approval_not_cached(self):
  raw=b'{}';c=make_config(approvals=[blob_approval('a.json',raw)]);entry=allow_entry('a.json',raw);self.assertIsNone(g.validate_allowlist_entry('a.json',raw,entry,c,'mattersyn-site')[1]);entry['sha256']='0'*64;self.assertEqual(g.validate_allowlist_entry('a.json',raw,entry,c,'mattersyn-site')[1],'source_file_hash_or_size_mismatch');g.history_project('mattersyn-site','a.json',raw,c);c['blob_approvals'][0]['decision']='omit';self.assertEqual(g.history_project('mattersyn-site','a.json',raw,c)['action'],'omit')
 def test_rights_revocation_remains_live(self):
  raw=b'fixture-image';path='assets/a.png';asset={'asset_hash':g.sha256(raw),'classification':'authored_diagram','source_bindings':[],'delivery_paths':[{'repo':'mattersyn-site','path':path,'bytes':len(raw)}],'rights':{'status':'not_source_derived','attribution':'Authored fixture'}};c=make_config(registry_assets=[asset]);c['path_rules'][0]['content_class']='site_asset';c['exact_blob_approval_classes']=[]
  self.assertEqual(g.history_project('mattersyn-site',path,raw,c)['action'],'allow');asset['rights']['status']='withheld';self.assertEqual(g.history_project('mattersyn-site',path,raw,c)['action'],'omit')
 def test_source_figure_provenance_and_permission_checked_after_cache_hit(self):
  raw=b'fixture-source-figure';path='assets/figures/example/figure-2.png';asset=user_directed_figure(path,raw);c=make_config(registry_assets=[asset]);c['path_rules'][0]['content_class']='site_asset';c['exact_blob_approval_classes']=[]
  self.assertEqual(g.history_project('mattersyn-site',path,raw,c)['action'],'allow');asset['source_bindings']=[];self.assertEqual(g.history_project('mattersyn-site',path,raw,c)['action'],'omit');asset['source_bindings']=[{'doi':'10.1000/example','url':'https://doi.org/10.1000/example'}];asset['rights']['copyright_permission_verified']=True;self.assertEqual(g.history_project('mattersyn-site',path,raw,c)['action'],'omit')
 def test_cache_limits_and_unchanged_bytes_not_retained(self):
  with patch.object(g,'_SANITATION_MEMO_MAX_ENTRIES',2):
   for i in range(3):g._sanitize_content(str(i)+'.json',b'{}',make_config(),'mattersyn-site')
   state=g.sanitation_memo_state();self.assertEqual(state['entries'],2);self.assertEqual(state['retained_output_bytes'],0)
 def fixture_stage(self,root,raw=b'{"x":1}'):
  c=make_config();file=root/'data.json';file.write_bytes(raw);(root/'index.html').write_bytes(b'<p>Fixture</p>');al=make_allowlist([allow_entry('index.html',b'<p>Fixture</p>'),allow_entry('data.json',raw)]);al['asset_rights_registry_sha256']=c['asset_rights_registry_sha256'];ap=root.parent/'allowlist.json';ap.write_text(json.dumps(al));return c,file,ap
 def test_stage_rereads_raced_same_size_file_even_with_mtime_restored(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)/'stage';root.mkdir();c,p,al=self.fixture_stage(root);self.assertEqual(g.validate_stage(root,al,c,'mattersyn-site')[1]['status'],'passed');st=p.stat();p.write_bytes(b'{"x":2}');os.utime(p,ns=(st.st_atime_ns,st.st_mtime_ns));result=g.validate_stage(root,al,c,'mattersyn-site')[1];self.assertEqual(result['status'],'failed');self.assertIn('staged_sha256_mismatch',[x['reason_code'] for x in result['failures']])
 def test_stage_membership_still_checked_after_warm_scan(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)/'stage';root.mkdir();c,p,al=self.fixture_stage(root);g.validate_stage(root,al,c,'mattersyn-site');(root/'extra.txt').write_text('unlisted');self.assertEqual(g.validate_stage(root,al,c,'mattersyn-site')[1]['status'],'failed');(root/'extra.txt').unlink();p.unlink();self.assertEqual(g.validate_stage(root,al,c,'mattersyn-site')[1]['status'],'failed')
 def test_warm_stage_symlink_gate_is_not_cached(self):
  for lexical_alias in (False,True):
   with self.subTest(lexical_alias=lexical_alias),tempfile.TemporaryDirectory() as td:
    top=Path(td)
    if lexical_alias:
     (top/'alias-parent').mkdir();top=top/'alias-parent'/'..'
    root=top/'stage';root.mkdir();c,p,al=self.fixture_stage(root)
    self.assertEqual(g.validate_stage(root,al,c,'mattersyn-site')[1]['status'],'passed')
    # The guard resolves its root; the mock must match the same file identity.
    # This also handles a Windows temporary directory with a short path name.
    p=p.resolve(strict=True);original=Path.is_symlink
    with patch.object(Path,'is_symlink',lambda path: True if path==p else original(path)):
     with self.assertRaisesRegex(g.BoundaryError,'symlink_not_allowed'):g.validate_stage(root,al,c,'mattersyn-site')
 def test_export_then_verify_same_byte_scan_reuse_and_exact_receipts(self):
  with tempfile.TemporaryDirectory() as td:
   top=Path(td);source=top/'source';source.mkdir();c,p,al=self.fixture_stage(source);g.sanitation_memo_state(enabled=False);cold=g.export_public_release(source,top/'cold',al,c,'mattersyn-site',top/'cm.json',top/'cr.json');g.sanitation_memo_state(clear=True,enabled=True);warm=g.export_public_release(source,top/'warm',al,c,'mattersyn-site',top/'wm.json',top/'wr.json');self.assertEqual(cold,warm);self.assertEqual((top/'cold/index.html').read_bytes(),(top/'warm/index.html').read_bytes());self.assertEqual(g.sanitation_memo_state()['misses'],1);self.assertGreaterEqual(g.sanitation_memo_state()['hits'],1)

if __name__=='__main__':unittest.main(verbosity=2)
