"""Root-owned import of the independently audited Gerion2001 review into the existing Site."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';V=B/'visuals';N=B/'neutralized-references'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
drafts=sorted((B/'canonical-drafts').glob('*.json'));assert len(drafts)==28
a=read(B/'canonical-records-audit.json');assert a['status'].startswith('passed')
assert {p.stem for p in drafts}==set(a['record_hashes'])
for p in drafts:assert sha(p)==a['record_hashes'][p.stem]
for name in ['reader-source-audit.json','molecular-source-audit.json','crop-source-audit.json','visual-source-audit.json','bindings-source-audit.json']:
 assert read(B/name)['status'].startswith('passed'),name
assert sha(B/'public-review-proposal/gerion2001.json')==read(B/'reader-source-audit.json')['reader_sha256']
assert read(B/'public-review-proposal/proposal-validation.json')['status'].startswith('passed')
assert sha(V/'registry-additions.json')==read(B/'molecular-source-audit.json')['registry_sha256']
assert sha(V/'gerion2001-protocol.mjs')==read(B/'visual-source-audit.json')['module_sha256']
assert read(V/'bindings-additions.json')['sourceRecordSha256']=={p.stem:sha(p)for p in drafts}
O=B/'inventory-proposal';O.mkdir(exist_ok=True)
if not(O/'base-inventory-summary.json').exists():shutil.copy2(S/'data/inventory-summary.json',O/'base-inventory-summary.json')
records=[]
for p in drafts:
 r=read(p);r['quality']['review_status']='source_reviewed'
 r['quality']['review_scope']='All eleven supplied main pages read and visually inspected, with independent source, canonical, molecular, apparatus and reader audits. Siloxane and MPA coating routes, optional APS extension, analytical procedures, distinct color cohorts and study-wide observations retain their scope. Explicitly announced HRTEM/AFM SI not located or verified; no missing micrographs, phase, atomic coordinates or recipe–specimen links invented.'
 r['sources'][0]['main_status']='All eleven supplied main pages text and visually reviewed; independent source and canonical audits completed. Announced HRTEM/AFM SI remains unmatched locally.'
 write(S/'data/records'/p.name,r);records.append(r)
review=read(B/'public-review-proposal/gerion2001.json')
review['remaining_gaps']=[g for g in review['remaining_gaps'] if g!='Independent source-to-reader, crop and canonical-link audits are pending.']
for category in ['figures','tables','equations','schemes','source_notes']:
 for item in review.get(category,[]):
  if item.get('public_asset'):item['reviewed']=True
review.update(coverage_status='supplied_main_text_and_visual_review_complete_si_unverified',source_review_promoted=True,independent_audit='All eleven supplied main pages, canonical extraction, reader coverage, molecular references and apparatus scenes independently audited. Announced HRTEM/AFM SI remains unlocated; publication is tracked separately.',publication_status='Reviewed contribution for the existing MatterSyn atlas; deployment tracked separately.',training_note='Two downstream coating routes and an optional incompletely dosed amine extension remain source-linked. Starting core/shell synthesis is cited upstream. Color-specific size and optical cohorts are not silently joined into individually documented recipe–product pairs. No exact-structure or success labels are inferred; analyses and separate comparator sets have distinct machine-readable state types.')
for item in review['recipe_inventory']:item['status']='source_reviewed'
assert review['review_scope']=='supplied_main_only_si_unverified'
write(S/'data/paper-reviews/gerion2001.json',review)
for asset in read(B/'reader-assets/crop-manifest.json')['assets']:
 p=B/'reader-assets'/asset['relative_asset'];assert sha(p)==asset['sha256'];dest=S/'dist'/asset['public_asset'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
dst=S/'dist/assets/chemical-registry'
for asset in read(V/'asset-manifest.json')['files']:
 p=V/asset['path'];assert sha(p)==asset['sha256'];dest=dst/asset['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
registry=read(dst/'registry.json');entries=read(V/'registry-additions.json')['entries'];ids={e['id']for e in entries}
assert not(ids & {e['id']for e in registry['entries']}),'New chemical IDs collide'
neutral=read(N/'registry-updates.json')
for e in neutral['entries']:
 for k in ['svgPath','model2dPath','model3dPath']:
  if e.get(k):shutil.copy2(N/e[k],dst/e[k])
updates={e['id']:e for e in neutral['entries']}
registry['entries']=[updates.get(e['id'],e)for e in registry['entries']]+entries;write(dst/'registry.json',registry)
bindings=read(dst/'bindings.json');delta=read(V/'bindings-additions.json')
bindings['recordBindings'].update(delta['recordBindings']);bindings.setdefault('bindingNotes',{}).update(delta.get('bindingNotes',{}))
for rid,bb in delta['recordBindings'].items():
 p=S/'data/records'/(rid+'.json');assert set(bb)=={m['id']for m in read(p)['materials']};bindings['sourceRecordSha256'][rid]=sha(p)
write(dst/'bindings.json',bindings)
products=read(dst/'product-bindings.json');products['recordBindings'].update(read(V/'product-reference-proposal.json')['recordBindings']);write(dst/'product-bindings.json',products)
shutil.copy2(V/'gerion2001-protocol.mjs',S/'dist/gerion2001-protocol.mjs')
p=S/'dist/protocol-visuals.mjs';t=p.read_text(encoding='utf-8');assert "from './gerion2001-protocol.mjs'" not in t
t="import {buildGerion2001Scene,createGerion2001Art} from './gerion2001-protocol.mjs';\n"+t
t=t.replace('const sourceArt=createShah2001Art','const sourceArt=createGerion2001Art(o,r)||createShah2001Art')
t=t.replace('shah=buildShah2001Scene(o,r);','shah=buildShah2001Scene(o,r),gerion=buildGerion2001Scene(o,r);')
t=t.replace('shah?.caption||','gerion?.caption||shah?.caption||')
t=t.replace('if(danek||dabbousi||veinot||yao||stiger||peng||shah){','if(danek||dabbousi||veinot||yao||stiger||peng||shah||gerion){')
t=t.replace("entries.filter(([k])=>/flow", "entries.filter(([k])=>gerion?!/^(temperature|duration|pressure)$/.test(k):/flow")
p.write_text(t,encoding='utf-8')
p=S/'dist/crystal-viewer.mjs';t=p.read_text(encoding='utf-8')
t=t.replace("'peng1998','shah2001']","'peng1998','shah2001','gerion2001']")
t=t.replace(" if(r.lineage?.source_group==='shah2001'&&entryId)"," if(r.lineage?.source_group==='gerion2001'&&entryId)host.append(el('p','The architecture drawing identifies the core/shell and surface chemistry; it does not assign a uniform shell, particle core count, crystal phase or measured atomic positions. Main-text size distributions and optical data are reproduced below. Announced HRTEM/AFM supporting figures are not available locally; no sample CIF or invented micrograph is supplied.','guide-notice'));\n if(r.lineage?.source_group==='shah2001'&&entryId)")
p.write_text(t,encoding='utf-8')
p=S/'scripts/build_atlas.py';t=p.read_text(encoding='utf-8');t=t.replace("NAMES['Pt']='Platinum nanocrystals'","NAMES['Pt']='Platinum nanocrystals'\nNAMES['CdSe/ZnS/siloxane']='Siloxane-coated CdSe/ZnS quantum dots'");p.write_text(t,encoding='utf-8')
p=S/'data/measurement-display.json';d=read(p);props={m['property']for r in records for m in r['measurements']if any(k in m['property']for k in ['diameter','height','size','shell_thickness','morphology','aggregation','eels','silicon_edge','selenium_edge','structure','grid','lattice'])};d['structural_properties']=list(dict.fromkeys(d['structural_properties']+sorted(props)));write(p,d)
p=S/'scripts/build_dataset.py';p.write_text(p.read_text(encoding='utf-8').replace("'dataset_version':'0.13.0'","'dataset_version':'0.14.0'"),encoding='utf-8')
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs')):
 t=p.read_text(encoding='utf-8');n=t.replace('0.13.0-r2','0.14.0-r1').replace('0.13.0-r1','0.14.0-r1')
 if n!=t:p.write_text(n,encoding='utf-8')
write(B/'integration-manifest.json',{'status':'integrated_pending_build_and_browser','at':datetime.now(timezone.utc).isoformat(),'source_id':'gerion2001','records':{r['record_id']:sha(S/'data/records'/(r['record_id']+'.json'))for r in records},'reader_sha256':sha(S/'data/paper-reviews/gerion2001.json'),'private_reader_sha256':sha(B/'public-review-proposal/gerion2001.json'),'apparatus_sha256':sha(S/'dist/gerion2001-protocol.mjs'),'record_promotion_changes':['quality.review_status','quality.review_scope','sources[0].main_status'],'schema_additions':['material_states.kind: analysis_data','material_states.kind: sample_set']})
print('Imported28 audited records into the existing MatterSyn Site; build, browser verification and publication remain pending.')
