from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy,sys,importlib.util
A=Path(__file__).resolve().parent;N=A.parent;C=N/'canonical-proposal';P=N/'public-review-proposal';S=Path('[local path redacted]');sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record,eligibility
def read(p):return json.loads(p.read_text('utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
bound={};checks=[]
def bind(p):bound[str(p)]=sha(p);return read(p) if p.suffix=='.json'else p
def ck(label,ok):checks.append({'check':label,'passed':bool(ok)});assert ok,label
prior=bind(A/'independent-audit-v1.json');old=bind(C/'v1/package-manifest.json');new=bind(C/'v2/package-manifest.json')
ck('Exact original v1 boundary',sha(C/'v1/package-manifest.json')=='5986df83c2313f8e5418d0c46c049d86e2ef62dbd049359c7a53a5010e312281')
for prefix,manifest in [('Preserved original',old),('Final v2',new)]:
 for name,h in manifest['bound_files'].items():p=Path(name);bind(p);ck(prefix+' exact '+name,sha(p)==h)
old_records={p.stem:p for p in (C/'v1').glob('pati-2009-*.json')};new_records={p.stem:p for p in (C/'v2').glob('pati-2009-*.json')}
ck('All 19 record IDs',set(old_records)==set(new_records)and len(old_records)==19)
for rid,p in new_records.items():
 ck('Canonical bytes unchanged '+rid,sha(p)==sha(old_records[rid]));r=read(p);ck('Current schema '+rid,not validate_record(r));ck('No eligible tasks '+rid,not any(x['eligible']for x in eligibility(r).values()))
before=bind(P/'v1/pati2009.json');after=bind(P/'v2/pati2009.json');expected=copy.deepcopy(before);expected['review_scope']='supplied_main_and_matched_si'
ck('Exactly one reader metadata leaf changed',after==expected)
ck('Source group and scientific counts unchanged',new['source_freeze_sha256']==old['source_freeze_sha256'] and new['source_audit_sha256']==old['source_audit_sha256'] and new['counts']==old['counts'])
fixture=A/'reader-contract-fixture';spec=importlib.util.spec_from_file_location('actual_reader_validator_v2',S/'scripts/build_paper_reviews.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.ROOT=fixture
errors=mod.validate(after);ck('Actual current reader consumer passes',not errors)
for p in [S/'scripts/build_paper_reviews.py',S/'scripts/review_scope.py',S/'scripts/dataset_lib.py',Path(__file__)]:bind(p)
for p in list((C/'v2').glob('*delta*.json'))+list((C/'v2').glob('*validation*.json')):bind(p)
out={**{k:v for k,v in prior.items()if k not in ['bound_files','open_findings','status','passed','created_at','proposal_freeze_sha256','check_count']},'created_at':datetime.now(timezone.utc).isoformat(),'status':'passed','passed':True,'proposal_freeze_sha256':sha(C/'v2/package-manifest.json'),'prior_audit_sha256':sha(A/'independent-audit-v1.json'),'reader_sha256':sha(P/'v2/pati2009.json'),'check_count':prior['check_count']+len(checks),'delta_check_count':len(checks),'delta_checks':checks,'open_findings':[],'resolved_findings':[{'id':'PATI-CAN-01','resolution':'Supported review_scope token in a preserved v2. Every other reader field and all 19 canonical bytes unchanged; actual current reader validator passes.'}],'bound_files':dict(sorted({**prior['bound_files'],**bound}.items())),'delta_scope':'Bounded v2 recheck. Does not claim a second full source reading, visual viewer approval or publication.'}
for name in ['independent-audit-v2.json','independent-audit.json']:(A/name).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8')
md='# Pati canonical/reader audit — v2\n\nPassed. The one unsupported review-scope token is corrected. All 19 canonical records are byte-identical, and every other reader field is deeply equal to preserved v1. The actual current Site reader validator passes in the private fixture.\n\nThe prior complete scientific/transport review covers 35 operation instances, 58 facts, 218 source units, 20 table cells, 1,101 reader fields and 20 selected crops. No remaining findings. Molecule, apparatus, mounted browser, publication and training gates remain separate.\n'
for name in ['independent-audit-v2.md','independent-audit.md']:(A/name).write_text(md,'utf8')
print(json.dumps({'status':'passed','delta_checks':len(checks),'freeze_sha256':sha(C/'v2/package-manifest.json'),'audit_sha256':sha(A/'independent-audit-v2.json')}))
