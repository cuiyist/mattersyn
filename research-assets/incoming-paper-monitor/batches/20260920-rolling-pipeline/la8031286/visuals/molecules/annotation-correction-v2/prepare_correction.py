"""Narrow preserved correction for three nitrate N annotations; never edits base files."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import json,hashlib
O=Path(__file__).resolve().parent;A=O.parent;P=A.parents[1]
assert not (O/'package-freeze.json').exists(),'Frozen correction must not be overwritten'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(rel,v):
 p=O/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf-8');return p
def diffs(a,b,p=''):
 if type(a)!=type(b):return [{'pointer':p,'before':a,'after':b}]
 if isinstance(a,dict):
  assert a.keys()==b.keys(),'No new/deleted fields '+p
  return [d for k in a for d in diffs(a[k],b[k],p+'/'+k.replace('~','~0').replace('/','~1'))]
 if isinstance(a,list):
  if len(a)!=len(b):return [{'pointer':p,'before':a,'after':b}]
  return [d for i,(x,y) in enumerate(zip(a,b)) for d in diffs(x,y,p+'/'+str(i))]
 return [] if a==b else [{'pointer':p,'before':a,'after':b}]
count=0
def ck(b,m):
 global count
 assert b,m
 count+=1
base=read(A/'package-freeze.json');ck(sha(A/'package-freeze.json')=='8b5724b9a7008dfb74cdc8f5cea7fdfcd47939a26b89d85916aebc77fed7c202','Original freeze')
for p,h in base['bound_files'].items():ck(sha(p)==h,'Original input unchanged '+p)
modelrel='models/pati2009-cerium-nitrate-2d.json';oldmodel=read(A/modelrel);model=deepcopy(oldmodel)
removed=[g for g in model['functionalGroups'] if g['label']=='Tertiary amine nitrogen']
ck([g['atomIndices'] for g in removed]==[[2],[6],[10]],'Only three incorrect nitrate nitrogen annotations')
model['functionalGroups']=[g for g in model['functionalGroups'] if g not in removed]
ck(len(model['functionalGroups'])==10,'Three nitrate, one Ce and six water groups retained')
save(modelrel,model);ck(diffs(oldmodel,model)==[{'pointer':'/functionalGroups','before':oldmodel['functionalGroups'],'after':model['functionalGroups']}],'Model annotation-only change')
registry=read(A/'registry-additions.json');oldregistry=deepcopy(registry);entry=next(e for e in registry['entries'] if e['id']=='pati2009-cerium-nitrate-reference');oldentry=deepcopy(entry)
ck(entry['functionalGroups']==oldmodel['functionalGroups'],'Original registry/model annotation equality');entry['functionalGroups']=deepcopy(model['functionalGroups']);entry['assetHashes']['model2dPath']=sha(O/modelrel)
oldhash,newhash=jsha(oldentry),jsha(entry);save('registry-additions.json',registry)
ck(oldhash=='bc43826def7091c04182008fc9b5b109222faa6baa4a177a281d4da750f0c3aa','Original entry digest')
ck({d['pointer'] for d in diffs(oldregistry,registry)}=={'/entries/0/functionalGroups','/entries/0/assetHashes/model2dPath'},'Registry minimal delta')
changes={'registry-additions.json':diffs(oldregistry,registry),modelrel:diffs(oldmodel,model)}
def replace_digest(v):
 if isinstance(v,dict):return {k:replace_digest(x) for k,x in v.items()}
 if isinstance(v,list):return [replace_digest(x) for x in v]
 return newhash if v==oldhash else v
for rel in ['bindings-proposal.json','material-slot-map.json']:
 old=read(A/rel);new=replace_digest(old);ds=diffs(old,new);ck(len(ds)==4,'Four nitrate digest mirrors '+rel)
 for d in ds:ck(d['pointer'].endswith('/entry_sha256') and d['before']==oldhash and d['after']==newhash,'Only entry digest '+rel)
 save(rel,new);changes[rel]=ds
pub=read(A/'public-asset-proposal.json');oldpub=deepcopy(pub)
for x in pub['assets']:
 if x['path']==modelrel:x['sha256']=sha(O/modelrel)
ds=diffs(oldpub,pub);ck(len(ds)==1 and ds[0]['pointer'].endswith('/sha256'),'Only public model digest');save('public-asset-proposal.json',pub);changes['public-asset-proposal.json']=ds
public=read(A/'effective-public-assets.json');oldpublic=deepcopy(public);public[modelrel]={'path':str((O/modelrel).resolve()),'sha256':sha(O/modelrel)};save('effective-public-assets.json',public)
ck(set(public)==set(oldpublic),'Same 34 asset identities')
for rel,x in public.items():
 ck(sha(x['path'])==x['sha256'],'Effective public asset hash '+rel)
 if rel!=modelrel:ck(x==oldpublic[rel],'Other public assets unchanged '+rel)
for e in registry['entries']:
 if e['id']!='pati2009-cerium-nitrate-reference':ck(e==next(x for x in oldregistry['entries'] if x['id']==e['id']),'Other identity unchanged '+e['id'])
 for g in e['functionalGroups']:ck(all(isinstance(i,int) and i>=0 for i in g['atomIndices']),'Valid group index type')
ck(next(e for e in registry['entries'] if e['id']=='pati2009-tea-reference')['functionalGroups']==next(e for e in oldregistry['entries'] if e['id']=='pati2009-tea-reference')['functionalGroups'],'True TEA tertiary amine retained')
effective=read(A/'effective-file-map.json')
for rel in ['registry-additions.json','bindings-proposal.json','material-slot-map.json','public-asset-proposal.json']:effective[rel]={'path':str((O/rel).resolve()),'sha256':sha(O/rel)}
for rel,x in effective.items():ck(sha(x['path'])==x['sha256'],'Effective metadata hash '+rel)
save('effective-file-map.json',effective)
v1=read(P/'canonical-proposal/v1/record-manifest.json');v2=read(P/'canonical-proposal/v2/record-manifest.json');by1={x['record_id']:x for x in v1['records']};by2={x['record_id']:x for x in v2['records']};ck(set(by1)==set(by2),'Same canonical record IDs')
for rid,x in by1.items():ck(sha(x['path'])==sha(by2[rid]['path']),'V2 record bytes unchanged '+rid)
ca=P/'canonical-reader-independent-audit/independent-audit-v2.json';ck(sha(ca)=='e59bfbcec0f265178bb502b814993c40649bf57ac006ced6394648146dcad55a' and read(ca)['status']=='passed','Distinct canonical v2 pass')
history={'schema':'mattersyn-molecule-annotation-correction/1','author':'/root/peng1998_reader_assets','finding':'PM1: Three nitrate nitrogen atoms were incorrectly annotated as tertiary amines. They remain part of the correct nitrate-resonance groups.','base_freeze_path':str(A/'package-freeze.json'),'base_freeze_sha256':sha(A/'package-freeze.json'),'source_of_error':'The original broad [NX3;H0] SMARTS also matched positively charged nitrate nitrogen. This correction removes only those three unsupported amine labels, without regenerating geometry.','changes':changes,'effective_public_asset_changes':diffs(oldpublic,public),'unchanged':['All atoms, bonds, coordinates, formulas, SVG and preview bytes','All source/canonical quantities, sample/slot identities and stock mappings','All other registry entries and all six cached 3D models','True TEA tertiary-amine annotation'],'canonical_v2_receipt':{'package_manifest_sha256':sha(P/'canonical-proposal/v2/package-manifest.json'),'audit_sha256':sha(ca),'all_19_record_bytes_unchanged':True,'original_v1_bound_record_bytes_remain_valid':True},'independent_audit_status':'pending'}
save('correction-history.json',history)
save('author-validation.json',{'status':'passed_author_checks_not_independent_approval','checks':count,'original_169_bound_files_unchanged':True,'effective_asset_count':len(public),'record_count':len(by1),'removed_incorrect_groups':removed,'only_model_field_changed':'functionalGroups','all_svg_and_preview_bytes_unchanged':True,'latest_canonical_records_unchanged':True})
(O/'README.md').write_text('# Pati molecular annotation correction v2\n\nThe original 8b5724b9… freeze is preserved. This overlay removes three false tertiary-amine annotations on nitrate nitrogen at indices 2, 6 and 10 from the cerium-nitrate 2D model and registry entry. Correct nitrate, cerium and water groups remain. TEA retains its genuine tertiary-amine annotation. No graph, coordinate, formula, SVG, preview, quantity, stock, specimen or slot assignment changes.\n\nUse this directory’s effective-file-map.json and effective-public-assets.json. Only one of 34 asset bytes changes, with the same public relative path; dependent registry and entry digests are refreshed. The exact changed JSON pointers are in correction-history.json. The unchanged original 169-file boundary is verified. The separate canonical v2 pass is bound as a receipt because all 19 record bytes are unchanged; no source or canonical files are rewritten.\n\nThis is author correction and validation, awaiting a distinct reviewer. No browser, publication, model-training or product-coordinate approval is added.\n','utf-8')
print(json.dumps({'checks':count,'replacements':4,'public_asset_replacements':1,'status':'prepared_unfrozen'}))
