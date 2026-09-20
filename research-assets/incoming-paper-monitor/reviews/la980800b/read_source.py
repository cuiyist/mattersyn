from pathlib import Path
import pypdfium2 as pdfium
import json,hashlib
B=Path(__file__).resolve().parent
source=Path('[local path redacted]')
doc=pdfium.PdfDocument(source)
manifest={'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'page_count':len(doc),'pages':[]}
for i,page in enumerate(doc):
    text=page.get_textpage().get_text_range()
    (B/f'page-{i+1}.txt').write_text(text,encoding='utf-8')
    page.render(scale=140/72).to_pil().save(B/f'page-{i+1}.png')
    manifest['pages'].append({'page':i+1,'text_file':f'page-{i+1}.txt','render_file':f'page-{i+1}.png','text_read':False,'visually_reviewed':False})
(B/'source-render-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'pages':len(doc),'sha256':manifest['sha256']}))

