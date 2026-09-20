from pathlib import Path
import json,hashlib,subprocess
import pdfplumber
B=Path(__file__).resolve().parent
MON=B.parent.parent
P=Path(r'[local path redacted]')
ledger=json.loads((MON/'ledger.json').read_text(encoding='utf-8'))
g=ledger['groups']['10.1021_jp010002l']
manifest={'source_path':str(P),'sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'fingerprint':g['fingerprint'],'documents':[]}
with pdfplumber.open(P) as pdf:
    manifest['main_page_count']=len(pdf.pages)
    for i,p in enumerate(pdf.pages,1):
        (B/f'main-{i:02}.txt').write_text(p.extract_text(layout=True),encoding='utf-8')
    manifest['metadata']=pdf.metadata
for k,h in g['fingerprint']['files'].items():
    f=ledger['files'][k]
    manifest['documents'].append({'filename':k,'sha256':h,'role_candidate':f.get('role'),'page_count':manifest['main_page_count']})
(B/'source-manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
subprocess.run([r'[local path redacted]','-r','125','-png',str(P),str(B/'main')],check=True)
print(json.dumps({'main_pages':manifest['main_page_count'],'sha256':manifest['sha256'],'documents':manifest['documents']}))

