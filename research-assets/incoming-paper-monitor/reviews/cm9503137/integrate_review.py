"""Root-only import into the existing MatterSyn Site after canonical audit passes."""
from pathlib import Path
import json,hashlib,shutil
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
audit=read(B/'canonical-records-audit.json')
assert audit['status'].startswith('passed'),audit['status']
hashes={x['basename']:x['sha256'] for x in audit['records']}
routes={'danek-1996-znse-overgrowth','danek-1996-bare-dot-film','danek-1996-overcoated-dot-film'}
ids=[]
for p in sorted((B/'canonical-drafts').glob('*.json')):
 assert sha(p)==hashes[p.name],p.name
 r=read(p);ids.append(r['record_id']);r['quality']['review_status']='source_reviewed'
 r['quality']['requested_tasks']=['precursor_selection','partial_protocol'] if r['record_id'] in routes else []
 r['quality']['review_scope']='All eight supplied main pages read in full and visually inspected. Independently audited source extraction and canonical chemistry, conditions and sample links. SI not located or verified. General recipes, control studies and characterization cohorts remain distinct; these record IDs are not author-assigned independent batches.'
 r['sources'][0]['main_status']='All eight supplied main pages read and visually inspected; independent source and canonical audits completed'
 write(S/'data/records'/p.name,r)
review=read(B/'public-review-proposal/danek1996.json')
review.update(coverage_status='supplied_main_text_and_visual_review_complete; SI_unverified',independent_audit='Complete supplied-main source review and bounded canonical scientific audit passed. Reader integration is checked separately; matching SI remains unverified.',publication_status='Reviewed contribution prepared for the existing MatterSyn atlas; deployment tracked separately.',source_review_promoted=True,training_note='This source ledger supplies contextual evidence, not additional training experiments. Three general synthesis routes request precursor-selection and partial-protocol views; supporting procedures, comparisons and unassigned outcomes stay separate.')
review['audit_details']['scope']='All supplied-main source and canonical scientific audits completed. Reader validation and deployment have separate private checkpoints. Reference structures, computed molecular models and author hypotheses remain outside measured training labels.'
for entry in review['recipe_inventory']:
 entry['status']='source_reviewed';entry['gaps']=[g for g in entry.get('gaps',[]) if 'canonical' not in g.lower()]
for section in review['reader_sections']:
 for item in section['items']:
  for l in item.get('canonical_links',[]):l['relation']='Reviewed canonical record; source context does not imply a unique physical specimen or full run-to-figure assignment.'
review['remaining_gaps']=[g for g in review['remaining_gaps'] if 'canonical' not in g.lower()]
review['material_evidence_records']={f:ids for f in ['CdSe/ZnSe','CdSe','ZnSe']}
scope='Danek1996: supplied main fully reviewed; SI unverified. Colloidal overcoating and ZnSe-matrix film fabrication are separate methods. Source cohorts and comparison conditions retain their own links; pure-component syntheses are not inferred. The no-CdSe-seed comparison contains ZnSe-precursor products without CdSe; it is contrast evidence, not a CdSe synthesis or CdSe property measurement.'
review['material_evidence_scope_notes']={f:('Component context: ' if f!='CdSe/ZnSe' else '')+scope for f in ['CdSe/ZnSe','CdSe','ZnSe']}
write(S/'data/paper-reviews/danek1996.json',review)
for item in read(B/'crop-assets/manifest.json')['items']:
 p=B/'crop-assets'/item['file'];assert sha(p)==item['sha256'];target=S/'dist/assets/figures/danek1996'/item['file'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
chem=B/'molecular-assets';dst=S/'dist/assets/chemical-registry'
for a in read(chem/'asset-manifest.json')['files']:
 p=chem/a['file'];assert sha(p)==a['sha256']
 if Path(a['file']).parts[0] in ['svg','models','sdf']:
  dest=dst/a['file'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
registry=read(dst/'registry.json');delta=read(chem/'registry-additions.json')['entries'];newids={e['id'] for e in delta};registry['entries']=[e for e in registry['entries'] if e['id'] not in newids]+delta;write(dst/'registry.json',registry)
bindings=read(dst/'bindings.json');newbindings=read(chem/'bindings-additions.json')['recordBindings'];bindings['recordBindings'].update(newbindings)
for rid,bb in newbindings.items():
 p=S/'data/records'/(rid+'.json');assert set(bb)=={m['id'] for m in read(p)['materials']};bindings['sourceRecordSha256'][rid]=sha(p)
write(dst/'bindings.json',bindings)
cr=B/'crystal-reference';dest=S/'dist/assets/crystal-references';ref=read(cr/'registry-entry.json');assert sha(cr/'9016056.cif')==ref['cifSha256'] and sha(cr/'model.json')==ref['modelSha256']
shutil.copy2(cr/'9016056.cif',dest/'9016056.cif');shutil.copy2(cr/'model.json',dest/ref['modelPath'])
registry=read(dest/'registry.json');registry['entries']=[x for x in registry['entries'] if x['id']!=ref['id']]+[ref];write(dest/'registry.json',registry)
shutil.copy2(B/'danek-protocol.mjs',S/'dist/danek-protocol.mjs')
p=S/'data/measurement-display.json';d=read(p);extra=['particle_size','relative_size_standard_deviation','znse_to_cdse_ratio','core_size','overall_znse_to_cdse_ratio','aes_znse_to_cdse_ratio','auger_escape_depth','symmetric_model_shell_thickness','initial_core_size','feed_znse_to_cdse_ratio','model_passivation_layer_count']
d['structural_properties']=list(dict.fromkeys(d['structural_properties']+extra));write(p,d)
shutil.copy2(B/'inventory-proposal/inventory-summary.json',S/'data/inventory-summary.json')
p=S/'scripts/build_atlas.py';t=p.read_text(encoding='utf-8');t=t.replace("NAMES={","NAMES={'CdSe/ZnSe':'Cadmium selenide / zinc selenide · coated dots and composite films',",1) if "'CdSe/ZnSe':" not in t else t;p.write_text(t,encoding='utf-8')
p=S/'scripts/build_dataset.py';p.write_text(p.read_text(encoding='utf-8').replace("'dataset_version':'0.6.0'","'dataset_version':'0.7.0'"),encoding='utf-8')
# Update reader cache keys coherently after the shared renderer change.
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs')):
 text=p.read_text(encoding='utf-8');new=text.replace('0.6.0-r1','0.7.0-r1').replace('0.6.0-r2','0.7.0-r1')
 if text!=new:p.write_text(new,encoding='utf-8')
p=S/'scripts/check_quality.py';text=p.read_text(encoding='utf-8')
if '"cdse-wurtzite-cod-9016056": (' not in text:text=text.replace('CRYSTALS = {','CRYSTALS = {\n    "cdse-wurtzite-cod-9016056": (186, "'+ref['cifSha256']+'", {"Cd": 2, "Se": 2}),')
text=text.replace('Seven independently reviewed crystal references','Eight independently reviewed crystal references');p.write_text(text,encoding='utf-8')
p=S/'dist/crystal-viewer.mjs';text=p.read_text(encoding='utf-8').replace("const colors={O:","const colors={Cd:'#d9af67',Se:'#689db3',O:");p.write_text(text,encoding='utf-8')
print('Imported12 independently audited records, source ledger,13 original assets,63 chemical bindings,21 chemical additions and one reused bulk crystal reference. Reader/build/browser checks and publication remain pending.')
