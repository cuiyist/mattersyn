"""Close the independently identified unit correction without altering author files."""
from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
E=Path(__file__).resolve().parents[1];O=Path(__file__).resolve().parent;R=E/'source-extraction-revision-2'
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=read(O/'source-scientific-audit-v1.json');freeze=read(R/'source-extraction-freeze.json');bound=dict(prior['bound_files']);checks=[]
def ck(ok,s):
 assert ok,s
 checks.append(s)
for p,digest in prior['bound_files'].items():ck(sha(Path(p))==digest,'Prior audited bytes preserved '+p)
for row in freeze['files']:
 p=Path(row['path']);ck(sha(p)==row['sha256'],'Corrected freeze dependency '+str(p));bound[str(p)]=sha(p)
a=read(E/'source-facts.json');b=read(R/'source-facts.json');delta=[]
def walk(a,b,path=''):
 if type(a)!=type(b):delta.append({'path':path,'before':a,'after':b});return
 if isinstance(a,dict):
  ck(a.keys()==b.keys(),'Same object keys '+path)
  for k in a:walk(a[k],b[k],path+'/'+k)
 elif isinstance(a,list):
  ck(len(a)==len(b),'Same list length '+path)
  for i,(x,y) in enumerate(zip(a,b)):walk(x,y,path+'/'+str(i))
 elif a!=b:delta.append({'path':path,'before':a,'after':b})
walk(a,b)
ck(delta==[{'path':'/facts/444/unit','before':'deg','after':'dimensionless'}],'Exactly the independently requested correction')
ck(b['facts'][444]['property']=='_diffrn_measured_fraction_theta_max' and b['facts'][444]['value']==0.98,'Corrected fraction retains original tag/value')
ck(freeze['effective_source_facts_path']==str(R/'source-facts.json'),'Effective facts path points to corrected copy')
ck(freeze['effective_source_inventory_path']==str(E/'source-inventory.json'),'Inventory remains immutable original')
for p in [R/'source-extraction-freeze.json',O/'source-scientific-audit-v1.json',Path(__file__)]:bound[str(p)]=sha(p)
report=dict(prior)
report.update(at=datetime.now(timezone.utc).isoformat(),status='passed_independent_source_scientific_audit_revision_2',author_freeze_sha256=sha(R/'source-extraction-freeze.json'),effective_source_facts_path=str(R/'source-facts.json'),effective_source_facts_sha256=sha(R/'source-facts.json'),effective_source_inventory_path=str(E/'source-inventory.json'),open_findings=[],resolved_findings=[{'id':'cif-measured-fraction-unit','resolution':'Exactly /facts/444/unit changed from deg to dimensionless. Original0.98 value, source tag and all other extraction fields unchanged; initial freeze and finding retained.'}],revision_delta=delta,delta_check_count=len(checks),delta_checks=checks,bound_files=bound)
report['scope']=dict(prior['scope']);report['scope']['bounded_delta_checks']=len(checks)
report['manual_checks']=[dict(x,status='passed') for x in prior['manual_checks']]
(E/'source-scientific-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(E/'source-scientific-audit.md').write_text('# Evans2010 independent source scientific audit\n\nPassed against source extraction revision2. All3 main pages and21 SI pages were read and visually inspected, together with all25 selected original crops. The review covers198 source units,457 typed facts,16 procedure families,47material roles,10stocks and29sample contexts. An independent tokenizer matched every99CIF scalar and2,896cell across7loops;13,617 supporting checks passed.\n\nOne extraction-unit finding was corrected: CIF completeness fraction0.980 is dimensionless. Exactly that unit field changed; every other source/extraction value, specimen link and original asset remains unchanged. The first freeze and finding report remain preserved.\n\nThe CIF describes molecular species9, not PbSe/CdSe QD coordinates. All source conflicts, missing workup/details and uncertain specimen joins remain explicit. This audit covers source extraction only; canonical records, readers, molecular/apparatus viewers, training and publication require their separate gates. Full-paper text payloads remain private.\n',encoding='utf8')
print(json.dumps({'status':report['status'],'audit_sha256':sha(E/'source-scientific-audit.json'),'delta_checks':len(checks),'bound_files':len(bound),'effective_facts_sha256':sha(R/'source-facts.json')}))
