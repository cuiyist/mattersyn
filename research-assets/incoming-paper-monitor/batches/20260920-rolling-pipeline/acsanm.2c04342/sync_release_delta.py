"""Apply reviewed public projection policy to only current-release project paths."""
from pathlib import Path
import hashlib,json,os,sys
L=Path(__file__).resolve().parent;MON=L.parents[2];M=L.parents[4];D=M.parent/'mattersyn-github-project'
sys.path.insert(0,str(M/'research-assets'))
import public_projection_policy as policy
from sync_github_public import io_path
assert (D/'.git').is_dir()
names=['MEMORY.md','README.md','REFERENCES.md','research-assets/verify_public_delivery.py','research-assets/incoming-paper-monitor/deadline-20260920/matuhina-review-scope-20260920.json','research-assets/reference-readme-generation.json','research-assets/github-public-delivery-verification.json','research-assets/github-publication-checkpoint.json','research-assets/github-public-project-sync.json','research-assets/github-public-site-sync.json']
names += ['research-assets/incoming-paper-monitor/'+n for n in ['ledger.json','latest-publication.json','public-progress-editorial.json','queue-status.json','queue-status.md','queue-status.html']]
names += ['research-assets/incoming-paper-monitor/deadline-20260920/active-cutoff.json']
files=[M/n for n in names if (M/n).is_file()]
folders=[L,L.parent/'acs.cgd.9b01519',L.parent/'intake-20260920T111852Z',MON/'deadline-20260920/admission-20260920T111852Z',M/'skills',M/'recipe-atlas/data',M/'recipe-atlas/dist',M/'recipe-atlas/scripts']
folders += [L.parent/'la8031286',L.parent/'intake-20260920T114139Z',MON/'deadline-20260920/admission-20260920T114139Z']
for folder in folders:
 for directory,dirs,names in os.walk(io_path(folder)):
  dirs[:]=[n for n in dirs if n not in {'.git','__pycache__','node_modules','preview-vendor'}]
  files += [folder/(Path(directory)/n).relative_to(io_path(folder)) for n in names]
rows=[];excluded=0
for source in dict.fromkeys(files):
 rel=source.relative_to(M).as_posix()
 if io_path(source).is_symlink() or policy.exclude_path(rel):excluded+=1;continue
 raw,_=policy.project_bytes(rel,io_path(source).read_bytes());target=io_path(D/rel)
 digest=hashlib.sha256(raw).hexdigest()
 if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==digest:continue
 target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);rows.append({'path':rel,'sha256':digest})
report={'status':'projected_not_committed','files_changed':len(rows),'excluded':excluded,'rows':rows,'deletions':0,'original_sources_modified':False,'policy':policy.policy_metadata()}
(L/'site-integration-proposal/project-delta-projection.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ['rows','policy']}))
