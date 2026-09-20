"""Commit the already checked private and public staging repositories."""
from pathlib import Path
from datetime import datetime,timezone
import json,shutil,subprocess
ROOT=Path('[local path redacted]')
PRIVATE=ROOT.parent/'mattersyn-github-private'
PUBLIC=ROOT.parent/'mattersyn-github-public/mattersyn-site'
GIT=r'C:\Program Files\Git\cmd\git.exe'
def git(repo,*args):
    p=subprocess.run([GIT,*args],cwd=repo,capture_output=True,text=True,encoding='utf8',errors='replace')
    if p.returncode:raise SystemExit(f'Git {args[0]} failed in {repo.name}; no credentials logged.')
    return p.stdout.strip()
report_path=ROOT/'research-assets/github-packaging-manifest.json'
report=json.loads(report_path.read_text(encoding='utf8'))
report['included_files']=[e for e in report['included_files'] if e['path']!='research-assets/github-packaging-manifest.json']
report['manifest_self_excluded_from_hash_list']=True
report_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
for name in ['github-packaging-manifest.json','github-staging-checkpoint.json','github-history-audit.json',
             'audit_github_history.py','commit_github_staging.py']:
    shutil.copyfile(ROOT/'research-assets'/name,PRIVATE/'research-assets'/name)
for repo,name in [(PRIVATE,'mattersyn'),(PUBLIC,'mattersyn-site')]:
    git(repo,'config','user.name','Yi Cui')
    git(repo,'config','user.email','147659097+cuiyist@users.noreply.github.com')
    git(repo,'config','core.autocrlf','false')
    git(repo,'config','core.longpaths','true')
    remotes=git(repo,'remote').splitlines()
    if 'origin' not in remotes:git(repo,'remote','add','origin',f'https://github.com/cuiyist/{name}.git')
    elif git(repo,'remote','get-url','origin')!=f'https://github.com/cuiyist/{name}.git':
        raise SystemExit('Unexpected repository destination; stopped.')
    git(repo,'add','--all')
    git(repo,'commit','--quiet','-m',
        'Back up MatterSyn project, curation history, memory and skills' if name=='mattersyn'
        else 'Publish MatterSyn atlas dataset 0.23.0 on GitHub Pages')
    print(json.dumps({'repository':name,'commit':git(repo,'rev-parse','HEAD'),
        'files':len(git(repo,'ls-files').splitlines())}),flush=True)
