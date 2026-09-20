from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
import pypdfium2 as pdfium
O=Path(__file__).resolve().parent;P=O.parent;B=P.parent
J=lambda p:json.loads(Path(p).read_text('utf-8-sig'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest=B/'intake-20260920T141934Z/intake-manifest.json'
intake=J(manifest)
paper=next(x for x in intake['papers'] if x['paper_id']=='legacy::10.1021_acs.jpcc.5c05144')
out=O/'source-render';out.mkdir(parents=True,exist_ok=True);rows=[]
for item in paper['file_copies']:
 p=Path(item['source_path']);assert sha(p)==item['sha256'];role=item['role_candidate'];doc=pdfium.PdfDocument(str(p))
 assert len(doc)=={'main':9,'si':11}[role]
 for i in range(len(doc)):
  page=doc[i];tp=page.get_textpage();text=tp.get_text_range();tp.close()
  png=out/f'{role}-{i+1:02}.png';txt=out/f'{role}-{i+1:02}.txt'
  assert not png.exists() and not txt.exists()
  page.render(scale=2).to_pil().convert('RGB').save(png);txt.write_text(text,'utf8')
  rows.append(dict(role=role,pdf_page=i+1,pdf_path=str(p),source_sha256=item['sha256'],png=str(png),png_sha256=sha(png),text_path=str(txt),text_sha256=sha(txt),actual_text_read=False,actual_visual_inspection=False));page.close()
 doc.close()
report=dict(auditor='/root/backlog_eta',prepared_at=datetime.now(timezone.utc).isoformat(),note='Preparation only; read/view completion must be recorded separately after actual inspection.',intake_sha256=sha(manifest),paper=paper,pages=rows)
(O/'reading-preparation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n','utf8')
print(json.dumps({'pages':len(rows),'source_hashes_verified':len(paper['file_copies'])}))
