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
 'core-3-or-4':('CdSe','ghosh2012-cdse-core-reference','CdSe core · standard 3 or 4 nm branches'),
 'core-2p2':('CdSe','ghosh2012-cdse-core-reference','CdSe core · 2.2 nm branch'),
 'core-5p5':('CdSe','ghosh2012-cdse-core-reference','CdSe core · 5.5 nm branch'),
 'core-only-7nm':('CdSe','ghosh2012-cdse-core-reference','CdSe core-only control · 7 nm; preparation not reported'),
 **{k:('CdSe/CdS','ghosh2012-cdse-cds-reference',label) for k,label in {
 'optimized-shell':'CdSe/CdS · optimized shell-growth context',
 'ode-primary':'CdSe/CdS · ODE / primary-amine comparison',
 'od-primary':'CdSe/CdS · octadecane / primary-amine comparison',
 'od-late-dilution':'CdSe/CdS · octadecane / late-dilution comparison',
 'od-extreme-dilution':'CdSe/CdS · octadecane / extreme-dilution comparison',
 'od-secondary':'CdSe/CdS · octadecane / secondary-amine comparison',
 'od-no-added-amine':'CdSe/CdS · octadecane / no-added-amine comparison',
 'od-long-anneal':'CdSe/CdS · octadecane / long-anneal comparison',
 'withdraw-10':'CdSe/CdS · 10% solution-withdrawal comparison',
 'withdraw-1':'CdSe/CdS · 1% solution-withdrawal comparison',
 'withdraw-1-oa':'CdSe/CdS · 1% solution withdrawal with OA comparison',
 'constant-s':'CdSe/CdS · constant-S comparison',
 'si-blinking-examples':'CdSe/CdS · SI blinking-example cohort',
 'optimized-performance':'CdSe/CdS · optimized-performance cohort',
 'four-core-series':'CdSe/CdS · four-core comparison cohort',
 'si-large-core-example':'CdSe/CdS · SI large-core example',
 **{'anneal-row-'+str(i):'CdSe/CdS · annealing table row '+str(i) for i in range(1,6)},
 **{'lifetime-row-'+str(i).zfill(2):'CdSe/CdS · SI lifetime table row '+str(i) for i in range(1,19)}
 }.items()}
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
notice='CdSe core sizes, CdSe/CdS shell-growth variants, parameter comparisons and optical cohorts retain distinct source contexts. Identity cards are symbolic and contain no atomic coordinates. TEM, PXRD, FTIR and optical measurements keep their own specimen assignments; nominal shell monolayers are not an atomic structure or proof of shared batch identity. No exact structure–recipe pair or DFT-ready input is inferred.'
save(O/'product-contexts-additions.json',{'recordContexts':contexts,'sourceNotices':{'ghosh2012':notice}})
save(O/'bindings.json',{'author':'/root','source_record_sha256':bound,'promotion_freeze_sha256':sha(P/'package-freeze.json'),'explicit_sample_mapping':mapping,'excluded_contexts':excluded,'no_coordinate_files_added':True,'scientific_values_unchanged':True})
save(O/'package-freeze.json',{'author':'/root','at':datetime.now(timezone.utc).isoformat(),'status':'pending_independent_product_context_audit','files':[{'path':p.name,'sha256':sha(p)} for p in sorted(O.glob('*.json'))],'contexts':sum(map(len,contexts.values())),'records':len(contexts),'registry_sha256':sha(P/'molecules/registry-additions.json'),'script_sha256':sha(Path(__file__))})
print(json.dumps({'freeze_sha256':sha(O/'package-freeze.json'),'contexts':sum(map(len,contexts.values())),'records':len(contexts),'site_changed':False}))
