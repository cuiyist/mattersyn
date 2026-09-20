from pathlib import Path
import ast,hashlib,json,datetime
P=Path('[local path redacted]');A=P/'site-integration-independent-audit';S=Path('[local path redacted]');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
script=P/'import_reviewed_matuhina.py';tree=ast.parse(script.read_text('utf-8'));texts={};checks=[];rel=None
for n in tree.body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='rel':rel=ast.literal_eval(n.value)
 if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='edit':
  args=[rel if isinstance(a,ast.Name) and a.id=='rel' else ast.literal_eval(a) for a in n.value.args];file,before,after=args[:3];count=args[3] if len(args)>3 else 1
  if file not in texts:texts[file]=(S/file).read_text('utf-8')
  found=texts[file].count(before);checks.append({'file':file,'expected':count,'actual':found,'passed':found==count,'before':before,'after':after});assert found==count
  texts[file]=texts[file].replace(before,after)
for rel,t in texts.items():
 p=A/'prospective-code'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t,'utf-8')
 if p.suffix=='.py':compile(t,str(p),'exec')
inputs={str(P/f):sha(P/f) for f in ['prepare_site_proposal.py','prepare_integration_helpers.py','import_reviewed_matuhina.py','build_matuhina_inventory.py','build_and_check_site.py']}
x={'schema':'mattersyn-independent-import-code-precheck/1','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed_pre_freeze_code_check_only','reviewer':'/root/norberg2004_extract','checks':checks,'input_hashes':inputs,'prospective_files':{rel:sha(A/'prospective-code'/rel) for rel in texts},'executed_root_script':False,'site_modified':False,'review_notes':['Read all five root helper scripts independently. Exact edit statements evaluated on in-memory Site baseline copies only.','All586 baseline records and eligibility frozen independently before import.','Private product fields dropped by explicit allowlist;47 selections/45 record-sample pairs remain distinguishable.','Old source dispatch precedence retained after new Matuhina exact-source handler. Generic conditions omitted only when source-specific scene selected.','No final proposal or integration approval before frozen input comparison and actual built state.']}
(A/'import-code-precheck.json').write_text(json.dumps(x,indent=2)+'\n','utf-8');print('literal edit checks',len(checks),'files',list(texts),'sha',sha(A/'import-code-precheck.json'))
