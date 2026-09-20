"""Build a private, explicitly partial SI numerical transcription checkpoint.

The TSV was manually read from native scan crops. These author checks do not
replace an independent numerical audit. Existing source/main-table files stay intact.
"""
from pathlib import Path
from decimal import Decimal
from datetime import datetime,timezone
import csv,json,hashlib
B=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
I=read(B/'source-inventory.json'); A=read(B/'source-scientific-audit.json')
D=I['source_documents']['si']; assert sha(D['path'])==D['sha256']
E=read(B/'si-numerical-assets.json')
for asset in E['assets']:assert sha(asset['path'])==asset['sha256']
original_files=['source-inventory.json','source-facts.json','page-coverage.json','source-scientific-audit.json',
                'main-tables.json','main-table-assets.json','source-review-checkpoint.json']
old_hashes={x:sha(B/x) for x in original_files}
rows=list(csv.DictReader((B/'si-reflections-pages01-02.tsv').open(encoding='utf-8'),delimiter='\t'))
columns=['h','k','l','Fcal2','Fobs2','sigma_Fobs2','marker']
col_labels={'h':'h','k':'k (left first-page header prints K)','l':'l','Fcal2':'Fcal^2','Fobs2':'Fobs^2',
            'sigma_Fobs2':'σ(Fobs^2)','marker':'trailing open-circle/lowercase-o-like mark; no header'}
blocks={(1,'L'):40,(1,'R'):40,(2,'L'):45,(2,'R'):45}
checks=[]
def check(name,value):
    checks.append({'check':name,'passed':bool(value)})
    assert value,name
check('Exactly 170 rows in completed two-page subset',len(rows)==170)
for (page,block),n in blocks.items():
    subset=[r for r in rows if int(r['page'])==page and r['block']==block]
    check(f'SI page {page} {block}: all {n} sequential rows', [int(r['row']) for r in subset]==list(range(1,n+1)))
data=[];cell_ids=[];negative=[]
for row in rows:
    page=int(row['page']);block=row['block'];rn=int(row['row']);rid=f'si-p{page:02d}-{block}-r{rn:03d}'
    ebase={'source_id':'heo2003-si','source_path':D['path'],'source_sha256':D['sha256'],
           'supporting_table':1,'pdf_page':page,'printed_page':40+page,'column_block':block,'row_in_block':rn}
    half='top' if rn <= (20 if page==1 else 23) else 'bottom'
    asset_id=f'si-{page:02d}-'+('left' if block=='L' else 'right')+'-'+half
    cell_data=[]
    for col in columns:
        raw=row[col];cid=rid+'-'+col;cell_ids.append(cid)
        number=None if col=='marker' else int(raw) if col in ['h','k','l'] else float(Decimal(raw))
        if col!='marker':
            check(cid+' finite numeric token',Decimal(raw).is_finite())
            check(cid+' exact decimal round trip',Decimal(str(number))==Decimal(raw))
        else:check(cid+' marker retained',raw=='o')
        evidence={**ebase,'column_key':col,'printed_column_label':col_labels[col],
                  'locator':f'SI PDF p. {page} (printed p. {40+page}), Supporting Table 1, {"left" if block=="L" else "right"} block, body row {rn}, {col_labels[col]}',
                  'original_crop_id':asset_id}
        note='Miller index; no symmetry expansion, equivalence merging or index transformation performed.' if col in ['h','k','l'] else \
             'Source scale/physical units are unreported here. Raw decimal precision is retained; no intensity rescaling or truncation.' if col!='marker' else \
             'Literal transcription uses ASCII o for the open-circle/lowercase-o-like glyph. Its meaning is unverified; it is not converted into a numeric zero or acceptance/rejection flag.'
        if cid=='si-p02-R-r002-Fobs2':
            note+=' The preceding isolated scan speck was inspected in an additional 4× nearest-neighbor detail: it is dot-shaped, not a printed minus sign. The numeric token is positive 116323.99; detail retained.'
        cell_data.append({'cell_id':cid,'raw_text':raw,'numeric_value':number,'unit':None,
            'unit_status':'not_applicable_index' if col in ['h','k','l'] else 'unreported' if col!='marker' else 'not_applicable_marker',
            'transcription_status':'manually_transcribed_from_original_scan',
            'source_comparison_status':'visually_compared_by_transcription_author',
            'independent_numerical_audit':'pending','evidence':evidence,'note':note})
        if col=='Fobs2' and number<0:negative.append({'cell_id':cid,'raw_text':raw,'numeric_value':number})
    data.append({'row_id':rid,'source_sample_label':'In66-X, as Supporting Table 1 title',
        'hkl':[int(row[x]) for x in ['h','k','l']], 'raw_cells':{c:row[c] for c in columns},'cells':cell_data})
check('All completed cell IDs unique',len(cell_ids)==len(set(cell_ids)))
check('170 unique supplied reflection indices; no merging applied',len({tuple(r['hkl']) for r in data})==170)
check('Exactly 1190 cells: 1020 numeric plus 170 uninterpreted markers',len(cell_ids)==1190)
check('All five negative observed values preserved',[(x['cell_id'],x['raw_text']) for x in negative]==[
    ('si-p01-L-r004-Fobs2','-407.76'),('si-p01-R-r038-Fobs2','-2910.49'),
    ('si-p02-L-r021-Fobs2','-7916.46'),('si-p02-R-r040-Fobs2','-4491.35'),('si-p02-R-r042-Fobs2','-302.17')])
check('No silent numerical values attached to markers',all(c['numeric_value'] is None for r in data for c in r['cells'] if c['evidence']['column_key']=='marker'))
check('Source PDF unchanged after transcription',sha(D['path'])==D['sha256'])
check('Existing author files unchanged',all(sha(B/k)==h for k,h in old_hashes.items()))
remaining=[]
for page in range(3,15):
    for block in ['L','R']:
        remaining.append({'pdf_page':page,'printed_page':40+page,'column_block':block,
            'remaining_rows':'ALL printed body rows in this block; row count has not been numerically inventoried in this checkpoint',
            'remaining_columns':columns,'remaining_cell_selector':f'si-p{page:02d}-{block}-r*-{{'+','.join(columns)+'}',
            'row_count':None,'cell_count':None,'count_status':'unverified; null does not mean zero',
            'transcription_status':'not_started','independent_numerical_audit':'not_started',
            'existing_page_image':str(B/f'si-{page:02d}.png'),'existing_page_image_sha256':sha(B/f'si-{page:02d}.png')})
transcription={'schema':'mattersyn-si-reflection-transcription/1','source_id':'heo2003','table_number':1,
    'title_as_printed':'Observed and Calculated Structure Factors Squared with Esds for In66-X',
    'author':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),
    'status':'partial_source_checked_author_transcription_pending_independent_numerical_audit',
    'source_path':D['path'],'source_sha256':D['sha256'],'source_page_count':14,
    'completed_transcription_pages':[1,2],'complete_document_transcription':False,'independent_audit_passed':False,
    'scientific_scope':'Printed reflection indices, calculated/observed squared structure factors and their reported esds. Not atomic coordinates, a new crystal model, a CIF or a DFT-ready structure.',
    'source_identity_caveat':'SI header prints ©2002 ACS, J. Phys. Chem. A, Heo jp0219348. Manuscript code, In66-X table and main SI declaration support the audited pairing despite journal/year header mismatch.',
    'field_order':columns,'original_header_labels':col_labels,'rows':data,
    'negative_observations':negative,'units_and_scale':'No intensity units, conversion factors or rescaling have been inferred. Raw decimal tokens preserve the supplied precision.',
    'marker_policy':'All 170 supplied open-circle/lowercase-o-like marks are preserved as raw o; semantic interpretation and Unicode identity remain unresolved.',
    'unresolved_numeric_tokens_in_completed_pages':[],'remaining_cells_by_page_block':remaining,
    'training_eligible':False,'published':False}
write(B/'si-reflections-transcription.json',transcription)
detail=B/'reader-assets'/'si-numerical'/'si-02-right-row02-fobs-detail.png'
checkpoint={'schema':'mattersyn-si-numerical-checkpoint/1','source_id':'heo2003',
    'created_at':datetime.now(timezone.utc).isoformat(),'author':'/root/peng1998_reader_assets',
    'status':'partial_author_transcription_source_comparison_complete_independent_audit_pending',
    'authoring_not_independent_audit':'No pre-existing SI cell transcription was present. This agent authored the separate TSV/JSON and compared its cells to the original scan; a different reviewer must provide the independent numerical audit.',
    'actual_scope':{'pages_transcribed':[1,2],'native_scan_pages_visually_inspected':[1,2],
        'cell_comparison_pages':[1,2],'completed_blocks':[{ 'page':p,'block':b,'rows':n} for (p,b),n in blocks.items()],
        'rows':170,'numeric_cells':1020,'marker_cells':170,'total_cells':1190,'negative_Fobs2_cells':5,
        'original_native_pages':2,'header_and_block_crops':10,
        'full_SI_pages':14,'remaining_untranscribed_pages':list(range(3,15)),
        'remaining_cell_count':None,'remaining_count_note':'Every body cell on pages 3–14 remains untranscribed. Per-block selectors are exhaustive, but row counts are not yet inventoried.'},
    'scan_reading_notes':[{'cell_id':'si-p02-R-r002-Fobs2','issue':'A preceding dot-like scan artifact could resemble a sign at reduced scale.',
        'resolution':'Native pixels magnified 4× with nearest-neighbor sampling show an isolated speck, not a horizontal minus glyph; numeric token transcribed as positive 116323.99.',
        'detail_path':str(detail),'detail_sha256':sha(detail),
        'detail_parent':'si-02-right-top.png','detail_crop_box':[280,70,530,135],'display_resize':[1000,260],
        'resampling':'nearest; no interpolation or numeral editing'}],
    'uncertainties':[{'scope':'All 170 trailing markers','status':'meaning unverified','handling':'Raw o retained; normalized value null.'},
        {'scope':'SI header year/journal','status':'source identity discrepancy retained','handling':'Audited DOI/content pairing is preserved; header is not silently corrected.'},
        {'scope':'Remaining pages 3–14','status':'all numerical cells pending','handling':'No inferred zeros, counts, symmetry-expanded values or placeholder measurements.'}],
    'programmatic_checks':checks,'programmatic_check_count':len(checks),
    'manual_source_comparison':'Every one of the 170 rows and its seven printed cells was read from the displayed native crops and compared during transcription; this is same-author source verification, not an independent audit.',
    'source_pdf_sha256':D['sha256'],'prior_partial_source_audit_sha256':sha(B/'source-scientific-audit.json'),
    'preserved_author_file_hashes':old_hashes,
    'bound_files':{str(B/name):sha(B/name) for name in ['si-reflections-pages01-02.tsv','si-reflections-transcription.json',
        'si-numerical-assets.json','prepare_si_numerical_evidence.py','build_si_transcription_checkpoint.py']},
    'bound_original_evidence':{a['path']:a['sha256'] for a in E['assets']},
    'remaining_cells_by_page_block':remaining,'training_eligible':False,'published':False}
write(B/'si-numerical-verification-checkpoint.json',checkpoint)
print(json.dumps({'pages':[1,2],'rows':170,'numeric_cells':1020,'markers':170,'negative_observations':5,
    'author_checks':len(checks),'remaining_pages':list(range(3,15)),'independent_numerical_audit':'pending'}))
