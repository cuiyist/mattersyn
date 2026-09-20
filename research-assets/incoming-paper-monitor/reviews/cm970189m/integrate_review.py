"""Root-only guarded import into the existing MatterSyn Site."""
from pathlib import Path
import hashlib,json,shutil
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audit=read(B/'canonical-records-audit.json');assert audit['status'].startswith('passed'),audit['status']
hashes={x['record_id']+'.json':x['sha256']for x in audit['record_hashes']}
routes={'veinot-1997-qdoh'}|{'veinot-1997-ester-2'+x for x in'abcde'}
ids=[]
O=B/'inventory-proposal';O.mkdir(exist_ok=True)
if not(O/'base-inventory-summary.json').exists():shutil.copy2(S/'data/inventory-summary.json',O/'base-inventory-summary.json')
for p in sorted((B/'canonical-drafts').glob('*.json')):
 assert sha(p)==hashes[p.name],p.name
 r=read(p);ids.append(r['record_id']);r['quality']['review_status']='source_reviewed';r['quality']['requested_tasks']=['precursor_selection','partial_protocol']if r['record_id']in routes else[]
 r['quality']['review_scope']='All six supplied main pages read in full and visually inspected, with independent source and canonical scientific audits. SI not located or verified. Named surface-functionalization variants, molecular precursor procedures, controls and compound-level analytical observations remain separate. Characterization compound labels do not establish unique physical batches or individual specimen-to-run joins.'
 r['sources'][0]['main_status']='All six supplied main pages read and visually checked; independent source and canonical audits completed'
 write(S/'data/records'/p.name,r)
review=read(B/'public-review-proposal/veinot1997.json')
review.update(coverage_status='supplied_main_text_and_visual_review_complete; SI_unverified',independent_audit='All six supplied main pages and canonical extraction independently audited. Reader and publication gates tracked separately; SI unverified.',publication_status='Reviewed contribution for the existing MatterSyn atlas; deployment tracked separately.',source_review_promoted=True,training_note='Six routes support precursor-selection and partial-protocol tasks. Surface-functionalization tasks retain the QDOH seed, acyl reagent and intended surface. Inherited common conditions remain labeled; molecular precursor products retain their actual organic formulas. Qualitative results, optical model sizes and compound-level spectroscopy do not become calibrated success, exact-structure or size-conditioned labels.')
for item in review['recipe_inventory']:item['status']='source_reviewed'
review['material_evidence_records']={'CdS':ids}
review['material_evidence_scope_notes']={'CdS':'Veinot1997 phenolic CdS and five surface esters. Supporting organic-precursor preparations are linked as upstream chemistry, not CdS products. Measurements identify compound classes; specimen/batch joins remain unresolved. Exact CdS phase and measured coordinates unreported.'}
write(S/'data/paper-reviews/veinot1997.json',review)
for a in read(B/'crop-assets/manifest.json')['assets']:
 p=B/'crop-assets'/a['relative_asset'];assert sha(p)==a['sha256'];dest=S/'dist/assets/figures/veinot1997'/a['relative_asset'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
chem=B/'molecular-assets';dst=S/'dist/assets/chemical-registry'
for a in read(chem/'asset-manifest.json')['files']:
 relative=a.get('file',a.get('path'));p=chem/relative;assert sha(p)==a['sha256']
 if Path(relative).parts[0]in['svg','models','sdf']:
  dest=dst/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
reg=read(dst/'registry.json');delta=read(chem/'registry-additions.json')['entries'];newids={e['id']for e in delta};reg['entries']=[e for e in reg['entries']if e['id']not in newids]+delta
for update in read(chem/'registry-neutralizations.json')['updates']:
 entry=next(x for x in reg['entries']if x['id']==update['id']);entry['caption']=update['caption'];entry['limitations']=update['limitations']
write(dst/'registry.json',reg)
binding_delta=read(chem/'bindings-additions.json');bind=read(dst/'bindings.json');bind['recordBindings'].update(binding_delta['recordBindings']);bind.setdefault('bindingNotes',{}).update(binding_delta.get('bindingNotes',{}))
for rid,bb in binding_delta['recordBindings'].items():
 p=S/'data/records'/(rid+'.json');assert set(bb)=={m['id']for m in read(p)['materials']},rid
 bind['sourceRecordSha256'][rid]=sha(p)
write(dst/'bindings.json',bind)
product_bindings=read(dst/'product-bindings.json')if(dst/'product-bindings.json').exists()else{'scope':'Illustrative product identity references only; never measured sample coordinates or training inputs.','recordBindings':{}}
product_bindings['recordBindings'].update(read(chem/'product-reference-proposal.json')['references']);write(dst/'product-bindings.json',product_bindings)
shutil.copy2(B/'veinot-protocol.mjs',S/'dist/veinot-protocol.mjs')
p=S/'dist/protocol-visuals.mjs';t=p.read_text(encoding='utf-8')
if 'from \'./veinot-protocol.mjs\''not in t:
 t="import {buildVeinotScene,createVeinotArt} from './veinot-protocol.mjs';\n"+t
 t=t.replace('const sourceArt=createDabbousiArt','const sourceArt=createVeinotArt(o,r)||createDabbousiArt')
 t=t.replace('dabbousi=buildDabbousiScene(o,r);','dabbousi=buildDabbousiScene(o,r),veinot=buildVeinotScene(o,r);')
 t=t.replace('dabbousi?.caption||','veinot?.caption||dabbousi?.caption||')
 t=t.replace('if(danek||dabbousi){','if(danek||dabbousi||veinot){')
 t=t.replace('reported_distance/.test(k)','reported_distance|frequency|mesh|drops|line_density|sieve_pore|remaining_volume|duration_threshold/.test(k)')
p.write_text(t,encoding='utf-8')
p=S/'data/measurement-display.json';d=read(p)
d['structural_properties']=list(dict.fromkeys(d['structural_properties']+['tem_mean_cluster_diameter','reported_tem_diameter_uncertainty','tight_binding_derived_cluster_diameter','source_described_aggregate_dimension','figure6_scale_bar','estimated_caps_per_cluster','estimated_surface_area_per_cap','model_sphere_surface_area','model_cluster_diameter','assumed_core_specific_gravity','author_estimated_thiol_contribution_to_sulfur']))
write(p,d)
p=S/'scripts/build_dataset.py';p.write_text(p.read_text(encoding='utf-8').replace("'dataset_version':'0.8.0'","'dataset_version':'0.9.0'"),encoding='utf-8')
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs')):
 t=p.read_text(encoding='utf-8');n=t.replace('0.8.0-r1','0.9.0-r1')
 if n!=t:p.write_text(n,encoding='utf-8')
print('Imported21 audited records and source assets; build, rendered reader audit, browser QA and publication remain pending.')
