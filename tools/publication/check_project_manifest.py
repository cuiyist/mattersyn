"""Require complete tracked-file coverage by the approved source manifest."""
from pathlib import Path
import argparse,json,subprocess

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--manifest',default='publication/project-allowlist.json');a=p.parse_args();root=a.root.resolve()
    def git(*args):return subprocess.check_output(['git',*args],cwd=root)
    manifest=(root/a.manifest).resolve()
    if not manifest.is_relative_to(root):raise RuntimeError('Manifest must be in the public source repository')
    data=json.loads(manifest.read_bytes());tracked={x.decode()for x in git('ls-files','-z').split(b'\0')if x};listed={x['path']for x in data['files']}
    if tracked!=listed|{a.manifest}:raise RuntimeError('Source manifest does not exactly cover tracked files')
    if len(listed)!=len(data['files']):raise RuntimeError('Duplicate source manifest paths')
    # A manifest cannot hash itself. Its sole successor commit adds/updates only
    # this control file; every other byte is bound to the reviewed source commit.
    changed={x.decode()for x in git('diff','--name-only','-z',data['source_commit'],'HEAD').split(b'\0')if x}
    if changed-{a.manifest}:raise RuntimeError('Source changed since its approved manifest commit')
    if data.get('repo')!='mattersyn':raise RuntimeError('Incorrect repository binding')
    print(json.dumps({'tracked_files':len(tracked),'approved_payload_files':len(listed),'manifest_self_exclusion':a.manifest,'status':'passed'}))
if __name__=='__main__':main()
