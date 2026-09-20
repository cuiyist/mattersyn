from pathlib import Path
from pypdf import PdfReader
import hashlib,json,subprocess,sys
sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent
src=Path('[local path redacted]')
r=PdfReader(src);pages=[]
for n,p in enumerate(r.pages,1):
    text=p.extract_text()
    (B/f'plain-page-{n}.txt').write_text(text,encoding='utf-8')
    pages.append({'pdf_page':n,'text_file':f'plain-page-{n}.txt','characters':len(text),'text_reviewed':False,'visual_reviewed':False})
manifest={'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'page_count':len(pages),'pages':pages,'metadata':dict(r.metadata or {})}
(B/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'pages':len(pages),'sha256':manifest['sha256'],'first_page':(B/'plain-page-1.txt').read_text(encoding='utf-8')[:4500]},ensure_ascii=False))
subprocess.run(['[local path redacted]','-png','-r','140',str(src),str(B/'main')],check=True,capture_output=True)
