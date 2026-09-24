"""Build an isolated policy-filtered history; never mutates or pushes the source.

The policy module must implement history_project(kind, path, raw, config).
All reports are private preservation artifacts. Public release gets a summary.
"""
from pathlib import Path
import argparse, datetime, hashlib, importlib.util, json, re, subprocess, sys

def git(repo,*args,input=None):
    p=subprocess.run(['git','-c','safe.directory='+repo.as_posix(),'-C',str(repo),*args],input=input,capture_output=True)
    if p.returncode:raise RuntimeError('Git operation failed: '+args[0])
    return p.stdout

def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def quoted(path):
    out=bytearray(b'"')
    for b in path.encode('utf-8'):
        if b in (34,92):out.extend(b'\\'+bytes([b]))
        elif 32<=b<127:out.append(b)
        else:out.extend(('\\%03o'%b).encode('ascii'))
    return bytes(out)+b'"'

class Reader:
    def __init__(self,repo):
        self.p=subprocess.Popen(['git','-c','safe.directory='+repo.as_posix(),'-C',str(repo),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    def get(self,oid):
        self.p.stdin.write(oid.encode()+b'\n');self.p.stdin.flush();h=self.p.stdout.readline().split()
        if len(h)!=3 or h[1] not in (b'blob',b'commit'):raise RuntimeError('Unsupported source object')
        raw=self.p.stdout.read(int(h[2]))
        if len(raw)!=int(h[2]) or self.p.stdout.read(1)!=b'\n':raise RuntimeError('Truncated source object')
        return raw
    def close(self):self.p.stdin.close();self.p.wait()

def tree(repo,commit):
    for line in git(repo,'ls-tree','-rz','--full-tree',commit).split(b'\0'):
        if not line:continue
        meta,path=line.split(b'\t',1);mode,kind,oid=meta.split()
        if kind!=b'blob' or mode not in (b'100644',b'100755'):raise RuntimeError('Review required for symlink or submodule')
        yield path.decode('utf-8'),mode.decode(),oid.decode()

def commit_parts(raw):
    header,message=raw.split(b'\n\n',1);fields={};parents=[]
    for line in header.splitlines():
        if line.startswith(b'parent '):parents.append(line[7:].decode())
        elif line.startswith((b'author ',b'committer ',b'encoding ')):
            key,value=line.split(b' ',1);fields[key.decode()]=value
        elif line.startswith(b'gpgsig '):raise RuntimeError('Signed commit requires explicit handling')
    if not all(k in fields for k in ('author','committer')):raise RuntimeError('Missing commit identities')
    return fields,parents,message

def run():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--destination',required=True);p.add_argument('--reports',required=True);p.add_argument('--policy',required=True);p.add_argument('--config',required=True);p.add_argument('--kind',choices=['project','site'],required=True);p.add_argument('--expected-head',required=True);a=p.parse_args()
    src=Path(a.source).resolve();dst=Path(a.destination).resolve();reports=Path(a.reports).resolve()
    if dst.exists() or src==dst or src in dst.parents or dst in src.parents:raise RuntimeError('New distinct destination required')
    if reports.exists() or reports==src or reports==dst or src in reports.parents or dst in reports.parents or reports in src.parents or reports in dst.parents:
        raise RuntimeError('New private report directory disjoint from both repositories required')
    head=git(src,'rev-parse','HEAD').decode().strip()
    if head!=a.expected_head:raise RuntimeError('Source head changed')
    refs=git(src,'show-ref');status=git(src,'status','--porcelain=v1','-z')
    for line in refs.decode().splitlines():
        if line.split()[1].startswith('refs/tags/'):raise RuntimeError('Tags require separate reviewed preservation')
    config=json.loads(Path(a.config).read_text(encoding='utf-8'))
    module_path=Path(a.policy).resolve();sys.path.insert(0,str(module_path.parent))
    spec=importlib.util.spec_from_file_location('history_release_policy',module_path);policy=importlib.util.module_from_spec(spec);sys.modules[spec.name]=policy;spec.loader.exec_module(policy)
    if 'policy_path'in config and'registry_path'in config:config=policy.load_config(config['policy_path'],config['registry_path'])
    preflight=getattr(policy,'history_exclude_path',lambda kind,path,config:None)
    policy_kind={'project':'mattersyn','site':'mattersyn-site'}[a.kind]
    commits=git(src,'rev-list','--reverse','--topo-order','--all').decode().splitlines()
    dst.mkdir(parents=True);reports.mkdir(parents=True,exist_ok=True)
    git(dst,'init','--initial-branch=main');git(dst,'config','core.autocrlf','false');git(dst,'config','core.longpaths','true')
    marksfile=reports/'import-marks.txt';log=(reports/'import.stderr').open('wb')
    importer=subprocess.Popen(['git','-c','safe.directory='+dst.as_posix(),'-C',str(dst),'fast-import','--quiet','--date-format=raw','--export-marks='+str(marksfile)],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=log)
    reader=Reader(src);cache={};path_decisions={};blobs={};commit_marks={};nextmark=1;rows=[];exclusions={};transforms={};read_bytes=0
    def emit(raw):importer.stdin.write(raw)
    try:
        for index,old in enumerate(commits):
            fields,parents,message=commit_parts(reader.get(old));allowed=[];omitted=0;changed=0
            # Commit messages preserve chronology without exposing machine paths.
            # These are short authored commit summaries, not exported source files.
            slash = bytes((47,))
            separator = b'[' + bytes((92, 92, 47)) + b']+'
            commit_path_pattern = b'(?:[A-Za-z]:' + separator + b'Users' + separator + b'|' + slash + b'Users' + slash + rb')[^\s\"\'<>]+' 
            clean_message=re.sub(commit_path_pattern,b'[LOCAL_PATH]',message)
            for path,mode,oid in tree(src,old):
                if path not in path_decisions:path_decisions[path]=preflight(policy_kind,path,config)
                reason=path_decisions[path]
                if reason:exclusions[path]=reason;omitted+=1;continue
                key=(path,oid)
                if key not in cache:
                    raw=reader.get(oid);read_bytes+=len(raw)
                    decision=policy.history_project(policy_kind,path,raw,config)
                    if decision['action']=='omit':cache[key]=(None,decision['reason'])
                    else:
                        clean=decision['content']
                        if not isinstance(clean,bytes):raise RuntimeError('Policy must return bytes')
                        cleanoid=hashlib.sha1(b'blob '+str(len(clean)).encode()+b'\0'+clean).hexdigest()
                        if cleanoid not in blobs:
                            mark=nextmark;nextmark+=1;blobs[cleanoid]=mark
                            emit(b'blob\nmark :'+str(mark).encode()+b'\ndata '+str(len(clean)).encode()+b'\n'+clean+b'\n')
                        cache[key]=(blobs[cleanoid],cleanoid,sha(raw),sha(clean),decision['content_class'])
                decision=cache[key]
                if decision[0] is None:exclusions[path]=decision[1];omitted+=1;continue
                mark,cleanoid,oldsha,newsha,content_class=decision
                allowed.append((path,mode,mark,cleanoid))
                if oldsha!=newsha:
                    changed+=1;transforms[path+'@'+oid]={'path':path,'old_blob':oid,'new_blob':cleanoid,'original_sha256':oldsha,'public_sha256':newsha,'content_class':content_class}
            cm=nextmark;nextmark+=1;commit_marks[old]=cm
            emit(b'commit refs/heads/projection-build\nmark :'+str(cm).encode()+b'\nauthor '+fields['author']+b'\ncommitter '+fields['committer']+b'\n')
            if 'encoding' in fields:emit(b'encoding '+fields['encoding']+b'\n')
            emit(b'data '+str(len(clean_message)).encode()+b'\n'+clean_message+b'\n')
            if parents:emit(b'from :'+str(commit_marks[parents[0]]).encode()+b'\n')
            for parent in parents[1:]:emit(b'merge :'+str(commit_marks[parent]).encode()+b'\n')
            emit(b'deleteall\n')
            for path,mode,mark,_ in allowed:emit(b'M '+mode.encode()+b' :'+str(mark).encode()+b' '+quoted(path)+b'\n')
            emit(b'\n');importer.stdin.flush()
            row={'old_commit':old,'parents':parents,'retained_files':len(allowed),'omitted_files':omitted,'transformed_files':changed,'tree_sha256':sha(json.dumps([(x,y,w) for x,y,z,w in allowed],separators=(',',':')).encode()),'author_sha256':sha(fields['author']),'committer_sha256':sha(fields['committer']),'public_message_sha256':sha(clean_message),'message_changed':message!=clean_message}
            rows.append(row)
            save(reports/'progress.json',{'phase':'project_history','completed':index+1,'total':len(commits),'unique_input_objects':len(cache),'bytes_read':read_bytes})
            if index%10==0 or index+1==len(commits):print(json.dumps({'commit':index+1,'total':len(commits),'retained':len(allowed),'omitted':omitted,'transformed':changed}),flush=True)
        emit(b'done\n');importer.stdin.close();rc=importer.wait();log.close()
        if rc:raise RuntimeError('Unpublished history import failed')
    finally:reader.close()
    marks=dict(line.split() for line in marksfile.read_text().splitlines());mapping={old:marks[':'+str(mark)] for old,mark in commit_marks.items()}
    for line in refs.decode().splitlines():
        oid,ref=line.split()
        if ref.startswith('refs/heads/'):git(dst,'update-ref',ref,mapping[oid])
    git(dst,'update-ref','-d','refs/heads/projection-build');git(dst,'symbolic-ref','HEAD','refs/heads/main')
    newreader=Reader(dst)
    try:
        for row in rows:
            new=mapping[row['old_commit']];fields,parents,message=commit_parts(newreader.get(new))
            if parents!=[mapping[p] for p in row['parents']]:raise RuntimeError('Parent graph mismatch')
            if sha(fields['author'])!=row['author_sha256'] or sha(fields['committer'])!=row['committer_sha256'] or sha(message)!=row['public_message_sha256']:raise RuntimeError('Commit metadata mismatch')
            actual=list(tree(dst,new))
            if sha(json.dumps(actual,separators=(',',':')).encode())!=row['tree_sha256']:raise RuntimeError('Projected tree mismatch')
            row['new_commit']=new;row['verified']=True
    finally:newreader.close()
    if git(src,'rev-parse','HEAD').decode().strip()!=head or git(src,'show-ref')!=refs or git(src,'status','--porcelain=v1','-z')!=status:raise RuntimeError('Source repository changed')
    if git(dst,'remote').strip() or (dst/'.git/objects/info/alternates').exists():raise RuntimeError('Destination isolation failure')
    if int(git(dst,'rev-list','--count','--all'))!=len(commits):raise RuntimeError('Reachable source commits lack an explicitly preserved destination ref')
    git(dst,'fsck','--full','--no-reflogs')
    # This is the newly-created, validated destination only; no source checkout reset.
    git(dst,'reset','--hard','HEAD')
    save(reports/'commit-map.json',mapping);save(reports/'omissions.json',exclusions);save(reports/'transformations.json',list(transforms.values()));save(reports/'commit-verification.json',rows)
    result={'schema':'mattersyn-history-repair/1','status':'verified_offline','kind':a.kind,'original_head':head,'public_head':mapping[head],'original_commit_count':len(commits),'public_commit_count':int(git(dst,'rev-list','--count','--all')),'omitted_path_count':len(exclusions),'transformed_path_version_count':len(transforms),'policy_sha256':sha(module_path.read_bytes()),'config_sha256':sha(Path(a.config).read_bytes()),'source_unchanged':True,'remote_configured':False,'original_evidence_retained_privately':True,'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save(reports/'verification.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':
    try:run()
    except Exception as e:
        print(type(e).__name__+': history projection stopped; no source contents logged',file=sys.stderr);raise SystemExit(1)
