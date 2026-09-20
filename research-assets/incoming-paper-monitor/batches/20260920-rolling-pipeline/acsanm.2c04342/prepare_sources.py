"""Local-only original hash verification and private PDF reading aids."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
from pypdf import PdfReader
import pypdfium2 as pdfium
P=Path(__file__).resolve().parent
I=P.parent/'intake-20260920T111852Z/intake-manifest.json'
entry=next(p for p in json.loads(I.read_bytes())['papers']if p['paper_id']=='10.1021_acsanm.2c04342')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,d):(P/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert not(P/'package-freeze.json').exists()
(P/'source-render/text').mkdir(parents=True,exist_ok=True)
docs=[];seen=set()
for f in entry['file_copies']:
 q=Path(f['source_path']);assert sha(q)==f['sha256'];assert q.stat().st_size==f['bytes']
 if f['sha256']in seen:continue
 seen.add(f['sha256']);role=f['role_candidate'];reader=PdfReader(q);pdf=pdfium.PdfDocument(q);pages=[]
 for i,page in enumerate(reader.pages):
  text=P/'source-render/text'/f'{role}-{i+1:02}.txt';text.write_text(page.extract_text()or'',encoding='utf8')
  layout=P/'source-render/text'/f'{role}-{i+1:02}-layout.txt';layout.write_text(page.extract_text(extraction_mode='layout')or'',encoding='utf8')
  png=P/'source-render'/f'{role}-{i+1:02}.png';p=pdf[i];bitmap=p.render(scale=2);bitmap.to_pil().save(png);bitmap.close();p.close()
  pages.append({'pdf_page':i+1,'text_path':str(text),'text_sha256':sha(text),'layout_text_path':str(layout),'layout_text_sha256':sha(layout),'image_path':str(png),'image_sha256':sha(png),'text_read':False,'visually_inspected':False})
 docs.append({'role':role,'source_path':str(q),'sha256':f['sha256'],'bytes':f['bytes'],'page_count':len(pages),'pages':pages})
 pdf.close()
save('intake-identity.json',entry)
save('source-preparation.json',{'created_at':datetime.now(timezone.utc).isoformat(),'author':'/root/backlog_eta','intake_path':str(I),'intake_sha256':sha(I),'source_generation':entry['source_generation'],'bundle_sha256':entry['bundle_sha256'],'verified_copy_count':len(entry['file_copies']),'unique_document_count':len(docs),'documents':docs,'render_engine':'PDFium; scale2','scope':'Preparation only; full reading and visual coverage remain pending. Complete text and full-page images remain within source-render.'})
print(json.dumps([{'role':d['role'],'pages':d['page_count'],'sha256':d['sha256']}for d in docs]))
for d in docs:print(d['role'],Path(d['pages'][0]['text_path']).read_text(encoding='utf8')[:4000])
