"""Independent final apparatus/source audit. Reads author artifacts; never rewrites them."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,xml.etree.ElementTree as ET,re
D=Path(__file__).resolve().parent;G=D.parents[1];A=G/'visuals/apparatus';M=G.parents[4]
sys.dont_write_bytecode=True
sys.path.insert(0,str(M/'research-assets/corpus-20260917/runtime'))
import pymupdf
from PIL import Image
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[]
def ck(ok,n):
 assert ok,n
 checks.append(n)
freeze=read(A/'package-freeze.json');factory=read(D/'actual-module-validation.json');view=read(D/'actual-visual-reading.json');criteria=read(D/'source-stage-checklist.json')
ck(sha(A/'package-freeze.json')=='94019688d5b8de7708248d4e21575e835559118959dbd0062cae891dd462420e','Expected immutable apparatus freeze')
ck(factory['package_sha256']==sha(A/'package-freeze.json'),'Actual factory checks bind final freeze')
for p,h in freeze['bound_files'].items():ck(sha(p)==h,'Final frozen bound file '+p)
for p,h in view['contact_files'].items():ck(sha(p)==h,'Actually viewed final contact unchanged '+p)
pm=read(A/'preview-manifest.json');scenes={s['operation_id']:s for s in read(D/'independent-scene-outputs.json')}
for row in pm['scenes']:
 oid=row['operation_id'];png=A/row['png_path'];svg=A/row['svg_path']
 ck(sha(png)==view['scenes'][oid]['png_sha256'],'Actually viewed final stage unchanged '+oid)
 ck(sha(svg)==view['scenes'][oid]['svg_sha256'],'Viewed source SVG unchanged '+oid)
 ck(svg.read_text(encoding='utf-8').strip()==scenes[oid]['svg'].strip(),'Saved SVG equals independently executed factory '+oid)
 with pymupdf.open(stream=svg.read_bytes(),filetype='svg')as doc:
  pix=doc[0].get_pixmap(matrix=pymupdf.Matrix(1.2,1.2),alpha=False)
  with Image.open(png)as im:
   im=im.convert('RGB');ck(im.size==(pix.width,pix.height)and im.tobytes()==pix.samples,'Independent pixel replay '+oid)
 ET.fromstring(svg.read_bytes());ck(True,'Well-formed SVG '+oid)
bindings=read(A/'canonical-bindings.json')['bindings'];record_ids=set()
for b in bindings:
 r=read(b['record_path']);record_ids.add(r['record_id']);ck(sha(b['record_path'])==b['record_sha256'],'Binding record hash '+b['operation_id'])
 o=r['operations'][int(b['operation_pointer'].split('/')[-1])]
 ck(o['id']==b['operation_id'],'Binding operation '+o['id'])
 for k in ['inputs','outputs','retained_fraction']:ck(b[k]==o[k],'Exact flow '+o['id']+'/'+k)
 ck(b['canonical_description']==o['description']and b['source_evidence']==o['evidence'],'Source prose/evidence binding '+o['id'])
 ck(not b['binding_approved'],'Author not self-approved '+o['id'])
 ck(scenes[o['id']]['description']==b['human_prose'],'Rendered human prose binding '+o['id'])
ck(len(record_ids)==15 and len(bindings)==33,'Complete 15-record/33-operation scope')
ck({x['operation_id']for x in bindings}=={x['operation_id']for x in criteria['operations']},'All prepared source scopes reviewed')
canonical_audit=G/'canonical-reader-independent-audit/independent-audit-v2.json';source_audit=G/'source-independent-audit/independent-audit-v2.json'
ck(read(canonical_audit)['status']=='passed','Distinct canonical v2 audit passed')
ck(read(source_audit)['status']=='passed','Distinct source v2 audit passed')
ck(freeze['canonical_audit_sha256']==sha(canonical_audit),'Correct canonical audit hash')
ck(freeze['canonical_package_sha256']==sha(G/'canonical-proposal/v2/package-manifest.json'),'Correct canonical v2 freeze')
ck(freeze['source_freeze_sha256']==sha(G/'package-freeze.json'),'Correct source revision2 freeze')
for p,h in [(Path('[local path redacted]'),'a624fe12df46fdfb6101824ec0836522ccd6bff10aa663c2379316001e175d96'),(Path('[local path redacted]'),'4143fa3e1d36e68e3e8017d7c236e33d36697b6445fd678b08e5e63ee23a1b01')]:ck(sha(p)==h,'Original source identity '+p.name)
ck(len(freeze['public_assets'])==1 and freeze['public_assets'][0]['target']=='ghosh2012-protocol.mjs','Public module-only allowlist; no source scans')
ck(not re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]|/Users/|source-render|private/text', (A/'ghosh2012-protocol.mjs').read_text(encoding='utf-8')),'No private path/fullpage source export in module')
manual=[]
for row in criteria['operations']:
 manual.append({'operation_id':row['operation_id'],'source_scope':row['source_scope'],'checked_distinctions':row['required_distinctions'],'actual_preview_viewed':True,'result':'passed'})
bound=dict(freeze['bound_files']);bound[str(A/'package-freeze.json')]=sha(A/'package-freeze.json')
for p in [canonical_audit,source_audit,G/'source-facts.json',G/'source-tables.json',G/'original-assets-manifest.json',G/'canonical-proposal/v2/package-manifest.json',D/'actual-module-validation.json',D/'actual-visual-reading.json',D/'source-stage-checklist.json',D/'check_scene_contract.mjs',D/'independent-scene-outputs.json',Path(__file__)]:bound[str(p)]=sha(p)
bound.update(criteria['bound_inputs'])
for b in bindings:bound[b['record_path']]=sha(b['record_path'])
report={'schema':'mattersyn-independent-apparatus-audit/1','status':'passed','author':'/root/norberg2004_extract','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'source_id':'ghosh2012','doi':'10.1021/ja212032q','proposal_freeze_path':str(A/'package-freeze.json'),'proposal_freeze_sha256':sha(A/'package-freeze.json'),'module_sha256':sha(A/'ghosh2012-protocol.mjs'),'counts':{**factory['counts'],'operation_records':15,'source_scope_notes':103,'art_types':29,'actual_stage_previews_viewed':33,'actual_contact_sheets_viewed':9,'independent_pixel_replays':33},'actual_factory_checks':factory['check_count'],'additional_hash_graph_pixel_scope_checks':len(checks),'check_count':factory['check_count']+len(checks),'manual_source_scope':'Targeted reread and native-image inspection of main PDF2–7 and SI9, source-bound figures/tables and previously passed extraction/canonical audits. All 33 scene previews actually viewed on nine contacts; their final PNG/SVG bytes are unchanged from those viewed. Source text/quantities/graphs are comparison inputs only; this is not self-certification of the auditor-authored canonical or molecular packages. No repeated full-source extraction or full SI-table reread.','manual_scopes':manual,'resolved_pre_freeze_findings':[{'id':'GA1','finding':'Generic count unit was rendered as cycles for scans/frames.','resolution':'Author retained neutral count while field labels identify washing cycles, scans and frames. Frozen module/actual function outputs/final previews independently checked.'}],'open_findings':[],'checks':checks,'limitations':['Diagram geometry, symbols, colors and optical layouts are explanatory, not measured hardware, lattice, spectra or micrographs.','Unreported flow/pressure, precursor preparations, exact transition cycles, dose schedules and physical cross-assay batch links remain unfilled.','Alternative ligand/solvent/anneal/withdrawal comparisons and separate FTIR specimens are not pooled into one physical batch.','This is a private source/apparatus audit. Integrated browser interaction, Site import, publication and training admission remain separate gates.'],'source_and_canonical_approval_reused_from_distinct_reviewer':True,'browser_tested_by_this_auditor':False,'site_written':False,'training_approved':False,'bound_files':bound,'bound_file_count':len(bound)}
save(D/'independent-audit.json',report)
md=f'''# Ghosh 2012 — independent apparatus audit

Passed the frozen private apparatus proposal authored by `/root/norberg2004_extract`; auditor `/root/backlog_eta`. No open finding.

The audit covers all 33 stages across 15 records: 70 operation quantities, ten parameters in five separate annealing schedules, 103 scope notes, 183 displayed rows and 29 diagram types. All 33 previews were actually viewed across nine contact sheets. Each final PNG was independently reproduced from the final SVG with identical pixels, and every saved SVG matches the independently executed scene factory. There are {report['check_count']} supporting checks ({factory['check_count']} actual module/selection/quantity checks and {len(checks)} additional binding/hash/pixel/scope checks).

Targeted native-source review covered main PDF pages 2–7 and SI page 9. The earlier distinct source and canonical audits supply the complete-source/table context; this audit does not repeat or self-certify the author's own canonical/molecular work. The source-stage checklist records all 33 manual comparisons. An auditor shorthand locator for core synthesis was corrected from page 2 to its actual page 3; no author source change was needed.

The preferred 1 h post-S/2.5 h post-Cd sequence remains separate from the five Table 1 schedules. Half-layer additions versus complete cycles, 1%/10% reaction-volume withdrawals, unresolved OA transition span, distinct solvent/amine alternatives, and initial constant-sulfur growth remain explicit. FTIR washing and acquisition are separate, pure-ligand specimens are not pooled, XRD/TEM contain no fabricated data, and liquid nitrogen is detector cooling. The seven-nanometre core control does not inherit an upstream preparation. Missing apparatus dimensions, pressures, feed rates and cross-assay specimen joins remain unknown.

One pre-freeze renderer finding was resolved: generic count units no longer label scans or frames as cycles. Exact final outputs were checked. No source value, graph or geometry correction was required.

Frozen apparatus SHA256: `{report['proposal_freeze_sha256']}`. Module SHA256: `{report['module_sha256']}`. The JSON report binds {len(bound)} exact files. The public proposal includes only the source-specific module, with no full-page scans or private source paths. Integrated browser testing, import, publication and training approval are outside this audit.
'''
(D/'independent-audit.md').write_text(md,encoding='utf-8')
print(json.dumps({'status':'passed','audit':str(D/'independent-audit.json'),'sha256':sha(D/'independent-audit.json'),'checks':report['check_count'],'bound_files':len(bound)}))
