"""Freeze the complete private author proposal after the distinct source pass."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import json,hashlib,shutil,re
P=Path(__file__).resolve().parent;C=P/'canonical-proposal/v1';V=P/'public-review-proposal/v1'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not(C/'package-manifest.json').exists()
cm=read(C/'record-manifest.json');rm=read(V/'reader-manifest.json');src=read(P/'source-facts.json');tables=read(P/'source-tables.json');cov=read(C/'source-to-field-coverage.json');rv=read(V/'matuhina2023.json');sm=read(C/'lossless-source-map.json');sf=read(P/'package-freeze.json');au=read(P/'source-independent-audit/independent-audit.json')
checks=[]
def ck(label,ok):checks.append({'check':label,'passed':bool(ok)});assert ok,label
ck('Distinct source audit passed',au['status']=='passed'and not au['open_findings']and au['reviewer']!='/root/backlog_eta')
ck('Source audit binds effective revision2',au['source_revision']==2 and au['source_package_freeze_sha256']==sha(P/'package-freeze.json'))
ck('Canonical source pass exacthash',cm['independent_source_audit_sha256']==sha(P/'source-independent-audit/independent-audit.json')and cm['source_freeze_sha256']==sha(P/'package-freeze.json'))
for p,h in sf['bound_files'].items():ck('Frozen source '+p,sha(p)==h)
for p,h in au['bound_files'].items():ck('Independent source input '+p,sha(p)==h)
for r in cm['records']:ck('Canonical record '+r['record_id'],sha(r['path'])==r['sha256'])
for n,h in rm['outputs'].items():ck('Reader file '+n,sha(V/n)==h)
for k,v in src.items():ck('Lossless source field '+k,sm[k]==v)
ck('Lossless all7tables',sm['tables']==tables['tables'])
ck('Source units353',len(cov['source_units'])==353 and all(x['canonical_bindings']for x in cov['source_units']))
ck('All321table fields',len(cov['table_cells'])==321 and len({x['source_cell_id']for x in cov['table_cells']})==321)
records={r['record_id']:read(r['path'])for r in cm['records']}
for protocol in src['protocols']:
 record=records['matuhina-2023-'+protocol['id']]
 ck('Distinct operation IDs '+protocol['id'],[o['id']for o in protocol['operations']]==[o['id']for o in record['operations']])
 for o,co in zip(protocol['operations'],record['operations']):
  ck('Retained original output count '+o['id'],len(o['outputs'])==len(co['outputs']))
  ck('Operation evidence '+o['id'],len(co['evidence'])==len(o['evidence']))
  ck('Missing conditions retained '+o['id'],all(x in record['quality']['missing_fields']for x in o['missing_fields']))
route=records['matuhina-2023-hot-injection-series'];expected=['nc150','nc180-07','nc180-05','nc180-035','nc200']
ck('Five paired conditions only',[o['id']for o in route['condition_options']]==expected)
for sc,opt in zip(src['sample_contexts'][:5],route['condition_options']):
 for k in['injection_temperature','reported_loading_Mn_Cs','cs_oleate_aliquot']:ck(sc['id']+' '+k,opt['parameters'][k]['value']==sc[k]['value']and opt['parameters'][k]['unit']==sc[k]['unit'])
ck('No exact or promoted record',all(not r['quality']['requested_tasks']and not r['structure_assets']and r['quality']['review_status']=='imported_unreviewed'and'collection'not in r for r in records.values()))
ck('No fullpages in reader allowlist',rv['counts']['full_page_public_assets']==0 and len(read(V/'reader-bindings-proposal.json')['original_assets'])==30)
ck('No source disk paths exported',not re.search(r'[A-Z]:[\\/]',json.dumps(rv)))
items=[i for s in rv['reader_sections']for i in s['items']]
ck('All380readeritems',len(items)==380 and len({i['id']for i in items})==380)
ck('Six required sections',[s['id']for s in rv['reader_sections']]==['precursors','protocol','structures','properties','intuition','sources'])
ck('AllsourceC13retained',any('C13:'in q.get('qualifier','')for i in items for q in i['facts']))
ck('Tauc left/right text bound',any('left' in i['text'].lower()and'right'in i['text'].lower()and'1/2'in i['text']for i in items if i['id']=='source-equations-tauc-axes'))
inputfiles={**cm['input_modules'],**{p:h for p,h in rm['input_hashes'].items()if '/recipe-atlas/'in p.replace('\\','/')}}
snap=C/'author-input-snapshots';snap.mkdir(exist_ok=True);mapping=[]
for original,h in inputfiles.items():
 path=Path(original);ck('Read-only helper hash '+original,sha(path)==h);dst=snap/(hashlib.sha256(original.encode()).hexdigest()[:10]+'-'+path.name);shutil.copy2(path,dst);mapping.append({'original_path':original,'sha256':h,'snapshot_path':str(dst),'scope':'Exact helper/renderer reference at author validation; not a new runtime or Site modification.'})
write(C/'author-input-snapshots.json',{'inputs':mapping})
counts={**cm['counts'],**rv['counts']};now=datetime.now(timezone.utc).isoformat()
write(C/'final-author-checks.json',{'author':'/root/backlog_eta','created_at':now,'status':'author_checks_passed_pending_distinct_canonical_reader_audit','checks':checks,'check_count':len(checks),'prior_schema_transport_checks':read(C/'author-validation.json')['check_count'],'reader_pointer_checks':read(V/'author-validation.json')['check_count'],'counts':counts,'manual_author_scope':'Source extraction author read all26pages and viewed all30selectedcrops before sourcefreeze. Reader overviews,20figure descriptions, operation boundaries, paired preparation options and source conflict display were written/reviewed in this canonical pass. Independent source audit passed separately; this is not a distinct canonical, visual or browser review.','not_approved':['training','atomic_model','canonical_independent_review','reader_independent_review','molecular_binding','apparatus_binding','browser','publication']})
(C/'README.md').write_text('''# Matuhina 2023 — private canonical and reader proposal v1

This proposal binds complete main/SI source revision 2 and its passed distinct audit. The 21 records contain one synthesis route with five paired conditions, thirteen procedures and seven observations. They retain 39 operations, 55 material slots, five stocks with fifteen components, and 678 measurement/context entries. Record and specimen-context counts are not independent experiment counts.

The six-section reader contains 380 items and 1,398 exact typed-field pointers. All 62 source facts, 186 fact quantities, 353 inventory units and seven tables are mapped. The 321 table fields comprise 301 printed body cells and twenty repeated group-heading metadata fields. All thirty selected original crops are proposed; no whole page is attached.

Source loading labels are not recalculated from unknown stock molarity. Injection alternatives are five explicitly paired conditions; antisolvents are separate trials. Films, dispersions, destructive ICP digests, stability controls, DFT models and the unencapsulated device have separate scopes. The literal structural-table zero occupancies, Wyckoff discrepancies, missing angles and absent 200 °C coordinates remain unqualified. All thirteen source conflicts, including the left/right Tauc typography and lowest FWHM temperature discrepancy, remain explicit.

The source-owner map and field-coverage map provide exact record/pointer entrypoints. The operation-quantity-scope file distinguishes action parameters from alternative acquisition conditions. The lossless source map is private provenance, not a public reader payload. Raw source files and full pages remain local under the established exclusion policy.

No training task, atomic model, source promotion, visual binding, browser rendering or publication is approved by this author package. A distinct canonical/reader auditor must review these exact bytes. No shared Site or ledger was modified.
''',encoding='utf-8')
bound={}
for folder in[C,V]:
 for path in sorted(folder.rglob('*')):
  if path.is_file():bound[str(path)]=sha(path)
for path in[P/'package-freeze.json',P/'source-facts.json',P/'source-tables.json',P/'source-inventory.json',P/'page-coverage.json',P/'original-assets-manifest.json',P/'source-independent-audit/independent-audit.json',P/'build_canonical_proposal.py',P/'build_reader_proposal.py',Path(__file__)]:bound[str(path)]=sha(path)
for a in read(P/'original-assets-manifest.json')['assets']:bound[a['path']]=a['sha256']
manifest={'schema':'mattersyn-private-canonical-reader-freeze/1','source_id':'matuhina2023','revision':1,'author':'/root/backlog_eta','created_at':now,'status':'frozen_for_distinct_canonical_reader_audit','source_freeze_sha256':sha(P/'package-freeze.json'),'source_revision':2,'source_audit_sha256':sha(P/'source-independent-audit/independent-audit.json'),'canonical_manifest_sha256':sha(C/'record-manifest.json'),'reader_sha256':sha(V/'matuhina2023.json'),'reader_manifest_sha256':sha(V/'reader-manifest.json'),'counts':counts,'bound_files':bound,'training_eligible':False,'atomic_models_approved':False,'source_records_promoted':False,'published':False}
write(C/'package-manifest.json',manifest)
print(json.dumps({'package':sha(C/'package-manifest.json'),'record_manifest':sha(C/'record-manifest.json'),'reader':sha(V/'matuhina2023.json'),'final_checks':len(checks),'bound_files':len(bound),'counts':counts}))
