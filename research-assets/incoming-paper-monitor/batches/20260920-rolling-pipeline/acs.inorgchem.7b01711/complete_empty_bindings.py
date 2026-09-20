"""Observation records without reagents require explicit empty registry mappings."""
from pathlib import Path
import hashlib,json,shutil
N=Path(__file__).resolve().parent;O=N/'site-integration-proposal';S=N.parents[4]/'recipe-atlas'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=S/'dist/assets/chemical-registry/bindings.json';before=sha(p);b=read(p);changes=[]
shutil.copy2(p,O/'bindings-before-empty-completion.json')
for path in (O/'v1/records').glob('*.json'):
 r=read(path);rid=r['record_id']
 if rid in b['recordBindings']:continue
 assert not r['materials'],rid
 b['recordBindings'][rid]={};b['bindingNotes'][rid]={};changes.append(rid)
assert len(changes)==7
p.write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(O/'empty-binding-delta.json').write_text(json.dumps({'before_sha256':before,'after_sha256':sha(p),'records':sorted(changes),'change':'Explicit empty recordBindings and bindingNotes only for seven zero-material observation records. No chemical identities, scientific fields or source links changed.','script_sha256':sha(Path(__file__))},indent=2)+'\n',encoding='utf8')
print(json.dumps({'empty_bindings_completed':len(changes),'scientific_fields_changed':0}))
