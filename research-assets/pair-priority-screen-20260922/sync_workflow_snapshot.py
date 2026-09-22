"""Publish explicit workflow/checkpoint changes, not unfrozen screening output or source text."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,subprocess
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT/'research-assets'))
import public_projection_policy as policy
GIT=r'C:\Program Files\Git\cmd\git.exe'
files=['MEMORY.md','skills/mattersyn-paper-to-site/references/incoming-corpus.md',
       'research-assets/public_projection_policy.py',
       'research-assets/incoming-paper-monitor/review-control.json','research-assets/incoming-paper-monitor/ledger.json',
       'research-assets/incoming-paper-monitor/queue-status.json','research-assets/incoming-paper-monitor/queue-status.md','research-assets/incoming-paper-monitor/queue-status.html',
       'research-assets/incoming-paper-monitor/public-progress-editorial.json',
       'recipe-atlas/dist/data/review-progress.json']
files += ['research-assets/pair-priority-screen-20260922/'+name for name in ['switch_to_pair_screen.py','previous-review-control.json','decision.json','automation-update-receipt.json','sync_workflow_snapshot.py']]
files += ['research-assets/one-month-20260922/duplicate-audit/'+name for name in ['SUMMARY.md','duplicate-audit-freeze-v1.json','safe-reuse-candidates.json','unresolved-identities-and-roles.json','pair-source-validity-overlay.json']]
report=[]
for kind,dest,repo in [('project',ROOT.parent/'mattersyn-github-project','mattersyn'),('site',ROOT.parent/'mattersyn-github-public-clean/mattersyn-site','mattersyn-site')]:
    origin=subprocess.check_output([GIT,'-c','safe.directory='+dest.as_posix(),'-C',str(dest),'remote','get-url','origin']).decode().strip()
    assert origin=='https://github.com/cuiyist/'+repo+'.git'
    for rel in files if kind=='project' else ['recipe-atlas/dist/data/review-progress.json']:
        assert policy.exclude_path(rel) is None
        clean,stats=policy.project_bytes(rel,(ROOT/rel).read_bytes())
        target=dest/(rel if kind=='project' else rel.removeprefix('recipe-atlas/dist/'))
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(clean)
        report.append({'kind':kind,'path':rel,'sha256':hashlib.sha256(clean).hexdigest(),'projection':stats})
for rel in ['research-assets/a/private/text.json','research-assets/a/private-text/main.txt','research-assets/a/private-pages/unusual.png','research-assets/a/private-render-220/combined.webp']:
    assert policy.exclude_path(rel)=='explicit_private_source_workspace'
(OUT/'public-projection-receipt.json').write_text(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'files':report,'original_sources_uploaded':False},indent=2)+'\n',encoding='utf8')
print(json.dumps({'project_files':len(files),'site_files':1,'source_packages_or_unfrozen_screen_output_copied':False}))
