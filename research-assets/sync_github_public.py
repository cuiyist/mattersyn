"""Synchronize audited public projections; original source files are never changed."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import argparse,hashlib,json,os,re,subprocess
import public_projection_policy as policy
ROOT=Path(__file__).resolve().parent.parent
GIT=r'C:\Program Files\Git\cmd\git.exe'
SKIP={'.git','node_modules','__pycache__','.sites-runtime','rdkit-runtime','runtime','python-packages','.venv','venv','validation-runtime','downloaded_papers'}
MORE_SUFFIX={'.7z','.rar','.pem','.key','.pfx','.p12','.bundle'}
DEST={'project':ROOT.parent/'mattersyn-github-project','site':ROOT.parent/'mattersyn-github-public-clean'/'mattersyn-site'}
OLD_URL='https://mattersyn-recipe-atlas.cuiy781513.chatgpt.site'
NEW_URL='https://cuiyist.github.io/mattersyn-site'
def git(dest,*args):
 p=subprocess.run([GIT,'-c','safe.directory='+dest.as_posix(),'-C',str(dest),*args],capture_output=True)
 if p.returncode:raise RuntimeError('Git '+args[0]+' failed; source/credential details withheld.')
 return p.stdout
def sha(raw):return hashlib.sha256(raw).hexdigest()

def io_path(path):
 """Keep logical/public paths unchanged; support deep local audit directories."""
 # Do not resolve links here: collect() must still detect and exclude them.
 absolute=path.absolute()
 if os.name=='nt' and not str(absolute).startswith('\\\\?\\'):
  return Path('\\\\?\\'+str(absolute))
 return absolute
def collect(kind):
 source=ROOT if kind=='project' else ROOT/'recipe-atlas/dist'
 rows=[];omissions=[]
 walkroot=io_path(source)
 for directory,dirs,files in os.walk(walkroot):
  dirs[:]=[n for n in dirs if n not in SKIP]
  for name in files:
   rel=(Path(directory)/name).relative_to(walkroot).as_posix();path=source/rel;policyrel=rel if kind=='project' else 'recipe-atlas/dist/'+rel
   if io_path(path).is_symlink() or path.suffix.lower() in MORE_SUFFIX or name.endswith(('.tar.gz','.tar')) or name=='.env' or name.startswith('.env.'):
    omissions.append({'path':rel,'reason':'local_archive_dependency_link_or_credential_configuration'});continue
   reason=policy.exclude_path(policyrel)
   if reason:omissions.append({'path':rel,'reason':reason});continue
   rows.append((rel,policyrel,path))
 return rows,omissions
def sync(kind):
 dest=DEST[kind]
 if not (dest/'.git').is_dir():raise RuntimeError('Expected isolated Git destination does not exist.')
 remote=git(dest,'remote').decode().strip()
 if remote:
  expected='https://github.com/cuiyist/'+('mattersyn' if kind=='project' else 'mattersyn-site')+'.git'
  if git(dest,'remote','get-url','origin').decode().strip()!=expected:raise RuntimeError('Unexpected destination remote; stopped.')
 entries,omissions=collect(kind)
 changes=[];transforms=[];count=0;total=0
 def project(entry):
  rel,policyrel,path=entry;raw=io_path(path).read_bytes();clean,stats=policy.project_bytes(policyrel,raw)
  if kind=='site' and path.suffix.lower()=='.html':clean=clean.replace(OLD_URL.encode(),NEW_URL.encode())
  if len(clean)>=100*1024*1024:raise RuntimeError('File exceeds GitHub per-file limit: '+rel)
  if kind=='site' and path.suffix.lower() in {'.html','.js','.mjs','.json','.jsonl','.css','.md','.toml','.txt'}:
   if re.search(rb'(?:C:[/\\]+Users[/\\]|file://|[local path redacted]',clean):raise RuntimeError('Local path in website projection: '+rel)
  target=io_path(dest/rel);changed=not target.is_file() or sha(target.read_bytes())!=sha(clean)
  if changed:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(clean)
  return {'path':rel,'bytes':len(clean),'sha256':sha(clean),'changed':changed,'projection':stats}
 with ThreadPoolExecutor(max_workers=8) as pool:
  for row in pool.map(project,entries):
   count+=1;total+=row['bytes']
   if row['changed']:changes.append(row)
   if row['projection']['changed']:transforms.append({'path':row['path'],**row['projection']})
 if kind=='site':(dest/'.nojekyll').write_bytes(b'')
 # Reconcile only individual tracked projection files that no longer have a
 # source counterpart. Resolve and bound every deletion to the isolated copy.
 keep={r for r,_,_ in entries}|{'.gitignore','.nojekyll'};removed=[]
 for rel in git(dest,'ls-files','-z').decode('utf8').split('\0'):
  if not rel or rel in keep:continue
  target=(dest/rel).resolve()
  if dest.resolve() not in target.parents:raise RuntimeError('Deletion target escapes isolated projection.')
  physical=io_path(target)
  if physical.is_file():physical.unlink();removed.append(rel)
 report={'schema':'mattersyn-public-sync/1','created_at':datetime.now(timezone.utc).isoformat(),'kind':kind,'source_root':str(ROOT),'destination':str(dest),'files_compared':count,'projected_bytes':total,'changed_or_added':changes,'excluded_paths':omissions,'content_transformations':transforms,'removed_projection_only_files':removed,'policy':policy.policy_metadata(),'original_source_files_changed':False,'git_commit_or_push_performed':False}
 out=ROOT/'research-assets'/('github-public-'+kind+'-sync.json');out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'kind':kind,'files':count,'updated':len(changes),'excluded':len(omissions),'transformed':len(transforms),'removed_stale_projection_files':len(removed),'report':str(out)},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('kind',choices=sorted(DEST));args=p.parse_args();sync(args.kind)
