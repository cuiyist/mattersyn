from pathlib import Path
import ast,json,hashlib,datetime
A=Path(__file__).resolve().parent;N=A.parent;S=Path('[local path redacted]')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[];bound={};code={}
def ck(n,v):checks.append({'check':n,'passed':bool(v)})
for name in ['import_reviewed_pati.py','build_pati_inventory.py','build_and_check_site.py']:
 p=N/name;bound[str(p)]=sha(p);t=p.read_text('utf8');ast.parse(t);ck('Valid Python syntax '+name,True);code[name]=t
tree=ast.parse(code['import_reviewed_pati.py']);rel=None;edits=[];state={}
for n in tree.body:
 if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='rel':
  try:rel=ast.literal_eval(n.value)
  except (ValueError,TypeError):pass
 if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Name)and n.value.func.id=='edit':
  call=n.value;args=[]
  for arg in call.args:args.append(rel if isinstance(arg,ast.Name)and arg.id=='rel'else ast.literal_eval(arg))
  filename,before,after=args[:3];count=args[3]if len(args)>3 else 1
  if filename not in state:
   # Independent pre-import snapshot remains stable after the real import.
   p=A/'independent-baseline'/filename;state[filename]=p.read_text('utf8');bound[str(p)]=sha(p)
  ck('Exact old code anchor '+filename+' '+before[:45],state[filename].count(before)==count);state[filename]=state[filename].replace(before,after);edits.append({'file':filename,'before':before,'after':after,'occurrences':count})
assert len(edits)==11
for filename,t in state.items():
 if filename.endswith('.py'):ast.parse(t);ck('Simulated patched Python syntax '+filename,True)
manual=['Read the complete root import, inventory and build helpers. Import requires exact passed promotion and product freezes before mutation.','All existing607 canonical hashes are captured and asserted unchanged; candidate copies reject unequal path collisions.','Registry, record/stock/product bindings and source-specific display maps append with existing-key rejection; only19 Pati records are admitted.','Exact source-specific protocol API precedes older-source fallbacks, and repeated generic conditions are bypassed when the Pati scene matches.','The reader relation alias is gated by source group pati2009 and exact stale token private_unapproved_reader.','TEA stale model-approval note suppression is gated by source group and exact literal note; all scientific source/canonical text remains intact and independently qualified reference captions retain the printed-formula conflict.','Site integration gate can become true locally; browser/publication flags remain false in imported reader. Registry published flags denote installed references, not evidence of anonymous deployment.','Inventory derives corpus/library, per-paper and per-material categories from actual generated artifacts, while full-corpus recipe/material totals remain unknown.','No training requests, atomic coordinates, source sample joins or physical replicate labels are added by the import.','Build helper uses established builders, static/quality/quantity/scope/role checks and syntax checks; no browser approval is inferred.']
r={'schema':'mattersyn-independent-import-code-preflight/1','auditor':'/root/norberg2004_extract','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed'if all(x['passed']for x in checks)else'open_findings','checks':checks,'check_count':len(checks),'manual_scope':manual,'expected_code_edits':edits,'bound_files':bound,'scope':'Static/read-only helper review and exact baseline edit simulation. Actual import/transport/browser checks remain pending.'}
(A/'import-code-precheck.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'status':r['status'],'checks':len(checks),'sha256':sha(A/'import-code-precheck.json')}))
