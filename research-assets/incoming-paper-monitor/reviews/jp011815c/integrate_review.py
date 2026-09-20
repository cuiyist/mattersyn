"""Root-only import of independently audited Shah2001 content into the existing Site."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';V=B/'visuals'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
a=read(B/'canonical-records-audit.json');assert a['status'].startswith('passed')
drafts=sorted((B/'canonical-drafts').glob('*.json'));assert len(drafts)==19
assert {p.stem for p in drafts}==set(a['record_hashes'])
for p in drafts:assert sha(p)==a['record_hashes'][p.stem]
for name in ['reader-source-audit.json','molecular-source-audit.json','crop-source-audit.json','visual-source-audit.json']:
 assert read(B/name)['status'].startswith('passed'),name
assert sha(B/'public-review-proposal/shah2001.json')==read(B/'reader-source-audit.json')['reader_sha256']
assert read(B/'reader-assets/canonical-to-reader-audit.json')['status'].startswith('passed')
ma=read(B/'molecular-source-audit.json');assert sha(V/'registry-additions.json')==ma['registry_sha256']
O=B/'inventory-proposal';O.mkdir(exist_ok=True)
if not(O/'base-inventory-summary.json').exists():shutil.copy2(S/'data/inventory-summary.json',O/'base-inventory-summary.json')
records=[]
for p in drafts:
 r=read(p);r['quality']['review_status']='source_reviewed'
 r['quality']['review_scope']='All eight supplied main pages read and visually inspected with independent source, canonical, molecular, apparatus and reader audits. Nine Ag A–I experiments, separate Ir/Pt conditions, typical framework, common workup, unassigned microscopy/optical cohorts, prior comparisons and author models retain their distinct scope. No matched SI verified; no invented per-run masses, Pt precursor correction or atomic coordinates.'
 r['sources'][0]['main_status']='All eight supplied main pages text and visually reviewed; independent source and canonical audits completed.'
 write(S/'data/records'/p.name,r);records.append(r)
review=read(B/'public-review-proposal/shah2001.json')
review['remaining_gaps']=[g for g in review['remaining_gaps'] if g!='Independent source-to-reader, crop and canonical-link audits are pending.']
for category in ['figures','tables','equations','schemes','source_notes']:
 for item in review.get(category,[]):
  if item.get('public_asset'):item['reviewed']=True
review.update(coverage_status='supplied_main_text_and_visual_review_complete_si_unverified',source_review_promoted=True,independent_audit='All eight supplied main pages, canonical extraction, source-to-reader coverage, chemical identities and apparatus scenes independently audited. SI not located or verified; publication is tracked separately.',publication_status='Reviewed contribution for the existing MatterSyn atlas; deployment tracked separately.',training_note='Nine Ag experiments and two Ir/Pt routes remain source-linked variants of one study. Ag diameters explicitly match Table 1 experiments A–I. Absolute charges per row are unreported; inferred common Ir/Pt conditions retain their status. Prior optical comparisons, unassigned images and model values do not create extra experimental labels. No exact-structure or success labels are inferred.')
for item in review['recipe_inventory']:item['status']='source_reviewed'
for f in ['Ag','Ir','Pt']:
 assert set(review['material_evidence_records'][f])=={r['record_id']for r in records if r['material']['formula'] in [f,'Ag/Ir/Pt']}
write(S/'data/paper-reviews/shah2001.json',review)
for asset in read(B/'reader-assets/crop-manifest.json')['assets']:
 p=B/'reader-assets'/asset['relative_asset'];assert sha(p)==asset['sha256'];dest=S/'dist'/asset['public_asset'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
dst=S/'dist/assets/chemical-registry'
for asset in read(V/'asset-manifest.json')['files']:
 p=V/asset['path'];assert sha(p)==asset['sha256'];dest=dst/asset['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
registry=read(dst/'registry.json');entries=read(V/'registry-additions.json')['entries'];ids={e['id']for e in entries}
assert not (ids & {e['id']for e in registry['entries']}), 'New chemical IDs collide with existing registry'
registry['entries']+=entries;write(dst/'registry.json',registry)
bindings=read(dst/'bindings.json');delta=read(V/'bindings-additions.json')
bindings['recordBindings'].update(delta['recordBindings']);bindings.setdefault('bindingNotes',{}).update(delta.get('bindingNotes',{}))
for rid,bb in delta['recordBindings'].items():
 p=S/'data/records'/(rid+'.json');assert set(bb)=={m['id']for m in read(p)['materials']};bindings['sourceRecordSha256'][rid]=sha(p)
write(dst/'bindings.json',bindings)
products=read(dst/'product-bindings.json');products['recordBindings'].update(read(V/'product-reference-proposal.json')['recordBindings']);write(dst/'product-bindings.json',products)
shutil.copy2(V/'shah2001-protocol.mjs',S/'dist/shah2001-protocol.mjs')
p=S/'dist/protocol-visuals.mjs';t=p.read_text(encoding='utf-8')
assert "from './shah2001-protocol.mjs'" not in t
t="import {buildShah2001Scene,createShah2001Art} from './shah2001-protocol.mjs';\n"+t
t=t.replace('const sourceArt=createPeng1998Art','const sourceArt=createShah2001Art(o,r)||createPeng1998Art')
t=t.replace('peng=buildPeng1998Scene(o,r);','peng=buildPeng1998Scene(o,r),shah=buildShah2001Scene(o,r);')
t=t.replace('peng?.caption||','shah?.caption||peng?.caption||')
t=t.replace('if(danek||dabbousi||veinot||yao||stiger||peng){','if(danek||dabbousi||veinot||yao||stiger||peng||shah){')
p.write_text(t,encoding='utf-8')
p=S/'dist/crystal-viewer.mjs';t=p.read_text(encoding='utf-8')
t=t.replace("['veinot1997','yao1998','stiger1999','peng1998']","['veinot1997','yao1998','stiger1999','peng1998','shah2001']")
t=t.replace("r.lineage?.source_group==='peng1998'?'Material identity'","['peng1998','shah2001'].includes(r.lineage?.source_group)?'Material identity'")
t=t.replace("['yao1998','stiger1999','peng1998'].includes","['yao1998','stiger1999','peng1998','shah2001'].includes")
t=t.replace(" if(r.lineage?.source_group==='peng1998'&&entryId)"," if(r.lineage?.source_group==='shah2001'&&entryId)host.append(el('p','The supplied article provides original microscopy and reports crystalline metal cores, but supplies no measured atomic coordinates or refined sample CIF. Hexagonal particle packing is an assembly observation, not a bulk crystal phase. Product cards and molecular conformers are reference illustrations.','guide-notice'));\n if(r.lineage?.source_group==='peng1998'&&entryId)")
p.write_text(t,encoding='utf-8')
p=S/'scripts/build_atlas.py';t=p.read_text(encoding='utf-8').replace("NAMES['Ag']='Silver · supported nanocrystal component'","NAMES['Ag']='Silver nanocrystals'\nNAMES['Pt']='Platinum nanocrystals'");p.write_text(t,encoding='utf-8')
p=S/'data/measurement-display.json';d=read(p);d['structural_properties']=list(dict.fromkeys(d['structural_properties']+['diameter_standard_deviation','size_distribution_asset','crystallinity','assembly','elemental_identification','polycrystallinity','population_scope','interparticle_edge_separation','inset_image_scale_bar','optical_comparison_mean_diameter','relative_size']));write(p,d)
p=S/'scripts/build_dataset.py';p.write_text(p.read_text(encoding='utf-8').replace("'dataset_version':'0.12.0'","'dataset_version':'0.13.0'"),encoding='utf-8')
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs')):
 t=p.read_text(encoding='utf-8');n=t.replace('0.12.0-r1','0.13.0-r1')
 if n!=t:p.write_text(n,encoding='utf-8')
write(B/'integration-manifest.json',{'status':'integrated_pending_build_and_browser','at':datetime.now(timezone.utc).isoformat(),'source_id':'shah2001','records':{r['record_id']:sha(S/'data/records'/(r['record_id']+'.json'))for r in records},'reader_sha256':sha(S/'data/paper-reviews/shah2001.json'),'private_reader_sha256':sha(B/'public-review-proposal/shah2001.json'),'apparatus_sha256':sha(S/'dist/shah2001-protocol.mjs'),'record_promotion_changes':['quality.review_status','quality.review_scope','sources[0].main_status']})
print('Imported 19 audited records into existing MatterSyn; build, browser verification and publication remain pending.')
