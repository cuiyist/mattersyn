"""Save the user's shorter target without changing the frozen collection or review gates."""
from pathlib import Path
from datetime import datetime,timezone
import json

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
MON=ROOT/'research-assets/incoming-paper-monitor'
now=datetime.now(timezone.utc)
target=now.replace(month=10,day=22)
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
control=read(MON/'review-control.json')
active=read(MON/'deadline-20260920/active-cutoff.json')
if not (OUT/'previous-deadline-state.json').exists():
    write(OUT/'previous-deadline-state.json',{'review_control':control,'active_cutoff':active})
decision={'schema':'mattersyn-one-month-target/1','recorded_at':now.isoformat(),
          'user_instruction':'Accelerate the process; finish in one month.',
          'target_at_utc':target.isoformat(),'target_calendar_date':'2026-10-22',
          'target_basis':'One calendar month from September22 request; planning target, not validated completion promise.',
          'cutoff_at':active['cutoff_at'],'cutoff_manifest':active['cutoff_manifest'],
          'pending_provisional_scopes':9500,'later_arrivals_separate':True,
          'required_closures_per_day_30_days':9500/30,'production_days_after_calibration_and_final_reserve':24,
          'required_closures_per_production_day':9500/24,'capacity_test_target_per_day':400,
          'paid_execution_authorized':False,'resource_choice':'awaiting_user_answer; continue_current_authorized_work',
          'pilot_proposal_cap_USD':200,'pilot_scopes':50,'pilot_retained_full_review_max':20,
          'pilot_runner_implemented':False,'production_budget_authorized':False,
          'quality_gate':'Separate independent audit per retained paper and per proposed exclusion; unchanged complete available main/SI coverage and source/sample/figure verification.',
          'accelerations':['Content-aware duplicate reconciliation, preserving distinct unavailable intended papers.','Reuse verified extraction/rendering and shared illustrations.','Parallel source extraction and independent audits.','Batch publication and synchronize changed files only.'],
          'plan_path':str(OUT/'ACCELERATION_PLAN.md')}
write(OUT/'decision.json',decision)
control.update(recorded_at=now.isoformat(),user_instruction=decision['user_instruction'],
               target_at_utc=target.isoformat(),deadline_decision=str(OUT/'decision.json'),
               remaining_time_estimate='One-month target requires317finaldispositions/day, or400/dayover24productiondays. Current measured capacity does not establish feasibility. Resources/pilot spending remain unapproved.')
write(MON/'review-control.json',control)
active.update(recorded_at=now.isoformat(),target_calendar_months=1,target_at_utc=target.isoformat(),
              target_basis=decision['target_basis'],target_request_at=now.isoformat(),
              previous_target_at_utc='2026-11-20T03:34:39.542641+00:00')
write(MON/'deadline-20260920/active-cutoff.json',active)
editorial=read(MON/'public-progress-editorial.json')
editorial['estimate']['status']='accelerating_toward_one_month_target'
editorial['estimate']['summary']='New completion target: October22,2026, for the fixed September20collection. Approximately9,500unfinished provisional scopes require317final dispositions/day across30days, or about400/day allowing six days for calibration and final repairs. This target is not yet supported by measured capacity; the previous linear extrapolations below are conditional baselines, not an optimized-pipeline forecast.'
editorial['estimate']['notes']=[n for n in editorial['estimate']['notes'] if 'November 20' not in n]
editorial['estimate']['notes'].insert(0,'Completion means an independently audited and published retained contribution, or an independently justified exclusion/duplicate closure. Missing required evidence remains unresolved. The same quality standard applies.')
editorial['estimate']['notes'].append('A $200 capped API pilot is proposed, not approved; it covers50diverse calibration scopes and up to20complete contributions. Additional capacity and production costs require a separate decision. No paid jobs have started.')
editorial['workflow']['summary']='The one-month target is being pursued through verified reuse, content-aware duplicate checks, parallel source extraction and independent audits, shared Reader components and batched publication. Current paper work continues while additional capacity is considered.'
editorial['recent_milestones'].insert(0,{'at':now.isoformat(),'text':'User set an October22completion target for the fixed collection. Capacity requirement:317final dispositions/day across30days, or approximately400/day with calibration/repair reserve. Duplicate source payload candidates are undergoing content-aware review; identical error responses cannot merge distinct intended papers or count as scientific completion. No paid processing or new scientific publication in this update.'})
write(MON/'public-progress-editorial.json',editorial)
memory=ROOT/'MEMORY.md'
text=memory.read_text(encoding='utf8')
header='## Current target — one month, requested September 22, 2026\n\nThe user now requests acceleration and completion within one month, interpreted as October22,2026. This supersedes the former November20target; the fixed September20collection and separate later-arrival queue are unchanged. Same full main/SI coverage and per-paper independent audit apply. At9,500unfinished provisional scopes, the target requires317closedscopes/day over30days or400/day over24productiondays after calibration/repair reserve. This is a capacity requirement, not measured performance or a promise. Paid API work remains unapproved; a resource-choice question is pending. The existing$200pilot proposal is concrete but its runner/budget reservation mechanism is not yet implemented or authorized for paid execution. Read research-assets/one-month-20260922/decision.json and ACCELERATION_PLAN.md.\n\nImmediate efficiency work: cached source extraction/rendering, shared-data-driven illustrations, parallel source/audit stages, and batched changed-file-only publication. Root found637identical-role/content bundle candidates in screening hashes; they require independent actual-content validation before consolidation. Common publisher error pages may have identical bytes while referring to different intended papers; never merge those paper identities or count them as no-recipe/completed. No queue reduction has been applied.\n\n'
if not text.startswith('## Current target — one month'):
    memory.write_text(header+text,encoding='utf8')
print(json.dumps({'target':decision['target_calendar_date'],'required_per_day':decision['required_closures_per_day_30_days'],'paid_execution':False,'cutoff_unchanged':True}))
