"""Root-only import after independent canonical audit; retains existing Site identity."""
from pathlib import Path
import json,hashlib,shutil
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audit=read(B/'canonical-records-audit.json');assert audit['status'].startswith('passed'),audit['status']
hashes={x['basename']:x['sha256']for x in audit['records']}
routes={'dabbousi-1997-zns-overgrowth','dabbousi-1997-cds-overgrowth'};ids=[]
for p in sorted((B/'canonical-drafts').glob('*.json')):
 assert sha(p)==hashes[p.name],p.name
 r=read(p);ids.append(r['record_id']);r['quality']['review_status']='source_reviewed';r['quality']['requested_tasks']=['precursor_selection','partial_protocol']if r['record_id']in routes else[]
 r['quality']['review_scope']='All thirteen supplied main pages read in full and visually inspected, with independent source and canonical scientific audits. SI not located or verified. General synthesis routes, analytical procedures, source model parameters and observation cohorts remain separate; records do not assert independent physical batches.'
 r['sources'][0]['main_status']='All thirteen supplied main pages read and visually checked; independent source and canonical audits completed'
 write(S/'data/records'/p.name,r)
review=read(B/'public-review-proposal/dabbousi1997.json')
review.update(coverage_status='supplied_main_text_and_visual_review_complete; SI_unverified',independent_audit='Complete supplied-main source review and bounded canonical scientific audit passed. Reader verification and publication tracked separately; matching SI unverified.',publication_status='Reviewed contribution for the existing MatterSyn atlas; deployment tracked separately.',source_review_promoted=True,training_note='Two source-reviewed overgrowth routes request precursor-selection and partial-protocol views. Six core-size/temperature choices are not six complete experiments. Supporting procedures, optical cohorts, fitted models and conflicting dimensions stay outside new measured outcome labels.')
for item in review['recipe_inventory']:item['status']='source_reviewed'
review['remaining_gaps']=[g for g in review['remaining_gaps']if not any(w in str(g).lower()for w in ['canonical draft','audit pending','integration pending'])]
cds=[f'dabbousi-1997-{k}'for k in ['cds-overgrowth','cds-optical-comparison','cdse-seed-preparation','optical-characterization']]
zns=[i for i in ids if i not in ['dabbousi-1997-cds-overgrowth','dabbousi-1997-cds-optical-comparison']]
review['material_evidence_records']={'CdSe/ZnS':zns,'ZnS':zns,'CdSe/CdS':cds,'CdS':cds,'CdSe':ids}
review['material_evidence_scope_notes']={f:'Dabbousi1997 supplied-main evidence; SI unverified. ZnS and CdS overgrowth are distinct source procedures. Component pages retain the full composite and sample context; neither an isolated shell-material synthesis nor an exact experimental atomic structure is implied.'for f in review['material_evidence_records']}
write(S/'data/paper-reviews/dabbousi1997.json',review)
for a in read(B/'crop-assets/manifest.json')['assets']:
 p=B/'crop-assets'/a['relative_asset'];assert sha(p)==a['sha256'];t=S/'dist/assets/figures/dabbousi1997'/a['relative_asset'];t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,t)
chem=B/'molecular-assets';dst=S/'dist/assets/chemical-registry'
for a in read(chem/'asset-manifest.json')['files']:
 p=chem/a['file'];assert sha(p)==a['sha256']
 if Path(a['file']).parts[0]in ['svg','models','sdf']:
  target=dst/a['file'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
reg=read(dst/'registry.json');delta=read(chem/'registry-additions.json')['entries'];newids={e['id']for e in delta};reg['entries']=[e for e in reg['entries']if e['id']not in newids]+delta;write(dst/'registry.json',reg)
bind=read(dst/'bindings.json');binding_delta=read(chem/'bindings-additions.json');new=binding_delta['recordBindings'];bind['recordBindings'].update(new)
bind.setdefault('bindingNotes',{}).update(binding_delta.get('bindingNotes',{}))
for rid,bb in new.items():
 p=S/'data/records'/(rid+'.json');assert set(bb)=={m['id']for m in read(p)['materials']};bind['sourceRecordSha256'][rid]=sha(p)
write(dst/'bindings.json',bind)
# Reuse a pure bulk CdSe reference. Broaden its explanatory scope without adding atoms.
cr=S/'dist/assets/crystal-references';registry=read(cr/'registry.json');ref=next(e for e in registry['entries']if e['id']=='cdse-wurtzite-cod-9016056')
ref['record_ids']=list(dict.fromkeys(ref['record_ids']+['dabbousi-1997-zns-overgrowth','dabbousi-1997-cds-overgrowth','dabbousi-1997-coverage-series']))
ref['description']='Independent COD9016056 bulk CdSe comparison. Not a measured nanocrystal, shell, interface or film structure.'
ref['scope']='A pure bulk wurtzite CdSe reference for core comparison. Danek Figure3 and Dabbousi Figure13 include wurtzite comparisons; this model does not reconstruct either experimental overlayer or interface. No ZnS, CdS or ZnSe shell atoms are added.'
model=read(cr/ref['modelPath']);model['notes']=[n for n in model['notes']if not n.startswith('Danek Figure3')]+['Independent bulk CdSe reference only; no experimental shell, nanocrystal interface or sample coordinates are asserted.']
write(cr/ref['modelPath'],model);ref['modelSha256']=sha(cr/ref['modelPath']);write(cr/'registry.json',registry)
shutil.copy2(B/'dabbousi-protocol.mjs',S/'dist/dabbousi-protocol.mjs')
p=S/'data/measurement-display.json';m=read(p);props=['major_axis_length','relative_major_axis_distribution','tem_derived_shell_coverage','saxs_model_size','saxs_model_relative_size_distribution','saxs_model_zn_to_cd_ratio','waxs_model_zn_to_cd_ratio','zn_to_cd_atomic_ratio','se_to_cd_atomic_ratio','porod_model_mean_radius','porod_model_polydispersity','source_reported_zn_to_cd_ratio','source_reported_core_radius','shell_thickness_at_reported_shift']
m['structural_properties']=list(dict.fromkeys(m['structural_properties']+props));write(p,m)
p=S/'scripts/build_atlas.py';t=p.read_text(encoding='utf-8')
if "'CdSe/ZnS':"not in t:t=t.replace('NAMES={',"NAMES={'CdSe/ZnS':'Cadmium selenide / zinc sulfide core/shell','ZnS':'Zinc sulfide · shell-component context',",1)
p.write_text(t,encoding='utf-8')
p=S/'scripts/build_dataset.py';p.write_text(p.read_text(encoding='utf-8').replace("'dataset_version':'0.7.0'","'dataset_version':'0.8.0'"),encoding='utf-8')
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs')):
 t=p.read_text(encoding='utf-8');newt=t.replace('0.7.0-r2','0.8.0-r1').replace('0.7.0-r1','0.8.0-r1')
 if newt!=t:p.write_text(newt,encoding='utf-8')
print('Imported independently audited Dabbousi records, complete source ledger and original assets. Reader builds, inventory reconciliation, browser checks and publication remain pending.')
