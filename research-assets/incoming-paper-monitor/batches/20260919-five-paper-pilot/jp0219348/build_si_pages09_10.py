"""Package the manual SI 9-10 reading without altering any earlier chunk."""
from pathlib import Path
from decimal import Decimal
from datetime import datetime,timezone
import csv,hashlib,json
B=Path(__file__).resolve().parent;stem='si-pages09-10'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
write=lambda p,x:Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
outputs=[B/(stem+s) for s in ['-reflections.tsv','-transcription.json','-author-checkpoint.json']]
assert not any(p.exists() for p in outputs),'Frozen output already exists; preserve revision history before correction.'
preserved=read(B/(stem+'-preserved-inputs.json'))
assert all(sha(p)==h for p,h in preserved.items()),'An earlier source/chunk/audit changed.'
source=read(B/'source-inventory.json')['source_documents']['si']
assets=read(B/(stem+'-assets.json'));amap={x['id']:x for x in assets['assets']}
blocks=read(B/(stem+'-author-blocks.json'))
assert sha(source['path'])==source['sha256']==assets['source_sha256']
assert all(sha(a['path'])==a['sha256'] for a in assets['assets'])
columns=['h','k','l','Fcal2','Fobs2','sigma_Fobs2','marker']
labels={'h':'h','k':'k','l':'l','Fcal2':'Fcal^2','Fobs2':'Fobs^2','sigma_Fobs2':'σ(Fobs^2)','marker':'unheaded trailing open-circle/o-like marker'}
checks=[]
def check(name,ok):
 checks.append({'check':name,'passed':bool(ok)});assert ok,name
check('Exactly four source blocks in page order',list(blocks)==['9L','9R','10L','10R'])
rows=[];flat=[];negative=[];zeros=[];cell_ids=[]
for key,lines in blocks.items():
 page=int(key[:-1]);block=key[-1];check(key+' has 45 visibly counted body rows',len(lines)==45)
 for rn,line in enumerate(lines,1):
  tokens=line.split();check(f'{key}/row{rn} retains seven raw tokens',len(tokens)==7)
  raw=dict(zip(columns,tokens));rid=f'si-p{page:02d}-{block}-r{rn:03d}'
  cropid=f'si-{page:02d}-'+('left' if block=='L' else 'right')+('-top' if rn<=25 else '-bottom')
  crop=amap[cropid];hkl=[int(raw[c]) for c in columns[:3]];cells=[]
  for c in columns:
   cid=rid+'-'+c;cell_ids.append(cid);number=None
   if c!='marker':
    dec=Decimal(raw[c]);check(cid+' decimal is finite',dec.is_finite())
    number=int(raw[c]) if c in columns[:3] else float(dec)
    check(cid+' exact numeric decimal roundtrip',Decimal(str(number))==dec)
   else:check(cid+' marker remains uninterpreted o',raw[c]=='o')
   evidence={'source_id':'heo2003-si','source_path':source['path'],'source_sha256':source['sha256'],'supporting_table':1,'pdf_page':page,'printed_page':40+page,'column_block':block,'row_in_block':rn,'column_key':c,'printed_column_label':labels[c],
     'locator':f'SI PDF p.{page} (printed p.{40+page}), Supporting Table1, '+('left' if block=='L' else 'right')+f' block, body row{rn}, {labels[c]}',
     'original_crop_id':cropid,'original_crop_path':crop['path'],'original_crop_sha256':crop['sha256'],'row_in_selected_crop':rn if rn<=25 else rn-24,'crop_overlap_policy':'Top and bottom native crops overlap at row25; the row is transcribed once and uses its top crop. Bottom-row numbering includes overlap row25 as row1.'}
   cell={'cell_id':cid,'raw_text':raw[c],'numeric_value':number,'unit':None,'unit_status':'not_applicable_index' if c in columns[:3] else 'not_applicable_marker' if c=='marker' else 'unreported','transcription_status':'manually_transcribed_from_original_scan','source_comparison_status':'visually_compared_by_transcription_author','independent_numerical_audit':'pending','evidence':evidence}
   cells.append(cell)
   if c=='Fobs2' and number<0:negative.append({'cell_id':cid,'raw_text':raw[c],'numeric_value':number})
   if c=='Fobs2' and number==0:zeros.append({'cell_id':cid,'raw_text':raw[c],'numeric_value':number})
  rows.append({'row_id':rid,'source_sample_label':'In66-X, as Supporting Table1 title','hkl':hkl,'raw_cells':raw,'cells':cells});flat.append({'page':page,'block':block,'row':rn,**raw})
expected_negative={'9L':{3:'-971.07',12:'-4703.37',28:'-7218.02',30:'-958.11',33:'-902.85',35:'-4889.59',37:'-8724.8'},'9R':{7:'-2590.67',14:'-1047.77',15:'-7450.98',18:'-12224.13',19:'-12689.99',39:'-1334.92',40:'-6694.15',41:'-931.38'},'10L':{8:'-1657.98',9:'-8759.87',21:'-873.14',27:'-1060.85',32:'-4545.68',34:'-9545.04',42:'-963.95'},'10R':{5:'-6844.48',22:'-9384.73',26:'-7199.85'}}
exp=[(f'si-p{int(k[:-1]):02d}-{k[-1]}-r{rn:03d}-Fobs2',raw) for k,v in expected_negative.items() for rn,raw in v.items()]
check('All 25 negative Fobs2 values preserved',[(x['cell_id'],x['raw_text']) for x in negative]==exp)
check('Printed zero distinguished from marker',[(x['cell_id'],x['raw_text']) for x in zeros]==[('si-p10-R-r010-Fobs2','0')])
check('Native reread retains six-digit Fcal2 at10R41',rows[135+40]['raw_cells']['Fcal2']=='190000.97')
check('180 rows and1260 unique cell IDs',len(rows)==180 and len(set(cell_ids))==1260)
previous=[]
for f in ['si-reflections-transcription.json','si-pages03-04-transcription.json','si-pages05-06-transcription.json','si-pages07-08-transcription.json']:previous+=read(B/f)['rows']
old_hkl={tuple(r['hkl']) for r in previous};new_hkl={tuple(r['hkl']) for r in rows}
check('180 new unique hkl distinct from preceding710 rows',len(previous)==710 and len(new_hkl)==180 and not old_hkl.intersection(new_hkl))
check('Prior source/chunk/audit files remain unchanged',all(sha(p)==h for p,h in preserved.items()))
with outputs[0].open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['page','block','row']+columns,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(flat)
now=datetime.now(timezone.utc).isoformat()
policy={'numeric_precision':'Raw decimal strings are authoritative. No rescaling, truncation, sign clipping, unit inference, symmetry expansion or merging.','marker':'ASCII o retains a scanned open-circle/lowercase-o-like glyph. Its meaning and exact Unicode identity are not established; it is not a numeric zero or acceptance flag.','scientific_scope':'Reflection indices, calculated/observed squared structure factors and esds; not atomic coordinates, a CIF, atom occupancies or a DFT-ready ordered structure.','source_identity_caveat':'SI prints ©2002 ACS, J. Phys. Chem. A, Heo jp0219348. Existing audited main/SI pairing and header discrepancy remain unchanged.'}
review_note={'cell_id':'si-p10-R-r041-Fcal2','initial_author_typing':'19000.97','final_raw_text':'190000.97','reason':'Author second visual comparison against native scan found one omitted zero before any chunk freeze. Original pixels were not changed. This is author proofreading, not an independent-auditor correction.','evidence_crop_id':'si-10-right-bottom'}
write(outputs[1],{'schema':'mattersyn-si-reflection-transcription-chunk/1','source_id':'heo2003','title_as_printed':'Observed and Calculated Structure Factors Squared with Esds for In66-X','author':'/root/peng1998_reader_assets','created_at':now,'pages':[9,10],'source_path':source['path'],'source_sha256':source['sha256'],'status':'author_transcribed_source_compared_independent_numerical_audit_pending','field_order':columns,'original_header_labels':labels,'rows':rows,'negative_observations':negative,'zero_observations':zeros,'policies':policy,'unresolved_numeric_tokens_in_chunk':[],'complete_document_transcription':False,'independent_audit_passed':False,'training_eligible':False,'published':False})
bound_files=[B/(stem+'-assets.json'),B/(stem+'-author-blocks.json'),B/(stem+'-preserved-inputs.json'),B/'prepare_si_pages09_10.py',B/'author_si_pages09_10.py',Path(__file__),outputs[0],outputs[1]]
write(outputs[2],{'schema':'mattersyn-si-numerical-chunk-author-checkpoint/1','source_id':'heo2003','author':'/root/peng1998_reader_assets','created_at':now,'status':'author_source_comparison_complete_independent_numerical_audit_pending','actual_scope':{'pages_transcribed':[9,10],'native_crop_pages_visually_read':[9,10],'native_full_pages_visually_viewed':[9,10],'printed_pages':[49,50],'rows':180,'numeric_cells':1080,'marker_cells':180,'total_cells':1260,'negative_Fobs2':25,'zero_Fobs2':1,'rows_per_page_block':{k:len(v) for k,v in blocks.items()}},'manual_source_comparison':'The author actually read all180rows and all seven fields from the eight native column crops, reread both headers and viewed both native full pages. All raw strings were compared against source pixels. Row25 overlaps top/bottom crops and is counted once. One pre-freeze typing omission was corrected during author comparison; independent numerical audit is a separate pending gate.','author_prefreeze_proofreading':[review_note],'complete_document_transcription':False,'remaining_untranscribed_pages':[11,12,13,14],'remaining_unaudited_pages':[9,10,11,12,13,14],'remaining_row_count':None,'policies':policy,'programmatic_check_count':len(checks),'programmatic_checks':checks,'preserved_prior_files':preserved,'source_pdf_sha256':source['sha256'],'bound_files':{str(p):sha(p) for p in bound_files},'bound_original_evidence':{x['path']:x['sha256'] for x in assets['assets']},'independent_audit_passed':False,'training_eligible':False,'published':False})
write(B/(stem+'-manifest.json'),{'schema':'mattersyn-si-numerical-chunk-freeze/1','source_id':'heo2003','author':'/root/peng1998_reader_assets','created_at':now,'pages':[9,10],'counts':{'rows':180,'numeric_cells':1080,'markers':180,'negative_Fobs2':25,'zero_Fobs2':1,'checks':len(checks)},'source_sha256':source['sha256'],'files':{str(p):sha(p) for p in bound_files+[outputs[2]]},'original_evidence':{x['path']:x['sha256'] for x in assets['assets']},'independent_audit':'pending','published':False,'training_eligible':False})
print(json.dumps({'pages':[9,10],'rows':180,'numeric_cells':1080,'markers':180,'negative_values':len(negative),'checks':len(checks),'manifest_sha256':sha(B/(stem+'-manifest.json')),'checkpoint_sha256':sha(outputs[2]),'transcription_sha256':sha(outputs[1]),'tsv_sha256':sha(outputs[0])},indent=2))
