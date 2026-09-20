"""Save the user's finish-active-then-pause direction; never admit a paper."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
F=Path(__file__).resolve().parent;MON=F.parents[2];M=F.parents[4]
read=lambda p:json.loads(p.read_text('utf8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
now=datetime.now(timezone.utc).isoformat()
policy={'status':'finish_active_then_pause','recorded_at':now,'user_instruction':'After finishing the current papers, temporarily stop for joint review of progress and results.','interpretation':'Current active review claims, not the whole corpus. This interpretation was communicated to the user.','active_group_ids':['legacy::10.1021_acs.jpcc.5c05144'],'already_published_source_ids':['friedfeld2019'],'new_paper_admission_allowed':False,'resume_requires_user_instruction':True,'automation_id':'mattersyn-sequential-paper-review','automation_current_action':'Existing heartbeat updated to finish-only; pause it after the active contribution and final publication verification complete.','remaining_time_estimate':'About1–2hours for the active paper, allow up to3hours for corrections; rough forecast, not a deadline or whole-corpus estimate.','estimate_scope':'Remaining illustrations, independent reviews, integration, browser verification and publication.','paid_api_pilot':'deferred'}
save(MON/'review-control.json',policy)
ed=read(MON/'public-progress-editorial.json');counts=read(MON/'deadline-20260920/active-cutoff.json')['counts']
ed['workflow']['summary']='Finish the paper already under active review, then temporarily pause for joint review of the results. No new papers will be admitted until the user asks to resume.'
ed['workflow']['capacity']='Parallel work is limited to the active Sasongko FAPbI3 contribution. Molecular, apparatus and sample-context illustrations retain separate audits. New-paper admission is paused.'
ed['workflow']['fixed_pending_provisional_scopes']=counts['included_pending_scopes']
ed['workflow']['later_arrival_groups_current']=counts['later_arrival_group_candidates']
ed['workflow']['later_arrival_file_candidates_current']=counts['later_arrival_file_candidates']
ed['workflow']['scope_counts_updated_at']=now
ed['estimate']['summary']='The fixed collection has '+format(counts['included_pending_scopes'],',')+' provisional scopes pending and three held identity cases. Only the active paper is being completed before a temporary pause. There is no validated whole-collection finish forecast.'
ed['estimate']['current_batch']='Friedfeld InP is published. Sasongko FAPbI3 has passed source and structured-data audits; illustrations and publication checks remain. Rough remaining estimate at this checkpoint: 1–2 hours, or up to 3 hours if corrections are needed. No new papers will start before the requested review pause.'
save(MON/'public-progress-editorial.json',ed)
note=f'''## 2026-09-20 — Finish active papers, then temporarily stop

Latest user direction saved {now}: finish the papers currently under active review, then pause so we can review the progress and results together. Root explicitly interpreted “current papers” as the active claims, not all papers in the folders. Friedfeld2019 is published; Sasongko2025 FAPbI3 is the sole remaining active claim. Do not claim/refill/start another paper. The existing five-minute heartbeat was updated through the app tool to this finish-only scope; retain it until current work is safely completed, then set it PAUSED. Do not create a replacement automation. Resume backlog only after user instruction.

Root communicated a rough remaining estimate of 1–2 hours, with up to 3 hours if corrections are needed. This is not a guaranteed completion time or a whole-corpus ETA. Sasongko source/main-SI and canonical/reader audits passed; Peng molecular/stock package freeze d0061aaac1876774eb8e6667ad2cec6203fdcf90cbd27b6de30c18be5c583bf8 is with Backlog for independent audit. Norberg is finishing the 21 apparatus scenes; Peng is preparing product/specimen-context views. Root alone integrates/publishes. Finish all gates without lowering quality, then publish final counts/open limitations/live links and pause. Saved policy: research-assets/incoming-paper-monitor/review-control.json. Paid pilot, source downloads and deferred chatbot/DFT features remain unauthorized or deferred.

'''
p=M/'MEMORY.md';p.write_text(note+p.read_text('utf8'),'utf8')
ref=M/'skills/mattersyn-paper-to-site/references/incoming-corpus.md'
s=ref.read_text('utf8');heading='# Growing local corpus: five-paper review batches\n'
addition='\n**Temporary stop instruction (September20,2026):** The user now requests finishing only the already active papers, then pausing for a joint progress/results review. Consult `review-control.json`, current memory and the actual ledger: do not refill or admit another paper during this finish-only period. Finish the active contribution through its separate audits and verified publication, save the handoff, and pause the existing heartbeat. Resume only after the user asks. This temporary instruction supersedes the rolling-admission guidance below without discarding it.\n'
assert heading in s
if addition not in s:ref.write_text(s.replace(heading,heading+addition,1),'utf8')
print('Saved finish-active-only policy, memory and project workflow reference; no source or claim changes.')
