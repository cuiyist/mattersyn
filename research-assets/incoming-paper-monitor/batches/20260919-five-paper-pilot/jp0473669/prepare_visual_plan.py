"""Freeze the next visual work scope from audited records; no Site or asset edits."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib
B=Path(__file__).resolve().parent
S=Path(r'[local path redacted]')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
R=S/'dist/assets/chemical-registry'; registry=read(R/'registry.json')
entries={e['id']:e for e in registry['entries']}
decisions={
 'sncl2-dihydrate':('new_qualified_component_depiction',[],
    'Qualify SnCl2·2H2O identity and connectivity/components. Keep two hydration waters explicit; do not invent dissolved Sn coordination, oxidation mechanism or a SnO2 precursor crystal. Show source supplier and unreported mass beside the view.'),
 'ethanol':('existing_reference_candidate',['ethanol'],
    'Inspect cached connectivity, 2D/3D geometry and embedded captions before reuse. Source grade is absolute ethanol (Merck); volume is unknown. An isolated reference molecule does not establish the solution structure.'),
 'hydrolysis-water':('existing_reference_candidate',['water'],
    'Use the same qualified water reference with a distinct hydrolysis role. Water grade, dose, dosing order and the basis of the approximate 500:1 ratio are unreported; do not inherit dialysis-water qualification.'),
 'dialysis-water':('existing_reference_candidate',['water'],
    'Water reference with explicitly deionized dialysis role. Preserve unknown volume, membrane, exchange schedule, duration and endpoint.'),
 'nitric-acid':('new_qualified_component_depiction',['identity-yi-nitric-acid'],
    'Existing formula-only acid drawing is from another source and lacks a molecular graph. Qualify an independent reference connectivity and show separate solvent component only to the extent supported; no acid concentration, dose or ionic proportion is supplied. Do not inherit Yi-specific provenance.'),
 'tbaoh-aqueous':('new_qualified_component_depiction',['tetrabutylammonium-bromide'],
    'The required reagent is aqueous tetrabutylammonium hydroxide, not the existing bromide. Verify cation, hydroxide and water components independently before a new depiction. Do not reuse the Br-containing model unchanged. Stock is 0.4 mol/L; final dose, concentration and measurement pH are unknown. Relative ion geometry remains schematic.'),
 'carbon-copper-grid':('source_specific_support',['identity-carbon-coated-copper-tem-grid-b47959'],
    'Source-specific carbon-coated copper grid illustration. No mesh count, coating thickness, brand, Formvar or atomic carbon phase is specified. Existing template provenance is not this specimen.'),
 'sno2-colloid':('source_specific_specimen',[],
    'Five analytical slots require their own sample context despite shared SnO2 identity. Use original HRTEM, radius histograms and scoped colloid schematics. Cassiterite is reported in XRD prose, but no original XRD/SAED trace or measured coordinates are supplied. A separately verified bulk reference, if later available, cannot become an exact sample structure or training pair.'),
 'sn-hydroxide-model':('author_proposed_intermediate',[],
    'Use explicit formula/context depiction for proposed Sn(OH)4 in Chemical intuition. It is not an isolated reagent, measured speciation or validated molecular geometry. Preserve unresolved Sn(II)-to-Sn(IV) pathway and authors’ differing growth descriptions.')}
scene={
 'hydrolysis-dissolve':'Salt and ethanol components with initial concentration series; no absolute volume or invented apparatus detail.',
 'hydrolysis-hydrolyze':'Generic hydrolysis vessel with separate water input of unspecified order. Room-temperature text, approximate 500:1 relative ratio with unknown basis, and white turbid endpoint; no inferred hot bath.',
 'hydrolysis-dialyze':'Schematic dialysis membrane and external deionized water; chloride removal and retained clear colloid, without unreported membrane specifications or timing.',
 'ph-treatment-acidify':'Source colloid plus nitric-acid adjustment, showing treatment pH range and 0.025 mol/L initial-precursor origin; no calculated dosing.',
 'ph-treatment-age':'Treatment samples with 24 h aging; temperature and atmosphere marked unknown.',
 'ph-treatment-redisperse':'Separate aqueous 0.4 mol/L TBAOH component card and optical specimen; unknown dose and final pH.',
 'ph-treatment-sonicate':'Probe-sonication action for 2 min; unknown power and geometry. Restrict to spectroscopic preparation.',
 'tem-preparation-wet-grid':'One colloid drop wetting carbon-coated copper grid for 20 s, with clear retained support/specimen distinction.',
 'tem-preparation-air-dry':'Air-drying grid, unknown duration; not a bulk powder isolation.',
 'tem-acquisition':'Microscopy acquisition schematic and original HRTEM links; 200 kV and at least 200 particles per size-distribution method.',
 'pl-acquisition':'Colloidal optical specimen and source acquisition settings with original PL; no invented spectrum.',
 'uv-acquisition':'Colloidal optical specimen and source absorption acquisition interval with original normalized curves; no invented curve-to-concentration map.',
 'zeta-acquisition':'Electrokinetic measurement context and original pH curve; do not carry over optical TBAOH preparation.'}
records={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')}
slots=[];operations=[]
for rid,d in records.items():
    for ix,m in enumerate(d['materials']):
        cls,candidates,note=decisions[m['id']]
        slots.append({'record_id':rid,'json_pointer':f'/materials/{ix}','source_material':m,
            'planned_treatment':cls,'candidate_registry_ids':candidates,'required_scope':note,'binding_approved':False})
    for ix,o in enumerate(d['operations']):
        operations.append({'record_id':rid,'json_pointer':f'/operations/{ix}','operation_id':o['id'],
            'planned_scene':scene[o['id']],'parameters_from_canonical':o['parameters'],
            'environment_from_canonical':o['environment'],'endpoint_from_canonical':o['endpoint'],
            'scene_approved':False})
candidates=sorted({i for v in decisions.values() for i in v[1]})
asset_hashes={}
for eid in candidates:
    for key in ['svgPath','model2dPath','model3dPath']:
        if entries[eid].get(key):
            p=R/entries[eid][key];asset_hashes[str(p)]=sha(p)
assert len(slots)==13 and len(operations)==13 and len({s['source_material']['id'] for s in slots})==9
output={'schema':'mattersyn-visual-preparation-plan/1','source_id':'ribeiro2004','author':'/root',
    'created_at':datetime.now(timezone.utc).isoformat(),'status':'candidate_plan_only_no_asset_or_binding_approval',
    'scope':'13 material slots across 9 identities, one initial-stock series and 13 operation scenes. Original 15 crops and final independent reader audit are already frozen; all new viewer assets and browser work remain pending.',
    'material_slots':slots,'operation_scenes':operations,'candidate_registry_snapshots':{i:entries[i] for i in candidates},
    'candidate_asset_hashes':asset_hashes,'record_hashes':{rid:sha(B/'canonical-drafts'/(rid+'.json')) for rid in records},
    'reader_audit_path':str(B/'reader-source-audit.json'),'reader_audit_sha256':sha(B/'reader-source-audit.json'),
    'registry_sha256':sha(R/'registry.json'),'plan_is_not_visual_audit':True,
    'known_reuse_rejections':['Tetrabutylammonium bromide cannot stand in for hydroxide.','Source-specific nitric-acid and grid provenance cannot be transferred.','Unverified bulk reference cannot supply the paper’s measured atom coordinates.'],
    'next_gates':['Qualify cached exact identities and generate missing source-specific assets in private scope.','Independent molecular/apparatus/product review.','Root integrates approved records, original figures and viewers into same Site.','Validate affected bindings and exercise actual desktop/mobile controls before publication.']}
(B/'visual-preparation-plan.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(B/'visual-preparation-plan.md').write_text('# Ribeiro SnO2 visual preparation\n\nCandidate plan only; no viewer binding or atomic model is approved.\n\nThree slots can use two existing molecular references after qualification: ethanol and water (separate hydrolysis and deionized dialysis roles). Three reagent identities need new qualified depictions: tin(II) chloride dihydrate, nitric acid and aqueous tetrabutylammonium hydroxide. The bromide reference cannot replace hydroxide. One support, five analytical SnO2 slots and one proposed-intermediate slot need source-specific context.\n\nAll 13 operations have a distinct scene plan driven by their canonical conditions, including dialysis, acid aging, optical redispersion, probe sonication, grid preparation and analytical acquisition. No hot bath, invented water dose, membrane specification or final measurement pH is added.\n\nThe 15 original crops and source-reviewed reader remain frozen. Cassiterite is an author XRD assignment without a supplied trace or atomic coordinates. Molecules, apparatus and product illustrations require separate validation and independent review before Site integration and actual browser QA.\n',encoding='utf-8')
print(json.dumps({'status':output['status'],'material_slots':len(slots),'identities':len(decisions),'operations':len(operations),'candidate_ids':candidates,'plan_sha256':sha(B/'visual-preparation-plan.json')}))
