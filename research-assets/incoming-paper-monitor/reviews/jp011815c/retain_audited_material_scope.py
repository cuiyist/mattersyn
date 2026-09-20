from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';p=S/'data/paper-reviews/shah2001.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
d=read(p);private=read(B/'public-review-proposal/shah2001.json')
for f in ['Ag','Ir','Pt']:assert set(d['material_evidence_records'][f])==set(private['material_evidence_records'][f])
for k in ['material_evidence_records','material_evidence_scope_notes']:d[k]=private[k]
write(p,d)
m=read(B/'integration-manifest.json');m['reader_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();write(B/'integration-manifest.json',m)
print('Preserved exact audited material ordering and scope notes; material record sets unchanged.')
