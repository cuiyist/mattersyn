"""Freeze the separately authored SI 11-12 native-pixel transcription.

One degraded sign remains unresolved: preserve the magnitude and withhold the
signed number. This is an author package, not an independent numerical audit.
"""
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone
import csv, hashlib, json

B = Path(__file__).resolve().parent
stem = 'si-pages11-12'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text(encoding='utf8'))
def write(p, value):
    Path(p).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')

outputs = {k:B/(stem+s) for k,s in {
    'tsv':'-reflections.tsv','transcription':'-transcription.json',
    'checkpoint':'-author-checkpoint.json','manifest':'-manifest.json'}.items()}
assert not any(p.exists() for p in outputs.values()), 'Do not overwrite a frozen chunk.'
preserved = read(B/(stem+'-preserved-inputs.json'))
source = read(B/'source-inventory.json')['source_documents']['si']
assets = read(B/(stem+'-assets.json'))
amap = {a['id']:a for a in assets['assets']}
blocks = read(B/(stem+'-author-blocks.json'))
uncertainty = read(B/(stem+'-sign-uncertainty.json'))
checks = []
def check(name, ok):
    checks.append({'check':name,'passed':bool(ok)})
    assert ok, name

check('Every previously frozen source/chunk/audit is unchanged', all(sha(p)==h for p,h in preserved.items()))
check('Actual source PDF still matches both source inventory and crop provenance',
      sha(source['path']) == source['sha256'] == assets['source_sha256'])
check('All twelve native page/header/column assets are unchanged', len(assets['assets'])==12 and all(sha(a['path'])==a['sha256'] for a in assets['assets']))
check('Exactly four 45-row blocks in source reading order', list(blocks)==['11L','11R','12L','12R'] and all(len(b)==45 for b in blocks.values()))
columns = ['h','k','l','Fcal2','Fobs2','sigma_Fobs2','marker']
labels = {'h':'h','k':'k','l':'l','Fcal2':'Fcal^2','Fobs2':'Fobs^2','sigma_Fobs2':'σ(Fobs^2)',
          'marker':'unheaded trailing open-circle/o-like marker'}
uncertain_id = 'si-p11-R-r035-Fobs2'
editorial_token = '[sign_unresolved]1965.46'
rows, flat, negative, zeros, unresolved = [], [], [], [], []
all_cell_ids = []
for block_key, lines in blocks.items():
    page, block = int(block_key[:-1]), block_key[-1]
    for rn, line in enumerate(lines, 1):
        tokens = line.split()
        check(f'{block_key}/row{rn} has seven raw fields', len(tokens)==7)
        raw = dict(zip(columns, tokens))
        rid = f'si-p{page:02d}-{block}-r{rn:03d}'
        crop_id = f'si-{page:02d}-'+('left' if block=='L' else 'right')+('-top' if rn<=25 else '-bottom')
        crop = amap[crop_id]
        cells = []
        for column in columns:
            cid = rid+'-'+column
            all_cell_ids.append(cid)
            ambiguous = cid == uncertain_id
            value = None
            if ambiguous:
                check('Only the explicitly qualified sign has an editorial token', raw[column]==editorial_token)
            elif column != 'marker':
                dec = Decimal(raw[column])
                check(cid+' decimal is finite', dec.is_finite())
                value = int(raw[column]) if column in columns[:3] else float(dec)
                check(cid+' exact decimal round-trip', Decimal(str(value))==dec)
            else:
                check(cid+' unheaded marker remains uninterpreted o', raw[column]=='o')
            evidence = {
                'source_id':'heo2003-si','source_path':source['path'],'source_sha256':source['sha256'],
                'supporting_table':1,'pdf_page':page,'printed_page':40+page,
                'column_block':block,'row_in_block':rn,'column_key':column,'printed_column_label':labels[column],
                'locator':f'SI PDF p.{page} (printed p.{40+page}), Supporting Table1, '+('left' if block=='L' else 'right')+f' block, body row {rn}, {labels[column]}',
                'original_crop_id':crop_id,'original_crop_path':crop['path'],'original_crop_sha256':crop['sha256'],
                'row_in_selected_crop':rn if rn<=25 else rn-24,
                'crop_overlap_policy':'Top and bottom native crops overlap at body row 25. That row is transcribed once and linked to the top crop. Bottom-crop row 1 is the overlap row; source body row 26 is crop row 2.'}
            cell = {
                'cell_id':cid,'raw_text':raw[column],'numeric_value':value,'unit':None,
                'unit_status':'not_applicable_index' if column in columns[:3] else 'not_applicable_marker' if column=='marker' else 'unreported',
                'transcription_status':'source_sign_unresolved' if ambiguous else 'manually_transcribed_from_original_scan',
                'source_comparison_status':'visually_compared_sign_unresolved' if ambiguous else 'visually_compared_by_transcription_author',
                'independent_numerical_audit':'pending','evidence':evidence}
            if ambiguous:
                cell.update({
                    'visible_digits':'1965.46','magnitude_value':1965.46,
                    'sign_status':'unresolved_from_retained_scan','signed_value_candidates':[-1965.46,1965.46],
                    'raw_text_includes_editorial_annotation':True,
                    'editorial_annotation':'[sign_unresolved] is a curator label, not printed source text. The clear digits are 1965.46.',
                    'uncertainty_note':'A tiny degraded pre-digit mark does not establish either a minus sign or the absence of a sign. The signed numeric value is withheld; no inference from calculated factors, neighboring rows or expected physics is applied.'})
                unresolved.append({'cell_id':cid,'visible_digits':'1965.46','raw_text':raw[column],
                                   'numeric_value':None,'magnitude_value':1965.46,'signed_value_candidates':[-1965.46,1965.46],
                                   'reason':cell['uncertainty_note'],'evidence':evidence})
            cells.append(cell)
            if column=='Fobs2' and value is not None and value<0:
                negative.append({'cell_id':cid,'raw_text':raw[column],'numeric_value':value})
            if column=='Fobs2' and value==0:
                zeros.append({'cell_id':cid,'raw_text':raw[column],'numeric_value':value})
        rows.append({'row_id':rid,'source_sample_label':'In66-X, as Supporting Table1 title',
                     'hkl':[int(raw[c]) for c in columns[:3]],'raw_cells':raw,'cells':cells})
        flat.append({'page':page,'block':block,'row':rn,**raw})

expected_negative = {
    '11L':{2:'-5689.84',7:'-14377.69',9:'-8556.85',11:'-9097.89',18:'-10885.13',25:'-8302.98',26:'-8847.86',33:'-232.84',34:'-9425.42',39:'-9830.96',42:'-3608.98'},
    '11R':{3:'-5505.61',5:'-3839.49',11:'-3376.28',14:'-14203.05',17:'-4535.62',21:'-1106.02',28:'-7778.96',30:'-789.73',44:'-671.66'},
    '12L':{7:'-10227.36',8:'-3117.84',13:'-4154.9',14:'-8532.08',16:'-9025.92',24:'-9178.61',29:'-9505.68',30:'-9313.5',42:'-14668.75',44:'-8414.55'},
    '12R':{6:'-8013.36',19:'-4245.07',24:'-5662.41',26:'-12959.55',31:'-413.74',39:'-9000.3'}}
expected = [(f'si-p{int(k[:-1]):02d}-{k[-1]}-r{rn:03d}-Fobs2',raw) for k,rs in expected_negative.items() for rn,raw in rs.items()]
check('Every one of the 36 unambiguously negative observations retains its exact sign/digits',
      [(c['cell_id'],c['raw_text']) for c in negative]==expected)
check('No zero observed factor is printed in this chunk', zeros==[])
check('Only one numeric field is withheld and its visible magnitude is preserved',
      len(unresolved)==1 and unresolved[0]['cell_id']==uncertain_id and unresolved[0]['numeric_value'] is None)
check('180 rows, 1260 unique cells and 1079 resolved numeric values',
      len(rows)==180 and len(set(all_cell_ids))==1260 and sum(c['numeric_value'] is not None for r in rows for c in r['cells'])==1079)
previous = []
for filename in ['si-reflections-transcription.json','si-pages03-04-transcription.json','si-pages05-06-transcription.json',
                 'si-pages07-08-transcription.json','si-pages09-10-transcription.json']:
    previous.extend(read(B/filename)['rows'])
old_hkl, new_hkl = {tuple(r['hkl']) for r in previous}, {tuple(r['hkl']) for r in rows}
check('180 unique new reflection indices do not duplicate the preceding 890 rows',
      len(previous)==890 and len(new_hkl)==180 and not old_hkl.intersection(new_hkl))
check('The initial reading archive and source-sign qualification are internally consistent',
      uncertainty['numeric_value'] is None and uncertainty['clear_visible_digits']=='1965.46'
      and all(sha(p)==h for p,h in uncertainty['archived_initial_reading'].items()))
check('Earlier source/chunk/audit files are still unchanged after packaging checks',all(sha(p)==h for p,h in preserved.items()))

now = datetime.now(timezone.utc).isoformat()
counts = {'rows':180,'numeric_cells':1080,'resolved_numeric_cells':1079,'unresolved_sign_cells':1,
          'markers':180,'total_cells':1260,'unambiguously_negative_Fobs2':36,'zero_Fobs2':0}
policies = {
    'numeric_precision':'Raw decimal strings are authoritative when readable. No rescaling, truncation, sign clipping, unit inference, symmetry expansion or merging.',
    'uncertain_sign':'One clear magnitude 1965.46 has an unresolved leading sign. Its signed numeric_value is null. Both signs remain candidates. The TSV and raw_text use an explicitly editorial [sign_unresolved] prefix; this token must not be parsed as a positive measurement.',
    'marker':'ASCII o retains the scanned unheaded open-circle/lowercase-o-like glyph. Its meaning and exact Unicode identity are unestablished. It is not numeric zero or an acceptance flag.',
    'scientific_scope':'Reflection indices, calculated/observed squared structure factors and esds; not atomic coordinates, a CIF, atom occupancies or a DFT-ready ordered structure.',
    'source_identity_caveat':'The retained SI prints ©2002 ACS, J. Phys. Chem. A, Heo jp0219348. Existing audited main/SI pairing and header discrepancy are preserved.'}
with outputs['tsv'].open('w',encoding='utf8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=['page','block','row']+columns,delimiter='\t',lineterminator='\n')
    writer.writeheader();writer.writerows(flat)
with outputs['tsv'].open(encoding='utf8',newline='') as f:
    roundtrip=list(csv.DictReader(f,delimiter='\t'))
check('Flat TSV retains every raw token including the editorial uncertainty label',
      all(all(a[k]==str(b[k]) for k in a) for a,b in zip(roundtrip,flat)) and len(roundtrip)==180)
write(outputs['transcription'],{
    'schema':'mattersyn-si-reflection-transcription-chunk/1','source_id':'heo2003',
    'title_as_printed':'Observed and Calculated Structure Factors Squared with Esds for In66-X',
    'author':'/root/peng1998_reader_assets','created_at':now,'pages':[11,12],
    'source_path':source['path'],'source_sha256':source['sha256'],
    'status':'author_source_compared_one_sign_unresolved_independent_numerical_audit_pending',
    'counts':counts,'field_order':columns,'original_header_labels':labels,'rows':rows,
    'negative_observations':negative,'zero_observations':zeros,'unresolved_numeric_tokens_in_chunk':unresolved,
    'policies':policies,'complete_document_transcription':False,'independent_audit_passed':False,'training_eligible':False,'published':False})
bound = [B/(stem+s) for s in ['-assets.json','-author-blocks.json','-preserved-inputs.json','-sign-uncertainty.json']]
bound += [B/'prepare_si_pages11_12.py',B/'author_si_pages11_12.py',B/'qualify_si_pages11_12_sign.py',Path(__file__),
          outputs['tsv'],outputs['transcription']]
bound += [Path(p) for p in uncertainty['archived_initial_reading']]
write(outputs['checkpoint'],{
    'schema':'mattersyn-si-numerical-chunk-author-checkpoint/1','source_id':'heo2003',
    'author':'/root/peng1998_reader_assets','created_at':now,
    'status':'author_comparison_complete_one_sign_unresolved_independent_numerical_audit_pending',
    'actual_scope':{'pages_transcribed':[11,12],'native_crop_pages_visually_read':[11,12],
                    'native_full_pages_visually_viewed':[11,12],'printed_pages':[51,52],
                    **counts,'rows_per_page_block':{k:len(v) for k,v in blocks.items()}},
    'manual_source_comparison':'The author read every row and seven fields from all eight native column crops, performed a second visual comparison, reread both headers and viewed both full native pages. Body row 25 overlaps top/bottom crops and is counted once. A degraded mark before page 11 right-block row 35 Fobs^2 leaves its sign unresolved; the clear magnitude and original source locator remain. The source pixels were not changed. Independent numerical audit is a separate pending gate.',
    'author_prefreeze_proofreading':{'numeric_digit_changes':0,'sign_qualifications':1,
                                   'history_path':str(B/(stem+'-sign-uncertainty.json'))},
    'complete_document_transcription':False,'remaining_untranscribed_pages':[13,14],
    'remaining_unaudited_pages':[11,12,13,14],'remaining_row_count':None,
    'unresolved_numeric_tokens_in_chunk':unresolved,'policies':policies,
    'programmatic_check_count':len(checks),'programmatic_checks':checks,'preserved_prior_files':preserved,
    'source_pdf_sha256':source['sha256'],'bound_files':{str(p):sha(p) for p in bound},
    'bound_original_evidence':{a['path']:a['sha256'] for a in assets['assets']},
    'independent_audit_passed':False,'training_eligible':False,'published':False})
write(outputs['manifest'],{
    'schema':'mattersyn-si-numerical-chunk-freeze/1','source_id':'heo2003',
    'author':'/root/peng1998_reader_assets','created_at':now,'pages':[11,12],
    'counts':{**counts,'checks':len(checks)},'source_sha256':source['sha256'],
    'files':{str(p):sha(p) for p in bound+[outputs['checkpoint']]},
    'original_evidence':{a['path']:a['sha256'] for a in assets['assets']},
    'unresolved_sign_cell_ids':[uncertain_id],
    'independent_audit':'pending','published':False,'training_eligible':False})
print(json.dumps({'counts':{**counts,'checks':len(checks)},'hashes':{k:sha(p) for k,p in outputs.items()}},indent=2))
