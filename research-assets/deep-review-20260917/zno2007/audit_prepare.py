from pathlib import Path
from pypdf import PdfReader
import json,hashlib
R=Path(__file__).resolve().parent;C=json.loads((R/'coverage.json').read_text(encoding='utf-8'))
(R/'audit-text').mkdir(exist_ok=True)
for d in C['documents']:
 p=Path(d['source_path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==d['sha256']
 pdf=PdfReader(p);assert len(pdf.pages)==d['page_count']
 for n,page in enumerate(pdf.pages,1):(R/'audit-text'/f"{d['role']}-{n}.txt").write_text(page.extract_text(),encoding='utf-8')
print('Nine original source pages text-extracted; source hashes verified.')
