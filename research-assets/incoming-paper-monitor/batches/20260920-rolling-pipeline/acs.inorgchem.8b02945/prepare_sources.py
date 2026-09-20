"""Read-only original PDF inspection and private source-render caches."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,logging
import pypdfium2 as pdfium
from pypdf import PdfReader
logging.getLogger('pypdf').setLevel(logging.ERROR)
P=Path(__file__).resolve().parent;I=P.parent/'intake-20260920T133256Z/intake-manifest.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
row=next(x for x in json.loads(I.read_text('utf8'))['papers'] if x['paper_id']=='legacy::10.1021_acs.inorgchem.8b02945')
assert row['source_generation']==1 and row['bundle_sha256']=='b13b449fbf4cab06f886ab37ee5e9051844453c5481dd533ab36a1869b78fdde'
out=P/'source-render';txt=out/'text';txt.mkdir(parents=True,exist_ok=True)
docs=[]
for c in row['file_copies']:
 p=Path(c['source_path']);assert sha(p)==c['sha256'];assert p.read_bytes().startswith(b'%PDF-')
 d=pdfium.PdfDocument(str(p));r=PdfReader(p);role=c['role_candidate'];pages=[]
 for i in range(len(d)):
  t=txt/f'{role}-{i+1:02}.txt';png=out/f'{role}-{i+1:02}.png';t.write_text(r.pages[i].extract_text(extraction_mode='layout'),'utf8')
  page=d[i];page.render(scale=150/72).to_pil().save(png);page.close()
  pages.append({'pdf_page':i+1,'text_path':str(t),'text_sha256':sha(t),'render_path':str(png),'render_sha256':sha(png),'text_read':False,'visual_review':False})
 docs.append({**c,'role':role,'detected_format':'PDF','page_count':len(d),'metadata':d.get_metadata_dict(),'pages':pages});d.close()
res={'schema':'mattersyn-source-preparation/1','author':'/root/peng1998_reader_assets','at':datetime.now(timezone.utc).isoformat(),'doi_candidate':'10.1021/acs.inorgchem.8b02945','source_generation':1,'bundle_sha256':row['bundle_sha256'],'intake_manifest':{'path':str(I),'sha256':sha(I)},'documents':docs,'renderer':'pypdfium2/PDFium at 150 dpi; text from pypdf layout extraction','coverage_status':'prepared_only_not_yet_read','source_originals_unchanged':True}
(P/'source-preparation.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps([{'role':d['role'],'pages':d['page_count'],'sha256':d['sha256']} for d in docs]))
