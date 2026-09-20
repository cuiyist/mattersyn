"""Rebind existing Heo molecular slots to canonical v2; no source/asset changes."""
from pathlib import Path
import copy,hashlib,json,subprocess
P=Path(__file__).resolve().parent;H=P.parent;A=P/'revision-2';O=P/'revision-3';C=H/'canonical-proposal/v2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def put(n,d):(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ptr(d,p):
 for k in p.strip('/').split('/') if p else []:
  k=k.replace('~1','/').replace('~0','~');d=d[int(k)] if isinstance(d,list) else d[k]
 return d
checks=[]
def ck(ok,label):
 checks.append({'check':label,'passed':bool(ok)})
 if not ok:raise AssertionError(label)
def delta(a,b,p=''):
 if type(a)!=type(b):return [{'pointer':p,'before':a,'after':b}]
 if isinstance(a,dict):
  assert set(a)==set(b),(p,'keys')
  return [d for k in a for d in delta(a[k],b[k],p+'/'+k)]
 if isinstance(a,list):
  if len(a)!=len(b):return [{'pointer':p,'before':a,'after':b}]
  return [d for i,(x,y) in enumerate(zip(a,b)) for d in delta(x,y,p+'/'+str(i))]
 return [] if a==b else [{'pointer':p,'before':a,'after':b}]

assert not O.exists(),'Preserve frozen revision 3.'
O.mkdir()
mf=read(A/'package-manifest.json');cm=read(C/'canonical-record-manifest.json')
ck(sha(A/'package-manifest.json')=='3c2f44a6ba4dd07d4a3a3299daca23f7e2bfed9395c7973484c9989586b23685','Audited binding revision 2 unchanged')
ck(sha(C/'proposal-package-manifest.json')=='10640012af6a21458edd6a84c24af2dea24562f950495a662930d682185fb05a','Canonical v2 package unchanged')
for n,h in mf['files'].items():ck(sha(A/n)==h,'Binding revision 2 frozen file '+n)
for n,h in read(C/'proposal-package-manifest.json')['files'].items():ck(sha(C/n)==h,'Canonical v2 frozen file '+n)
old_integrity=read(A/'input-integrity.json')
for n,h in old_integrity['before'].items():ck(sha(H/n)==h,'Preserved original input '+n)
changed=[rid for rid in cm['record_hashes'] if cm['record_hashes'][rid]!=mf['record_hashes'][rid]]
X='heo-2003-xps-acquisition';ck(changed==[X],'Only XPS record hash changed')
oldrecord=read(H/'canonical-proposal/v1/canonical-drafts'/f'{X}.json');newrecord=read(C/'canonical-drafts'/f'{X}.json')
record_delta=delta(oldrecord,newrecord)
ck({d['pointer'] for d in record_delta}=={'/materials/1/evidence/0/locator','/operations/1/environment/evidence'},'Only audited evidence-array changes upstream')
maps=read(A/'material-slot-map.json');original_maps=copy.deepcopy(maps)
bind=read(A/'bindings-proposal.json');original_bind=copy.deepcopy(bind)
for b in maps['bindings']:
 rid=b['record_id']
 if rid==X:
  b['canonical']['file']=str((C/'canonical-drafts'/f'{X}.json').relative_to(H)).replace('\\','/')
  b['canonical']['sha256']=cm['record_hashes'][X]
  b['canonical']['payload']=copy.deepcopy(ptr(newrecord,b['canonical']['json_pointer']))
  b['canonical_sha256']=cm['record_hashes'][X]
  bind['bindingNotes'][X][b['material_id']]['canonical_sha256']=cm['record_hashes'][X]
 ck(b['canonical_sha256']==cm['record_hashes'][rid],'Binding has canonical v2 content hash '+b['binding_id'])
 cp=H/b['canonical']['file'];ck(sha(cp)==b['canonical_sha256'],'Exact retained canonical file '+b['binding_id'])
 ck(ptr(read(C/'canonical-drafts'/f'{rid}.json'),b['canonical']['json_pointer'])==b['canonical']['payload'],'Slot payload matches canonical v2 '+b['binding_id'])
 for src in b['source_links']:
  ck(sha(H/src['file'])==src['sha256'] and ptr(read(H/src['file']),src['json_pointer'])==src['payload'],'Source pointer unchanged '+b['binding_id']+' '+src['json_pointer'])
 ck(sha(H/b['reference']['file'])==b['reference']['sha256'],'Reference metadata still exact '+b['binding_id'])
 for asset in b['reference_assets']:ck(sha(H/asset['file'])==asset['sha256'],'Reference asset unchanged '+b['binding_id']+' '+asset['kind'])
map_delta=delta(original_maps,maps);binding_delta=delta(original_bind,bind)
allowed=set()
for i,b in enumerate(original_maps['bindings']):
 if b['record_id']==X:
  allowed|={f'/bindings/{i}/canonical/file',f'/bindings/{i}/canonical/sha256',f'/bindings/{i}/canonical_sha256'}
  if b['material_id']=='argon':allowed.add(f'/bindings/{i}/canonical/payload/evidence/0/locator')
ck({x['pointer'] for x in map_delta}==allowed,'Material-map delta only XPS paths/hashes and argon evidence')
ck({x['pointer'] for x in binding_delta}=={f'/bindingNotes/{X}/{m}/canonical_sha256' for m in ['final-crystal','argon','parent-reference','indium-reference']},'Viewer binding delta only four XPS canonical hashes')
ck(bind['recordBindings']==original_bind['recordBindings'],'All fourteen reference assignments unchanged')
put('material-slot-map.json',maps);put('bindings-proposal.json',bind)
for n in ['stock-component-map.json','unbound-context-dispositions.json','registry-additions-effective.json','registry-metadata-delta.json']:
 (O/n).write_bytes((A/n).read_bytes());ck(sha(O/n)==sha(A/n),'Byte-identical '+n)
stock=read(O/'stock-component-map.json')['stocks'][0]
ck(ptr(read(C/'canonical-drafts/heo-2003-in66-route.json'),stock['canonical']['json_pointer'])==stock['canonical']['payload'],'Unchanged stock matches canonical v2')
patch=read(A/'canonical-patch-proposal.json');patch['base_manifest_sha256']=sha(C/'proposal-package-manifest.json');patch['record_hashes']=cm['record_hashes'];ck(patch['patches']==[],'No canonical patches proposed')
put('canonical-patch-proposal.json',patch)
runtime=(A/'runtime-contract-check.mjs').read_text(encoding='utf-8').replace(json.dumps(str(A)),json.dumps(str(O)),1)
(O/'runtime-contract-check.mjs').write_text(runtime,encoding='utf-8')
node=r'[local path redacted]'
r=subprocess.run([node,str(O/'runtime-contract-check.mjs')],capture_output=True,text=True,encoding='utf-8');ck(r.returncode==0,'Current pure viewer contract '+r.stderr)
rr=json.loads(r.stdout);rr['module']=read(A/'runtime-contract-result.json')['module'];ck(sha(rr['module']['file'])==rr['module']['sha256'],'Actual viewer module unchanged');put('runtime-contract-result.json',rr)
put('binding-v2-to-v3-delta.json',{'schema':'mattersyn-private-binding-canonical-rebind-delta/1','source_id':'heo2003','author':'/root/peng1998_reader_assets','status':'author_checked_pending_distinct_delta_audit',
 'prior_binding_manifest_sha256':sha(A/'package-manifest.json'),'old_canonical_package_sha256':mf['canonical_v1_manifest_sha256'],'new_canonical_package_sha256':sha(C/'proposal-package-manifest.json'),
 'upstream_canonical_delta':record_delta,'material_slot_map_delta':map_delta,'viewer_bindings_delta':binding_delta,
 'changed_canonical_records':changed,'invariant_scope':['All fourteen slot/reference assignments','All source quantities and stock components','All specimen roles and scoped captions','Formal disconnected Tl+/acetate and absence of salt 3D','All models and SVGs','Corrected Table 2 registry locator','Approval/publication/training flags remain false'],
 'canonical_path_policy':'Only XPS canonical paths move to v2 because only that file changed. Other retained v1 paths are immutable and byte-identical to canonical v2; every slot was compared directly with v2.',
 'independent_audit':'pending'})
inputs={str(p.relative_to(H)).replace('\\','/'):sha(p) for p in [A/'package-manifest.json',C/'proposal-package-manifest.json',C/'canonical-record-manifest.json',H/'visuals/molecules/package-freeze.json',H/'visuals/molecules-independent-audit/independent-audit.json']}
for rid in cm['record_hashes']:inputs[str((C/'canonical-drafts'/f'{rid}.json').relative_to(H)).replace('\\','/')]=sha(C/'canonical-drafts'/f'{rid}.json')
put('input-integrity.json',{'schema':'mattersyn-private-rebind-input-integrity/1','status':'passed','new_inputs':inputs,'preserved_original_input_manifest':{'file':'canonical-binding-proposal/revision-2/input-integrity.json','sha256':sha(A/'input-integrity.json')},'all_original_inputs_rechecked_unchanged':True})
for n,h in mf['files'].items():ck(sha(A/n)==h,'Previous revision remained unchanged '+n)
put('author-validation.json',{'schema':'mattersyn-private-binding-author-validation/1','author':'/root/peng1998_reader_assets','source_id':'heo2003','status':'passed_author_checks_pending_distinct_delta_audit','check_count':len(checks),'checks':checks,'runtime_contract_checks':rr['checks'],'independent_scientific_audit':'pending','binding_approved':False,'published':False,'scope':'Bounded canonical evidence/hash rebind only. Earlier molecular audit does not automatically approve this revision. No browser or Site integration was performed.'})
(O/'README.md').write_text('''# Heo binding revision 3

This is the canonical-v2-bound version for independent delta review and later Site-owner integration. It preserves binding revision 2 and the original molecular freeze. Four XPS slot records now cite the new canonical record hash; their canonical paths point to v2. The argon slot snapshot includes the corrected main p. 5 identity locator. All other slot assignments, source quantities, stock components, captions, specimen roles, model/SVG hashes and pending approval flags remain unchanged. Nine unchanged canonical records have identical v1/v2 bytes, so their retained v1 dependency paths remain valid.

Use `bindings-proposal.json`, `material-slot-map.json` and `stock-component-map.json` from this revision. The `registry-additions-effective.json` bytes are exactly the independently reviewed revision-2 overlay that corrects the Table 2 locator; original molecular assets and reused entries remain in the frozen `visuals/molecules` package. `binding-v2-to-v3-delta.json` enumerates every changed binding field. No canonical mutation is proposed. The two unbound state/context depictions remain explicitly deferred.

All approval/publication/training flags remain false. Root must bind the distinct canonical-v2 audit and distinct binding-delta audit before any promotion. No Site, shared registry, ledger or original source was modified.
''',encoding='utf-8')
files={str(p.relative_to(O)).replace('\\','/'):sha(p) for p in sorted(O.rglob('*')) if p.is_file()}
put('package-manifest.json',{'schema':'mattersyn-private-canonical-binding-package/1','version':3,'source_id':'heo2003','author':'/root/peng1998_reader_assets','status':'frozen_author_rebind_pending_distinct_delta_audit','binding_approved':False,'published':False,'eligible_training':False,'counts':mf['counts'],
 'previous_binding_manifest':{'file':'canonical-binding-proposal/revision-2/package-manifest.json','sha256':sha(A/'package-manifest.json')},'canonical_v2_package_sha256':sha(C/'proposal-package-manifest.json'),'canonical_v2_manifest_sha256':sha(C/'canonical-record-manifest.json'),
 'molecule_freeze_sha256':mf['molecule_freeze_sha256'],'effective_registry_sha256':sha(O/'registry-additions-effective.json'),'record_hashes':cm['record_hashes'],'files':files,'builder':{'file':'canonical-binding-proposal/build_revision_3.py','sha256':sha(Path(__file__))},'author_validation_sha256':sha(O/'author-validation.json')})
print(json.dumps({'status':'frozen_author_rebind','manifest_sha256':sha(O/'package-manifest.json'),'bindings_sha256':sha(O/'bindings-proposal.json'),'map_sha256':sha(O/'material-slot-map.json'),'delta_sha256':sha(O/'binding-v2-to-v3-delta.json'),'checks':len(checks),'runtime_checks':rr['checks']},indent=2))
