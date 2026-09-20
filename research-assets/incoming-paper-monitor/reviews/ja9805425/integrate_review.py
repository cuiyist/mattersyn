"""Root-only import of audited Peng main/SI data into the existing MatterSyn Site."""
from pathlib import Path
import json,hashlib,shutil
B=Path(__file__).resolve().parent; S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
a=read(B/'canonical-records-audit.json');assert a['status']=='passed'
hashes={x['file']:x['sha256']for x in a['records']}
drafts=sorted((B/'canonical-drafts').glob('*.json'));assert len(drafts)==12 and set(hashes)=={p.name for p in drafts}
for p in drafts:assert sha(p)==hashes[p.name],p.name
reader_audit=read(B/'reader-source-audit.json');assert reader_audit['status'].startswith('passed')
O=B/'inventory-proposal';O.mkdir(exist_ok=True)
if not(O/'base-inventory-summary.json').exists():shutil.copy2(S/'data/inventory-summary.json',O/'base-inventory-summary.json')
records=[]
for p in drafts:
 r=read(p);r['quality']['review_status']='source_reviewed'
 r['quality']['review_scope']='All two main pages and four matched SI PDF pages read and visually inspected, with independent source and canonical audits. Strict injection bounds, inferred CdSe growth temperature, sequential feeds, aliquot preparation, calibration rows and the unlinked 8.5 nm TEM specimen remain distinct. No measured phase, atomic coordinates or independent calibration synthesis runs inferred.'
 r['sources'][0]['main_status']='All two supplied main pages text and visually reviewed; independent source and canonical audits completed.'
 r['sources'][0]['si_status']='Matched four-page supplied SI: exact DOI cover and three scientific pages fully text/visually reviewed with independent audit.'
 write(S/'data/records'/p.name,r);records.append(r)
review=read(B/'public-review-proposal/peng1998.json')
assert sha(B/'public-review-proposal/peng1998.json')=='7f4cffe18f233e41d4dfe8ff6c52933f38f1d068725928f839a4f8d79ac37e78'
review['remaining_gaps']=[g for g in review['remaining_gaps']if g!='Independent canonical-link and source-to-reader audits remain pending for this private proposal.']
review['corpus_paper_id']='paper-28c103b8279a9218e414'
review['corpus_document_id']='doc-9b8d7c481763aff3b48d'
for d in review['documents']:
 d['corpus_document_id']='doc-9b8d7c481763aff3b48d' if d['role']=='main' else 'doc-4d3b8bea60dbbf31e15e'
review.update(coverage_status='supplied_main_and_matched_si_text_and_visual_review_complete',source_review_promoted=True,independent_audit='All six supplied PDF pages and canonical extraction independently audited. Reader and publication checks tracked separately.',publication_status='Reviewed contribution for the existing MatterSyn atlas; deployment tracked separately.',training_note='Two source-linked hot-injection routes support precursor selection and partial protocol tasks. Sequential feed additions are correlated stages, not independent experiments. The 36 calibration rows, source-derived kinetic observations and unlinked TEM specimen do not create size-conditioned, exact-structure, success or optical-outcome labels.')
for item in review['recipe_inventory']:item['status']='source_reviewed'
review['material_evidence_scope_notes']={}
for f in ['CdSe','InAs']:
 review.setdefault('material_evidence_records',{})[f]=[r['record_id']for r in records if r['material']['formula']in [f,'CdSe/InAs']]
 review.setdefault('material_evidence_scope_notes',{})[f]='Material-specific synthesis and analysis with shared author-model context. Calibration rows are prior sizing references, not newly linked reaction outcomes. The Figure 3 TEM specimen remains separately scoped; no physical batch joins or measured phase are invented.'
write(S/'data/paper-reviews/peng1998.json',review)
for a in read(B/'reader-assets/crop-manifest.json')['assets']:
 p=B/'reader-assets'/a['relative_asset'];assert sha(p)==a['sha256']
 dest=S/'dist'/a['public_asset'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
V=B/'visuals';dst=S/'dist/assets/chemical-registry'
for a in read(V/'asset-manifest.json')['files']:
 p=V/a['path'];assert sha(p)==a['sha256'];dest=dst/a['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
registry=read(dst/'registry.json');entries=read(V/'registry-additions.json')['entries'];newids={e['id']for e in entries}
registry['entries']=[e for e in registry['entries']if e['id']not in newids]+entries;write(dst/'registry.json',registry)
binding=read(dst/'bindings.json');delta=read(V/'bindings-additions.json')
binding['recordBindings'].update(delta['recordBindings']);binding.setdefault('bindingNotes',{}).update(delta.get('bindingNotes',{}))
for rid,bb in delta['recordBindings'].items():
 p=S/'data/records'/(rid+'.json');assert set(bb)=={m['id']for m in read(p)['materials']};binding['sourceRecordSha256'][rid]=sha(p)
write(dst/'bindings.json',binding)
products=read(dst/'product-bindings.json');products['recordBindings'].update(read(V/'product-reference-proposal.json')['recordBindings']);write(dst/'product-bindings.json',products)
shutil.copy2(V/'peng1998-protocol.mjs',S/'dist/peng1998-protocol.mjs')
p=S/'dist/protocol-visuals.mjs';t=p.read_text(encoding='utf-8')
if "from './peng1998-protocol.mjs'" not in t:
 t="import {buildPeng1998Scene,createPeng1998Art} from './peng1998-protocol.mjs';\n"+t
 t=t.replace('const sourceArt=createStigerArt','const sourceArt=createPeng1998Art(o,r)||createStigerArt')
 t=t.replace('stiger=buildStigerScene(o,r);','stiger=buildStigerScene(o,r),peng=buildPeng1998Scene(o,r);')
 t=t.replace('stiger?.caption||','peng?.caption||stiger?.caption||')
 t=t.replace('if(danek||dabbousi||veinot||yao||stiger){','if(danek||dabbousi||veinot||yao||stiger||peng){')
p.write_text(t,encoding='utf-8')
p=S/'dist/crystal-viewer.mjs';t=p.read_text(encoding='utf-8')
t=t.replace("['veinot1997','yao1998','stiger1999']","['veinot1997','yao1998','stiger1999','peng1998']")
t=t.replace("r.lineage?.source_group==='stiger1999'?'Supported nanocrystal structure':r.lineage?.source_group==='stiger1999'?'Supported nanocrystal structure':","r.lineage?.source_group==='stiger1999'?'Supported nanocrystal structure':r.lineage?.source_group==='peng1998'?'Material identity':")
t=t.replace("['yao1998','stiger1999'].includes","['yao1998','stiger1999','peng1998'].includes")
if 'No measured phase or atomic coordinates' not in t:
 t=t.replace(" if(r.lineage?.source_group==='stiger1999')", " if(r.lineage?.source_group==='peng1998'&&entryId)host.append(el('p','No measured phase or atomic coordinates are supplied for these specimens. Identity cards do not reconstruct a crystal lattice. The 8.5 nm CdSe TEM specimen and the optical calibration tables retain separate source contexts; no sample CIF is inferred.','guide-notice'));\n if(r.lineage?.source_group==='stiger1999')")
p.write_text(t,encoding='utf-8')
p=S/'scripts/build_atlas.py';t=p.read_text(encoding='utf-8')
if "NAMES['InAs']"not in t:t=t.replace("NAMES['Ag/Si']","NAMES['InAs']='Indium arsenide'\nNAMES['Ag/Si']")
p.write_text(t,encoding='utf-8')
p=S/'data/measurement-display.json';d=read(p);d['structural_properties']=list(dict.fromkeys(d['structural_properties']+['optically_estimated_mean_diameter','calibration_tem_size','image_scale_bar']));write(p,d)
p=S/'scripts/build_dataset.py';p.write_text(p.read_text(encoding='utf-8').replace("'dataset_version':'0.11.0'","'dataset_version':'0.12.0'"),encoding='utf-8')
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs')):
 t=p.read_text(encoding='utf-8');n=t.replace('0.11.0-r1','0.12.0-r1')
 if n!=t:p.write_text(n,encoding='utf-8')
print('Imported 12 independently audited Peng records and source assets; build, browser QA and publication remain pending.')
