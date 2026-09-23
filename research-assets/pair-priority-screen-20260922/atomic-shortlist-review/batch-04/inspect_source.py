import argparse,json,re,hashlib,sys
from pathlib import Path
sys.dont_write_bytecode=True
import pypdfium2 as pdfium
O=Path(__file__).resolve().parent;P=O/'private'
D=json.loads((P/'source-preparation.json').read_text(encoding='utf-8'))['source_files']
ap=argparse.ArgumentParser();ap.add_argument('--sha',required=True);ap.add_argument('--pages',default='');ap.add_argument('--find',default='atomic|fractional|coordinate|CCDC|CIF|Rietveld');a=ap.parse_args()
h=next(x for x in D if x.startswith(a.sha));f=D[h];assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==h
pdf=pdfium.PdfDocument(f['path']); texts=[]
for i in range(len(pdf)):
    page=pdf[i];t=page.get_textpage().get_text_range().replace('\r\n','\n').replace('\r','\n');texts.append(t)
    hits=[line.strip()for line in t.splitlines()if re.search(a.find,line,re.I)]
    if hits:print(json.dumps({'page':i+1,'hits':hits},ensure_ascii=False))
(P/f'{h[:12]}-all-source-text.txt').write_text('\n\n'.join(f'--- PDF PAGE {i+1} ---\n{t}'for i,t in enumerate(texts)),encoding='utf-8')
for pno in [int(s)for s in a.pages.split(',')if s]:
    ip=P/f'{h[:12]}-p{pno:03d}.png';tp=P/f'{h[:12]}-p{pno:03d}.txt'
    if not ip.exists():pdf[pno-1].render(scale=2).to_pil().save(ip)
    if not tp.exists():tp.write_text(texts[pno-1],encoding='utf-8')
pdf.close()
