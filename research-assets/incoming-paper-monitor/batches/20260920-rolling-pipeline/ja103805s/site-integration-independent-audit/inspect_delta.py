import json
from pathlib import Path
E=Path(__file__).resolve().parents[1]
P=E/'site-integration-proposal/v1'
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def diff(a,b,p=''):
    if type(a)!=type(b):return [(p,a,b)]
    if isinstance(a,dict):
        out=[]
        for k in sorted(a.keys()|b.keys()):
            if k not in a:out.append((p+'/'+k,'<absent>',b[k]))
            elif k not in b:out.append((p+'/'+k,a[k],'<absent>'))
            else:out+=diff(a[k],b[k],p+'/'+k)
        return out
    if isinstance(a,list):
        if len(a)!=len(b):return [(p,a,b)]
        return sum((diff(x,y,p+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
    return [] if a==b else [(p,a,b)]
if __name__=='__main__':
    old=load(E/'public-review-proposal/v3/evans2010.json');new=load(P/'reader/evans2010.json')
    ds=diff(old,new)
    print('Reader diffs',len(ds))
    for path,a,b in ds:
        print(path, '=>',str(b)[:400] if not path.startswith('/recipe_inventory/') else str(b)[:60])
    pm=load(P/'promotion-manifest.json')
    print('SCOPE',pm['scope']);print('PENDING',pm['pending_gates'])
    print('REGISTRY_KEYS',load(P/'molecules/registry-additions.json').keys())
    print('BINDING_KEYS',load(P/'molecules/bindings-additions.json').keys())
    print('asset sample',pm['public_assets'][0]);print('freeze sample',load(P/'package-freeze.json')['files'][0])
