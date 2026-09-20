"""Bounded pre-import code audit; never executes the import or edits Site."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,subprocess
H=Path(__file__).resolve().parents[1];O=Path(__file__).resolve().parent;S=Path('[local path redacted]');P=H/'site-integration-proposal'
NODE=Path('[local path redacted]')
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[];bound={}
def ck(ok,label):
 checks.append({'check':label,'passed':bool(ok)})
 if not ok:raise AssertionError(label)
def bind(p):bound[str(p)]=sha(p)
script=H/'import_reviewed_heo.py';inventory=H/'build_heo_inventory.py';tree=ast.parse(script.read_text(encoding='utf-8'));ast.parse(inventory.read_text(encoding='utf-8'));bind(script);bind(inventory)
# Independently simulate only the literal text replacements on private copies.
targets=['protocol-visuals.mjs','crystal-viewer.mjs','source-evidence.mjs','illustrated-record.mjs']
state={n:(S/'dist'/n).read_text(encoding='utf-8') for n in targets}
for n in targets:bind(S/'dist'/n)
current=None;env={};counts=[]
for stmt in tree.body:
 if isinstance(stmt,ast.Assign):
  names=[x.id for x in stmt.targets if isinstance(x,ast.Name)]
  if 'p' in names:
   values=[x.value for x in ast.walk(stmt.value) if isinstance(x,ast.Constant) and isinstance(x.value,str)]
   current=next((v.split('/')[-1] for v in values if v.split('/')[-1] in targets),None)
  if 'anchor' in names and isinstance(stmt.value,ast.Constant):env['anchor']=stmt.value.value
  if 'insertion' in names and isinstance(stmt.value,ast.Constant):env['insertion']=stmt.value.value
  if 'text' in names and current:
   v=stmt.value
   if isinstance(v,ast.BinOp) and isinstance(v.op,ast.Add) and isinstance(v.left,ast.Constant):state[current]=v.left.value+state[current]
   if isinstance(v,ast.Call) and isinstance(v.func,ast.Attribute) and v.func.attr=='replace':
    args=[x.value if isinstance(x,ast.Constant) else env.get(x.id) if isinstance(x,ast.Name) else None for x in v.args]
    if len(args)==2 and all(isinstance(x,str) for x in args):
     n=state[current].count(args[0]);ck(n==1,'Unique actual replacement anchor '+current+': '+args[0][:50]);counts.append({'file':current,'anchor':args[0],'matches':n});state[current]=state[current].replace(*args)
for n,text in state.items():
 path=O/('simulated-'+n);path.write_text(text,encoding='utf-8');subprocess.run([str(NODE),'--check',str(path)],check=True,capture_output=True);ck(True,'Actual patched JS syntax '+n)
ck('if(await mountHeoAverage(host,r))return;await productIdentity(host,r);' in state['crystal-viewer.mjs'],'Source-specific average adapter selected before generic full occupancy')
ck("sourceId==='heo2003'&&item.id==='inventory-supporting_tables-0'" in state['source-evidence.mjs'],'Source-specific lazy SI insertion guard')
ck('const dl=heo?createHeo2003ConditionGrid(o,r):aerosol?' in state['protocol-visuals.mjs'],'Heo full condition rows selected')
ck('if(!aerosol&&!heo)for' in state['protocol-visuals.mjs'],'Generic temperature/time/pressure placeholders excluded from Heo')
ck('if(!heo){const env=' in state['protocol-visuals.mjs'],'Generic environment duplication excluded from Heo')
ck('if(heo||nagasaki||ribeiro||norberg)' in state['protocol-visuals.mjs'],'Heo diagram enlargement enabled')
ck('if(danek||dabbousi' in state['protocol-visuals.mjs'] and '||heo){const extra' not in state['protocol-visuals.mjs'],'Legacy extra condition branch not additionally enabled for Heo')
staged={p.stem:read(p) for p in (P/'records').glob('*.json')};old=list((S/'data/records').glob('*.json'))
ck(len(staged)==10 and len(old)==470,'Actual staged and old record counts')
ck(not set(staged)&{p.stem for p in old},'All ten staged record IDs new')
ck(all(r['quality']['requested_tasks']==[] for r in staged.values()),'Staged training tasks remain empty')
ck("assert all(sha(S/'data/records'/n)==h for n,h in before_records.items())" in script.read_text(),'Import asserts every old record hash unchanged')
reader=read(P/'promoted-reader/heo2003.json');bind(P/'promoted-reader/heo2003.json')
items=[i for s in reader['reader_sections'] for i in s['items']]
ck(len(items)==372,'Actual reader retains372 items')
ck(sum(i['id']=='inventory-supporting_tables-0' for i in items)==1,'One actual lazy SI target item')
figs=list((P/'dist').rglob('*'));figs=[p for p in figs if p.is_file()]
ck(len(figs)==16 and all(p.suffix=='.png' and p.parent.name=='heo2003' for p in figs),'Current staged source tree contains exactly16 selected PNGs')
ck(all(not p.name.startswith(('main-page','si-page')) for p in figs),'No named whole-page images in current staged public tree')
publicfiles=next(ast.literal_eval(x.value) for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id=='public_files' for y in x.targets))
manifest=read(H/'visuals/products/package-manifest.json');bind(H/'visuals/products/package-manifest.json')
for src,dst in publicfiles.items():
 ck(sha(H/src)==manifest['public_assets'][src],'Exact public viewer/data asset '+src);bind(H/src)
 ck('..' not in Path(dst).parts and not Path(dst).is_absolute(),'Public destination relative '+dst)
ck(set(publicfiles)==set(manifest['public_assets']),'Eight explicit viewer/data assets exactly match frozen public asset manifest')
for p in figs:bind(p)
# Evaluate the actual pure route-classification function without importing/mutating builders.
atlas=S/'scripts/build_atlas.py';bind(atlas);at=ast.parse(atlas.read_text(encoding='utf-8'));fn=next(n for n in at.body if isinstance(n,ast.FunctionDef) and n.name=='synthesis_route');ns={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-synthesis-route','exec'),ns)
route=staged['heo-2003-in66-route'];classified=ns['synthesis_route'](route)
findings=[]
if not classified:findings.append({'id':'route-discovery-training-coupling','severity':'blocking_for_material_discovery','script':'build_heo_inventory.py and actual scripts/build_atlas.py','evidence':'Actual synthesis_route returns false for heo-2003-in66-route because requested_tasks is empty and the selector requires precursor_selection. The import only adds a material display name; it does not modify this selector.','effect':'Heo route is counted as contextual control and no direct synthesis hub/card is produced.','required_change':'Separate reviewed route display eligibility from training admission, or add a narrowly scoped reviewed Heo route condition. Keep all Heo requested_tasks empty and all exact/DFT/task eligibility false.'})
notes=[{'id':'stage-tree-snapshot','status':'current_snapshot_checked','note':'Current O/dist tree has exactly16 source crops. The script recursively copies it rather than asserting its exact approved manifest; before invocation preserve/audit the staged snapshot or assert exact filenames/hashes.'},{'id':'audit-hash-gate','status':'scope_limit','note':'CLI gates inspect passed status but do not independently validate every audit bound-file hash. Parent must perform the separate exact-hash gate before import; this review does not approve scientific promotion.'},{'id':'retry-on-si-load','status':'nonblocking_robustness','note':'Lazy SI viewer sets started before loading and leaves it true on error. A transient failure cannot retry by reopening. Download/table fallback should remain accessible; successful normal fetch paths are correct.'}]
report={'schema':'mattersyn-independent-preimport-code-audit/1','auditor':'/root/peng1998_reader_assets','at':datetime.now(timezone.utc).isoformat(),'status':'findings_require_bounded_fix' if findings else 'passed_bounded_static_contract_review','scope':'Pre-import renderer contracts, URLs, actual staged counts and preservation checks; no Site execution, browser test, inventory build or scientific promotion audit.','checks':checks,'check_count':len(checks),'actual_route_classifier_result':classified,'findings':findings,'nonblocking_notes':notes,'replacement_anchors':counts,'bound_files':bound}
(O/'independent-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(O/'independent-audit.md').write_text('# Heo pre-import integration code review\n\n'+('One blocking discovery finding: the actual route selector rejects the task-empty Heo route. Preserve training exclusions and separately permit the reviewed route to appear.\n\n' if findings else 'Bounded checks passed.\n\n')+f'{len(checks)} checks passed on actual files. Source-specific crystal mounting, lazy SI item/paths, full protocol-condition selection and existing-record preservation are consistent. The staged public tree contains16 selected source crops plus8 explicitly whitelisted viewer/data assets. Patched private copies pass JavaScript syntax checks.\n\nNo Site/shared-state writes and no import/build/browser or scientific-promotion approval. See JSON for exact hashes and nonblocking robustness notes.\n',encoding='utf-8');print(json.dumps({'status':report['status'],'checks':len(checks),'findings':findings,'audit_sha256':sha(O/'independent-audit.json')}))
