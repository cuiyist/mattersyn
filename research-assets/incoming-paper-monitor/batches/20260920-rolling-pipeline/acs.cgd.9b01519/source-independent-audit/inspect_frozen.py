from pathlib import Path
import json,sys
A=Path(__file__).parent;R=A.parent
def load(p):return json.loads(p.read_text(encoding='utf-8'))
assert (R/'package-freeze.json').exists(),'Do not inspect mutable author extraction before freeze.'
f=load(R/'source-facts.json')
mode=sys.argv[1] if len(sys.argv)>1 else 'summary'
if mode=='summary':
 print(json.dumps({k:(len(v) if isinstance(v,(list,dict)) else v) for k,v in f.items()},ensure_ascii=False,indent=2))
 print(json.dumps(load(R/'package-freeze.json'),ensure_ascii=False,indent=2)[:5500])
elif mode=='facts':
 start=int(sys.argv[2]);end=int(sys.argv[3])
 for i,x in enumerate(f['facts'][start:end],start):print(i,json.dumps(x,ensure_ascii=False))
elif mode in f:
 print(json.dumps(f[mode],ensure_ascii=False,indent=2))
elif mode=='asset':
 print(json.dumps(load(R/'original-assets-manifest.json'),ensure_ascii=False,indent=2))
elif mode=='tables':
 print(json.dumps(load(R/'source-tables.json'),ensure_ascii=False,indent=2))
