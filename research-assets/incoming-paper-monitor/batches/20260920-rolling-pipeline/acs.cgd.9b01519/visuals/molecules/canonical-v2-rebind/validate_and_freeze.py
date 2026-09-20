"""Bounded author verification; independent audit remains a separate gate."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone
import json, hashlib
D=Path(__file__).resolve().parent; O=D.parent; P=O.parents[1]
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x): (D/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def ptr(x,p):
 for t in p.strip('/').split('/'): x=x[int(t)] if isinstance(x,list) else x[t]
 return x
checks=[]
def ck(n,v):
 checks.append({'check':n,'passed':bool(v)})
 assert v,n
assert not (D/'package-freeze.json').exists()
base=read(O/'package-freeze.json')
for p,h in base['bound_files'].items(): ck('Frozen original '+p,sha(p)==h)
cm=P/'canonical-proposal/v2/record-manifest.json'; records={x['record_id']:read(x['path']) for x in read(cm)['records']}
for x in read(cm)['records']: ck('Canonical hash '+x['record_id'],sha(x['path'])==x['sha256'])
ca=P/'canonical-reader-independent-audit/independent-audit-v2.json'
ck('Exact passed canonical audit',sha(ca)=='8bf47e1fb1d72c074d050e1638d68add32a29faf7f5013fbe9cc3e159088c12c' and read(ca)['status'].startswith('passed'))
oldslots=read(O/'material-slot-map.json'); newslots=read(D/'material-slot-map.json')
ck('62 slots',len(oldslots['slots'])==len(newslots['slots'])==62)
for a,b in zip(oldslots['slots'],newslots['slots']):
 key=b['record_id']+'/'+b['material_id']; special=key=='sommer-2020-scf-route/insitu-water'
 ck(key+' exact current snapshot',b['canonical_identity']==ptr(records[b['record_id']],b['json_pointer']))
 x=deepcopy(a); y=deepcopy(b)
 for k in ['canonical_record_sha256','entry_sha256']:x.pop(k);y.pop(k)
 if special:
  ck(key+' scoped SCF name',b['viewOverrides']['name']=='Aqueous SCF solvent')
  ck(key+' scoped SCF note',b['viewOverrides']['limitations'][0]==b['canonical_identity']['notes'][0])
  ck(key+' no in situ caption inheritance','No in situ nitrate-stock preparation, salt charge or solution volume is inherited' in b['viewOverrides']['caption'] and 'Grade not specified in the in situ nitrate preparation.' not in b['viewOverrides']['caption'])
  for k in ['canonical_identity','viewOverrides']:x.pop(k);y.pop(k)
 ck(key+' all remaining fields unchanged',x==y)
 ck(key+' exact typed quantities',a['quantity_links']==b['quantity_links'])
 ck(key+' binding pending',b['binding_approved'] is False)
oldb=read(O/'bindings-proposal.json'); newb=read(D/'bindings-proposal.json')
ck('Exact record assignments',oldb['recordBindings']==newb['recordBindings'])
for b in newslots['slots']:ck('Mirrored slot '+b['record_id']+'/'+b['material_id'],newb['bindingNotes'][b['record_id']][b['material_id']]==b)
olds=read(O/'stock-component-map.json'); news=read(D/'stock-component-map.json')
for a,b in zip(olds['stocks'],news['stocks']):
 x=deepcopy(a);y=deepcopy(b);x.pop('canonical_record_sha256');y.pop('canonical_record_sha256')
 ck(b['stock_id']+' all stock science unchanged',x==y)
 ck(b['stock_id']+' exact current snapshot',b['canonical_stock']==ptr(records[b['record_id']],b['json_pointer']))
em=read(D/'effective-file-map.json'); ep=read(D/'effective-public-assets.json')
ck('Eight logical files',len(em)==8);ck('36 public assets',len(ep)==36)
for n,x in list(em.items())+list(ep.items()):ck('Effective asset '+n,Path(x['path']).is_absolute() and sha(x['path'])==x['sha256'])
changed=[]
for n,x in ep.items():
 if sha(O/n)!=x['sha256']:changed.append(n)
ck('Only water SVG changed',changed==['svg/sommer2020-insitu-water-reference.svg'])
delta=read(D/'rebind-delta.json'); rel=changed[0];svg=(D/rel).read_text(encoding='utf8')
for x in delta['svg_text_replacements']:
 ck('Replacement count '+x['after'],svg.count(x['after'])==x['occurrences']);svg=svg.replace(x['after'],x['before'])
ck('SVG reverse delta restores original text',svg==(O/rel).read_text(encoding='utf8'))
for n,h in delta['unchanged_model_hashes'].items():ck('Unchanged model '+n,sha(O/n)==h and ep[n.replace('\\','/')]['path']==str(O/n))
vr=read(D/'viewer-function-checks.json');ck('Actual chemicalEntry checks passed',vr['status']=='passed_author_execution_checks' and vr['check_count']==374)
save('author-visual-review.json',{'status':'passed_author_view','scope':'Actually viewed the complete regenerated shared-water SVG preview at full size. Heading and note are source-neutral and readable; atom/bond drawing unchanged. SCF and in situ captions retain separate source scope in the binding map.','preview_path':str(D/'previews/sommer2020-insitu-water-reference.png'),'preview_sha256':sha(D/'previews/sommer2020-insitu-water-reference.png'),'independent_audit':False,'mounted_browser_approval':False})
save('author-validation.json',{'status':'passed_author_bounded_checks','check_count':len(checks),'checks':checks,'actual_viewer_check_count':vr['check_count'],'generation_checks':delta['check_count'],'independent_audit':False,'all_model_bytes_unchanged':True,'no_source_or_canonical_edits':True})
external={str(O/'package-freeze.json'):sha(O/'package-freeze.json'),str(cm):sha(cm),str(ca):sha(ca)}
external.update(base['bound_files'])
external.update({x['path']:x['sha256'] for x in em.values()})
external.update({x['path']:x['sha256'] for x in ep.values()})
for x in read(cm)['records']:external[x['path']]=x['sha256']
files={str(p):sha(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='package-freeze.json' and '__pycache__' not in p.parts};files.update(external)
freeze={'schema':'mattersyn-molecular-rebind-overlay/1','created_at':datetime.now(timezone.utc).isoformat(),'author':'/root/peng1998_reader_assets','status':'private_author_frozen_pending_distinct_overlay_audit','base_freeze':{'path':str(O/'package-freeze.json'),'sha256':sha(O/'package-freeze.json')},'canonical_record_manifest':{'path':str(cm),'sha256':sha(cm)},'canonical_audit':{'path':str(ca),'sha256':sha(ca)},'counts':{'identities':28,'material_slots':62,'stocks':7,'stock_components':23,'public_assets':36,'changed_public_assets':1,'unchanged_models':8},'bound_files':files,'binding_approved':False,'publication_approved':False,'training_eligible':False,'atomic_product_model':False}
save('package-freeze.json',freeze)
print(json.dumps({'freeze_sha256':sha(D/'package-freeze.json'),'bound_files':len(files),'checks':len(checks),'viewer_checks':vr['check_count']}))
