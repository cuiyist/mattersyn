from pathlib import Path
import sys,json,hashlib,re,math,datetime
A=Path(__file__).parent;R=A.parent;M=Path('[local path redacted]')
sys.path.insert(0,str(M/'research-assets/rdkit-runtime'))
sys.path.append('[local path redacted]')
import pypdfium2
from PIL import Image
load=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[]
def check(label,value):checks.append({'check':label,'passed':bool(value)})
freeze=load(R/'package-freeze.json');facts=load(R/'source-facts.json');tables=load(R/'source-tables.json');inventory=load(R/'source-inventory.json');assets=load(R/'original-assets-manifest.json')['assets'];reading=load(A/'independent-table1.json')
for p,h in freeze['bound_files'].items():check('frozen hash '+p,Path(p).exists() and sha(p)==h)
for p,h in freeze['source_hashes'].items():check('original source hash '+p,sha(p)==h)
doc=pypdfium2.PdfDocument(next(iter(freeze['source_hashes'])))
check('original 11 pages',len(doc)==11)
rows=tables['tables'][0]['rows'];check('37 rows',len(rows)==37)
norm=lambda s:re.sub(r'\s+','',str(s)).replace('−','-').replace('–','-').replace('≈','~')
for er,ar in zip(reading['rows'],rows):
 check('independent label '+er[0],er[0]==ar['row_label']==ar['sample_id'])
 for j,(raw,c) in enumerate(zip(er[1:],ar['cells'])):
  actual=c['raw_text'];expected=raw
  if 'day' in raw:
   if 'day' not in actual:actual=actual+' '+c['unit']
   actual=actual.replace('days','day');expected=expected.replace('days','day')
  check('independent raw '+er[0]+'/'+str(j),norm(expected)==norm(actual))
  unit=['M','degC','ratio_parts','min','min'][j]
  if 'day' in raw:unit='day'
  if raw=='RT':unit=None
  check('table unit '+c['id'],c['unit']==unit)
  if raw=='RT':check('room temp not invented '+c['id'],c['value'] is None and c['status']=='reported_text')
  if j==2:check('ratio components '+c['id'],c['components']==[float(v) for v in raw.split(':')])
  if raw.startswith('~'):check('approximate '+c['id'],c['approximate'] is True)
  if '–' in raw:check('interval '+c['id'],c['range']=={'min':0.0,'max':40.0} and c['value'] is None)
  if raw not in ['RT'] and ':' not in raw and '–' not in raw:check('table numeric '+c['id'],c['value']==float(raw.lstrip('~').split()[0]))
def pointer(x,p):
 for k in p.lstrip('/').split('/'):
  k=k.replace('~1','/').replace('~0','~');x=x[int(k)] if isinstance(x,list) else x[k]
 return x
cache={'source-facts.json':facts,'source-tables.json':tables}
units=inventory['inventory_units'];check('unique unit ids',len(units)==len({x['id'] for x in units}))
for u in units:
 if u['path'] not in cache:cache[u['path']]=load(R/u['path'])
 try:v=pointer(cache[u['path']],u['json_pointer']);ok=v.get('id',v.get('row_label'))==u['source_object_id']
 except Exception:ok=False
 check('unit pointer '+u['id'],ok)
def walk(x,path=''):
 if isinstance(x,list):
  for i,v in enumerate(x):yield from walk(v,path+'/'+str(i))
 elif isinstance(x,dict):
  yield path,x
  for k,v in x.items():yield from walk(v,path+'/'+k)
fids={x['id'] for x in facts['facts']};cids={x['id'] for x in facts['conflicts']};gids={x['id'] for x in facts['missingness']};aids={x['id'] for x in assets};mid={x['id'] for x in facts['materials']};sid={x['id'] for x in facts['stocks']}
for rootname,root in [('facts',facts),('tables',tables)]:
 for path,x in walk(root):
  for field,univ in [('source_fact_ids',fids),('context_fact_ids',fids),('conflict_ids',cids),('gap_ids',gids)]:
   for v in x.get(field,[]):check(rootname+path+'/'+field+'/'+v,v in univ)
  if 'source_sha256' in x and 'pdf_page' in x:check('locator '+rootname+path,x['source_sha256']==reading['source_sha256'] and 1<=x['pdf_page']<=11 and x.get('document_role','main')=='main')
  if 'raw_text' in x and 'meaning' in x:
   check('quantity evidence '+rootname+path,bool(x.get('evidence')))
   raw=x['raw_text']
   if x.get('value') is not None:
    token=raw.lstrip('~<>=').strip().split()[0]
    try:expected=float(token.split('(')[0]) if '/' not in token else float(token.split('/')[0])/float(token.split('/')[1])
    except ValueError:expected=None
    check('typed scalar '+rootname+path,expected==x['value'])
   if x.get('uncertainty') is not None:
    match=re.search(r'(\d+(?:\.\d+)?)\((\d+)\)',raw)
    expect=int(match[2])*10**(-len(match[1].split('.')[1])) if '.' in match[1] else int(match[2])
    check('parenthetic uncertainty '+rootname+path,math.isclose(expect,x['uncertainty'],rel_tol=1e-12))
   if x.get('comparison'):check('comparison '+rootname+path,raw.startswith(x['comparison']))
for s in facts['stocks']:
 for v in s['components']:check('stock component '+s['id']+'/'+v,v in mid|sid)
for s in facts['sample_contexts']:check('no exact pair '+s['id'],s['verified_cross_technique_exact_pair'] is False)
for p in facts['protocols']:check('no exact protocol '+p['id'],p['exact_protocol_eligibility'] is False)
for fig in facts['figures']:check('figure asset '+fig['id'],fig['asset_id'] in aids)
pages={};replays=[]
for a in assets:
 key=(a['pdf_page'],a['render_scale'])
 if key not in pages:pages[key]=doc[key[0]-1].render(scale=key[1]).to_pil().convert('RGB')
 expected=pages[key].crop(a['pixel_bbox']);actual=Image.open(a['path']).convert('RGB')
 check('asset hash '+a['id'],sha(a['path'])==a['sha256'])
 match=expected.size==actual.size and expected.tobytes()==actual.tobytes()
 check('asset pixels '+a['id'],match)
 check('selected not complete page '+a['id'],a['contains_complete_source_page'] is False and actual.width*actual.height<pages[key].width*pages[key].height*.8)
 replays.append({'id':a['id'],'path':a['path'],'sha256':sha(a['path']),'pixel_match':match})
check('all20 selected',len(assets)==20)
check('facts64/quantities136',len(facts['facts'])==64 and sum(len(f['quantities']) for f in facts['facts'])==136)
check('ops31',sum(len(p['operations']) for p in facts['protocols'])==31)
check('refs65',len(facts['references'])==65)
check('literal optical expression',next(x for x in facts['equations'] if x['id']=='kubelka-munk')['expression']=='C/S = (1-R)^2 (2R)^x; x=1/2')
out={'reviewer':'/root/norberg2004_extract','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_freeze_sha256':sha(R/'package-freeze.json'),'checks':checks,'passed':sum(x['passed'] for x in checks),'failed':[x for x in checks if not x['passed']],'crop_replay':replays,'scope':'Mechanical source binding, typed-value and independently hand-read Table1 comparison; supports but does not replace full manual source and scientific review.'}
(A/'mechanical-checks-v1.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'checks':len(checks),'failed':out['failed']},ensure_ascii=False))
