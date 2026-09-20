"""Read-only source intake. Writes derived scratch assets inside this batch only."""
from pathlib import Path
import hashlib,json
import pypdfium2 as pdfium
from pypdf import PdfReader
B=Path(__file__).resolve().parent
SRC=Path('[local path redacted]')
for suffix in ['jp0219348','ja0496423','la036034c']:
 out=B/suffix;out.mkdir(exist_ok=True);docs=[]
 for role,ending in [('main',''),('si','_si_1')]:
  src=SRC/f'10.1021_{suffix}{ending}.pdf';raw=src.read_bytes();sig=raw[:16];entry={'role_candidate':role,'path':str(src),'filename':src.name,'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'signature_hex':sig.hex(),'detected_format':'pdf' if raw[:1024].find(b'%PDF-')>=0 else 'not_pdf','rendered_pages':[]}
  if entry['detected_format']=='pdf':
   r=PdfReader(src);d=pdfium.PdfDocument(src);entry.update(page_count=len(d),metadata={str(k):str(v) for k,v in (r.metadata or {}).items()})
   for n,page in enumerate(d,1):
    tp=page.get_textpage();txt=tp.get_text_range().replace('\r\n','\n').replace('\r','\n');(out/f'{role}-{n:02}.txt').write_text(txt,encoding='utf8');page.render(scale=125/72).to_pil().save(out/f'{role}-{n:02}.png');entry['rendered_pages'].append(n)
  else:entry['header_text']=raw[:600].decode('utf8','replace')
  docs.append(entry)
 (out/'intake-manifest.json').write_text(json.dumps({'doi':'10.1021/'+suffix,'documents':docs},indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 print(suffix,[(x['role_candidate'],x['detected_format'],x.get('page_count'),x['sha256']) for x in docs])
