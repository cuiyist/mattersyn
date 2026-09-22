"""Record the user-authorized restart; no scientific milestone is completed here."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys

ROOT = Path(__file__).resolve().parents[2]
MON = ROOT / 'research-assets/incoming-paper-monitor'
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(MON))
import monitor

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')

def binding(path):
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

now = datetime.now(timezone.utc).isoformat()
control_path = MON / 'review-control.json'
old = read(control_path)
backup = OUT / 'review-control-before-resume.json'
if not backup.exists():
    write(backup, old)
ledger = monitor.read_ledger(MON / 'ledger.json')
claims = monitor.active_claims(ledger)
assert len(claims) == 2
assert {c['group_id'] for c in claims} == {'legacy::10.1021_acsami.3c08812', 'legacy::10.1021_acsami.8b04556'}
write(control_path, {
    **old, 'status': 'active_fixed_cutoff_review', 'recorded_at': now,
    'user_instruction': 'Proceed with the rest of the papers and SI using the improved website standard; estimate rough completion time.',
    'interpretation': 'Resume fixed-cutoff corpus review; the prior pause is superseded. Later arrivals remain separate.',
    'active_group_ids': [c['group_id'] for c in claims],
    'new_paper_admission_allowed': True, 'resume_requires_user_instruction': False,
    'automation_current_action': 'Existing heartbeat resumed through automation_update; saved receipt confirms ACTIVE.',
    'automation_resume_receipt': str(OUT / 'automation-resume-receipt.json'),
    'remaining_time_estimate': 'Recalibrating from nine newly admitted published scopes; see the dated ETA report.',
    'estimate_scope': 'The frozen September 20 collection only; post-cutoff papers are queued separately.',
    'previous_pause_checkpoint': str(backup), 'paid_api_pilot': 'deferred'
})
partition_path = MON / 'deadline-20260920/resume-20260922/resume-partition.json'
partition = read(partition_path)
active_path = MON / 'deadline-20260920/active-cutoff.json'
active = read(active_path)
active.update(recorded_at=now, counts=partition['counts'], latest_scope_partition=binding(partition_path),
              current_activation=binding(MON / 'deadline-20260920/resume-20260922/activation/activation-proof.json'))
write(active_path, active)

intake = read(MON / 'batches/20260922-resumed-review/intake-manifest.json')
for paper in intake['papers']:
    monitor.checkpoint(MON / 'ledger.json', 'mattersyn-primary', group_id=paper['paper_id'],
        status='in_progress', note='User-authorized resumed review; hashed main/SI bundle assigned to extractor. No scientific completion claimed.',
        data={'review_directory': paper['review_directory'],
              'intake_manifest': str(MON / 'batches/20260922-resumed-review/intake-manifest.json'),
              'si_status': 'Local supplement candidate present; content pairing and full coverage under review.',
              'next_action': 'Complete source reading and extraction, then obtain a distinct independent source/sample audit before integration.',
              'current_work_items': [{'label':'Full main/SI review and extraction','status':'in_progress','scope':'Separate paper-specific package; no new scientific release yet.'}]},
        milestones={'read': {'status':'partial','evidence':[str(MON / 'batches/20260922-resumed-review/intake-manifest.json')],
                             'note':'Intake hashes checked; complete text/visual reading remains in progress.'}})

# Refresh a stale scientific-version checkpoint from the already verified UI release.
release_path = MON / 'latest-publication.json'
release = read(release_path)
old_release = OUT / 'publication-checkpoint-before-resume.json'
if not old_release.exists():
    write(old_release, release)
receipt_path = ROOT / 'research-assets/morphology-preferences-20260922/live-delivery.json'
receipt = read(receipt_path)
manifest = read(ROOT / 'recipe-atlas/dist/data/dataset-manifest.json')
assert receipt['deployment'] == 'success' and manifest['record_count'] == release['record_count'] == 675
release.update(dataset_version=manifest['dataset_version'], reader_version=receipt['reader_version'],
    public_live_version='GitHub Pages / dataset0.34.0 / Reader0.34.1',
    recorded_at=now, published_at=receipt['verified_at'], commit_sha=receipt['site_commit'],
    new_source_ids=[], remaining_batch_papers=2, current_active_paper_claims=2,
    publication_scope='Already verified all-material Reader and morphology release; no new source contribution in this checkpoint refresh.',
    prior_publication_checkpoint=str(old_release), current_release_receipt=binding(receipt_path))
release.pop('anonymous_verification', None)
release.pop('project_commit_sha', None)
release['deployment']={'provider':'github_pages','status':'built','commit':receipt['site_commit'],'pages_run':receipt['pages_run']}
write(release_path, release)
print(json.dumps({'status':'resumed','active_claims':len(claims),'fixed_pending_scopes':partition['counts']['included_pending_scopes'],
                  'later_scopes':partition['counts']['later_arrival_group_candidates'], 'scientific_records_added':0}))
