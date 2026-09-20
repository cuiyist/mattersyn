from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
O=Path(__file__).resolve().parent; A=O.parent/'apparatus'; P=A.parents[1]
def read(p):return json.loads(p.read_text('utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=0; bound={}
def check(x,msg):
 global checks
 assert x,msg
 checks+=1
def bind(p,h=None):
 p=Path(p);check(p.is_file(),'Exists '+str(p));s=sha(p)
 if h:check(s==h,'SHA '+str(p))
 bound[str(p.resolve())]=s
 return s
freeze=read(A/'package-freeze.json')
bind(A/'package-freeze.json','88a93e0c48e1752b4d12e6df7da771f102ab024bde0d55f22bcd37d7f727f4f2')
for p,h in freeze['bound_files'].items():bind(p,h)
facts=read(P/'source-facts.json');bind(P/'source-facts.json')
for d in facts['source_documents']:bind(d['source_path'],d['sha256'])
sa=read(P/'source-independent-audit/independent-audit-v2.json');check(sa['status']=='passed','Source passed')
source_ops={o['id']:o for p in facts['protocols'] for o in p['operations']}
bindings=read(A/'canonical-bindings.json')['bindings'];check(len(source_ops)==len(bindings)==39,'39 source and canonical operations')
check(len({(x['record_id'],x['operation_id']) for x in bindings})==39,'Unique operation bindings')
compact={r['record_id']:r for r in read(A/'records.json')}
source_quantity_count=0
for b in bindings:
 r=read(Path(b['record_path']));o=r['operations'][int(b['operation_pointer'].split('/')[2])];s=source_ops[o['id']]
 check(o['id']==b['operation_id'],'Operation ID')
 for k in ['operations','materials','material_states','condition_options']:
  check(compact[r['record_id']].get(k)==r.get(k),'Compact transport '+k)
 if o['id']=='nc-inject':
  check(not o['parameters'] and len(s['quantities'])==9,'Injection source options remain grouped')
  for option in r['condition_options']:
   for q in option['parameters'].values():
    check(any(x['raw_text']==q['raw_text'] and x['unit']==q['unit'] and x['value']==q['value'] for x in s['quantities']),'Condition option source value')
 elif o['id'] in ['nc-dry','ipa-or-etoac','meoac-spin','ta-acquire','dft-calculate']:
  expected={'nc-dry':['overnight'],'ipa-or-etoac':['1:2'],'meoac-spin':['1:1','12000'],'ta-acquire':['300','~150','80','445','550','600','300','370','420'],'dft-calculate':['6:6:6','3:3:3','25']}
  check([q['raw_text'] for q in s['quantities']]==expected[o['id']],'Explicit contextual/qualitative source values, manually checked in scene notes')
 else:check(len(o['parameters'])==len(s['quantities']),'Source quantity count '+o['id'])
 for q in o['parameters'].values():
  matches=[x for x in s['quantities'] if x['raw_text']==q['raw_text'] and x['unit']==q['unit']]
  check(bool(matches),'Source raw text and unit '+o['id']); sq=matches[0]
  check(q['approximate']==sq['approximate'],'Source approximation')
  if sq['comparison']=='>=':
   check(q['value'] is None and q['minimum']==sq['value'] and q.get('minimum_exclusive') is False,'Source lower bound')
  elif sq['range']:
   check(q['value'] is None and q['minimum']==sq['range']['min'] and q['maximum']==sq['range']['max'],'Source interval')
  else:check(q['value']==sq['value'],'Source value')
  source_quantity_count+=1
 check(len(b['source_evidence'])>0,'Source evidence bound')
check(source_quantity_count==67,'All 67 source operation quantities')
preview=read(A/'preview-manifest.json')
for item in preview['scenes']:
 sp=A/item['svg_path'];pp=A/item['png_path'];bind(sp,item['svg_sha256']);bind(pp,item['png_sha256'])
 root=ET.fromstring(sp.read_bytes()); texts=[''.join(e.itertext()) for e in root.iter() if e.tag.endswith('text')]
 check(texts==item['visible_text'],'Exact visible SVG text '+item['operation_id'])
 check(all('NaN' not in x and 'undefined' not in x for x in texts),'No invalid generated values')
check({s['operation_id'] for s in preview['scenes']}==set(source_ops),'All source operations previewed')
for item in preview['contacts']:bind(A/item['path'],item['sha256'])
pages={'main':[2,3,4,5,7,8,9,10],'si':[3,6,7,11,13]}
for role,nums in pages.items():
 for n in nums:bind(P/'source-render'/f'{role}-{n:02d}.png')
bind(O/'check_runtime.mjs');bind(O/'runtime-checks.json');bind(Path(__file__))
result={'schema':'mattersyn-independent-apparatus-package-checks/1','reviewer':'/root/peng1998_reader_assets','status':'passed','checks':checks,'source_quantities_checked':source_quantity_count,'source_pdf_hashes_verified':True,'bound_files':bound}
(O/'package-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'checks':checks,'bound_files':len(bound),'source_quantities':source_quantity_count}))
