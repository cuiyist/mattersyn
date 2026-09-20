"""Local source preparation only; no scientific review state is inferred."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
import pypdf,pypdfium2

P=Path(__file__).resolve().parent
I=P.parent/'intake-20260920T071632Z/intake-manifest.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
intake=json.loads(I.read_bytes())
paper=next(p for p in intake['papers'] if p['paper_id']=='legacy::10.1021_acsami.1c18038')
files=[]
for f in paper['file_copies']:
    src=Path(f['source_path']);before=src.stat();digest=sha(src);after=src.stat()
    assert digest==f['sha256'] and before.st_size==after.st_size and before.st_mtime_ns==after.st_mtime_ns
    files.append({**f,'verified_actual_sha256':digest,'verified_bytes':after.st_size})
docs=[]
for role in ['main','si']:
    f=next(f for f in files if f['role_candidate']==role)
    src=Path(f['source_path']);reader=pypdf.PdfReader(src);pdf=pypdfium2.PdfDocument(str(src));pages=[]
    for n,page in enumerate(reader.pages,1):
        text=page.extract_text();tp=P/'private/text'/f'{role}-{n:02}.txt';tp.parent.mkdir(parents=True,exist_ok=True);tp.write_text(text,encoding='utf-8')
        out=P/'source-render'/f'{role}-{n:02}.png';out.parent.mkdir(exist_ok=True)
        native=pdf[n-1];bitmap=native.render(scale=2);image=bitmap.to_pil();image.save(out);dims=image.size;image.close();bitmap.close();native.close()
        pages.append({'pdf_page':n,'printed_page':58907+n if role=='main' else 'S-'+str(n),'text':text,'text_path':str(tp),'text_sha256':sha(tp),'render_path':str(out),'render_sha256':sha(out),'render_pixels':dims,'text_read':False,'visually_inspected':False})
    pdf.close()
    docs.append({'document_id':role,'source_path':str(src),'source_sha256':f['sha256'],'page_count':len(pages),'pages':pages})
report={'schema':'mattersyn.private-complete-source-payloads/1','prepared_at':datetime.now(timezone.utc).isoformat(),'author':'/root/backlog_eta','source_generation':paper['source_generation'],'bundle_sha256':paper['bundle_sha256'],'source_copies':files,'documents':docs,'status':'prepared_not_fully_read','scope':'Complete source text and page images are local-only. Preparation does not establish scientific reading, pairing or independent audit.','intake_manifest_sha256':sha(I),'extractor':'pypdf '+pypdf.__version__,'renderer':'pypdfium2; scale 2 pixels per PDF point; sequential native calls'}
(P/'complete-source-payloads.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'page_counts':{d['document_id']:d['page_count']for d in docs},'verified_copies':len(files),'source_generation':paper['source_generation'],'payload_sha256':sha(P/'complete-source-payloads.json')}))
