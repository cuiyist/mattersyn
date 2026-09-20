"""Bind existing audited symbolic identities to explicit canonical product contexts."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json
N=Path(__file__).resolve().parent;P=N/'site-integration-proposal/v1';O=N/'site-integration-proposal/product-context-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert not O.exists()
mapping={'CdSe/CdS':'morrison2017-cdse-cds-qb-reference','CdS':'morrison2017-cds-powder-reference','C14H12CdN2S4':'morrison2017-cdptc-reference','C18H20CdN2OS4':'morrison2017-cdptc-thf-crystal-reference'}
registry={e['id']:e for e in read(P/'molecules/registry-additions.json')['entries']}
contexts={};bound={};excluded=[]
for path in sorted((P/'records').glob('*.json')):
 r=read(path);rid=r['record_id'];bound[rid]=sha(path);rows=[]
 for i,s in enumerate(r['products']):
  comp=s['composition']['value'];entry=mapping.get(comp)
  if not entry:
   excluded.append({'record_id':rid,'sample_id':s['sample_id'],'reason':'No exact composition-to-symbol mapping approved; no context inferred from nominal record formula.'});continue
  assert registry[entry]['depictionKind']=='symbolic_context' and not registry[entry].get('model3dPath')
  qualifier='Precursor identity only; the SI crystal tables do not establish CdSe/CdS product coordinates.' if comp.startswith('C1') else 'Product identity only; no measured atomic coordinates, shell coverage or specimen join is inferred.'
  caption=comp+' · '+s['sample_id']+'. '+qualifier+' The symbol is a reference illustration; source-specific morphology, phase and measurements remain in the linked data.'
  rows.append({'sample_id':s['sample_id'],'label':comp,'registry_id':entry,'caption':caption,'phase':copy.deepcopy(s['phase']),'canonical_product_pointer':'/products/'+str(i),'composition_evidence':copy.deepcopy(s['composition']['evidence']),'morphology':copy.deepcopy(s['morphology']),'training_eligible':False,'atomic_model':False})
 if rows:contexts[rid]=rows
notice='Original TEM, XRD, optical measurements and precursor single-crystal tables are retained with their individual source contexts. Product identity drawings are symbolic. No CdSe/CdS product atomic coordinates or sample CIF are supplied; the precursor crystal is a separate chemical species. No unverified structure download or exact structure–recipe pair is inferred.'
save(O/'product-contexts-additions.json',{'recordContexts':contexts,'sourceNotices':{'morrison2017':notice}})
save(O/'bindings.json',{'author':'/root','source_record_sha256':bound,'promotion_freeze_sha256':sha(P/'package-freeze.json'),'excluded_contexts':excluded,'no_coordinate_files_added':True,'scientific_values_unchanged':True})
save(O/'package-freeze.json',{'author':'/root','at':datetime.now(timezone.utc).isoformat(),'status':'pending_independent_product_context_audit','files':[{'path':p.name,'sha256':sha(p)} for p in sorted(O.glob('*.json'))],'contexts':sum(map(len,contexts.values())),'records':len(contexts),'registry_sha256':sha(P/'molecules/registry-additions.json'),'script_sha256':sha(Path(__file__))})
print(json.dumps({'freeze_sha256':sha(O/'package-freeze.json'),'contexts':sum(map(len,contexts.values())),'records':len(contexts),'site_changed':False}))
