"""Root-only import of the independently reviewed Heath contribution."""
from pathlib import Path
import json,hashlib,shutil,sys
B=Path(__file__).resolve().parent
S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

manifest=read(B/'source-manifest.json')
for p in manifest['pages']:
    p.update(text_reviewed=True,visual_reviewed=True,reviewed_text_file=f"plain-page-{p['pdf_page']}.txt",render_file=f"main-{p['pdf_page']}.png")
manifest['review_scope']='Root text and visual reading of all six supplied main pages; independent full-main audit in source-audit.json. Matching SI not located or verified in source-identity.json.'
write(B/'source-manifest.json',manifest)

if '--manifest-only' in sys.argv:raise SystemExit(0)

audit=read(B/'canonical-records-audit.json')
print('Canonical audit status:',audit.get('status',audit.get('passed')))
assert audit['status']=='passed_bounded_scientific_draft_audit'
for path in sorted((B/'canonical-drafts').glob('*.json')):
    assert sha(path)==audit['reviewed_hashes'][path.name]
    r=read(path)
    r['quality']['review_status']='source_reviewed'
    r['quality']['requested_tasks']=['precursor_selection','partial_protocol'] if r['record_type']=='protocol_variant' else []
    r['quality']['review_scope']=r['quality']['review_scope'].replace('Private structured draft from all six supplied main pages; canonical audit and reader integration remain pending.','All six supplied main pages read and visually reviewed; independently audited source extraction and sample links.').replace('Private contextual observation','Independently reviewed contextual observation')
    r['sources'][0]['main_status']='All six supplied main pages read and visually inspected; independent scientific audit completed for this source scope'
    write(S/'data/records'/(r['record_id']+'.json'),r)
proposal=read(B/'public-review-proposal/heath1996.json')
proposal['coverage_status']='supplied_main_text_and_visual_review_complete; SI_unverified'
proposal['independent_audit']='Complete supplied-main scientific audit and bounded canonical operation/stock/measurement/sample-link audit passed. Reader integration checks are recorded separately; no matching SI has been reviewed.'
proposal['publication_status']='Reviewed contribution prepared for the existing MatterSyn atlas; deployment tracked separately.'
proposal['audit_details']['scope_note']='Source and canonical audits completed. Source-only models and references remain outside measured training labels.'
proposal['source_review_promoted']=True
proposal['training_note']='The source ledger is contextual evidence, not a training example. Two reviewed template variants request precursor-selection and partial-protocol tasks; characterization and unpatterned comparison remain excluded. Eligibility is derived separately from canonical records.'
for entry in proposal['recipe_inventory']:
    entry['status']='source_reviewed'
    entry['gaps']=[g for g in entry.get('gaps',[]) if g!='Canonical source-join audit and reader integration remain pending.']
for section in proposal.get('reader_sections',[]):
    for item in section['items']:
        for link in item.get('canonical_links',[]):link['relation']='Reviewed canonical record; source-level context does not establish a unique physical specimen.'
ids=[p.stem for p in sorted((B/'canonical-drafts').glob('*.json'))]
proposal['material_evidence_records']={f:ids for f in ['Ge/Si','Ge','Si']}
scope='Six supplied main pages reviewed; matching SI unverified. Both template variants share one substrate and CVD exposure. Spectroscopy is shared patterned-wafer context; unpatterned pilot observations retain their separate scope.'
proposal['material_evidence_scope_notes']={'Ge/Si':scope,'Ge':'Component context: supported Ge islands on Si, not an isolated Ge-colloid synthesis. '+scope,'Si':'Component context: Si substrate supporting Ge dots, separate from surface-oxidized silicon colloids. Measurements retain the Ge/Si specimen attribution. '+scope}
write(S/'data/paper-reviews/heath1996.json',proposal)
for item in read(B/'crop-assets/manifest.json')['items']:
    src=B/'crop-assets'/item['file'];assert sha(src)==item['sha256']
    dest=S/'dist/assets/figures/heath1996'/item['file'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)

# Source-specific fields remain structural observations, not optical properties.
p=S/'data/measurement-display.json';display=read(p)
extra=['well_diameter','well_depth','oxide_mask_thickness','islands_per_well','wells_in_distance_analysis','nearest_neighbor_distances_below_100nm_count','afm_wells_imaged','afm_single_dot_wells','afm_wells_without_apparent_dot','apparent_afm_height','apparent_afm_width','author_bounded_particle_diameter','reported_late_island_size','substrate_coverage']
display['structural_properties']=list(dict.fromkeys(display['structural_properties']+extra));write(p,display)

p=S/'scripts/build_atlas.py';text=p.read_text(encoding='utf-8').replace("'Si':'Silicon cores in surface-oxidized colloids'","'Si':'Silicon · cores and substrates','Ge/Si':'Germanium quantum dots on silicon','Ge':'Germanium in supported quantum-dot arrays'")
p.write_text(text,encoding='utf-8')
p=S/'scripts/build_dataset.py';text=p.read_text(encoding='utf-8').replace("'dataset_version':'0.5.0'","'dataset_version':'0.6.0'");p.write_text(text,encoding='utf-8')
print('Imported four reviewed records and supplied-main ledger. Chemical assets, process diagrams and independent reader validation remain required before publication.')
