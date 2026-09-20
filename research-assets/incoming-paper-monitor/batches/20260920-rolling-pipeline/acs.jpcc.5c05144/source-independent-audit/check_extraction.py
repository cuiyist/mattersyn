import json,hashlib,re,datetime
from pathlib import Path
from PIL import Image,ImageChops
import pypdfium2 as pdf
O=Path(__file__).parent;P=O.parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[]
def ck(label,ok,detail=None):checks.append({'check':label,'pass':bool(ok),**({'detail':detail} if detail is not None else {})})
F=read(P/'source-facts.json');T=read(P/'source-tables.json');I=read(P/'source-inventory.json');A=read(P/'original-assets-manifest.json');C=read(P/'page-coverage.json');Z=read(P/'package-freeze.json');B=read(O/'independent-numeric-reading.json');R=read(O/'independent-reading-checkpoint.json')
ck('requested author freeze',sha(P/'package-freeze.json')=='c4e1c1cdd065b46e16f1b2fec288a998dec8c5c0fc0867c8e6e902c6242eda08')
for n,d in Z['bound_files'].items():ck('frozen file '+n,sha(P/n)==d['sha256'])
files={x['role_candidate']:x for x in R['paper']['file_copies']}
for role,s in files.items():ck('original '+role,sha(s['source_path'])==s['sha256'])
for role,n in [('main',9),('si',11)]:
 ck('complete page coverage '+role,sorted(p['pdf_page'] for p in C['pages'] if p['document_role']==role)==list(range(1,n+1)))
for p in C['pages']:
 for k in ['text','render']:ck('page cache '+p['document_role']+str(p['pdf_page'])+k,sha(p[k+'_path'])==p[k+'_sha256'])
 ck('page authored read/view '+p['document_role']+str(p['pdf_page']),p['text_read'] and p['visual_review'])
facts={f['id']:f for f in F['facts']};samples={x['id']:x for x in F['sample_contexts']};tables={t['id']:t for t in T['tables']}
for k in ['facts','materials','stocks','protocols','sample_contexts','figures','schemes','equations','references','conflicts','missingness']:
 ck('unique IDs '+k,len({v['id'] for v in F[k]})==len(F[k]))
ck('unit mirror',I['units']==I['semantic_units'])
ck('unique unit IDs',len({u['id'] for u in I['units']})==157)
def ptr(obj,path):
 for key in path.lstrip('/').split('/'):
  key=key.replace('~1','/').replace('~0','~');obj=obj[int(key)] if isinstance(obj,list) else obj[key]
 return obj
cache={'source-facts.json':F,'source-tables.json':T}
for u in I['units']:
 for target in u['extraction_targets']:
  f=target['file'];cache.setdefault(f,read(P/f))
  if 'json_pointer' in target:value=ptr(cache[f],target['json_pointer']);ok=value is not None
  elif 'asset_id' in target:ok=any(a['id']==target['asset_id'] for a in A['assets'])
  else:ok=target['private_payload_id'] in json.dumps(cache[f])
  ck('inventory target '+u['id'],ok)
def walk(v,path=''):
 if isinstance(v,dict):
  if {'source_sha256','pdf_page','document_role'}<=v.keys():
   role=v['document_role'];ck('source locator '+path,role in files and v['source_sha256']==files[role]['sha256'] and 1<=v['pdf_page']<=(9 if role=='main' else 11))
  if 'source_fact_ids' in v:
   for fid in v['source_fact_ids']:ck('fact link '+path+' '+fid,fid in facts)
  if 'sample_context_ids' in v:
   for sid in v['sample_context_ids']:ck('sample link '+path+' '+sid,sid in samples)
  if 'conflict_ids' in v:
   for cid in v['conflict_ids']:ck('conflict link '+path+' '+cid,cid in {x['id'] for x in F['conflicts']})
  if 'gap_ids' in v:
   for gid in v['gap_ids']:ck('gap link '+path+' '+gid,gid in {x['id'] for x in F['missingness']})
  for k,x in v.items():walk(x,path+'/'+k)
 elif isinstance(v,list):
  for j,x in enumerate(v):walk(x,path+'/'+str(j))
for name,data in [('facts',F),('tables',T),('inventory',I)]:walk(data,name)
for tid,bid in [('ligand-numeric','figure1_rows'),('wash-numeric','figure2_rows')]:
 for r,expected in zip(tables[tid]['rows'],B[bid]):
  parts=list(map(int,expected[0].split(':')));vals=parts+expected[1:]
  for j,(c,v) in enumerate(zip(r['cells'],vals)):ck('independent numeric '+tid+'/'+r['id']+'/'+str(j),c['value']==v)
  ck('ratio sample '+r['id'],r['sample_context'] in samples)
for r,expected in zip(tables['growth-numeric']['rows'],B['figure3_rows']):
 vals=[expected[0],expected[1],expected[3],expected[4],20]
 for j,(c,v) in enumerate(zip(r['cells'],vals)):ck('independent growth cell '+r['id']+'/'+str(j),c['value']==v)
 ck('growth printed uncertainty '+r['id'],r['cells'][1]['uncertainty']['value']==expected[2] and 'unreported' in r['cells'][1]['uncertainty']['kind'])
 ck('growth approximate lifetime '+r['id'],r['cells'][3]['approximate'])
for r,b in zip(tables['pl-slopes']['rows'],B['temperature_slopes_rows']):
 for j in [1,2]:ck('slope '+r['id']+str(j),r['cells'][j]['value']==b[j])
expected_cells=[[8.88,8.88,6.28],[8.92,8.92,6.33],[6.36,6.36,6.36]]
for r,ex in zip(tables['reference-cells']['rows'],expected_cells):
 ck('reference cell scope '+r['id'],r['sample_context'].endswith('-reference'))
 for j,(c,v) in enumerate(zip(r['cells'],ex)):ck('cited cell '+r['id']+str(j),c['value']==v)
for r,b in zip(tables['table-s1']['rows'],B['table_s1_rows']):
 ck('S1 row '+r['id'],r['cells'][0]['value']==b[0]);ck('S1 gamma beta '+r['id'],r['cells'][2]['value']==b[2]);c=r['cells'][3]
 if b[3] is None:ck('S1 missing '+r['id'],c['value'] is None and c['status']=='missing' and c['raw_text']=='')
 elif isinstance(b[3],str):ck('S1 range '+r['id'],c['range']=={'min':260,'max':280} and c['value'] is None)
 else:ck('S1 beta alpha '+r['id'],c['value']==b[3])
 ck('S1 citation '+r['id'],r.get('reference_id')==('si-reference-'+str(b[4]) if b[4] else None))
 ck('S1 sample scope '+r['id'],samples[r['sample_context']]['kind']==('literature_context' if b[0]<11 else 'current_study_summary'))
 # Semantic sample/method text was independently manually compared to all native row cells.
ck('121 table body cells',sum(len(r['cells']) for t in T['tables'] for r in t['rows'])==121)
ck('100 fact quantities',sum(len(f['quantities']) for f in F['facts'])==100)
for st in F['stocks']:
 ck('unknown stock final concentration '+st['id'],st['concentration'] is None and st['final_volume'] is None)
 for co in st['components']:ck('stock component identity '+st['id']+'/'+co['material_id'],co['material_id'] in {m['id'] for m in F['materials']})
ck('FA stock transfer separate',F['stocks'][0]['subsequent_transfer'][0]['value']==.51 and F['stocks'][0]['components'][0]['amount_quantities'][0]['value']==.1042)
ops=[o for p in F['protocols'] for o in p['operations']]
for o in ops:
 # Duplicated stage quantities must agree with at least one supporting fact quantity exactly.
 for q in o['quantities']:
  core=lambda d:{k:v for k,v in d.items() if k!='evidence'}
  ck('operation quantity inheritance '+o['id']+'/'+q['meaning'],any(core(q)==core(fq) and all(e in fq['evidence'] for e in q['evidence']) for fid in o['source_fact_ids'] for fq in facts[fid]['quantities']))
ck('first retained fraction',next(o for o in ops if o['id']=='first-spin')['retained_fraction']=='first precipitate')
ck('second retained fraction',next(o for o in ops if o['id']=='second-spin')['retained_fraction']=='supernatant')
for role,total in [('main',74),('si',15)]:
 refs=[x for x in F['references'] if x['document_role']==role];ck('reference numbering '+role,[x['number'] for x in refs]==list(range(1,total+1)))
 # Whitespace-insensitive exact source text matching catches missing continuation/footer contamination.
 text=''.join((O/'source-render'/f'{role}-{i:02}.txt').read_text(encoding='utf-8-sig') for i in range(1,(9 if role=='main' else 11)+1))
 norm=lambda v:re.sub(r'\s+','',v).replace('\ufffe','-')
 for ref in refs:ck('reference source text '+ref['id'],norm(ref['raw_citation']) in norm(text))
docs={role:pdf.PdfDocument(f['source_path']) for role,f in files.items()};renders={}
for a in A['assets']:
 key=(a['document_role'],a['pdf_page'],a['render_dpi'])
 if key not in renders:renders[key]=docs[key[0]][key[1]-1].render(scale=key[2]/72).to_pil().convert('RGB')
 im=renders[key];crop=im.crop(a['crop_box_render_pixels']);actual=Image.open(a['path']).convert('RGB')
 ck('crop pixel replay '+a['object_id'],crop.size==actual.size and ImageChops.difference(crop,actual).getbbox() is None)
 ck('crop hash '+a['object_id'],sha(a['path'])==a['sha256'])
 ck('selected excerpt '+a['object_id'],not a['contains_complete_source_page'] and crop.size!=im.size)
ck('training pending',F['training_eligibility'] is False)
ck('independent source stage only',F['independent_audit_status']=='pending')
rr=facts['sasongko2025-raman-range'];displayed=next(q for q in rr['quantities'] if q['meaning']=='displayed temperature interval')
ck('SAS-SRC-01 exact Figure S2 caption locator on range claim',any(e['document_role']=='si' and e['pdf_page']==5 for e in rr['evidence']))
ck('SAS-SRC-01 exact Figure S2 caption locator on displayed range',any(e['document_role']=='si' and e['pdf_page']==5 for e in displayed['evidence']))
result={'author':'/root/peng1998_reader_assets','auditor':'/root/backlog_eta','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'summary':{'total':len(checks),'passed':sum(x['pass'] for x in checks),'failed':[x for x in checks if not x['pass']]},'manual_scope_note':'Checks support, but do not replace, actual independent all20page/all17crop viewing and complete scientific comparison. No curve digitization/external reference retrieval.'}
(O/'comparison-checks-v1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result['summary'],ensure_ascii=False,indent=2))
