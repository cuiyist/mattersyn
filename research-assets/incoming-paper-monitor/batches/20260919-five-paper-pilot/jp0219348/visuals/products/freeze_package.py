"""Bound and freeze the private authored viewer proposal; never promote it."""
from pathlib import Path
import csv,hashlib,json,subprocess
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;H=P.parents[1];R=H/'si-reader-proposal';C=H/'canonical-proposal/v2';A=H/'structure-candidate'
NODE=Path('[local path redacted]')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rel(p):return p.relative_to(H).as_posix()
assert not(P/'package-manifest.json').exists(),'Preserve the frozen package; create a separate revision.'
checks=[]
def ck(ok,label):
 checks.append({'check':label,'passed':bool(ok)})
 if not ok:raise AssertionError(label)
cm=read(C/'canonical-record-manifest.json');binding=read(P/'product-viewer-proposal.json')
for rid,digest in cm['record_hashes'].items():ck(sha(C/'canonical-drafts'/f'{rid}.json')==digest,'Unmodified canonical '+rid)
ck(sha(C/'proposal-package-manifest.json')=='10640012af6a21458edd6a84c24af2dea24562f950495a662930d682185fb05a','Unmodified canonical v2 freeze')
ck(sha(A/'average-model.json')=='990eb81a939e2c638dd519a5f64c12ba9184cabfbd4c9f72a9782f1b86af0d20','Unmodified audited average model')
ck(sha(P/'heo2003-average-position-occupancy.cif')==sha(A/'heo2003-average-position-occupancy.cif'),'Exact audited CIF bytes')
ck(sha(H/'si-complete-candidate/independent-audit.json')=='e5f0cb753560f9a1561b0b55b06bb647b16a315cdd8b4a51fb9b7563591ad741','Unmodified SI aggregate audit')
for b in binding['bindings']:
 rec=read(C/'canonical-drafts'/f"{b['record_id']}.json");sample=rec['products'][int(b['canonical_json_pointer'].split('/')[-1])]
 ck(sample==b['canonical_sample'] and b['sample_id']==sample['sample_id'],'Exact product context '+b['record_id'])
 ck(b['canonical_record_sha256']==cm['record_hashes'][b['record_id']],'Exact binding hash '+b['record_id'])
 ck(b['binding_approved'] is False and b['exact_structure_recipe_eligible'] is False,'Pending mapping gates '+b['record_id'])
si=read(R/'heo2003-reflections.json');source=read(H/'si-complete-candidate/all-reflections.json')
rows=list(csv.DictReader((R/'heo2003-reflections.tsv').open(encoding='utf-8',newline=''),delimiter='\t'))
ck(len(rows)==len(si['rows'])==len(source['rows'])==1209,'Full 1209-row transport')
for src,r,t in zip(source['rows'],si['rows'],rows):
 ck(src['raw_cells']==r['raw_cells'] and src['hkl']==r['hkl'],'Exact source raw row '+r['row_id'])
 ck(t['row_id']==r['row_id'],'Exact TSV row identity '+r['row_id'])
 cells={x['evidence']['column_key']:x for x in r['cells']}
 for k in ['h','k','l','Fcal2','Fobs2','sigma_Fobs2','marker']:
  ck(t[k if k in ('h','k','l') else k+'_raw']==str(r['raw_cells'][k]),'Exact TSV raw '+r['row_id']+'/'+k)
 for k in ['Fcal2','Fobs2','sigma_Fobs2']:
  value=cells[k]['numeric_value'];v=t[k+'_numeric']
  ck(v=='' if value is None else float(v)==value,'Exact TSV numeric '+r['row_id']+'/'+k)
  ck(cells[k]['numeric_value']==next(x for x in src['cells'] if x['evidence']['column_key']==k)['numeric_value'],'Exact source typed '+r['row_id']+'/'+k)
def inspect_paths(x):
 if isinstance(x,dict):
  for k,v in x.items():
   ck(k not in ('source_path','original_crop_path','path','transcription_path'),'Public key is not a private path: '+k)
   inspect_paths(v)
 elif isinstance(x,list):
  for v in x:inspect_paths(v)
 elif isinstance(x,str):
  ck('C:/' not in x and 'C:\\' not in x and '/Users/' not in x,'No local absolute path value')
inspect_paths(si)
runtime=json.loads(subprocess.check_output([str(NODE),str(P/'check_viewer_contract.mjs')],text=True,encoding='utf-8'))
save(P/'runtime-author-validation.json',runtime)
browser=read(P/'author-preview/browser-validation.json');ck(browser['status']=='passed_private_browser_author_checks','Private browser checks passed')
ck(not browser['runtime_errors'],'No private browser JS errors')
for file in [P/'heo2003-average-viewer.mjs',R/'heo2003-reflection-viewer.mjs']:
 subprocess.run([str(NODE),'--check',str(file)],check=True,capture_output=True);ck(True,'JS syntax '+file.name)
snapshots=['desktop-unit-cell.png','periodic-model.png','occupancy-and-caveats.png','unresolved-signs.png','mobile-unit-cell.png','mobile-reflections.png','fallback-projection.png']
manual=[
 'Actually viewed desktop unit cell and periodic model screenshots: source-average markers and frame render; controls and scope notes readable.',
 'Actually viewed expanded occupancy table and caveats: mixed T, 25/32 and 1/32 split occupations, nominal discrepancy, ADP omission and unresolved angle remain readable.',
 'Actually viewed the unresolved-sign screenshot: both raw editorial tokens, null parsed value and signed alternatives visible; o-like marker is literal.',
 'Actually viewed mobile unit-cell and reflection screenshots: controls wrap and the wide table scrolls inside its container, with no page overflow.',
 'Actually viewed original-coordinate-derived SVG fallback screenshot: full cell projection and explanatory caption visible without clipping.',
 'The seven screenshots are private author-preview evidence; no live Site integration or independent scientific approval is claimed.'
]
bound=[A/'average-model.json',A/'heo2003-average-position-occupancy.cif',A/'independent-audit.json',A/'independent-audit-addendum.json',A/'package-freeze.json',H/'si-complete-candidate/all-reflections.json',H/'si-complete-candidate/independent-audit.json',C/'proposal-package-manifest.json',C/'canonical-record-manifest.json',H/'canonical-proposal/audit-v2/independent-audit.json']
bound += [C/'canonical-drafts'/f'{rid}.json' for rid in cm['record_hashes']]
save(P/'final-author-validation.json',{'status':'passed_private_author_validation','author':'/root/peng1998_reader_assets','at':datetime.now(timezone.utc).isoformat(),'check_count':len(checks),'checks':checks,'initial_data_transport_checks':read(P/'data-author-validation.json')['check_count'],'exported_function_checks':runtime['checks'],'private_browser_checks':browser['checks'],'manual_visual_scope':manual,'inspected_screenshots':[{ 'path':rel(P/'author-preview'/n),'sha256':sha(P/'author-preview'/n)} for n in snapshots],'bound_source_files':{rel(p):sha(p) for p in bound},'historical_report_note':'data-author-validation.json records data-stage runtime/visual pending; this report and the separately hashed browser report complete only author checks. Distinct package audit and Site integration remain pending.','independent_scientific_audit':'pending','live_site_integration':'pending','training_approved':False})
public_product=['heo2003-average-view.json','heo2003-average-position-occupancy.cif','heo2003-average-cell.svg','heo2003-average-viewer.mjs','heo2003-viewers.css']
public_si=['heo2003-reflections.json','heo2003-reflections.tsv','heo2003-reflection-viewer.mjs']
save(R/'package-manifest.json',{'schema':'mattersyn-private-si-reader-projection/1','source_id':'heo2003','status':'frozen_author_candidate_pending_distinct_review','counts':si['counts'],'public_assets':{n:sha(R/n) for n in public_si},'files':{rel(p):sha(p) for p in sorted(R.rglob('*')) if p.is_file() and p.name!='package-manifest.json'},'source_aggregate_sha256':sha(H/'si-complete-candidate/all-reflections.json'),'source_aggregate_audit_sha256':sha(H/'si-complete-candidate/independent-audit.json'),'published':False,'training_approved':False})
owned=[p for base in [P,R] for p in sorted(base.rglob('*')) if p.is_file() and p!=P/'package-manifest.json']
save(P/'package-manifest.json',{'schema':'mattersyn-private-source-average-and-reflection-viewers/1','source_id':'heo2003','author':'/root/peng1998_reader_assets','status':'frozen_author_candidate_pending_distinct_review','counts':{'product_bindings':3,'explicit_record_exclusions':7,'distinct_average_positions':680,'statistical_species_components':872,'weighted_atoms':642,'reflection_rows':1209,'numeric_positions':7254,'resolved_numeric_values':7252,'null_signed_values':2,'negative_observations':137,'zero_observations':1},'public_assets':{rel(p):sha(p) for p in [*[P/n for n in public_product],*[R/n for n in public_si]]},'private_files':{rel(p):sha(p) for p in owned},'bound_source_files':{rel(p):sha(p) for p in bound},'independent_scientific_audit':'pending','binding_approved':False,'published':False,'requested_tasks':[],'exact_structure_recipe_eligible':False,'dft_input_eligible':False})
print(json.dumps({'status':'frozen_author_candidate','product_manifest_sha256':sha(P/'package-manifest.json'),'si_manifest_sha256':sha(R/'package-manifest.json'),'author_final_sha256':sha(P/'final-author-validation.json'),'author_checks':len(checks),'runtime_checks':runtime['checks'],'browser_checks':browser['checks']}))
