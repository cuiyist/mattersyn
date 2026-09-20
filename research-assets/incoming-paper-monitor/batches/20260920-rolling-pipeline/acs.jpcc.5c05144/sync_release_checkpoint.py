"""Publish-filtered incremental backup after the already-synced science release."""
from pathlib import Path
import json,hashlib,os,sys,subprocess
F=Path(__file__).resolve().parent;MON=F.parents[2];M=F.parents[4];D=M.parent/'mattersyn-github-project';W=M.parent/'mattersyn-github-public-clean/mattersyn-site'
sys.path.insert(0,str(M/'research-assets'))
import public_projection_policy as policy
from sync_github_public import io_path,SKIP,MORE_SUFFIX
names=['MEMORY.md','README.md','REFERENCES.md','recipe-atlas/data/paper-reviews/sasongko2025.json','research-assets/verify_public_delivery.py','research-assets/github-public-delivery-verification.json','research-assets/github-publication-checkpoint.json','research-assets/github-public-site-sync.json','research-assets/reference-readme-generation.json']
names+=['research-assets/incoming-paper-monitor/'+n for n in ['ledger.json','review-control.json','joint-review-handoff.md','build_public_progress.py','latest-publication.json','public-progress-editorial.json','queue-status.json','queue-status.md','queue-status.html','deadline-20260920/active-cutoff.json','deadline-20260920/sasongko-published-scope-20260920.json']]
cmd=[r'C:/Program Files/Git/cmd/git.exe','-c','safe.directory='+W.as_posix(),'-C',str(W)]
changes=subprocess.check_output(cmd+['diff','HEAD','--name-only','-z']).decode().split('\0')
names+=['recipe-atlas/dist/'+n for n in changes if n]
files=[M/n for n in names if io_path(M/n).is_file()]
for folder in [F,F.parent/'acs.inorgchem.8b02945',M/'skills']:
 for root,dirs,entries in os.walk(io_path(folder)):
  dirs[:]=[n for n in dirs if n not in SKIP]
  files.extend(folder/(Path(root)/n).relative_to(io_path(folder)) for n in entries)
rows=[];omitted=0
for p in dict.fromkeys(files):
 rel=p.relative_to(M).as_posix()
 if io_path(p).is_symlink()or p.suffix.lower()in MORE_SUFFIX or policy.exclude_path(rel):omitted+=1;continue
 raw,_=policy.project_bytes(rel,io_path(p).read_bytes());q=io_path(D/rel)
 assert len(raw)<100*1024*1024
 if q.is_file()and q.read_bytes()==raw:continue
 q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw)
 rows.append({'path':rel,'sha256':hashlib.sha256(raw).hexdigest()})
out=F/'site-integration-proposal/checkpoint-projection.json'
out.write_text(json.dumps({'status':'projected_not_committed','files':rows,'omitted':omitted,'deletions':0,'source_files_changed':False},indent=2)+'\n','utf8')
print(json.dumps({'changed':len(rows),'omitted':omitted,'source_files_changed':False}))

