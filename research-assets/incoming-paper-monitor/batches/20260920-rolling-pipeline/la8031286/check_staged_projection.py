from pathlib import Path
import json,subprocess,sys
N=Path(__file__).resolve().parent;M=N.parents[4];sys.path.insert(0,str(M/'research-assets'))
import public_projection_policy as policy
from sync_github_public import io_path
git=r'C:/Program Files/Git/cmd/git.exe';rows=[]
for name,prefix in [('mattersyn-github-project',''),('mattersyn-github-public-clean/mattersyn-site','recipe-atlas/dist/')]:
 d=M.parent/name;cmd=[git,'-c','safe.directory='+d.as_posix(),'-c','core.longpaths=true','-C',str(d)]
 paths=subprocess.check_output(cmd+['diff','--cached','--name-only','--diff-filter=ACMR','-z']).decode().split('\0');paths=[p for p in paths if p]
 for rel in paths:
  assert not policy.exclude_path(prefix+rel),rel
  assert Path(rel).suffix.lower() not in {'.pdf','.docx','.doc','.zip','.tar','.gz','.pyc'},rel
  f=io_path(d/rel);assert not f.is_symlink() and f.stat().st_size<100*1024*1024,rel
 rows.append({'repository':name,'changed_files':len(paths),'forbidden_paths':0,'symlinks':0,'oversize_files':0})
(N/'site-integration-proposal/staged-projection-check.json').write_text(json.dumps({'status':'passed','policy':policy.policy_metadata(),'checks':rows},indent=2)+'\n','utf8')
print(json.dumps(rows))
