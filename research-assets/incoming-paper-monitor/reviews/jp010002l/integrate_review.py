"""Root-only import of the independently audited Braun2001 contribution."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';V=B/'visuals'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
drafts=sorted((B/'canonical-drafts').glob('*.json'));assert len(drafts)==9
a=read(B/'canonical-records-audit.json');assert a['status'].startswith('passed')
assert {p.stem for p in drafts}==set(a['record_hashes'])
for p in drafts:assert sha(p)==a['record_hashes'][p.stem]
for name in ['reader-source-audit.json','molecular-source-audit.json','visual-source-audit.json','bindings-source-audit.json']:assert read(B/name)['status'].startswith('passed'),name
assert read(B/'reader-source-audit.json')['asset_count']==8
assert sha(B/'reader-assets/crop-manifest.json')==read(B/'reader-source-audit.json')['crop_manifest_sha256']
assert sha(B/'public-review-proposal/braun2001.json')==read(B/'reader-source-audit.json')['reader_sha256']
assert read(B/'public-review-proposal/proposal-validation.json')['status'].startswith('passed')
assert sha(V/'registry-additions.json')==read(B/'molecular-source-audit.json')['registry_sha256']
assert sha(V/'braun2001-protocol.mjs')==read(B/'visual-source-audit.json')['module_sha256']
assert read(V/'bindings-additions.json')['sourceRecordSha256']=={p.stem:sha(p)for p in drafts}
O=B/'inventory-proposal';O.mkdir(exist_ok=True)
if not(O/'base-inventory-summary.json').exists():shutil.copy2(S/'data/inventory-summary.json',O/'base-inventory-summary.json')
records=[]
for p in drafts:
 r=read(p);r['quality']['review_status']='source_reviewed';r['quality']['review_scope']='All four supplied main pages read and visually inspected, with independent source, canonical, molecular, apparatus and reader audits. Three CdS/HgS/CdS architectures retain distinct exchange/deposition sequences and source-assigned optical contexts. Counterions, several feed doses and the core-size discrepancy remain unresolved. Matching SI not located or verified; cited upstream preparations and theory are not independently reviewed here.'
 r['sources'][0]['main_status']='All four supplied main pages text and visually reviewed; independent source and canonical audits completed. Matching local SI not located or verified.'
 write(S/'data/records'/p.name,r);records.append(r)
review=read(B/'public-review-proposal/braun2001.json')
review['remaining_gaps']=[g for g in review['remaining_gaps'] if g not in ['Independent source-to-reader, crop and canonical-link audits are pending.','Independent audits pending.']]
for category in ['figures','tables','equations','schemes','source_notes']:
 for item in review.get(category,[]):
  if item.get('public_asset'):item['reviewed']=True
review.update(coverage_status='supplied_main_text_and_visual_review_complete_si_unverified',source_review_promoted=True,independent_audit='All four supplied main pages, canonical extraction, reader coverage, original crops, molecular references and apparatus scenes independently audited. Matching SI remains unlocated or unverified; publication tracked separately.',publication_status='Reviewed contribution for the existing MatterSyn atlas; deployment tracked separately.',training_note='Three source-described layer sequences remain distinct. Recipe completeness, actual specimen joins and task eligibility are explicit; named architecture, cited tetrahedral shape and illustrated layers do not supply measured atomic coordinates or exact-structure labels. Water-reference subtraction is not a nanocrystal Raman measurement.')
for item in review['recipe_inventory']:item['status']='source_reviewed'
assert review['review_scope']=='supplied_main_only_si_unverified'
write(S/'data/paper-reviews/braun2001.json',review)
for asset in read(B/'reader-assets/crop-manifest.json')['assets']:
 p=B/'reader-assets'/asset['relative_asset'];assert sha(p)==asset['sha256'];dest=S/'dist'/asset['public_asset'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
dst=S/'dist/assets/chemical-registry'
for asset in read(V/'asset-manifest.json')['files']:
 p=V/asset['path'];assert sha(p)==asset['sha256'];dest=dst/asset['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
registry=read(dst/'registry.json');entries=read(V/'registry-additions.json')['entries'];ids={e['id']for e in entries};assert not(ids & {e['id']for e in registry['entries']}),'New chemical IDs collide';registry['entries']+=entries;write(dst/'registry.json',registry)
bindings=read(dst/'bindings.json');delta=read(V/'bindings-additions.json');bindings['recordBindings'].update(delta['recordBindings']);bindings.setdefault('bindingNotes',{}).update(delta.get('bindingNotes',{}))
for rid,bb in delta['recordBindings'].items():
 p=S/'data/records'/(rid+'.json');assert set(bb)=={m['id']for m in read(p)['materials']};bindings['sourceRecordSha256'][rid]=sha(p)
write(dst/'bindings.json',bindings)
products=read(dst/'product-bindings.json');products['recordBindings'].update(read(V/'product-reference-proposal.json')['recordBindings']);write(dst/'product-bindings.json',products)
shutil.copy2(V/'braun2001-protocol.mjs',S/'dist/braun2001-protocol.mjs')
p=S/'dist/protocol-visuals.mjs';t=p.read_text(encoding='utf-8');assert "from './braun2001-protocol.mjs'" not in t
t="import {buildBraun2001Scene,createBraun2001Art} from './braun2001-protocol.mjs';\n"+t
t=t.replace('const sourceArt=createGerion2001Art','const sourceArt=createBraun2001Art(o,r)||createGerion2001Art')
t=t.replace('gerion=buildGerion2001Scene(o,r);','gerion=buildGerion2001Scene(o,r),braun=buildBraun2001Scene(o,r);')
t=t.replace('gerion?.caption||','braun?.caption||gerion?.caption||')
t=t.replace('||shah||gerion){','||shah||gerion||braun){').replace('=>gerion?','=>(gerion||braun)?')
t=t.replace("uM:'µM'","uM:'µM',uJ:'µJ'")
t=t.replace("q.qualifier==='room temperature'","/^room temperature\\b/i.test(q.qualifier||'')")
p.write_text(t,encoding='utf-8')
p=S/'dist/crystal-viewer.mjs';t=p.read_text(encoding='utf-8');t=t.replace("'shah2001','gerion2001']","'shah2001','gerion2001','braun2001']")
t=t.replace(" if(r.lineage?.source_group==='gerion2001'&&entryId)"," if(r.lineage?.source_group==='braun2001'&&entryId)host.append(el('p','Layer-sequence illustrations follow the source-assigned CdS/HgS/CdS architectures. The paper cites tetrahedral CdS and shows schematic wavefunctions, but supplies no measured atomic coordinates, sample CIF, TEM, XRD or SAED pattern. Core-size values conflict between the general preparation and system descriptions; the original figures and source notes preserve that distinction.','guide-notice'));\n if(r.lineage?.source_group==='gerion2001'&&entryId)")
p.write_text(t,encoding='utf-8')
p=S/'scripts/build_atlas.py';t=p.read_text(encoding='utf-8');t=t.replace("NAMES['Pt']='Platinum nanocrystals'","NAMES['Pt']='Platinum nanocrystals'\nNAMES['CdS/HgS/CdS']='CdS/HgS quantum-dot quantum wells'\nNAMES['HgS']='Mercury sulfide · quantum-well component'");p.write_text(t,encoding='utf-8')
p=S/'data/measurement-display.json';d=read(p);props={m['property']for r in records for m in r['measurements']if any(k in m['property']for k in ['diameter','size','thickness','shape','morphology','well_count','layer_count','architecture'])};d['structural_properties']=list(dict.fromkeys(d['structural_properties']+sorted(props)));write(p,d)
p=S/'scripts/build_dataset.py';p.write_text(p.read_text(encoding='utf-8').replace("'dataset_version':'0.14.0'","'dataset_version':'0.15.0'"),encoding='utf-8')
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs'))+list((S/'dist').glob('*.html')):
 t=p.read_text(encoding='utf-8');n=t.replace('0.14.0-r1','0.15.0-r1')
 if p.suffix=='.html':n=n.replace('material-hub.mjs?v=0.12.0-r1','material-hub.mjs?v=0.15.0-r1')
 if n!=t:p.write_text(n,encoding='utf-8')
write(B/'integration-manifest.json',{'status':'integrated_pending_build_and_browser','at':datetime.now(timezone.utc).isoformat(),'source_id':'braun2001','records':{r['record_id']:sha(S/'data/records'/(r['record_id']+'.json'))for r in records},'reader_sha256':sha(S/'data/paper-reviews/braun2001.json'),'private_reader_sha256':sha(B/'public-review-proposal/braun2001.json'),'apparatus_sha256':sha(S/'dist/braun2001-protocol.mjs'),'record_promotion_changes':['quality.review_status','quality.review_scope','sources[0].main_status'],'schema_additions':[]})
print('Imported 9 audited records into the existing MatterSyn Site; build, browser checks and publication remain pending.')


