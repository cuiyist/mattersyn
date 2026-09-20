"""Independent SI 5–8 audit against manually entered native-scan readings."""
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone
import csv, hashlib, io, json, sys
sys.dont_write_bytecode=True
sys.path[:0]=[r'[local path redacted]',r'[local path redacted]']
import pymupdf
from PIL import Image
B=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(n,x):(B/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
columns=['h','k','l','Fcal2','Fobs2','sigma_Fobs2','marker']

def audit(first,last,expected_checkpoint):
    slug=f'{first:02d}-{last:02d}';checks=[];bound={}
    def check(n,v):
        checks.append({'check':n,'passed':bool(v)})
        if not v:raise AssertionError(n)
    def bind(p,expected=None):
        p=Path(p);digest=sha(p)
        if expected:check('Exact frozen hash '+p.name,digest==expected)
        bound[str(p)]=digest
    checkpoint_path=B/f'si-pages{slug}-author-checkpoint.json';checkpoint=read(checkpoint_path)
    bind(checkpoint_path,expected_checkpoint)
    trans=read(B/f'si-pages{slug}-transcription.json');assets=read(B/f'si-pages{slug}-assets.json');asset_by={x['id']:x for x in assets['assets']};author=read(B/f'si-pages{slug}-author-blocks.json')
    allvisual=read(B/'si-pages05-08-auditor-visual-reading.json')['blocks'];keys=[f'{p}{side}' for p in range(first,last+1) for side in ['L','R']];visual={key:allvisual[key] for key in keys}
    findings=read(B/f'si-pages{slug}-independent-findings-initial.json')
    check('Independent auditor distinct from author',checkpoint['author']==trans['author']=='/root')
    check('Exact two-page scope',trans['pages']==[first,last] and checkpoint['actual_scope']['pages_transcribed']==[first,last])
    check('Exact column headings',trans['field_order']==columns)
    check('Marker meaning unverified','Meaning and exact Unicode identity unverified' in trans['policies']['marker'])
    check('No full-document or training/publishing assertion',not trans['complete_document_transcription'] and not checkpoint['complete_document_transcription'] and not trans['training_eligible'] and not trans['published'])
    check('Original SI source hash',sha(trans['source_path'])==trans['source_sha256']==assets['source_sha256']==checkpoint['source_pdf_sha256'])
    bind(trans['source_path'])
    for category in ['bound_files','bound_original_evidence','preserved_prior_files']:
        for p,d in checkpoint[category].items():bind(p,d)
    for name in ['si-pages05-08-auditor-reading.py','si-pages05-08-auditor-visual-reading.json',f'si-pages{slug}-independent-findings-initial.json']:
        bind(B/name)
    check('12 evidence assets',len(assets['assets'])==12)
    pdf=pymupdf.open(trans['source_path']);native={}
    for page in [first,last]:
        imgs=pdf[page-1].get_images(full=True);check('One original embedded scan '+str(page),len(imgs)==1)
        native[page]=Image.open(io.BytesIO(pdf.extract_image(imgs[0][0])['image'])).convert('L')
    for asset in assets['assets']:
        expected=native[asset['source_pdf_page']]
        if asset['original_image_box'] is not None:expected=expected.crop(asset['original_image_box'])
        actual=Image.open(asset['path']).convert('L')
        check('Original PDF pixel equality '+asset['id'],actual.size==expected.size and actual.tobytes()==expected.tobytes())
        check('Declared dimensions '+asset['id'],list(actual.size)==asset['pixels']);bind(asset['path'],asset['sha256'])
    pdf.close()
    tsv=list(csv.DictReader((B/f'si-pages{slug}-reflections.tsv').open(encoding='utf-8',newline=''),delimiter='\t'))
    check('180 rows in independent and author forms',sum(len(x) for x in visual.values())==len(trans['rows'])==len(tsv)==180)
    check('Four 45-row blocks',list(visual)==list(author)==keys and all(len(x)==45 for x in visual.values()))
    check('Unique row and cell IDs',len({r['row_id'] for r in trans['rows']})==180 and len({c['cell_id'] for r in trans['rows'] for c in r['cells']})==1260)
    rows={r['row_id']:r for r in trans['rows']};table={(int(r['page']),r['block'],int(r['row'])):r for r in tsv};manual=[];negatives=[]
    for block,lines in visual.items():
        page=int(block[0]);side=block[1]
        for number,line in enumerate(lines,1):
            tok=line.split();rid=f'si-p{page:02d}-{side}-r{number:03d}';row=rows[rid];tab=table[(page,side,number)]
            check('Seven source fields '+rid,len(tok)==7)
            check('Author matches independent scan reading '+rid,tok==author[block][number-1].split())
            check('Exact hkl '+rid,row['hkl']==[int(x) for x in tok[:3]])
            crop=f'si-{page:02d}-'+('left' if side=='L' else 'right')+('-top' if number<=23 else '-bottom')
            manual.append({'row_id':rid,'pdf_page':page,'printed_page':40+page,'column_block':side,'row_in_block':number,'original_crop_id':crop,'raw_tokens':tok,'status':'all seven tokens independently compared to original scan'})
            check('Seven typed cells '+rid,len(row['cells'])==7)
            for field,token,cell in zip(columns,tok,row['cells']):
                cid=rid+'-'+field;e=cell['evidence']
                check('Exact raw value scan/TSV/JSON '+cid,token==tab[field]==row['raw_cells'][field]==cell['raw_text'])
                check('Typed field identity '+cid,cell['cell_id']==cid)
                check('Exact decimal meaning '+cid,cell['numeric_value'] is None if field=='marker' else Decimal(str(cell['numeric_value']))==Decimal(token))
                check('Complete cell locator '+cid,e['pdf_page']==page and e['printed_page']==40+page and e['column_block']==side and e['row_in_block']==number and e['column_key']==field and e['supporting_table']==1)
                check('Exact cell/crop/source binding '+cid,e['original_crop_id']==crop and e['original_crop_sha256']==asset_by[crop]['sha256'] and e['original_crop_path']==asset_by[crop]['path'] and e['source_sha256']==trans['source_sha256'])
                unit_status='not_applicable_index' if field in ['h','k','l'] else 'not_applicable_marker' if field=='marker' else 'unreported'
                check('No inferred units '+cid,cell['unit'] is None and cell['unit_status']==unit_status)
                if field=='Fobs2' and Decimal(token)<0:negatives.append({'cell_id':cid,'raw_text':token,'numeric_value':cell['numeric_value']})
            check('Uninterpreted o-like marker '+rid,tok[-1]=='o' and row['cells'][-1]['numeric_value'] is None)
    check('All negative observations retained',negatives==trans['negative_observations'] and len(negatives)==(20 if first==5 else 21))
    check('Unique reflection indices within chunk',len({tuple(r['hkl']) for r in trans['rows']})==180)
    prior_names=['si-reflections-transcription.json','si-pages03-04-transcription.json']+(['si-pages05-06-transcription.json'] if first==7 else [])
    for name in prior_names:
        prior=read(B/name);bind(B/name)
        check('No reflection duplicated from prior chunk '+name,not {tuple(x['hkl']) for x in prior['rows']} & {tuple(x['hkl']) for x in trans['rows']})
    resolutions=[]
    if findings['differences']:
        history_path=B/f'si-pages{slug}-correction-history.json';check('Author correction history retained',history_path.exists());bind(history_path)
        revision=B/f'si-pages{slug}-author-revision-1';check('Original author version retained',revision.is_dir())
        before=read(revision/f'si-pages{slug}-author-blocks.json');changes=[]
        for block in keys:
            for i,(old,new) in enumerate(zip(before[block],author[block]),1):
                for j,(u,v) in enumerate(zip(old.split(),new.split())):
                    if u!=v:changes.append({'block':block,'row':i,'field':columns[j],'independent_scan_reading':v,'author':u})
        check('Only initially identified source-supported tokens changed',changes==findings['differences'])
        for p in revision.iterdir():
            if p.is_file():bind(p)
        resolutions=[{**d,'status':'resolved_by_author_and_rechecked'} for d in findings['differences']]
    for p,d in bound.items():check('Frozen at close '+Path(p).name,sha(p)==d)
    prior_audits=['si-pages-1-2-independent-audit.json','si-pages-3-4-independent-audit.json']+(['si-pages-5-6-independent-audit.json'] if first==7 else [])
    for name in prior_audits:bind(B/name)
    out={'schema':'mattersyn-independent-si-numerical-audit/1','source_id':'heo2003','auditor':'/root/backlog_eta','transcription_author':'/root','audited_at':datetime.now(timezone.utc).isoformat(),'status':f'passed_for_si_pages_{first}_{last}_only'+('_after_author_correction' if resolutions else ''),'scope':f'Complete original-scan numerical comparison for SI pages {first}–{last}, two 45-row blocks per page. No full-SI audit or atom-coordinate claim.',
     'actual_manual_scope':{'pdf_pages':[first,last],'printed_pages':[40+first,40+last],'body_rows':180,'numeric_cells':1080,'uninterpreted_marker_cells':180,'all_original_assets_viewed':12,'method':'Native full pages and headers inspected. Every token independently entered from eight original column crops before opening author blocks for comparison. Top rows 1–23, bottom rows 24–45; overlap row 23 checked and counted once.','row_checks':manual},
     'mechanical_scope':{'check_count':len(checks),'checks':checks,'not_manual_check_count':True,'source_pixel_identity':'All native PNGs and crops equal the unchanged embedded source-PDF scan pixels exactly.','precision':'Raw decimal strings authoritative; no rounding, rescaling, symmetry expansion or merging.'},'negative_observations':negatives,'correction_resolution':resolutions,'open_findings':[],'bound_files':bound,'auditor_script_sha256':sha(Path(__file__)),'prior_chunks':{'audit_hashes':{name:sha(B/name) for name in prior_audits},'repeated_manual_audit':False},'full_si_numerical_audit':False,'pages_outside_this_audit':[p for p in range(1,15) if p not in [first,last]],'full_si_remaining_cell_count':None,'limits':['Units/scales for Fcal², Fobs² and sigma remain unreported.','The trailing o-like glyph has no verified meaning or exact Unicode identity; it is not treated as numeric zero or acceptance.','Header prints ©2002 ACS, J. Phys. Chem. A, Heo jp0219348; pairing discrepancy remains explicit.','Reflection tables are not atomic coordinates, an ordered crystal, CIF or DFT-ready structure.','No original source, main, canonical, Site, ledger or author output was edited by the auditor.'],'training_eligible':False,'published':False}
    name=f'si-pages-{first}-{last}-independent-audit';write(name+'.json',out)
    (B/(name+'.md')).write_text(f'# Heo SI pages {first}–{last}: independent numerical audit\n\nPassed for this two-page chunk only. All 180 rows, 1,080 numeric cells and 180 uninterpreted trailing markers were independently read from original native crops. All {len(negatives)} negative Fobs² observations are preserved. The source headers and 12 retained assets were inspected; native/crop pixel equality to the PDF was checked separately.\n\n'+(f'{len(resolutions)} initially discrepant author tokens were corrected, preserved in author revision history and rechecked against the independent source reading.\n\n' if resolutions else 'No numerical discrepancies were found.\n\n')+f'{len(checks)} mechanical checks verify exact raw/TSV/typed values, decimal precision, cell IDs, evidence locators, crop hashes, unique reflections and protected prior chunks. This count is not a count of manual reading actions.\n\nAuthor checkpoint SHA256: `{sha(checkpoint_path)}`. Exact input hashes and per-row readings are retained in the JSON audit.\n\nPrior pages remain separate and unchanged. Other SI pages are outside this audit; this is not full SI approval. Units/scales and the o-like marker meaning remain unknown. No atomic coordinates, CIF, training admission or publication approval is asserted.\n',encoding='utf-8')
    return {'pages':[first,last],'status':out['status'],'checks':len(checks),'negative_observations':len(negatives),'corrections':len(resolutions),'audit_sha256':sha(B/(name+'.json'))}

if __name__=='__main__':
    first=int(sys.argv[1]);assert first in [5,7];print(json.dumps(audit(first,first+1,sys.argv[2]),indent=2))
