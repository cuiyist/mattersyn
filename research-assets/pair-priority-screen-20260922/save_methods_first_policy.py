"""Save the user's lightweight triage correction without changing science states."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
MON=ROOT/'research-assets/incoming-paper-monitor'
OUT=HERE/'methods-first'
OUT.mkdir(exist_ok=True)
at=datetime.now(timezone.utc).isoformat()
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def read(p):return json.loads(p.read_bytes())
decision={
  'at':at,'status':'active_user_workflow_correction',
  'user_instruction':'Check Methods/relevant SI for synthesis first; skip papers without synthesis from detailed review; for those with synthesis, check sufficient structural evidence.',
  'first_pass':['Find Methods/Experimental/Preparation in the main paper and relevant SI.',
                'Record target synthesis present, no usable target preparation found in inspected scope, referenced-only, or unresolved.',
                'For synthesis-positive papers record available phase/XRD, size/morphology/TEM/SAED, and experimental atom-coordinate evidence separately.',
                'Select strong usable links for detailed extraction/audit; park unreadable or ambiguous files without delaying readable sources.'],
  'not_first_pass':['Complete reading of every page','Full transcription of every recipe or characterization result','Per-paper complete scientific audit','Legacy parser engineering','Website preparation'],
  'preserved_requirements':['Matched main/SI roles, with missing/unreadable SI explicitly unresolved.',
                           'No synthesis in main alone is not a no-recipe finding when SI remains unchecked.',
                           'Detailed published contributions still need full scoped extraction and independent audit.',
                           'Phase/size/morphology links are distinct from measured sample atomic coordinates.',
                           'Triage skip is not an independently audited final corpus closure.'],
  'eta_correction':'Withdraw3–7days as an estimate for the lightweight first pass; that earlier allowance bundled difficult-format recovery and source verification. No replacement duration claimed without timed evidence.',
  'existing_automated_screen_reused':True,'restart_full_corpus_extraction':False,
  'format_recovery_blocks_readable_sources':False,'no_new_paid_processing_or_downloads':True,
  'scientific_states_changed':False}
save(OUT/'decision.json',decision)
control_path=MON/'review-control.json'
before=control_path.read_bytes()
if not(OUT/'control-before.json').exists():(OUT/'control-before.json').write_bytes(before)
control=read(control_path)
control.update(recorded_at=at,workflow_phase='rapid_methods_then_structure_triage',
    user_instruction=decision['user_instruction'],
    new_paper_admission_allowed=True,
    admission_hold_reason=None,
    admission_conditions='Only synthesis-positive, structurally useful source-checked candidates enter detailed curation; existing source/generation holds still apply. Unreadable unrelated files do not block admission.',
    remaining_time_estimate='Previous3–7day initial-screen allowance withdrawn as conflating triage with recovery/audit. October22 target retained; estimate lightweight triage separately from detailed curation.',
    fast_triage_decision=str(OUT/'decision.json'))
save(control_path,control)
editorial_path=MON/'public-progress-editorial.json'
editorial=read(editorial_path)
if not(OUT/'editorial-before.json').exists():(OUT/'editorial-before.json').write_bytes(editorial_path.read_bytes())
for work in editorial['current_work']:
    if work['short_label']=='Collection screening':
        work.update(title='Methods-first synthesis and structure screening',
            stage='Rapid source triage; difficult formats separately queued',
            summary='Reuse the completed automated pass. Check the main Methods and relevant SI for usable synthesis; skip synthesis-negative papers from detailed curation, then assess structural evidence in synthesis-positive papers. This is a short eligibility check, not complete paper extraction.',
            stages=[
              {'label':'Cached-text nomination pass','status':'complete','detail':'Existing screen of 9,532 groups is retained; it is not repeated or relabeled as manual review.'},
              {'label':'Methods and relevant SI','status':'in_progress','detail':'Identify actual target preparation and distinguish precursor-only, cited-only and characterization procedures.'},
              {'label':'Structural evidence','status':'in_progress','detail':'Check phase, size/morphology and atomic coordinates separately; retain source/sample linkage limits.'},
              {'label':'Difficult source files','status':'pending','detail':'Unresolved files are separately queued and do not delay strong readable candidates.'},
              {'label':'Detailed curation and publication','status':'pending','detail':'Full extraction and independent audit are reserved for retained contributions; complete contributions may publish together.'}])
editorial['workflow'].update(summary='Methods-first eligibility screening, then structure checks and detailed review of the strongest retained sources.',
    screening_scope='Automated nominations cover the fixed collection; source-based rapid Methods/SI checks are in progress. Difficult formats remain unresolved and separately queued.',
    capacity='Parallel rapid source triage and audits of already prepared contributions. Parser recovery is no longer a prerequisite for readable papers.')
editorial['estimate'].update(status='separating_fast_screening_from_detailed_curation',
    summary='October 22 remains the target. The earlier 3–7-day screening allowance included file recovery and verification; it is withdrawn as an estimate for the lightweight Methods/SI pass. Detailed curation and training admission are estimated separately from triage.')
editorial['recent_milestones'].insert(0,{'at':at,'text':'Workflow simplified at user request: Methods/relevant SI first, structure evidence second. Unreadable files are deferred without blocking readable candidates. Full per-paper audits remain required for published data; no new training pairs claimed.'})
save(editorial_path,editorial)
memory=ROOT/'MEMORY.md'
heading='## 2026-09-22 — Lightweight Methods-first screening; recovery no longer blocks readable papers'
assert heading not in memory.read_text(encoding='utf8')
entry=f'''{heading}

User corrected the initial screening scope: inspect Methods/Experimental and relevant SI for usable synthesis, skip papers without it from detailed review, then assess sufficient structural information for synthesis-positive papers. Do not bundle first-pass triage with full reading, complete extraction, independent full scientific audits, website preparation or difficult-format recovery. Reuse the already completed cached-text screen. Unknown or unreadable SI is unresolved, not proof of no synthesis. Record target synthesis separately from precursor preparation, device/film assembly, cited-only methods and characterization preparation. Preserve original source locators.

This supersedes the blanket hold on new full website admissions pending all238format cases and all priority verifications. Strong readable synthesis/structure candidates may enter detailed curation once their own source roles and eligibility are checked, subject to existing source/generation holds and full independent audit before publication/training admission. Difficult formats remain separately queued. Existing Chen/Saini packages are preserved. No paid API work, installs or new paper downloads authorized. The3–7day initial-screen estimate is withdrawn because it included recovery/audit; no replacement time is claimed without measuring the lighter pass. Earlier2–5month/500–1600scenarios remain historical conditional planning, not measured workload or yield.

Decision and prior state saved under research-assets/pair-priority-screen-20260922/methods-first/. Work in progress is preserved: first atomic shortlist batch10scopes/8articles frozen pending separate audit; second batch identified SSZ-48 printed coordinates as a candidate, not a certified pair. DOC exact-family extension independently checked187copies but qualifies only the prior singleton; Word97 prototype will be checkpointed and parked without a broad batch. Root image-only PDF notes have explicit per-page coverage; positive screening is not full extraction. Current scientific dataset remains unchanged.

'''
memory.write_text(entry+memory.read_text(encoding='utf8'),encoding='utf8')
skill=ROOT/'skills/mattersyn-paper-to-site/references/incoming-corpus.md'
lesson='''

## Lightweight Methods-first eligibility screen (September22user correction)

For the initial corpus pass, inspect main Methods/Experimental and relevant SI preparation sections for a usable target synthesis, then check structural evidence only for synthesis-positive sources. Record concise section/page pointers and four outcomes: synthesis present; no usable target preparation found in inspected main/SI; referenced-only; unresolved. Main-only absence cannot exclude a paper whose SI is unchecked. Separate target preparation from precursor-only, device assembly and characterization procedures. Phase/XRD, size/morphology/TEM/SAED and sample-refined atom coordinates are distinct evidence levels.

Reserve full reading, exhaustive extraction and independent scientific audit for retained contributions. A first-pass skip from detailed review is not a final audited no-recipe corpus closure. Park unreadable/ambiguous files without delaying readable candidates, and do not turn parser development into an initial-screen prerequisite. Reuse existing caches and nomination passes; report triage time separately from recovery, curation and publication time. This supersedes the earlier blanket format-recovery admission hold for the original MatterSyn collection. Complete publication/training gates remain unchanged.
'''
assert '## Lightweight Methods-first eligibility screen' not in skill.read_text(encoding='utf8')
skill.write_text(skill.read_text(encoding='utf8')+lesson,encoding='utf8')
save(OUT/'policy-change-receipt.json',{'at':at,'decision_sha256':hashlib.sha256((OUT/'decision.json').read_bytes()).hexdigest(),
    'control_sha256':hashlib.sha256(control_path.read_bytes()).hexdigest(),'format_gate_removed':True,'scientific_states_changed':False})
print(json.dumps({'phase':control['workflow_phase'],'new_paper_admission_allowed':True,'science_unchanged':True}))
