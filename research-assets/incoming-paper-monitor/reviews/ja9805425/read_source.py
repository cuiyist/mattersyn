from pathlib import Path
import pypdfium2 as pdfium
import json, hashlib
B=Path(__file__).resolve().parent
source=Path('[local path redacted]')
manifest={'documents':[]}
for role,name in [('main','10.1021_ja9805425.pdf'),('si','10.1021_ja9805425_si_1.pdf')]:
    path=source/name
    doc=pdfium.PdfDocument(path)
    item={'role':role,'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'page_count':len(doc),'pages':[]}
    for i,page in enumerate(doc):
        text=page.get_textpage().get_text_range()
        (B/f'{role}-{i+1:02}.txt').write_text(text,encoding='utf-8')
        page.render(scale=150/72).to_pil().save(B/f'{role}-{i+1:02}.png')
        item['pages'].append({'page':i+1,'text_file':f'{role}-{i+1:02}.txt','render_file':f'{role}-{i+1:02}.png','text_read':False,'visually_reviewed':False})
    manifest['documents'].append(item)
    print(json.dumps({'role':role,'pages':len(doc),'sha256':item['sha256']}))
(B/'source-render-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
