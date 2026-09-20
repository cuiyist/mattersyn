"""Root-only import of independently audited Yi contribution. Run once."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';V=B/'visuals'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
drafts=sorted((B/'canonical-drafts').glob('*.json'));assert len(drafts)==18
a=read(B/'canonical-records-audit.json');assert a['status'].startswith('passed')
assert {p.stem for p in drafts}==set(a['record_hashes'])
for p in drafts:assert sha(p)==a['record_hashes'][p.stem]
for f in ['reader-source-audit.json','molecular-source-audit.json','visual-source-audit.json','bindings-source-audit.json']:assert read(B/f)['status'].startswith('passed'),f
assert sha(B/'reader-assets/crop-manifest.json')==read(B/'reader-source-audit.json')['crop_manifest_sha256']
assert sha(B/'public-review-proposal/yi2002.json')==read(B/'reader-source-audit.json')['reader_sha256']
assert read(B/'public-review-proposal/proposal-validation.json')['status'].startswith('passed')
assert sha(V/'registry-additions.json')==read(B/'molecular-source-audit.json')['registry_sha256']
assert sha(V/'yi2002-protocol.mjs')==read(B/'visual-source-audit.json')['module_sha256']
assert read(V/'bindings-additions.json')['sourceRecordSha256']=={p.stem:sha(p)for p in drafts}
binding_audit=read(B/'bindings-source-audit.json')
assert sha(V/'bindings-additions.json')==binding_audit['bindings_sha256']
assert sha(V/'product-reference-proposal.json')==binding_audit['product_reference_sha256']
assert binding_audit['record_hashes']=={p.stem:sha(p)for p in drafts}
O=B/'inventory-proposal';O.mkdir(exist_ok=True)
if not(O/'base-inventory-summary.json').exists():shutil.copy2(S/'data/inventory-summary.json',O/'base-inventory-summary.json')
records=[]
for p in drafts:
 r=read(p);r['quality']['review_status']='source_reviewed';r['quality']['review_scope']='All five supplied main pages text-read and visually inspected, with independent source, canonical, molecular, apparatus and reader audits. Five hydrothermal annealing comparisons, independent solid-state bulk preparation, stock preparation, structural/optical analyses and author mechanisms retain their own evidence scopes. Printed mass/mole and nominal feed/formula conflicts, individual comparison charges and unassigned analysis specimens remain explicit. Matching SI not located or verified; cited external works not independently inspected.'
 r['sources'][0]['main_status']='All five supplied main pages text and visually reviewed; independent source and canonical audits completed. Matching local SI not located or verified.'
 write(S/'data/records'/p.name,r);records.append(r)
review=read(B/'public-review-proposal/yi2002.json')
review['remaining_gaps']=[g for g in review['remaining_gaps']if g not in ['Independent source-to-reader, crop and canonical-link audits are pending.','Independent audits pending.']]
for category in ['figures','tables','equations','schemes','source_notes']:
 for item in review.get(category,[]):
  if item.get('public_asset'):item['reviewed']=True
review.update(coverage_status='supplied_main_text_and_visual_review_complete_si_unverified',source_review_promoted=True,independent_audit='All five supplied main pages, canonical extraction, complete reader coverage, original crops, chemical identities and apparatus scenes independently audited. Matching SI remains unlocated or unverified; publication tracked separately.',publication_status='Reviewed contribution for the existing MatterSyn atlas; deployment tracked separately.',training_note='Five annealing conditions do not establish five independently quantified precursor batches. XRD crystallite size, TEM diameter and intensity-based particle-analyzer distribution retain distinct sample and metric scopes. Proposed energy-transfer mechanisms and specimen diagrams are not measured atomic structures or absolute quantum yields.')
for item in review['recipe_inventory']:item['status']='source_reviewed'
assert review['review_scope']=='supplied_main_only_si_unverified'
write(S/'data/paper-reviews/yi2002.json',review)
for asset in read(B/'reader-assets/crop-manifest.json')['assets']:
 p=B/'reader-assets'/asset['relative_asset'];assert sha(p)==asset['sha256'];dest=S/'dist'/asset['public_asset'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
dst=S/'dist/assets/chemical-registry'
for asset in read(V/'asset-manifest.json')['files']:
 p=V/asset['path'];assert sha(p)==asset['sha256'];dest=dst/asset['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
registry=read(dst/'registry.json');entries=read(V/'registry-additions.json')['entries'];assert not({e['id']for e in entries}&{e['id']for e in registry['entries']}),'New chemical IDs collide';registry['entries']+=entries;write(dst/'registry.json',registry)
bindings=read(dst/'bindings.json');delta=read(V/'bindings-additions.json');bindings['recordBindings'].update(delta['recordBindings']);bindings.setdefault('bindingNotes',{}).update(delta.get('bindingNotes',{}))
for rid,bb in delta['recordBindings'].items():
 p=S/'data/records'/(rid+'.json');assert set(bb)=={m['id']for m in read(p)['materials']};bindings['sourceRecordSha256'][rid]=sha(p)
write(dst/'bindings.json',bindings)
products=read(dst/'product-bindings.json');products['recordBindings'].update(read(V/'product-reference-proposal.json')['recordBindings']);write(dst/'product-bindings.json',products)
shutil.copy2(V/'yi2002-protocol.mjs',S/'dist/yi2002-protocol.mjs')
p=S/'dist/protocol-visuals.mjs';t=p.read_text(encoding='utf-8');assert "from './yi2002-protocol.mjs'"not in t
t="import {buildYi2002Scene,createYi2002Art} from './yi2002-protocol.mjs';\n"+t
t=t.replace('const sourceArt=createDantas2002Art','const sourceArt=createYi2002Art(o,r)||createDantas2002Art')
t=t.replace('dantas=buildDantas2002Scene(o,r);','dantas=buildDantas2002Scene(o,r),yi=buildYi2002Scene(o,r);').replace('dantas?.caption||','yi?.caption||dantas?.caption||').replace('||braun||besson||dantas){','||braun||besson||dantas||yi){').replace('=>(gerion||braun||besson||dantas)?','=>(gerion||braun||besson||dantas||yi)?');p.write_text(t,encoding='utf-8')
p=S/'dist/crystal-viewer.mjs';t=p.read_text(encoding='utf-8').replace("'besson2002','dantas2002']","'besson2002','dantas2002','yi2002']")
t=t.replace(" if(r.lineage?.source_group==='dantas2002'&&entryId)"," if(r.lineage?.source_group==='yi2002'&&entryId)host.append(el('p','Specimen diagrams are illustrative. The 800 °C powder is assigned tetragonal La2(MoO4)3 with a small unidentified second phase. No refined atomic coordinates, dopant occupancies or measured unit-cell file are supplied. TEM particle sizes, XRD crystallite size and particle-analyzer distributions retain separate specimen/metric scopes.','guide-notice'));\n if(r.lineage?.source_group==='dantas2002'&&entryId)")
p.write_text(t,encoding='utf-8')
p=S/'scripts/build_atlas.py';t=p.read_text(encoding='utf-8');assert "NAMES['La2(MoO4)3:Yb,Er']"not in t;t=t.replace("NAMES['Pt']='Platinum nanocrystals'","NAMES['Pt']='Platinum nanocrystals'\nNAMES['La2(MoO4)3:Yb,Er']='Ytterbium/erbium-codoped lanthanum molybdate'");p.write_text(t,encoding='utf-8')
# Explicitly classify source structural measurements after canonical authoring.
p=S/'data/measurement-display.json';d=read(p);extra=read(B/'structural-property-additions.json');d['structural_properties']=list(dict.fromkeys(d['structural_properties']+extra));write(p,d)
p=S/'scripts/build_dataset.py';p.write_text(p.read_text(encoding='utf-8').replace("'dataset_version':'0.17.0'","'dataset_version':'0.18.0'"),encoding='utf-8')
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs'))+list((S/'dist').glob('*.html')):
 t=p.read_text(encoding='utf-8');n=t.replace('0.17.0-r1','0.18.0-r1')
 if n!=t:p.write_text(n,encoding='utf-8')
write(B/'integration-manifest.json',{'status':'integrated_pending_build_and_browser','at':datetime.now(timezone.utc).isoformat(),'source_id':'yi2002','records':{r['record_id']:sha(S/'data/records'/(r['record_id']+'.json'))for r in records},'reader_sha256':sha(S/'data/paper-reviews/yi2002.json'),'private_reader_sha256':sha(B/'public-review-proposal/yi2002.json'),'apparatus_sha256':sha(S/'dist/yi2002-protocol.mjs'),'record_promotion_changes':['quality.review_status','quality.review_scope','sources[0].main_status'],'schema_additions':[]})
print('Imported18audited records into existing MatterSyn; build/browser/publication pending.')
