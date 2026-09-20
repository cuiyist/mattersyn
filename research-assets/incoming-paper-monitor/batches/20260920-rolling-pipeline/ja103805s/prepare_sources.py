from pathlib import Path
import sys,json,hashlib,subprocess,datetime
sys.path.insert(0,r'[local path redacted]')
import fitz
P=Path(__file__).resolve().parent;R=P/'reader-assets';R.mkdir(exist_ok=True)
manifest=P.parent/'intake-manifest.json'
entry=next(x for x in json.loads(manifest.read_text('utf-8-sig'))['papers'] if x['paper_id']=='10.1021_ja103805s')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
poppler=Path(r'[local path redacted]')
rows=[]
for item in entry['file_copies']:
    src=Path(item['source_path']);actual=sha(src)
    assert actual==item['sha256'],(src,'source changed')
    row=dict(item,observed_sha256=actual,unchanged=True)
    if src.suffix=='.pdf':
        role='main' if item['role_candidate']=='main' else 'si'
        doc=fitz.open(src);row['pdf_page_count']=len(doc);row['text_pages']=[]
        for i,page in enumerate(doc):
            dest=R/f'{role}-{i+1:02}.txt';dest.write_text(page.get_text(),'utf-8')
            row['text_pages'].append({'pdf_page':i+1,'path':str(dest),'sha256':sha(dest),'page_width_pt':page.rect.width,'page_height_pt':page.rect.height})
        subprocess.run([str(poppler),'-r','150','-png',str(src),str(R/role)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        images=sorted(R.glob(role+'-*.png'));assert len(images)==len(doc)
        row['rendered_pages']=[{'path':str(x),'sha256':sha(x),'renderer':'Poppler pdftoppm','dpi':150} for x in images]
    else:
        row['file_format']='CIF';row['read_scope']='awaiting content pairing and complete semantic inventory'
    assert sha(src)==actual
    rows.append(row)
out={'schema':'mattersyn-private-source-preparation/1','source_id':'evans2010','doi':'10.1021/ja103805s','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'author':'/root/norberg2004_extract','source_intake_manifest':{'path':str(manifest),'sha256':sha(manifest)},'documents':rows,'text_extractor':'PyMuPDF '+str(fitz.version),'rendering':'Poppler pdftoppm at150dpi','scientific_scope':'Hash verification and derived text/render preparation only; no reading, pairing or extraction completion asserted.'}
(P/'source-preparation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'documents':[(x['original_filename'],x.get('pdf_page_count'),x['observed_sha256']) for x in rows],'source_preparation_sha256':sha(P/'source-preparation.json')},indent=2))
