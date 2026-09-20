"""Explicit sample-to-symbol mappings; no atomic model or inherited phase."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json
L=Path(__file__).resolve().parent; P=L/'site-integration-proposal/v1'; O=L/'site-integration-proposal/product-context-v1'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert not O.exists()
mapping={
 'bulk-a':('(C12H28N)2SbCl5','lian2021-bulk-a-reference','Bulk A'),
 'bulk-a-crystal':('(C12H28N)2SbCl5','lian2021-bulk-a-reference','Bulk A crystal'),
 'bulk-b':('(C12H28N)SbCl4','lian2021-bulk-b-reference','Bulk B'),
 'bulk-b-crystal':('(C12H28N)SbCl4','lian2021-bulk-b-reference','Bulk B crystal'),
 'nc-a':('(C12H28N)2SbCl5','lian2021-nc-a-reference','Nanocrystal A'),
 'nc-a-dried-powder':('(C12H28N)2SbCl5','lian2021-nc-a-reference','Nanocrystal A · dried powder'),
 'nc-a-colloid-vs-dry':('(C12H28N)2SbCl5','lian2021-nc-a-reference','Nanocrystal A · colloid/dry comparison'),
 'film-spincoat':('(C12H28N)2SbCl5','lian2021-spincoat-film-reference','Spin-coated A film'),
 'film-composite-series':(None,'lian2021-composite-film-reference','Nanocrystal A / polystyrene / phosphor composite film series'),
 **{'film-blend-'+str(i):(None,'lian2021-composite-film-reference','Composite film · blend '+str(i)) for i in range(1,6)}
}
registry={e['id']:e for e in read(P/'molecules/registry-additions.json')['entries']}
contexts={};bound={};excluded=[]
for path in sorted((P/'records').glob('*.json')):
 r=read(path);rid=r['record_id'];bound[rid]=sha(path);rows=[]
 for i,s in enumerate(r['products']):
  match=mapping.get(s['sample_id'])
  if not match:
   excluded.append({'record_id':rid,'sample_id':s['sample_id'],'reason':'No explicitly approved specimen-to-symbol mapping; calculations, mixed analytical scopes and unknown contexts are not inferred from nominal record composition.'});continue
  expected,entry,label=match
  assert s['composition']['value']==expected,(rid,s['sample_id'])
  assert registry[entry]['depictionKind']=='symbolic_context' and not registry[entry].get('model3dPath')
  caption=label+'. Symbolic material identity only; no atomic coordinates, surface geometry, specimen equivalence or phase is inferred. Measurements and original figures retain their own specimen and acquisition scope.'
  rows.append({'sample_id':s['sample_id'],'label':label,'registry_id':entry,'caption':caption,'phase':copy.deepcopy(s['phase']),'canonical_product_pointer':'/products/'+str(i),'composition_evidence':copy.deepcopy(s['composition']['evidence']),'morphology':copy.deepcopy(s['morphology']),'training_eligible':False,'atomic_model':False})
 if rows:contexts[rid]=rows
notice='Bulk A/B crystals, nanocrystal A, spin-coated films and composite films are separate source contexts. These identity cards are symbolic. Original PXRD, TEM/HRTEM, optical measurements and bulk single-crystal tables retain sample-specific provenance. Bulk coordinates cannot be assigned to nanocrystal or film specimens. No exact structure–recipe training pair or DFT-ready input is inferred.'
save(O/'product-contexts-additions.json',{'recordContexts':contexts,'sourceNotices':{'lian2021':notice}})
save(O/'bindings.json',{'author':'/root','source_record_sha256':bound,'promotion_freeze_sha256':sha(P/'package-freeze.json'),'explicit_sample_mapping':mapping,'excluded_contexts':excluded,'no_coordinate_files_added':True,'scientific_values_unchanged':True})
save(O/'package-freeze.json',{'author':'/root','at':datetime.now(timezone.utc).isoformat(),'status':'pending_independent_product_context_audit','files':[{'path':p.name,'sha256':sha(p)} for p in sorted(O.glob('*.json'))],'contexts':sum(map(len,contexts.values())),'records':len(contexts),'registry_sha256':sha(P/'molecules/registry-additions.json'),'script_sha256':sha(Path(__file__))})
print(json.dumps({'freeze_sha256':sha(O/'package-freeze.json'),'contexts':sum(map(len,contexts.values())),'records':len(contexts),'site_changed':False}))
