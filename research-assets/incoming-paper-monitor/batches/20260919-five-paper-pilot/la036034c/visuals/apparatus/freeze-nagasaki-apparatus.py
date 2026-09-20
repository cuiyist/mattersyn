"""Freeze root's visually inspected apparatus proposal for distinct review."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
V=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
m=read(V/'scene-manifest.json');r=read(V/'render-validation.json')
assert not (V/'author-visual-check.json').exists()
assert m['counts']['total_scenes']==r['scene_count']==36 and not r['text_overflows']
assert m['module_sha256']==r['module_sha256']==sha(V/'nagasaki2004-protocol.mjs')
assert r['scene_manifest_sha256']==sha(V/'scene-manifest.json')
bound=dict(m['bound_inputs'])
for p,h in bound.items():assert sha(p)==h,p
for n in ['nagasaki2004-protocol.mjs','render-nagasaki-scenes.mjs','render-nagasaki-previews.py','scene-manifest.json','render-validation.json']:
    bound[str(V/n)]=sha(V/n)
for s in m['scenes']:
    assert sha(V/s['svg_file'])==s['svg_sha256'];bound[str(V/s['svg_file'])]=s['svg_sha256']
for s in r['scenes']:
    assert sha(V/s['png_file'])==s['png_sha256'];bound[str(V/s['png_file'])]=s['png_sha256']
for s in r['contact_sheets']:
    assert sha(V/s['file'])==s['sha256'];bound[str(V/s['file'])]=s['sha256']
checks=[
 'All36actual canonical operation IDs have their own configuration and truthful current state.',
 'EO syringe cooling has no assigned numerical temperature or cooled reactor; two-day interval has no stir arrow.',
 'No CdS particle shown in Cd addition or polymer-only preparation; symbols begin at sulfide/coprecipitation context.',
 'Biotin installation precedes dialysis and CdS; 2h belongs to condensation, not reduction.',
 'Biotin variant lacks its own quantitative charges; no representative8mL/1h/concentration transfer.',
 'Water-dialysis retention differs from THF Soxhlet PEG-prepolymer removal; no unreported separation apparatus inferred.',
 'Source35degC/5h and10:1v/v belong to hydrolysis only; heat support is generic.',
 'Polymer group concentration, CdS chemical molarity and polymer M_n with unprinted unit remain distinct.',
 'HCl/NaOH alternatives and NaCl challenge/zeta/FRET electrolyte scopes remain separate.',
 'Protein control addition order preserved; Figure5 C2 and Figure2 C1 unresolved.',
 'TEM grid air drying and200kV not synthesis conditions; formval source wording retained.',
 'Separate freeze-dried polymer/CdS specimens; original XRD, TEM and optical data are not simulated.',
 'All36scenes inspected on6contact sheets;7changed examples reopened at full scene resolution, including all3corrected stabilizer controls.',
 'Each stabilizer control retains its own reported precursor concentrations and explicitly states unresolved stock-versus-final basis and addition volumes; PAMA now displays both CdCl2 and Na2S rows.',
 'Arrow occlusion, Soxhlet label collision and freeze-dryer title spacing corrected before freeze; XRD/TEM probe diagrams distinct.'
]
save(V/'author-visual-check.json',{'schema':'mattersyn.private-apparatus-author-check/1','source_id':'nagasaki2004','author':'/root','created_at':datetime.now(timezone.utc).isoformat(),'status':'passed_author_visual_source_mapping_pending_independent_audit',
    'scope':'Apparatus mapping from existing independently audited canonical operations. Root read all36operation descriptions/parameters and actually viewed all36rendered scenes; this does not assert a new full-paper extraction or independent audit.',
    'counts':{'scenes':36,'contact_sheets':6,'changed_full_scene_views':7,'mechanical_selection_checks':len(m['checks']),'scientific_author_scopes':len(checks),'bound_files':len(bound)},'scientific_scopes':checks,'bound_files':bound,
    'independent_visual_audit':'pending','molecule_product_audit':'separate','browser_qa':'not performed','site_integration':'not performed','publication_approved':False})
print(json.dumps({'scenes':36,'bound_files':len(bound),'author_check_sha256':sha(V/'author-visual-check.json')}))
