from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
A=Path(__file__).resolve().parent;N=A.parents[1];C=N/'canonical-proposal/v2';P=N/'public-review-proposal/v2'
def read(p):return json.loads(p.read_text('utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(A/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf-8')
assert not (A/'package-freeze.json').exists(),'Do not overwrite frozen packages'
audit=N/'canonical-reader-independent-audit/independent-audit-v2.json'
assert read(audit)['status']=='passed'
b=read(A/'canonical-bindings.json');assert b['record_manifest_sha256']==sha(C/'record-manifest.json')
for x in b['bindings']:assert sha(Path(x['record_path']))==x['record_sha256'] and Path(x['record_path']).parent==C
b['status']='author_frozen_pending_distinct_audit';save('canonical-bindings.json',b)
v=read(A/'author-validation.json');assert v['operations']==31 and v['canonical_parameters']==50
previews=read(A/'preview-manifest.json');previews['visual_review_status']='All 31 preliminary scenes viewed on eight contact sheets; final grouped-condition critical previews reopened.';save('preview-manifest.json',previews)
save('author-visual-review.json',{'author':'/root','at':datetime.now(timezone.utc).isoformat(),'status':'author_checked_pending_independent_audit','original_pages_viewed':[7,8],'source_scope':'Passed independent source v2 and canonical v2; root read original main experimental pages 7 and 8 specifically for apparatus. Root does not claim fresh full-paper rereading.','scene_count':31,'viewed_contact_sheets':[{'path':x['path'],'sha256':sha(A/x['path'])} for x in previews['contacts']],'critical_final_previews':['mw-heat','insitu-heat','acs-heat','pdf-acquire','scf-react','oxide-heat'],'findings_resolved_before_first_freeze':['Grouped alternative schedules for readability while retaining every exact quantity pointer.','Preserved raw scalar precision, parenthetic wavelength uncertainty and fraction exponent.','Explicit unknown mixture composition and independent workup boundaries inherited from audited records.'],'actual_private_browser_scope':{'stage_selections':31,'visible_condition_rows':168,'console_errors':0,'mobile_viewport':{'width':390,'height':844,'document_width':375,'scroll_width':375},'mobile_scenes':['mw-heat','insitu-heat'],'site_integration_test':False},'scientific_independent_approval':False})
(A/'README.md').write_text('''# Sommer 2020 apparatus proposal

Root-authored candidate for 31 operations across 12 records, bound to passed source revision 2 and canonical revision 2. Independent apparatus approval and later integrated-site checks remain separate.

The module reads 50 operation quantities and all 155 alternative schedule quantities directly from canonical objects. Alternatives are grouped by source sample or profile, with exact quantity objects and JSON pointers retained. The 168 display rows include source-scoped conditions, alternatives, conflicts and missingness. A Table 1 zero dwell is not inferred to mean zero residence time. D-series intervals are collection contexts, not heating dwells.

Microwave, autoclave and continuous-flow reactors have distinct scenes. Capillary experiments, stock preparation, independent workup, microscopy and optical/diffraction acquisition have stage-specific illustrations. Vessel geometry, colors and detector layouts are explanatory. No numerical pressure, bath, spectrum, micrograph or atomic structure is invented.

Only `sommer2020-protocol.mjs` is a proposed Site module. `quantity-value.mjs` is an unchanged shared dependency. Preview data and source files do not become website attachments.

API mirrors the existing source-specific renderer: `buildSommer2020Scene`, `createSommer2020Art`, `createSommer2020ConditionGrid`, `renderSommer2020Markup`, `sommer2020SceneSelection`. Exact paper, record and operation gates reject unrelated contexts.
''','utf-8')
extra=[N/'package-freeze.json',N/'source-independent-audit/independent-audit-v2.json',C/'package-manifest.json',C/'record-manifest.json',audit,P/'sommer2020.json']+[Path(x['record_path']) for x in b['bindings']]
files=[p for p in A.rglob('*') if p.is_file() and p.name!='package-freeze.json' and '__pycache__' not in p.parts]+extra
save('package-freeze.json',{'schema':'mattersyn-private-apparatus-freeze/1','source_id':'sommer2020','doi':'10.1021/acs.cgd.9b01519','author':'/root','at':datetime.now(timezone.utc).isoformat(),'status':'frozen_pending_distinct_independent_audit','source_freeze_sha256':sha(N/'package-freeze.json'),'canonical_package_sha256':sha(C/'package-manifest.json'),'canonical_audit_sha256':sha(audit),'counts':{'scenes':31,'operation_records':12,'operation_parameters':50,'option_quantities':v['alternative_schedule_parameters'],'display_rows':168,'author_checks':v['checks']},'public_assets':[{'path':str(A/'sommer2020-protocol.mjs'),'sha256':sha(A/'sommer2020-protocol.mjs'),'target':'sommer2020-protocol.mjs'}],'bound_files':{str(p):sha(p) for p in files},'scientific_independent_approval':False,'site_imported':False,'published':False,'training_approved':False})
print(json.dumps({'freeze_sha256':sha(A/'package-freeze.json'),'counts':read(A/'package-freeze.json')['counts']}))
