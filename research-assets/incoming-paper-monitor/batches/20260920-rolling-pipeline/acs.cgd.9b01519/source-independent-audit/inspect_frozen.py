from pathlib import Path
import json,sys
A=Path(__file__).parent;R=A.parent
def load(p):return json.loads(p.read_text(encoding='utf-8'))
assert (R/'package-freeze.json').exists(),'Do not inspect mutable author extraction before freeze.'
f=load(R/'source-facts.json')
mode=sys.argv[1] if len(sys.argv)>1 else 'summary'
def slim(x):
 if isinstance(x,list):return [slim(v) for v in x]
 if isinstance(x,dict):
  return {k:([(e.get('pdf_page'),e.get('locator')) for e in v] if k=='evidence' else slim(v)) for k,v in x.items() if v is not None and k not in ['independent_audit_status','quantity_scope_note']}
 return x
if mode=='summary':
 print(json.dumps({k:(len(v) if isinstance(v,(list,dict)) else v) for k,v in f.items()},ensure_ascii=False,indent=2))
 print(json.dumps(load(R/'package-freeze.json'),ensure_ascii=False,indent=2)[:5500])
elif mode in ['facts','claims']:
 start=int(sys.argv[2]);end=int(sys.argv[3])
 for i,x in enumerate(f['facts'][start:end],start):
  if mode=='claims':
   x={k:v for k,v in x.items() if k not in ['independent_audit_status']}
   x['evidence']=[(e['pdf_page'],e['locator']) for e in x['evidence']]
   x['quantities']=[{k:v for k,v in q.items() if v is not None and k!='evidence'} for q in x['quantities']]
  print(i,json.dumps(x,ensure_ascii=False))
elif mode in f:
 for x in f[mode]:print(json.dumps(slim(x),ensure_ascii=False))
elif mode=='asset':
 print(json.dumps(load(R/'original-assets-manifest.json'),ensure_ascii=False,indent=2))
elif mode=='tables':
 print(json.dumps(load(R/'source-tables.json'),ensure_ascii=False,indent=2))
