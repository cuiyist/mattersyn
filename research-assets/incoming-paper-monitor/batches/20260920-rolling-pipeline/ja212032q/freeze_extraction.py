"""One-time author source freeze; version corrections instead of rerunning this after freeze."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,runpy
P=Path(__file__).resolve().parent
assert not(P/'package-freeze.json').exists(),'Preserve existing freeze and prepare a versioned correction.'
NOW=datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(n):return json.loads((P/n).read_bytes())
def write(n,obj):(P/n).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
a=read('original-assets-manifest.json')
for asset in a['assets']:asset['manual_visual_review']='Extraction author viewed this original crop on the six contact sheets; all nineteen full native source pages were read/viewed. Adjusted table/equation crops were reopened individually. Independent review remains pending.'
write('original-assets-manifest.json',a)
visual={'schema':'mattersyn-source-crop-author-review/1','author':'/root/backlog_eta','reviewed_at':NOW,'status':'author_viewed_independent_audit_pending','actual_manual_scope':{'complete_source_text_pages_read':19,'native_full_page_images_viewed':19,'all_native_table_rows_read':True,'selected_crops_viewed':36,'contact_sheets_viewed':6,'adjusted_crops_reopened':['table-2','table-3','equations-si-fit','equation-si-fit-repeat']},'bound_assets':{x['path']:x['sha256']for x in a['assets']},'contact_sheets':{str(x):sha(x)for x in sorted((P/'private').glob('crop-contact-*.png'))},'independent_audit':False}
write('author-visual-review.json',visual)
runpy.run_path(str(P/'validate_extraction.py'),run_name='__main__')
v=read('extraction-validation.json');s=read('source-facts.json');payload=read('complete-source-payloads.json')
write('author-validation.json',{'schema':'mattersyn-source-author-final-validation/1','author':'/root/backlog_eta','validated_at':NOW,'status':'passed_author_checks_independent_audit_pending','checks_count':v['check_count'],'counts':s['counts'],'actual_manual_scope':visual['actual_manual_scope'],'mechanical_validation':{'path':'extraction-validation.json','sha256':sha(P/'extraction-validation.json')},'independent_audit':False})
notes=f'''# Ghosh 2012 full supplied-source extraction

DOI: 10.1021/ja212032q. Extraction author: /root/backlog_eta. This package is local author work; independent scientific audit, canonical/reader approval, visual-model qualification and publication remain separate gates.

All 10 main and nine SI pages were read in full and individually visually inspected. The six-author byline, complete title, main SI declaration and matching figure/table content support main/SI pairing. All four original copies were hashed; incoming and legacy files represent two unique PDFs. No paper or attachment was downloaded.

The package retains 71 facts and 194 typed or explicitly text-only quantities; 25 materials; three stock/formulation descriptions; 15 synthesis/comparison/acquisition/control protocol scopes with 33 operations; 81 sample/comparison contexts; 13 figures including the graphical abstract; one scheme and footnote; six mathematical definitions; 23 numbered references containing 24 individual works. Context counts do not represent 81 independently verified experimental specimens.

All five tables are transcribed: main Tables 1–3, SI Table S1 and the unnumbered eleven-row band table within Figure S2. They contain 44 rows and 272 cells: 215 scalar numeric cells, six phase-ratio cells, one range cell, 40 qualitative/text cells and ten original-image cells. Table S1 retains all 180 numeric tokens. Main Table 1 retains every approximate QY and the >45% bound. Table 2/3 Low/Mod-High/None labels remain qualitative. All ten embedded TEM images are available as separate original crops as well as in their tables.

Core branches remain distinct: common 3 or 4 nm growth with unspecified exact timing, 2.2 nm cold-toluene early quench, 5.5 nm extra-feed growth, and a separate incompletely specified 7 nm core-only control. The preferred CdS shell procedure uses 240 °C, post-S 1 h and post-Cd 2.5 h; the five Table 1 schedules are comparison variants. The ligand switch remains a 5–8-layer span, not an invented exact cycle. One- and ten-percent labels describe removal of reaction solution while planned precursor doses remain fixed; no molar precursor-excess percentage is computed.

All solvent, primary/secondary/no-added-amine, late/extreme-dilution, withdrawal/OA and constant-sulfur comparisons and their poor/nonemissive outcomes are retained. Table 3 explicitly uses moderately thick-shell TEM images while the QY column describes >15 ML particles. No exact same-specimen TEM/QY pairing is invented. Surface-termination, steric-packing and dipole explanations are author interpretations; WZ:ZB estimates are semiquantitative phase weight fractions. No atomic coordinates, measured lattice model, CIF, SAED or exact recipe–structure task is approved or supplied.

Six explicit conflict/qualification records preserve (C1) preferred versus comparison anneals and ligand-switch wording, (C2) rounded narrative totals/statistics versus Table 1, (C3) SI secondary-amine versus oleylamine/NH2 wording, (C4) >99% versus ≥99% nonblinking definitions, (C5) approximate ~70:30 versus plotted 67:33 secondary-amine phase ratios, and (C6) the 5.5 nm/16.9 ML trace examples versus the 15.57 ML final Table S1 row. Eight missingness groups cover upstream stocks, practical workup, sample joins, per-layer accounting, acquisition, atomistic structure, surface speciation and graph/fit data.

The 750 nm³ and 65 ns relationships are approximate, paper-scoped trends; the 3.0 nm lifetime exception is explicit. SI fitting coefficients are averaged and rounded: the author diagnostic recomputation differs from reported Tavg by up to {max(abs(x['difference_ns'])for x in v['source_table_diagnostics']):.6f} ns, and no printed value is overwritten. This diagnostic is neither an independent numerical audit nor a physical-model qualification.

All 36 selected crops were actually viewed on six contact sheets, with adjusted table/equation crops reopened individually. {v['check_count']} author checks passed, including source hashes, source/page locators, inventory pointers, all 180 S1 native-text tokens, bounds and qualitative typing, and pixel-identical replay of all 36 crops from the original PDFs.

`source-render/`, `private/text/` and `complete-source-payloads.json` contain whole-source material and must remain local. The preparation payload's original unread flags describe the preparation moment; `page-coverage.json` and `author-visual-review.json` record completed author reading. Selected crops are candidates only and still require the later publication allowlist gate. No Site, shared ledger, source PDF, memory or GitHub file was changed by this extraction.
'''
(P/'extraction-notes.md').write_text(notes,encoding='utf-8')
names=['prepare_sources.py','source_author_data.py','build_extraction.py','validate_extraction.py','freeze_extraction.py','intake-identity.json','complete-source-payloads.json','source-facts.json','source-tables.json','source-inventory.json','page-coverage.json','pairing-review.json','relevance-screening.json','original-assets-manifest.json','author-visual-review.json','extraction-validation.json','author-validation.json','extraction-notes.md']
files=[P/n for n in names]+list((P/'private/text').glob('*.txt'))+list((P/'private').glob('crop-contact-*.png'))+list((P/'source-render').glob('*.png'))+list((P/'reader-assets').glob('*.png'))+[P.parent/'intake-20260920T082035Z/intake-manifest.json']
bound={str(p.resolve()):sha(p)for p in sorted(set(files))}
for f in payload['source_copies']:
 assert sha(f['source_path'])==f['sha256'];bound[f['source_path']]=f['sha256']
freeze={'schema':'mattersyn-source-extraction-freeze/1','source_id':s['source_id'],'doi':s['doi'],'title':s['title'],'author':'/root/backlog_eta','frozen_at':NOW,'revision':1,'source_generation':2,'bundle_sha256':s['bundle_sha256'],'status':'author_complete_supplied_pdfs_independent_audit_pending','counts':s['counts'],'author_check_count':v['check_count'],'bound_files':bound,'bound_file_count':len(bound),'private_scope':['All 19 supplied main/SI pages read and visually inspected.','Whole-source PDFs/text/full-page images remain local only.','No independent audit, canonical, reader, model, browser or public-import approval is asserted.','No source, Site or shared ledger edits.'],'independent_audit':False}
write('package-freeze.json',freeze)
print(json.dumps({'freeze':str(P/'package-freeze.json'),'sha256':sha(P/'package-freeze.json'),'source_facts_sha256':sha(P/'source-facts.json'),'source_tables_sha256':sha(P/'source-tables.json'),'bound_files':len(bound),'checks':v['check_count']},ensure_ascii=False))
