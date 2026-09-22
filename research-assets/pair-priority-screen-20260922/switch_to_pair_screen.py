"""Record the user's pair-first screening workflow; preserve current extraction packages."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys,hashlib
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
MON=ROOT/'research-assets/incoming-paper-monitor'
sys.path.insert(0,str(MON))
import monitor
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
now=datetime.now(timezone.utc).isoformat()
control=read(MON/'review-control.json')
if not (OUT/'previous-review-control.json').exists():write(OUT/'previous-review-control.json',control)
control.update(recorded_at=now,workflow_phase='corpus_pair_screen_before_new_website_builds',
               user_instruction='Screen all existing papers first and identify high-quality synthesis–structure pairs; then prioritize those papers for websites.',
               new_paper_admission_allowed=False,
               admission_hold_reason='Temporary workflow gate: finish pair-oriented corpus screening and independent ranking checks before admitting further full website builds. Existing source packages retained.',
               remaining_time_estimate='Re-estimate after verified pair-candidate count and complexity are known. October22 remains a target, not an all-paper curation promise.',
               paid_api_pilot='deferred_pending_screened_priority_workload_and_user_resource_decision')
write(MON/'review-control.json',control)
batch=MON/'batches/20260922-resumed-review'
for group,folder,freeze_sha in [
    ('legacy::10.1021_acsami.8b04556','legacy--10.1021_acsami.8b04556--261eafeba8a3','ab044e25cb405b9358298029de529f07bd3e30982d1d58818f0d20e74cbf7d37'),
    ('legacy::10.1021_acsami.3c08812','legacy--10.1021_acsami.3c08812--6a1ca8cf812d','913a7767472f90d495b8733e590ca6f16ec80124ce3f79c8e77925c9f797a3b1')]:
    paper=batch/folder;freeze=paper/'author-freeze-v1.json'
    assert hashlib.sha256(freeze.read_bytes()).hexdigest()==freeze_sha
    milestones={stage:{'status':'complete','evidence':[str(freeze)],'note':'Source author reports complete supplied main/SI text and visual coverage plus frozen extraction; independent audit is tracked separately.'} for stage in ('read','extract')}
    if '8b04556' in group:
        audit=paper/'source-independent-audit/independent-audit.json'
        assert hashlib.sha256(audit.read_bytes()).hexdigest()=='90e7c1683ae8be5cf8fc562299df520917be9280cd7a00ee7615bd409f9a8678'
        milestones['audit']={'status':'complete','evidence':[str(audit)],'note':'Independent complete source extraction audit passed; canonical/model/task/website approvals remain separate pending gates.'}
    monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id=group,status='in_progress',milestones=milestones,
        note='Preserve frozen source work; user now prioritizes corpus-wide pair screening before further website builds.',
        data={'source_freeze':str(freeze),'source_freeze_sha256':freeze_sha,
              'si_status':'Complete supplied main and content-matched local SI read by extractor; see separate independent-audit status.',
              'next_action':'Use the preserved package in pair-quality screening; hold new canonical/website builds until corpus ranking is reviewed.',
              'current_work_items':[{'label':'Pair-oriented corpus screening','status':'in_progress','scope':'Corpus-wide candidate ranking and source-validity checks; preserved current paper source package.'}]})
editorial=read(MON/'public-progress-editorial.json')
editorial['workflow']['summary']='Screen the full fixed collection for high-quality synthesis–structure pairs first, then build readers for the strongest verified contributions. Prior keyword screening is being upgraded with source validity, recipe completeness, structure type and explicit specimen–recipe linkage checks.'
editorial['workflow']['capacity']='Existing extraction packages are preserved. Workers are preparing the pair-quality ranker, independent rubric/benchmark checks and source-validity exceptions before further website builds.'
editorial['workflow']['steps']=[
    'Account for every fixed-cutoff main/SI source and retain invalid, missing or mispaired documents as explicit unresolved cases.',
    'Rank measured/refined atomic-structure candidates with usable recipes first; keep phase, size and morphology-linked recipes as a separate useful tier.',
    'Verify top candidates against the original main/SI: the structure and recipe must describe a supported shared sample or formulation.',
    'Retain all screened candidates and gaps; external reference cells, simulations and molecular-precursor coordinates do not become measured product pairs.',
    'Build and publish academic material readers only after the selected paper’s source, data, figure and independent audit gates pass.']
editorial['estimate']['status']='recalibrating_after_pair_priority_screen'
editorial['estimate']['summary']='October22 remains the requested target. The immediate milestone is a complete pair-oriented screen of the fixed collection, followed by verified priority candidates for website curation. A revised finish estimate will use the number and complexity of eligible papers; the old19–28month extrapolation assumed comparable full curation for every provisional group and is not a forecast for this priority workflow.'
editorial['estimate']['current_batch']='Chen’s18-page main/SI source package passed its separate independent audit. Saini’s119-page extraction is frozen and awaiting independent audit. Both are preserved while pair-oriented screening is completed; neither new contribution is published yet.'
editorial['estimate']['scenarios']=[]
editorial['estimate']['notes']=[
    'Screened candidate, source-verified pair, independently audited contribution and published record are separate states.',
    'A strong pair needs useful synthesis conditions and a defensible link to the characterized specimen. Atomic coordinates have highest priority, while phase/size/morphology pairs remain separately useful.',
    'Identical promotional or error payloads under unrelated filenames do not establish duplicate paper identity or scientific completion. Source-role and identity exceptions remain visible.',
    'The existing collection contains13,831top-level document copies and three nested identity cases. Later-arrival papers remain separate.',
    'Screening all papers and publishing a selected priority subset is not the same as completing full curation of every paper. Remaining work will be reported explicitly.',
    'Paid API processing remains unapproved. Additional capacity can be considered after the verified priority workload is known.']
for work in editorial['current_work']:
    chen=work['short_label'].startswith('Chen')
    work['stage']='Source audit passed; retained for pair screening' if chen else 'Extraction frozen; retained for pair screening'
    work['stages'][0]['status']='complete';work['stages'][0]['detail']='Complete supplied main/SI text and visual coverage recorded.'
    work['stages'][1]['status']='complete';work['stages'][1]['detail']='Hash-bound source extraction package saved; no canonical or website promotion.'
    work['stages'][2]['status']='complete' if chen else 'pending'
    work['stages'][2]['detail']='Separate complete source audit passed; downstream gates remain pending.' if chen else 'Distinct independent source audit remains pending.'
    work['stages'][3]['detail']='Deferred until the pair-oriented corpus ranking has been checked.'
editorial['recent_milestones'].insert(0,{'at':now,'text':'Workflow changed at the user’s request: screen every source in the fixed collection for usable synthesis–structure pairs before further website builds. Chen source extraction passed its independent audit; Saini complete main/SI extraction is preserved for later audit. No new scientific records published.'})
write(MON/'public-progress-editorial.json',editorial)
decision={'at':now,'scope':'Fixed September20collection; new arrivals separate','phase':control['workflow_phase'],
          'priority_tiers':['Candidate measured/refined sample atomic structures plus usable synthesis','Candidate linked product phase/size/morphology plus usable synthesis','Recipe-bearing but limited or unlinked structure evidence','No usable recipe or invalid/missing source; independent disposition required'],
          'no_automatic_verified_pairs':True,'no_automatic_exclusions':True,'existing_work_preserved':True,
          'unapproved_paid_jobs_started':False,'target':'2026-10-22','eta':'Recalibrate after evidence-linked screening and priority verification.'}
write(OUT/'decision.json',decision)
print(json.dumps({'phase':control['workflow_phase'],'preserved_source_packages':2,'new_website_builds_on_hold':True,'scientific_records_added':0}))
