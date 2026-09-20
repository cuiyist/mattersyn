from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
A=Path(__file__).resolve().parent; P=A.parents[1]; C=P/'canonical-proposal/v1'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text('utf-8'))
def save(n,v): (A/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf-8')
assert not (A/'package-freeze.json').exists()
audit=P/'source-independent-audit/independent-audit-v2.json'
assert read(audit)['status']=='passed'
b=read(A/'canonical-bindings.json'); assert b['record_manifest_sha256']==sha(C/'record-manifest.json')
for x in b['bindings']: assert sha(Path(x['record_path']))==x['record_sha256']
v=read(A/'author-validation.json'); assert v['operations']==39 and v['canonical_parameters']==67 and v['total_display_rows']==168
preview=read(A/'preview-manifest.json')
preview['visual_review_status']='All 39 scenes inspected on 10 contact sheets; final precursor-charge, retained-pellet and edge-coupled-device previews reopened.'
save('preview-manifest.json',preview)
save('author-visual-review.json',{'author':'/root','at':datetime.now(timezone.utc).isoformat(),'status':'author_checked_pending_independent_audit','source_scope':'Root visually read complete main experimental pages 2 and 3. The separately passed 26-page source audit supports the broader contextual claims; this is not a root full-source rereading.','original_pages_viewed':[2,3],'scene_count':39,'viewed_contacts':[{'path':x['path'],'sha256':sha(A/x['path'])} for x in preview['contacts']],'final_previews_reopened':['cs-load','nc-centrifuge','lsc-measure'],'changes_before_first_freeze':['Solid precursor charge and retained precipitates explicitly depicted; no pellet in failed hexane-only trial.','Edge-coupled device shown in side view with glass edge directly contacting diode and surrounding opaque cover.','Source data feed the analysis icon; geometry is explanatory.'],'browser_scope':{'private_preview':True,'actual_stage_selections':39,'visible_condition_rows':168,'selected_heading_and_svg_titles_match':True,'console_errors':0,'responsive_check':{'width':390,'height':844,'document_width':375,'scroll_width':375,'scenes':['nc-grow-quench','lsc-measure']},'integrated_site_checked':False},'independent_scientific_approval':False})
(A/'README.md').write_text('''# Matuhina 2023 apparatus proposal

39 source-specific stages across 14 canonical records. This is a root-authored proposal, pending distinct independent apparatus approval and later integrated-site review. The source revision 2 is independently passed; canonical/reader v1 review is a separate gate.

The module reads all 67 operation quantities directly from immutable canonical objects. The five demonstrated synthesis-condition options are displayed, grouped by their source label, at injection and the subsequent five-second hold. This is 30 quantity appearances, not ten independent experiments. There are 168 display rows in total. No Cartesian temperature/aliquot grid, unreported pressure, numerical overnight duration or force conversion is inferred.

Apparatus scenes distinguish solid loading, degassing, addition, injection, ice-water quenching, separation, unsuccessful precipitation, vacuum desiccation, film/grid preparation, destructive digestion, diffraction, spectroscopy, aging, calculation and edge-coupled device measurement. Heavy water belongs to probe generation. Film, dispersion, computed structure and aged-specimen contexts remain separate. SI coordinate tables are retained but do not yet constitute an approved interactive atomic model.

Only `matuhina2023-protocol.mjs` is proposed for website import. All original full-page source images stay local. Geometry, colors and particle symbols are explanatory; no micrograph, spectrum or atomic structure is synthesized. Browser receipt covers this private preview, not the integrated website.
''','utf-8')
extra=[P/'package-freeze.json',audit,C/'package-manifest.json',C/'record-manifest.json',P/'public-review-proposal/v1/matuhina2023.json']+list({Path(x['record_path']) for x in b['bindings']})
files=[p for p in A.rglob('*') if p.is_file() and p.name!='package-freeze.json' and '__pycache__' not in p.parts]+extra
save('package-freeze.json',{'schema':'mattersyn-private-apparatus-freeze/1','source_id':'matuhina2023','doi':'10.1021/acsanm.2c04342','author':'/root','at':datetime.now(timezone.utc).isoformat(),'status':'frozen_pending_distinct_independent_audit','source_freeze_sha256':sha(P/'package-freeze.json'),'source_audit_sha256':sha(audit),'canonical_package_sha256':sha(C/'package-manifest.json'),'canonical_audit_status_at_freeze':'pending_separate_review','counts':{'scenes':39,'operation_records':14,'operation_parameters':67,'option_quantity_appearances':v['alternative_schedule_parameters'],'display_rows':168,'author_checks':v['checks']},'public_assets':[{'path':str(A/'matuhina2023-protocol.mjs'),'sha256':sha(A/'matuhina2023-protocol.mjs'),'target':'matuhina2023-protocol.mjs'}],'bound_files':{str(p):sha(p) for p in sorted(set(files))},'scientific_independent_approval':False,'site_imported':False,'published':False,'training_approved':False})
print(json.dumps({'freeze_sha256':sha(A/'package-freeze.json'),'counts':read(A/'package-freeze.json')['counts']}))
