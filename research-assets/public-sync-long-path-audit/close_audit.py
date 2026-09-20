from pathlib import Path
import json,hashlib,subprocess,difflib,ast
from datetime import datetime,timezone
A=Path(__file__).resolve().parent;R=A.parent;M=R.parent;D=M.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
test=read(A/'long-path-test-result.json');assert test['status']=='passed'
for p,h in test['bound_files'].items():assert sha(Path(p))==h,p
git=[r'C:\Program Files\Git\cmd\git.exe','-c','safe.directory='+(D/'mattersyn-github-project').as_posix(),'-C',str(D/'mattersyn-github-project')]
commit=subprocess.run(git+['rev-parse','HEAD'],capture_output=True,check=True).stdout.decode().strip()
old=subprocess.run(git+['show','HEAD:research-assets/sync_github_public.py'],capture_output=True,check=True).stdout
new=(R/'sync_github_public.py').read_bytes()
diff=''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile='project HEAD sync_github_public.py',tofile='current local sync_github_public.py'))
(A/'reviewed-code-delta.diff').write_text(diff,encoding='utf-8')
trees=[ast.parse(x) for x in [old.decode(),new.decode()]]
functions=[{x.name:ast.dump(x,include_attributes=False) for x in t.body if isinstance(x,ast.FunctionDef)} for t in trees]
changed=sorted(k for k in functions[0] if functions[0][k]!=functions[1][k]);assert changed==['collect','sync'];assert set(functions[1])-set(functions[0])=={'io_path'}
constants=[[(ast.dump(x,include_attributes=False)) for x in t.body if not isinstance(x,ast.FunctionDef)] for t in trees];assert constants[0]==constants[1]
frozen=M/'research-assets/incoming-paper-monitor/batches/20260920-rolling-pipeline/acs.inorgchem.7b01711/site-integration-proposal/sync-github-before-symlink-correction.py'
bound={**test['bound_files'],str(A/'long-path-test-result.json'):sha(A/'long-path-test-result.json'),str(A/'reviewed-code-delta.diff'):sha(A/'reviewed-code-delta.diff'),str(Path(__file__)):sha(Path(__file__))}
if frozen.exists():bound[str(frozen)]=sha(frozen)
report={'schema':'mattersyn.independent_public_sync_long_path_audit/1','at':datetime.now(timezone.utc).isoformat(),'auditor':'/root/norberg2004_extract','author':'/root','status':'passed','open_findings':[],
 'script_sha256':sha(R/'sync_github_public.py'),'policy_sha256':sha(R/'public_projection_policy.py'),'baseline_project_commit':commit,'baseline_script_sha256':hashlib.sha256(old).hexdigest(),
 'scope':'Bounded review of Windows extended-path filesystem I/O for the existing local-drive MatterSyn project and website projections. No production sync, source change, Git mutation, network operation or recursive deletion was performed by this auditor.',
 'reviewed_code_delta':{'new_function':'io_path','modified_functions':changed,'other_functions_and_top_level_policy_constants_unchanged':True,'policy_module_bytes_unchanged_from_project_HEAD':True},
 'runtime_test':{'status':'passed','checks':len(test['checks']),'long_destination_characters':test['fixture_long_path_characters'],'fixture_root':test['fixture_root'],'actual_project_sync':True,'actual_site_sync':True,'git_and_network_stubbed':True,'production_roots_rebound_to_scratch':True,'recursive_deletion':False},
 'resolved_findings':[
  {'id':'LONGPATH-01','finding':'Initial io_path used resolve() before is_symlink(), dereferencing the object before the exclusion check.','resolution':'Root preserved the initial revision and changed the helper to absolute(). Code review and a resolver-trap test confirm no dereference occurs in helper; source symlink check still receives the original pathname.','runtime_qualification':'Host rejected creation of a real file symlink with WinError 1314. No actual-file-symlink execution pass is claimed.'},
  {'id':'LONGPATH-02','finding':'An unprefixed os.walk silently omitted the deep source subtree on this Windows runtime; an explicit onerror probe exposed FileNotFoundError.','resolution':'Root now walks the extended source root, derives relative paths against the same physical walk root, and constructs logical source/relative paths for policy and metadata. Actual 484-character fixture is discovered, read and copied by both corrected sync modes.'}
 ],
 'verified':[
  'Actual extended-path mkdir/write/read and copying with logical destination paths exceeding 260 characters.',
  'Corrected source traversal reaches the deep JSON fixture; ordinary source files are still included.',
  'PDF, raw page-text and .env fixtures are excluded under the unchanged rules.',
  'The existing JSON private-field filter and Site URL replacement behave identically in long-path fixture projection.',
  'Relative file paths in both reports and source_root/destination remain logical, without Windows extended-path prefixes.',
  'Deletion still resolves and verifies containment in the isolated destination before calling the physical-path helper, and uses only individual file unlink. No deletion was exercised or performed by this audit.',
  'All top-level constants and all functions other than collect/sync are unchanged from the repository baseline; io_path is the only new function. The public projection policy module is byte-identical to that baseline.'
 ],
 'limitations':[
  'Real symlink creation was denied by the host; the correction is reviewed statically and tested with a resolver trap, not falsely reported as a real symlink test.',
  'Scope is the configured Windows local-drive roots. UNC/network paths and path components exceeding filesystem component-length limits were not tested.',
  'This does not certify corpus completeness, credentials/PII beyond the existing policy, live publication or the outcome of root’s production sync. Existing os.walk permission-error behavior was not broadened by this patch.'
 ],'bound_files':bound}
out=R/'public-sync-long-path-audit.json';out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
(R/'public-sync-long-path-audit.md').write_text(f'''# Public sync long-path audit

**Passed** for the current configured Windows local-drive roots. No open findings.

The initial helper could dereference a file symlink before exclusion, and the unprefixed source walk could silently omit deep folders. Root corrected both while preserving the prior revision. The publication-policy module remains byte-identical to project commit `{commit}`.

Actual synthetic project and website syncs passed {len(test['checks'])} checks, including a {test['fixture_long_path_characters']}-character destination, source discovery, copy/read/write, original exclusions, JSON filtering and URL conversion. Public/report metadata retain logical relative paths. The existing resolved containment guard still precedes individual-file deletion. No production repository, source file or network operation was touched; no recursive deletion occurred.

Host permissions denied real symlink creation (WinError 1314). The non-dereferencing fix is verified by code and a resolver trap; no real-symlink execution pass is claimed. UNC paths and corpus-wide completeness are outside scope.

Script SHA256: `{report['script_sha256']}`

Audit SHA256: `{sha(out)}`
''',encoding='utf-8')
print(json.dumps({'status':'passed','audit_sha256':sha(out),'script_sha256':report['script_sha256'],'checks':len(test['checks'])},indent=2))
