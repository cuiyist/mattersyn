from pathlib import Path
import hashlib,json,subprocess
from pypdf import PdfReader
R=Path(__file__).resolve().parent
S=R.parent.parent.parent/'downloaded_papers'
POP=Path(r'[local path redacted]')
out=[]
for role,fn in [('main','10.1021_acs.chemmater.7b00354.pdf'),('si','10.1021_acs.chemmater.7b00354_si_1.pdf')]:
    p=S/fn; reader=PdfReader(p)
    folder=R/role; folder.mkdir(parents=True,exist_ok=True)
    texts=[]
    for n,page in enumerate(reader.pages,1):
        text=page.extract_text();texts.append(f'=== PAGE {n} ===\n{text}')
        (folder/f'page-{n:02d}.txt').write_text(text,encoding='utf-8')
    (folder/'full-text.txt').write_text('\n\n'.join(texts),encoding='utf-8')
    if not (folder/'page-1.png').exists():subprocess.run([str(POP),'-r','130','-png',str(p),str(folder/'page')],check=True,capture_output=True)
    out.append({'role':role,'source_path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'page_count':len(reader.pages),'page_sizes_pt':[[float(pg.mediabox.width),float(pg.mediabox.height)] for pg in reader.pages]})
(R/'source-manifest.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
