"""Record exact verified progress delivery, preserving scientific publication state."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
PAIR=HERE.parent
ROOT=PAIR.parents[1]
MON=ROOT/'research-assets/incoming-paper-monitor'
path=PAIR/'live-progress-delivery-284017709231.json'
receipt=json.loads(path.read_bytes())
assert receipt['passed'] and receipt['site_commit']=='284017709231a7411c1e58fe0c3e62904332d01e'
assert len(receipt['checks'])==4 and all(r['matches_published_checkout'] for r in receipt['checks'])
target=MON/'latest-publication.json'
backup=HERE/'publication-before.json'
assert not backup.exists(), 'Preserve already recorded milestone'
backup.write_bytes(target.read_bytes())
release=json.loads(target.read_bytes())
control=json.loads((MON/'review-control.json').read_bytes())
assert release['record_count']==675 and release['synthesis_route_count']==123 and release['material_hub_count']==50
run=next(r for r in receipt['pages_runs'] if r['conclusion']=='success')
release.update(status='published_verified',commit_sha=receipt['site_commit'],recorded_at=receipt['verified_at'],
    published_at=receipt['verified_at'],progress_published_at=receipt['verified_at'],
    review_status=control['status'],review_phase=control['workflow_phase'],progress_only_update=True,
    publication_scope='Methods-first triage, daily schedule, and bounded shortlist progress; no scientific records or training pairs added.',
    prior_publication_checkpoint=str(backup),current_release_receipt={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()},
    deployment={'provider':'github_pages','status':'built','commit':receipt['site_commit'],'pages_run':run['id']},
    anonymous_verification={'authenticated':False,'cookies_used':False,'checks':receipt['checks']})
target.write_text(json.dumps(release,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
(HERE/'delivery-receipt.json').write_bytes(path.read_bytes())
memory=ROOT/'MEMORY.md'
heading='## 2026-09-22 — User changed MatterSyn automation to daily\n\n'
text=memory.read_text(encoding='utf8')
assert text.startswith(heading)
note=('Progress-only publication verified at '+receipt['verified_at']+': site commit '+receipt['site_commit']+
      ', GitHub Pages run '+str(run['id'])+'. Four public endpoints match exact deployment bytes without login. '
      'The daily schedule and Methods-first workflow are saved in project memory and the installed skill '
      '(incoming-corpus.md SHA256498d51ad67ce49e9483c8fef57798876173f55e124e7127ffdf3c3e9865834a4). '
      'Scientific dataset counts remain675records/123routes/50hubs and zero task-ready exact pairs.\n\n')
memory.write_text(heading+note+text[len(heading):],encoding='utf8')
print(json.dumps({'published_commit':receipt['site_commit'],'pages_run':run['id'],'science_added':0}))
