"""Sync project work into the private GitHub checkout; never includes raw papers or dependencies."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib,json,os,re,shutil,subprocess
ROOT=Path('[local path redacted]');DEST=ROOT.parent/'mattersyn-github-private'
GIT=r'C:\Program Files\Git\cmd\git.exe'
SKIP={'.git','node_modules','__pycache__','.sites-runtime','rdkit-runtime','runtime','python-packages','.venv','venv','validation-runtime','downloaded_papers'}
SUFFIX={'.pdf','.doc','.docx','.ppt','.pptx','.zip','.7z','.rar','.pem','.key','.pfx','.p12'}
TEXT={'.py','.js','.mjs','.json','.jsonl','.html','.css','.md','.txt','.toml','.yaml','.yml','.xml','.csv','.tsv'}
SECRETS=[re.compile(p) for p in [rb'gh[opusr]_[A-Za-z0-9]{30,}',rb'github_pat_[A-Za-z0-9_]{50,}',rb'(?<![A-Za-z])sk-[A-Za-z0-9_-]{35,}',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']]
def git(*args):
    p=subprocess.run([GIT,*args],cwd=DEST,capture_output=True,text=True,encoding='utf8',errors='replace')
    if p.returncode:raise SystemExit(f'Git {args[0]} failed; stopped without logging credential details.')
    return p.stdout.strip()
assert git('remote','get-url','origin')=='https://github.com/cuiyist/mattersyn.git'
if git('status','--porcelain'):raise SystemExit('Private checkout has uncommitted edits; inspect before synchronizing.')
paths=[]
for directory,dirs,files in os.walk(ROOT):
    dirs[:]=[d for d in dirs if d not in SKIP]
    for name in files:
        p=Path(directory)/name
        if p.suffix.lower() in SUFFIX or name.endswith(('.tar.gz','.tar','.bundle')) or name=='.env' or name.startswith('.env.') or p.is_symlink():continue
        if p==ROOT/'research-assets/github-private-sync-report.json':continue
        paths.append(p)
def compare(p):
    rel=p.relative_to(ROOT);target=DEST/rel;source=p.read_bytes()
    digest=hashlib.sha256(source).hexdigest()
    if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest()==digest:return None
    if len(source)>=100*1024*1024:raise RuntimeError('Updated project file exceeds GitHub limit: '+str(rel))
    if p.suffix.lower() in TEXT and any(pattern.search(source) for pattern in SECRETS):raise RuntimeError('Possible literal credential in '+str(rel)+'; stopped without logging contents.')
    return {'path':rel.as_posix(),'sha256':digest,'bytes':len(source)}
with ThreadPoolExecutor(max_workers=12) as pool:
    changes=[x for x in pool.map(compare,paths) if x]
for change in changes:
    target=DEST/change['path'];target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/change['path'],target)
report={'at':datetime.now(timezone.utc).isoformat(),'project_files_compared':len(paths),'changed_or_added_files':changes,
    'deletions_performed':False,'repository':'cuiyist/mattersyn','visibility_required':'private',
    'public_repository_touched':False,'source_documents_uploaded':False}
out=ROOT/'research-assets/github-private-sync-report.json';out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
shutil.copyfile(out,DEST/'research-assets/github-private-sync-report.json')
git('add','--all');git('commit','--quiet','-m','Save verified GitHub publication, current review queue and project memory')
print(json.dumps({'files_compared':len(paths),'files_updated':len(changes),'commit':git('rev-parse','HEAD')},indent=2))
