"""Root-only import of independently audited Yao records into the existing atlas."""
from pathlib import Path
import hashlib,json,shutil
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audit=read(B/'canonical-records-audit.json');assert audit['status'].startswith('passed'),audit['status']
hashes={x['record_id']+'.json':x['sha256']for x in audit.get('record_hashes',audit.get('records',[]))}
drafts=sorted((B/'canonical-drafts').glob('*.json'));assert len(drafts)==11 and set(hashes)=={p.name for p in drafts}
for p in drafts:assert sha(p)==hashes[p.name],p.name
routes={'yao-1998-sample-a','yao-1998-sample-b'};ids=[]
O=B/'inventory-proposal';O.mkdir(exist_ok=True)
if not(O/'base-inventory-summary.json').exists():shutil.copy2(S/'data/inventory-summary.json',O/'base-inventory-summary.json')
for p in drafts:
 r=read(p);ids.append(r['record_id']);r['quality']['review_status']='source_reviewed';r['quality']['requested_tasks']=['precursor_selection','partial_protocol']if r['record_id']in routes else[]
 r['quality']['review_scope']='All seven supplied main pages read in full and visually inspected with independent source and canonical scientific audits. Matching SI not located or verified. Two formulations, upstream host preparation, analytical procedures and contextual observations remain separate. Regional and instrument cohorts do not establish unique physical batches. Salt-concentration and reaction-clock ambiguities remain unresolved.'
 r['sources'][0]['main_status']='All seven supplied main pages read and visually checked; independent source and canonical audits completed'
 write(S/'data/records'/p.name,r)
review=read(B/'public-review-proposal/yao1998.json')
review.update(coverage_status='supplied_main_text_and_visual_review_complete; SI_unverified',independent_audit='All seven supplied main pages and canonical extraction independently audited. Reader and publication gates tracked separately; SI unverified.',publication_status='Reviewed contribution for the existing MatterSyn atlas; deployment tracked separately.',source_review_promoted=True,training_note='Two routes support precursor-selection and partial-protocol tasks, retaining the polymer host and separate electrolyte process materials. Missing conditions remain unknown. Regional TEM sizes, XRD line-broadening sizes and author-model quantities do not become size-conditioned, exact-structure, success or optical-outcome labels.')
for item in review['recipe_inventory']:item['status']='source_reviewed'
review['material_evidence_records']={'CdS':ids,'CdS/polymer':ids}
review['material_evidence_scope_notes']={f:'Two CdS/Chelex100 composite formulations and source-scoped characterization. Resin conditioning and cadmium loading are upstream preparation, not independent CdS syntheses. Measured host sizes, nanocrystal sizes and distribution depths retain distinct scopes. No verified specimen-to-run joins or atomic coordinates.'for f in ['CdS','CdS/polymer']}
write(S/'data/paper-reviews/yao1998.json',review)
for a in read(B/'crop-assets/manifest.json')['assets']:
 p=B/'crop-assets'/a['relative_asset'];assert sha(p)==a['sha256'];dest=S/'dist/assets/figures/yao1998'/a['relative_asset'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
chem=B/'molecular-assets';dst=S/'dist/assets/chemical-registry'
for a in read(chem/'asset-manifest.json')['files']:
 relative=a.get('file',a.get('path'));p=chem/relative;assert sha(p)==a['sha256']
 if Path(relative).parts[0]in ['svg','models','sdf']:
  dest=dst/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
reg=read(dst/'registry.json');delta=read(chem/'registry-additions.json')['entries'];newids={e['id']for e in delta};reg['entries']=[e for e in reg['entries']if e['id']not in newids]+delta
write(dst/'registry.json',reg)
binding_delta=read(chem/'bindings-additions.json');bind=read(dst/'bindings.json');bind['recordBindings'].update(binding_delta['recordBindings']);bind.setdefault('bindingNotes',{}).update(binding_delta.get('bindingNotes',{}))
for rid,bb in binding_delta['recordBindings'].items():
 p=S/'data/records'/(rid+'.json');assert set(bb)=={m['id']for m in read(p)['materials']},rid
 bind['sourceRecordSha256'][rid]=sha(p)
write(dst/'bindings.json',bind)
products=read(dst/'product-bindings.json');products['recordBindings'].update(read(chem/'product-reference-proposal.json')['references']);write(dst/'product-bindings.json',products)
shutil.copy2(B/'yao-protocol.mjs',S/'dist/yao-protocol.mjs')
p=S/'dist/protocol-visuals.mjs';t=p.read_text(encoding='utf-8')
if "from './yao-protocol.mjs'"not in t:
 t="import {buildYaoScene,createYaoArt} from './yao-protocol.mjs';\n"+t
 t=t.replace('const sourceArt=createVeinotArt','const sourceArt=createYaoArt(o,r)||createVeinotArt')
 t=t.replace('veinot=buildVeinotScene(o,r);','veinot=buildVeinotScene(o,r),yao=buildYaoScene(o,r);')
 t=t.replace('veinot?.caption||','yao?.caption||veinot?.caption||')
 t=t.replace('if(danek||dabbousi||veinot){','if(danek||dabbousi||veinot||yao){')
 t=t.replace('duration_threshold/.test(k)','duration_threshold|wavelength|two_theta|eluent_pH|diameter|depth/.test(k)')
p.write_text(t,encoding='utf-8')
p=S/'data/measurement-display.json';d=read(p)
d['structural_properties']=list(dict.fromkeys(d['structural_properties']+['host_polymer_particle_diameter','xrd_two_theta_scan_range','xrd_radiation_wavelength','xrd_two_theta_peak','xrd_line_broadening_mean_size','depth_below_polymer_surface','cds_distribution_layer_terminal_depth','central_region_observation','dispersion_state','local_nanocrystal_diameter','aggregate_size_description','tem_distribution_mean_diameter','lognormal_fit_reported_standard_deviation','histogram_region_depth','tem_distribution_standard_deviation','qualitative_nanocrystal_size_context','optical_ring_depth','dispersion_layer_width_definition','dispersion_layer_width_comparison','optical_layer_width_precision_limit']))
write(p,d)
p=S/'scripts/build_dataset.py';p.write_text(p.read_text(encoding='utf-8').replace("'dataset_version':'0.9.0'","'dataset_version':'0.10.0'"),encoding='utf-8')
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs')):
 t=p.read_text(encoding='utf-8');n=t.replace('0.9.0-r1','0.10.0-r1')
 if n!=t:p.write_text(n,encoding='utf-8')
print('Imported 11 audited records and source assets; build, reader QA and publication remain pending.')
