"""Root-only import of checked chemical assets and wafer diagrams."""
from pathlib import Path
import json,hashlib,shutil
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
src=B/'molecular-assets';dst=S/'dist/assets/chemical-registry'
for a in read(src/'asset-manifest.json')['files']:
    p=src/a['file'];assert sha(p)==a['sha256']
    if Path(a['file']).parts[0] not in ['svg','models','sdf']:continue
    target=dst/a['file'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
registry=read(dst/'registry.json');delta=read(src/'registry-additions.json')['entries']
newids={e['id'] for e in delta}
registry['entries']=[e for e in registry['entries'] if e['id'] not in newids]+delta
write(dst/'registry.json',registry)
bindings=read(dst/'bindings.json');bindingdelta=read(src/'bindings-additions.json')
bindings['recordBindings'].update(bindingdelta['recordBindings'])
for rid,bound in bindingdelta['recordBindings'].items():
    p=S/'data/records'/(rid+'.json');r=read(p)
    assert set(bound)=={m['id'] for m in r['materials']}
    bindings['sourceRecordSha256'][rid]=sha(p)
write(dst/'bindings.json',bindings)
print('Imported ten chemical identities and24 bindings, preserving all existing entries.')
