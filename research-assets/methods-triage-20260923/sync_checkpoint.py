"""Narrow source-free projection of the September23 Methods-first checkpoint."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'research-assets'))
import public_projection_policy as policy
GIT=r'C:\Program Files\Git\cmd\git.exe'
PAIR=ROOT/'research-assets/pair-priority-screen-20260922/atomic-shortlist-review'

files=[ROOT/x for x in ['MEMORY.md','research-assets/incoming-paper-monitor/review-control.json','research-assets/incoming-paper-monitor/public-progress-editorial.json','recipe-atlas/dist/index.html','recipe-atlas/dist/data/review-progress.json']]
files += [HERE/x for x in ['save_checkpoint.py','save_public_checkpoint.py','sync_checkpoint.py','screening-checkpoint.json','screened-scopes.json','README.md']]
for n in (1,2):
    d=HERE/f'mixed-batch-{n:02d}'
    files += [d/x for x in ['notes.json','freeze_screen.py','prepare_sources.py','batch-summary.json','author-freeze.json']]
    a=HERE/f'mixed-batch-{n:02d}-independent-check'
    files += [a/'independent-check.json']
    files += list(a.glob('*.py'))
    if (a/'source-role-hold.json').exists(): files.append(a/'source-role-hold.json')
    d=HERE/f'phase-batch-{n:02d}'
    files += [d/x for x in ['summary.json','README.md','author-freeze.json']]
    files += list(d.glob('scope-rank*.json')) + list(d.glob('*.py'))
    if (d/'exact-hash-reuse.json').exists():files.append(d/'exact-hash-reuse.json')
for rel in ['phase-batch-01-independent-check/independent-check.json','phase-batch-02-coordinate-check/independent-check.json','phase-batch-02-coordinate-check/bindings.json']:
    files.append(HERE/rel)
files += [PAIR/'batch-02-independent-audit/independent-audit.json']
for n in (3,4):
    d=PAIR/f'batch-{n:02d}'
    files += [d/x for x in ['summary.json','summary.md','author-freeze.json']]
    files += list(d.glob('*.py'))
for optional in ['delivery-receipt.json','record_delivery.py']:
    if (HERE/optional).exists():files.append(HERE/optional)
files=sorted(set(files))
for p in files:
    rel=p.relative_to(ROOT).as_posix()
    assert p.is_file(),rel
    assert policy.exclude_path(rel) is None,rel
    assert p.stat().st_size<3_000_000,rel
assert all('private' not in p.relative_to(ROOT).parts for p in files)
receipts=[]
for kind,dest,name in [('project',ROOT.parent/'mattersyn-github-project','mattersyn'),('site',ROOT.parent/'mattersyn-github-public-clean/mattersyn-site','mattersyn-site')]:
    cmd=[GIT,'-c','safe.directory='+dest.as_posix(),'-C',str(dest)]
    origin=subprocess.check_output(cmd+['remote','get-url','origin'],text=True).strip()
    assert origin=='https://github.com/cuiyist/'+name+'.git'
    selected=files if kind=='project' else [ROOT/'recipe-atlas/dist/index.html',ROOT/'recipe-atlas/dist/data/review-progress.json']
    for p in selected:
        rel=p.relative_to(ROOT).as_posix();raw,stats=policy.project_bytes(rel,p.read_bytes())
        outrel=rel if kind=='project' else rel.removeprefix('recipe-atlas/dist/')
        target=dest/outrel;target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists() or target.read_bytes()!=raw:target.write_bytes(raw)
        receipts.append({'kind':kind,'path':outrel,'sha256':hashlib.sha256(raw).hexdigest(),'projection':stats})
    subprocess.run(cmd+['-c','core.whitespace=cr-at-eol','diff','--check'],check=True)
report={'at':datetime.now(timezone.utc).isoformat(),'files':receipts,'policy_version':policy.POLICY_VERSION,'raw_sources_published':False,'science_added':0,'schedule':'daily_preserved'}
(HERE/'projection-receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps({'project_files':len(files),'site_files':2,'science_added':0,'raw_sources_published':False}))
