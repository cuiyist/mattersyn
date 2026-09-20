from pathlib import Path
import sys,json,hashlib,re,math
from datetime import datetime,timezone
A=Path(__file__).resolve().parent;G=A.parent;M=G.parents[4]
sys.path.insert(0,str(M/'research-assets/corpus-20260917/runtime'))
sys.path.insert(0,str(M/'research-assets/rdkit-runtime'))
sys.path.append('[local path redacted]')
import pypdfium2
from PIL import Image
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[]
def check(label,test):checks.append({'check':label,'passed':bool(test)})
freeze=load(G/'package-freeze.json');f=load(G/'source-facts.json');tables=load(G/'source-tables.json')['tables'];assets=load(G/'original-assets-manifest.json')['assets'];inv=load(G/'source-inventory.json')['inventory_units'];reading=load(A/'independent-table-reading.json')
for p,h in freeze['bound_files'].items():check('frozen hash '+p,Path(p).is_file() and sha(p)==h)
ident=load(G/'intake-identity.json');docs={}
for x in ident['documents']:
 check('source hash '+x['role'],sha(x['source_path'])==x['sha256']);docs[x['role']]=pypdfium2.PdfDocument(x['source_path']);check('page count '+x['role'],len(docs[x['role']])==x['page_count'])
pages={};crop_replay=[]
for x in assets:
 k=(x['source_role'],x['pdf_page'])
 if k not in pages:
  bitmap=docs[k[0]][k[1]-1].render(scale=x['render_scale'])
  pages[k]=bitmap.to_pil().convert('RGB')
 ref=pages[k].crop(x['bbox_pixels_at_render']);actual=Image.open(x['path']).convert('RGB')
 check('asset bytes '+x['id'],sha(x['path'])==x['sha256'])
 check('asset exact pixels '+x['id'],ref.size==actual.size and ref.tobytes()==actual.tobytes())
 check('asset selected only '+x['id'],x['whole_source_page'] is False and ref.width*ref.height<pages[k].width*pages[k].height*.8)
 crop_replay.append({'id':x['id'],'path':x['path'],'sha256':sha(x['path']),'source_role':k[0],'pdf_page':k[1],'bbox':x['bbox_pixels_at_render'],'pixel_match':ref.size==actual.size and ref.tobytes()==actual.tobytes()})
 if x['id'] in ['figure-1','figure-s4']:
  x0,y0,x1,y1=x['bbox_pixels_at_render'];expanded=pages[k].crop((x0,y0,min(x1+90,pages[k].width),y1));out=A/(x['id']+'-independent-right-padding.png');expanded.save(out)
ids={x['id'] for x in f['facts']};samples={x['id'] for x in f['samples']};aids={x['id'] for x in assets};conf={x['id'] for x in f['conflicts']};gaps={x['id'] for x in f['gaps']}
check('inventory IDs unique',len(inv)==len({x['id'] for x in inv}))
def pointer(obj,p):
 for k in p.lstrip('/').split('/'):
  k=k.replace('~1','/').replace('~0','~');obj=obj[int(k)] if isinstance(obj,list) else obj[k]
 return obj
for u in inv:
 try:obj=pointer(f,u['json_pointer']);valid=obj.get('id')==u['source_object_id']
 except (KeyError,ValueError,TypeError):valid=False
 check('unit pointer '+u['id'],valid)
for x in f['facts']:
 check('fact sample '+x['id'],x['sample_scope'] in samples)
 for q in x.get('quantities',[]):
  check('quantity evidence '+x['id']+' '+str(q.get('meaning')),bool(q.get('evidence')))
for x in f['samples']:check('sample identity not invented '+x['id'],x['physical_sample_identity_verified'] is False)
def walk(x,path=''):
 if isinstance(x,list):
  for i,v in enumerate(x):yield from walk(v,path+'/'+str(i))
 elif isinstance(x,dict):
  yield path,x
  for k,v in x.items():yield from walk(v,path+'/'+k)
for path,x in walk(f):
 for k,universe in [('source_fact_ids',ids),('source_context_ids',samples),('conflict_ids',conf),('gap_ids',gaps),('asset_ids',aids)]:
  for v in x.get(k,[]):check(path+'/'+k+'/'+v,v in universe)
 if 'document_role' in x and 'pdf_page' in x:
  role=x['document_role'];check('source locator '+path,role in docs and 1<=x['pdf_page']<=len(docs[role]) and x.get('source_sha256')==next(z['sha256'] for z in ident['documents'] if z['role']==role))
for t in tables:
 for r in t['rows']:
  for c in r['cells']:
   check('cell evidence '+c['id'],bool(c.get('evidence')))
   raw=c.get('raw_text','')
   if c.get('value') is not None:
    nums=re.findall(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?',raw)
    check('typed number '+c['id'],bool(nums) and float(nums[0])==c['value'])
   if raw.startswith('~') and c.get('value') is not None:check('approximation '+c['id'],c.get('approximate') is True)
   if c.get('comparison'):check('bound '+c['id'],raw.startswith(c['comparison']))
   if c.get('components'):check('ratio '+c['id'],[float(v) for v in raw.lstrip('~').split(':')]==c['components'])
   if c.get('asset_id'):check('image cell '+c['id'],c['asset_id'] in aids)
def normalize(s):return re.sub(r'\s+','',str(s)).lower().replace('−','-').replace('–','-').replace('≈','~').replace('mis-shapen','misshapen')
by={x['id']:x for x in tables}
for tid,rkey in [('table-1','table1'),('table-2','table2'),('table-3','table3'),('table-s1','table_s1')]:
 if rkey not in reading:continue
 expect=reading[rkey]['raw_rows'];actual=by[tid]['rows'];check(tid+' row count independent',len(expect)==len(actual))
 for i,(rr,ar) in enumerate(zip(expect,actual)):
  for j,raw in enumerate(rr):
   c=ar['cells'][j];value=c['raw_text']+(' '+c['unit'] if tid=='table-1' and j<2 else '')
   check(tid+f' independent token {i+1}/{j+1}',normalize(raw)==normalize(value))
for rr,ar in zip(reading['figure_s2_table']['raw_rows'],by['table-s2-inset']['rows']):
 label=ar['row_label'].replace('nu','n').replace('delta','d').replace('_','')
 check('OA table assignment '+ar['row_label'],normalize(rr[0])==normalize(label))
 value=ar['cells'][0]['raw_text']+(' ('+ar['qualifier']+')' if ar.get('qualifier')=='v. weak' else '')
 check('OA table value '+ar['row_label'],normalize(rr[1])==normalize(value))
check('table copies identical',f['tables']==tables)
check('original source generation',freeze['source_generation']==2 and freeze['bundle_sha256']==ident['bundle_sha256'])
check('page coverage is all19',[(x['document_role'],x['pdf_page']) for x in load(G/'page-coverage.json')['pages']]==[('main',n) for n in range(1,11)]+[('si',n) for n in range(1,10)])
check('facts194quantities',sum(len(x.get('quantities',[])) for x in f['facts'])==194)
check('alltablecells272',sum(len(r['cells']) for t in tables for r in t['rows'])==272)
check('source inputs4copies',len(load(G/'complete-source-payloads.json')['source_copies'])==4)
for x in load(G/'complete-source-payloads.json')['source_copies']:check('originalcopy '+x['source_path'],sha(x['source_path'])==x['sha256'])
save(A/'mechanical-checks-v1.json',{'reviewer':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'freeze_sha256':sha(G/'package-freeze.json'),'checks':checks,'passed':sum(x['passed'] for x in checks),'failed':[x for x in checks if not x['passed']],'crop_replay':crop_replay,'reading_keys':list(reading),'facts_keys':list(f)})
print(json.dumps({'checks':len(checks),'failed':[x for x in checks if not x['passed']],'reading_keys':list(reading),'facts_keys':list(f)},ensure_ascii=False))
