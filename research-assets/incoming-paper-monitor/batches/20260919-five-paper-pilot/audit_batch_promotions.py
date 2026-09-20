"""Root independent review of worker-authored metadata promotion and task views."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import hashlib,json,sys,types
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record,eligibility,training_view,build_groups
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
tasks={
 'la036034c':{'nagasaki-2004-cho-cds':['precursor_selection','partial_protocol'],'nagasaki-2004-biotin-cds':['precursor_selection','partial_protocol'],**{x:['partial_protocol'] for x in ['nagasaki-2004-polymer-preparation','nagasaki-2004-aldehyde-polymer','nagasaki-2004-biotin-polymer']}},
 'jp0473669':{'ribeiro-2004-hydrolysis':['precursor_selection','partial_protocol']},
 'ja048427j':{'norberg-2004-hydrolysis':['precursor_selection','partial_protocol'],**{x:['partial_protocol'] for x in ['norberg-2004-amine-cleaning','norberg-2004-films-a-c','norberg-2004-surface-control']}}
}
allrecords=[]
for folder,expected_tasks in tasks.items():
 P=B/folder;manifest=read(P/'promotion-proposal/promotion-manifest.json');checks=[];bound={}
 def check(label,value):
  checks.append({'check':label,'passed':bool(value)})
  assert value,(folder,label)
 def bind(p,h=None):
  p=Path(p);v=sha(p);bound[str(p)]=v
  if h:check('Bound hash '+str(p),v==h)
  return v
 bind(P/'promotion-proposal/promotion-manifest.json')
 for p,h in manifest['bound_inputs'].items():bind(p,h)
 audit=read(P/'canonical-records-audit.json');check('Independent canonical audit passed',audit['status'].startswith('passed'))
 originals=[];records=[];views=[];decisions=[]
 for item in manifest['records']:
  rid=item['record_id'];a=P/'canonical-drafts'/(rid+'.json');b=P/'promotion-proposal'/item['proposal_path']
  bind(a,item['source_sha256']);bind(b,item['proposal_sha256']);check(rid+' previously audited canonical bytes',sha(a)==audit['record_hashes'][rid])
  old=read(a);new=read(b);restored=deepcopy(new)
  if 'collection' in old:restored['collection']=old['collection']
  else:restored.pop('collection',None)
  for key in ['review_status','review_scope','requested_tasks']:restored['quality'][key]=old['quality'][key]
  restored['sources'][0]['main_status']=old['sources'][0]['main_status']
  check(rid+' all scientific fields exactly unchanged',old==restored)
  check(rid+' schema/lineage/evidence',not validate_record(new))
  check(rid+' expected promotion',new['collection']=='reviewed_literature' and new['quality']['review_status']=='source_reviewed')
  check(rid+' primary-source SI scope preserved',new['sources'][0]['si_status']==old['sources'][0]['si_status'])
  check(rid+' independently selected task set',new['quality']['requested_tasks']==expected_tasks.get(rid,[]))
  check(rid+' complete task gate',{t for t,g in eligibility(new).items() if g['eligible']}==set(expected_tasks.get(rid,[])))
  for task in expected_tasks.get(rid,[]):
   v=training_view(new,task);views.append(v)
   check(rid+'/'+task+' input excludes observed outcomes and figures',set(v['input'])<={'composition','method','requested_surface','requested_host'})
   if task=='partial_protocol':
    ops=v['output']['operations'];ids={o['id'] for o in ops}
    check(rid+' preparative operations and dependency closure',bool(ops) and all(set(o['depends_on'])<=ids for o in ops))
    check(rid+' exact source gaps retained',v['output']['missing_fields']==old['quality']['missing_fields'] and bool(v['output']['missing_fields']))
    decisions.append({'record_id':rid,'tasks':expected_tasks[rid],'operations':[{'id':o['id'],'stage':o['stage'],'label':o['label'],'description':o['description']} for o in ops]})
   if rid=='norberg-2004-hydrolysis' and task=='precursor_selection':
    check('Zn host and Mn dopant both included',{x['role'] for x in v['output']['precursors']}=={'host_precursor','dopant_precursor'} and len(v['output']['precursors'])==2)
  originals.append(old);records.append(new)
 preview=read(P/'promotion-proposal/training-export-preview.json');bind(P/'promotion-proposal/training-export-preview.json',manifest['training_export_preview_sha256'])
 check('Exact recomputed export rows',views==preview['exports'])
 check('One unchanged source group',build_groups(records)==build_groups(originals) and len(set(build_groups(records).values()))==1)
 allrecords+=records
 result={'status':'passed_metadata_and_task_scope','auditor':'/root','author':'/root/backlog_eta','at':datetime.now(timezone.utc).isoformat(),'scope':'Independent comparison with frozen and previously independently audited canonical source records. Only five review metadata fields changed. Conservative requested tasks reviewed by source procedure scope; this is not a re-audit of original numerical extraction or approval of browser integration.','checks':checks,'bound_files':bound,'open_findings':[],'task_decisions':decisions,'records':len(records),'exports':len(views),'exact_structure_pairs':0}
 save(P/'promotion-source-audit.json',result)
 print(json.dumps({'paper':folder,'checks':len(checks),'decisions':decisions},ensure_ascii=False))
assert len(allrecords)==46 and len(set(build_groups(allrecords).values()))==3
# The two newly supported precursor roles must not change any of the 424 public baseline examples.
path=S/'scripts/dataset_lib.py';code=path.read_text(encoding='utf8');oldmod=types.ModuleType('prior_dataset_lib');oldmod.__file__=str(path)
exec(compile(code.replace("'metal_precursor','host_precursor','dopant_precursor'","'metal_precursor'"),str(path),'exec'),oldmod.__dict__)
base=read(B/'integration-proposal/base-record-hashes.json');checks=[]
for name,h in base.items():
 p=S/'data/records'/name;assert sha(p)==h;r=read(p);assert oldmod.eligibility(r)==eligibility(r)
 for task,g in eligibility(r).items():
  if g['eligible']:assert oldmod.training_view(r,task)==training_view(r,task)
 checks.append(name)
save(B/'integration-proposal/training-gate-regression.json',{'status':'passed','baseline_records_unchanged':len(checks),'baseline_task_views_unchanged':True,'new_host_dopant_gate_source_sha256':sha(path),'new_source_groups':3,'new_records':46,'exact_structure_pairs_added':0})
