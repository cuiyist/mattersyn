"""Bounded read-only audit of cutoff selection. Only writes this audit's artifacts."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,sys,subprocess
sys.dont_write_bytecode=True
W=Path(__file__).resolve().parent;MON=W.parent.parent
sys.path.insert(0,str(MON))
import monitor
from activate_screened_cutoff import build_policy

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
checks=[]
def check(ok,label):
 checks.append({'check':label,'passed':bool(ok)})
 if not ok:raise AssertionError(label)

if (W/'independent-workflow-audit.json').exists():raise RuntimeError('Audit already frozen.')
live_raw=(MON/'ledger.json').read_bytes(); live=json.loads(live_raw)
prior=read(W/'activation/ledger-before-activation.json')
partition=read(W/'scope-partition.json'); report=read(W/'screen/ranked-scopes.json')
proof=read(W/'activation/activation-proof.json'); coverage=read(W/'screen-coverage-check.json')
policy=read(W/'activation/priority-policy.json'); progress=read(W/'screen/progress.json')
snapshot=read(W/'ledger-snapshot.json')
rows=[json.loads(s) for s in (W/'screen/documents.jsonl').read_text(encoding='utf-8').splitlines() if s]
files={str(p):sha(p) for p in [MON/'activate_screened_cutoff.py',MON/'monitor.py',MON/'test_cutoff_activation.py',MON/'test_batch.py',W/'screen-coverage-check.json',W/'check_screen_coverage.py',W/'activation/activation-proof.json',W/'activation/priority-policy.json',W/'activation/ledger-before-activation.json',W/'screen/ranked-scopes.json',W/'screen/progress.json',W/'screen/documents.jsonl',W/'scope-partition.json',W/'ledger-snapshot.json',Path(__file__)]}
check(sha(W/'screen/ranked-scopes.json')==proof['report_sha256']==coverage['screen_report_sha256']==progress['report_sha256'],'Report hashes agree')
check(sha(W/'scope-partition.json')==proof['partition_sha256'],'Partition hash agrees')
check(sha(W/'screen/documents.jsonl')==coverage['documents_sha256'],'Document disposition hash agrees')
check(sha(W/'ledger-snapshot.json')==coverage['snapshot_sha256']==report['source_snapshot_sha256'],'Screen snapshot hashes agree')
check(progress['state']=='complete','Screen completion recorded')
check(report['scientific_review_performed'] is False and report['review_state_changed'] is False,'Screen explicitly disclaims scientific review and review-state mutation')
check(coverage['screening_is_not_full_reading_or_exclusion'] is True,'Coverage disclaimer explicit')
check(proof['screening_exclusions_assigned']==0 and proof['scientific_statuses_changed'] is False,'Activation proof assigns no scientific exclusions')
cutoff=Path(partition['cutoff_manifest_path']);files[str(cutoff)]=sha(cutoff)
check(sha(cutoff)==partition['cutoff_manifest_sha256'],'Immutable cutoff manifest agrees')
for p,digest in read(cutoff)['bound_files'].items():
 check(sha(p)==digest,'Cutoff dependency '+p);files[p]=digest
check(partition['partition_ledger_sha256']==sha(W/'activation/ledger-before-activation.json'),'Activation based on exact partition ledger')
rebuilt,held=build_policy(prior,report,partition,W/'screen/ranked-scopes.json')
check(rebuilt==policy and held==proof['stale_rankings_held'],'Saved policy recomputes exactly')
check({k:v for k,v in live['selection_policy'].items() if k!='applied_at'}==policy,'Current policy matches cutoff-restricted activation')
included=set(partition['included_canonical_group_ids']);later=set(partition['later_arrival_group_ids'])
ranked={x['group_id'] for x in policy['rankings']}
check(len(ranked)==len(policy['rankings'])==9536,'Unique cutoff ranking count')
check(ranked==included and not ranked&later and len(later)==31,'Only immutable-cutoff scopes ranked')
for key in later:
 state=monitor.priority_state(live,key)
 check(state['status']=='pending_unranked' and not state['eligible_for_selection'],'Later scope blocked '+key)
for x in policy['rankings']:
 check(live['groups'][x['group_id']]['generation']==x['source_generation'],'Current source generation '+x['group_id'])
check(set(snapshot['files'])==set(prior['files']),'Screen snapshot and activation file inventories agree')
check(snapshot['groups']==prior['groups'] and snapshot['current_batch']==prior['current_batch'],'Screening preserved all source groups and current batch')
check(len(rows)==len({x['file_key'] for x in rows})==13862,'Every snapshot copy has one disposition')
check({x['file_key'] for x in rows}=={k for k,v in snapshot['files'].items() if v['exists']},'Disposition keys cover every present snapshot copy')
check(Counter(x['status'] for x in rows)==Counter(report['counts']['status_counts']),'Disposition totals agree')
for row in rows:
 check(row['hash_computed'] is True and row['source_unchanged_from_snapshot'] is True,'Per-copy hash/disposition declaration '+row['file_key'])
 check(row['status'] in {'text_screened_candidate','manual_format_or_text_review_required'},'Candidate/manual status only '+row['file_key'])
 for k in ('verified_recipe','verified_structure','verified_sample_join'):
  if k in row.get('features',{}):check(row['features'][k] is False,'No scientific inference '+row['file_key']+' '+k)
check(coverage['fixed_cutoff_file_dispositions']==13831 and coverage['later_top_level_copies_separate']==31,'Cutoff and later-copy counts separate')
check(len(coverage['held_nested_copy_dispositions'])==3 and all(x['disposition']=='unique_nested_candidate_requires_queue_admission_and_pairing' for x in coverage['held_nested_copy_dispositions']),'Three nested candidates remain held')
check(live['current_batch']['batch_id']==prior['current_batch']['batch_id'],'Original batch identity retained')
check(live['current_batch']['papers'][:5]==prior['current_batch']['papers'],'All five original batch reservations retained')
check(live['groups']['10.1021_jp0219348']==prior['groups']['10.1021_jp0219348'],'Heo source/review checkpoint unchanged')
active=monitor.active_claims(live)
check({x['group_id'] for x in active}=={'10.1021_jp0219348','10.1021_ja103805s'},'Exactly Heo and one newly admitted scope active')
changes=[k for k in live['groups'] if live['groups'][k]!=prior['groups'].get(k)]
check(changes==['10.1021_ja103805s'],'Only admitted group state differs since activation')
check(live['groups'][changes[0]]['review']['status']=='in_progress' and prior['groups'][changes[0]]['review']['status']=='queued','New scope is active, not scientifically completed')
closed=[p['group_id'] for p in prior['current_batch']['papers'] if p['group_id']!='10.1021_jp0219348']
check(all(live['groups'][k]==prior['groups'][k] and live['groups'][k]['review']['status'] in monitor.TERMINAL_STATUSES for k in closed),'Four original completed members preserved')
test=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','test_cutoff_activation','-v'],cwd=MON,capture_output=True,text=True,encoding='utf-8')
check(test.returncode==0,'Six isolated selection tests pass')
check((MON/'ledger.json').read_bytes()==live_raw,'Audit and isolated tests did not mutate production ledger')
snapshot_out=W/'independent-workflow-ledger-snapshot.json';snapshot_out.write_bytes(live_raw);files[str(snapshot_out)]=sha(snapshot_out)
log=W/'independent-workflow-test-output.txt';log.write_text(test.stdout+test.stderr,encoding='utf-8');files[str(log)]=sha(log)
out={'schema':'mattersyn-independent-cutoff-workflow-audit/1','author':'/root/peng1998_reader_assets','audited_at':datetime.now(timezone.utc).isoformat(),'status':'passed_bounded_workflow_scope','check_count':len(checks),'isolated_tests':6,'open_findings':[],
 'scope':'Read implementation and actual activation/disposition proofs; recomputed cutoff policy, verified frozen hashes and exact saved/live states; ran isolated tests. This is not source-content or full scientific review.',
 'counts':{'snapshot_copy_dispositions':13862,'cutoff_copy_dispositions':13831,'ranked_cutoff_scopes':9536,'later_scopes_unranked':31,'manual_copy_dispositions':238,'nested_candidates_held':3,'active_scopes':2,'original_completed_batch_members_preserved':4},
 'active_group_ids':[x['group_id'] for x in active], 'implementation_review':[
 'set_priority is lock-protected and changes selection_policy only, validates report SHA, unique canonical group IDs, finite scores and current generations.',
 'build_policy restricts rankings to the immutable cutoff partition; stale generations are held. No source score assigns no-recipe or completed statuses.',
 'claim and explicit claim_batch --refill enforce current priority coverage and source stability. Refills preserve earlier batch members and admit only free active-paper slots.',
 'Screen content statuses are candidate/manual dispositions. Coordinate, recipe and sample-join verification flags remain false; later source work and source/SI pairing remain required.',
 'Current real ledger differs from the activation backup by the intended one new in-progress group and its recorded admission; Heo and all four earlier completed member groups are unchanged.'
 ],'limitations':[
 'No original papers/SI were scientifically reread or source bytes rehashed in this bounded workflow audit. Actual source-hash claims are checked through the hash-bound disposition evidence; this audit does not recreate the screen.',
 'The exact after-set_priority ledger was not stored as a separate file before the later intended refill. We verify the activation code, isolated no-mutation test, saved policy/proof and current snapshot; we do not label the current post-refill ledger as that transient state.',
 'Later discovered/new or changed sources still need refreshed screened generations. Nested candidates remain held and require an explicit scope decision.',
 'The audit approves neither keyword-based recipe exclusion nor public scientific publication.'
 ],'bound_files':files,'checks':checks,'production_writes_performed':False}
(W/'independent-workflow-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(W/'independent-workflow-audit.md').write_text(f'''# Independent cutoff workflow audit

Passed the bounded implementation and saved-state review with {len(checks):,} checks and six isolated tests. No open finding was identified.

The active policy contains only the 9,536 canonical scopes in the immutable cutoff. All 31 later scopes are unranked and unclaimable. The screen has 13,862 copy dispositions: 13,831 cutoff copies and 31 later copies; 238 require manual format/text review. Three nested candidates remain held. These are screening dispositions, not claims of scientific reading, main/SI identity verification, recipes or structures.

Heo remains active with its previous checkpoint unchanged. The four earlier completed batch members are retained unchanged. The only new group-state change is the recorded admission of ja103805s as in progress; the active count is two. A refill changes reservations, not scientific completion.

The source code, report/snapshot/cutoff hashes, recomputed restricted policy, per-copy status semantics and current ledger snapshot were checked. All six tests used temporary ledgers; the production ledger bytes were unchanged by this audit. The saved JSON contains the exact scope and hashes.

This audit did not reread papers or recompute every original source hash. The live snapshot is after the intended refill, not a reconstructed claim of the transient post-activation ledger. No keyword-based exclusion, full scientific review, publication or later-scope admission is approved here.
''',encoding='utf-8')
print(json.dumps({'status':out['status'],'checks':len(checks),'audit_sha256':sha(W/'independent-workflow-audit.json'),'active':out['active_group_ids']}))
