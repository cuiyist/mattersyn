"""A single source-locator overlay; preserve the molecular and binding v1 freezes."""
from pathlib import Path
import copy,hashlib,json,subprocess
P=Path(__file__).resolve().parent
H=P.parent
M=H/'visuals/molecules'
O=P/'revision-2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def put(n,d):(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not (O/'package-manifest.json').exists(),'Preserve frozen revision.'
O.mkdir(exist_ok=True)
v1=read(P/'package-manifest.json')
assert sha(P/'package-manifest.json')=='77606a89b080b94bb0a0465feffec5fe5bd499bf53b649747fe58263811f392f'
for n,h in v1['files'].items():assert sha(P/n)==h,n
original=read(M/'registry-additions.json');effective=copy.deepcopy(original)
entry=next(x for x in effective['entries'] if x['id']=='identity-heo2003-in66-x')
idx=effective['entries'].index(entry)
old='Main PDF p. 4, printed p. 1123, Table 2 and footnote c'
new='Main PDF p. 5, printed p. 1124, Table 2 and footnote c'
assert entry['provenance']['sourceLocators'][1]==old
entry['provenance']['sourceLocators'][1]=new
ptr=f'/entries/{idx}/provenance/sourceLocators/1'
table=read(H/'main-tables.json')['tables'][1]
assert table['table_number']==2 and table['source']['pdf_page']==5 and table['source']['printed_page']==1124
put('registry-additions-effective.json',effective)
delta=[]
def diff(a,b,p=''):
 if type(a)!=type(b):delta.append({'pointer':p,'before':a,'after':b})
 elif isinstance(a,dict):
  assert set(a)==set(b)
  for k in a:diff(a[k],b[k],p+'/'+k)
 elif isinstance(a,list):
  assert len(a)==len(b)
  for i,(x,y) in enumerate(zip(a,b)):diff(x,y,p+'/'+str(i))
 elif a!=b:delta.append({'pointer':p,'before':a,'after':b})
diff(original,effective)
assert delta==[{'pointer':ptr,'before':old,'after':new}]
put('registry-metadata-delta.json',{'schema':'mattersyn-private-registry-metadata-overlay/1',
 'author':'/root/peng1998_reader_assets','status':'author_checked_pending_distinct_review',
 'source_id':'heo2003','original_freeze':{'file':'visuals/molecules/package-freeze.json','sha256':sha(M/'package-freeze.json')},
 'original_registry':{'file':'visuals/molecules/registry-additions.json','sha256':sha(M/'registry-additions.json')},
 'effective_registry':{'file':str((O/'registry-additions-effective.json').relative_to(H)).replace('\\','/'),'sha256':sha(O/'registry-additions-effective.json')},
 'json_patch':[{'op':'test','path':ptr,'value':old},{'op':'replace','path':ptr,'value':new}],
 'parsed_differences':delta,'source_evidence':{'file':'main-tables.json','sha256':sha(H/'main-tables.json'),'json_pointer':'/tables/1/source','value':table['source']},
 'unchanged_scope':'All other registry fields and all model/SVG bytes, source/canonical bytes and quantitative claims remain unchanged.',
 'binding_approved':False,'independent_review':'pending'})
copied=['bindings-proposal.json','stock-component-map.json','canonical-patch-proposal.json','unbound-context-dispositions.json','input-integrity.json']
for n in copied:(O/n).write_bytes((P/n).read_bytes())
maps=read(P/'material-slot-map.json');count=0
for b in maps['bindings']:
 if b['registry_id']=='identity-heo2003-in66-x':
  b['reference']['file']=str((O/'registry-additions-effective.json').relative_to(H)).replace('\\','/')
  b['reference']['sha256']=sha(O/'registry-additions-effective.json');count+=1
assert count==3
put('material-slot-map.json',maps)
runtime=(P/'runtime-contract-check.mjs').read_text(encoding='utf-8').replace(json.dumps(str(P)),json.dumps(str(O)),1)
(O/'runtime-contract-check.mjs').write_text(runtime,encoding='utf-8')
node=r'[local path redacted]'
r=subprocess.run([node,str(O/'runtime-contract-check.mjs')],capture_output=True,text=True,encoding='utf-8');assert r.returncode==0,r.stderr
rr=json.loads(r.stdout);rr['module']=read(P/'runtime-contract-result.json')['module'];put('runtime-contract-result.json',rr)
before=read(P/'input-integrity.json')['before']
assert all(sha(H/p)==h for p,h in before.items())
proof={'schema':'mattersyn-private-binding-revision-author-check/1','author':'/root/peng1998_reader_assets','status':'passed_author_checks_pending_independent_review',
 'initial_validation':{'path':str((P/'author-validation.json').relative_to(H)).replace('\\','/'),'sha256':sha(P/'author-validation.json'),'check_count':238},
 'checks':{'initial_freeze_files_unchanged':True,'single_registry_locator_leaf_changed':True,'source_table_page_verified':True,'three_in66_reference_paths_rebound':True,'all_other_binding_payloads_unchanged':True,'all_frozen_inputs_unchanged':True,'zero_canonical_patches':True,'all_approval_flags_remain_false':True},
 'runtime_contract_checks':rr['checks'],'independent_scientific_audit':'pending','browser_qa':'not_performed','published':False,'binding_approved':False}
put('author-validation.json',proof)
(O/'README.md').write_text((P/'README.md').read_text(encoding='utf-8')+'''

## Corrected metadata overlay

The original molecular freeze and initial binding package remain untouched. This revision corrects only the In66-X registry provenance locator for Table 2/footnote c from main PDF p. 4/printed p. 1123 to main PDF p. 5/printed p. 1124. The exact one-leaf test/replace patch and source table locator are in `registry-metadata-delta.json`. All eight new entries are preserved in `registry-additions-effective.json`; only that one locator differs from the original registry. Use this effective registry if independently approved, with the original frozen model/SVG assets and reused references. Three In66-X material-slot references now bind these exact effective registry bytes. No molecule or specimen coordinates changed.

The retained original package and this author-checked overlay require the distinct reviewer's hash-bound approval. This file is not that approval.
''',encoding='utf-8')
files={str(p.relative_to(O)).replace('\\','/'):sha(p) for p in sorted(O.rglob('*')) if p.is_file()}
put('package-manifest.json',{'schema':'mattersyn-private-canonical-binding-package/1','version':2,'source_id':'heo2003','author':'/root/peng1998_reader_assets',
 'status':'frozen_author_proposal_pending_independent_binding_audit','binding_approved':False,'published':False,'eligible_training':False,'counts':v1['counts'],
 'previous_binding_manifest':{'file':'canonical-binding-proposal/package-manifest.json','sha256':sha(P/'package-manifest.json')},
 'canonical_v1_manifest_sha256':v1['canonical_v1_manifest_sha256'],'molecule_freeze_sha256':v1['molecule_freeze_sha256'],
 'files':files,'builder':{'file':'canonical-binding-proposal/build_revision_2.py','sha256':sha(Path(__file__))},'record_hashes':v1['record_hashes'],
 'effective_registry_sha256':sha(O/'registry-additions-effective.json'),'author_validation_sha256':sha(O/'author-validation.json')})
print(json.dumps({'status':'author_frozen_v2','manifest_sha256':sha(O/'package-manifest.json'),'effective_registry_sha256':sha(O/'registry-additions-effective.json'),'metadata_delta_sha256':sha(O/'registry-metadata-delta.json'),'author_validation_sha256':sha(O/'author-validation.json'),'counts':v1['counts']},indent=2))
