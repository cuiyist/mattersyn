from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
O=Path(__file__).resolve().parent;A=O.parent/'apparatus';P=A.parents[1]
def read(p):return json.loads(p.read_text('utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=0;bound={}
def check(v,m):
 global checks
 assert v,m
 checks+=1
def bind(p,h=None):
 p=Path(p);check(p.is_file(),'File '+str(p));s=sha(p)
 if h:check(s==h,'SHA '+str(p))
 bound[str(p.resolve())]=s
 return s
f=read(A/'package-freeze.json');bind(A/'package-freeze.json','cc8eb91a72ddb4a8f8c9741a0a0cfdffefed8364523662847bf4893ce1e18bd0')
for p,h in f['bound_files'].items():bind(p,h)
bind(P/'package-freeze.json',f['source_freeze_sha256']);bind(P/'canonical-proposal/v1/package-manifest.json',f['canonical_package_sha256'])
facts=read(P/'source-facts.json');bind(P/'source-facts.json');prep=read(P/'source-preparation.json');bind(P/'source-preparation.json')
for d in prep['documents']:
 bind(d['source_path'],d['sha256'])
 for page in d['pages']:bind(page['render_path'],page['render_sha256'])
sa=P/'source-independent-audit/independent-audit-v1.json';bind(sa,'792fe4a10d755d7db21d3c8dee035591a682563bfa9e5ffce3b1a9882daa37eb');check(read(sa)['status']=='passed','Prior independent source pass')
source_ops={o['id']:o for p in facts['protocols'] for o in p['operations']};check(len(source_ops)==19,'19 source operations')
factmap={x['id']:x for x in facts['facts']};bindings=read(A/'canonical-bindings.json')['bindings'];compact={r['record_id']:r for r in read(A/'records.json')}
check(len(bindings)==35 and len(compact)==14,'35 scenes in 14 records');check(len({x['scene_id'] for x in bindings})==35,'Unique scenes');check({x['operation_id'] for x in bindings}==set(source_ops),'Complete source action coverage')
qcount=0
for b in bindings:
 bind(b['record_path'],b['record_sha256']);r=read(Path(b['record_path']));op=r['operations'][int(b['operation_pointer'].split('/')[2])];s=source_ops[b['operation_id']]
 check(compact[r['record_id']]==r,'Whole canonical record transport');check(op['id']==b['operation_id'],'Operation pointer ID');check(op['evidence']==b['source_evidence'],'Operation evidence');check(r['quality']['requested_tasks']==[],'No task admission')
 check(len(s['quantities'])==len(op['parameters']),'Source operation quantity count '+op['id'])
 for sq,q in zip(s['quantities'],op['parameters'].values()):
  check(sq['raw_text']==q['raw_text'],'Raw token');check(sq['unit']==q['unit'],'Unit');check(sq['approximate']==q['approximate'],'Approximation');check(sq['status']==q['status'],'Status')
  if sq['range']:
   check(q['value'] is None and q['minimum']==sq['range']['min'] and q['maximum']==sq['range']['max'],'Range')
  else:check(q['value']==sq['value'],'Value')
  qcount+=1
 expected=[]
 for fid in b['supplemental_source_fact_ids']:
  check(fid in factmap,'Existing supporting fact')
  for e in factmap[fid]['evidence']:
   if e not in expected:expected.append(e)
 check(b['supplemental_source_evidence']==expected,'Exact supporting source locators')
check(qcount==43,'43 numeric rows, shared source method repeated only across three solvent routes')
pre=read(A/'preview-manifest.json');check(pre['scene_count']==35,'35 previews')
for x in pre['scenes']:
 sp=A/x['svg_path'];bind(sp,x['svg_sha256']);bind(A/x['png_path'],x['png_sha256']);root=ET.fromstring(sp.read_bytes());texts=[''.join(e.itertext()) for e in root.iter() if e.tag.endswith('text')]
 check(texts==x['visible_text'],'Visible SVG text inventory');check(not any('NaN' in t or 'undefined' in t for t in texts),'No invalid render tokens');check(x['scene_id']==x['record_id']+'--'+x['operation_id'],'Preview dispatch')
check({x['scene_id'] for x in pre['scenes']}=={x['scene_id'] for x in bindings},'Complete preview scene set')
for x in pre['contacts']:bind(A/x['path'],x['sha256'])
check([i for x in pre['contacts'] for i in x['scene_ids']]==[x['scene_id'] for x in pre['scenes']],'Complete contact set')
public=read(A/'public-asset-proposal.json')['assets'];check(len(public)==37,'Only two modules and 35 schematic SVGs')
for key,x in public.items():
 bind(x['path'],x['sha256']);check(Path(key).suffix in ['.mjs','.svg'],'No original source pages');check(Path(x['path']).resolve().is_relative_to(A.resolve()),'Package asset only')
check('source-render' not in json.dumps(public),'No full source-page projection')
for file in ['runtime-checks.json','check_runtime.mjs','preview-replay.json','replay_previews.py']:bind(O/file)
bind(Path(__file__))
# A preserved reader-only metadata revision appeared during this audit. It does not alter the apparatus inputs.
v2=P/'canonical-proposal/v2/record-manifest.json'
if v2.is_file():
 bind(v2);m2=read(v2);m1=read(P/'canonical-proposal/v1/record-manifest.json');one={x['record_id']:x for x in m1['records']};two={x['record_id']:x for x in m2['records']};check(set(one)==set(two),'V2 same 19 records')
 for rid,x in two.items():check(sha(Path(x['path']))==sha(Path(one[rid]['path'])),'V2 byte-identical canonical '+rid);bind(x['path'])
 for p in [P/'canonical-proposal/v2/package-manifest.json',P/'canonical-proposal/v2/reader-scope-delta.json']:
  if p.is_file():bind(p)
out={'schema':'mattersyn-independent-apparatus-package-checks/1','reviewer':'/root/peng1998_reader_assets','status':'passed','checks':checks,'source_quantities_checked':qcount,'source_pdf_hashes_verified':True,'all_author_freeze_files_unchanged':True,'bound_files':bound}
(O/'package-checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf-8');print(json.dumps({'checks':checks,'files':len(bound),'source_quantities':qcount}))
