"""Verify retained source bytes and prepare private text/page render caches."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess
import pypdfium2 as pdfium
from pypdf import PdfReader
P=Path(__file__).resolve().parent;R=P.parent
I=R/'intake-20260920T114139Z/intake-manifest.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
intake=json.loads(I.read_text(encoding='utf8'));row=next(x for x in intake['papers']if x['paper_id']=='10.1021_la8031286')
assert row['source_generation']==1 and row['bundle_sha256']=='b90762f8d91a417cdecfdd62da360d015e6dc40902529806048dfc5635a28db3'
OUT=P/'source-render';OUT.mkdir(exist_ok=True);TXT=OUT/'text';TXT.mkdir(exist_ok=True)
poppler=Path('[local path redacted]')
docs=[]
for c in row['file_copies']:
 path=Path(c['source_path']);assert sha(path)==c['sha256'];assert path.read_bytes().startswith(b'%PDF-')
 role=c['role_candidate'];pdf=pdfium.PdfDocument(str(path));reader=PdfReader(path);pages=[]
 for i in range(len(pdf)):
  t=TXT/f'{role}-{i+1:02}.txt';png=OUT/f'{role}-{i+1:02}.png'
  t.write_text(reader.pages[i].extract_text(extraction_mode='layout'),encoding='utf8')
  page=pdf[i];page.render(scale=150/72).to_pil().save(png);pages.append({'pdf_page':i+1,'text_path':str(t),'text_sha256':sha(t),'render_path':str(png),'render_sha256':sha(png),'text_read':False,'visual_review':False});page.close()
 docs.append({**c,'role':role,'detected_format':'PDF','page_count':len(pdf),'metadata':pdf.get_metadata_dict(),'pages':pages});pdf.close()
out={'schema':'mattersyn-source-preparation/1','author':'/root/peng1998_reader_assets','at':datetime.now(timezone.utc).isoformat(),'doi_candidate':'10.1021/la8031286','source_generation':1,'bundle_sha256':row['bundle_sha256'],'intake_manifest':{'path':str(I),'sha256':sha(I)},'documents':docs,'renderer':'pypdfium2/PDFium at 150 dpi; text from pypdf layout extraction (Poppler pdftotext not installed)','coverage_status':'prepared_only_not_yet_read','source_originals_unchanged':True}
(P/'source-preparation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps([{'role':d['role'],'page_count':d['page_count'],'metadata':d['metadata'],'sha256':d['sha256']}for d in docs],ensure_ascii=False))
