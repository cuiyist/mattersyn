from pathlib import Path
import json,hashlib,subprocess
from pypdf import PdfReader

B=Path(__file__).resolve().parent
M=B.parents[1]
incoming=Path('[local path redacted]')
legacy=Path('[local path redacted]')
ledger=json.loads((M/'ledger.json').read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for suffix in ['jp0473669','ja048427j']:
    target=B/suffix;target.mkdir(parents=True,exist_ok=True)
    hits={}
    for key in ['files','groups','doi_candidate_index','group_aliases']:
        obj=ledger.get(key,{})
        if isinstance(obj,dict):hits[key]={k:v for k,v in obj.items() if suffix in (k+json.dumps(v))}
        elif isinstance(obj,list):hits[key]=[v for v in obj if suffix in json.dumps(v)]
    (target/'ledger-candidate-snapshot.json').write_text(json.dumps(hits,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    documents=[]
    for root in [incoming,legacy]:
        for p in sorted(root.glob('*'+suffix+'*')):
            if not p.is_file():continue
            blob=p.read_bytes()
            d={'path':str(p),'sha256':sha(p),'bytes':len(blob),'pdf_signature':blob[:8].decode('ascii',errors='replace'),'has_eof_marker':b'%%EOF' in blob[-2048:],'location':'incoming'if root==incoming else'legacy'}
            if p.suffix.lower()=='.pdf':
                reader=PdfReader(p)
                d.update(page_count=len(reader.pages),metadata={str(k):str(v)for k,v in (reader.metadata or {}).items()},encrypted=reader.is_encrypted)
                if root==incoming:
                    role='si'if '_si_'in p.name else'main'
                    for i,page in enumerate(reader.pages,1):
                        (target/f'{role}-{i:02d}.txt').write_text(page.extract_text()or'',encoding='utf8')
                    proc=subprocess.run(['pdftoppm','-r','115','-png',str(p),str(target/role)],capture_output=True,text=True)
                    d['render_exit_code']=proc.returncode
                    if proc.returncode:d['render_error']=proc.stderr
            documents.append(d)
    (target/'intake-manifest.json').write_text(json.dumps({'ledger_sha256_at_read':sha(M/'ledger.json'),'documents':documents},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'suffix':suffix,'documents':[{k:v for k,v in d.items()if k not in ['metadata']}for d in documents],'ledger_matches':{k:len(v)for k,v in hits.items()}},indent=2))
