"""Read-only independent review binding; writes only separate audit files in B."""
from pathlib import Path
import json,hashlib,datetime
B=Path(__file__).resolve().parent
A=B/'visuals/apparatus'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
runtime=read(B/'apparatus-independent-runtime-check.json')
assert runtime['status']=='passed'
author=read(A/'author-visual-check.json')
manifest=read(A/'scene-manifest.json')
old=read(A/'author-revision-1/scene-manifest.json')
checks=[]
def check(name,condition,detail=None):
    checks.append(dict(check=name,passed=bool(condition),**({'detail':detail} if detail is not None else {})))
bound=dict(runtime['bound_files'])
for name in ['author-visual-check.json','scene-manifest.json','nagasaki2004-protocol.mjs']:
    p=A/name;bound[str(p)]=sha(p)
for p,h in runtime['bound_files'].items():
    check('Runtime bound file remains exact: '+p,sha(Path(p))==h)
for p,h in author['bound_files'].items():
    check('Author frozen file independently rehashed: '+p,sha(Path(p))==h)
    bound[p]=h
src=read(B/'source-inventory.json')
for d in src['documents']:
    p=Path(d['original_path']);check('Original '+d['role']+' source SHA unchanged',sha(p)==d['source_sha256']);bound[str(p)]=sha(p)
for f in ['main-02.txt','main-03.txt','main-04.txt','si-01.txt','main-02.png','si-01.png','apparatus-independent-runtime-check.json','audit_apparatus_readonly.mjs']:
    p=B/f;bound[str(p)]=sha(p)
old_by={s['operation_id']:s for s in old['scenes']}
changed=[]
allowed={'no-polymer-control-prepare','peg-control-prepare','pama-control-prepare'}
for s in manifest['scenes']:
    old_s=old_by[s['operation_id']]
    check(s['operation_id']+' exact canonical operation across correction',s['operation']==old_s['operation'] and s['canonical_sha256']==old_s['canonical_sha256'])
    fields=[k for k in s if s[k]!=old_s[k]]
    if fields:
        changed.append({'operation_id':s['operation_id'],'fields':fields})
        check(s['operation_id']+' bounded presentation-only revision',s['operation_id'] in allowed and set(fields)<= {'caption','condition_rows','svg_sha256'})
    if s['operation_id'] in allowed:
        check(s['operation_id']+' concentration-basis caveat visible','Stock-versus-final concentration basis' in s['caption'])
    if s['operation_id']=='pama-control-prepare':
        rows={row['label']:row['value'] for row in s['condition_rows']}
        check('PAMA control CdCl2 and Na2S displayed separately',rows.get('Reported CdCl₂ concentration')=='0.0025 mol/L' and rows.get('Reported Na₂S concentration')=='0.0025 mol/L',rows)
check('Only the three reported control scenes changed',set(x['operation_id'] for x in changed)==allowed)
for f in ['scene-manifest.json','nagasaki2004-protocol.mjs','author-visual-check.json']:
    p=A/'author-revision-1'/f;bound[str(p)]=sha(p)
manual=[
 {'id':'polymer-upstream','operations':['pdp-form','eo-add','eo-react','ama-block'],'finding':'The source PDP/THF/EO/AMA charges, two-day then 60-minute order, cooled syringe without a numerical temperature, and ambient AMA interval are preserved. No reaction cooling, inert atmosphere or stirring is assigned to the EO hold.'},
 {'id':'polymer-workup','operations':['polymer-precipitate','pama-protonate','soxhlet-clean'],'finding':'Excess 2-propanol precipitation retains the block copolymer. Protonation remains before THF Soxhlet extraction without identifying an unreported acid; PEG prepolymer is the removed fraction. Generic equipment does not supply thermal or isolation parameters.'},
 {'id':'polymer-nmr','operations':['polymer-nmr'],'finding':'Almost quantitative acetal functionality stays a qualitative source conclusion. The scene has no invented spectrum, field, solvent or exact percentage.'},
 {'id':'aldehyde-branch','operations':['hydrolyze-acetal','neutralize','dialyze-polymer'],'finding':'10:1 v/v acid/water, 35 °C and five hours belong to acetal hydrolysis. NaOH neutralization has no inferred endpoint or dose; dialysis retains the polymer-containing fraction in water.'},
 {'id':'biotin-endgroup','operations':['biotin-condense','biotin-reduce','biotin-dialysis-context'],'finding':'Biocytin hydrazide is installed before dialysis and CdS preparation. Two hours belongs to condensation; NaBH4 reduction has no inherited duration. CHO, Schiff-base and biotin symbols remain distinct, without exact chain conformation.'},
 {'id':'representative-cds','operations':['polymer-medium','cd-add','s-add','cds-stir','cds-dialyze'],'finding':'The initial aqueous polymer volume is 8 mL and concentration is per amine group. CdCl2 precedes Na2S; no CdS particles appear before sulfide addition. The one-hour ambient hold and retained dialyzed dispersion are preserved; addition volumes and stock-versus-final concentration basis remain unreported/unresolved.'},
 {'id':'biotin-variant','operations':['biotin-cds-coprecipitate'],'finding':'The similar-manner biotin branch is explicit but does not inherit the representative 8 mL, amine concentration, added volumes or one-hour duration as reported biotin values. A qualitative framework is not a newly quantified synthesis batch.'},
 {'id':'concentration-series','operations':['cho-cds-low-amine-prepare','cho-cds-high-amine-prepare'],'finding':'Low and high amine values are source comparison contexts; the intermediate representative remains separate. Nominal CdS chemistry concentration is not a particle number density, and C1/sample correspondence is not resolved by the picture.'},
 {'id':'stabilizer-controls','operations':['no-polymer-control-prepare','peg-control-prepare','pama-control-prepare'],'finding':'No-polymer, PEG-OH and PAMA homopolymer contexts are separate; only source outcome schematics are shown. Both 0.0025 mol/L reagent values and their unresolved basis are now visible in all three. Mn has no invented printed unit, and PAMA low-salt appearance is not a simulated spectrum.'},
 {'id':'salt-challenge','operations':['salt-expose'],'finding':'The 0.3 mol/L NaCl challenge and qualitative several-day observation are separate from preparation. Four depicted contexts are not mixed and do not assert four independent synthesis batches.'},
 {'id':'optical-acquisition','operations':['uv-vis','fluorescence'],'finding':'The 1 cm quartz cell belongs to absorption; 400 nm and both 2.5 nm bandwidths belong to fluorescence. Acquisition diagrams contain no reconstructed curve or asserted cross-specimen batch join.'},
 {'id':'zeta-acquisition','operations':['zeta-medium'],'finding':'pH 2–11, 7.5 mmol/L NaCl and HCl OR NaOH are measurement-medium conditions. They are not synthesis pH or an identified polymer-protonation reagent.'},
 {'id':'fret-assay','operations':['fret-mix'],'finding':'Biotin-CdS plus TexasRed-streptavidin is a recognition assay: ionic strength 0.15 mol/L, nominal CdS 396 micromol/L and excitation 400 nm stay in assay scope. The electrolyte identity and cross-figure physical batch are not invented.'},
 {'id':'recognition-controls','operations':['streptavidin-competition-premix','bsa-control-premix'],'finding':'Unlabeled streptavidin and BSA are distinct premixes before the TexasRed-streptavidin addition. The C2 varied-species conflict and exclusion-volume interpretation remain contextual, rather than repaired experimental assignments.'},
 {'id':'tem-acquisition','operations':['tem-grid-dry','tem-acquire'],'finding':'The supplied SI calls for a dilute drop, formval-film-coated Cu grid, air drying and EF-TEM at 200 kV. No mesh, carbon coating, drying time or exact identity with a biotin specimen is added.'},
 {'id':'xrd-acquisition','operations':['xrd-freeze-dry','xrd-scan'],'finding':'PEG/PAMA and PEG/PAMA–CdS are separately freeze-dried and placed on glass slides. Cu Kα, 40 kV, 30 mA, 15–60° 2θ and 0.02° increment are retained. No synthetic diffraction trace, dwell time, scan rate or extra polymer-only measured trace is generated.'},
 {'id':'visual-legibility','operations':'all 36','finding':'All six contact sheets were actually viewed and every panel read; the three revised control PNGs were additionally inspected at their full rendered size. Academic titles, source-stage labels, retained fractions, conditions and limitations are readable. Geometry and colors are labeled explanatory, not measured atomic or apparatus data.'}
]
check('Manual scopes enumerate all 36 canonical operation IDs',set(o for m in manual if isinstance(m['operations'],list) for o in m['operations'])==set(s['operation_id'] for s in manifest['scenes']))
fail=[x for x in checks if not x['passed']]
report={
 'schema':'mattersyn.independent-apparatus-source-audit/1','source_id':'nagasaki2004','auditor':'/root/peng1998_reader_assets','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'findings' if fail else 'passed',
 'scope':'Independent source/canonical-to-scene audit of the 36 private Nagasaki apparatus scenes. This is not a new complete source extraction, molecular/crystal audit, integrated-Site test, or browser interaction approval.',
 'counts':{'scenes':36,'manual_scientific_scopes':len(manual),'contact_sheets_actually_viewed':6,'revised_full_scene_views':3,'runtime_mechanical_checks':runtime['counts']['checks'],'final_binding_and_delta_checks':len(checks),'failures':len(fail),'bound_files':len(bound)},
 'actual_source_scope':{'text_reread':['main PDF p2, Experimental and relevant results','main PDF p3, Figures 1–3 and source context','main PDF p4, FRET and recognition-control prose/captions','SI PDF p1, TEM and XRD methods'],'source_page_images_actually_viewed_in_this_audit':['main-02.png','si-01.png'],'prior_audited_inputs':['source-inventory.json','source-facts.json','canonical-records-audit.json','reader-source-audit.json'],'limitation':'Other full source pages were not redundantly reread for this bounded apparatus audit; current canonical bindings and the previously passed source/canonical/reader boundaries were retained.'},
 'actual_visual_scope':{'all_contact_sheets':[str(p) for p in sorted((A/'review').glob('contact-*.png'))],'revised_full_scenes':[str(A/'review'/('nagasaki-2004-stabilizer-controls--'+s+'.png')) for s in sorted(allowed)],'live_browser':False,'mounted_api':'DOM stub checked exact returned SVG, classes and scoped dataset for all 36 operations; no claim of live DOM layout/WebGL/browser interaction.'},
 'manual_scientific_scopes':manual,'correction_history':[
 {'id':'A1','status':'resolved','original_finding':'PAMA control scene omitted the two reported precursor-concentration rows, although canonical quantities were present.','resolution':'Author added exact CdCl2 and Na2S canonical parameter rows, each 0.0025 mol/L. Original freeze retained under author-revision-1; revised full PNG viewed.'},
 {'id':'A2','status':'resolved','original_finding':'No-polymer/PEG/PAMA control captions did not expose the stock-versus-final concentration-basis ambiguity.','resolution':'Author added explicit unresolved basis/addition-volume notes to all three captions. No canonical numerical or source field changed.'}],
 'presentation_delta':changed,'checks':checks,'failures':fail,'bound_files':bound,
 'remaining_gates':['Independent components/binding audit and any separate crystal-reference gate','Actual Site integration and responsive/browser interaction verification','Publication approval by site owner'],
 'site_integration_approved':False,'publication_approved':False,'training_admission_approved':False,
 'audit_helper_sha256':sha(Path(__file__))
}
(B/'apparatus-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# Nagasaki apparatus: independent source audit','',f"Status: **{report['status']}**.",'',f"Inspected all 36 canonical operation/configuration pairs and actual scenes on six contact sheets; revisited all three revised control PNGs at full rendered size. {runtime['counts']['checks']} runtime/mechanical checks and {len(checks)} final hash/delta checks; {len(fail)} open findings.",'','Two presentation omissions were corrected by the author: the PAMA control now exposes both reported 0.0025 mol/L precursor values, and all three stabilizer-control captions show the unresolved stock-versus-final concentration basis. The original freeze and finding history are retained. No source or canonical scientific data changed.','','Targeted source rereads covered main pages 2–4 and SI page 1. Main page 2 and SI page 1 images were actually viewed during this audit. Other source coverage remains bound to the separately passed extraction/canonical/reader audits.','','## Scientific boundaries','']
lines.extend('- '+x['finding'] for x in manual)
lines+=['','## Scope limits','','The DOM-stub check verifies the current module output and mounting metadata; it is not live-browser QA. This audit does not approve molecular/crystal models, Site integration, publication or training admission. Exact input/output hashes and the complete operation coverage are in the accompanying JSON and apparatus-independent-runtime-check.json.','']
(B/'apparatus-source-audit.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({'status':report['status'],'counts':report['counts'],'audit_sha256':sha(B/'apparatus-source-audit.json'),'failures':fail},ensure_ascii=False,indent=2))
