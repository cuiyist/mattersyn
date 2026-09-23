from pathlib import Path
import json,hashlib,zipfile
from xml.etree import ElementTree as ET
import pypdfium2 as pdfium
HERE=Path(__file__).resolve().parent; PRIVATE=HERE/'private'; PRIVATE.mkdir(exist_ok=True)
AUTHOR=HERE.parent/'mixed-batch-01'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
freeze=read(AUTHOR/'author-freeze.json'); summary=read(AUTHOR/'batch-summary.json'); checks=[]
for b in freeze['bound_files']:
 p=AUTHOR/b['path'];h=b['sha256']
 assert sha(p)==h,p;checks.append({'path':str(p),'sha256':h,'kind':'author_binding'})
copies=[f for r in summary['receipts'] for f in r['files']]
for f in copies:
 assert sha(f['path'])==f['sha256'];checks.append({'path':f['path'],'sha256':f['sha256'],'kind':'current_source'})
sources=read(AUTHOR/'private'/'sources.json')['files']; fresh=[]
for h,f in sources.items():
 pages={1}
 for r in summary['receipts']:
  for item in r.get('full_pdf_text_pages_read',[]):
   if item['source_sha256']==h:pages.add(item['pdf_page'])
  for item in r.get('original_pdf_pages_visually_inspected',[]):
   if item['source_sha256']==h:pages.add(item['pdf_page'])
 if f['format']=='pdf':
  pdf=pdfium.PdfDocument(f['path'])
  for n in sorted(pages):
   pg=pdf[n-1];t=pg.get_textpage();text=t.get_text_range();t.close();pg.close()
   dest=PRIVATE/f'{h[:12]}-p{n:03}.txt';dest.write_text(text,encoding='utf8')
   cached=AUTHOR/'private'/dest.name
   assert sha(dest)==sha(cached),(h,n)
   fresh.append({'source_sha256':h,'pdf_page':n,'fresh_text_path':str(dest),'text_sha256':sha(dest),'replayed_from_original':True})
  pdf.close()
 elif f['format']=='docx':
  with zipfile.ZipFile(f['path']) as z:
   assert z.getinfo('word/document.xml').file_size<10_000_000
   tree=ET.fromstring(z.read('word/document.xml'))
   text='\n'.join(''.join(t.itertext()) for t in tree.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
  dest=PRIVATE/f'{h[:12]}-document.txt';dest.write_text(text,encoding='utf8')
  assert sha(dest)==sha(AUTHOR/'private'/dest.name)
  fresh.append({'source_sha256':h,'ooxml_part':'word/document.xml','fresh_text_path':str(dest),'text_sha256':sha(dest),'replayed_from_original':True})
report={'started_at':'2026-09-23T13:16:18+00:00','author_freeze_sha256':sha(AUTHOR/'author-freeze.json'),'summary_sha256':sha(AUTHOR/'batch-summary.json'),'bindings':checks,'fresh_original_text_replays':fresh,'raw_text_private':True,'replay_is_not_reading_claim':True,'failures':[]}
(HERE/'binding-check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps({'author_freeze_sha256':report['author_freeze_sha256'],'summary_sha256':report['summary_sha256'],'binding_checks':len(checks),'original_text_replays':len(fresh),'headers':[{ 'sha':h[:12],'format':f['format'],'header':(PRIVATE/f'{h[:12]}-p001.txt').read_text(encoding='utf8')[:1300] if f['format']=='pdf' else (PRIVATE/f'{h[:12]}-document.txt').read_text(encoding='utf8')[:1400]} for h,f in sources.items()]},ensure_ascii=False))
