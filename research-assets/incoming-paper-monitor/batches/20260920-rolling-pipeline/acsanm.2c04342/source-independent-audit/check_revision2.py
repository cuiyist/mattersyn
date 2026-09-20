import json,hashlib,difflib
from pathlib import Path
from datetime import datetime,timezone
A=Path(__file__).resolve().parent;P=A.parent;V=P/'source-revision-1'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[]
def ck(n,b):checks.append({'check':n,'passed':bool(b)})
old=load(V/'package-freeze.json');new=load(P/'package-freeze.json');history=load(P/'source-revision-2-delta.json')
ck('prior-freeze-exact',sha(V/'package-freeze.json')=='e57825801f343b57b48ff66722a686b9fda045a04baeb71c5d1fc946f75c0151')
ck('new-freeze-exact',sha(P/'package-freeze.json')=='20d153c4fb174bd5a0cfb92ebc35c0726c015a9debfd379515165db902dbda00')
for p,h in new['bound_files'].items():ck('current-bound-hash:'+p,sha(p)==h)
changed=[]
for p,h in old['bound_files'].items():
 if sha(p)!=h:changed.append(p)
 archived=V/Path(p).name
 ck('prior-hash-preserved-or-unchanged:'+p,sha(p)==h or (archived.is_file() and sha(archived)==h))
ck('only-facts-and-builder-changed',set(Path(p).name for p in changed)=={'source-facts.json','build_extraction.py'})
before=load(V/'source-facts.json');after=load(P/'source-facts.json');leaves=[];equal_leaves=0
def diff(a,b,ptr=''):
 global equal_leaves
 if type(a)!=type(b):leaves.append({'pointer':ptr,'before':a,'after':b});return
 if isinstance(a,dict):
  for k in set(a)|set(b):
   if k not in a or k not in b:leaves.append({'pointer':ptr+'/'+k,'before':a.get(k),'after':b.get(k)})
   else:diff(a[k],b[k],ptr+'/'+k)
 elif isinstance(a,list):
  if len(a)!=len(b):leaves.append({'pointer':ptr,'before':a,'after':b})
  else:
   for i,(x,y) in enumerate(zip(a,b)):diff(x,y,ptr+'/'+str(i))
 elif a!=b:leaves.append({'pointer':ptr,'before':a,'after':b})
 else:equal_leaves+=1
diff(before,after)
ck('exactly-two-requested-leaves',set(x['pointer'] for x in leaves)=={'/equations/7/expression','/equations/7/scope_note'} and len(leaves)==2)
for x in leaves:
 match=[d for d in history['scientific_delta'] if d['json_pointer']==x['pointer']]
 ck('declared-leaf-agrees:'+x['pointer'],len(match)==1 and x['before']==match[0]['before'] and x['after']==match[0]['after'])
for key in before:
 if key!='equations':ck('unchanged-root-science:'+key,before[key]==after[key])
for i,e in enumerate(before['equations']):
 if i!=7:ck('other-equation-unchanged:'+str(i),e==after['equations'][i])
eq=after['equations'][7]
ck('left-and-right-scope-explicit','Left ordinate:' in eq['expression'] and 'exponent 2;' in eq['expression'] and 'right ordinate:' in eq['expression'] and 'exponent 1/2' in eq['expression'])
ck('right-discrepancy-preserved','printed mismatch' in eq['scope_note'] and 'no fit points' in eq['scope_note'])
builderdiff=''.join(difflib.unified_diff((V/'build_extraction.py').read_text(encoding='utf-8').splitlines(True),(P/'build_extraction.py').read_text(encoding='utf-8').splitlines(True),fromfile='preserved-v1/build_extraction.py',tofile='revision2/build_extraction.py'))
(A/'revision2-builder-diff.txt').write_text(builderdiff,encoding='utf-8')
ck('no-open-mechanical-finding',all(c['passed'] for c in checks))
result={'reviewer':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'current_freeze_sha256':sha(P/'package-freeze.json'),'checks_run':len(checks),'checks_passed':sum(c['passed'] for c in checks),'checks':checks,'changed_leaves':leaves,'unchanged_leaf_comparisons':equal_leaves,'changed_prior_bound_files':changed,'manual_delta_scope':'Independently read both replacement strings and re-viewed native SI8 FigureS4b: left square quantity/square unit and right square quantity/one-half unit preserved. No author numerical repair.'}
save(A/'revision2-checks.json',result)
assert all(c['passed'] for c in checks),[c for c in checks if not c['passed']]
prior=load(A/'independent-audit-v1.json')
report={**prior,'created_at':datetime.now(timezone.utc).isoformat(),'status':'passed','source_revision':2,'source_package_freeze_sha256':sha(P/'package-freeze.json'),'source_facts_sha256':sha(P/'source-facts.json'),'open_findings':[],'findings':[{**prior['findings'][0],'status':'resolved','resolution':'Exactly two equation text leaves distinguish the source left/right axes. Numerical values, tables, quantities, sample assignments, all original/crop files and other source objects unchanged.'}],'prior_audit':{'path':str(A/'independent-audit-v1.json'),'sha256':sha(A/'independent-audit-v1.json'),'status':'one bounded wording finding, preserved'},'bounded_revision_checks':{'path':str(A/'revision2-checks.json'),'sha256':sha(A/'revision2-checks.json'),'run':len(checks),'passed':len(checks),'unchanged_leaf_comparisons':equal_leaves}}
bound=dict(new['bound_files']);bound[str(P/'package-freeze.json')]=sha(P/'package-freeze.json')
for p in sorted(V.rglob('*')):
 if p.is_file():bound[str(p)]=sha(p)
for p in sorted(A.rglob('*')):
 if p.is_file() and p.name not in ['independent-audit-v2.json','independent-audit-v2.md','independent-audit.json','independent-audit.md']:bound[str(p)]=sha(p)
report['bound_files']=bound
for name in ['independent-audit-v2.json','independent-audit.json']:save(A/name,report)
md='# Matuhina2023 independent source audit — passed revision2\n\nIndependently read and viewed all13main+13SI pages; reviewed62facts/186quantities,39operations,41sample contexts,all55bibliographic entries and all30selectedcrops. Compared all321typed table fields (301printed bodycells+20repeated groupmetadata) with a separate transcription made before opening the author extraction. All4,034 original supporting checks and '+str(len(checks))+' bounded revision checks pass;30fresh source-pixel replays are identical.\n\nThe single finding is resolved: FigureS4b now distinguishes the left unit exponent2 from the right unit exponent1/2, preserving the printed inconsistency. Exactly two text leaves changed; all numbers, tables, sample assignments and crop/source bytes remain unchanged. The source’s13conflicts remain unresolved as source evidence, including unusable refinement details and the FWHM temperature mismatch.\n\nThis approval covers source extraction only. It does not approve a coordinate model, exact structure–recipe training pair, canonical/reader transport, illustrations, browser rendering or publication.\n'
for name in ['independent-audit-v2.md','independent-audit.md']:(A/name).write_text(md,encoding='utf-8')
print(json.dumps({'status':report['status'],'audit_sha256':sha(A/'independent-audit-v2.json'),'checks':len(checks),'unchanged_leaves':equal_leaves,'bound_files':len(bound),'builder_diff':builderdiff},ensure_ascii=False))
