"""Package only the manually read final SI13-14 rows; whole-SI review remains separate."""
from pathlib import Path
from decimal import Decimal
from datetime import datetime,timezone
import csv,hashlib,json
B=Path(__file__).resolve().parent;stem='si-pages13-14'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf8'))
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
outs={k:B/(stem+s) for k,s in {'tsv':'-reflections.tsv','transcription':'-transcription.json',
    'checkpoint':'-author-checkpoint.json','manifest':'-manifest.json','notes':'-author-notes.md'}.items()}
assert not any(p.exists() for p in outs.values()),'Preserve a frozen revision before any corrections.'
preserved=read(B/(stem+'-preserved-inputs.json'))
verified=read(B/(stem+'-source-verification.json'))
source=read(B/'source-inventory.json')['source_documents']['si']
assets=read(B/(stem+'-assets.json'));amap={a['id']:a for a in assets['assets']}
blocks=read(B/(stem+'-author-blocks.json'))
checks=[]
def check(name,ok):checks.append({'check':name,'passed':bool(ok)});assert ok,name
check('Actual source still matches retained generation2 SI bytes',sha(source['path'])==source['sha256']==assets['source_sha256'])
check('Current group generation remains2',read(B.parents[2]/'ledger.json')['groups']['10.1021_jp0219348']['generation']==2)
check('All four incoming/legacy source copies remain unchanged',len(verified['sources'])==4 and all(sha(s['path'])==s['sha256'] for s in verified['sources']))
check('All prior source/chunk/history files remain unchanged',all(sha(p)==h for p,h in preserved.items()))
check('Every native page/header/column crop remains unchanged',len(assets['assets'])==12 and all(sha(a['path'])==a['sha256'] for a in assets['assets']))
expected_counts={'13L':45,'13R':45,'14L':25,'14R':24}
check('All four source blocks have their visibly counted row totals',{k:len(v) for k,v in blocks.items()}==expected_counts)
columns=['h','k','l','Fcal2','Fobs2','sigma_Fobs2','marker']
labels={'h':'h','k':'k','l':'l','Fcal2':'Fcal^2','Fobs2':'Fobs^2','sigma_Fobs2':'σ(Fobs^2)',
        'marker':'unheaded trailing open-circle/o-like marker'}
rows=[];flat=[];negative=[];zeros=[];ids=[]
for key,lines in blocks.items():
    page=int(key[:-1]);block=key[-1]
    for rn,line in enumerate(lines,1):
        tokens=line.split();check(f'{key}/row{rn} has seven source fields',len(tokens)==7)
        raw=dict(zip(columns,tokens));rid=f'si-p{page:02d}-{block}-r{rn:03d}'
        cropid=f'si-{page:02d}-'+('left' if block=='L' else 'right')+('-top' if rn<=25 else '-bottom')
        crop=amap[cropid];cells=[]
        for col in columns:
            cid=rid+'-'+col;ids.append(cid);number=None
            if col!='marker':
                dec=Decimal(raw[col]);check(cid+' finite decimal',dec.is_finite())
                number=int(raw[col]) if col in columns[:3] else float(dec)
                check(cid+' exact numeric decimal roundtrip',Decimal(str(number))==dec)
            else:check(cid+' o-like marker remains uninterpreted',raw[col]=='o')
            evidence={'source_id':'heo2003-si','source_path':source['path'],'source_sha256':source['sha256'],
                'supporting_table':1,'pdf_page':page,'printed_page':40+page,'column_block':block,
                'row_in_block':rn,'column_key':col,'printed_column_label':labels[col],
                'locator':f'SI PDF p.{page} (printed p.{40+page}), Supporting Table1, '+('left' if block=='L' else 'right')+f' block, body row {rn}, {labels[col]}',
                'original_crop_id':cropid,'original_crop_path':crop['path'],'original_crop_sha256':crop['sha256'],
                'row_in_selected_crop':rn if rn<=25 else rn-24,
                'crop_overlap_policy':'Top and bottom native crops overlap at body row25, when present; that row is transcribed once and linked to the top crop. Body row26 is bottom-crop row2. Page14 left ends at row25; page14 right ends at row24. Blank lower areas do not add rows.'}
            cell={'cell_id':cid,'raw_text':raw[col],'numeric_value':number,'unit':None,
                  'unit_status':'not_applicable_index' if col in columns[:3] else 'not_applicable_marker' if col=='marker' else 'unreported',
                  'transcription_status':'manually_transcribed_from_original_scan',
                  'source_comparison_status':'visually_compared_by_transcription_author',
                  'independent_numerical_audit':'pending','evidence':evidence}
            if cid=='si-p14-R-r016-Fobs2':
                cell['glyph_review_note']='A separated tiny scan mark lies near the tops of the digits, above the position of a printed minus. Native full-column and magnified pixel inspection supports unsigned2613.68; this reading does not use the physical meaning of a squared structure factor.'
            cells.append(cell)
            if col=='Fobs2' and number<0:negative.append({'cell_id':cid,'raw_text':raw[col],'numeric_value':number})
            if col=='Fobs2' and number==0:zeros.append({'cell_id':cid,'raw_text':raw[col],'numeric_value':number})
        rows.append({'row_id':rid,'source_sample_label':'In66-X, as Supporting Table1 title',
                     'hkl':[int(raw[c]) for c in columns[:3]],'raw_cells':raw,'cells':cells})
        flat.append({'page':page,'block':block,'row':rn,**raw})
expected_negative={
    '13L':{3:'-4797.89',5:'-9011.54',7:'-3199.36',14:'-5361.93',34:'-5413.47',38:'-10033.97',43:'-5080.73',45:'-4930.2'},
    '13R':{3:'-11780.12',7:'-6237.72',32:'-2852.44',34:'-5048.82',41:'-8375.93',45:'-7043.14'},
    '14L':{12:'-14134',13:'-10043.23',24:'-9588.01'},
    '14R':{1:'-713.85',7:'-7069.08',11:'-1091.17',12:'-5396.2',14:'-782.97'}}
expected=[(f'si-p{int(k[:-1]):02d}-{k[-1]}-r{rn:03d}-Fobs2',v) for k,x in expected_negative.items() for rn,v in x.items()]
check('All22 visibly negative observed factors retain exact signs and digits',[(x['cell_id'],x['raw_text']) for x in negative]==expected)
check('No zero Fobs2 appears on these two pages',zeros==[])
check('139rows and973unique cells; all834numeric fields resolved',len(rows)==139 and len(set(ids))==973 and sum(c['numeric_value'] is not None for r in rows for c in r['cells'])==834)
previous=[]
for f in ['si-reflections-transcription.json','si-pages03-04-transcription.json','si-pages05-06-transcription.json',
          'si-pages07-08-transcription.json','si-pages09-10-transcription.json','si-pages11-12-transcription.json']:
    previous.extend(read(B/f)['rows'])
old_hkl={tuple(r['hkl']) for r in previous};new_hkl={tuple(r['hkl']) for r in rows}
check('139unique new indices are distinct from preceding1070rows',len(previous)==1070 and len(new_hkl)==139 and not old_hkl.intersection(new_hkl))
old_uncertain=read(B/'si-pages11-12-transcription.json')['unresolved_numeric_tokens_in_chunk']
check('Earlier two sign uncertainties remain null and unimputed',len(old_uncertain)==2 and all(x['numeric_value'] is None for x in old_uncertain))
with outs['tsv'].open('w',encoding='utf8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['page','block','row']+columns,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(flat)
with outs['tsv'].open(encoding='utf8',newline='') as f:back=list(csv.DictReader(f,delimiter='\t'))
check('TSV preserves all raw field strings exactly',len(back)==139 and all(all(a[k]==str(b[k]) for k in a) for a,b in zip(back,flat)))
check('Prior source/history/chunk hashes unchanged after packaging',all(sha(p)==h for p,h in preserved.items()))
now=datetime.now(timezone.utc).isoformat()
counts={'rows':139,'numeric_cells':834,'resolved_numeric_cells':834,'unresolved_sign_cells':0,
        'markers':139,'total_cells':973,'negative_Fobs2':22,'zero_Fobs2':0}
policies={'numeric_precision':'Raw decimal strings are authoritative; no rescaling, clipping, unit inference, sign imputation, symmetry expansion or merging.',
          'marker':'ASCII o preserves the unheaded scanned open-circle/lowercase-o-like glyph. Its semantic meaning and exact Unicode identity are unestablished; it is not zero or an acceptance flag.',
          'scientific_scope':'Only reflection indices, calculated/observed squared structure factors and esds. No atomic coordinates, occupancy model, CIF, exact ordered specimen or DFT-ready structure is created.',
          'source_identity_caveat':'The original header prints ©2002 American Chemical Society, J. Phys. Chem. A, Heo jp0219348. The previously audited main/SI pairing and header discrepancy are not silently repaired.',
          'scope_boundary':'This author chunk covers only SI13-14. It does not mark the full SI audited or scientifically complete. SI11-12 retains two unresolved signs, and whole-document reconciliation belongs to the separate review process.'}
write(outs['transcription'],{'schema':'mattersyn-si-reflection-transcription-chunk/1','source_id':'heo2003',
    'title_as_printed':'Observed and Calculated Structure Factors Squared with Esds for In66-X',
    'author':'/root/peng1998_reader_assets','created_at':now,'pages':[13,14],'source_generation':2,
    'source_path':source['path'],'source_sha256':source['sha256'],
    'status':'author_transcribed_source_compared_independent_numerical_audit_pending',
    'counts':counts,'field_order':columns,'original_header_labels':labels,'rows':rows,
    'negative_observations':negative,'zero_observations':zeros,'unresolved_numeric_tokens_in_chunk':[],
    'policies':policies,'complete_document_transcription':False,'independent_audit_passed':False,
    'training_eligible':False,'published':False})
outs['notes'].write_text('''# Heo SI pages13–14: author reading scope

The four retained incoming/legacy main and SI files were actually rehashed before reading and matched generation2. The SI hash remains3b2e262af1932ed04cfddd596958c92d89c37099ab9dad8c4ce1f11254d4acc6.

The author visually read both native full pages (printed53–54), both column headers, all source body rows, and the blank lower portion of the final page. Page13 contains45left+45right rows; page14 contains25left+24right rows. All139rows/834numeric positions/139markers were manually transcribed and compared again to the native scan. No OCR-generated numeric data was used.

The22negative observed squared factors remain signed. There is no zero observed factor in this chunk. Integer and decimal strings retain their printed precision. The trailing unheaded o-like glyph remains semantically uninterpreted.

The small mark before page14 right row16 Fobs²2613.68 was inspected in the native parent crop and magnified original-pixel detail. It lies near the digit tops, above the printed-minus position; the source reading remains2613.68 based on glyph geometry rather than physical expectations. No unresolved numeric glyph was identified on these two pages.

The earlier two unresolved signs on SI11–12 are unchanged and unimputed. Whole-SI completion, numerical reconciliation and independent audit of this chunk remain separate gates. This package creates no CIF, atom coordinates or exact specimen join.
''',encoding='utf8')
bound=[B/(stem+s) for s in ['-source-verification.json','-assets.json','-preserved-inputs.json','-author-blocks.json']]
bound += [B/'prepare_si_pages13_14.py',B/'author_si_pages13_14.py',Path(__file__),outs['tsv'],outs['transcription'],outs['notes']]
write(outs['checkpoint'],{'schema':'mattersyn-si-numerical-chunk-author-checkpoint/1','source_id':'heo2003',
    'author':'/root/peng1998_reader_assets','created_at':now,'source_generation':2,
    'status':'author_source_comparison_complete_independent_numerical_audit_pending',
    'actual_scope':{'pages_transcribed':[13,14],'native_crop_pages_visually_read':[13,14],
                   'native_full_pages_visually_viewed':[13,14],'printed_pages':[53,54],**counts,
                   'rows_per_page_block':expected_counts},
    'manual_source_comparison':'Every source row and all seven columns were visually read and compared again against native pixels. Both full-page headers/page numbers and the final blank lower region were inspected. Crop overlap row25 is counted once. Page14 has25left/24right rows, not two full45-row blocks. Source glyph geometry at14R16 was separately inspected without physical sign inference.',
    'complete_document_transcription':False,'whole_SI_completion_authorized_by_this_chunk':False,
    'remaining_untranscribed_pages_in_retained_14_page_SI':[],
    'remaining_unaudited_pages_for_this_chunk':[13,14],
    'remaining_gaps':['Distinct independent audit of SI13-14.','Whole-SI chunk reconciliation and completeness review remain separate.','SI11R35 Fobs² and SI12L12 Fcal² signs remain unresolved from retained pixels.','Trailing marker semantics and structure-factor units remain unestablished.','No CIF, atomic coordinate model or exact specimen linkage inferred.'],
    'unresolved_numeric_tokens_in_chunk':[],'policies':policies,
    'programmatic_check_count':len(checks),'programmatic_checks':checks,
    'preserved_prior_files':preserved,'source_pdf_sha256':source['sha256'],
    'bound_files':{str(p):sha(p) for p in bound},
    'bound_original_evidence':{a['path']:a['sha256'] for a in assets['assets']},
    'independent_audit_passed':False,'training_eligible':False,'published':False})
write(outs['manifest'],{'schema':'mattersyn-si-numerical-chunk-freeze/1','source_id':'heo2003',
    'author':'/root/peng1998_reader_assets','created_at':now,'pages':[13,14],'source_generation':2,
    'counts':{**counts,'checks':len(checks)},'source_sha256':source['sha256'],
    'files':{str(p):sha(p) for p in bound+[outs['checkpoint']]},
    'original_evidence':{a['path']:a['sha256'] for a in assets['assets']},
    'independent_audit':'pending','complete_SI_review':False,'published':False,'training_eligible':False})
print(json.dumps({'counts':{**counts,'checks':len(checks)},'hashes':{k:sha(p) for k,p in outs.items()},
                  'preserved_prior_files':len(preserved)},indent=2))
