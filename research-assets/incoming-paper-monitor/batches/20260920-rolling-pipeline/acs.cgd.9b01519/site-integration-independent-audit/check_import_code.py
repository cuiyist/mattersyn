"""Independently replay only literal code substitutions in memory; never execute import."""
from pathlib import Path
from datetime import datetime,timezone
import ast,json,hashlib,subprocess
A=Path(__file__).resolve().parent;N=A.parent;S=Path('[local path redacted]')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[];bound={};projections={};replacements=[]
def ck(label,ok):
 checks.append({'check':label,'passed':bool(ok)})
 assert ok,label
def bind(p):bound[str(p)]=sha(p)
script=N/'import_reviewed_sommer.py';tree=ast.parse(script.read_text(encoding='utf8'));bind(script)
rel=None
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='rel' for t in node.targets):rel=ast.literal_eval(node.value)
 if not(isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='edit'):continue
 call=node.value;arg=call.args[0];path=rel if isinstance(arg,ast.Name) and arg.id=='rel' else ast.literal_eval(arg)
 before,after=map(ast.literal_eval,call.args[1:3]);count=ast.literal_eval(call.args[3]) if len(call.args)>3 else 1
 if path not in projections:projections[path]=(S/path).read_text(encoding='utf8');bind(S/path)
 ck(path+' exact old snippet '+str(len(replacements)),projections[path].count(before)==count)
 projections[path]=projections[path].replace(before,after);replacements.append({'file':path,'before':before,'after':after,'count':count})
for path,t in projections.items():
 out=A/'preimport-code-projection'/path;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(t,encoding='utf8');bind(out)
 if path.endswith('.py'):ast.parse(t);ck(path+' resulting Python parses',True)
 else:
  run=subprocess.run(['[local path redacted]','--check',str(out)],capture_output=True,text=True)
  ck(path+' resulting JavaScript parses',run.returncode==0)
mod=N/'visuals/apparatus/sommer2020-protocol.mjs';bind(mod);txt=mod.read_text(encoding='utf8')
for name in ['buildSommer2020Scene','createSommer2020Art','createSommer2020ConditionGrid']:ck('Exact apparatus export '+name,'export function '+name in txt)
symbols=read(N/'product-context-proposal/registry-additions.json')['entries'];ck('Exactly three product symbols',len(symbols)==3)
for e in symbols:
 ck('Symbol import suffix '+e['id'],e['id'].endswith('-observed-phase-symbol'))
 ck('Symbol only '+e['id'],not e['model3dPath'] and not e['model2dPath'])
 bind(N/'product-context-proposal'/e['svgPath']);ck('Audited symbol bytes '+e['id'],sha(N/'product-context-proposal'/e['svgPath'])==e['assetHashes']['svgPath'])
old=read(A/'pre-integration-baseline.json')
for name,h in old['previous_records'].items():ck('Prior record still unchanged '+name,sha(S/'data/records'/name)==h)
for rel,x in old['training_export_snapshots'].items():ck('Training export still unchanged '+rel,sha(S/rel)==x['sha256'])
for n in ['build_and_check_site.py','build_sommer_inventory.py','prepare_site_proposal.py']:
 p=N/n;ast.parse(p.read_text(encoding='utf8'));bind(p);ck(n+' parses',True)
code=script.read_text(encoding='utf8');inv=(N/'build_sommer_inventory.py').read_text(encoding='utf8')
ck('Audit gates precede imports',code.index("audit['status']=='passed'")<code.index("old={p.name"))
ck('Old record count and hash preservation explicit',"assert len(old)==567" in code and "assert all(sha(S/'data/records'/name)==h for name,h in old.items())" in code)
ck('Inventory exact source group',"newgroups=['sommer2020']" in inv and "expected_new=19" in inv)
ck('Inventory keeps unknown corpus outcomes',"ss['full_corpus_recipe_count']is None" in inv and "ss['full_corpus_distinct_synthesized_material_count']is None" in inv)
ck('Inventory derives task eligibility',"eligibility(r)[t]['eligible']" in inv)
bind(A/'pre-integration-baseline.json');bind(Path(__file__))
out={'schema':'mattersyn-preimport-code-review/1','author':'/root','auditor':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),'status':'passed_preimport_code_review','open_findings':[],'check_count':len(checks),'checks':checks,'literal_code_replacements':replacements,'manual_scope':['Read all of root prepare_site_proposal.py, import_reviewed_sommer.py, build_and_check_site.py and build_sommer_inventory.py.','Verified exact existing protocol hook sequence, Sommer scene/caption/grid dispatch, generic-condition suppression and inherited source-context expansion. Literal replacements replayed sequentially in private memory and syntax-checked.','Import requires exact passed promotion/product freezes, preserves 567 existing canonical record bytes, extends new-source-only maps, and copies only audited asset paths. Three exact product symbols are copied; no model data or scientific records altered.','Reader changes are status/audit metadata only; actual runtime, generated records, prior-source dispatch and training regression will be tested after import.','Inventory derives current categories and eligibility from canonical data; whole-corpus recipe and material totals remain unknown.'], 'bound_files':bound,'site_changed':False,'source_science_reaudit':False,'actual_integration_approved':False,'browser_approved':False}
(A/'preimport-code-review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':out['status'],'checks':len(checks),'sha256':sha(A/'preimport-code-review.json')}))
