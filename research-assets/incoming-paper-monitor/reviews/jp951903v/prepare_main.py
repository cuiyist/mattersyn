from pathlib import Path
from pypdf import PdfReader
import hashlib,json,subprocess
B=Path(__file__).resolve().parent
source=Path('[local path redacted]')
reader=PdfReader(source);pages=[]
for number,page in enumerate(reader.pages,1):
    text=page.extract_text(extraction_mode='layout')
    (B/f'main-page-{number}.txt').write_text(text,encoding='utf-8')
    pages.append({'pdf_page':number,'text_file':f'main-page-{number}.txt','characters':len(text),'text_reviewed':False,'visual_reviewed':False})
(B/'main-all.txt').write_text('\n\n'.join(f'PDF PAGE {i+1}\n'+(B/f'main-page-{i+1}.txt').read_text(encoding='utf-8') for i in range(len(pages))),encoding='utf-8')
manifest={'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'page_count':len(pages),'pages':pages,'metadata':dict(reader.metadata or {})}
(B/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pages':len(pages),'sha256':manifest['sha256'],'first_page':(B/'main-page-1.txt').read_text(encoding='utf-8')[:2600]},ensure_ascii=False))
