"""Build a new isolated artifact; no package installs, Git mutations or publication."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys,os,time
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class BuildCommandError(RuntimeError):
    """Preserve the failed stage in the private build log."""
    def __init__(self,run):
        self.run=run
        super().__init__('Command failed: '+str(run['command'])+'\n'+run['stdout']+'\n'+run['stderr'])

def execute(command,cwd):
    started=time.perf_counter()
    result=subprocess.run(command,cwd=cwd,text=True,capture_output=True,encoding='utf-8',errors='replace',env={**os.environ,'PYTHONIOENCODING':'utf-8','PYTHONDONTWRITEBYTECODE':'1'})
    run={'command':command,'stdout':result.stdout,'stderr':result.stderr,'returncode':result.returncode,'elapsed_seconds':round(time.perf_counter()-started,6)}
    if result.returncode:raise BuildCommandError(run)
    return run
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--gate',type=Path);p.add_argument('--allowlist',type=Path);p.add_argument('--policy',type=Path);p.add_argument('--registry',type=Path,required=True);p.add_argument('--display-overrides',type=Path);p.add_argument('--artifact-transform',type=Path);p.add_argument('--candidate',action='store_true',help='Build a review artifact only; never approve or emit release-manifest.json');a=p.parse_args()
    if not a.candidate and not all([a.gate,a.allowlist,a.policy]):raise SystemExit('Final release requires --gate, --allowlist and --policy; use --candidate for unapproved review output')
    if a.output.exists():raise SystemExit('Output must not exist. No existing dist/source tree is overwritten.')
    snapshot=read(a.snapshot)
    if not a.candidate:
        if a.snapshot.resolve().is_relative_to(ROOT.parent.resolve()):raise SystemExit('Final runtime snapshot must be outside the source repository')
        actual_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT.parent,text=True).strip()
        if actual_head!=snapshot.get('source_commit'):raise SystemExit('Final source HEAD differs from runtime snapshot')
        if subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=ROOT.parent,text=True).strip():raise SystemExit('Final source repository must be clean')
    for row in snapshot['input_files']:
        path=(ROOT.parent/row['path']).resolve()
        if not path.is_relative_to(ROOT.parent.resolve())or not path.is_file()or sha(path)!=row['sha256']:raise SystemExit('Input hash mismatch: '+row['path'])
    work=a.output/'project/recipe-atlas';work.mkdir(parents=True)
    # Source/static inputs reached this tree only through the cleared migration.
    for name in ['scripts','templates','data','static','tests']:
        if (ROOT/name).exists():shutil.copytree(ROOT/name,work/name)
    if(ROOT.parent/'README.md').is_file():shutil.copyfile(ROOT.parent/'README.md',work.parent/'README.md')
    shutil.copytree(work/'static',work/'dist');runs=[]
    if a.display_overrides:
        (work/'private-build').mkdir();shutil.copyfile(a.display_overrides,work/'private-build/asset-display-overrides.json')
    try:
        if a.artifact_transform:runs.append(execute([sys.executable,str(a.artifact_transform.resolve()),'--phase','prebuild','--root',str((work/'dist').resolve()),'--source-root',str(work.resolve()),'--registry',str(a.registry.resolve())],work))
        for script in ['build_dataset.py','build_reader_views.py','build_evidence_views.py','build_paper_reviews.py','build_atlas.py','build_inventory.py','build_reader_metadata.py']:
            runs.append(execute([sys.executable,'scripts/'+script],work))
        sys.path.insert(0,str(work/'scripts'));from generate_release_metadata import generate
        metadata=generate(work,snapshot)
        baseline=read(work/'data/release-baseline-manifest.json');built=read(work/'dist/data/dataset-manifest.json')
        old={r['record_id']:r for r in baseline['records']};new={r['record_id']:r for r in built['records']}
        if set(old)!=set(new):raise ValueError('Build changed approved record membership')
        for rid in old:
            expected_digest=snapshot.get('approved_record_digests',{}).get(rid,old[rid]['record_sha256'])
            if expected_digest!=new[rid].get('record_sha256'):raise ValueError('Build changed approved record: '+rid)
            if old[rid].get('eligibility')!=new[rid].get('eligibility'):raise ValueError('Build changed task eligibility: '+rid)
        if a.artifact_transform:runs.append(execute([sys.executable,str(a.artifact_transform.resolve()),'--phase','postbuild','--root',str((work/'dist').resolve()),'--source-root',str(work.resolve()),'--registry',str(a.registry.resolve())],work))
        for rid in old:
            if read(work/'dist/data/records'/f'{rid}.json')!=read(work/'data/records'/f'{rid}.json'):raise ValueError('Artifact transform changed a scientific record: '+rid)
        runs.append(execute([sys.executable,'-m','unittest','discover','-s','tests','-v'],work))
        for script in ['check_site.py','check_atlas.py','check_quality.py']:runs.append(execute([sys.executable,'scripts/'+script],work))
        (work/'dist/.nojekyll').write_bytes(b'')
        files=[{'path':p.relative_to(work/'dist').as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted((work/'dist').rglob('*'))if p.is_file()]
        common={'source_commit':snapshot['source_commit'],'release_id':snapshot['release_id'],'display_override_sha256':sha(a.display_overrides)if a.display_overrides else None,'snapshot_sha256':sha(a.snapshot),'files':files,'metadata':metadata,'published':False}
        if a.candidate:
            candidate={'schema':'mattersyn-unapproved-build-candidate/1','status':'UNAPPROVED','release_eligible':False,'boundary_gate_passed':False,'scope':'Build/data checks only; inspect exact output and prepare a reviewed allowlist before a separate final clean rebuild.',**common}
            (a.output/'candidate-manifest.json').write_text(json.dumps(candidate,indent=2)+'\n',encoding='utf-8',newline='\n')
        else:
            runs.append(execute([sys.executable,str(a.gate.resolve()),'--root',str((work/'dist').resolve()),'--policy',str(a.policy.resolve()),'--allowlist',str(a.allowlist.resolve()),'--registry',str(a.registry.resolve()),'--repo','mattersyn-site','--manifest-out',str((a.output/'boundary-manifest.json').resolve()),'--report-out',str((a.output/'boundary-report.json').resolve())],work))
            final={'schema':'mattersyn-reproducible-release/1','status':'BOUNDARY_GATE_PASSED_PENDING_PUBLICATION_APPROVAL','boundary_manifest_sha256':sha(a.output/'boundary-manifest.json'),**common}
            (a.output/'release-manifest.json').write_text(json.dumps(final,indent=2)+'\n',encoding='utf-8',newline='\n')
    except BuildCommandError as exc:
        runs.append(exc.run)
        raise
    finally:(a.output/'build-log.json').write_text(json.dumps(runs,indent=2)+'\n',encoding='utf-8',newline='\n')
if __name__=='__main__':main()
