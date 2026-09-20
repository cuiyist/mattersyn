from pathlib import Path
import sys,json,hashlib
O=Path(__file__).resolve().parent;C=O.parent/'canonical-proposal/draft-v2';S=Path('[local path redacted]')
sys.path.insert(0,str(S))
from dataset_lib import validate_record,eligibility
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
rows=[]
for m in read(C/'record-manifest.json')['records']:
 r=read(m['path']);errors=validate_record(r);tasks=eligibility(r)
 rows.append({'record_id':r['record_id'],'errors':errors,'task_eligibility':tasks,'passed':not errors and not any(v['eligible'] for v in tasks.values())})
out={'status':'passed' if all(x['passed'] for x in rows) else 'findings','method':'Direct current schema/semantic validator and eligibility evaluator on frozen files; no author builder executed.','rows':rows,'bound_validator_files':{str(S/n):hashlib.sha256((S/n).read_bytes()).hexdigest() for n in ['dataset_lib.py','schema_definition.py']}}
(O/'schema-and-eligibility-checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'status':out['status'],'records':len(rows),'failures':[x for x in rows if not x['passed']]}))
