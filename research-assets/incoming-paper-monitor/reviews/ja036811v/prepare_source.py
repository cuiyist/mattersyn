from pathlib import Path
import json,hashlib,subprocess,pdfplumber
B=Path(__file__).resolve().parent;MON=B.parent.parent;ROOT=Path(r'[local path redacted]')
g=json.loads((MON/'ledger.json').read_text(encoding='utf8'))['groups']['10.1021_ja036811v']
manifest={'doi':'10.1021/ja036811v','fingerprint':g['fingerprint'],'documents':[]}
for role,name in [('main','10.1021_ja036811v.pdf'),('si','10.1021_ja036811v_si_1.pdf')]:
 p=ROOT/name
 with pdfplumber.open(p)as pdf:
  count=len(pdf.pages)
  for i,page in enumerate(pdf.pages,1):(B/f'{role}-{i:02}.txt').write_text(page.extract_text(layout=True),encoding='utf8')
  manifest['documents'].append({'role_candidate':role,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'page_count':count,'metadata':pdf.metadata})
 subprocess.run([r'[local path redacted]','-r','125','-png',str(p),str(B/role)],check=True)
(B/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(manifest,ensure_ascii=False))
