"""Independent extraction checks; writes only this audit directory."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re,math
from PIL import Image
import pypdfium2 as pdfium
O=Path(__file__).resolve().parent;F=O.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
checks=[]
def ck(name,ok,detail=None):
 checks.append({'check':name,'passed':bool(ok),'detail':detail})
def ptr(j,p):
 for key in p.strip('/').split('/'):
  key=key.replace('~1','/').replace('~0','~');j=j[int(key)] if isinstance(j,list) else j[key]
 return j
def walk(j,p=''):
 yield p,j
 if isinstance(j,dict):
  for k,v in j.items():yield from walk(v,p+'/'+k)
 elif isinstance(j,list):
  for k,v in enumerate(j):yield from walk(v,p+'/'+str(k))
def norm(s):return ''.join(c.lower() for c in s if c.isalnum())
freeze=read(F/'package-freeze.json')
ck('exact author freeze',sha(F/'package-freeze.json')=='7599e47c1ef1d43d56b2f4f835e4b550a1ef652aecca2e9dd8e593abc5769c04')
bound={str(F/'package-freeze.json'):sha(F/'package-freeze.json'),str(Path(__file__)):sha(__file__)}
for name,entry in freeze['bound_files'].items():
 p=F/name;bound[str(p)]=sha(p);ck('author bound hash '+name,bound[str(p)]==entry['sha256']);ck('author bound size '+name,p.stat().st_size==entry['bytes'])
for name,h in freeze['source_files'].items():ck('original hash '+name,sha(name)==h);bound[name]=sha(name)
for name in ['independent-reading-checkpoint.json','independent-table-reading.json','independent-reading-notes.md']:
 bound[str(O/name)]=sha(O/name)
baseline=read(O/'independent-table-reading.json'); prior=read(O/'independent-reading-checkpoint.json')
ck('independent reading predates author freeze',prior['completed_at']<freeze['created_at'])
ck('independent reading was before author comparison',prior['author_extraction_opened'] is False)
ck('all33 independently read/viewed',sum(len(d['pages']) for d in prior['documents'])==33 and all(p['text_read'] and p['visual_review'] for d in prior['documents'] for p in d['pages']))
for d in prior['documents']:
 for p in d['pages']:
  ck('independent text hash '+p['text_path'],sha(p['text_path'])==p['text_sha256']);ck('independent native image hash '+p['image_path'],sha(p['image_path'])==p['image_sha256'])
data=read(F/'source-facts.json');tables=read(F/'source-tables.json');inv=read(F/'source-inventory.json');assets=read(F/'original-assets-manifest.json');coverage=read(F/'page-coverage.json')
loaded={'source-facts.json':data,'source-tables.json':tables,'source-inventory.json':inv}
expected_counts={'facts':65,'materials':39,'stocks':5,'protocols':16,'sample_contexts':62,'figures':44,'schemes':2,'equations':31,'references':56}
for k,n in expected_counts.items():ck('count '+k,len(data[k])==n);ck('unique '+k,len({x['id'] for x in data[k]})==n)
ck('34 source operations',sum(len(x['operations']) for x in data['protocols'])==34)
ck('10 stock components',sum(len(x['components']) for x in data['stocks'])==10)
ck('153 fact quantities',sum(len(x['quantities']) for x in data['facts'])==153)
ck('44 actual figure IDs',set(x['id'] for x in data['figures'])=={f'figure-{i}' for i in range(1,6)}|{f'figure-s{i}' for i in range(1,40)})
fact_ids={x['id'] for x in data['facts']};sample_ids={x['id'] for x in data['sample_contexts']};material_ids={x['id'] for x in data['materials']}
sources={d['role']:d['sha256'] for d in prior['documents']};pages={'main':8,'si':25}
for fn,j in loaded.items():
 for p,x in walk(j):
  if not isinstance(x,dict):continue
  if 'source_sha256' in x and 'pdf_page' in x:
   role=x.get('document_role');ck('source locator '+fn+p,role in sources and x['source_sha256']==sources[role] and isinstance(x['pdf_page'],int) and 1<=x['pdf_page']<=pages[role] and bool(x.get('locator')))
  for key,ids in [('source_fact_ids',fact_ids),('sample_context_ids',sample_ids)]:
   if key in x:ck('reference resolution '+fn+p+'/'+key,all(a in ids for a in x[key]),x[key])
for s in data['stocks']:
 for c in s['components']:ck('stock material '+s['id']+'/'+c['material_id'],c['material_id'] in material_ids)
for s in data['sample_contexts']:
 ck('no atomic model '+s['id'],s['atomic_structure_supplied'] is False)
 ck('batch limitation '+s['id'],bool(s['physical_batch_join']))
ck('inventory207 distinct',len(inv['units'])==207 and len({x['id'] for x in inv['units']})==207)
for u in inv['units']:
 ck('inventory evidence '+u['id'],bool(u['evidence']))
 for t in u['extraction_targets']:
  target=loaded.get(t['file']) or read(F/t['file'])
  ident=t.get('json_pointer') or t.get('asset_id') or t.get('private_payload_id')
  try:
   if 'json_pointer' in t:v=ptr(target,t['json_pointer']);ok=v is not None
   else:ok=any(isinstance(v,dict) and (v.get('id')==ident or v.get('payload_id')==ident) for _,v in walk(target))
  except (KeyError,IndexError,ValueError):ok=False
  ck('inventory target '+u['id']+ident,ok)
ck('page coverage33',len(coverage['pages'])==33 and len({(p['document_role'],p['pdf_page']) for p in coverage['pages']})==33)
for p in coverage['pages']:
 ck('page author payload hashes '+p['document_role']+str(p['pdf_page']),sha(p['text_path'])==p['text_sha256'] and sha(p['render_path'])==p['render_sha256'])
 ck('page full reading '+p['document_role']+str(p['pdf_page']),p['text_read'] and p['visual_review'])
 # Every advertised unit resolves; source bearing page coverage need not imply a scientific fact for every bibliography line.
 ck('page units resolve '+p['document_role']+str(p['pdf_page']),all(u in {x['id'] for x in inv['units']} for u in p['source_unit_ids']))
ts={t['id']:t for t in tables['tables']}
def compare_rows(tid,expected,raw=False):
 rows=ts[tid]['rows'];ck('table row count '+tid,len(rows)==len(expected))
 for i,(r,vs) in enumerate(zip(rows,expected)):
  ck(f'table cell count {tid}/{i}',len(r['cells'])==len(vs))
  for k,(c,v) in enumerate(zip(r['cells'],vs)):
   ck(f'independent table {tid}/{i}/{k}',c['raw_text']==v if raw else c['value']==float(v),{'author_raw':c['raw_text'],'independent':v})
compare_rows('table-1',baseline['main_table_1']['rows'])
compare_rows('table-s22',baseline['si_s22']['rows'],True)
compare_rows('scherrer-prose',[r[1:] for r in baseline['scherrer_printed_prose']['rows']],True)
compare_rows('gaussian-boxes',[r[2:] for r in baseline['scherrer_fit_boxes']['rows']],True)
fit_ids=['fit-s6-150','fit-s6-200','fit-s6-250','fit-s6-300','fit-s8-150','fit-s20-log','fit-s21-high','fit-s21-middle','fit-s21-low','fit-s21-inset','fit-s30-indium','fit-s31-indium','fit-s31-acid','fit-s32-low','fit-s32-middle','fit-s32-high','fit-s33','fit-s34-low','fit-s34-middle','fit-s34-high','fit-s36-low','fit-s36-middle','fit-s36-high']
fitrows={r['id']:r for r in ts['printed-linear-fits']['rows']}
for rid,ex in zip(fit_ids,baseline['printed_linear_fits']['rows']):
 for i,v in enumerate(ex[2:5]):ck('independent fit '+rid+'/'+str(i),fitrows[rid]['cells'][i]['raw_text']==v)
for i,v in enumerate(['0.00564','-0.00012','0.9904']):ck('main Figure5 fit '+str(i),fitrows['fit-figure5']['cells'][i]['raw_text']==v)
nmr=[['11.4','1'],['7.36–7.27','5'],['3.66','2','7.74'],['12.1','1'],['7.06–7.01','2'],['7.01–6.97','3'],['3.16','2','7.73'],['178.77'],['134.13','2.94'],['129.99','1.84'],['129.05'],['127.69'],['41.40','55.64']]
compare_rows('acid-nmr',nmr,True)
for r,m in zip(ts['acid-nmr']['rows'],['br s','overlapping m','d','br s','m','overlapping m','d','s','d','d','s','s','d']):ck('NMR multiplicity '+r['id'],r['multiplicity_raw']==m)
ck('185 typed table fields',sum(len(r['cells']) for t in tables['tables'] for r in t['rows'])==185)
for t in tables['tables']:
 for r in t['rows']:
  for c in r['cells']:
   ck('table numeric or explicit range '+r['id']+c['meaning'],c['value'] is not None or c['range'] is not None)
for r in ts['gaussian-boxes']['rows']:
 ck('source uncertainties remain blank '+r['id'],r['std_dev_raw']==['','',''] and all(c['uncertainty'] is None for c in r['cells']))
 ck('Gaussian expression '+r['id'],norm(r['raw_expression'])==norm(baseline['scherrer_fit_boxes']['formula']))
# Ref citations are compared against original PDF text that was separately read/viewed.
text='\n'.join(Path(d['pages'][i]['text_path']).read_text(encoding='utf8') for d in prior['documents'] if d['role']=='main' for i in [6,7])
for r in data['references']:ck('reference text original '+str(r['number']),norm(r['raw_citation']) in norm(text))
ck('reference numbers1-56',[r['number'] for r in data['references']]==list(range(1,57)))
# Actual source pixel replay, independent of author builders. No image is changed or written.
docs={role:pdfium.PdfDocument(d['source_path']) for role in ['main','si'] for d in prior['documents'] if d['role']==role};cache={}
for a in assets['assets']:
 key=(a['document_role'],a['pdf_page'],a['render_dpi'])
 if key not in cache:
  pg=docs[key[0]][key[1]-1];bm=pg.render(scale=key[2]/72);cache[key]=bm.to_pil().convert('RGB').copy();bm.close();pg.close()
 im=cache[key];actual=Image.open(a['path']).convert('RGB');crop=im.crop(tuple(a['crop_box_render_pixels']))
 ck('asset sourcehash '+a['id'],a['source_sha256']==sources[a['document_role']]);ck('asset exact hash '+a['id'],sha(a['path'])==a['sha256']);ck('asset source crop pixels '+a['id'],actual.size==crop.size and actual.tobytes()==crop.tobytes())
 ck('asset selected extent '+a['id'],actual.width<im.width or actual.height<im.height)
for d in docs.values():d.close()
for name,h in freeze['source_files'].items():ck('original unchanged after replay '+name,sha(name)==h)
ck('51 selected crops',len(assets['assets'])==51)
for fn,expected in [('source-facts.json','05c25ab87ba032c8006c86e4fe07c719a5348bebec22a2e3daf00dbf5993b192'),('package-freeze.json','7599e47c1ef1d43d56b2f4f835e4b550a1ef652aecca2e9dd8e593abc5769c04')]:ck('author still frozen '+fn,sha(F/fn)==expected)
result={'schema':'mattersyn-independent-source-mechanical-checks/1','source_id':'friedfeld2019','author':'/root/peng1998_reader_assets','reviewer':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'executed_checks':len(checks),'passed_checks':sum(x['passed'] for x in checks),'failed_checks':[x for x in checks if not x['passed']],'checks':checks,'bound_files':bound,'scope_note':'Mechanical validation supplements actual33-page reading and all51 crop views. Known scientific locator/typing/mapping findings are recorded separately; passing these checks alone is not approval.'}
(O/'mechanical-checks-v1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:result[k] for k in ['executed_checks','passed_checks','failed_checks']},ensure_ascii=False))
