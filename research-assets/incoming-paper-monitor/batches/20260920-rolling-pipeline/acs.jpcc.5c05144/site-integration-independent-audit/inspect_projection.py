from pathlib import Path
import json,sys,collections
sys.dont_write_bytecode=True
J=Path(__file__).resolve().parents[1]; P=J/'site-integration-proposal/v1'; M=J.parents[4]
sys.path.insert(0,str(M/'research-assets'))
from sync_github_public import io_path
def read(p):return json.loads(io_path(p).read_text('utf8'))
def diff(a,b,p=''):
 if type(a)!=type(b):return [(p,a,b)]
 if isinstance(a,dict):
  return sum((diff(a[k],b[k],p+'/'+k) if k in a and k in b else [(p+'/'+k,a.get(k,'<absent>'),b.get(k,'<absent>'))] for k in sorted(set(a)|set(b))),[])
 if isinstance(a,list):
  if len(a)!=len(b):return [(p+'#length',len(a),len(b))]
  return sum((diff(x,y,p+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
 return [] if a==b else [(p,a,b)]
manifest=read(P/'promotion-manifest.json')
print('counts',manifest['counts'])
pairs=[('reader',J/'canonical-proposal/v1/reader/sasongko2025.json',P/'reader/sasongko2025.json'),
 ('molecule-registry',J/'visuals/molecules/registry-additions.json',P/'molecules/registry-additions.json'),
 ('molecule-bindings',J/'visuals/molecules/bindings-proposal.json',P/'molecules/bindings-additions.json'),
 ('solutions',J/'visuals/molecules/solution-components-proposal.json',P/'molecules/solution-components-additions.json'),
 ('product-contexts',J/'visuals/products/public-product-contexts-proposal.json',P/'products/product-contexts-additions.json'),
 ('product-registry',J/'visuals/products/registry-additions.json',P/'products/registry-additions.json')]
for name,a,b in pairs:
 d=diff(read(a),read(b));print(name,len(d));print(json.dumps(d[:100] if name=='reader' else d[:12],ensure_ascii=False,indent=1))
for row in manifest['records'][:2]:
 rid=row['record_id'];d=diff(read(Path(row['original_path'])),read(P/'records'/(rid+'.json')));print(rid,json.dumps(d,ensure_ascii=False,indent=1))
print('reader keys',read(P/'reader/sasongko2025.json').keys())
print('freeze keys',read(P/'package-freeze.json').keys())
for f in ['visuals/molecules/package-freeze.json','visuals/products/package-freeze.json','visuals/apparatus/package-freeze.json','canonical-proposal/v1/package-freeze.json']:
 d=read(J/f);print(f,list(d),json.dumps(d,ensure_ascii=False)[:600])
