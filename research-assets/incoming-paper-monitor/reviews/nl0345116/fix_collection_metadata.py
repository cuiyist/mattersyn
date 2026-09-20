from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
bindings_path=S/'dist/assets/chemical-registry/bindings.json';bindings=read(bindings_path);manifest=read(B/'integration-manifest.json')
for rid in manifest['records']:
 p=S/'data/records'/(rid+'.json');r=read(p);assert r.get('collection')in[None,'reviewed_literature'];r['collection']='reviewed_literature';write(p,r);h=hashlib.sha256(p.read_bytes()).hexdigest();bindings['sourceRecordSha256'][rid]=h;manifest['records'][rid]=h
manifest['record_promotion_changes'].append('collection');manifest['collection_promotion']='reviewed_literature assigned to the 15 audited literature records; no scientific payload changes.'
write(bindings_path,bindings);write(B/'integration-manifest.json',manifest)
p=B/'integrate_review.py';s=p.read_text(encoding='utf8').replace("r=read(p);r['quality'].update","r=read(p);r['collection']='reviewed_literature';r['quality'].update");p.write_text(s,encoding='utf8')
print('Assigned missing literature collection metadata to 15 promoted records; scientific content unchanged.')
