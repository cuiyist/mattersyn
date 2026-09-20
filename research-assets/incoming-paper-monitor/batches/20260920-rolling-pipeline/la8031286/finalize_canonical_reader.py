"""Freeze private Pati proposal after bounded author transport and scope checks."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,re
P=Path(__file__).resolve().parent;C=P/'canonical-proposal/v1';V=P/'public-review-proposal/v1'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not(C/'package-manifest.json').exists()
cm=read(C/'record-manifest.json');rm=read(V/'reader-manifest.json');d=read(P/'source-facts.json');t=read(P/'source-tables.json');i=read(P/'source-inventory.json');rv=read(V/'pati2009.json');sm=read(C/'lossless-source-map.json');sf=read(P/'package-freeze.json');au=read(P/'source-independent-audit/independent-audit.json');cov=read(C/'source-to-field-coverage.json');records={r['record_id']:read(r['path'])for r in cm['records']};checks=[]
def ck(n,ok):checks.append({'check':n,'passed':bool(ok)});assert ok,n
ck('Distinct source audit passed',au['status']=='passed'and not au['open_findings']and au['reviewer']!='/root/backlog_eta')
ck('Source boundary exact',au['source_package_freeze_sha256']==sha(P/'package-freeze.json')==cm['source_freeze_sha256'])
ck('Source audit exact',cm['independent_source_audit_sha256']==sha(P/'source-independent-audit/independent-audit.json'))
for p,h in sf['bound_files'].items():ck('Source '+p,sha(p)==h)
for p,h in au['bound_files'].items():ck('Audit input '+p,sha(p)==h)
for r in cm['records']:ck('Canonical '+r['record_id'],sha(r['path'])==r['sha256'])
for n,h in rm['outputs'].items():ck('Reader '+n,sha(V/n)==h)
ck('Lossless source facts',sm['source_facts']==d);ck('Lossless source tables',sm['source_tables']==t);ck('Lossless inventory',sm['source_inventory']==i)
ck('All58facts/218units/20numericcells',len(cov['facts'])==58 and len(cov['source_units'])==218 and len(cov['table_cells'])==20 and all(x['canonical_bindings']for x in cov['source_units']))
for sol in['ethanol','propanol','butanol']:
 r=records['pati-2009-'+sol+'-route'];ops={o['id']:o for o in r['operations']}
 ck(sol+' route8steps',len(ops)==8 and'diagnostic'not in ops)
 ck(sol+' stock concentrations',[s['concentrations']['reported_stock_concentration']['value']for s in r['stocks']]==[0.1,0.4])
 ck(sol+' source stock IDs',[s['id']for s in r['stocks']]==[sol+'-nitrate-stock',sol+'-tea-stock'])
 ck(sol+' two100mLtransfers',ops['drip']['parameters']['nitrate_stock_transferred_volume']['value']==100 and ops['drip']['parameters']['tea_receiving_volume']['value']==100)
 ck(sol+' separate1hhold',ops['poststir']['parameters']['post_precipitation_stirring_duration']['value']==1)
 ck(sol+' 24hbeforeacetone',[o['id']for o in r['operations']][-2:]==['ambient-dry','acetone-wash']and ops['ambient-dry']['parameters']['ambient_drying_duration']['value']==24)
 ck(sol+' unknownwholeaspreparedcomposition',all(p['composition']['value']is None for p in r['products']))
 ck(sol+' noaddedwater/NH4OH',not({m['id']for m in r['materials']}&{'hydrate-water','ammonium-hydroxide','air'}))
cal=records['pati-2009-calcination'];ck('Calcination unknown atmosphere',cal['operations'][0]['environment']['value']is None)
ck('TGA air only',records['pati-2009-tga']['operations'][0]['environment']['value']=='Air (TGA only)')
ck('Calcined source phases only',[(p['source_sample_label'],p['composition']['value'])for p in cal['products']if p['composition']['value']is not None]==[(s+'-calcined','CeO2')for s in['ethanol','propanol','butanol']])
ck('No qualified structure, task or promoted record',all(not r['quality']['requested_tasks']and not r['structure_assets']and r['quality']['review_status']=='imported_unreviewed'and'collection'not in r for r in records.values()))
ck('All20selectedcrops',rv['counts']['full_page_public_assets']==0 and len(read(V/'reader-bindings-proposal.json')['original_assets'])==20)
ck('No private source path export',not re.search(r'[A-Z]:[\\/]',json.dumps(rv)))
items=[it for s in rv['reader_sections']for it in s['items']]
ck('243 unique reader items',len(items)==243 and len({x['id']for x in items})==243)
ck('All6sections',[s['id']for s in rv['reader_sections']]==['precursors','protocol','structures','properties','intuition','sources'])
ck('Alltenconflicts',rv['evidence_conflicts']==d['conflicts'])
ck('DLS radius/diameter kept',any('radii'in x['text']and'diameters'in x['text']for x in items))
ck('XPS less-than/approximate separate',any(q['canonical_quantity'].get('maximum_exclusive')is True and q['canonical_quantity'].get('maximum')==15 for x in items for q in x['facts'])and any(q['canonical_quantity'].get('approximate')and q['canonical_quantity'].get('value')==15 for x in items for q in x['facts']))
ck('All4printedexpressions',[x['raw_expression']for x in sm['source_facts']['equations']]==[x['raw_expression']for x in d['equations']])
snap=C/'author-input-snapshots';snap.mkdir(exist_ok=True);mapping=[]
inputs={**cm['input_modules'],**{p:h for p,h in rm['input_hashes'].items()if'/recipe-atlas/'in p.replace('\\','/')}}
for p,h in inputs.items():
 ck('Read-only helper '+p,sha(p)==h);dst=snap/(hashlib.sha256(p.encode()).hexdigest()[:10]+'-'+Path(p).name);shutil.copyfile(p,dst);mapping.append({'original_path':p,'sha256':h,'snapshot_path':str(dst),'scope':'Immutable baseline helper bytes; shared Site path may later change.'})
write(C/'author-input-snapshots.json',{'inputs':mapping})
counts={**cm['counts'],**rv['counts']};now=datetime.now(timezone.utc).isoformat()
write(C/'final-author-checks.json',{'author':'/root/backlog_eta','created_at':now,'status':'author_checks_passed_pending_distinct_canonical_reader_audit','checks':checks,'check_count':len(checks),'prior_schema_transport_checks':read(C/'author-validation.json')['check_count'],'reader_pointer_checks':read(V/'author-validation.json')['check_count'],'counts':counts,'manual_author_scope':'Read all58 audited fact claims and quantity definitions, all11 protocol scopes/19 source actions,20 source material definitions,six stocks,22 sample contexts,ten conflicts/eight gaps,four figure assignments,four expressions and exact table/source-unit contracts. Reviewed curated overviews,source-card prose,route/diagnostic/calcination boundaries and typed display. The prior distinct source auditor read/viewed every supplied page/crop; this author pass does not claim a repeated independent page audit or browser review.','not_approved':['training','atomic_model','canonical_independent_review','reader_independent_review','molecular_binding','apparatus_binding','browser','publication']})
(C/'README.md').write_text('''# Pati 2009 — private canonical and reader proposal v1

The proposal binds the complete four-page main and four-page matched SI source package and its passed distinct audit. It contains 19 records: three explicit solvent routes, eleven procedures and five observations. The 35 operation instances represent nineteen distinct source operations; counts do not establish independent physical replicates. All 58 facts, 90 fact quantities, 218 source units, twenty numerical table cells and 36 raw grid cells are preserved. The reader has 243 items, 1,101 typed canonical-field pointers and twenty selected original crops.

Ethanol, 1-propanol and 1-butanol have separate route graphs and six stock formulations. Stock preparation volume is unknown; 100 mL is a transferred quantity. The ammonium-hydroxide filtrate diagnostic is outside each retained-precipitate branch. Alcohol washing and 24 h room-temperature drying precede acetone washing; an additional drying step is not invented. Calcination is a separate source-linked procedure with unknown atmosphere, distinct from TGA in air.

As-prepared whole-powder composition remains unknown despite local CeO2 microscopy. The source calcined cubic-phase claim, solution DLS, BET-equivalent diameters, thermal inferences and four exposure-dependent XPS surface contexts remain separate. The source radius/diameter conflict, printed TEA formula, spin/spectrum labels, calibration value and area-expression inconsistencies are retained without repair. No missing complementary valence fraction, atomic coordinates, product model or exact training pair is generated.

The field and source-item maps identify every canonical and reader pointer. Lossless source maps are private provenance, not public payloads. The original asset allowlist includes selected crops only; raw text and full pages remain local. Immutable helper snapshots preserve the current validation/rendering contract without requiring a future mutable Site checkout to keep those bytes.

No training tasks, model approval, promotion, visual binding, mounted browser validation or publication are granted by this author package. Distinct canonical/reader review is the next gate. No Site or ledger was modified.
''',encoding='utf-8')
bound={str(p):sha(p)for folder in[C,V]for p in sorted(folder.rglob('*'))if p.is_file()}
for p in[P/n for n in['package-freeze.json','source-facts.json','source-tables.json','source-inventory.json','page-coverage.json','original-assets-manifest.json','source-independent-audit/independent-audit.json','build_canonical_proposal.py','build_reader_proposal.py','finalize_canonical_reader.py']]:bound[str(p)]=sha(p)
for a in read(P/'original-assets-manifest.json')['assets']:bound[a['path']]=a['sha256']
write(C/'package-manifest.json',{'schema':'mattersyn-private-canonical-reader-freeze/1','source_id':'pati2009','revision':1,'author':'/root/backlog_eta','created_at':now,'status':'frozen_for_distinct_canonical_reader_audit','source_freeze_sha256':sha(P/'package-freeze.json'),'source_revision':au['source_revision'],'source_audit_sha256':sha(P/'source-independent-audit/independent-audit.json'),'canonical_manifest_sha256':sha(C/'record-manifest.json'),'reader_sha256':sha(V/'pati2009.json'),'reader_manifest_sha256':sha(V/'reader-manifest.json'),'counts':counts,'bound_files':bound,'training_eligible':False,'atomic_models_approved':False,'source_records_promoted':False,'published':False})
print(json.dumps({'package':sha(C/'package-manifest.json'),'record_manifest':sha(C/'record-manifest.json'),'reader':sha(V/'pati2009.json'),'final_checks':len(checks),'bound_files':len(bound),'counts':counts}))
