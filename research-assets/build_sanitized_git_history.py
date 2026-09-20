"""Build a new local Git history with only policy-qualified blobs.

Reads the original repository with cat-file/ls-tree only. The destination must not
exist. No cloning, alternates, remote configuration, old Git writes, or pushing.
"""
from pathlib import Path
import argparse, subprocess, json, hashlib, os, sys, datetime, collections
import public_projection_policy as policy

def git(repo,*args,input=None):
    p=subprocess.run(['git','-c','safe.directory='+Path(repo).as_posix(),'-C',str(repo),*args],input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode:raise RuntimeError('Git operation failed: '+args[0]+' (details withheld; no source values logged)')
    return p.stdout
def digest(raw):return hashlib.sha256(raw).hexdigest()
def quote_git_path(path):
    out=bytearray(b'"')
    for b in path.encode('utf-8'):
        if b in (34,92):out.extend(b'\\'+bytes([b]))
        elif 32<=b<127:out.append(b)
        else:out.extend(('\\%03o'%b).encode('ascii'))
    out.extend(b'"');return bytes(out)
def write_json(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
class ObjectReader:
    def __init__(self,repo):self.p=subprocess.Popen(['git','-C',str(repo),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    def get(self,oid):
        self.p.stdin.write(oid.encode()+b'\n');self.p.stdin.flush();header=self.p.stdout.readline().split()
        if len(header)!=3 or header[1] not in [b'blob',b'commit']:raise RuntimeError('Unexpected source Git object type')
        size=int(header[2]);raw=self.p.stdout.read(size)
        if self.p.stdout.read(1)!=b'\n' or len(raw)!=size:raise RuntimeError('Truncated Git object')
        return raw
    def close(self):self.p.stdin.close();self.p.wait()
def tree(repo,commit):
    rows=[]
    for row in git(repo,'ls-tree','-rz','--full-tree',commit).split(b'\0'):
        if not row:continue
        meta,name=row.split(b'\t',1);mode,kind,oid=meta.split()
        if kind!=b'blob' or mode not in [b'100644',b'100755']:raise RuntimeError('Unsupported symlink/submodule/tree entry; review required')
        path=name.decode('utf-8');policy.normalize_path(path);rows.append((path,mode.decode(),oid.decode()))
    return rows
def commit_data(raw):
    header,message=raw.split(b'\n\n',1);fields={};parents=[]
    for row in header.splitlines():
        if row.startswith(b'parent '):parents.append(row[7:].decode())
        elif row.startswith((b'author ',b'committer ',b'encoding ')):
            key,value=row.split(b' ',1);fields[key.decode()]=value
        elif row.startswith(b'gpgsig '):raise RuntimeError('Signed commit needs explicit signature-rewrite handling')
    if not all(k in fields for k in ['author','committer']):raise RuntimeError('Missing commit identity')
    return fields,parents,message
def self_test():
    assert policy.exclude_path('.git/config')
    assert policy.exclude_path('research-assets/new-cache/main-33.png')
    assert policy.exclude_path('downloaded_papers/source.pdf')
    assert policy.exclude_path('research-assets/new-source.pdf.txt')
    assert policy.exclude_path('research-assets/private/text/new.tmp')
    assert policy.exclude_path('research-assets/reader-assets/figure-3.png') is None
    assert policy.exclude_path('MEMORY.md') is None
    assert policy.exclude_path('skills/example/SKILL.md') is None
    raw=b'{"metadata":{"firstPagePreviewPrivate":"omitted","value":12},"nested":[{"firstPagePreviewPrivat\\u0065":"omitted2"}],"public_asset":"assets/figures/norberg2004/pages/si-01.png","locator":"SI p1","facts":[1]}'
    clean,stats=policy.project_bytes('data/example.json',raw);d=json.loads(clean)
    assert stats['private_fields_removed']==2 and stats['page_attachments_removed']==1
    assert d=={'metadata':{'value':12},'nested':[{}],'locator':'SI p1','facts':[1]}
    assert policy.transform_bytes('data/example.json',clean)==clean
    unchanged=b'{"value": 2}\r\n';assert policy.transform_bytes('data/example.json',unchanged)==unchanged
    for rel,raw in [('data/bad.json',b'{bad'),('code.txt',b'%PDF-1.0'),('test.txt',b'ghp_'+b'A'*36)]:
        try:policy.transform_bytes(rel,raw)
        except policy.ProjectionError:pass
        else:raise AssertionError('Fail-closed gate not triggered')
    return {'status':'passed','scopes':['path rules','Git metadata','unchanged bytes','recursive and escaped JSON keys','Norberg attachment-only removal','idempotency','invalid JSON','unclassified PDF','credential gate']}

def build(args):
    source=Path(args.source).resolve();dest=Path(args.destination).resolve();reportdir=Path(args.report_dir).resolve()
    if dest.exists():raise RuntimeError('Destination already exists; builder will not overwrite it')
    if dest==source or source in dest.parents or dest in source.parents:raise RuntimeError('Source and destination must be distinct sibling repositories')
    policy_info=policy.policy_metadata();tests=self_test()
    head=git(source,'rev-parse','HEAD').decode().strip();old_refs=git(source,'show-ref').decode().splitlines();old_status=git(source,'status','--porcelain=v1','-z')
    expected=json.loads((Path(policy.__file__).resolve().parent/policy.REPORT_RELATIVE).read_bytes())
    if head!=expected['head']:raise RuntimeError('Source HEAD differs from reviewed exclusion report')
    commits=git(source,'rev-list','--reverse','--topo-order','--all').decode().splitlines()
    if len(commits)!=expected['commit_count']:raise RuntimeError('Unexpected reachable source commit count')
    dest.mkdir();reportdir.mkdir(parents=True,exist_ok=True)
    git(dest,'init','--initial-branch=main');git(dest,'config','core.autocrlf','false');git(dest,'config','core.longpaths','true')
    marks_path=reportdir/'fast-import-marks.txt';log=open(reportdir/'fast-import.stderr.log','wb')
    fi=subprocess.Popen(['git','-C',str(dest),'fast-import','--quiet','--date-format=raw','--export-marks='+str(marks_path)],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=log)
    reader=ObjectReader(source);nextmark=1;blob_cache={};commit_marks={};rows_report=[];transforms=[];excluded=set();secret_scanned=0;readbytes=0
    def send(raw):fi.stdin.write(raw)
    try:
        for ci,old in enumerate(commits):
            fields,parents,message=commit_data(reader.get(old));allowed=[];removed=[];changed=[]
            for path,mode,oid in tree(source,old):
                reason=policy.exclude_path(path)
                if reason:removed.append({'path':path,'reason':reason});excluded.add(path);continue
                # Content projection only depends on JSON classification, not filename identity.
                cachekey=(oid,Path(path).suffix.lower(),'.json.' in path.lower())
                if cachekey not in blob_cache:
                    raw=reader.get(oid);readbytes+=len(raw);clean,stats=policy.project_bytes(path,raw);secret_scanned+=1
                    mark=nextmark;nextmark+=1
                    send(b'blob\nmark :'+str(mark).encode()+b'\ndata '+str(len(clean)).encode()+b'\n'+clean+b'\n')
                    newoid=hashlib.sha1(b'blob '+str(len(clean)).encode()+b'\0'+clean).hexdigest()
                    blob_cache[cachekey]=(mark,newoid,stats,digest(raw),digest(clean))
                mark,newoid,stats,oldsha,newsha=blob_cache[cachekey];allowed.append((path,mode,mark,newoid))
                if stats['changed']:changed.append({'path':path,'old_git_blob':oid,'new_git_blob':newoid,'old_sha256':oldsha,'new_sha256':newsha,'removed_private_fields':stats['private_fields_removed'],'removed_page_attachments':stats['page_attachments_removed']})
            cm=nextmark;nextmark+=1;commit_marks[old]=cm
            send(b'commit refs/heads/projection-build\nmark :'+str(cm).encode()+b'\nauthor '+fields['author']+b'\ncommitter '+fields['committer']+b'\n')
            if 'encoding' in fields:send(b'encoding '+fields['encoding']+b'\n')
            send(b'data '+str(len(message)).encode()+b'\n'+message+b'\n')
            if parents:send(b'from :'+str(commit_marks[parents[0]]).encode()+b'\n')
            for parent in parents[1:]:send(b'merge :'+str(commit_marks[parent]).encode()+b'\n')
            send(b'deleteall\n')
            for path,mode,mark,newoid in allowed:
                send(b'M '+mode.encode()+b' :'+str(mark).encode()+b' '+quote_git_path(path)+b'\n')
            send(b'\n');fi.stdin.flush()
            rows_report.append({'old_commit':old,'new_commit_mark':cm,'parent_old_commits':parents,'retained_files':len(allowed),'excluded_files':len(removed),'transformed_files':len(changed),'retained_tree_expected_sha256':digest(json.dumps([(p,m,o) for p,m,_,o in allowed],separators=(',',':')).encode()),'author_line_sha256':digest(fields['author']),'committer_line_sha256':digest(fields['committer']),'message_sha256':digest(message),'excluded_paths':removed,'transformed_paths':changed})
            write_json(reportdir/'progress.json',{'phase':'import','completed_commits':ci+1,'total_commits':len(commits),'current_old_commit':old,'unique_content_objects_qualified':secret_scanned,'source_content_bytes_read':readbytes})
            print(json.dumps({'commit':ci+1,'retained':len(allowed),'excluded':len(removed),'transformed':len(changed)}),flush=True)
        send(b'done\n');fi.stdin.close();rc=fi.wait();log.close()
        if rc:raise RuntimeError('fast-import failed; destination is an unpublished partial build')
    finally:reader.close()
    marks=dict(line.split() for line in marks_path.read_text().splitlines());mapping={old:marks[':'+str(mark)] for old,mark in commit_marks.items()}
    git(dest,'update-ref','refs/heads/main',mapping[head]);git(dest,'update-ref','-d','refs/heads/projection-build');git(dest,'symbolic-ref','HEAD','refs/heads/main')
    # Preserve additional local branch names only. Do not copy source remote refs/config.
    for refline in old_refs:
        oid,ref=refline.split()
        if ref.startswith('refs/heads/') and ref!='refs/heads/main':git(dest,'update-ref',ref,mapping[oid])
        elif ref.startswith('refs/tags/'):raise RuntimeError('Tag preservation requires explicit tag review')
    validation=[];newreader=ObjectReader(dest)
    try:
        for row in rows_report:
            old=row['old_commit'];new=mapping[old];row['new_commit']=new
            fields,parents,message=commit_data(newreader.get(new))
            if [mapping[p] for p in row['parent_old_commits']]!=parents:raise RuntimeError('Parent ancestry mismatch')
            if digest(fields['author'])!=row['author_line_sha256'] or digest(fields['committer'])!=row['committer_line_sha256'] or digest(message)!=row['message_sha256']:raise RuntimeError('Commit metadata mismatch')
            actual=tree(dest,new)
            if any(policy.exclude_path(p) for p,_,_ in actual):raise RuntimeError('Excluded path survived in a public commit')
            if digest(json.dumps(actual,separators=(',',':')).encode())!=row['retained_tree_expected_sha256']:raise RuntimeError('Projected file mode/path/blob tree mismatch')
            validation.append({'old_commit':old,'new_commit':new,'message_author_committer_dates_unchanged':True,'parents_mapped_exactly':True,'every_retained_path_mode_blob_matches_projection':True,'excluded_paths_absent':True})
    finally:newreader.close()
    if git(source,'rev-parse','HEAD').decode().strip()!=head or git(source,'show-ref').decode().splitlines()!=old_refs or git(source,'status','--porcelain=v1','-z')!=old_status:raise RuntimeError('Source repository state changed during build')
    if git(dest,'remote').strip():raise RuntimeError('Unexpected destination remote')
    if (dest/'.git/objects/info/alternates').exists():raise RuntimeError('Unexpected object-store alternate')
    git(dest,'fsck','--full','--no-reflogs')
    git(dest,'reset','--hard','HEAD')
    write_json(reportdir/'commit-map.json',mapping)
    write_json(reportdir/'history-projection-detail.json',{'commits':rows_report,'validation':validation})
    result={'schema':'mattersyn-sanitized-history-build/1','status':'passed_offline_history_projection','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_repository':str(source),'destination_repository':str(dest),'source_head':head,'sanitized_head':mapping[head],'source_commit_count':len(commits),'sanitized_commit_count':int(git(dest,'rev-list','--count','--all')),'historical_excluded_path_union':len(excluded),'expected_baseline_exclusions':policy.EXPECTED_EXCLUDED_PATHS,'current_retained_files':rows_report[-1]['retained_files'],'current_excluded_files':rows_report[-1]['excluded_files'],'current_transformed_files':rows_report[-1]['transformed_files'],'unique_qualified_content_objects':secret_scanned,'source_content_bytes_read':readbytes,'metadata_and_tree_validated_commits':len(validation),'original_checkout_refs_head_index_status_unchanged':True,'destination_has_no_remotes':True,'separate_object_store_no_alternates':True,'git_fsck_passed':True,'policy':policy_info,'policy_self_tests':tests,'scientific_audit_recertification':False,'limits':['Only reviewed source-equivalent path rules and recursive private field projection applied; arbitrary future embedded source formats require a new content review.','Selected scientific figures, typed data, audit provenance, code, memory and skills retained. Historical scientific input hashes are not rewritten as if transformed public bytes had been independently scientifically audited.','No remote operations, pushes, repository visibility changes or deployments performed.'],'bound_files':{str(Path(policy.__file__).resolve()):digest(Path(policy.__file__).read_bytes()),str(Path(__file__).resolve()):digest(Path(__file__).read_bytes()),str(reportdir/'commit-map.json'):digest((reportdir/'commit-map.json').read_bytes()),str(reportdir/'history-projection-detail.json'):digest((reportdir/'history-projection-detail.json').read_bytes())}}
    if len(excluded)<policy.EXPECTED_EXCLUDED_PATHS:raise RuntimeError('Not all reviewed excluded historical paths were encountered')
    write_json(reportdir/'sanitized-history-report.json',result)
    print(json.dumps({k:result[k] for k in ['status','sanitized_head','source_commit_count','sanitized_commit_count','historical_excluded_path_union','current_retained_files','current_transformed_files']},indent=2),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',required=True);ap.add_argument('--destination',required=True);ap.add_argument('--report-dir',required=True);ap.add_argument('--self-test-only',action='store_true');args=ap.parse_args()
    try:
        if args.self_test_only:print(json.dumps(self_test(),indent=2))
        else:build(args)
    except Exception as exc:
        # Do not echo arbitrary exception payloads from parsers or subprocesses.
        if isinstance(exc,(policy.ProjectionError,RuntimeError)):print(type(exc).__name__+': '+str(exc),file=sys.stderr)
        else:print(type(exc).__name__+': history projection stopped; inspect code without logging source values',file=sys.stderr)
        raise SystemExit(1)
