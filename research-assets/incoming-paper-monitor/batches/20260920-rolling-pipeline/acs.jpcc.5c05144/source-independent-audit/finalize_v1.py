import json,hashlib,datetime
from pathlib import Path
O=Path(__file__).parent;P=O.parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
Z=read(P/'package-freeze.json');F=read(P/'source-facts.json');A=read(P/'original-assets-manifest.json');C=read(O/'comparison-checks-v1.json');R=read(O/'independent-reading-checkpoint.json')
assert len(C['summary']['failed'])==2 and all('SAS-SRC-01' in x['check'] for x in C['summary']['failed'])
bound={}
for n,d in Z['bound_files'].items():
 f=P/n;assert sha(f)==d['sha256'];bound[str(f.resolve())]=sha(f)
for f in [P/'package-freeze.json',O/'reading-preparation.json',O/'independent-reading-checkpoint.json',O/'independent-numeric-reading.json',O/'freeze_reading.py',O/'prepare_reading.py',O/'check_extraction.py',O/'comparison-checks-v1.json',O/'comparison-checks-initial-diagnostics.json',O/'source-render/symmetry-native-recheck.png',Path(__file__)]:bound[str(f.resolve())]=sha(f)
for p in R['pages']:
 for k in ['png','text_path']:bound[str(Path(p[k]).resolve())]=sha(p[k])
for s in R['paper']['file_copies']:bound[str(Path(s['source_path']).resolve())]=sha(s['source_path'])
report={
'schema':'mattersyn-independent-source-audit/1','source_id':'sasongko2025','doi':'10.1021/acs.jpcc.5c05144','author':'/root/peng1998_reader_assets','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'revision':1,'status':'revision_required','source_freeze':str(P/'package-freeze.json'),'source_freeze_sha256':sha(P/'package-freeze.json'),
'scope':'Complete independent reading of supplied main and matched SI, then comparison of frozen structured source extraction and selected original crops. This is not canonical/reader/model/training/publication approval.',
'pairing':R['pairing'],
'coverage':{'main_pages_read_and_viewed':9,'si_pages_read_and_viewed':11,'facts_read_and_compared':48,'fact_quantities_compared':100,'materials':13,'stocks':4,'stock_components':9,'protocols':9,'operations':sum(len(p['operations']) for p in F['protocols']),'sample_contexts':33,'figures':8,'schemes':1,'equations':2,'table_groups':6,'table_body_cells':121,'references':89,'inventory_units':157,'selected_crops_actually_viewed':17,'selected_crops_pixel_replayed':17},
'manual_scopes':[
'Read all20 independent source text pages and native page images before opening author scientific payload; preserved numeric/table baseline first.',
'Matched complete title, byline, Associated Content declaration and SI experimental/property continuity; independently hashed both originals against intake.',
'Compared every one of48 claims and100 typed quantities, including source-bound approximations, bounds, ranges, uncertainty definitions and present/missing units.',
'Compared all13 material identities/grades, four stock/formulation definitions and nine components; prepared FA stock charge distinguished from0.51mL aliquot and unknown final concentration.',
'Read all21 operation stages across9 protocols; checked reagent order, nitrogen/vacuum boundary, selected-temperature pre-injection30min, prompt cooling, two centrifugations and retained fractions.',
'Read all33 source contexts; ligand/wash/growth families are source-defined alternatives, no27-condition factorial or exact cross-technique batch joins are manufactured.',
'Independently transcribed and compared all55 Table S1 body cells, citations and four size annotations; missing transition cells remain null, cited rows remain literature, row9/reference14 conflict retained.',
'Compared all66 other typed body cells against actual figure labels and prose: ligand/wash widths and lifetimes, growth sizes/spreads/FWHMs/bars, PL slopes and cited cells.',
'Read all8 figure maps, Scheme1 and the graphical abstract; source phase models and reference lattice cells do not become measured QD atomic coordinates.',
'Checked lifetime equation numerator/denominator and hour-based stability fit; source equation numbering and instrument typography remain explicit.',
'Checked Raman caption/prose/numbering scope, fringe/index/reference-cell discrepancy, reference14 specimen conflict and missingness of acquisition/batch/atomic evidence.',
'Read every citation on main7–9 and SI9–11; verified89 numbered raw citations against independently extracted text after known PDFium soft-hyphen normalization. No cited source was externally retrieved.',
'Actually viewed all17 selected original crops individually; checked labels, captions, scale bars and limits against full native pages; independently replayed all17 at220dpi from originals.',
'Verified all76 frozen author files,157 source-unit mappings and complete per-page coverage; initial mechanical diagnostics were resolved as auditor assumptions, not author scientific edits.'
],
'findings':[{'id':'SAS-SRC-01','severity':'required_bounded_locator_correction','status':'open','source_location':'SI PDF page5 / printedS5, FigureS2 caption','affected_author_fields':['source-facts.json /facts sasongko2025-raman-range /evidence','same fact /quantities meaning displayed temperature interval /evidence','corresponding operation/inventory/page-coverage evidence copies'], 'observation':'The displayed80–190K range is printed in FigureS2 caption on SI p5. Current evidence arrays cite p6 and p4; a locator string refers to p5 but its pdf_page is6. Add exact p5 evidence without replacing the p6 prose80–200K/above190K scope or p4 instrument evidence.','required_change':'Preserve original freeze; add the exact caption locator and propagate only necessary evidence/coverage metadata. All values and crop bytes remain unchanged.'}],
'auditor_corrections':[
{'id':'AUD-NOTE-01','type':'auditor_reading_note_error','detail':'The initial independent-reading-checkpoint boundary note incorrectly wrote alpha Pm-3m. A432dpi original-source crop subsequently showed literal Pm3m without overbar. Author extraction is correct and needs no change. Initial note is preserved; this correction supersedes only that notation.', 'source_asset':str(O/'source-render/symmetry-native-recheck.png')},
{'id':'AUD-CHECK-01','type':'checker_assumption','detail':'Initial exact operation-quantity equality rejected14 evidence-list subsets because broader fact evidence also includes apparatus context. Scientific cores match; final checker explicitly checks exact core and evidence subset. No author error.'},
{'id':'AUD-CHECK-02','type':'PDF_text_normalization','detail':'Initial17 reference equality failures were solely PDFium U+FFFE soft-hyphen versus author normalized hyphen. After explicit normalization, all89 raw citations match. Initial diagnostics retained; no author change.'}
],
'mechanical_summary':C['summary'],'bound_files':bound,'bound_file_count':len(bound),
'limitations':['Original source contradictions remain unresolved; passage will verify faithful extraction, not settle them.','No curve digitization, external reference validation, molecular/crystal model qualification or exact sample joins.','Canonical/reader/visual/training and release gates require their separate reviews; no Site or ledger mutation.'],
'source_payload_policy':'Full native pages and complete source text remain local under source-render; selected excerpts have no public approval in this source review.'}
for name in ['independent-audit-v1.json','independent-audit.json']:
 dest=O/name;assert not dest.exists();dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md='''# Sasongko2025 independent source audit — revision1

**Revision required: one exact evidence locator.** Author: `/root/peng1998_reader_assets`; independent reviewer: `/root/backlog_eta`.

All nine main and eleven SI pages were independently read and visually inspected before opening the extraction. Both original hashes match intake and main/SI identity is content verified. All48 facts/100 quantities,13 materials, four stocks,21 operations,33 contexts,121 table body cells and89 citations were compared. All17 selected crops were individually viewed and reproduced pixel-for-pixel from the originals.2,270 supporting checks pass.

SAS-SRC-01: add the actual SI page5 FigureS2 caption to the80–190K displayed-range evidence in `sasongko2025-raman-range` and its typed quantity/copied mappings. Existing p6 prose and p4 apparatus locators remain. No scientific number, sample assignment or crop correction is requested.

The author's literal `Pm3m` is correct: a high-resolution original crop corrected the auditor's earlier overbar assumption. Initial checker-only differences in evidence-list breadth and PDFium soft hyphens were also resolved without author changes. All original reading and diagnostic checkpoints remain preserved.

Five source discrepancies and six missingness groups remain explicit. Reference lattice cells are contextual, not measured QD coordinates. No canonical, visual, model, training or publication approval is made. Exact bound files and source hashes are in the JSON report.
'''
for name in ['independent-audit-v1.md','independent-audit.md']:(O/name).write_text(md,encoding='utf-8')
print(sha(O/'independent-audit-v1.json'),len(bound),report['coverage'])
