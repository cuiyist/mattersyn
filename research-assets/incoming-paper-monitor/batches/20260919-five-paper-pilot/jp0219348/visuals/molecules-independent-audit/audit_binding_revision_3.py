from pathlib import Path
import json,hashlib,datetime
A=Path(__file__).resolve().parent
H=A.parents[1]
R2=H/'canonical-binding-proposal/revision-2'
R3=H/'canonical-binding-proposal/revision-3'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[];bound={}
def check(label,condition):
 checks.append({'check':label,'passed':bool(condition)})
 if not condition: raise AssertionError(label)
def bind(p,expected=None):
 p=Path(p); observed=sha(p);bound[str(p)]={'path':str(p),'sha256':observed,'bytes':p.stat().st_size}
 if expected:check('hash '+str(p.relative_to(H)) if p.is_relative_to(H) else str(p),observed==expected)
 return observed
def diff(a,b,path=''):
 if type(a)!=type(b):return [{'pointer':path,'before':a,'after':b}]
 if isinstance(a,dict):
  out=[]
  for k in sorted(set(a)|set(b)):
   p=path+'/'+k.replace('~','~0').replace('/','~1')
   if k not in a or k not in b:out.append({'pointer':p,'before':a.get(k),'after':b.get(k)})
   else:out.extend(diff(a[k],b[k],p))
  return out
 if isinstance(a,list):
  if len(a)!=len(b):return [{'pointer':path,'before':a,'after':b}]
  return [item for i,(x,y) in enumerate(zip(a,b)) for item in diff(x,y,path+'/'+str(i))]
 return [] if a==b else [{'pointer':path,'before':a,'after':b}]
def ptr(o,p):
 for part in p.strip('/').split('/'):
  part=part.replace('~1','/').replace('~0','~')
  o=o[int(part)] if isinstance(o,list) else o[part]
 return o
old_audit=read(A/'independent-audit.json')
bind(A/'independent-audit.json','ff67e58d63021afbb3cbea9f68b4cc027944d8c6d9e04cdc64fdd8d990b0c86b')
bind(R2/'package-manifest.json','3c2f44a6ba4dd07d4a3a3299daca23f7e2bfed9395c7973484c9989586b23685')
bind(R3/'package-manifest.json','82ae8ebda8607566f6d0582e306c6c00309c2d565ada770a7ae95b8d51ea7a09')
for p,h in old_audit['bound_files'].items():bind(p,h)
for directory in [R2,R3]:
 m=read(directory/'package-manifest.json')
 for name,h in m['files'].items():bind(directory/name,h)
 bind(H/m['builder']['file'],m['builder']['sha256'])
manifest=read(R3/'package-manifest.json');d=read(R3/'binding-v2-to-v3-delta.json')
for p,h in read(R3/'input-integrity.json')['new_inputs'].items():bind(H/p,h)
oldslot=read(R2/'material-slot-map.json');newslot=read(R3/'material-slot-map.json')
oldview=read(R2/'bindings-proposal.json');newview=read(R3/'bindings-proposal.json')
actual_slot=diff(oldslot,newslot);actual_view=diff(oldview,newview)
check('exact declared slot-map delta',sorted(actual_slot,key=lambda v:v['pointer'])==sorted(d['material_slot_map_delta'],key=lambda v:v['pointer']))
check('exact declared viewer delta',sorted(actual_view,key=lambda v:v['pointer'])==sorted(d['viewer_bindings_delta'],key=lambda v:v['pointer']))
check('13 slot-map leaves: 4 paths +8 repeated hashes +1 locator',len(actual_slot)==13)
check('4 viewer changes all XPS canonical hashes',len(actual_view)==4 and all('heo-2003-xps-acquisition' in x['pointer'] and x['pointer'].endswith('/canonical_sha256') for x in actual_view))
check('all14 reference assignments unchanged',oldview['recordBindings']==newview['recordBindings'] and sum(map(len,newview['recordBindings'].values()))==14)
for name in ['stock-component-map.json','unbound-context-dispositions.json','registry-additions-effective.json','registry-metadata-delta.json']:
 check('unchanged substantive file '+name,(R2/name).read_bytes()==(R3/name).read_bytes())
patch_delta=diff(read(R2/'canonical-patch-proposal.json'),read(R3/'canonical-patch-proposal.json'))
check('patch proposal changed only package and XPS hashes',set(x['pointer'] for x in patch_delta)=={'/base_manifest_sha256','/record_hashes/heo-2003-xps-acquisition'})
check('zero canonical patches still proposed',read(R3/'canonical-patch-proposal.json')['patches']==[])
for flag in ['binding_approved','published','eligible_training']:
 for package in [manifest,newslot,newview]:check('false '+package['schema' if 'schema' in package else 'schemaVersion']+' '+flag,package[flag] is False)
records={};record_diffs={}
for record_id,h in manifest['record_hashes'].items():
 p=H/'canonical-proposal/v2/canonical-drafts'/f'{record_id}.json';bind(p,h)
 old=H/'canonical-proposal/v1/canonical-drafts'/f'{record_id}.json';bind(old)
 records[record_id]=read(p)
 delta=diff(read(old),read(p))
 if delta:record_diffs[record_id]=delta
check('only XPS canonical changed',list(record_diffs)==['heo-2003-xps-acquisition'])
check('only two declared canonical evidence fields changed',sorted(record_diffs['heo-2003-xps-acquisition'],key=lambda x:x['pointer'])==sorted(d['upstream_canonical_delta'],key=lambda x:x['pointer']))
check('material argon evidence now explicit p5',records['heo-2003-xps-acquisition']['materials'][1]['evidence'][0]['locator']=='Main PDF p. 5 (printed p. 1124), XPS Analyses: argon sputtering')
check('sputter environment retains settings p2 and identity p5',len(records['heo-2003-xps-acquisition']['operations'][1]['environment']['evidence'])==2)
for item in newslot['bindings']:
 record_id=item['binding_id'].split('::')[0]
 c=item['canonical'];p=H/c['file'];bind(p,c['sha256'])
 check('canonical payload '+item['binding_id'],ptr(read(p),c['json_pointer'])==c['payload'])
 check('v2 actual payload '+item['binding_id'],ptr(records[record_id],c['json_pointer'])==c['payload'])
 check('bound record hash '+item['binding_id'],item['canonical_sha256']==manifest['record_hashes'][record_id])
# Existing chemical audit retains real prior visual scope; this delta reopens only original p5.
bind(H/'main-05.png','a841f179be90bdca43974d3d61b938094ee747850424e05bd060ca54fd7a1830')
bind(Path(__file__))
report={'schema':'mattersyn-independent-binding-delta-audit/1','source_id':'heo2003','reviewer':'/root/norberg2004_extract','author':'/root/peng1998_reader_assets','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed_bounded_binding_revision_3_delta','prior_scientific_audit_sha256':sha(A/'independent-audit.json'),'binding_revision_3_manifest_sha256':sha(R3/'package-manifest.json'),'canonical_v2_package_sha256':manifest['canonical_v2_package_sha256'],'effective_registry_sha256':manifest['effective_registry_sha256'],'scope':'Independent exact-delta and pointer/hash verification, plus original main PDF5 visual recheck of argon identity. No new molecule-generation or full-source scientific audit claimed. Earlier molecule science/visual findings are inherited only through the exact unchanged bound files of the prior independent audit.','counts':{'machine_checks':len(checks),'material_slots':14,'stocks':1,'stock_components':2,'slot_map_changed_leaves':len(actual_slot),'viewer_changed_leaves':len(actual_view),'changed_canonical_records':1,'canonical_evidence_changes':2,'new_original_pages_reopened':1,'bound_files':len(bound)},'manual_findings':[{'id':'binding-delta-argon-source','status':'resolved_by_upstream_canonical_v2_and_binding_v3','evidence':'Original main PDF5 printed1124, lower left XPS paragraph explicitly names consecutive sputtering with argon. Material locator now points there; operation evidence also retains PDF2 instrument settings. All other slot/stock assignments, scopes, captions and assets match previously audited revision2.'}],'open_findings':[],'actual_slot_delta':actual_slot,'actual_viewer_delta':actual_view,'actual_canonical_delta':record_diffs,'checks':checks,'bound_files':list(bound.values()),'approval_limits':['Canonical v2 independent audit remains a separate gate; this report does not replace it.','Required effective-registry locator overlay remains mandatory.','No browser, apparatus, atomic-structure, integration, publication, exact-structure pair or training approval.','Author approval/publication/training flags remain false.']}
(A/'binding-revision-3-delta-audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
md=f'''# Heo binding revision 3 — independent bounded delta audit

Passed. Revision 3 preserves all fourteen material assignments, the stock and its two component links, the scoped captions, every model/SVG and the required corrected registry. Exact comparison found only thirteen slot-map leaves (four paths, eight repeated hashes and one argon locator) and four viewer hash leaves changed.

Only the XPS canonical record changed: the argon material evidence now points to main PDF5/printed1124; sputtering environment evidence retains PDF2 settings and adds PDF5 identity. I reopened the original PDF5 image and verified its explicit argon wording. All fourteen canonical payload snapshots resolve exactly against canonical v2.

{len(checks)} independent machine checks passed; {len(bound)} exact files are bound. The original molecule/binding audit and all its files remain unchanged. This is a delta audit, not a fresh full molecular/source review or replacement for canonical v2's separate audit. No browser, publication, training or atomic-coordinate approval is implied.

Revision 3 manifest: `{sha(R3/'package-manifest.json')}`.
Prior scientific audit: `{sha(A/'independent-audit.json')}`.
Required effective registry: `{manifest['effective_registry_sha256']}`.

No open finding in this bounded scope.
'''
(A/'binding-revision-3-delta-audit.md').write_text(md,encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':len(checks),'bound_files':len(bound),'json_sha256':sha(A/'binding-revision-3-delta-audit.json'),'md_sha256':sha(A/'binding-revision-3-delta-audit.md')},indent=2))
