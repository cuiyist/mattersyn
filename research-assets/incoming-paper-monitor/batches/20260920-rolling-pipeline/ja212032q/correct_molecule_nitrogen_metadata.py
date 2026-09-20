"""Preserved source-neutral metadata-only molecular overlay; no geometry change."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy
G=Path(__file__).resolve().parent;O=G/'visuals/molecules';R=O/'canonical-v2-rebind';N=O/'metadata-correction-v3'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def save(p,x):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not N.exists();N.mkdir()
prior=read(R/'package-freeze.json');checks=[]
def ck(ok,s):
 assert ok,s
 checks.append(s)
for p,h in prior['bound_files'].items():ck(sha(p)==h,'Prior bound bytes preserved '+p)
effective=read(R/'effective-file-map.json');reg=read(effective['registry-additions.json']['path']);entry=next(e for e in reg['entries']if e['id']=='ghosh2012-liquid-nitrogen-reference');oldentry=js(entry)
relative=entry['model3dPath'];oldmodel=read(O/relative);model=copy.deepcopy(oldmodel)
assert model['sourceType']=='Geometry derived from an external reference, not observed Norberg atomic coordinates'
model['sourceType']='Geometry derived from an external reference; not observed sample coordinates'
save(N/relative,model)
ck({k:v for k,v in oldmodel.items()if k!='sourceType'}=={k:v for k,v in model.items()if k!='sourceType'},'Only sourceType leaf changed in model')
oldhash=entry['assetHashes']['model3dPath'];entry['assetHashes']['model3dPath']=sha(N/relative);newentry=js(entry)
save(N/'registry-additions.json',reg);effective['registry-additions.json']={'path':str(N/'registry-additions.json'),'sha256':sha(N/'registry-additions.json')}
replacements={oldentry:newentry,oldhash:sha(N/relative)};changes=[]
def replace(x,p=''):
 if isinstance(x,dict):return {k:replace(v,p+'/'+k)for k,v in x.items()}
 if isinstance(x,list):return [replace(v,p+'/'+str(i))for i,v in enumerate(x)]
 if isinstance(x,str)and x in replacements:
  changes.append({'pointer':p,'before':x,'after':replacements[x]});return replacements[x]
 return x
deltafiles={}
for n in ['bindings-proposal.json','material-slot-map.json','public-asset-proposal.json']:
 before=read(effective[n]['path']);changes=[];after=replace(before)
 if before!=after:
  save(N/n,after);deltafiles[n]=changes;effective[n]={'path':str(N/n),'sha256':sha(N/n)}
ck(read(effective['bindings-proposal.json']['path'])['recordBindings']==read(O/'bindings-proposal.json')['recordBindings'],'All 88 registry assignments unchanged')
for r in ['atoms','bonds','functionalGroups','coordinateUnits','referenceDistanceAngstrom','referenceIsotopologue']:
 ck(model[r]==oldmodel[r],'Nitrogen '+r+' unchanged')
assets=read(effective['public-asset-proposal.json']['path'])['relative_asset_files']
assetmap={rel:{'path':str(N/rel if rel==relative else O/rel),'sha256':h}for rel,h in assets.items()}
for rel,d in assetmap.items():ck(sha(d['path'])==d['sha256'],'Effective asset '+rel)
save(N/'effective-file-map.json',effective);save(N/'effective-public-assets.json',assetmap)
save(N/'metadata-delta.json',{'author':'/root/backlog_eta','reviewer_request':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),'base_freeze_sha256':sha(O/'package-freeze.json'),'canonical_v2_rebind_sha256':sha(R/'package-freeze.json'),'model_change':{'relative_path':relative,'pointer':'/sourceType','before':oldmodel['sourceType'],'after':model['sourceType'],'old_sha256':oldhash,'new_sha256':sha(N/relative)},'dependent_changes':deltafiles,'registry_entry_delta':'Only assetHashes/model3dPath updated; all names, roles, source captions, identities and historical retained-provenance fields unchanged.','unchanged_model_arrays':True,'unchanged_slot_assignments':88,'unchanged_stock_components':8,'independent_approval':False,'checks':checks,'check_count':len(checks)})
(N/'README.md').write_text('Effective private molecular revision 3. Follow effective-file-map.json and effective-public-assets.json. Only the nitrogen model sourceType is neutralized; coordinates/connectivity/reference distance and all slot/stock/scientific data are unchanged. Updated dependent digests are recorded. Original molecule freeze and canonical-v2 rebind remain immutable. Registry entries remain unapproved until the separate peer audit.\n',encoding='utf-8')
bound=copy.deepcopy(prior['bound_files']);bound[str(R/'package-freeze.json')]=sha(R/'package-freeze.json');bound[str(Path(__file__))]=sha(__file__)
bound.update({str(p):sha(p)for p in N.rglob('*')if p.is_file()})
manifest={'schema':'mattersyn-private-molecular-metadata-overlay/1','author':'/root/backlog_eta','source_id':'ghosh2012','status':'author_metadata_checks_passed_independent_audit_pending','canonical_version':2,'canonical_package_sha256':prior['canonical_package_sha256'],'base_freeze_path':str(O/'package-freeze.json'),'base_freeze_sha256':sha(O/'package-freeze.json'),'previous_rebind_path':str(R/'package-freeze.json'),'previous_rebind_sha256':sha(R/'package-freeze.json'),'counts':prior['counts'],'effective_files':effective,'effective_public_assets':assetmap,'author_checks':len(checks),'bound_files':bound,'bound_file_count':len(bound),'independent_approval':False,'site_written':False}
save(N/'package-freeze.json',manifest)
print(json.dumps({'manifest':str(N/'package-freeze.json'),'sha256':sha(N/'package-freeze.json'),'checks':len(checks),'new_model_sha256':sha(N/relative)}))
