"""Synchronize only reviewed deadline/progress files to the existing public projections."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys,hashlib,subprocess
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT/'research-assets'))
import public_projection_policy as policy
GIT=r'C:\Program Files\Git\cmd\git.exe'
files=['MEMORY.md','skills/mattersyn-paper-to-site/references/incoming-corpus.md',
       'research-assets/incoming-paper-monitor/review-control.json',
       'research-assets/incoming-paper-monitor/deadline-20260920/active-cutoff.json',
       'research-assets/incoming-paper-monitor/public-progress-editorial.json',
       'recipe-atlas/dist/data/review-progress.json']
names=['ACCELERATION_PLAN.md','decision.json','inspect_duplicate_work.py','duplicate-work-opportunities.json',
       'previous-deadline-state.json','automation-update-receipt.json','update_target.py','sync_deadline_snapshot.py']
files += ['research-assets/one-month-20260922/'+name for name in names]
results=[]
for kind,dest,expected in [('project',ROOT.parent/'mattersyn-github-project','mattersyn'),
                          ('site',ROOT.parent/'mattersyn-github-public-clean/mattersyn-site','mattersyn-site')]:
    origin=subprocess.check_output([GIT,'-c','safe.directory='+dest.as_posix(),'-C',str(dest),'remote','get-url','origin']).decode().strip()
    assert origin=='https://github.com/cuiyist/'+expected+'.git'
    selected=files if kind=='project' else ['recipe-atlas/dist/data/review-progress.json']
    for rel in selected:
        assert policy.exclude_path(rel) is None
        raw,stats=policy.project_bytes(rel,(ROOT/rel).read_bytes())
        target=dest/(rel if kind=='project' else rel.removeprefix('recipe-atlas/dist/'))
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        results.append({'kind':kind,'path':rel,'sha256':hashlib.sha256(raw).hexdigest(),'projection':stats})
(OUT/'projection-receipt.json').write_text(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'original_sources_uploaded':False,'files':results},indent=2)+'\n',encoding='utf8')
print(json.dumps({'project_files':len(files),'site_files':1,'source_packages_copied':False}))
