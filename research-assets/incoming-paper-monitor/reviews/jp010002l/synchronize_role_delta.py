from pathlib import Path
import json,hashlib,copy
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
a=read(B/'role-normalization-source-audit.json');assert a['status']=='passed'
delta=read(B/'role-normalization-delta.json');assert delta['changed_field_count']==24
for item in delta['changed_records']:
 p=S/'data/records'/item['file'];r=read(p);draft=read(B/'canonical-drafts'/item['file']);assert sha(B/'canonical-drafts'/item['file'])==a['record_hashes'][r['record_id']]
 for patch in item['patches']:
  m=next(m for m in r['materials']if m['id']==patch['material_id']);key=patch['path'].split('/')[-1];assert key in ['role','notes'];assert m[key]==patch['before'];m[key]=patch['after']
 x=copy.deepcopy(r);x['quality']['review_status']=draft['quality']['review_status'];x['quality']['review_scope']=draft['quality']['review_scope'];x['sources'][0]['main_status']=draft['sources'][0]['main_status'];assert x==draft
 write(p,r)
p=S/'dist/assets/chemical-registry/bindings.json';bindings=read(p)
for item in delta['changed_records']:bindings['sourceRecordSha256'][item['record_id']]=sha(S/'data/records'/item['file'])
write(p,bindings)
p=B/'integration-manifest.json';m=read(p);m['role_normalization_audit']='role-normalization-source-audit.json';m['records']={p.stem:sha(S/'data/records'/p.name)for p in (B/'canonical-drafts').glob('*.json')};write(p,m)
print('Applied only the independently audited role/notes delta; scientific fields and reader unchanged.')
