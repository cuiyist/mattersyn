"""Bounded private long-path fixture checks; no production sync or deletion."""
from pathlib import Path
import importlib.util,sys,json,hashlib,subprocess,os,copy,uuid
from datetime import datetime,timezone
A=Path(__file__).resolve().parent;R=A.parent;DESKTOP=R.parents[1]
sys.path.insert(0,str(R))
spec=importlib.util.spec_from_file_location('sync_under_test',R/'sync_github_public.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[];notes=[]
def ck(v,t):checks.append({'ok':bool(v),'check':t})
fixture=DESKTOP/('mattersyn-long-path-audit-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:6])
src=fixture/'source';dest=fixture/'destination';site=fixture/'site-destination'
def extended(p):
    q=os.path.abspath(str(p));return Path('\\\\?\\'+q) if os.name=='nt' and not q.startswith('\\\\?\\') else Path(q)
for p in [src/'research-assets',dest/'.git',site/'.git']:
    extended(p).mkdir(parents=True,exist_ok=True)
deep=Path('research-assets')
for i in range(6):deep/=f'context-{i}-'+'a'*48
deep/='selected-figure-identity.json'
payload=b'{"schema":"audit-fixture/1","value":17,"unit":"nm","source":"selected-facts-only"}\n'
short='research-assets/selected-fact.json'; excluded={'research-assets/paper.pdf':b'%PDF-synthetic-fixture','research-assets/private/text/main-01.txt':b'synthetic fixture only','.env':b'FAKE_LOCAL_FIXTURE=yes\n'}
for rel,data in [(deep,payload),(Path(short),payload),*( (Path(k),v) for k,v in excluded.items())]:
    p=extended(src/rel);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
mod.ROOT=src;mod.DEST={'project':dest,'site':site}
gitcalls=[]
def fakegit(p,*args):
    gitcalls.append({'logical_dest':str(p),'args':list(args)})
    if args==('remote',):return b''
    if args==('ls-files','-z'):return b''
    raise AssertionError('Unexpected command; real Git/network not allowed in fixture')
mod.git=fakegit
io=mod.io_path(dest/deep.parent/'io-only-probe.json');io.parent.mkdir(parents=True,exist_ok=True);io.write_bytes(payload)
ck(io.read_bytes()==payload,'actual extended destination read/write at >260 characters')
ck(len(str(dest/deep))>260,'destination fixture exceeds Windows MAX_PATH')
ck(mod.io_path(io)==io,'helper idempotent on already-prefixed path')
walkerrors=[];walked=[]
for directory,ds,fs in os.walk(src,onerror=lambda e:walkerrors.append({'type':type(e).__name__,'errno':e.errno,'filename':str(e.filename)})):
    walked += [Path(directory)/n for n in fs]
unprefixed_reaches_long_source=src/deep in walked
rows,omissions=mod.collect('project');rels={x[0] for x in rows}
ck(deep.as_posix() in rels,'collector retains long source file')
ck(short in rels,'collector retains ordinary source file')
for rel in excluded:ck(rel in {x['path'] for x in omissions},'unchanged exclusion '+rel)
ck(all(not x.startswith('\\\\?\\') and ':' not in x for x in rels),'collector exports only logical relative paths')
# A symlink is tested when the host permits unprivileged creation.
symlink=src/'research-assets/linked-fact.json'
try:
    symlink.symlink_to(src/short)
    old_gate=symlink.is_symlink();new_gate=mod.io_path(symlink).is_symlink()
    ck(old_gate and new_gate,'file-symlink exclusion survives I/O normalization')
    rr,oo=mod.collect('project');ck('research-assets/linked-fact.json' in {x['path'] for x in oo},'actual collector excludes file symlink')
except OSError as e:
    notes.append({'scope':'symlink creation not permitted by host','exception':type(e).__name__,'winerror':getattr(e,'winerror',None),'verification':'No actual-symlink runtime pass claimed; non-dereferencing helper verified separately by code and explicit resolver trap.'})
try:
    mod.sync('project')
    report=json.loads((src/'research-assets/github-public-project-sync.json').read_text(encoding='utf-8'))
    ck(deep.as_posix() in {x['path'] for x in report['changed_or_added']},'sync actually copies deep file on first pass')
    ck(all(not x['path'].startswith('\\\\?\\') for x in report['changed_or_added']),'physical prefixes absent from changed-file metadata')
    ck(not report['destination'].startswith('\\\\?\\') and not report['source_root'].startswith('\\\\?\\'),'physical prefixes absent from source/destination metadata')
    ck(extended(dest/deep).read_bytes()==payload,'final copied deep file bytes unchanged')
except Exception as e:notes.append({'scope':'actual fixture sync','exception':type(e).__name__,'message':str(e)});ck(False,'fixture sync completes')
# Exercise Site projection with a separate source tree and only synthetic content.
webroot=src/'recipe-atlas/dist';webdeep=Path(*deep.parts[1:])
for rel,data in [(webdeep,b'{"value":17,"firstPagePreviewPrivate":"synthetic private field"}'),(Path('index.html'),('<a href="'+mod.OLD_URL+'/dataset">Records</a>').encode())]:
    p=extended(webroot/rel);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
mod.sync('site')
sr=json.loads((src/'research-assets/github-public-site-sync.json').read_text(encoding='utf-8'))
ck(json.loads(extended(site/webdeep).read_bytes())=={'value':17},'long Site JSON keeps reviewed content transformation')
ck(mod.NEW_URL.encode() in (site/'index.html').read_bytes() and mod.OLD_URL.encode() not in (site/'index.html').read_bytes(),'existing Site URL transformation unchanged')
ck(all(not x['path'].startswith('\\\\?\\') and ':' not in x['path'] for x in sr['changed_or_added']),'Site public metadata keeps logical relative paths')
ck((site/'.nojekyll').is_file(),'Site marker generated in scratch destination')
# The helper is invoked only after the existing resolved-containment guard in deletion.
code=(R/'sync_github_public.py').read_text(encoding='utf-8')
class ResolverTrap:
    def absolute(self):return src/'research-assets/synthetic-link-name.json'
    def resolve(self):raise AssertionError('Helper must not dereference a link')
ck(str(mod.io_path(ResolverTrap())).endswith('synthetic-link-name.json'),'helper absolute path preserves link pathname without resolve')
ck(code.index('if dest.resolve() not in target.parents')<code.index('physical=io_path(target)'),'deletion containment guard precedes extended-path helper')
ck('physical.unlink()' in code and 'rmtree' not in code,'only individually bounded unlink; no recursive deletion')
repo=DESKTOP/'mattersyn-github-project'
oldpolicy=subprocess.run([mod.GIT,'-c','safe.directory='+repo.as_posix(),'-C',str(repo),'show','HEAD:research-assets/public_projection_policy.py'],capture_output=True,check=True).stdout
ck(hashlib.sha256(oldpolicy).hexdigest()==sha(R/'public_projection_policy.py'),'publication policy bytes unchanged from current project HEAD')
result={'at':datetime.now(timezone.utc).isoformat(),'status':'passed' if all(x['ok'] for x in checks) else 'open_findings','fixture_root':str(fixture),'checks':checks,'unprefixed_source_walk_reaches_deep_file':unprefixed_reaches_long_source,'source_walk_errors':walkerrors,'notes':notes,'fixture_long_path_characters':len(str(dest/deep)),'git_calls_stubbed':gitcalls,'production_mutations':False,'recursive_deletion_performed':False,'bound_files':{str(p):sha(p) for p in [R/'sync_github_public.py',R/'public_projection_policy.py',Path(__file__)]}}
(A/'long-path-test-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in {'checks','bound_files','git_calls_stubbed'}}|{'failed_checks':[x['check'] for x in checks if not x['ok']],'check_count':len(checks)},indent=2))
