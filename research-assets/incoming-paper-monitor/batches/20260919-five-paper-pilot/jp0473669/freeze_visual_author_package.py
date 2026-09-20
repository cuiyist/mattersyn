"""Freeze private visual author outputs, leaving independent review pending."""
import json, hashlib, datetime, xml.etree.ElementTree as ET
from pathlib import Path
B=Path(__file__).resolve().parent;V=B/'visuals';A=V/'apparatus';M=V/'molecules'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[]
def ck(x,label):checks.append({'check':label,'passed':bool(x)})
g=read(M/'generation-manifest.json');mv=read(M/'author-validation.json');sc=read(A/'scene-manifest.json');rv=read(A/'render-validation.json');bind=read(M/'molecule-bindings-proposal.json')
ck(mv['status']=='passed_author_checks' and not mv['failures'],'Molecular author validation passed')
ck(all(x['passed'] for x in sc['checks']),'Scene renderer checks passed')
for p,d in g['input_hashes'].items():ck(sha(Path(p))==d,'Protected input '+p)
for p,d in g['files'].items():ck(sha(M/p)==d,'Frozen molecule asset/provenance '+p)
ck(sha(A/'scene-manifest.json')==rv['scene_manifest_sha256'],'Preview manifest binds exact scene manifest')
ck(sha(A/sc['module'])==sc['module_sha256'],'Exact module hash')
for x in rv['files']:
 ck(sha(A/x['svg_file'])==x['svg_sha256'] and sha(A/x['png_file'])==x['png_sha256'],x['operation_id']+' SVG/PNG correspondence')
for p in list((M/'svg').glob('*.svg'))+list((A/'scene-svg').glob('*.svg')):
 tree=ET.fromstring(p.read_text());ck(tree.tag.endswith('svg') and tree.find('{http://www.w3.org/2000/svg}title') is not None,p.name+' valid labeled SVG')
for x in bind['slots']:ck(not x['binding_approved'] and x['independent_scientific_audit']=='pending','Binding stays unapproved '+x['record_id']+x['json_pointer'])
ck(sha(B/'public-review-proposal/ribeiro2004.json')=='847eec69dbc8e54386a8911e0b572cbb99d46d7cd4566f7a4bbd15233478d085','Frozen reader unchanged')
ck(sc['counts']['total_scenes']==13 and sc['counts']['preparation_operations']==9 and sc['counts']['acquisition_operations']==4,'Complete 13 operation scenes')
science=[
 {'check':'Tin precursor hydrate','finding':'Exact PubChem CID 10198436 ionic-component graph retains Sn2+, two Cl− and two H2O; 61436 connected Cl–Sn–Cl alternate is cached but not used. Neither is called measured source geometry.'},
 {'check':'Nitric acid','finding':'CID 944 HNO3 properties, 2D and 3D SDF connectivity agree. The original database-computed heavy coordinates are preserved; N–O distances recalculated as 1.3980, 1.2298 and 1.2299 Å. Aqueous species fractions are not inferred.'},
 {'check':'Aqueous TBAOH','finding':'CID 2723671 yields four n-butyl chains on N+ and isolated OH−, no Br. Source 0.4 mol/L is the stock concentration; source J. T. Baker, dose and final-pH missingness retained. Solvent water is separate, with no invented fixed stoichiometry.'},
 {'check':'Role-specific water/ethanol','finding':'Reuse exact qualified ethanol/water assets. Absolute ethanol / Merck belongs to its binding. Hydrolysis-water grade is unknown; dialysis-water grade is deionized. The registry’s Milli-Q alias must not be shown as source evidence. Aqueous reagent-solvent grades are unknown.'},
 {'check':'Support and specimen identity','finding':'New Ribeiro support metadata replaces incompatible other-paper provenance. Sn(OH)4 remains a proposed formula intermediate. A composition-only SnO2 icon serves five distinct canonical contexts without joining physical batches or asserting sizes/coordinates.'},
 {'check':'Hydrolysis and dialysis','finding':'Initial 0.0025–0.1 mol/L ethanolic precursor range, room-temperature hydrolysis, approximate 500:1 ratio of unknown basis, white turbidity and chloride-removal dialysis preserve reported/missing distinctions. No addition sequence, time, membrane cutoff or water amount invented.'},
 {'check':'Treatment versus measurement','finding':'0.025 M-origin modified-pH samples age 24 h at unreported temperature/atmosphere, then receive TBAOH and 2 min probe sonication for spectroscopy. Acid-set pH 1.5–8.5 is not final pH after base; no numeric final pH or sonicator power supplied.'},
 {'check':'TEM preparation/acquisition','finding':'One colloid drop, 20 s wetting of carbon-coated copper grids, air drying, Philips CM200 at 200 kV and at least 200 particles are retained. This is specimen preparation, not bulk-powder isolation. Radius is distinguished from diameter; no synthetic micrograph or SAED pattern supplied.'},
 {'check':'Optical/electrokinetic acquisition','finding':'UV–vis acquisition 220–360 nm, PL excitation 250 nm and acquisition 250–400 nm remain separate from figure display limits. Named instruments and optical room temperature retained; path length/dilution and zeta cell/applied-field details remain unknown.'},
 {'check':'Source and crystal scope','finding':'Main article only; SI unverified. Source cassiterite/XRD prose does not supply the missing trace, SAED, lattice parameters, CIF or atomic coordinates. No crystal asset or exact structure-training admission created.'}
]
manual={'author':'/root/backlog_eta','status':'passed_author_visual_inspection','main_source_reread':'Main PDF p. 2 Experimental Procedure text and original experimental-procedure.png visually reopened; source facts/canonical records retained as audited dependencies. This is not a repeated whole-paper extraction.',
 'molecules':'All six final identity preview designs were inspected. The corrected final tin component cards were reopened at full size after initial water-label overlap was found.',
 'apparatus':'All thirteen scene designs were visually inspected across four contact sheets; the corrected TBAOH-redispersion PNG was reopened individually. Other scenes remained source-specific, legible and distinct.',
 'corrections':[{'asset':'Tin dihydrate depiction','change':'Separated touching water labels using five explicit component cards and a spaced 2D atom layout. Exact chemical graph and hydration count unchanged.'},{'asset':'TBAOH redispersion scene','change':'Removed the small redundant caption that crossed the top of the reagent bottle. Scientific condition panel and source values unchanged.'}],
 'browser_test':'Not performed; DOM wrapper compatibility is a static test only. Desktop/mobile control checks belong to later integration.',
 'independent_scientific_audit':'Pending distinct reviewer.'}
dump(A/'author-visual-check.json',{'schema':'mattersyn-private-apparatus-author-visual-check/1','source_id':'ribeiro2004','status':'passed_author_visual_inspection','scene_manifest_sha256':sha(A/'scene-manifest.json'),'render_validation_sha256':sha(A/'render-validation.json'),'manual_review':manual,'scientific_checks':science[5:],'all_13_operations_covered':True,'independent_visual_audit':'pending'})
files={str(p.relative_to(B)).replace('\\','/'):sha(p) for p in V.rglob('*') if p.is_file() and p.name not in ['visual-author-manifest.json','visual-author-validation.json']}
files['freeze_visual_author_package.py']=sha(Path(__file__))
failed=[x for x in checks if not x['passed']]
validation={'schema':'mattersyn-private-visual-author-validation/1','source_id':'ribeiro2004','status':'passed_author_checks' if not failed else 'failed','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'counts':{'molecular_checks':mv['counts']['checks'],'scene_checks':len(sc['checks']),'freeze_checks':len(checks),'new_reference_entries':6,'reused_entries':2,'new_models':4,'new_identity_svg_png_pairs':6,'material_slot_proposals':13,'component_contexts':3,'operation_scenes':13,'contact_sheets':4},'checks':checks,'failures':failed,'scientific_author_checks':science,'manual_visual_review':manual,'source_and_canonical_unchanged':not failed,'independent_audit':'pending','site_edited':False,'new_paper_downloads':False}
dump(V/'visual-author-validation.json',validation)
files['visuals/visual-author-validation.json']=sha(V/'visual-author-validation.json')
manifest={'schema':'mattersyn-private-visual-author-manifest/1','source_id':'ribeiro2004','author':'/root/backlog_eta','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'frozen_author_package_pending_distinct_visual_audit' if not failed else 'failed_freeze','counts':validation['counts'],'files':files,'source_inputs':g['input_hashes'],'frozen_reader_sha256':sha(B/'public-review-proposal/ribeiro2004.json'),'source_main_sha256':sc['source_main_sha256'],'candidate_plan_sha256':sc['plan_sha256'],'molecular_generation_manifest_sha256':sha(M/'generation-manifest.json'),'apparatus_manifest_sha256':sha(A/'scene-manifest.json'),'independent_scientific_audit':'pending','binding_approval':False,'browser_approval':False,'publication_approval':False}
dump(V/'visual-author-manifest.json',manifest)
print(json.dumps({'status':manifest['status'],'counts':manifest['counts'],'failures':failed,'manifest_sha256':sha(V/'visual-author-manifest.json'),'validation_sha256':sha(V/'visual-author-validation.json')},indent=2));raise SystemExit(bool(failed))
