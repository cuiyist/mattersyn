"""Publishable milestone and durable workflow pointers; scientific data unchanged."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
MON=ROOT/'research-assets/incoming-paper-monitor'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
r=read(HERE/'screening-checkpoint.json')
n=r['newly_screened_scopes_this_checkpoint']; total=r['provisional_scopes_with_receipts']; positives=r['new_positive_scopes'];deferred=r['new_deferred_or_source_hold_scopes']
at=datetime.now(timezone.utc).isoformat()
editorial=read(MON/'public-progress-editorial.json')
w=editorial['current_work'][0]
w['stage']=f'{total} provisional scopes have targeted source-screen receipts; detailed review remains separate'
w['summary']=f'This checkpoint added {n} initial Methods/SI screens: {positives} retain preparation information and {deferred} remain deferred or held. One previously closed news scope was reused. Counts include aliases and are not unique-paper totals. Complete extraction, independent scientific audit and training admission are still separate.'
w['stages'][1]['detail']=f'{total} provisional scopes now have targeted source receipts across the tracked shortlist and mixed batches. Seven-positive outcomes in each mixed batch passed separate bounded checks; the prior second atomic batch also passed. Other checks remain partial or pending.'
w['stages'][2]['detail']='New candidates include actual refined atom tables as well as phase/morphology observations. Preserve average/disordered models, uncertain recipe-variant assignments, molecular precursors, simulations and external references as separate roles; zero new exact pairs approved.'
editorial['estimate']['status']='initial_screening_timing_measured_in_purposive_batches'
editorial['estimate']['summary']='October 22 remains the planning target for a prioritized audited release. The new Methods-first batches are much lighter than full curation, but their selected-source timings do not establish a whole-collection finish date. The 9,500 unfinished fixed-collection groups still require final dispositions.'
editorial['estimate']['notes']=[
    'Two mixed batches took 6.7 and 8.8 minutes for nine and ten new initial screens; their separate checks took 4.8 and 4.3 minutes. These are selected readable sources, not a representative corpus benchmark.',
    'Initial screening, complete extraction, independent scientific audit, website integration and training admission have different completion gates.',
    'Duplicate receipt reuse saves repeated reading only when exact source identity and inspected coverage match; it is not an extra completed paper.',
    'A file labelled as the main article was verified to be a Peer Review File; the true main remains held while useful SI preparation information is retained.',
    'Additional GPU capacity is not established as the bottleneck. An API pilot remains deferred; no paid processing or source upload was started.',
    'Daily scheduling is preserved. A daily wakeup does not establish continuous execution or a fixed number of processing hours.',
]
editorial['recent_milestones'].insert(0,{'at':at,'text':f'Parallel Methods-first screening added {n} provisional scope checks ({positives} with usable preparation information; {deferred} deferred or held), plus reuse of one already-closed news scope. {total} provisional scopes now have tracked source-screen receipts, including aliases. Separate bounded checks passed for both mixed batches and the prior second atomic shortlist; selected phase candidates were spot-checked. No new scientific records or exact training pairs were published.'})
editorial['workflow']['screening_scope']='Completed automated nominations plus ongoing targeted original-source Methods/SI checks. Source screens are retained with exact file bindings and coverage; they are not complete-paper scientific reviews.'
editorial['workflow']['source_screen_checkpoint_at']=at
editorial['workflow']['source_screen_receipt_scopes']=total
editorial['workflow']['source_screen_new_scopes_latest']=n
editorial['workflow']['screening_count_limit']='Includes aliases and prior terminal reuse; no final-disposition or training count implied.'
save(MON/'public-progress-editorial.json',editorial)
control=read(MON/'review-control.json')
control['latest_source_screen_checkpoint']={'at':at,'path':str((HERE/'screening-checkpoint.json').relative_to(ROOT)),'sha256':hashlib.sha256((HERE/'screening-checkpoint.json').read_bytes()).hexdigest(),'screened_scope_index':str((HERE/'screened-scopes.json').relative_to(ROOT)),'scope_receipts':total,'not_scientific_completion':True}
control['additional_source_role_holds']=[{'group_id':'legacy::10.1038_s43246-021-00198-z','receipt':str((HERE/'mixed-batch-02-independent-check/source-role-hold.json').relative_to(ROOT)),'reason':'Main and SI1 are identical peer-review files; true main missing in selected local scope. SI2 retains partial preparation information. Do not admit until source role is resolved.'}]
save(MON/'review-control.json',control)

heading='## 2026-09-23 — Parallel Methods-first source screening checkpoint'
memory=(ROOT/'MEMORY.md').read_text(encoding='utf8')
assert heading not in memory,'Checkpoint already saved; use an explicit follow-up entry.'
entry=f'''{heading}

Daily review continued with the user-authorized efficient workflow. Added {n} initial source-screen receipts: {positives} positive for scoped preparation information and {deferred} deferred/source-held cases; one preexisting terminal news scope was reused. The tracked batches now cover {total} provisional scopes, including exact-copy aliases and parallel editions. This is not a count of unique completed papers. Scientific counts remain675records/123routes/50hubs and zero task-ready exact sample-coordinate recipe pairs. No new complete-paper extraction, scientific closure, dataset admission or material reader was claimed.

Durable checkpoint: research-assets/methods-triage-20260923/screening-checkpoint.json. Reuse the screened-scopes.json index to avoid rescreening unchanged sources; consult original per-scope generation/hash/coverage bindings, and retain alias identities. Atomic batches01/02 and mixed batches01/02 have separate bounded source checks. Phase batch01 has independent spot-checks only for ranks53/55/58; phase batch02 has a separate check of Cs3Cu2Cl5 rank66, with exact-copy alias78. Atomic batches03/04 remain author-screened, not independently scientifically approved. Preserve source-role uncertainty and all detailed-review gates.

The new main-role hold legacy::10.1038_s43246-021-00198-z is supported by an independent receipt: main and SI1 are identical Peer Review Files, while matching-title SI2 contains partial ZnSe epilayer preparation. This is not a no-synthesis exclusion. Review control links the supplemental hold; do not mutate the historical frozen ranker/overlay. Lower-ranked mixed sampling also found useful synthesis, so low automated scores remain nominations rather than exclusions.

Initial author screening took6.7min for9new scopes and8.8min for10new scopes in the two root mixed batches; independent checks took4.75min and4.26min. Selected atomic/phase batches have their own timed summaries. These timings include record preparation and interruptions, are not representative sampling and exclude full extraction/integration. Do not extrapolate a whole-corpus calendar ETA or add overlapping worker durations as wall time. October22 remains a prioritized-release target, with9500fixed scopes awaiting final disposition. Preserve daily scheduling, separate new arrivals, and the existing Chen/Saini full-review packages.

Potential capacity improvements must be measured on representative source-bound cases. Hash-bound cache/duplicate reuse, selective page reading and parallel auditing are now in use; additional local GPUs are not demonstrated to be a bottleneck. No paid API run, cloud GPU, installation, source download or external source-archive transmission was started. Public progress delivery is recorded separately after verification; original sources, full text and page images stay local.

'''
(ROOT/'MEMORY.md').write_text(entry+memory,encoding='utf8')
(HERE/'README.md').write_text(f'''# Methods-first screening checkpoint — September 23, 2026

{n} new provisional scopes screened; {positives} retain preparation information and {deferred} are deferred or held. One existing terminal decision was reused. The cumulative tracked source-screen register contains {total} provisional scopes, including aliases. Scientific data and training admissions are unchanged.

`screening-checkpoint.json` binds the frozen batch summaries and independent checks. `screened-scopes.json` prevents repeated screening of unchanged inputs; it does not merge identities or close papers. Each author package states exactly which text pages, visual pages and SI were inspected. Full review and publication require the established per-paper quality gates.

The atomic batch02 independent audit and mixed batch01/02 checks passed. Phase checks are selective, not whole-batch audits. Do not promote author screens or coordinate-table candidates into verified recipe pairs. Kirstein's wrong-main source hold is explicit. No unsupported synthesis-negative corpus exclusions were made.

The first small timing samples demonstrate a lighter screening process, not whole-corpus throughput. No new spending or source downloads occurred; the daily schedule is unchanged. PDFs, SI, full text and page images remain local under private directories. Public projection uses an explicit allowlist and the existing exclusion policy.
''',encoding='utf8')
print(json.dumps({'at':at,'new_scope_screens':n,'cumulative_scope_receipts':total,'scientific_records_added':0}))
