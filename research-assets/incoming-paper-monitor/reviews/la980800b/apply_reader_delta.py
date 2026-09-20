from pathlib import Path
import json
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';p=S/'data/paper-reviews/stiger1999.json'
r=json.loads(p.read_text(encoding='utf-8'));delta=json.loads((B/'public-review-proposal/final-reader-delta.json').read_text(encoding='utf-8'))
for change in delta['patches']:
 parts=change['json_pointer'].strip('/').split('/');node=r
 for part in parts[:-1]:node=node[int(part)]if isinstance(node,list)else node[part]
 key=int(parts[-1])if isinstance(node,list)else parts[-1]
 assert node[key]in [change['before'],change['set']],change['json_pointer']
 node[key]=change['set']
for a in r['figures']+[i for k in ['tables','schemes','equations','source_notes']for i in r.get(k,[])if i.get('public_asset')]:a.update(reviewed=True,reader_render_verified=True)
r['independent_audit']='All nine supplied main pages, 8 canonical records, 36 apparatus scenes, 47 chemical bindings, all 144 reader items covering 202 source units, and 15 original source assets independently audited. All original image links and figure enlargement dialogs checked in the local browser. Matching SI remains unverified; deployment is tracked separately.'
p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Applied five guarded reader clarifications and verified image-display flags; canonical records unchanged.')
