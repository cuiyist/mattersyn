"""Freeze the private Ghosh canonical/reader proposal for distinct review."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
P=Path(__file__).resolve().parent;C=P/'canonical-proposal/v1';V=P/'public-review-proposal/v1'
assert not(C/'package-manifest.json').exists(),'Frozen proposals require a preserved revision.'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
source=read(P/'package-freeze.json');ap=P/'source-independent-audit/independent-audit-v2.json';audit=read(ap)
assert audit['status']=='passed'and not audit['open_findings']and audit['proposal_freeze_sha256']==sha(P/'package-freeze.json')
for manifest in [source,audit]:
 for p,h in manifest['bound_files'].items():assert sha(p)==h,p
cm=read(C/'record-manifest.json');rm=read(V/'reader-manifest.json');review=read(V/'ghosh2012.json');records={x['record_id']:read(x['path'])for x in cm['records']}
assert len(records)==21 and sum(len(r['operations'])for r in records.values())==33
assert sum(len(r['materials'])for r in records.values())==88 and sum(len(r['stocks'])for r in records.values())==3
assert all(r['quality']['review_status']=='imported_unreviewed'and not r.get('collection')and r['quality']['requested_tasks']==[]and r['structure_assets']==[]for r in records.values())
assert all(sha(x['path'])==x['sha256']for x in cm['records'])and all(sha(V/n)==h for n,h in rm['outputs'].items())
assert review['counts']['source_table_cells']==272 and review['counts']['typed_reader_fields']==1176 and not review['training_eligible']and not review['source_review_promoted']
assert review['counts']['reader_items']==325 and review['counts']['selected_original_assets']==36
notes='''# Ghosh 2012 — private canonical and reader proposal v1

The supplied ten-page main article and nine-page SI PDF passed the distinct scientific source audit of extraction revision 2. That audit binds 71 facts, 194 fact quantities, all 272 table cells, all 19 read/viewed pages and 36 selected original crops. The first source freeze, exact bounded correction history and independent audit revisions remain preserved. Historical pending flags inside the immutable source payload describe its author-freeze moment, before the separate source audit.

The canonical proposal has 21 records: two literature protocols, three protocol variants, ten supporting procedures and six observation/context records. It preserves 33 operations, 88 material slots, three stock formulations, 89 record-local product/context slots and 585 measurement/context entries. These counts do not represent independent physical batches. All 243 source inventory units, 71 facts and 272 cells have exact canonical JSON-pointer mappings, including 335 fact bindings and 790 source-unit bindings. The lossless source map retains all source tokens, units, approximations, ranges, inequalities, uncertainties, qualitative labels, table definitions, image-cell identities and conflicts.

Core branches remain separate: common growth for 3 or 4 nm cores with unreported exact size-specific timing, the 2.2 nm cold-toluene early-quench branch, and the 5.5 nm additional-feed branch. The latter two reference the common initial operations instead of inventing duplicate charges. The separate 7 nm core-only control has unreported upstream preparation; its washing/optical observations are not borrowed into those core recipes. TOP-Se, S/OD and Cd-oleate/OD formulations are recorded without fabricating upstream synthesis or stock volumes. Whole formulation charges are not silently converted into aliquot concentrations.

Preferred shell growth retains Cd prepassivation, separate anion/cation additions, 240 °C, post-S 1 h and post-Cd 2.5 h. The first 5–8-cycle ligand span is unresolved rather than forced to one switch cycle. A pair of half-layer precursor additions forms a complete shell cycle; Cd prepassivation remains distinct. All five Table 1 comparison schedules are separate typed condition options. The rounded narrative anneal totals and associated QYs remain context measurements, not universal controls.

The solvent, primary/secondary/no-added-amine, late/extreme-dilution, withdrawal/OA and constant-sulfur comparisons retain their negative outcomes and incomplete formulations. Grouped alternative inputs do not describe a single charge containing all solvents or ligands simultaneously. One- and ten-percent quantities refer to withdrawn reaction volume with subsequent planned precursor doses retained; no molar-excess percentage is inferred. Two comparison outputs originally named withdrawn-aliquots receive operation-specific local state IDs to prevent graph collisions. This is bookkeeping, not an additional physical sample claim.

Operation quantity placement is explicitly documented in operation-quantity-scope.json. FTIR preparation gets six wash cycles, while acquisition gets 4 cm−1 resolution and 32 scans. XRD deposition does not inherit scan conditions. Rhodamine 6G purity is a reference-material context, not a product QY or acquisition setting. Measured sizes, QYs, turbidity, phase weights and morphology observations are retained in measurements rather than assigned as process controls. Text-only durations and ratio formulations remain explicit source claims/typed text; the schema is not forced to invent numeric endpoints.

All five tables remain complete. Table 3 uses moderately thick-shell TEM images but >15 ML QY outcomes; no exact same-thickness or same-particle join is certified. Table S1 has eighteen rows/180 values with printed precision, averaged amplitudes and lifetimes. A diagnostic recomputation from rounded mean coefficients does not replace reported average lifetimes. The 5.5 nm/16.9 ML trace examples are not forced onto the final 15.57 ML table row. The reported mean-lifetime equation is named descriptively without mislabeling it as the conventional amplitude-weighted average.

The reader provides five academic sections plus Sources and limitations: 325 items, 1,176 typed canonical fields, all source-unit/fact/table mappings, all 33 operations, 88 material slots, three stocks, 89 context slots and 585 measurement entries. All 13 figure contexts, one scheme, six equations and 23 numbered references/24 works are retained. Its 36 selected original excerpts are proposals only. Complete source text, PDFs, payload manifests and full-page images are absent from public attachment paths and remain local.

Six source conflict groups remain explicit: preferred versus comparison anneals and the ligand-switch span; rounded narrative totals/statistics versus Table 1; the SI secondary-amine/oleylamine-NH2 identity wording; greater-than versus at-least 99% definitions; approximate versus plotted secondary-amine phase ratios; and the unverified 16.9/15.57 ML sample association. Eight missingness groups remain. Surface, dipole and quasi-type-II mechanisms are author interpretations; the approximate 750 nm³ and 65 ns trends retain the 3.0 nm exception. Semiquantitative WZ:ZB phase weights, a half-c-parameter monolayer convention and TEM images do not supply atomic coordinates, a measured CIF or an exact recipe–structure label.

All records remain imported_unreviewed, without collection promotion, structure assets or requested training tasks. Canonical/reader independent approval, molecular/component and apparatus bindings, browser checks, Site import and publication are separate gates. This author freeze does not certify those gates and changes no Site, source PDF, shared ledger, memory or GitHub state.
'''
(C/'proposal-notes.md').write_text(notes,encoding='utf-8')
(V/'README.md').write_text('Private Ghosh reader: ghosh2012.json. Source extraction revision 2 passed a distinct audit. Canonical/reader, visual, browser and publication approvals remain pending. All 36 public-asset candidates are selected excerpts; no full page or complete source payload is proposed for attachment. Exact canonical pointers and source identities are retained in the coverage and binding manifests.\n',encoding='utf-8')
# Keep immutable copies of reusable code dependencies for later transport audits.
deps=[Path(p)for p in cm['input_modules']]+[P.parent/'acsami.1c18038/build_reader_proposal.py']
snap=C/'input-snapshots';snap.mkdir(exist_ok=True);mapping={}
for p in deps:
 dst=snap/('lian-reader-builder.py'if p.parent.name=='acsami.1c18038'else p.name);shutil.copy2(p,dst);assert sha(p)==sha(dst);mapping[str(p)]={'snapshot_path':str(dst),'sha256':sha(dst)}
write(C/'input-snapshots.json',mapping)
paths=[p for root in [C,V]for p in root.rglob('*')if p.is_file()]
paths += [P/'build_canonical_proposal.py',P/'build_reader_proposal.py',P/'adapt_reader_builder.py',Path(__file__),P/'package-freeze.json',ap,P/'source-correction-history.json',P/'source-facts.json',P/'source-inventory.json',P/'source-tables.json',P/'page-coverage.json',P/'original-assets-manifest.json']
paths += [Path(a['path'])for a in read(P/'original-assets-manifest.json')['assets']]
paths += [Path(p)for p in rm['input_hashes']]
bound={str(p.resolve()):sha(p)for p in sorted(set(paths),key=str)}
manifest={'schema':'mattersyn-private-canonical-reader-freeze/1','source_id':'ghosh2012','doi':'10.1021/ja212032q','version':1,'author':'/root/backlog_eta','frozen_at':datetime.now(timezone.utc).isoformat(),'status':'author_proposal_source_audit_passed_canonical_reader_audit_pending','source_generation':2,'bundle_sha256':source['bundle_sha256'],'source_freeze_sha256':sha(P/'package-freeze.json'),'source_audit':{'path':str(ap),'sha256':sha(ap),'reviewer':audit['reviewer'],'status':audit['status'],'scope':'All supplied 10 main + 9 SI pages, 36 selected crops, 71 facts/194 quantities and all 272 table cells; canonical and visual approval are separate.'},'canonical_record_manifest_sha256':sha(C/'record-manifest.json'),'reader_manifest_sha256':sha(V/'reader-manifest.json'),'reader_sha256':sha(V/'ghosh2012.json'),'canonical_counts':cm['counts'],'reader_counts':review['counts'],'author_checks':{'canonical':read(C/'author-validation.json')['check_count'],'reader':read(V/'author-validation.json')['check_count']},'bound_files':bound,'bound_file_count':len(bound),'independent_canonical_reader_approval':False,'training_approved':False,'visual_model_approved':False,'browser_approved':False,'site_imported':False,'published':False,'publication_exclusions':['Original PDFs','Complete-source payload manifest','All private/text files','All source-render full-page images','Complete-page attachments or local source paths'],'scope_notes_path':str(C/'proposal-notes.md'),'input_snapshots_path':str(C/'input-snapshots.json')}
write(C/'package-manifest.json',manifest)
print(json.dumps({'manifest':str(C/'package-manifest.json'),'sha256':sha(C/'package-manifest.json'),'reader_sha256':sha(V/'ghosh2012.json'),'canonical_manifest_sha256':sha(C/'record-manifest.json'),'bound_files':len(bound),'checks':manifest['author_checks']}))
