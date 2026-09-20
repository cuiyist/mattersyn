"""Freeze Sommer private canonical/reader author proposal after distinct source approval."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
P=Path(__file__).resolve().parent;C=P/'canonical-proposal/v1';V=P/'public-review-proposal/v1'
assert not(C/'package-manifest.json').exists(),'Preserve a frozen proposal; use a new revision.'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sf=P/'package-freeze.json';source=read(sf);ap=P/'source-independent-audit/independent-audit-v2.json';audit=read(ap)
assert sha(sf)=='fb2aa081c3c33972454111a4631ffcf944b66f2b78bfec2894564745bccf072b'
assert audit['status']=='passed'and not audit['open_findings']and any(v==sha(sf)for v in audit.values()if isinstance(v,str))
for doc in [source,audit]:
 for p,h in doc['bound_files'].items():assert sha(p)==h,p
cm=read(C/'record-manifest.json');rm=read(V/'reader-manifest.json');rv=read(V/'sommer2020.json');records=[read(x['path'])for x in cm['records']]
assert cm['independent_source_audit_sha256']==sha(ap)
assert len(records)==19 and sum(len(r['operations'])for r in records)==31
assert all(r['quality']['review_status']=='imported_unreviewed'and r['quality']['requested_tasks']==[]and r['structure_assets']==[]and'collection'not in r for r in records)
assert all(sha(x['path'])==x['sha256']for x in cm['records'])
assert all(sha(V/n)==h for n,h in rm['outputs'].items())
assert rv['counts']['source_table_cells']==222 and rv['counts']['selected_original_assets']==20
assert not rv['training_eligible']and not rv['source_review_promoted']and rv['supporting_information']['status']=='declared_locally_unlocated_unverified'
notes='''# Sommer et al. (2020) — private canonical and academic reader proposal v1

The complete supplied 11-page main source passed distinct scientific audit of extraction revision 2. The source review binds 65 facts, 137 fact quantities, all 37 Table 1 rows/222 printed body cells, 20 selected original crops and 332 source inventory units. Its original revision and exact five-category correction history are preserved. The declared Supporting Information remains locally unlocated and unverified; no SI reading or inferred values are claimed.

The proposal contains 19 records: three laboratory synthesis families (microwave, SCF and autoclave), nine supporting procedures and seven observation/context records. Thirty-one source operations are preserved without duplication. The in situ nitrate and ZnO/Al(OH)3 branches remain coupled reaction/measurement procedures. Common powder isolation is a separate procedure linked from each laboratory route and applies to separate powders, never a pooled batch. The autoclave route links the explicitly shared laboratory nitrate/base preparation.

Sixty-two record-local material slots map the 28 source identities. The seven stocks have 23 constituent slots. The nested microwave/base formulations display the already prepared nitrate stock’s constituents without claiming new nitrate/water charges. The 20 mL laboratory water charge remains distinct from an asserted final volume; the in situ stock is a separately reported 30.0 mL solution. Only the 1.00 mL NaOH aliquot belongs to the NaOH-stock source entry; 0.480 M Zn and 0.960 M Al belong to the postmix reaction. Water and ethanol grades, specified hydrates and unresolved aqueous speciation stay separate.

Thirty-nine condition options comprise the 37 Table 1 rows and two alternative microwave heating profiles. Each named row retains the NaOH concentration as printed, its unresolved in situ concentration basis, temperature, ratio, total time and dwell. The source’s approximate SCF one-minute entry and separate zero dwell are preserved. Autoclave day units override the minute column heading as printed. In situ 0–40 min ranges and D-series 3.3 min observations are not invented fixed synthesis endpoints. Microwave ramp totals, SCF S2 380/450 °C and ACS 17 days/2.5 weeks are unresolved, not silently reconciled.

All claims and quantities have exact canonical pointers. Table sample-label cells and all 185 nonlabel data cells are individually linked. Process specifications, source models, cited ranges and physical observations are separately labeled. The added 150–350 °C ZnO range is cited prior-work context, never a current D2 recipe. Named M/A/S/I quantities retain their specific specimen scope. Record-local context counts do not count unique physical batches; no universal same-aliquot link is verified.

Structural results retain phase fractions, parenthetic uncertainties, polymodal A1/A2 sizes and original TEM/model scopes. Laboratory positions/occupancies were fixed to literature; the in situ defect formula lacks its SI parameter table. Neither gives a complete new measured product CIF. All 13 source conflict/qualification groups remain visible, including Figure 11 colors and sample/time labels, Figure 6 seconds/minutes, Figure 4b precursor legend, M2’s unquantifiable trace AlOOH, coordination wording and conclusion size range. The optical equation retains its printed multiplication and x=1/2; unlabeled band-gap bars are not converted to exact numeric labels.

The academic reader has five topical sections plus Sources and limitations, with an overview for each and explicit source-specific operation/figure prose. All canonical typed fields, operation/material/stock/specimen contexts, 14 original figure contexts, seven expressions, 65 references and source limitations are mapped. Its 20 proposed public attachments are selected original excerpts. Full pages, complete source text and local source paths are excluded from attachment fields. Public import and visual/browser validation have not occurred.

All records remain imported_unreviewed with empty requested_tasks, no collection promotion and no atomic structure assets. Independent canonical/reader review, molecular/component and apparatus bindings, visual model qualification, browser checks and publication remain separate gates. This package was authored only in this paper directory; no shared Site, ledger, source PDF, memory or GitHub state was changed.
'''
(C/'proposal-notes.md').write_text(notes,encoding='utf-8')
(V/'README.md').write_text('Private Sommer reader: sommer2020.json. Complete supplied-main source revision 2 passed independent audit; SI remains unlocated. Canonical/reader, visual, integration/browser and publication approval remain separate. All 20 attachment candidates are selected original crops; no source page scans or complete source payloads are proposed publicly.\n',encoding='utf-8')
snap=C/'input-snapshots';snap.mkdir(exist_ok=True);mapping={}
for p in [Path(p)for p in cm['input_modules']]+[S for S in [P/'build_canonical_proposal.py',P/'build_reader_proposal.py']]:
 dst=snap/p.name;shutil.copy2(p,dst);assert sha(p)==sha(dst);mapping[str(p)]={'snapshot_path':str(dst),'sha256':sha(dst)}
write(C/'input-snapshots.json',mapping)
paths=[p for folder in[C,V]for p in folder.rglob('*')if p.is_file()]
paths +=[P/'build_canonical_proposal.py',P/'build_reader_proposal.py',Path(__file__),sf,ap,P/'source-correction-history.json',P/'source-facts.json',P/'source-inventory.json',P/'source-tables.json',P/'page-coverage.json',P/'original-assets-manifest.json']
paths +=[Path(a['path'])for a in read(P/'original-assets-manifest.json')['assets']]
paths +=[Path(p)for p in rm['input_hashes']]
bound={str(p.resolve()):sha(p)for p in sorted(set(paths),key=str)}
manifest={'schema':'mattersyn-private-canonical-reader-freeze/1','source_id':'sommer2020','doi':'10.1021/acs.cgd.9b01519','version':1,'author':'/root/backlog_eta','frozen_at':datetime.now(timezone.utc).isoformat(),'status':'author_proposal_source_audit_passed_canonical_reader_audit_pending','source_generation':2,'bundle_sha256':source['bundle_sha256'],'source_freeze_sha256':sha(sf),'source_audit':{'path':str(ap),'sha256':sha(ap),'reviewer':audit.get('reviewer',audit.get('auditor')),'status':'passed','scope':'All 11 supplied main pages; SI remains unlocated/unverified. Final 65 facts/137 quantities/222 table cells and 20 selected original crops.'},'canonical_record_manifest_sha256':sha(C/'record-manifest.json'),'reader_manifest_sha256':sha(V/'reader-manifest.json'),'reader_sha256':sha(V/'sommer2020.json'),'canonical_counts':cm['counts'],'reader_counts':rv['counts'],'author_checks':{'canonical':read(C/'author-validation.json')['check_count'],'reader':read(V/'author-validation.json')['check_count']},'bound_files':bound,'bound_file_count':len(bound),'independent_canonical_reader_approval':False,'training_approved':False,'visual_model_approved':False,'browser_approved':False,'site_imported':False,'published':False,'publication_exclusions':['Original PDFs','Complete-source payload manifest','All private/text files','All source-render full-page images','Complete-page attachments or local source paths'],'scope_notes_path':str(C/'proposal-notes.md'),'input_snapshots_path':str(C/'input-snapshots.json')}
write(C/'package-manifest.json',manifest)
print(json.dumps({'manifest':str(C/'package-manifest.json'),'sha256':sha(C/'package-manifest.json'),'reader_sha256':sha(V/'sommer2020.json'),'canonical_manifest_sha256':sha(C/'record-manifest.json'),'bound_files':len(bound),'checks':manifest['author_checks']},indent=2))
