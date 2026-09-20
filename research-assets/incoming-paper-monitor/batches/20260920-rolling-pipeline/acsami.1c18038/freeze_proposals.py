"""Freeze the private Lian canonical/reader author package for distinct review."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
P=Path(__file__).resolve().parent;C=P/'canonical-proposal'/'v1';V=P/'public-review-proposal'/'v1'
assert not(C/'package-manifest.json').exists(),'Frozen proposals require a preserved revision.'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
source=read(P/'package-freeze.json');ap=P/'source-independent-audit'/'independent-audit-v2.json';audit=read(ap)
assert audit['status']=='passed'and not audit['open_findings']and audit['proposal_freeze_sha256']==sha(P/'package-freeze.json')
for p,h in source['bound_files'].items():assert sha(p)==h,p
for p,h in audit['bound_files'].items():assert sha(p)==h,p
cm=read(C/'record-manifest.json');rm=read(V/'reader-manifest.json');review=read(V/'lian2021.json');records={x['record_id']:read(x['path'])for x in cm['records']}
assert len(records)==16 and sum(len(r['operations'])for r in records.values())==21
assert all(r['quality']['review_status']=='imported_unreviewed'and not r.get('collection')and r['quality']['requested_tasks']==[]and r['structure_assets']==[]for r in records.values())
assert all(sha(x['path'])==x['sha256']for x in cm['records'])and all(sha(V/n)==h for n,h in rm['outputs'].items())
assert review['counts']['source_table_cells']==891 and review['counts']['typed_reader_fields']==1465 and not review['training_eligible']and not review['source_review_promoted']
notes='''# Lian 2021 — private canonical and reader proposal v1

The supplied eight-page main article and 26-page SI PDF passed a distinct scientific source audit of extraction revision 2. That audit binds the original source hashes, all 57 claims, 134 fact quantities, 891 table cells and 53 selected original crops. The cited crystal ZIP and scintillation MP4 are not among the supplied local attachments and were not downloaded.

This proposal contains 16 records: two literature routes, one explicit stoichiometric variant, six supporting procedures and seven observation/context records. It maps all 21 operations, 45 material slots, five stock formulations, 44 record-local sample/model contexts and 1,149 measurement/context entries. These are data-model counts, not counts of separately synthesized batches. All 167 uniquely identified inventory units and every original table cell have exact canonical pointers. Raw tokens, uncertainty definitions and printed scales remain in the curated source map.

Bulk A, (C12H28N)2SbCl5, and bulk B, (C12H28N)SbCl4, remain distinct from A nanocrystals, dried powder, settling colloid, five phosphor/nanocrystal/PS blend contexts and the precursor spin-coated film. Four preparation-to-nominal-product links are explicit from their procedures; they do not create a universal same-specimen characterization join. The nanocrystal stock solvent charge is not a calibrated final solution volume, so the 500 µL injected aliquot is not converted into exact salt millimoles.

The five composite-film ratios retain relative mass parts, including the pure-component controls, without absolute loadings. The peeled composite state excludes the removed glass support while its operation retains glass as an input. The spin-coated film keeps its support and its reported 1000 µL DMF charge and 80 °C/30 min annealing conditions; composite-film missingness is explicitly qualified rather than applied to that route. The exact blend ratio of the β-tested composite remains unknown.

Table S1 cells use the printed A/B column headings to associate each value with bulk-a-crystal or bulk-b-crystal, while the table definition retains its two-compound scope. Tables S6–S9 describe measured bulk non-hydrogen coordinates and displacement parameters; they do not supply complete hydrogen/occupancy data, a measured nanocrystal CIF or relaxed DFT coordinates. The two independent B Sb centres and unresolved main-text distortion/mean-distance scope remain explicit. Both reported space groups are centrosymmetric. No ordered atomic model or exact recipe–structure training pair is admitted.

The reader contains five academic sections plus Sources and limitations, with 224 items and exact transport of all 1,465 typed canonical fields. All 34 page-coverage entries, 30 reference entries, figure/table/equation scopes and four source conflicts are preserved. Fifty-three selected crops are proposed; complete text caches, full-page renders and original PDFs remain private and absent from reader attachment paths. Figure scope and section placement were checked against the passed source inventory before freezing.

The source-defined non-emissive B outcome is not a measured zero PLQE. Bulk 96.8% PLQE, dried-nanocrystal 89.3% PLQE, colloidal settling and dry/bulk storage observations remain distinct. Calculated PBE/HSE06 gaps, transition-probability arguments and fitted activation/phonon parameters remain model outputs. No raw plot arrays, SAED pattern, complete atomic model or unreported synthesis condition is invented.

All records remain imported_unreviewed, without collection promotion and with empty requested_tasks. Canonical/reader independent approval, molecular and apparatus bindings, atomic-model qualification, browser checks, Site import and publication remain separate gates. No training export or publication is approved by this author freeze.
'''
(C/'proposal-notes.md').write_text(notes,encoding='utf-8')
(V/'README.md').write_text('Private Lian reader: `lian2021.json`. Source-item coverage binds all canonical typed fields; reader-bindings-proposal maps selected original crops and future material/stock/protocol slots. Source audit passed separately. Canonical/reader, visual/model, browser, training and publication approval remain pending. No complete-source payload is proposed for public attachment.\n',encoding='utf-8')
paths=[p for root in [C,V]for p in root.iterdir()if p.is_file()]
paths += [P/'build_canonical_proposal.py',P/'build_reader_proposal.py',Path(__file__),P/'package-freeze.json',ap,P/'source-correction-history.json',P/'source-facts.json',P/'source-inventory.json',P/'source-tables.json',P/'page-coverage.json',P/'original-assets-manifest.json']
paths += [Path(a['path'])for a in read(P/'original-assets-manifest.json')['assets']]
paths += [Path(p)for p in cm['input_modules']]+[Path(p)for p in rm['input_hashes']]
bound={str(p.resolve()):sha(p)for p in sorted(set(paths),key=str)}
manifest={'schema':'mattersyn-private-canonical-reader-freeze/1','source_id':'lian2021','doi':'10.1021/acsami.1c18038','version':1,'author':'/root/backlog_eta','frozen_at':datetime.now(timezone.utc).isoformat(),'status':'author_proposal_source_audit_passed_canonical_reader_audit_pending','source_generation':1,'bundle_sha256':source['bundle_sha256'],'source_freeze_sha256':sha(P/'package-freeze.json'),'source_audit':{'path':str(ap),'sha256':sha(ap),'reviewer':audit['auditor'],'status':audit['status'],'scope':'All supplied 8 main + 26 SI PDF pages, all 53 crops, 57 source facts and all 891 typed table cells; no canonical/model approval.'},'canonical_record_manifest_sha256':sha(C/'record-manifest.json'),'reader_manifest_sha256':sha(V/'reader-manifest.json'),'reader_sha256':sha(V/'lian2021.json'),'canonical_counts':cm['counts'],'reader_counts':review['counts'],'author_checks':{'canonical':read(C/'author-validation.json')['check_count'],'reader':read(V/'author-validation.json')['check_count']},'bound_files':bound,'bound_file_count':len(bound),'independent_canonical_reader_approval':False,'training_approved':False,'visual_model_approved':False,'browser_approved':False,'site_imported':False,'published':False,'publication_exclusions':['Original PDFs','Complete-source payload manifest','All private/text files','All source-render full-page images','Complete-page attachments or local source paths'],'scope_notes_path':str(C/'proposal-notes.md')}
write(C/'package-manifest.json',manifest)
print(json.dumps({'manifest':str(C/'package-manifest.json'),'sha256':sha(C/'package-manifest.json'),'reader_sha256':sha(V/'lian2021.json'),'canonical_manifest_sha256':sha(C/'record-manifest.json'),'bound_files':len(bound),'checks':manifest['author_checks']}))
