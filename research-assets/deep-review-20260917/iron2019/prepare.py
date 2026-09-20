import concurrent.futures,hashlib,json,subprocess
from pathlib import Path
from pypdf import PdfReader
BASE=Path('[local path redacted]')
OUT=Path(__file__).parent
POP='[local path redacted]'
docs=[];jobs=[]
for role,suffix in [('main',''),('si','_si_1')]:
    pdf=BASE/'downloaded_papers'/f'10.1021_acsnano.8b05032{suffix}.pdf'
    reader=PdfReader(pdf);pages=[]
    for i,p in enumerate(reader.pages,1):
        textdir=OUT/'text';textdir.mkdir(exist_ok=True)
        renderdir=OUT/'pages';renderdir.mkdir(exist_ok=True)
        txt=textdir/f'{role}-{i:02}.txt';txt.write_text(p.extract_text(),encoding='utf-8')
        target=renderdir/f'{role}-{i:02}'
        pages.append({'page':i,'text_path':str(txt),'image_path':str(target.with_suffix('.png')),'page_size_points':[float(p.mediabox.width),float(p.mediabox.height)],'text_read':False,'visual_review':False,'sections':[],'unresolved':[]})
        jobs.append((pdf,i,target))
    docs.append({'role':role,'source_path':str(pdf),'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'page_count':len(reader.pages),'pages':pages})
def render(job):
    pdf,i,target=job
    subprocess.run([POP,'-f',str(i),'-l',str(i),'-singlefile','-r','145','-png',str(pdf),str(target)],check=True,capture_output=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(render,jobs))
(OUT/'document-inventory.json').write_text(json.dumps(docs,indent=2),encoding='utf-8')
print('Prepared',len(jobs),'pages across',len(docs),'documents.')
