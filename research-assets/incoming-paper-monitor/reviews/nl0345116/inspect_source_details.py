from pathlib import Path
import sys,json,re
sys.path.insert(0,'[local path redacted]')
import pymupdf
B=Path(__file__).resolve().parent
S=Path('[local path redacted]')
d=pymupdf.open(S)
# Column-contiguous reference text, preserving source spelling without external normalization.
t=d[5].get_text(clip=pymupdf.Rect(315,145,610,745))+'\n'+d[6].get_text(clip=pymupdf.Rect(40,25,310,730))+'\n'+d[6].get_text(clip=pymupdf.Rect(310,25,610,730))
refs=[]
parts=re.split(r'(?m)^\((\d+)\)\s*',t)
for n,tx in zip(parts[1::2],parts[2::2]):
 tx=re.sub(r'\s+',' ',tx).strip();tx=re.sub(r' NL0345116.*','',tx)
 refs.append({'number':int(n),'page':6 if int(n)<=30 else 7,'text':tx})
(B/'reference-candidates.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2),encoding='utf8')
for n in [5,6]:
 # Full columns with equations, not rewritten diagrams.
 w,h=d[n-1].rect.width,d[n-1].rect.height
 pix=d[n-1].get_pixmap(matrix=pymupdf.Matrix(4,4),clip=pymupdf.Rect(w*.07,h*(.47 if n==5 else .025),w*.52,h*(.94 if n==5 else .59)))
 pix.save(B/f'equation-detail-p{n}.png')
print(json.dumps({'refs':len(refs),'numbers':[r['number']for r in refs],'metadata':d.metadata,'si_text_matches':[(i+1, bool(re.search('supporting|supplement',p.get_text(),re.I)))for i,p in enumerate(d)]}))
