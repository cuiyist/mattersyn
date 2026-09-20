"""Independently compare scan readings with the frozen Heo SI 3–4 package."""
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone
import csv, hashlib, io, json, sys
sys.dont_write_bytecode=True
sys.path.insert(0,r'[local path redacted]')
sys.path.insert(0,r'[local path redacted]')
import pymupdf
from PIL import Image
B=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(n,x):(B/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
checks=[]
def check(n,v):
    checks.append({'check':n,'passed':bool(v)})
    if not v:raise AssertionError(n)

checkpoint_path=B/'si-pages03-04-author-checkpoint.json';checkpoint=read(checkpoint_path)
check('expected corrected checkpoint',sha(checkpoint_path)=='44fc9ec04bcf7bf90e3cb3bce96567daf682e86aa5fcd8d7a047bb8d947b74b5')
trans=read(B/'si-pages03-04-transcription.json');assets=read(B/'si-pages03-04-assets.json');asset_by={a['id']:a for a in assets['assets']}
author=read(B/'si-pages03-04-author-blocks.json');visual=read(B/'si-pages03-04-auditor-visual-reading.json')['blocks'];finding=read(B/'si-pages03-04-independent-findings-initial.json')
columns=['h','k','l','Fcal2','Fobs2','sigma_Fobs2','marker']
check('independent author identity',checkpoint['author']=='/root' and trans['author']=='/root')
check('scope exactly pages 3 and 4',trans['pages']==[3,4] and checkpoint['actual_scope']['pages_transcribed']==[3,4])
check('correct reflection field order',trans['field_order']==columns)
check('unknown units and marker policy preserved','Meaning and exact Unicode identity unverified' in trans['policies']['marker'])
check('not full SI transcription',trans['complete_document_transcription'] is False and checkpoint['complete_document_transcription'] is False)
check('pages 5 through 14 still pending',checkpoint['remaining_untranscribed_pages']==list(range(5,15)) and checkpoint['remaining_row_count'] is None)
check('no training or publication admission',trans['training_eligible'] is False and trans['published'] is False)
check('source PDF hash unchanged',sha(trans['source_path'])==trans['source_sha256']==assets['source_sha256']==checkpoint['source_pdf_sha256'])
bound={str(checkpoint_path):sha(checkpoint_path)}
for category in ['bound_files','bound_original_evidence','preserved_prior_files']:
    for p,h in checkpoint[category].items():check('bound exact '+Path(p).name,sha(p)==h);bound[p]=h
bound[trans['source_path']]=sha(trans['source_path'])
for n in ['si-pages03-04-auditor-reading.py','si-pages03-04-auditor-visual-reading.json','si-pages03-04-independent-findings-initial.json','si-pages03-04-correction-history.json']:
    bound[str(B/n)]=sha(B/n)
check('expected correction history',sha(B/'si-pages03-04-correction-history.json')=='b28805862387b7ac4dd8d0ec826105c9ce945a505fe5f705b621b170a50eb5a6')
old=read(B/'si-pages03-04-author-revision-1/si-pages03-04-author-blocks.json')
changes=[]
for key in author:
    for n,(before,after) in enumerate(zip(old[key],author[key]),1):
        for c,(a,b) in enumerate(zip(before.split(),after.split())):
            if a!=b:changes.append((key,n,columns[c],a,b))
check('exactly one source-supported token correction',changes==[('4L',33,'Fobs2','255019.38','255019.39')])
for old_file in (B/'si-pages03-04-author-revision-1').iterdir():
    if old_file.is_file():bound[str(old_file)]=sha(old_file)
check('all 12 evidence assets retained',len(assets['assets'])==12)

# Independently establish that every native page and crop is the unmodified
# original embedded PDF bitmap, rather than accepting the supplied PNG hash alone.
pdf=pymupdf.open(trans['source_path']);native={}
for page in [3,4]:
    objects=pdf[page-1].get_images(full=True);check('one native scan page '+str(page),len(objects)==1)
    native[page]=Image.open(io.BytesIO(pdf.extract_image(objects[0][0])['image'])).convert('L')
for a in assets['assets']:
    expected=native[a['source_pdf_page']];box=a['original_image_box']
    if box is not None:expected=expected.crop(box)
    actual=Image.open(a['path']).convert('L')
    check('original pixel identity '+a['id'],expected.size==actual.size and expected.tobytes()==actual.tobytes())
    check('declared dimensions '+a['id'],list(actual.size)==a['pixels'])
pdf.close()

tsv=list(csv.DictReader((B/'si-pages03-04-reflections.tsv').open(encoding='utf8',newline=''),delimiter='\t'))
check('180 rows in three independently compared forms',len(tsv)==len(trans['rows'])==sum(len(x) for x in visual.values())==180)
check('four complete blocks',list(visual)==list(author)==['3L','3R','4L','4R'] and all(len(x)==45 for x in visual.values()))
check('unique row and cell IDs',len({r['row_id'] for r in trans['rows']})==180 and len({c['cell_id'] for r in trans['rows'] for c in r['cells']})==1260)
rows={r['row_id']:r for r in trans['rows']};tsv_by={(int(r['page']),r['block'],int(r['row'])):r for r in tsv}
manual_rows=[];negatives=[]
for block,lines in visual.items():
    page=int(block[0]);side=block[1]
    for number,line in enumerate(lines,1):
        tokens=line.split();rid=f'si-p{page:02d}-{side}-r{number:03d}';row=rows[rid];t=tsv_by[(page,side,number)]
        check('visual reading seven cells '+rid,len(tokens)==7)
        check('author source matches independent scan reading '+rid,tokens==author[block][number-1].split())
        check('hkl exact '+rid,row['hkl']==[int(x) for x in tokens[:3]])
        crop=f'si-{page:02d}-'+('left' if side=='L' else 'right')+('-top' if number<=23 else '-bottom')
        manual_rows.append({'row_id':rid,'source_pdf_page':page,'printed_page':40+page,'column_block':side,'body_row':number,'original_crop_id':crop,'raw_tokens':tokens,'numeric_cells_compared':6,'marker_cells_compared':1,'status':'all_tokens_compared_to_original_scan'})
        check('seven typed cells '+rid,len(row['cells'])==7)
        for field,token,cell in zip(columns,tokens,row['cells']):
            cid=rid+'-'+field;e=cell['evidence']
            check('raw text exact across scan TSV JSON '+cid,token==t[field]==row['raw_cells'][field]==cell['raw_text'])
            check('cell ID order '+cid,cell['cell_id']==cid)
            check('cell numeric precision '+cid,cell['numeric_value'] is None if field=='marker' else Decimal(str(cell['numeric_value']))==Decimal(token))
            check('cell locator exact '+cid,e['pdf_page']==page and e['printed_page']==40+page and e['column_block']==side and e['row_in_block']==number and e['column_key']==field and e['supporting_table']==1)
            check('cell crop binding '+cid,e['original_crop_id']==crop and e['original_crop_sha256']==asset_by[crop]['sha256'] and e['original_crop_path']==asset_by[crop]['path'] and e['source_sha256']==trans['source_sha256'])
            expected_status='not_applicable_index' if field in ['h','k','l'] else 'not_applicable_marker' if field=='marker' else 'unreported'
            check('no invented units '+cid,cell['unit'] is None and cell['unit_status']==expected_status)
            if field=='Fobs2' and Decimal(token)<0:negatives.append({'cell_id':cid,'raw_text':token,'numeric_value':cell['numeric_value']})
        check('uninterpreted marker '+rid,tokens[-1]=='o' and row['cells'][-1]['numeric_value'] is None)
check('all eight signed negative observations retained',negatives==trans['negative_observations'] and len(negatives)==8)
check('single reported correction resolved',rows['si-p04-L-r033']['raw_cells']['Fobs2']=='255019.39')
prior=read(B/'si-reflections-transcription.json')
check('prior pages 1–2 remain separate and no duplicate hkl',len(prior['rows'])==170 and not {tuple(r['hkl']) for r in prior['rows']} & {tuple(r['hkl']) for r in trans['rows']})
for p,h in bound.items():check('post-audit frozen '+Path(p).name,sha(p)==h)

resolution={'finding_id':'si-p04-L-r033-Fobs2-last-digit','original_value':'255019.38','source_value':'255019.39','status':'resolved_by_author_and_rechecked','initial_checkpoint_sha256':finding['author_checkpoint_sha256_at_review'],'corrected_checkpoint_sha256':sha(checkpoint_path),'source_asset_sha256':asset_by['si-04-left-bottom']['sha256'],'scope':'The complete independent row reading matches the corrected author blocks, TSV and typed JSON. Source image bytes did not change.'}
out={'schema':'mattersyn-independent-si-numerical-audit/1','source_id':'heo2003','auditor':'/root/backlog_eta','transcription_author':'/root','audited_at':datetime.now(timezone.utc).isoformat(),'status':'passed_for_si_pages_3_4_only_after_author_correction','scope':'Every printed row and seven fields on SI pages 3 and 4, two 45-row blocks per page. Independent manual reading of native original crops, followed by mechanical verification of author raw blocks, TSV, typed cells, locators, source bytes and unmodified pixel provenance. This is not a complete SI audit.','actual_manual_scope':{'pdf_pages':[3,4],'printed_pages':[43,44],'body_rows':180,'numeric_cells':1080,'uninterpreted_marker_cells':180,'all_original_assets_viewed':12,'method':'Headers and full native pages inspected; every body token independently entered from eight original block crops. Top crop rows 1–23 and bottom crop rows 24–45; overlap row 23 checked and counted once.','row_checks':manual_rows},'mechanical_scope':{'check_count':len(checks),'checks':checks,'source_pixel_identity':'Both native PNGs and all ten crops match the original PDF embedded image pixels exactly.','precision':'Authoritative decimal strings compared without rescaling, rounding or truncation; negative Fobs² values retained.','not_manual_check_count':True},'negative_observations':negatives,'correction_resolution':[resolution],'open_findings':[],'bound_files':bound,'auditor_script_sha256':sha(__file__),'prior_chunk':{'pages':[1,2],'audit_sha256':sha(B/'si-pages-1-2-independent-audit.json'),'repeated_manual_audit':False},'full_si_numerical_audit':False,'remaining_untranscribed_and_unaudited_pages':list(range(5,15)),'remaining_cell_count':None,'limits':['Units or scale of Fcal², Fobs² and sigma are unreported; no scale inferred.','The trailing o-like glyph is preserved without assigning its meaning, exact Unicode identity, a numeric zero or acceptance status.','The source header prints ©2002 ACS and J. Phys. Chem. A; audited DOI/content pairing remains separate from this discrepancy.','Reflection indices and squared structure factors are not atom coordinates, an ordered crystal model or a DFT-ready structure.','No source/main/canonical/Site/ledger file was changed by the auditor.'],'training_eligible':False,'published':False}
write('si-pages-3-4-independent-audit.json',out)
md=f'''# Heo SI pages 3–4: independent numerical audit

Passed for this two-page chunk after one author correction. All 180 rows, 1,080 numeric cells and 180 unheaded o-like markers were independently read from the original scan crops. Twelve assets were inspected: two complete native pages, two headers and eight block crops. The repeated overlap row 23 was checked but counted once.

The single correction is SI page 4, printed page 44, left block row 33, hkl (1, 15, 17): Fobs² is **255019.39**, rather than the original author transcription 255019.38. The author corrected the raw block and generated forms; the entire independent reading now matches.

All eight negative Fobs² values remain signed. Decimal strings, seven-field order, row/block/page locators and source hashes agree across the independent reading, author raw blocks, TSV and typed JSON. {len(checks):,} mechanical checks supplement the manual reading; they are not additional manual comparisons. Each retained PNG was also checked pixel-for-pixel against the native embedded source scan or its declared rectangle.

Final author checkpoint SHA256: {sha(checkpoint_path)}.

Units and the o-like marker meaning remain unverified. The SI header's ©2002 / J. Phys. Chem. A discrepancy is preserved. Reflection hkl and squared structure factors are not atomic coordinates or a structure-model approval.

The independently audited pages 1–2 remain unchanged and were not manually re-audited here. **Pages 5–14 remain untranscribed and numerically unaudited.** This result does not grant complete SI, canonical, visualization, training or publication approval.
'''
(B/'si-pages-3-4-independent-audit.md').write_text(md,encoding='utf8')
print(json.dumps({'status':out['status'],'manual_rows':180,'numeric_cells':1080,'markers':180,'mechanical_checks':len(checks),'audit_sha256':sha(B/'si-pages-3-4-independent-audit.json'),'checkpoint_sha256':sha(checkpoint_path)}))
