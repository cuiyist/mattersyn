"""Private preservation only. Does not change source repositories or remotes."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, shutil, subprocess

def physical(path):
    p = str(Path(path).absolute())
    return Path('\\\\?\\' + p) if os.name == 'nt' and not p.startswith('\\\\?\\') else Path(p)

def git(repo, *args):
    p = subprocess.run(['git', '-c', 'safe.directory='+repo.as_posix(), '-C', str(repo), *args], capture_output=True)
    if p.returncode:
        raise RuntimeError('Git preservation operation failed: '+args[0])
    return p.stdout

def sha(path):
    h = hashlib.sha256()
    with physical(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024), b''): h.update(block)
    return h.hexdigest()

def preserve_index(src,dst):
    """Retain staged-only bytes and index stages, including unreferenced blobs."""
    head=git(src,'rev-parse','HEAD').decode().strip()
    entries=git(src,'ls-files','--stage','-z')
    (dst/'index-entries.bin').write_bytes(entries)
    (dst/'staged-changes.patch').write_bytes(git(src,'diff','--cached','--binary','HEAD'))
    index_path=Path(git(src,'rev-parse','--git-path','index').decode().strip())
    if not index_path.is_absolute():index_path=src/index_path
    if index_path.is_file():shutil.copy2(index_path,dst/'git-index.bin')
    reachable={line.split(b' ',1)[0].decode()for line in git(src,'rev-list','--objects','--all').splitlines()}
    index_oids={line.split(b'\t',1)[0].split()[1].decode()for line in entries.split(b'\0')if line}
    saved=[]
    for oid in sorted(index_oids-reachable):
        raw=git(src,'cat-file','blob',oid)
        if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=oid:raise RuntimeError('Index blob verification failed')
        path=dst/'index-only-blobs'/oid;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);saved.append({'git_blob':oid,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
    result={'schema':'mattersyn-private-index-preservation/1','head':head,'entry_bytes_sha256':hashlib.sha256(entries).hexdigest(),'index_blob_count':len(index_oids),'index_only_blobs':saved,'staged_patch_sha256':sha(dst/'staged-changes.patch')}
    (dst/'index-preservation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('destination');a=ap.parse_args()
    src=Path(a.source).resolve();dst=Path(a.destination).resolve()
    if src==dst or src in dst.parents or dst in src.parents or dst.exists():
        raise RuntimeError('A new private sibling destination is required')
    head=git(src,'rev-parse','HEAD').decode().strip();refs=git(src,'show-ref')
    status=git(src,'status','--porcelain=v1','-z')
    dst.mkdir(parents=True)
    bundle=dst/'all-refs.bundle'
    git(src,'bundle','create',str(bundle),'--all')
    git(src,'bundle','verify',str(bundle))
    index_preservation=preserve_index(src,dst)
    (dst/'working-changes.patch').write_bytes(git(src,'diff','--binary','HEAD'))
    (dst/'status-before.bin').write_bytes(status)
    (dst/'refs-before.txt').write_bytes(refs)
    paths=(set(git(src,'ls-files','--modified','--others','--exclude-standard','-z').decode('utf-8').split('\0'))|set(git(src,'diff','--cached','--name-only','-z','HEAD').decode('utf-8').split('\0')))-{''}
    files=[]
    for rel in sorted(paths):
        source=src/rel;target=dst/'working-files'/rel
        if not physical(source).is_file():
            files.append({'path':rel,'state':'absent'});continue
        physical(target.parent).mkdir(parents=True,exist_ok=True)
        shutil.copy2(physical(source),physical(target))
        digest=sha(source)
        if sha(target)!=digest:raise RuntimeError('Backup hash mismatch')
        files.append({'path':rel,'state':'preserved','sha256':digest,'bytes':physical(target).stat().st_size})
    if git(src,'rev-parse','HEAD').decode().strip()!=head or git(src,'show-ref')!=refs or git(src,'status','--porcelain=v1','-z')!=status:
        raise RuntimeError('Source changed during preservation; retain snapshot and reconcile before proceeding')
    report={'schema':'mattersyn-private-preservation/1','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':head,'bundle_sha256':sha(bundle),'bundle_bytes':bundle.stat().st_size,'bundle_verified':True,'source_unchanged':True,'index_preservation':index_preservation,'working_files':files}
    (dst/'preservation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='working_files'}|{'preserved_working_files':len(files)}))

if __name__=='__main__':main()
