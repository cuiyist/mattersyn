"""Root-only project projection; no push, delete, source write or visibility action."""
from pathlib import Path
import hashlib,json,os,sys
L=Path(__file__).resolve().parent
if L.name=='delivery-helper-proposal':L=L.parent
MON=L.parents[2];M=L.parents[4];D=M.parent/'mattersyn-github-project'
sys.dont_write_bytecode=True;sys.path.insert(0,str(M/'research-assets'))
import public_projection_policy as policy
from sync_github_public import io_path,SKIP,MORE_SUFFIX
assert (D/'.git').is_dir()
names=['MEMORY.md','README.md','REFERENCES.md','research-assets/verify_public_delivery.py','research-assets/public_projection_policy.py','research-assets/sync_github_public.py','research-assets/reference-readme-generation.json','research-assets/github-public-delivery-verification.json','research-assets/github-publication-checkpoint.json','research-assets/github-public-project-sync.json','research-assets/github-public-site-sync.json']
names+=['research-assets/incoming-paper-monitor/'+n for n in ['ledger.json','latest-publication.json','public-progress-editorial.json','queue-status.json','queue-status.md','queue-status.html']]
files=[M/n for n in names if io_path(M/n).is_file()]
folders=[L,L.parent/'acs.jpcc.5c05144',M/'skills',M/'recipe-atlas',MON/'deadline-20260920',L.parent/'intake-20260920T133256Z',L.parent/'intake-20260920T141934Z']
for folder in folders:
 if not io_path(folder).is_dir():continue
 walkroot=io_path(folder)
 for directory,dirs,names in os.walk(walkroot,followlinks=False):
  dirs[:]=[n for n in dirs if n not in SKIP and not (Path(directory)/n).is_symlink()]
  files.extend(folder/(Path(directory)/n).relative_to(walkroot)for n in names)
rows=[];excluded=0
for source in dict.fromkeys(files):
 rel=source.relative_to(M).as_posix();logical=Path(rel)
 if io_path(source).is_symlink()or logical.suffix.lower()in MORE_SUFFIX or source.name.endswith(('.tar.gz','.tar'))or source.name=='.env'or source.name.startswith('.env.')or policy.exclude_path(rel):excluded+=1;continue
 raw,_=policy.project_bytes(rel,io_path(source).read_bytes());target=io_path(D/rel);digest=hashlib.sha256(raw).hexdigest()
 assert len(raw)<100*1024*1024,'Oversized projected file requires review: '+rel
 if target.exists()and hashlib.sha256(target.read_bytes()).hexdigest()==digest:continue
 target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);rows.append({'path':rel,'sha256':digest})
report={'status':'projected_not_committed','files_changed':len(rows),'excluded':excluded,'rows':rows,'deletions':0,'original_sources_modified':False,'policy':policy.policy_metadata(),'scope':'Current Friedfeld/Sasongko checkpoints, fixed-cutoff and separate later-arrival metadata, memory/skills and all Site code/data/dist; original documents/fulltext/fullpages remain local.'}
(L/'site-integration-proposal/project-delta-projection.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
print(json.dumps({k:v for k,v in report.items()if k not in['rows','policy']}))
