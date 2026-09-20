from pathlib import Path
import json,hashlib,subprocess,pdfplumber
B=Path(__file__).resolve().parent;MON=B.parent.parent;ROOT=Path(r'[local path redacted]')
g=json.loads((MON/'ledger.json').read_text(encoding='utf8'))['groups']['10.1021_nl0345116']
manifest={'doi':'10.1021/nl0345116','fingerprint':g['fingerprint'],'documents':[]}
p=ROOT/'10.1021_nl0345116.pdf'
with pdfplumber.open(p)as pdf:
 count=len(pdf.pages)
 for i,page in enumerate(pdf.pages,1):(B/f'main-{i:02}.txt').write_text(page.extract_text(layout=True)or'',encoding='utf8')
 manifest['documents'].append({'role_candidate':'main','path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'page_count':count,'metadata':pdf.metadata})
subprocess.run([r'[local path redacted]','-r','125','-png',str(p),str(B/'main')],check=True)
(B/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(manifest,ensure_ascii=False))
