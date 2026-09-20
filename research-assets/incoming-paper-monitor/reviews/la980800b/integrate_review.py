"""Root-only import of independently audited Stiger records into the existing Site."""
from pathlib import Path
import hashlib,json,shutil
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audit=read(B/'canonical-records-audit.json');assert audit['status'].startswith('passed'),audit['status']
hashes={x['record_id']+'.json':x['sha256']for x in audit.get('record_hashes',audit.get('records',[]))}
drafts=sorted((B/'canonical-drafts').glob('*.json'));assert len(drafts)==8 and set(hashes)=={p.name for p in drafts}
for p in drafts:assert sha(p)==hashes[p.name],p.name
ids=[];O=B/'inventory-proposal';O.mkdir(exist_ok=True)
if not(O/'base-inventory-summary.json').exists():shutil.copy2(S/'data/inventory-summary.json',O/'base-inventory-summary.json')
for p in drafts:
 r=read(p);ids.append(r['record_id']);r['quality']['review_status']='source_reviewed';r['quality']['requested_tasks']=['precursor_selection','partial_protocol']if r['record_id']=='stiger-1999-electrodeposition'else[]
 r['quality']['review_scope']='All nine supplied main pages read in full and visually inspected, with independent source and canonical audits. Matching SI not located or verified. Preparation, electrochemical comparisons, controls, AFM and transferred TEM/SAED cohorts retain their separate scopes. Source charge units, CV concentrations, captions and nucleation-rate units remain unresolved; no measured atomic coordinates or exact physical batch joins inferred.'
 r['sources'][0]['main_status']='All nine supplied main pages read and visually checked; independent source and canonical audits completed'
 write(S/'data/records'/p.name,r)
review=read(B/'public-review-proposal/stiger1999.json')
review.update(coverage_status='supplied_main_text_and_visual_review_complete; SI_unverified',independent_audit='All nine supplied main pages and canonical extraction independently audited. Reader and publication gates tracked separately; SI unverified.',publication_status='Reviewed contribution for the existing MatterSyn atlas; deployment tracked separately.',source_review_promoted=True,training_note='One pulsed-electrodeposition protocol supports precursor selection and partial protocol tasks. Its source-specific pulse options and measurement cohorts do not establish independent batch identities or an interpolated size recipe. Controls, current transients, contradictory charge units, author models and unlinked TEM/AFM results are excluded from exact-structure, size-conditioned, success and optical-outcome labels.')
for item in review['recipe_inventory']:item['status']='source_reviewed'
review['material_evidence_records']={f:ids for f in ['Ag/Si','Ag','Si']}
review['material_evidence_scope_notes']={f:'One Ag-on-Si synthesis protocol plus source-scoped analytical procedures, bare-Si controls and contextual observations. Component pages refer to the supported product, not a separately isolated component synthesis. Control and model contexts are not measured Ag/Si specimens; source concentrations and figure/caption discrepancies remain explicit.'for f in ['Ag/Si','Ag','Si']}
write(S/'data/paper-reviews/stiger1999.json',review)
for a in read(B/'crop-assets/manifest.json')['assets']:
 p=B/'crop-assets'/a['relative_asset'];assert sha(p)==a['sha256'];dest=S/'dist/assets/figures/stiger1999'/a['relative_asset'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
chem=B/'molecular-assets';dst=S/'dist/assets/chemical-registry'
for a in read(chem/'asset-manifest.json')['files']:
 relative=a.get('file',a.get('path'));p=chem/relative;assert sha(p)==a['sha256']
 if Path(relative).parts[0]in ['svg','models','sdf']:
  dest=dst/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
reg=read(dst/'registry.json');delta=read(chem/'registry-additions.json')['entries'];newids={e['id']for e in delta};reg['entries']=[e for e in reg['entries']if e['id']not in newids]+delta
for update in read(chem/'registry-neutralizations.json')['updates']:
 entry=next(e for e in reg['entries']if e['id']==update['id'])
 for field,expected in update['expectedAssetHashes'].items():assert sha(dst/entry[field])==expected
 entry['caption']=update['caption'];entry['limitations']=update['limitations']
write(dst/'registry.json',reg)
binding_delta=read(chem/'bindings-additions.json');bind=read(dst/'bindings.json');bind['recordBindings'].update(binding_delta['recordBindings']);bind.setdefault('bindingNotes',{}).update(binding_delta.get('bindingNotes',{}))
for rid,bb in binding_delta['recordBindings'].items():
 p=S/'data/records'/(rid+'.json');assert set(bb)=={m['id']for m in read(p)['materials']},rid
 bind['sourceRecordSha256'][rid]=sha(p)
write(dst/'bindings.json',bind)
products=read(dst/'product-bindings.json');products['recordBindings'].update(read(chem/'product-reference-proposal.json')['references']);write(dst/'product-bindings.json',products)
shutil.copy2(B/'stiger-protocol.mjs',S/'dist/stiger-protocol.mjs')
p=S/'dist/protocol-visuals.mjs';t=p.read_text(encoding='utf-8')
if "from './stiger-protocol.mjs'"not in t:
 t="import {buildStigerScene,createStigerArt} from './stiger-protocol.mjs';\n"+t
 t=t.replace('const sourceArt=createYaoArt','const sourceArt=createStigerArt(o,r)||createYaoArt')
 t=t.replace('yao=buildYaoScene(o,r);','yao=buildYaoScene(o,r),stiger=buildStigerScene(o,r);')
 t=t.replace('yao?.caption||','stiger?.caption||yao?.caption||')
 t=t.replace('if(danek||dabbousi||veinot||yao){','if(danek||dabbousi||veinot||yao||stiger){')
 t=t.replace('wavelength|two_theta|','potential|electrode_area|camera_length|aperture|scan_width|scan_height|fields_per_sample|wavelength|two_theta|')
p.write_text(t,encoding='utf-8')
p=S/'dist/crystal-viewer.mjs';t=p.read_text(encoding='utf-8').replace("['veinot1997','yao1998']","['veinot1997','yao1998','stiger1999']")
t=t.replace("r.lineage?.source_group==='yao1998'?'Polymer and composite structure'","r.lineage?.source_group==='stiger1999'?'Supported nanocrystal structure':r.lineage?.source_group==='yao1998'?'Polymer and composite structure'")
t=t.replace("r.lineage?.source_group==='yao1998'?'Enlarge product representation ↗'","['yao1998','stiger1999'].includes(r.lineage?.source_group)?'Enlarge product representation ↗'")
anchor=" if(r.lineage?.source_group==='veinot1997'"
if 'No refined Ag/Si interface'not in t:t=t.replace(anchor," if(r.lineage?.source_group==='stiger1999')host.append(el('p','The paper assigns FCC silver using the original SAED pattern and tabulated spacings. No refined Ag/Si interface or measured atomic coordinates are supplied. A verified local Ag crystal reference is unavailable; no sample CIF or atomistic interface is invented. Product diagrams are schematic, and bare-Si controls retain their own identity.','guide-notice'));\n"+anchor)
p.write_text(t,encoding='utf-8')
p=S/'scripts/build_atlas.py';t=p.read_text(encoding='utf-8')
if "NAMES['Ag/Si']"not in t:t=t.replace("NAMES['CdS/polymer']", "NAMES['Ag/Si']='Silver nanocrystals on silicon'\nNAMES['Ag']='Silver · supported nanocrystal component'\nNAMES['CdS/polymer']")
p.write_text(t,encoding='utf-8')
p=S/'data/measurement-display.json';d=read(p)
structural=[row['property']for row in read(B/'characterization-draft.json')['measurement_rows']if any(k in row['property']for k in ['height','diameter','roughness','spacing','nucleation_density','particle_density','fcc','step','morphology','coverage','diffraction','scan_area','count'])]
d['structural_properties']=list(dict.fromkeys(d['structural_properties']+structural));write(p,d)
p=S/'scripts/build_dataset.py';p.write_text(p.read_text(encoding='utf-8').replace("'dataset_version':'0.10.0'","'dataset_version':'0.11.0'"),encoding='utf-8')
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs')):
 t=p.read_text(encoding='utf-8');n=t.replace('0.10.0-r1','0.11.0-r1')
 if n!=t:p.write_text(n,encoding='utf-8')
print('Imported8 audited Stiger records and source assets; build, reader QA and publication remain pending.')
