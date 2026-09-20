"""Independent numerical audit of exactly two scanned Heo SI pages.
The comparison inputs were manually read from original body crops by the auditor.
This helper checks transfer, locators and unchanged source pixels; it does not
substitute programmatic checks for visual reading or audit SI pages 3–14.
"""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
import sys,json,hashlib,csv,io
sys.dont_write_bytecode=True
sys.path.insert(0,r'[local path redacted]')
sys.path.insert(0,r'[local path redacted]')
import pymupdf
from PIL import Image
B=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
T=read(B/'si-reflections-transcription.json')
C=read(B/'si-numerical-verification-checkpoint.json')
M=read(B/'si-numerical-assets.json')
V=read(B/'si-pages-1-2-auditor-visual-reading-resolved.json')
DETAIL=read(B/'reader-assets/si-independent-audit/detail-manifest.json')
COLS=['h','k','l','Fcal2','Fobs2','sigma_Fobs2','marker']
EXPECTED_HASHES={'si-reflections-pages01-02.tsv':'8ea2a1d1737623c743a38d8e379b424f11e2fc7afcc0163205cff0cf8750305a','si-reflections-transcription.json':'a6221a37bb638f9b9300d1c88875ff11b44714f5b98bfa4d73fced8d6130b6b9','si-numerical-verification-checkpoint.json':'6f5a86d76337fa2c597b8701ba3a0e5c2c128496e9e9355b9d66a88991a422dc'}
checks=[];findings=[]
def check(ok,label,kind='mechanical_integrity'):
    checks.append({'check':label,'passed':bool(ok),'kind':kind})
    if not ok:findings.append({'check':label,'kind':kind})
for file,h in EXPECTED_HASHES.items():check(sha(B/file)==h,file+' exact corrected frozen hash')
for p,h in C['bound_files'].items():check(sha(p)==h,'Author-bound file bytes independently rechecked: '+p)
for p,h in C['preserved_author_file_hashes'].items():check(sha(B/p)==h,'Pre-existing author/source file unchanged: '+p)
check(sha(T['source_path'])==T['source_sha256']==M['source_sha256']=='3b2e262af1932ed04cfddd596958c92d89c37099ab9dad8c4ce1f11254d4acc6','Original source SI bytes')
# Re-extract only the two relevant PDF scans and compare the original pixel arrays.
doc=pymupdf.open(T['source_path']);check(len(doc)==14,'Source document page count, not numerical coverage')
native={};assets={a['id']:a for a in M['assets']}
for page in [1,2]:
    images=doc[page-1].get_images(full=True);check(len(images)==1,f'SI page {page} one embedded scan')
    raw=doc.extract_image(images[0][0]); im=Image.open(io.BytesIO(raw['image'])).convert('L');native[page]=im
    a=assets[f'si-{page:02d}-native'];stored=Image.open(a['path']).convert('L')
    check(im.size==stored.size and im.tobytes()==stored.tobytes(),f'SI page {page} native evidence pixel equality with actual PDF')
for a in M['assets']:
    check(sha(a['path'])==a['sha256'],a['id']+' evidence hash')
    if 'original_image_box' in a:
        expected=native[a['source_pdf_page']].crop(a['original_image_box']);actual=Image.open(a['path']).convert('L')
        check(expected.size==actual.size and expected.tobytes()==actual.tobytes(),a['id']+' exact source-scan crop pixels')
for a in DETAIL:
    check(sha(a['source_path'])==a['source_sha256'] and sha(a['path'])==a['sha256'],a['id']+' auditor detail source/output hashes')
    im=Image.open(a['source_path']);im=im.crop(a['crop_box']);im=im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST);actual=Image.open(a['path'])
    check(im.size==actual.size and im.tobytes()==actual.tobytes(),a['id']+' auditor enlargement contains no numeral reconstruction')

manual=[];visual_ranges=[]
for block_key,raw in V['blocks'].items():
    p,block=block_key.split('-');page=int(p)
    lines=raw.splitlines();check(len(lines)==(40 if page==1 else 45),block_key+' independent visual row count','visual_source_reading_transfer')
    for j,line in enumerate(lines):
        cells=line.split();check(len(cells)==7,block_key+f' row {j+1} seven independently read tokens','visual_source_reading_transfer')
        rowid=f'si-p{page:02d}-{block}-r{j+1:03d}'
        manual.append({'row_id':rowid,'page':page,'block':block,'row':j+1,'raw_cells':dict(zip(COLS,cells))})
    visual_ranges.append({'pdf_page':page,'printed_page':40+page,'column_block':block,'rows':len(lines),'numeric_cells':len(lines)*6,'markers':len(lines),'visual_method':'Every printed token was independently read from the original body crops, including sign and printed decimal precision.','body_crop_ids':[f'si-{page:02d}-'+('left' if block=='L' else 'right')+'-top',f'si-{page:02d}-'+('left' if block=='L' else 'right')+'-bottom'],'status':'visually_read_in_full_and_compared_to_final_transcription'})
with (B/'si-reflections-pages01-02.tsv').open(encoding='utf-8',newline='') as f:tsv=list(csv.DictReader(f,delimiter='\t'))
check(len(manual)==len(tsv)==len(T['rows'])==170,'170 rows in independent visual reading, author TSV and author JSON','visual_source_reading_transfer')
cell_ids=[];audited_rows=[];negative=[]
for idx,(mine,a,jr) in enumerate(zip(manual,tsv,T['rows'])):
    rowid=mine['row_id'];expected_cells=mine['raw_cells']
    check(jr['row_id']==rowid and int(a['page'])==mine['page'] and a['block']==mine['block'] and int(a['row'])==mine['row'],rowid+' exact page/block/row identity')
    check(jr['hkl']==[int(expected_cells[k]) for k in ['h','k','l']],rowid+' original Miller indices and order','visual_source_reading_transfer')
    check(jr['source_sample_label']=='In66-X, as Supporting Table 1 title',rowid+' sample title scope')
    check(len(jr['cells'])==7,rowid+' seven cell records')
    for ci,key in enumerate(COLS):
        raw=expected_cells[key];cell=jr['cells'][ci];ev=cell['evidence'];cid=rowid+'-'+key
        cell_ids.append(cid)
        check(raw==a[key]==jr['raw_cells'][key]==cell['raw_text'],cid+' raw token matches independent original-scan reading','visual_source_reading_transfer')
        check(cell['cell_id']==cid,cid+' cell ID')
        check(ev['pdf_page']==mine['page'] and ev['printed_page']==40+mine['page'] and ev['column_block']==mine['block'] and ev['row_in_block']==mine['row'] and ev['column_key']==key and ev['supporting_table']==1,cid+' exact numerical locator')
        check(ev['source_sha256']==T['source_sha256'] and ev['source_path']==T['source_path'] and ev['source_id']=='heo2003-si',cid+' source binding')
        top=mine['row']<=(20 if mine['page']==1 else 23)
        crop=f"si-{mine['page']:02d}-"+('left' if mine['block']=='L' else 'right')+('-top' if top else '-bottom')
        check(ev['original_crop_id']==crop,cid+' correct original body crop')
        check(ev['printed_column_label']==T['original_header_labels'][key],cid+' correct header column')
        if key=='marker':
            check(raw=='o' and cell['numeric_value'] is None and cell['unit_status']=='not_applicable_marker',cid+' circle-like marker is preserved without numeric or acceptance interpretation','visual_source_reading_transfer')
        else:
            check(Decimal(str(cell['numeric_value']))==Decimal(raw),cid+' numeric parse preserves independent printed value')
            check(cell['unit'] is None and cell['unit_status']==('not_applicable_index' if key in ['h','k','l'] else 'unreported'),cid+' units and scale not invented')
            if key=='Fobs2' and Decimal(raw)<0:negative.append({'cell_id':cid,'hkl':jr['hkl'],'raw_text':raw,'parsed_value':cell['numeric_value']})
    audited_rows.append({'row_id':rowid,'hkl':jr['hkl'],'raw_cells_from_independent_source_reading':expected_cells,'cell_ids':[rowid+'-'+k for k in COLS],'all_tokens_match_corrected_author_files':all(expected_cells[k]==a[k]==jr['raw_cells'][k] for k in COLS)})
check(len(cell_ids)==len(set(cell_ids))==1190,'All 1190 independently inspected cells have unique IDs')
check([n['raw_text'] for n in negative]==['-407.76','-2910.49','-7916.46','-4491.35','-302.17'],'All five original negative observed squared structure factors retained','visual_source_reading_transfer')
check(T['completed_transcription_pages']==[1,2] and T['complete_document_transcription'] is False,'Partial transcription scope remains explicit')
check(T['training_eligible'] is False and T['published'] is False,'No training or publication approval')
remaining=T['remaining_cells_by_page_block'];check(len(remaining)==24,'24 untouched remaining page/block selectors')
check({(r['pdf_page'],r['column_block']) for r in remaining}=={(p,b) for p in range(3,15) for b in ['L','R']},'Remaining SI pages 3–14 are not absorbed into this numerical audit')
check(all(r['row_count'] is None and r['cell_count'] is None and r['remaining_columns']==COLS and r['independent_numerical_audit']=='not_started' for r in remaining),'Unreviewed remaining counts/columns preserve exact missingness')
corrected=next(r for r in T['rows'] if r['row_id']=='si-p01-R-r013')
check(corrected['raw_cells']['Fobs2']=='111928.27','Confirmed source error SI12-N1 fixed in final JSON and TSV','visual_source_reading_transfer')
speck=next(r for r in T['rows'] if r['row_id']=='si-p02-R-r002')
check(speck['raw_cells']['Fobs2']=='116323.99','P2 R2 original speck is dot-like, not minus; positive printed value retained','visual_source_reading_transfer')
# Scope of source visual inspection is recorded explicitly, separately from code checks.
for p,h in EXPECTED_HASHES.items():check(sha(B/p)==h,p+' still frozen at audit close')
bound={str(B/p):sha(B/p) for p in ['si-reflections-pages01-02.tsv','si-reflections-transcription.json','si-numerical-verification-checkpoint.json','si-numerical-checkpoint.md','si-numerical-assets.json','build_si_transcription_checkpoint.py','prepare_si_numerical_evidence.py','si-pages-1-2-auditor-visual-reading.json','si-pages-1-2-auditor-visual-reading-resolved.json','prepare_independent_si_audit_details.py','audit_si_pages_1_2.py','source-scientific-audit.json']}
bound[T['source_path']]=sha(T['source_path'])
for a in M['assets']:bound[a['path']]=sha(a['path'])
for a in DETAIL:bound[a['path']]=sha(a['path'])
bound[str(B/'reader-assets/si-independent-audit/detail-manifest.json')]=sha(B/'reader-assets/si-independent-audit/detail-manifest.json')
speckpath=B/'reader-assets/si-numerical/si-02-right-row02-fobs-detail.png';bound[str(speckpath)]=sha(speckpath)
status='passed_after_bounded_author_correction' if not findings else 'changes_required'
audit={'schema':'mattersyn-independent-si-numerical-audit/1','source_id':'heo2003','doi':'10.1021/jp0219348','reviewer':'/root/norberg2004_extract','transcription_author':'/root/peng1998_reader_assets','independent':True,'at':datetime.now(timezone.utc).isoformat(),'status':status,'source_pdf_sha256':T['source_sha256'],'exact_scope':{'supporting_table':1,'sample_as_printed':'In66-X','pdf_pages':[1,2],'printed_pages':[41,42],'rows':170,'numeric_cells':1020,'marker_cells':170,'total_cells':1190,'negative_observed_cells':5,'full_document_pages':14,'remaining_pages_not_numerically_audited':list(range(3,15))},'visual_source_verification':{'method':'The auditor independently read and entered every numeric token and circle-like marker from all eight native-scan body crops, then compared the resulting literal strings against the author TSV and cell JSON. Full-page scans established table boundary, printed page numbers, title and journal/year header; the two header crops established exact column identities. Four first-pass differences were independently re-opened as nearest-neighbor source-pixel details. No OCR output, author programmatic pass count or scientific plausibility substituted for visual numeral checking.','ranges':visual_ranges,'original_assets_actually_viewed':[a['id'] for a in M['assets']],'additional_actual_views':[a['id'] for a in DETAIL]+['si-02-right-row02-fobs-detail'],'reviewer_first_pass_corrections':V['reviewer_first_pass_corrections'],'marker_reading':'170 open-circle/lowercase-o-like glyphs, literal ASCII o accepted. Their semantics and exact Unicode identity remain unresolved.','speck_recheck':'P2 R2 has an isolated dot-like speck before 116323.99, unlike the horizontal printed minus signs. Its positive transcription is source-supported; no positivity assumption was used.'},'independent_row_comparisons':audited_rows,'negative_observations_verified':negative,'resolved_findings':[{'id':'SI12-N1','scope':'SI PDF page 1, right block, body row 13, Fobs²; hkl (3,5,9)','initial_author_value':'119928.27','source_value':'111928.27','initial_author_tsv_sha256':'d0f322ef1e5a3859bef074518d044529a396a483a4b3ce407c785b8b85912598','initial_author_json_sha256':'3b74766c16ab8f033844e0fe3157102691eea95a87a6b67ac078ccd5703971fa','source_detail':'reader-assets/si-independent-audit/p01-R-r13-Fobs.png','resolution':'Author confirmed source glyphs, changed exactly the erroneous TSV cell and regenerated. Auditor independently rechecked corrected token/parsed value/locators and all final row values. Finding history is retained.','resolved':corrected['raw_cells']['Fobs2']=='111928.27'}],'open_findings':findings,'mechanical_checks':checks,'mechanical_check_count':len(checks),'programmatic_scope_caveat':'Code verifies independently read values, transfer, locators, source hashes and exact image pixels. Check count is not a count of separately visually inspected source facts, and the author’s 2,222 checks are not reused as independent visual evidence.','bound_files':bound,'retained_limitations':['SI pages 3–14 were not numerically audited in this task; all their body cells remain pending.','The 2002/J. Phys. Chem. A SI header mismatch remains explicitly distinguished from the main publication metadata; prior paired-source audit is not broadened.','Intensity units/scale and trailing-marker semantics are unreported/unverified. No reflection is merged, symmetry-expanded, rescaled or clamped.','Structure-factor rows are not atomic coordinates, a new refined model, a CIF, a DFT-ready structure, a canonical training approval or a published reader page.'],'source_author_files_modified_by_auditor':False,'site_or_ledger_modified':False,'complete_si_numerical_audit':False,'training_eligible':False,'published':False}
save(B/'si-pages-1-2-independent-audit.json',audit)
md=f'''# Heo SI pages 1–2: independent numerical audit\n\nStatus: **{status}**. Reviewer: `/root/norberg2004_extract`; transcription author: `/root/peng1998_reader_assets`.\n\nThe audit covers every printed body cell of Supporting Table 1 on SI PDF pages **1–2** (printed pages **41–42**): **170 rows, 1,020 numeric cells and 170 trailing markers**. Page 1 has 40 rows per block; page 2 has 45. All seven columns were checked in original left-block/right-block/page order.\n\nThe reviewer independently entered the tokens from all eight source body crops, inspected both headers and both full-page scans, then compared those readings with the author TSV and cell JSON. This is actual independent visual comparison, not adoption of the author's programmatic checks. Source-native images were independently re-extracted from the actual PDF and matched pixel-for-pixel with the original evidence files. Four first-pass comparison differences were re-opened at pixel-preserving magnification. Three were reviewer reading slips, preserved transparently in the JSON history; one was a confirmed author error.\n\nThe confirmed error, **SI12-N1**, was page 1, right block, row 13, reflection **(3, 5, 9)**: Fobs² is **111928.27**, not **119928.27**. The author corrected that cell and regenerated the files. The reviewer verified the correction and all final row values. Open findings: **{len(findings)}**.\n\nAll five negative observed values remain intact: **−407.76, −2910.49, −7916.46, −4491.35, −302.17**. The dot-like speck before page 2/right/row 2 `116323.99` is not a horizontal minus glyph. That value remains positive based on source pixels, not scientific plausibility. All 170 circle-like marks remain literal `o`, with unknown semantics. Units, scale and decimal precision are not normalized or inferred.\n\nExact corrected input hashes:\n\n- TSV: `{EXPECTED_HASHES['si-reflections-pages01-02.tsv']}`\n- Cell JSON: `{EXPECTED_HASHES['si-reflections-transcription.json']}`\n- Author checkpoint: `{EXPECTED_HASHES['si-numerical-verification-checkpoint.json']}`\n- Source SI PDF: `{T['source_sha256']}`\n\nThe JSON contains all 170 independent row readings, cell IDs, exact source/file bindings, the correction history and {len(checks):,} independent integrity checks. The check count reflects value-transfer, locator, scope, hash and pixel checks; it is not an inflated count of visually examined source cells.\n\n**SI pages 3–14 remain outside this audit.** Their row and cell counts remain unknown rather than zero. The prior main-paper/source-identity audit is not retroactively expanded. This result does not approve a complete SI transcription, atomic-coordinate/CIF construction, training admission, reader publication or Site changes. The auditor modified no author source/transcription file, Site file or shared ledger.\n'''
(B/'si-pages-1-2-independent-audit.md').write_text(md,encoding='utf-8')
print(json.dumps({'status':status,'open_findings':findings,'checks':len(checks),'bound_files':len(bound),'audit_sha256':sha(B/'si-pages-1-2-independent-audit.json'),'markdown_sha256':sha(B/'si-pages-1-2-independent-audit.md')}))
