"""Pure-function adversarial adapter probes; never calls main/set_priority."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,importlib.util,datetime
W=Path(__file__).resolve().parent;P=W.parent/'activate_pair_priority.py';raw=P.read_bytes();digest=hashlib.sha256(raw).hexdigest()
(W/('activation-adapter-snapshot-'+digest[:12]+'.py')).write_bytes(raw)
s=importlib.util.spec_from_file_location('adapter_audit',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ids=[f'audit-scope-{n:05d}' for n in range(9532)]
ledger={'groups':{g:{'generation':1,'review':{'status':'queued'}} for g in ids},'files':{},'current_batch':{'owner':'preserve'},'current_paper':{'group_id':ids[50]}}
partition={'included_canonical_group_ids':ids,'later_arrival_group_ids':['later-arrival'],'unmapped_cutoff_files':[],'missing_current_cutoff_scope_ids':[],'included_groups':[{'group_id':g,'requires_generation_reopen_consistency_check':n<4} for n,g in enumerate(ids)]}
rows=[{'group_id':g,'candidate_inspection_rank':n+1,'source_hold':n==10,'source_generation_in_partition':1,'verified_pair':False,'task_ready':False,'automatic_exclusion':False,'main_si_pairing':'unverified_candidate_group_only'} for n,g in enumerate(ids)]
checks=[]
def check(name,ok):checks.append({'check':name,'pass':bool(ok)})
def rejected(name,fn):
    try:fn()
    except (ValueError,KeyError,TypeError):check(name,True)
    else:check(name,False)
before=json.dumps([ledger,partition,rows],sort_keys=True)
ranked,held=m.build_rows(ledger,partition,rows)
check('baseline excludes one source hold and four generation holds',len(ranked)==9527 and len(held)==5)
check('pure build leaves source inputs and claims unchanged',json.dumps([ledger,partition,rows],sort_keys=True)==before)
check('no later arrival ranked','later-arrival' not in {r['group_id'] for r in ranked})
rejected('missing scope rejected',lambda:m.build_rows(ledger,partition,rows[:-1]))
bad=deepcopy(rows);bad[-1]=deepcopy(bad[0]);rejected('duplicate scope rejected',lambda:m.build_rows(ledger,partition,bad))
bad=deepcopy(rows);bad[0]['candidate_inspection_rank']=2;rejected('broken inspection order rejected',lambda:m.build_rows(ledger,partition,bad))
for key in ['verified_pair','task_ready','automatic_exclusion']:
    bad=deepcopy(rows);bad[0][key]=True;rejected(key+' true rejected',lambda b=bad:m.build_rows(ledger,partition,b))
bad=deepcopy(rows);bad[0]['main_si_pairing']='verified';rejected('automatic source pairing rejected',lambda:m.build_rows(ledger,partition,bad))
bad=deepcopy(partition);bad['later_arrival_group_ids']=[ids[20]];rejected('overlapping later membership rejected',lambda:m.build_rows(ledger,bad,rows))
bad=deepcopy(partition);bad['unmapped_cutoff_files']=['unknown'];rejected('unmapped cutoff held',lambda:m.build_rows(ledger,bad,rows))
bad=deepcopy(partition);bad['missing_current_cutoff_scope_ids']=['unknown'];rejected('missing cutoff scope held',lambda:m.build_rows(ledger,bad,rows))
bad=deepcopy(ledger);bad['groups'][ids[20]]['generation']=2;x,y=m.build_rows(bad,partition,rows);check('stale row generation held',ids[20] not in {r['group_id'] for r in x})
bad=deepcopy(ledger);bad['groups'][ids[20]]['alias_of']='canonical';x,y=m.build_rows(bad,partition,rows);check('current alias held',ids[20] not in {r['group_id'] for r in x})
bad=deepcopy(ledger);del bad['groups'][ids[20]];x,y=m.build_rows(bad,partition,rows);check('missing current scope held',ids[20] not in {r['group_id'] for r in x})
summary={'script_sha256':'a'*64};good={'passed':True,'summary_sha256':'b'*64,'ranker_script_sha256':'a'*64}
m.check_audits(summary,'b'*64,good,good);check('both exact-run passes accepted',True)
for name in ['integrity','benchmark']:
    for field,value in [('passed',False),('passed',1),('summary_sha256','c'*64),('ranker_script_sha256','c'*64)]:
        bad={**good,field:value};args=(bad,good) if name=='integrity' else (good,bad);rejected(name+' '+field+' mismatch rejected '+str(value)[:8],lambda args=args:m.check_audits(summary,'b'*64,*args))
# Demonstrate why fresh partition flags must not silently override known audited holds.
cleared=deepcopy(partition)
for g in cleared['included_groups']:g['requires_generation_reopen_consistency_check']=False
x,y=m.build_rows(ledger,cleared,rows);released=[g for g in ids[:4] if g in {r['group_id'] for r in x}]
findings=[{'id':'ADAPTER-AUDIT-01','severity':'safeguard_required_before_activation','finding':'Ledger equality check precedes monitor.set_priority lock; monitored ledger can change between check and commit. Monitor re-reads under lock but has no adapter expected-byte comparison; post-write comparison can fail after policy is already applied.','scope':'Independent code review; no concurrency or actual activation executed.','required_fix':'Compare expected ledger bytes/hash under the same lock as the actual commit.'},{'id':'ADAPTER-AUDIT-02','severity':'safeguard_required_before_activation','finding':'build_rows trusts only fresh partition generation-hold flags; clearing those flags releases all four prior audited holds.','adversarial_released_known_hold_ids':released,'required_fix':'Bind and enforce audit generation_dispatch_holds separately from fresh partition flags, with explicit reconciliation required to release.'}]
out={'schema':'mattersyn-independent-activation-adapter-probes/1','script_sha256':digest,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'initial_review_findings_before_activation','counts':{'pure_function_checks':len(checks),'failed_checks':sum(not c['pass'] for c in checks),'actionable_findings':len(findings)},'checks':checks,'findings':findings,'actual_scope':'Pure check_audits/build_rows adversarial data and direct adapter/monitor code inspection only. Adapter main, monitor.set_priority and actual shared ledger writes were never called.','shared_state_changed':False}
op=W/('activation-adapter-probes-'+digest[:12]+'.json');op.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'path':str(op),'script_sha256':digest,'counts':out['counts'],'released_prior_holds':len(released)},indent=2))
