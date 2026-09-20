"""Filtered public backup of current review checkpoints; no source-file edits."""
from pathlib import Path
import os,sys,json,hashlib
F=Path(__file__).resolve().parent;MON=F.parents[2];M=F.parents[4];D=M.parent/'mattersyn-github-project'
sys.path.insert(0,str(M/'research-assets'))
import public_projection_policy as policy
from sync_github_public import io_path
assert (D/'.git').is_dir()
names=['MEMORY.md','README.md','REFERENCES.md','research-assets/github-public-site-sync.json']
names+=['research-assets/incoming-paper-monitor/'+n for n in ['ledger.json','latest-publication.json','public-progress-editorial.json','queue-status.json','queue-status.md','queue-status.html','deadline-20260920/active-cutoff.json','deadline-20260920/friedfeld-source-reviewed-scope-20260920.json']]
files=[M/n for n in names if (M/n).is_file()]
folders=[F,F.parent/'acs.jpcc.5c05144',F.parent/'intake-20260920T141934Z',MON/'deadline-20260920/admission-20260920T141934Z',M/'skills']
for folder in folders:
 for directory,dirs,filenames in os.walk(io_path(folder)):
  dirs[:]=[n for n in dirs if n not in {'.git','__pycache__','node_modules','preview-vendor'}]
  files += [folder/(Path(directory)/n).relative_to(io_path(folder)) for n in filenames]
files += [M/'recipe-atlas/dist'/n for n in ['progress.html','data/review-progress.json']]
changes=[];excluded=0
for source in dict.fromkeys(files):
 rel=source.relative_to(M).as_posix()
 if io_path(source).is_symlink() or policy.exclude_path(rel):excluded+=1;continue
 raw,_=policy.project_bytes(rel,io_path(source).read_bytes());dst=io_path(D/rel)
 assert len(raw)<100*1024*1024,rel
 digest=hashlib.sha256(raw).hexdigest()
 if dst.exists() and hashlib.sha256(dst.read_bytes()).hexdigest()==digest:continue
 dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw);changes.append({'path':rel,'sha256':digest})
out=F/'progress-publication/project-projection.json';out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps({'status':'projected_not_committed','changes':changes,'excluded_paths':excluded,'deletions':0,'policy':policy.policy_metadata()},indent=2)+'\n','utf8')
print(json.dumps({'changed_files':len(changes),'excluded_paths':excluded,'source_files_changed':False}))
