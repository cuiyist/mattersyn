from inspect_delta import *
Q=E/'site-integration-proposal/v2'
for name in ['records/evans-2010-species9-crystallization.json','records/evans-2010-molecular9-structure.json','molecules/bindings-additions.json','reader/evans2010.json','promotion-manifest.json']:
    a=P/name;b=Q/name
    if a.exists() and b.exists():
        ds=diff(load(a),load(b)); print(name,len(ds))
        for path,x,y in ds:print(path,str(y)[:4500])
print('v2files',[str(p.relative_to(Q)) for p in Q.rglob('*.json') if 'dist' not in p.parts and 'records' not in p.parts])
print('modelkeys',load(Q/'dist/assets/chemical-registry/models/evans2010-species9-source-cif.json').keys() if (Q/'dist/assets/chemical-registry/models/evans2010-species9-source-cif.json').exists() else 'find model')
