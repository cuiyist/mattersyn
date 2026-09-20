"""Package the root's manually read SI pages7–8; independent audit is separate."""
from pathlib import Path
from decimal import Decimal
from datetime import datetime,timezone
import csv,hashlib,json
B=Path(__file__).resolve().parent
stem='si-pages07-08'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
out=[B/(stem+s) for s in ['-reflections.tsv','-transcription.json','-author-checkpoint.json']]
assert not any(p.exists() for p in out),'Freeze already exists; use bounded correction history.'
names=['source-inventory.json','source-facts.json','page-coverage.json','source-scientific-audit.json','main-tables.json','main-table-assets.json','source-review-checkpoint.json','si-reflections-pages01-02.tsv','si-reflections-transcription.json','si-numerical-verification-checkpoint.json','si-pages-1-2-independent-audit.json','si-pages-1-2-independent-audit.md','si-numerical-correction-history.json','si-pages03-04-author-blocks.json','si-pages03-04-assets.json','si-pages03-04-reflections.tsv','si-pages03-04-transcription.json','si-pages03-04-author-checkpoint.json','si-pages03-04-correction-history.json','si-pages-3-4-independent-audit.json','si-pages-3-4-independent-audit.md']
names += ['si-pages05-06-author-blocks.json','si-pages05-06-assets.json','si-pages05-06-reflections.tsv','si-pages05-06-transcription.json','si-pages05-06-author-checkpoint.json']
preserved={str(B/n):sha(B/n) for n in names}
source=read(B/'source-inventory.json')['source_documents']['si']
assets=read(B/(stem+'-assets.json')); amap={a['id']:a for a in assets['assets']}
blocks=read(B/(stem+'-author-blocks.json'))
assert sha(source['path'])==source['sha256']==assets['source_sha256']
assert all(sha(a['path'])==a['sha256'] for a in assets['assets'])
columns=['h','k','l','Fcal2','Fobs2','sigma_Fobs2','marker']
labels={'h':'h','k':'k','l':'l','Fcal2':'Fcal^2','Fobs2':'Fobs^2','sigma_Fobs2':'σ(Fobs^2)','marker':'unheaded trailing open-circle/o-like marker'}
checks=[]
def check(label,ok):
    checks.append({'check':label,'passed':bool(ok)})
    assert ok,label
check('Exact page/block scope',list(blocks)==['7L','7R','8L','8R'])
rows=[];tsv=[];neg=[];ids=[]
for key,lines in blocks.items():
    page=int(key[:-1]);block=key[-1]
    check(key+' has45visuallycounted rows',len(lines)==45)
    for rn,line in enumerate(lines,1):
        tokens=line.split();check(f'{key}/{rn} seven printed tokens',len(tokens)==7)
        raw=dict(zip(columns,tokens));rid=f'si-p{page:02d}-{block}-r{rn:03d}'
        cidbase=f'si-{page:02d}-'+('left' if block=='L' else 'right')+('-top' if rn<=23 else '-bottom')
        a=amap[cidbase];cells=[]
        hkl=[int(raw[c]) for c in columns[:3]]
        for c in columns:
            cid=rid+'-'+c;ids.append(cid);n=None
            if c!='marker':
                dec=Decimal(raw[c]);check(cid+' finite',dec.is_finite())
                n=int(raw[c]) if c in columns[:3] else float(dec)
                check(cid+' exact decimal roundtrip',Decimal(str(n))==dec)
            else:check(cid+' glyph retained uninterpreted',raw[c]=='o')
            ev={'source_id':'heo2003-si','source_path':source['path'],'source_sha256':source['sha256'],'supporting_table':1,'pdf_page':page,'printed_page':40+page,'column_block':block,'row_in_block':rn,'column_key':c,'printed_column_label':labels[c],
                'locator':f'SI PDF p.{page} (printed p.{40+page}), Supporting Table1, '+('left' if block=='L' else 'right')+f' block, body row{rn}, {labels[c]}',
                'original_crop_id':cidbase,'original_crop_path':a['path'],'original_crop_sha256':a['sha256']}
            cells.append({'cell_id':cid,'raw_text':raw[c],'numeric_value':n,'unit':None,'unit_status':'not_applicable_index' if c in columns[:3] else 'not_applicable_marker' if c=='marker' else 'unreported',
                'transcription_status':'manually_transcribed_from_original_scan','source_comparison_status':'visually_compared_by_transcription_author','independent_numerical_audit':'pending','evidence':ev})
            if c=='Fobs2' and n<0:neg.append({'cell_id':cid,'raw_text':raw[c],'numeric_value':n})
        rows.append({'row_id':rid,'source_sample_label':'In66-X, as Supporting Table1 title','hkl':hkl,'raw_cells':raw,'cells':cells})
        tsv.append({'page':page,'block':block,'row':rn,**raw})
expected_negative={'7L':{4:'-3376.68',10:'-1513.71',14:'-402.11',18:'-6421',21:'-1237.99',44:'-3012.84'},'7R':{9:'-3525.26',20:'-5571.09',24:'-9055.25'},'8L':{13:'-2669.78',18:'-3160.58',27:'-7783.89',31:'-3825.71',42:'-4171.98',43:'-6588.8'},'8R':{6:'-6416.11',8:'-5941.85',14:'-9989.62',16:'-4540.39',33:'-6744.26',42:'-6997.27'}}
expected=[(f'si-p{int(k[:-1]):02d}-{k[-1]}-r{rn:03d}-Fobs2',s) for k,d in expected_negative.items() for rn,s in d.items()]
check('All21negative observations retained',[(n['cell_id'],n['raw_text']) for n in neg]==expected)
check('180rows/1260distinct cells',len(rows)==180 and len(set(ids))==1260)
previous=read(B/'si-reflections-transcription.json')['rows']+read(B/'si-pages03-04-transcription.json')['rows']+read(B/'si-pages05-06-transcription.json')['rows']
prior_hkl={tuple(r['hkl']) for r in previous};new_hkl={tuple(r['hkl']) for r in rows}
check('180distinct new hkl; no prior530overlap or merging',len(new_hkl)==180 and not new_hkl.intersection(prior_hkl))
check('All previous source/audit/numeric chunks unchanged',all(sha(p)==h for p,h in preserved.items()))
with out[0].open('w',encoding='utf8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['page','block','row']+columns,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(tsv)
now=datetime.now(timezone.utc).isoformat()
policy={'numeric_precision':'Raw decimal strings authoritative. No rescaling, unit inference, truncation, symmetry expansion or merging.',
    'marker':'ASCII o represents scanned open-circle/lowercase-o-like glyph. Meaning and exact Unicode identity unverified; not numeric zero or acceptance status.',
    'scientific_scope':'Reflection indices and squared structure factors with esds, not atomic coordinates, CIF or a DFT-ready ordered crystal.',
    'source_identity_caveat':'SI prints ©2002 ACS, J. Phys. Chem. A, Heo jp0219348; audited content/DOI pairing and header discrepancy retained.'}
write(out[1],{'schema':'mattersyn-si-reflection-transcription-chunk/1','source_id':'heo2003','title_as_printed':'Observed and Calculated Structure Factors Squared with Esds for In66-X','author':'/root','created_at':now,'pages':[7,8],
    'source_path':source['path'],'source_sha256':source['sha256'],'status':'author_transcribed_source_compared_independent_numerical_audit_pending','field_order':columns,'original_header_labels':labels,'rows':rows,'negative_observations':neg,'policies':policy,
    'unresolved_numeric_tokens_in_chunk':[],'complete_document_transcription':False,'independent_audit_passed':False,'training_eligible':False,'published':False})
files=[B/(stem+'-author-blocks.json'),B/(stem+'-assets.json'),B/'prepare_si_pages07_08.py',Path(__file__),out[0],out[1]]
write(out[2],{'schema':'mattersyn-si-numerical-chunk-author-checkpoint/1','source_id':'heo2003','author':'/root','created_at':now,'status':'author_source_comparison_complete_independent_numerical_audit_pending',
    'actual_scope':{'pages_transcribed':[7,8],'native_crop_pages_visually_read':[7,8],'rows':180,'numeric_cells':1080,'marker_cells':180,'total_cells':1260,'negative_Fobs2':21,'rows_per_page_block':{k:len(v) for k,v in blocks.items()}},
    'manual_source_comparison':'Root actually read all180rows/seven fields from eight native scan column crops and both headers. Overlap row23 was counted once per block. Independent numerical audit remains pending.',
    'complete_document_transcription':False,'remaining_untranscribed_pages':list(range(9,15)),'remaining_unaudited_pages':list(range(5,15)),'remaining_row_count':None,
    'policies':policy,'programmatic_check_count':len(checks),'programmatic_checks':checks,'preserved_prior_files':preserved,
    'source_pdf_sha256':source['sha256'],'bound_files':{str(p):sha(p) for p in files},'bound_original_evidence':{a['path']:a['sha256'] for a in assets['assets']},
    'independent_audit_passed':False,'training_eligible':False,'published':False})
print(json.dumps({'chunk':'pages07-08','rows':len(rows),'numeric_cells':1080,'markers':180,'negative_values':len(neg),'checks':len(checks),'checkpoint_sha256':sha(out[2]),'independent_audit':'pending'}))
