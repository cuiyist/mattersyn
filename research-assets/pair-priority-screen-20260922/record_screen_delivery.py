"""Record a verified progress-only delivery without changing scientific counts."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MONITOR = HERE.parent/'incoming-paper-monitor'
receipt_path = HERE/'live-progress-delivery-79cd5205ea15.json'
receipt = json.loads(receipt_path.read_bytes())
assert receipt['passed'] and receipt['site_commit'] == '79cd5205ea15982be2c2b6ffe9f1b00fa9dc5d28'
run = next(r for r in receipt['pages_runs'] if r['conclusion'] == 'success')
target = MONITOR/'latest-publication.json'
backup = HERE/'publication-before-accepted-screen.json'
assert not backup.exists(), 'Delivery checkpoint already recorded'
backup.write_bytes(target.read_bytes())
release = json.loads(target.read_bytes())
control_path = MONITOR/'review-control.json'
control = json.loads(control_path.read_bytes())
activation_path = HERE/'activation-20260922/activation-proof.json'
activation = json.loads(activation_path.read_bytes())
assert activation['activated'] and not activation['scientific_statuses_changed']
control['nomination_policy_activation'] = {'at': activation['at'], 'ranked_scopes': activation['ranked_scopes'],
    'held_scopes': activation['held_scopes'], 'proof_sha256': hashlib.sha256(activation_path.read_bytes()).hexdigest()}
control_path.write_text(json.dumps(control, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
release.update(status='published_verified', commit_sha=receipt['site_commit'],
    recorded_at=receipt['verified_at'], published_at=receipt['verified_at'],
    progress_published_at=receipt['verified_at'], review_status=control['status'],
    review_phase=control['workflow_phase'], progress_only_update=True,
    publication_scope='Verified automated-screening progress and remaining source gaps; no new scientific records.',
    prior_publication_checkpoint=str(backup),
    current_release_receipt={'path': str(receipt_path), 'sha256': hashlib.sha256(receipt_path.read_bytes()).hexdigest()},
    deployment={'provider':'github_pages', 'status':'built', 'commit':receipt['site_commit'], 'pages_run':run['id']},
    anonymous_verification={'authenticated':False,'cookies_used':False,'checks':receipt['checks']})
target.write_text(json.dumps(release, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
memory = ROOT/'MEMORY.md'
text = memory.read_text(encoding='utf8')
note = ('Progress-only delivery verified at '+receipt['verified_at']+': site commit '+receipt['site_commit']+
        ', GitHub Pages run '+str(run['id'])+'. Four anonymous public artifacts match the isolated checkout. '
        'Scientific counts remain 675 records, 123 routes and 50 hubs. The checked nomination policy ranks 9,496 scopes and holds 36 source/generation cases; claims and scientific statuses are unchanged. '
        'The existing heartbeat is ACTIVE for safe format recovery and bounded priority-source checks, with further full website admissions held. '
        'Memory and reusable skill instructions include source-benchmark sensitivity, cache-binding limits and raw-cue exclusion.\n\n')
heading = '## 2026-09-22 — Accepted automated pair nominations; manual screening continues\n\n'
assert text.startswith(heading)
memory.write_text(heading+note+text[len(heading):], encoding='utf8')
print(json.dumps({'site_commit':receipt['site_commit'], 'pages_run':run['id'], 'scientific_records_added':0, 'prior_receipt_preserved':True}))
