"""Bind a committed portable build blueprint to a clean source checkout's HEAD."""
from pathlib import Path
import argparse,hashlib,json,subprocess
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def make(root,blueprint,out):
    root=root.resolve();blueprint=blueprint.resolve();out=out.resolve()
    if out.is_relative_to(root):raise ValueError('Runtime snapshot must be outside source repository')
    if out.exists():raise ValueError('Runtime snapshot output must be new')
    gitroot=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=root,text=True).strip()).resolve()
    if gitroot!=root:raise ValueError('Source root must be the repository root')
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=root,text=True).strip():raise ValueError('Source checkout must be clean before binding a runtime snapshot')
    if not blueprint.is_relative_to(root):raise ValueError('Blueprint must be a committed repository member')
    subprocess.check_call(['git','ls-files','--error-unmatch','--',blueprint.relative_to(root).as_posix()],cwd=root,stdout=subprocess.DEVNULL)
    data=json.loads(blueprint.read_bytes())
    if data.get('schema')!='mattersyn-build-input-blueprint/1':raise ValueError('Unexpected blueprint schema')
    for row in data['input_files']:
        p=(root/row['path']).resolve()
        if not p.is_relative_to(root)or not p.is_file()or sha(p)!=row['sha256']:raise ValueError('Input does not match committed blueprint: '+row['path'])
    snapshot={k:v for k,v in data.items()if k not in {'schema','note'}}
    snapshot.update(schema='mattersyn-release-snapshot/1',source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),blueprint_sha256=sha(blueprint))
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(snapshot,indent=2)+'\n',encoding='utf-8')
    return {'snapshot_sha256':sha(out),'source_commit':snapshot['source_commit'],'input_count':len(snapshot['input_files'])}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--blueprint',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(make(a.root,a.blueprint,a.output)))
if __name__=='__main__':main()
