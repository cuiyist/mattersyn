from pathlib import Path
import hashlib,json,subprocess
from pypdf import PdfReader
R=Path(__file__).resolve().parent
ROOT=R.parents[2]
P=Path('[local path redacted]')
out=[]
for role,name in [('main','10.1021_acs.jpcc.8b11124.pdf'),('si','10.1021_acs.jpcc.8b11124_si_1.pdf')]:
 source=ROOT/'downloaded_papers'/name;pdf=PdfReader(source);folder=R/role;folder.mkdir(exist_ok=True)
 doc={'role':role,'source_path':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'page_count':len(pdf.pages),'pages':[]}
 whole=[]
 for n,p in enumerate(pdf.pages,1):
  t=p.extract_text();(folder/f'page-{n:02d}.txt').write_text(t,encoding='utf-8');whole.append(f'=== PAGE {n} ===\n'+t)
  proc=subprocess.run([str(P),'-f',str(n),'-l',str(n),'-singlefile','-r','144','-png',str(source),str(folder/f'page-{n:02d}')],capture_output=True,check=True)
  doc['pages'].append({'page':n,'text_read':False,'visual_review':False,'sections':[],'unresolved':[],'local_text_path':str(folder/f'page-{n:02d}.txt'),'local_render_path':str(folder/f'page-{n:02d}.png'),'render_notes':proc.stderr.decode('utf-8',errors='replace').strip()})
 (folder/'full-text.txt').write_text('\n\n'.join(whole),encoding='utf-8');out.append(doc)
(R/'source-manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps([{k:v for k,v in d.items() if k!='pages'} for d in out],indent=2))
