"""Preserve v1 and add two source-crystal references plus scoped display mapping."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil
E=Path(__file__).resolve().parent;A=E/'site-integration-proposal/v1';O=E/'site-integration-proposal/v2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert not O.exists(),'Preserve existing version'
for row in read(A/'package-freeze.json')['files']:assert sha(A/row['path'])==row['sha256']
shutil.copytree(A,O)
# The copied freeze describes v1; replace only in the newly created v2 directory.
bindings={'evans-2010-species9-crystallization':'species9-crystallization','evans-2010-molecular9-structure':'species9-cif'}
changes=[]
for rid,sample in bindings.items():
 p=O/'records'/(rid+'.json');r=read(p);assert not r['structure_assets'];assert sample in {p['sample_id'] for p in r['products']}
 r['structure_assets']=[{'id':'evans2010-species9-source-model','role':'measured_sample','sample_id':sample,'url':'/assets/chemical-registry/models/evans2010-species9-reference-3d.json','description':'Molecular species9 source crystallographic refinement, transformed from fractional to Cartesian coordinates. Asymmetric-unit molecule only;20H atoms use the reported calculated riding model. This source-specific molecular model is not a CdSe/PbSe quantum dot, a full periodic refinement file, or an exact-structure training pair. Download is the reviewed coordinate-transform JSON, not the original CIF.','eligible_as_measured_label':False}]
 save(p,r);changes.append({'record_id':rid,'sample_id':sample,'before_sha256':sha(A/'records'/p.name),'after_sha256':sha(p),'change':'Added existing qualified source molecular structure reference only.'})
registry=read(O/'molecules/bindings-additions.json')
for row in changes:registry['sourceRecordSha256'][row['record_id']]=row['after_sha256']
save(O/'molecules/bindings-additions.json',registry)
manifest=read(O/'promotion-manifest.json')
for row in manifest['records']:row['promoted_sha256']=sha(O/'records'/(row['record_id']+'.json'))
manifest['version']=2;manifest['qualified_molecular_reference_bindings']=changes;save(O/'promotion-manifest.json',manifest)
reader=read(O/'reader/evans2010.json');records={p.stem:read(p) for p in (O/'records').glob('*.json')};ids={rid:set() for rid in records}
for sec in reader['reader_sections']:
 if sec['id']=='structures':
  for item in sec['items']:
   for link in item.get('canonical_links',[]):
    bits=link['json_pointer'].strip('/').split('/')
    if bits[0]=='measurements':ids[link['record_id']].add(records[link['record_id']]['measurements'][int(bits[1])]['id'])
save(O/'record-structural-measurements.json',{rid:sorted(v) for rid,v in ids.items()})
save(O/'revision-history.json',{'from_freeze_sha256':sha(A/'package-freeze.json'),'changes':changes,'scientific_values_and_coordinates_unchanged':True,'additional_change':'Record-scoped structural measurement ID mapping derived from independently passed reader section assignments. It changes display only, never training labels or scientific values.'})
files=[{'path':p.relative_to(O).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(O.rglob('*')) if p.is_file() and p.name!='package-freeze.json']
save(O/'package-freeze.json',{'schema':'mattersyn.site_integration_proposal_freeze/1','author':'/root','at':datetime.now(timezone.utc).isoformat(),'status':'frozen_for_independent_promotion_audit','version':2,'prior_freeze_sha256':sha(A/'package-freeze.json'),'files':files,'source_audits':manifest['source_audits'],'author_script_sha256':sha(Path(__file__))})
print(json.dumps({'freeze_sha256':sha(O/'package-freeze.json'),'qualified_molecular_reference_bindings':len(changes),'record_scoped_structural_measurements':sum(len(v) for v in ids.values()),'shared_site_changed':False}))
