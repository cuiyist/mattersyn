"""Prepare a dated public restart snapshot without changing scientific records."""
from pathlib import Path
from datetime import datetime, timezone
import json

ROOT = Path(__file__).resolve().parents[2]
MON = ROOT / 'research-assets/incoming-paper-monitor'
now = datetime.now(timezone.utc).isoformat()
path = MON / 'public-progress-editorial.json'
d = json.loads(path.read_text(encoding='utf8'))
original = Path(__file__).resolve().parent / 'progress-editorial-before-resume.json'
if not original.exists():
    original.write_text(json.dumps(d, ensure_ascii=False, indent=2)+'\n', encoding='utf8')

def current(label, title, summary):
    return {'short_label':label, 'title':title, 'stage':'Main/SI review and extraction', 'summary':summary,
            'stages':[
                {'label':'Source reading and pairing','status':'in_progress','detail':'Local main and supplement identities checked; complete coverage documented in the paper package.'},
                {'label':'Structured extraction','status':'in_progress','detail':'Recipes, variants, figures, specimen assignments and unresolved details being recorded.'},
                {'label':'Independent audit','status':'pending','detail':'A distinct reviewer checks the frozen paper-specific evidence package.'},
                {'label':'Reader and dataset integration','status':'pending','detail':'Shared illustrations and Reader standard; source-specific conditions and specimen links checked.'},
                {'label':'Publication','status':'pending','detail':'Publish only after required scientific and website checks pass.'}]}

d['current_work']=[
    current('Saini et al. (2023)', 'Natural amine-targeted carbon quantum dots and nanoaminocatalysis',
            '12-page main article and 107-page matched supplement. Carbon-dot preparation, catalytic protocols, characterization and product spectra are being reviewed; this is not a published contribution yet.'),
    current('Chen et al. (2018)', 'Cs₄PbBr₆/CsPbBr₃ composites: synthesis, luminescence and formation mechanism',
            '8-page main article and 10-page matched supplement. Composite variants, a separate CsPbBr₃ comparison route, scale-up and device preparation are being extracted. Refined/fixed coordinate tables require sample- and phase-specific qualification.')]
d['estimate']={
    'status':'active_with_conditional_estimate',
    'summary':'About 9,500 unfinished provisional scopes remain in the fixed collection. Nine newly admitted scopes reached verified publication over 12.87 elapsed hours in the last observed run (0.70 scopes/hour). If every remaining scope required similar work, the linear extrapolation is about 19 months at continuous throughput, or 28 months at 16 equivalent hours/day. These are conditional planning scenarios, not validated completion forecasts.',
    'current_batch':'Two paper/SI bundles are now in review. One includes a 107-page supplement, so the recent short cohort does not establish a reliable completion time for this pair.',
    'scenarios':[
        {'label':'Observed cadence sustained continuously (hypothetical)','reviews_per_day':'16.79','duration':'About 566 days / 19 months'},
        {'label':'Observed cadence for 16 equivalent hours/day','reviews_per_day':'11.19','duration':'About 849 days / 28 months'},
        {'label':'Observed cadence for 8 equivalent hours/day','reviews_per_day':'5.60','duration':'About 1,698 days / 56 months'}],
    'notes':[
        'The denominator includes provisional groups, unresolved pairings and potential duplicates. It is not 9,500 verified distinct recipe papers. Two are active; 9,498 are waiting within the fixed collection.',
        'The throughput sample comprises nine newly admitted, selected evidence-rich scopes, eight with supplied main/SI and one with unverified SI. It excludes an older carry-over paper. Elapsed publication cadence is not measured active compute time or a guarantee of continuous execution.',
        'Duplicates and independently evidenced no-recipe exclusions may shorten the total; their eventual yield and handling time are not measured. Complex supplements, corrections and interruptions may lengthen it.',
        'The fixed collection contains 13,831 top-level document copies plus three nested identity cases. A closure is a retained contribution passing its stated review and publication gates, or an independently audited exclusion with its reason retained.',
        'Later arrivals are separate: 3,136 provisional groups and 3,777 file copies in this scan. Late or changed evidence for an included paper reopens the affected review.',
        'The original November 20 target would require roughly 163 closures/day from this snapshot. Current observed capacity does not support that target. No paid API processing has been started.',
        'Local recurring work depends on host/app availability. Estimates will be recalibrated from subsequent audited closures, not from automated screening speed.']}
d['workflow'].update(
    summary='Corpus review has resumed at the user’s request. Screened synthesis/structure-rich papers are being read and extracted in parallel, with separate audits before shared Reader integration and batched publication.',
    capacity='Two active paper claims; up to five may be held in the rolling queue. The available runtime supports four agents including the integration owner, so extraction and independent audits share those worker slots.',
    fixed_pending_provisional_scopes=9500, scope_counts_updated_at=now,
    later_arrival_groups_current=3136, later_arrival_file_candidates_current=3777)
event={'at':now,'text':'Review resumed after the website revision. The fixed-cutoff ranking was refreshed and two main/SI bundles were assigned: Saini2023 carbon dots and Chen2018 perovskite composites. Original source names and hashes are preserved; 3,136 later-arrival scopes remain separate. No additional scientific records are published in this progress update.'}
d['recent_milestones'].insert(0,event)
path.write_text(json.dumps(d, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(json.dumps({'active_papers':len(d['current_work']),'scientific_records_added':0,'updated_at':now}))
