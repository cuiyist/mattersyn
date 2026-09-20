"""Root-only filtered project backup; default dry-run, no Git/network/deletion."""
from pathlib import Path
import argparse,hashlib,json,os,sys
from release_support import paper_root,load_config
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
 J=paper_root();MON=J.parents[2];M=J.parents[4];D=M.parent/'mattersyn-github-project'
 if args.apply:load_config(J)
 sys.dont_write_bytecode=True;sys.path.insert(0,str(M/'research-assets'))
 import public_projection_policy as policy
 from sync_github_public import io_path,SKIP,MORE_SUFFIX
 assert (D/'.git').is_dir()
 names=['MEMORY.md','README.md','REFERENCES.md','research-assets/verify_public_delivery.py','research-assets/public_projection_policy.py','research-assets/sync_github_public.py','research-assets/reference-readme-generation.json','research-assets/github-public-delivery-verification.json','research-assets/github-publication-checkpoint.json','research-assets/github-public-project-sync.json','research-assets/github-public-site-sync.json']
 names+=['research-assets/incoming-paper-monitor/'+n for n in ['ledger.json','review-control.json','latest-publication.json','public-progress-editorial.json','queue-status.json','queue-status.md','queue-status.html']]
 files=[M/n for n in names if io_path(M/n).is_file()]
 folders=[J,J.parent/'acs.inorgchem.8b02945',M/'skills',M/'recipe-atlas',MON/'deadline-20260920',J.parent/'intake-20260920T133256Z',J.parent/'intake-20260920T141934Z']
 for folder in folders:
  if not io_path(folder).is_dir():continue
  walkroot=io_path(folder)
  for directory,dirs,entries in os.walk(walkroot,followlinks=False):
   dirs[:]=[n for n in dirs if n not in SKIP and not(Path(directory)/n).is_symlink()]
   files.extend(folder/(Path(directory)/n).relative_to(walkroot) for n in entries)
 rows=[];excluded=0
 for source in dict.fromkeys(files):
  rel=source.relative_to(M).as_posix();logical=Path(rel)
  if io_path(source).is_symlink() or logical.suffix.lower() in MORE_SUFFIX or source.name.endswith(('.tar.gz','.tar')) or source.name=='.env' or source.name.startswith('.env.') or policy.exclude_path(rel):excluded+=1;continue
  raw,_=policy.project_bytes(rel,io_path(source).read_bytes());target=io_path(D/rel);digest=hashlib.sha256(raw).hexdigest()
  assert len(raw)<100*1024*1024,'Oversized file requires review: '+rel
  if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==digest:continue
  if args.apply:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
  rows.append({'path':rel,'sha256':digest})
 report={'status':'projected_not_committed' if args.apply else 'dry_run_no_mutation','files_changed':len(rows),'excluded':excluded,'rows':rows,'deletions':0,'original_sources_modified':False,'policy':policy.policy_metadata(),'scope':'Final Friedfeld/Sasongko checkpoints, paused control/editorial/memory, existing skills, immutable cutoff and separate later-arrival metadata, all Site code/data/dist. Original source documents/fulltext/fullpages remain local.'}
 if args.apply:(J/'site-integration-proposal/project-delta-projection.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
 print(json.dumps({k:v for k,v in report.items() if k not in ['rows','policy']}))
if __name__=='__main__':main()
