"""Recheck patched adapter; writes only isolated synthetic ledgers in this audit folder."""
from pathlib import Path
from copy import deepcopy
import json, hashlib, importlib.util, datetime, tempfile, contextlib, ast
W=Path(__file__).resolve().parent
# Reuse the original independently authored 25 pure-function regressions.
exec(compile((W/'probe_activation_adapter.py').read_text(encoding='utf8').split('# Demonstrate why')[0], str(W/'probe_activation_adapter.py'), 'exec'))
cleared=deepcopy(partition)
for g in cleared['included_groups']:g['requires_generation_reopen_consistency_check']=False
x,y=m.build_rows(ledger,cleared,rows,ids[:4])
check('all four audited generation holds survive cleared current partition flags',set(ids[:4]).isdisjoint({r['group_id'] for r in x}) and len(y)==5)
rejected('audited hold outside cutoff rejected',lambda:m.build_rows(ledger,partition,rows,['not-in-cutoff']))
check('hold file hash is enforced in adapter main',"require(digest(holds_path) == audit['generation_dispatch_holds_sha256']" in raw.decode())
check('adapter supplies exact ledger preimage to locked mutation', 'expected_ledger_sha256=hashlib.sha256(before_raw).hexdigest()' in raw.decode())
mon=m.monitor
monitor_path=Path(mon.__file__); monitor_raw=monitor_path.read_bytes(); monitor_sha=hashlib.sha256(monitor_raw).hexdigest()
(W/('monitor-set-priority-snapshot-'+monitor_sha[:12]+'.py')).write_bytes(monitor_raw)
set_node=next(n for n in ast.parse(monitor_raw.decode()).body if isinstance(n,ast.FunctionDef) and n.name=='set_priority')
lock_node=next(n for n in set_node.body if isinstance(n,ast.With))
check('expected digest guard occurs inside ledger lock before read',isinstance(lock_node.body[0],ast.If) and 'expected_ledger_sha256' in ast.unparse(lock_node.body[0].test) and 'ledger = read_ledger(path)' in ast.unparse(lock_node.body[1]))
with tempfile.TemporaryDirectory(prefix='adapter-isolated-',dir=W) as temp:
    temp=Path(temp); lp=temp/'ledger.json'; rp=temp/'source-report.json'
    synthetic={'schema_version':1,'groups':{'scope':{'generation':1,'review':{'status':'queued'},'queue_order':1,'needs_recheck':False}},'files':{},'current_paper':{'group_id':'scope','reviewer':'preserve'},'current_batch':{'owner':'preserve','papers':[{'group_id':'scope','reviewer':'preserve'}]}}
    original=json.dumps(synthetic,sort_keys=True).encode();lp.write_bytes(original)
    rp.write_text('{"synthetic":true}\n',encoding='utf8')
    policy={'mode':'evidence_richness','require_screened':True,'source_report':str(rp.resolve()),'source_report_sha256':hashlib.sha256(rp.read_bytes()).hexdigest(),'screened_at':'2026-09-22T00:00:00+00:00','rankings':[{'group_id':'scope','source_generation':1,'score':2}]}
    mon.set_priority(lp,policy,now=1000000000)
    changed=json.loads(lp.read_bytes())
    check('existing default caller still accepts valid evidence policy',changed['selection_policy']['rankings']==policy['rankings'])
    check('default policy update preserves scientific state and claims',all(changed.get(k)==synthetic.get(k) for k in ['groups','files','current_paper','current_batch']))
    lp.write_bytes(original)
    mon.set_priority(lp,policy,now=1000000000,expected_ledger_sha256=hashlib.sha256(original).hexdigest())
    check('matching preimage permits isolated policy write','selection_policy' in json.loads(lp.read_bytes()))
    lp.write_bytes(original)
    try:mon.set_priority(lp,policy,expected_ledger_sha256='0'*64)
    except RuntimeError: check('stale expected preimage rejects before any write',lp.read_bytes()==original)
    else:check('stale expected preimage rejects before any write',False)
    check('rejected preimage releases lock',not lp.with_suffix('.json.lock').exists())
    for bad in ['BAD',42,'A'*64]:
        try:mon.set_priority(lp,policy,expected_ledger_sha256=bad)
        except ValueError:check('invalid expected digest rejected '+str(bad)[:8],lp.read_bytes()==original)
        else:check('invalid expected digest rejected '+str(bad)[:8],False)
    # Simulate a cooperating concurrent edit at the boundary before lock acquisition.
    real_locked=mon.locked_ledger
    concurrent=json.dumps({**synthetic,'last_scan_at':'concurrent-update'}).encode()
    @contextlib.contextmanager
    def changed_before_lock(path):
        path.write_bytes(concurrent)
        with real_locked(path):yield
    mon.locked_ledger=changed_before_lock
    try:
        try:mon.set_priority(lp,policy,expected_ledger_sha256=hashlib.sha256(original).hexdigest())
        except RuntimeError:check('simulated concurrent change survives rejected activation unchanged',lp.read_bytes()==concurrent)
        else:check('simulated concurrent change survives rejected activation unchanged',False)
    finally:mon.locked_ledger=real_locked
    lp.write_bytes(original)
    mon.set_priority(lp,{'mode':'arrival_order'},now=1000000000)
    check('existing arrival order caller retains default behavior',json.loads(lp.read_bytes())['selection_policy']['mode']=='arrival_order')
out={'schema':'mattersyn-independent-activation-adapter-audit/1','passed':all(c['pass'] for c in checks),'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'adapter_script_sha256':digest,'monitor_script_sha256':monitor_sha,'probe_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'counts':{'checks':len(checks),'failed':sum(not c['pass'] for c in checks)},'checks':checks,'resolved_findings':['ADAPTER-AUDIT-01','ADAPTER-AUDIT-02'],'scope':'Direct code review, synthetic full-denominator pure-function probes and actual set_priority calls only against a disposable isolated audit ledger. Adapter main and actual shared ledger were never invoked. Concurrent change simulated at lock entry; no real worker concurrency run.','limitations':['This adapter pass does not replace both exact-run source/semantic screening audits.','Shared ledger must still match the supplied fresh partition at activation.','Scientific status, claim and identity review remain separate; ordering does not approve a pair.'],'shared_ledger_mutated':False}
op=W/'activation-adapter-audit.json';op.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
(W/('activation-adapter-audit-'+digest[:12]+'.json')).write_bytes(op.read_bytes())
print(json.dumps({'path':str(op),'sha256':hashlib.sha256(op.read_bytes()).hexdigest(),'passed':out['passed'],'counts':out['counts'],'adapter_sha256':digest,'monitor_sha256':monitor_sha},indent=2))
assert out['passed']
