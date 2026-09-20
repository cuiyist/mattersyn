"""Prepare isolated private backup and public Pages trees; original project stays in place."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib, json, os, re, shutil, subprocess
from concurrent.futures import ThreadPoolExecutor

ROOT = Path('[local path redacted]')
PRIVATE = ROOT.parent/'mattersyn-github-private'
PUBLIC = ROOT.parent/'mattersyn-github-public'/'mattersyn-site'
GIT = r'C:\Program Files\Git\cmd\git.exe'
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.sites-runtime', 'rdkit-runtime',
    'runtime', 'python-packages', '.venv', 'venv', 'validation-runtime', 'downloaded_papers'}
SOURCE_SUFFIXES = {'.pdf', '.doc', '.docx', '.ppt', '.pptx', '.zip', '.7z', '.rar'}
SECRET_PATTERNS = [re.compile(p) for p in [
    rb'gh[opusr]_[A-Za-z0-9]{30,}', rb'github_pat_[A-Za-z0-9_]{50,}',
    rb'(?<![A-Za-z])sk-[A-Za-z0-9_-]{35,}', rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']]
TEXT_SUFFIXES = {'.py','.js','.mjs','.json','.jsonl','.html','.css','.md','.txt','.toml','.yaml','.yml','.xml','.csv','.tsv'}

def git(*args, cwd=None):
    result = subprocess.run([GIT,*args], cwd=cwd, capture_output=True, text=True, encoding='utf8', errors='replace')
    if result.returncode:
        raise RuntimeError(f'Git command failed: {args[0]} (details withheld from packaging logs)')
    return result.stdout.strip()

def excluded(path):
    rel=path.relative_to(ROOT)
    if any(part in SKIP_DIRS for part in rel.parts): return 'raw_source_or_runtime_directory'
    if path.suffix.lower() in SOURCE_SUFFIXES or path.name.endswith(('.tar.gz','.tar','.bundle')): return 'raw_document_or_redundant_archive'
    if path.name == '.env' or path.name.startswith('.env.') or path.suffix.lower() in {'.pem','.key','.pfx','.p12'}: return 'credential_configuration'
    return None

if PRIVATE.exists() or PUBLIC.exists():
    raise SystemExit('Staging already exists; inspect and update it without overwriting history.')
included=[]; omitted=[]; findings=[]; candidates=[]
for directory, dirs, files in os.walk(ROOT):
    for name in list(dirs):
        if name in SKIP_DIRS:
            omitted.append({'path':(Path(directory)/name).relative_to(ROOT).as_posix()+'/', 'reason':'raw_source_or_runtime_directory'})
            dirs.remove(name)
    for name in files:
        path=Path(directory)/name; rel=path.relative_to(ROOT).as_posix(); reason=excluded(path)
        if reason:
            omitted.append({'path':rel,'reason':reason}); continue
        if path.is_symlink():
            omitted.append({'path':rel,'reason':'external_or_symbolic_link'}); continue
        candidates.append(path)
def scan(path):
    raw=path.read_bytes(); rel=path.relative_to(ROOT).as_posix(); flagged=[]
    if len(raw)>=100*1024*1024:flagged.append({'path':rel,'reason':'exceeds_github_file_limit'})
    if path.suffix.lower() in TEXT_SUFFIXES or path.name in {'.gitignore','.gitattributes'}:
        if any(pattern.search(raw) for pattern in SECRET_PATTERNS):flagged.append({'path':rel,'reason':'possible_literal_secret'})
    return {'path':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}, flagged
with ThreadPoolExecutor(max_workers=12) as pool:
    for index,(entry,flagged) in enumerate(pool.map(scan,candidates),1):
        included.append(entry);findings.extend(flagged)
        if index%10000==0:print(f'Checked {index} project files.',flush=True)
report={'created_at':datetime.now(timezone.utc).isoformat(), 'source_root':str(ROOT),
    'private_repository':'cuiyist/mattersyn', 'public_repository':'cuiyist/mattersyn-site',
    'source_site_head':git('rev-parse','HEAD',cwd=ROOT/'recipe-atlas'),
    'source_site_history_commits':int(git('rev-list','--count','HEAD',cwd=ROOT/'recipe-atlas')),
    'included_files':included,'excluded_paths':omitted,'findings':findings,
    'file_count':len(included),'total_bytes':sum(x['bytes'] for x in included)}
out=ROOT/'research-assets/github-packaging-manifest.json'
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
if findings:
    print(json.dumps({'findings':findings,'files':len(included)},indent=2));raise SystemExit(2)

# The prior Site history remains ancestry; the first new commit reorganizes it under recipe-atlas/.
git('clone','--no-local','--no-checkout',str(ROOT/'recipe-atlas'),str(PRIVATE))
git('remote','remove','origin',cwd=PRIVATE)
git('branch','-M','main',cwd=PRIVATE)
git('read-tree','--empty',cwd=PRIVATE)
def copy_entry(entry):
    target=PRIVATE/entry['path'];target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/entry['path'],target)
with ThreadPoolExecutor(max_workers=12) as pool:
    for index,_ in enumerate(pool.map(copy_entry,included),1):
        if index%10000==0:print(f'Copied {index} private project files.',flush=True)
shutil.copyfile(out, PRIVATE/'research-assets/github-packaging-manifest.json')
(PRIVATE/'README.md').write_text('''# MatterSyn research project

Private project backup for the MatterSyn materials synthesis atlas.

- `recipe-atlas/`: source application, structured dataset, validators and website assets.
- `research-assets/`: source-linked extraction work, coverage records, independent audits, queue and scientific review history.
- `skills/`: reusable MatterSyn curation and publishing workflow.
- `MEMORY.md`: project decisions, progress and unresolved work.

The original website Git history is preserved as ancestry. Earlier commits use the website files at repository root; this backup places the current application in `recipe-atlas/`.

The public website is published separately at https://cuiyist.github.io/mattersyn-site/ from https://github.com/cuiyist/mattersyn-site . Keep this project repository private.

Downloaded paper PDFs and SI, redundant deployment archives, credentials and installed dependencies stay local. Structured extraction outputs and audit evidence are preserved here. See `research-assets/github-packaging-manifest.json` for the explicit file and exclusion inventory. Paths in historical evidence manifests identify the original workstation and are provenance, not portable installation paths.

Current website code is in `recipe-atlas/dist`. See `recipe-atlas/README.md` and `recipe-atlas/requirements-data.txt` for its build/check workflow. A backup is not a claim that every indexed paper has been fully reviewed; consult the current memory and per-source audit scope.
''',encoding='utf8')
(PRIVATE/'.gitignore').write_text('''**/downloaded_papers/
**/node_modules/
**/__pycache__/
**/.sites-runtime/
**/.venv/
**/venv/
**/rdkit-runtime/
**/validation-runtime/
**/runtime/
**/python-packages/
**/.env
**/.env.*
*.pdf
*.docx
*.zip
*.tar.gz
*.pem
*.key
''',encoding='utf8')

PUBLIC.mkdir(parents=True)
shutil.copytree(ROOT/'recipe-atlas/dist',PUBLIC,dirs_exist_ok=True)
changes=[]
old='https://mattersyn-recipe-atlas.cuiy781513.chatgpt.site'
new='https://cuiyist.github.io/mattersyn-site'
for path in PUBLIC.rglob('*.html'):
    text=path.read_text(encoding='utf8')
    updated=text.replace(old,new)
    if updated != text:
        path.write_text(updated,encoding='utf8');changes.append(path.relative_to(PUBLIC).as_posix())
(PUBLIC/'.nojekyll').write_text('',encoding='utf8')
(PUBLIC/'README.md').write_text('''# MatterSyn website

Public static website for MatterSyn: https://cuiyist.github.io/mattersyn-site/

Explore materials through the periodic table, read source-linked synthesis protocols and characterization, and download structured synthesis records. This repository contains the website publication files. Private project memory, research workflow and audit history are maintained separately.

Scientific illustrations distinguish reported measurements from reference structures and illustrative models. Consult each source and its stated review scope. Source-specific credits and provenance remain with the corresponding assets and records; this repository does not grant additional rights to third-party figures or data.
''',encoding='utf8')
public_findings=[]
for path in PUBLIC.rglob('*'):
    if not path.is_file():continue
    rel=path.relative_to(PUBLIC).as_posix()
    if path.suffix.lower() in SOURCE_SUFFIXES or path.name.lower() in {'memory.md','skill.md'}:
        public_findings.append({'path':rel,'reason':'private_or_raw_document'})
    if path.suffix.lower() in TEXT_SUFFIXES:
        raw=path.read_bytes()
        if any(pattern.search(raw) for pattern in SECRET_PATTERNS):public_findings.append({'path':rel,'reason':'possible_literal_secret'})
        if re.search(rb'(?:C:[/\\]+Users[/\\]|file://|[local path redacted]',raw):public_findings.append({'path':rel,'reason':'local_private_path'})
if public_findings:
    print(json.dumps({'public_findings':public_findings[:30]},indent=2));raise SystemExit(3)
git('init','--initial-branch=main',cwd=PUBLIC)
public_manifest={'created_at':report['created_at'],'source_dataset':'0.23.0','source_site_head':report['source_site_head'],
    'deployment_only_html_url_replacements':changes,'public_files':sum(1 for p in PUBLIC.rglob('*') if p.is_file() and '.git' not in p.parts),
    'public_scan_findings':public_findings,'private_scan_findings':findings,'private_worktree':str(PRIVATE),'public_worktree':str(PUBLIC)}
(ROOT/'research-assets/github-staging-checkpoint.json').write_text(json.dumps(public_manifest,indent=2)+'\n',encoding='utf8')
print(json.dumps({'private_files':report['file_count'],'private_bytes':report['total_bytes'],
    'history_commits':report['source_site_history_commits'],**public_manifest},indent=2))
