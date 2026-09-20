from pathlib import Path
import hashlib,json,sys,datetime
M=Path('[local path redacted]')
sys.path.insert(0,str(M/'research-assets/corpus-20260917/runtime'))
sys.path.insert(0,str(M/'research-assets/rdkit-runtime'))
sys.path.append('[local path redacted]')
import fitz
import pypdfium2 as pdfium
A=Path(__file__).resolve().parent;B=A.parent.parent;I=B/'intake-20260920T111852Z/intake-manifest.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
item=next(p for p in json.loads(I.read_text())['papers'] if p['paper_id']=='10.1021_acsanm.2c04342')
copies=[]
for p in item['file_copies']:
 f=Path(p['source_path']);actual=sha(f);assert actual==p['sha256']
 copies.append({'path':str(f),'sha256':actual,'bytes':f.stat().st_size,'role_candidate':p['role_candidate']})
for directory in ['audit-pages','audit-text']:(A/directory).mkdir(exist_ok=True)
documents=[]
for role in ['main','si']:
 source=Path(next(p['path'] for p in copies if p['role_candidate']==role))
 d=fitz.open(source);raster=pdfium.PdfDocument(source);pages=[]
 for i,page in enumerate(d):
  t=A/'audit-text'/f'{role}-{i+1:02}.txt';t.write_text(page.get_text(sort=True),encoding='utf-8')
  p=A/'audit-pages'/f'{role}-{i+1:02}.png';raster[i].render(scale=2.6).to_pil().save(p)
  pages.append({'page':i+1,'text':str(t),'text_sha256':sha(t),'render':str(p),'render_sha256':sha(p),'read_status':'pending'})
 documents.append({'role_candidate':role,'source_path':str(source),'source_sha256':sha(source),'page_count':len(d),'pages':pages})
out={'schema':'mattersyn-independent-source-reading/1','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'/root/norberg2004_extract','intake':str(I),'intake_sha256':sha(I),'source_generation':item['source_generation'],'bundle_sha256':item['bundle_sha256'],'original_copies':copies,'renderer':'pypdfium2 PDFium scale=2.6','documents':documents,'scope':'Independent source reading preparation before opening author extraction; not completed review.'}
(A/'reading-inputs.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'documents':[{'role':x['role_candidate'],'pages':x['page_count']} for x in documents],'copies':copies,'manifest':str(A/'reading-inputs.json')},indent=2))
