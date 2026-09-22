"""Project only the explicit restart/status files; never copy source workspaces."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, subprocess, sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
DEST=ROOT.parent/'mattersyn-github-project'
sys.path.insert(0,str(ROOT/'research-assets'))
import public_projection_policy as policy
GIT=r'C:\Program Files\Git\cmd\git.exe'
remote=subprocess.check_output([GIT,'-c','safe.directory='+DEST.as_posix(),'-C',str(DEST),'remote','get-url','origin']).decode().strip()
assert remote=='https://github.com/cuiyist/mattersyn.git'
files=[
    'MEMORY.md', 'skills/mattersyn-paper-to-site/references/incoming-corpus.md',
    'research-assets/public_projection_policy.py',
    'research-assets/incoming-paper-monitor/review-control.json',
    'research-assets/incoming-paper-monitor/ledger.json',
    'research-assets/incoming-paper-monitor/queue-status.json',
    'research-assets/incoming-paper-monitor/queue-status.md',
    'research-assets/incoming-paper-monitor/queue-status.html',
    'research-assets/incoming-paper-monitor/latest-publication.json',
    'research-assets/incoming-paper-monitor/public-progress-editorial.json',
    'research-assets/incoming-paper-monitor/build_public_progress.py',
    'research-assets/incoming-paper-monitor/deadline-20260920/active-cutoff.json',
    'research-assets/incoming-paper-monitor/batches/20260922-resumed-review/intake-manifest.json',
    'recipe-atlas/dist/index.html', 'recipe-atlas/dist/progress.html',
    'recipe-atlas/dist/data/review-progress.json']
for base in [OUT,ROOT/'research-assets/incoming-paper-monitor/deadline-20260920/resume-20260922']:
    files += [p.relative_to(ROOT).as_posix() for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts
              and p.suffix.lower() in {'.json','.md','.py'} and p.name!='project-sync-receipt.json']
# Verify the explicit private-source rule against the new packages and retain no raw data.
private_files=[p for p in (ROOT/'research-assets/incoming-paper-monitor/batches/20260922-resumed-review').rglob('*')
               if p.is_file() and 'private' in p.parts]
assert private_files and all(policy.exclude_path(p.relative_to(ROOT).as_posix()) for p in private_files)
assert policy.exclude_path('research-assets/example/private/pages/arbitrary-name.png')
assert policy.exclude_path('research-assets/example/private/full-text.json')
assert policy.exclude_path('research-assets/example/private/text/cache.txt')
assert policy.exclude_path('research-assets/example/source-render/page-1.png')
assert policy.exclude_path('research-assets/example/figures/fig1-tem.png') is None
rows=[]
for rel in sorted(set(files)):
    reason=policy.exclude_path(rel)
    if reason:
        rows.append({'path':rel,'excluded':reason});continue
    raw=(ROOT/rel).read_bytes()
    clean,stats=policy.project_bytes(rel,raw)
    assert len(clean)<100*1024*1024
    target=DEST/rel
    if not target.exists() or target.read_bytes()!=clean:
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(clean)
    rows.append({'path':rel,'sha256':hashlib.sha256(clean).hexdigest(),'projection':stats})
report={'created_at':datetime.now(timezone.utc).isoformat(),'scope':'Explicit restart/status allowlist; in-progress source packages not copied.',
        'private_source_files_checked_and_excluded':len(private_files),'policy':policy.POLICY_VERSION,'files':rows,'source_files_changed':False}
(OUT/'project-sync-receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps({'projected_files':len(rows),'private_files_excluded':len(private_files),'source_files_changed':False}))
