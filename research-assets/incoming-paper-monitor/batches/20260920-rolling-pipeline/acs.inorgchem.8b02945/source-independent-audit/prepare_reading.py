"""Independent immutable-source reading aids; no author extraction is read."""
from pathlib import Path
import json,hashlib,logging
from datetime import datetime,timezone
from pypdf import PdfReader
import pypdfium2 as pdfium
logging.getLogger('pypdf').setLevel(logging.ERROR)
O=Path(__file__).resolve().parent;R=O/'source-render';R.mkdir(exist_ok=True)
M=Path('[local path redacted]');B=M/'research-assets/incoming-paper-monitor/batches/20260920-rolling-pipeline'
intake=B/'intake-20260920T133256Z/intake-manifest.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paper=next(p for p in json.loads(intake.read_text())['papers'] if p['paper_id']=='legacy::10.1021_acs.inorgchem.8b02945')
out={'reviewer':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'intake_path':str(intake),'intake_sha256':sha(intake),'source_generation':paper['source_generation'],'bundle_sha256':paper['bundle_sha256'],'documents':[],'author_extraction_opened':False,'reading_status':'aids_prepared_not_yet_full_read'}
for f in paper['file_copies']:
 p=Path(f['source_path']);assert sha(p)==f['sha256'];role=f['role_candidate'];reader=PdfReader(p);pdf=pdfium.PdfDocument(str(p));pages=[]
 for i,pg in enumerate(reader.pages):
  t=R/f'{role}-{i+1:02}.txt';im=R/f'{role}-{i+1:02}.png';t.write_text(pg.extract_text() or '',encoding='utf8')
  page=pdf[i];bitmap=page.render(scale=2);bitmap.to_pil().save(im);bitmap.close();page.close()
  pages.append({'pdf_page':i+1,'text_path':str(t),'text_sha256':sha(t),'image_path':str(im),'image_sha256':sha(im),'text_read':False,'visual_review':False})
 pdf.close();assert sha(p)==f['sha256']
 out['documents'].append({'role':role,'source_path':str(p),'sha256':f['sha256'],'page_count':len(pages),'pages':pages})
 print(role,len(pages),flush=True)
(O/'reading-preparation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
