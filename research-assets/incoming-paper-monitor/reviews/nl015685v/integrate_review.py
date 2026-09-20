"""Root-only import of the independently audited Besson2002 contribution."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';V=B/'visuals'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
drafts=sorted((B/'canonical-drafts').glob('*.json'));assert len(drafts)==12
a=read(B/'canonical-records-audit.json');assert a['status'].startswith('passed')
assert {p.stem for p in drafts}==set(a['record_hashes'])
for p in drafts:assert sha(p)==a['record_hashes'][p.stem]
for name in ['reader-source-audit.json','molecular-source-audit.json','visual-source-audit.json','bindings-source-audit.json']:assert read(B/name)['status'].startswith('passed'),name
assert read(B/'reader-source-audit.json')['asset_count']==10
assert sha(B/'reader-assets/crop-manifest.json')==read(B/'reader-source-audit.json')['crop_manifest_sha256']
assert sha(B/'public-review-proposal/besson2002.json')==read(B/'reader-source-audit.json')['reader_sha256']
assert read(B/'public-review-proposal/proposal-validation.json')['status'].startswith('passed')
assert sha(V/'registry-additions.json')==read(B/'molecular-source-audit.json')['registry_sha256']
assert sha(V/'besson2002-protocol.mjs')==read(B/'visual-source-audit.json')['module_sha256']
assert read(V/'bindings-additions.json')['sourceRecordSha256']=={p.stem:sha(p)for p in drafts}
O=B/'inventory-proposal';O.mkdir(exist_ok=True)
if not(O/'base-inventory-summary.json').exists():shutil.copy2(S/'data/inventory-summary.json',O/'base-inventory-summary.json')
records=[]
for p in drafts:
 r=read(p);r['quality']['review_status']='source_reviewed';r['quality']['review_scope']='All six supplied main pages read and visually inspected, with independent source, canonical, molecular, apparatus and reader audits. Mesoporous silica preparation, repeated CdS pore loading, optical properties and microscopy retain separate host and nanoparticle structure scopes. Copolymer identity, several operation conditions and the Figure4 stage-assignment conflict remain unresolved. Matching SI not located or verified; cited upstream preparations and theory are not independently reviewed here.'
 r['sources'][0]['main_status']='All six supplied main pages text and visually reviewed; independent source and canonical audits completed. Matching local SI not located or verified.'
 write(S/'data/records'/p.name,r);records.append(r)
review=read(B/'public-review-proposal/besson2002.json')
review['remaining_gaps']=[g for g in review['remaining_gaps'] if g not in ['Independent source-to-reader, crop and canonical-link audits are pending.','Independent audits pending.']]
for category in ['figures','tables','equations','schemes','source_notes']:
 for item in review.get(category,[]):
  if item.get('public_asset'):item['reviewed']=True
review.update(coverage_status='supplied_main_text_and_visual_review_complete_si_unverified',source_review_promoted=True,independent_audit='All six supplied main pages, canonical extraction, reader coverage, original crops, molecular references and apparatus scenes independently audited. Matching SI remains unlocated or unverified; publication tracked separately.',publication_status='Reviewed contribution for the existing MatterSyn atlas; deployment tracked separately.',training_note='Repeated impregnation and H2S exposure remain a loading trajectory, not independent synthesis batches. Copolymer details, PL substrate identity and caption conflict remain explicit. Mesostructure symmetry and image Fourier power spectra do not become atomic CIF or SAED labels.')
for item in review['recipe_inventory']:item['status']='source_reviewed'
assert review['review_scope']=='supplied_main_only_si_unverified'
write(S/'data/paper-reviews/besson2002.json',review)
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
shutil.copy2(V/'besson2002-protocol.mjs',S/'dist/besson2002-protocol.mjs')
p=S/'dist/protocol-visuals.mjs';t=p.read_text(encoding='utf-8');assert "from './besson2002-protocol.mjs'" not in t
t="import {buildBesson2002Scene,createBesson2002Art} from './besson2002-protocol.mjs';\n"+t
t=t.replace('const sourceArt=createBraun2001Art','const sourceArt=createBesson2002Art(o,r)||createBraun2001Art')
t=t.replace('braun=buildBraun2001Scene(o,r);','braun=buildBraun2001Scene(o,r),besson=buildBesson2002Scene(o,r);')
t=t.replace('braun?.caption||','besson?.caption||braun?.caption||')
t=t.replace('||gerion||braun){','||gerion||braun||besson){').replace('=>(gerion||braun)?','=>(gerion||braun||besson)?')
p.write_text(t,encoding='utf-8')
p=S/'dist/crystal-viewer.mjs';t=p.read_text(encoding='utf-8');t=t.replace("'gerion2001','braun2001']","'gerion2001','braun2001','besson2002']")
t=t.replace(" if(r.lineage?.source_group==='braun2001'&&entryId)"," if(r.lineage?.source_group==='besson2002'&&entryId)host.append(el('p','Pore and particle illustrations describe the mesoscopic arrangement. The original HRTEM supports some blende-type CdS 111 fringes; P6₃/mmc and nanometre lattice dimensions describe the mesostructure. Figure 3d is an image Fourier power spectrum, not SAED. No measured atomic coordinates or source CIF are supplied.','guide-notice'));\n if(r.lineage?.source_group==='braun2001'&&entryId)")
p.write_text(t,encoding='utf-8')
p=S/'scripts/build_atlas.py';t=p.read_text(encoding='utf-8');t=t.replace("NAMES['Pt']='Platinum nanocrystals'","NAMES['Pt']='Platinum nanocrystals'\nNAMES['CdS/SiO2']='CdS nanocrystals in mesoporous silica'\nNAMES['SiO2']='Mesoporous silica films'");p.write_text(t,encoding='utf-8')
p=S/'data/measurement-display.json';d=read(p);props={m['property']for r in records for m in r['measurements']if any(k in m['property']for k in ['diameter','size','thickness','shape','morphology','lattice','mesostructure','mesoscopic','space_group','pore','filling','contrast','fringes','orientation','phase'])}
props.update({'0002_intensity_evolution','0002_intensity_relative_to_calcined_host','0002_peak_shift','0002_peak_width_evolution','local_atomic_structure_assignment','atomic_assignment_reference','cadmium_depth_distribution','cds_volume_fraction','figure2_displayed_two_theta_range','figure2_intensity_display_multiplier','figure2_trace_labels','figure3a_scale_bar_length','figure3b_scale_bar_length','figure3c_scale_bar_length','figure3d_index_labels','image_power_definition','structure_scale_distinction'})
props.discard('author_weak_confinement_size_threshold');d['structural_properties']=list(dict.fromkeys(d['structural_properties']+sorted(props)));write(p,d)
p=S/'scripts/build_dataset.py';p.write_text(p.read_text(encoding='utf-8').replace("'dataset_version':'0.15.0'","'dataset_version':'0.16.0'"),encoding='utf-8')
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs'))+list((S/'dist').glob('*.html')):
 t=p.read_text(encoding='utf-8');n=t.replace('0.15.0-r1','0.16.0-r1')
 if p.suffix=='.html':n=n.replace('material-hub.mjs?v=0.12.0-r1','material-hub.mjs?v=0.15.0-r1')
 if n!=t:p.write_text(n,encoding='utf-8')
write(B/'integration-manifest.json',{'status':'integrated_pending_build_and_browser','at':datetime.now(timezone.utc).isoformat(),'source_id':'besson2002','records':{r['record_id']:sha(S/'data/records'/(r['record_id']+'.json'))for r in records},'reader_sha256':sha(S/'data/paper-reviews/besson2002.json'),'private_reader_sha256':sha(B/'public-review-proposal/besson2002.json'),'apparatus_sha256':sha(S/'dist/besson2002-protocol.mjs'),'record_promotion_changes':['quality.review_status','quality.review_scope','sources[0].main_status'],'schema_additions':[]})
print('Imported 12 audited records into the existing MatterSyn Site; build, browser checks and publication remain pending.')


