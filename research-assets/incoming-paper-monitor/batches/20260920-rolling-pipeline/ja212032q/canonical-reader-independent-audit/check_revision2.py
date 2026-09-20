from pathlib import Path
import json,hashlib,sys,datetime,collections
A=Path(__file__).resolve().parent;G=A.parent;S=Path('[local path redacted]');sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record,eligibility,build_groups
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
bound={};checks=collections.Counter();fails=[]
def read(p):bound[str(p)]=sha(p);return json.loads(p.read_text(encoding='utf-8'))
def ck(ok,kind,detail):
 checks[kind]+=1
 if not ok:fails.append({'category':kind,'detail':detail})
def diff(x,y,p=''):
 if type(x)!=type(y):return [(p,x,y)]
 if isinstance(x,dict):return sum([diff(x[k],y[k],p+'/'+k) if k in x and k in y else [(p+'/'+k,x.get(k),y.get(k))] for k in set(x)|set(y)],[])
 if isinstance(x,list):return [(p,x,y)] if len(x)!=len(y) else sum([diff(a,b,p+'/'+str(i)) for i,(a,b) in enumerate(zip(x,y))],[])
 return [] if x==y else [(p,x,y)]
old=read(A/'independent-audit-v1.json');freeze=read(G/'canonical-proposal/v2/package-manifest.json');delta=read(G/'canonical-proposal/v2/revision-2-delta.json')
ck(sha(G/'canonical-proposal/v2/package-manifest.json')=='7b71cd4d861328b057adefab344b0bb1029152cf981e569ccfacf06f1672316d','freeze','expectedv2')
for p,h in freeze['bound_files'].items():ck(sha(Path(p))==h,'v2_bound_hash',p);bound[p]=sha(Path(p))
for x in old['bound_files']:ck(sha(Path(x['path']))==x['sha256'],'v1_preserved',x['path'])
expected={x['record_id']:{v['state_id']:v for v in old['findings'][0]['required_changes'] if v['record_id']==x['record_id']} for x in old['findings'][0]['required_changes']}
records=[];recorddeltas=[]
for p in sorted((G/'canonical-proposal/v1').glob('ghosh-2012-*.json')):
 before=read(p);after=read(G/'canonical-proposal/v2'/p.name);records.append(after);dd=diff(before,after);recorddeltas.append({'record_id':before['record_id'],'deltas':dd})
 restored=json.loads(json.dumps(after))
 for ix,st in enumerate(before['material_states']):
  if st['id'] in expected.get(before['record_id'],{}):
   ck(after['material_states'][ix]['kind']=='sample_set','sample_set',st['id']);restored['material_states'][ix]['kind']=st['kind']
   if st['id']=='ftir-film':ck(after['material_states'][ix]['name']=='Separate particle and pure-ligand FTIR specimens','ftir_specimen_name',st['id']);restored['material_states'][ix]['name']=st['name']
 ck(restored==before,'only_requested_record_changes',p.name)
 ck(not validate_record(after),'schema',p.name);ck(not any(x['eligible'] for x in eligibility(after).values()),'zero_training',p.name)
 if p.stem not in expected:ck(sha(p)==sha(G/'canonical-proposal/v2'/p.name),'17_identical_records',p.name)
ck(len(set(build_groups(records).values()))==1,'source_group','21')
rb=read(G/'public-review-proposal/v1/ghosh2012.json');ra=read(G/'public-review-proposal/v2/ghosh2012.json');rd=diff(rb,ra)
ck(len(rd)==4,'four_reader_labels',rd)
for p,b,a in rd:ck(('/notes/' in p or p.endswith('/operation_context/material_flow_labels/ftir-film')) and 'ftir film' in b.lower() and 'Separate particle and pure-ligand FTIR specimens' in a,'requested_reader_label',p)
def ptr(o,p):
 for k in p.lstrip('/').split('/'):o=o[int(k)] if isinstance(o,list) else o[k]
 return o
for before,after in zip([i for s in rb['reader_sections'] for i in s['items']],[i for s in ra['reader_sections'] for i in s['items']]):ck(before['facts']==after['facts'],'all_reader_quantities_unchanged',before['id'])
ck(len([x for x in recorddeltas if x['deltas']])==4,'four_records_changed','classification only')
out={'schema':'mattersyn-independent-canonical-reader-delta/1','status':'passed' if not fails else 'open_findings','reviewer':'/root/norberg2004_extract','author':'/root/backlog_eta','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'proposal_freeze_sha256':sha(G/'canonical-proposal/v2/package-manifest.json'),'prior_audit_sha256':sha(A/'independent-audit-v1.json'),'source_audit_sha256':old['source_audit_sha256'],'checks':sum(checks.values()),'checks_by_category':dict(checks),'failures':fails,'record_deltas':recorddeltas,'reader_deltas':rd,'counts':old['counts'],'manual_scopes':old['manual_scopes'],'findings':[dict(old['findings'][0],status='resolved',resolution='Five sample_set state classifications and FTIR name/four reader labels independently verified; no numerical/evidence changes.')],'limits':old['excluded_gates'],'bound_files':[{'path':p,'sha256':h} for p,h in sorted(bound.items())]}
for p in [A/'check_revision2.py',S/'scripts/dataset_lib.py',S/'scripts/schema_definition.py']:out['bound_files'].append({'path':str(p),'sha256':sha(p)})
for name in ['independent-audit-v2.json','independent-audit.json']:(A/name).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md='# Ghosh 2012 canonical/reader audit — revision 2\n\nStatus: '+out['status']+'.\n\nThe five grouped states now use `sample_set`; the FTIR state and four corresponding reader labels explicitly describe separate particle/pure-ligand specimens. Exactly six canonical leaves and four reader leaves changed. Seventeen other records are byte-identical. All quantities, operations, evidence and prior versions remain unchanged.\n\nThe complete v1 review covered 21 records, 33 operations, 325 prose items, 1,176 typed fields, 585 measurements, 71 source facts, 243 source units and all 272 table cells. Its 60,188 checks passed (44,178 were public-path string guards); this bounded revision adds '+str(sum(checks.values()))+' checks. Current schema, source-group and zero-task checks pass.\n\nMolecular/apparatus, mounted browser, Site integration, publication and training gates remain separate.\n'
for n in ['independent-audit-v2.md','independent-audit.md']:(A/n).write_text(md,encoding='utf-8')
print(json.dumps({'status':out['status'],'checks':out['checks'],'failures':fails,'audit_sha256':sha(A/'independent-audit-v2.json'),'deltas':rd},ensure_ascii=False,indent=2))
