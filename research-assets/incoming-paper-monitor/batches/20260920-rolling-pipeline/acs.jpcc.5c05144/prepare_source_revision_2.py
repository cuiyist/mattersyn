from pathlib import Path
from copy import deepcopy
import json,hashlib,datetime
F=Path(__file__).resolve().parent;O=F/'source-extraction-revision-2'
assert not (O/'package-freeze.json').exists(),'Immutable revision already frozen'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
base=read(F/'package-freeze.json');assert sha(F/'package-freeze.json')=='c4e1c1cdd065b46e16f1b2fec288a998dec8c5c0fc0867c8e6e902c6242eda08'
original={str(F/'package-freeze.json'):sha(F/'package-freeze.json')}
for p,h in base['bound_files'].items():
 fp=F/p;assert sha(fp)==h['sha256'];original[str(fp)]=sha(fp)
for p,h in base['source_files'].items():assert sha(p)==h;original[p]=h
ev={'source_id':'sasongko2025-si','document_role':'si','source_sha256':base['source_files'][next(k for k in base['source_files'] if k.endswith('_si_1.pdf'))],'pdf_page':5,'printed_page':'S5','locator':'Figure S2 caption: temperature-dependent Raman spectra measured from 80 to 190 K'}
uid='sasongko2025-unit-sasongko2025-raman-range';changes=[]
def visit(x,p='',filename=''):
 if isinstance(x,dict):
  target=x.get('id') in ['sasongko2025-raman-range',uid] or (x.get('raw_text')=='80–190' and x.get('meaning')=='displayed temperature interval') or ('sasongko2025-raman-range' in x.get('source_fact_ids',[]) and 'Raman prose says' in x.get('description',''))
  if target and 'evidence' in x and ev not in x['evidence']:
   changes.append({'file':filename,'pointer':p+'/evidence/'+str(len(x['evidence'])),'operation':'add','value':deepcopy(ev)});x['evidence'].append(deepcopy(ev))
  if x.get('id')==uid and 'sasongko2025-si-p05' not in x['source_payload_ids']:
   changes.append({'file':filename,'pointer':p+'/source_payload_ids/'+str(len(x['source_payload_ids'])),'operation':'add','value':'sasongko2025-si-p05'});x['source_payload_ids'].append('sasongko2025-si-p05')
  for k,v in list(x.items()):visit(v,p+'/'+k,filename)
 elif isinstance(x,list):
  for i,v in enumerate(x):visit(v,p+'/'+str(i),filename)
O.mkdir(exist_ok=True)
for n in ['source-facts.json','source-inventory.json']:
 x=read(F/n);visit(x,filename=n);save(n,x)
x=read(F/'page-coverage.json');row=next(p for p in x['pages'] if p['document_role']=='si' and p['pdf_page']==5)
if uid not in row['source_unit_ids']:
 idx=x['pages'].index(row);changes.append({'file':'page-coverage.json','pointer':f'/pages/{idx}/source_unit_ids/{len(row["source_unit_ids"])}','operation':'add','value':uid});row['source_unit_ids'].append(uid)
save('page-coverage.json',x)
def remove_at(x,p):
 parts=p.strip('/').split('/')
 for k in parts[:-1]:x=x[int(k)] if isinstance(x,list) else x[k]
 if isinstance(x,list):x.pop(int(parts[-1]))
 else:del x[parts[-1]]
for n in ['source-facts.json','source-inventory.json','page-coverage.json']:
 x=read(O/n)
 for ch in reversed(changes):
  if ch['file']==n:remove_at(x,ch['pointer'])
 assert x==read(F/n),n+' science invariance'
for p,h in original.items():assert sha(p)==h
history={'schema':'mattersyn-source-correction/1','finding_id':'SAS-SRC-01','reason':'Add exact SI PDF5/printed S5 Figure S2 caption to displayed 80–190 K evidence while retaining PDF6 prose and PDF4 instrument locators.','author':'peng1998_reader_assets','original_freeze_path':str(F/'package-freeze.json'),'original_freeze_sha256':sha(F/'package-freeze.json'),'original_files_unchanged':original,'actual_visual_scope':{'path':str(F/'source-render/si-05.png'),'sha256':sha(F/'source-render/si-05.png'),'inspection':'Original full page visually re-opened; Figure S2 caption explicitly says measured from 80 to 190 K.'},'changes':changes,'validation':{'reverse_delta_restores_original_structures':True,'all_original_files_hash_unchanged':True,'numeric_values_units_raw_tokens_sample_assignments_tables_and_crops_unchanged':True},'independent_audit':'pending distinct backlog_eta delta audit'}
save('source-correction-history.json',history)
effective={n:{'path':str(O/n),'sha256':sha(O/n)} for n in ['source-facts.json','source-inventory.json','page-coverage.json']}
save('effective-file-map.json',{'base_freeze':{'path':str(F/'package-freeze.json'),'sha256':sha(F/'package-freeze.json')},'replacements':effective,'all_other_files':'Exact original paths/bytes; no wholesale re-extraction or source mutation.'})
bound={str(F/'package-freeze.json'):sha(F/'package-freeze.json'),str(Path(__file__).resolve()):sha(__file__),str(F/'source-independent-audit/independent-audit-v1.json'):sha(F/'source-independent-audit/independent-audit-v1.json'),**original}
for p in O.iterdir():
 if p.is_file():bound[str(p)]=sha(p)
save('package-freeze.json',{'schema':'mattersyn-source-extraction-overlay-freeze/1','source_id':'sasongko2025','revision':2,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'immutable_author_overlay_pending_independent_audit','source_generation':1,'base_freeze_sha256':sha(F/'package-freeze.json'),'effective_files':effective,'bound_files':bound,'change_count':len(changes),'claims':'Only added exact evidence, semantic page linkage and page coverage. All original files preserved.'})
print(json.dumps({'freeze':sha(O/'package-freeze.json'),'changes':len(changes),'files':len(bound),'facts':sha(O/'source-facts.json')}))
