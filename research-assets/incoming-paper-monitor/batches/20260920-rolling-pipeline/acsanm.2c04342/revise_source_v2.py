"""Preserve revision 1; clarify only the two printed Tauc ordinate unit exponents."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import json,hashlib,shutil
P=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
fr=read(P/'package-freeze.json');assert fr['revision']==1
for p,h in fr['bound_files'].items():assert sha(p)==h,p
oldhash=sha(P/'package-freeze.json');A=P/'source-revision-1';A.mkdir(exist_ok=False)
for p in [P/'package-freeze.json']+[Path(p)for p in fr['bound_files']if Path(p).parent==P]:shutil.copy2(p,A/p.name)
d=read(P/'source-facts.json');before=deepcopy(d);q=next(x for x in d['equations']if x['id']=='tauc-axes')
q['expression']='Left ordinate: (alpha*h*nu)^2, with printed unit exponent 2; right ordinate: (alpha*h*nu)^2, with printed unit exponent 1/2'
q['scope_note']='Retain the left/right axis typography separately. The right ordinate retains its printed mismatch between the squared quantity and one-half unit exponent; no fit points, gap values or corrected formula are inferred.'
delta=[{'json_pointer':'/equations/7/'+k,'before':before['equations'][7][k],'after':q[k]}for k in['expression','scope_note']]
chk=deepcopy(d)
for k in['expression','scope_note']:chk['equations'][7][k]=before['equations'][7][k]
assert chk==before
write(P/'source-facts.json',d)
bp=P/'build_extraction.py';s=bp.read_text(encoding='utf-8')
s=s.replace("'(alpha*h*nu)^2; units printed with exponent1/2'",repr(q['expression']))
s=s.replace("'Retain original axis typography;no newly derived fit points or gaps.'",repr(q['scope_note']))
bp.write_text(s,encoding='utf-8')
report={'schema':'mattersyn-source-bounded-revision/1','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'revision':2,'prior_freeze_sha256':oldhash,'preserved_prior_directory':str(A),'finding':'M1: distinguish Figure S4b left versus right printed unit exponents','scientific_delta':delta,'source_facts_exactly_two_text_leaves_changed':True,'unchanged_source_table_sha256':sha(P/'source-tables.json'),'unchanged_selected_asset_manifest_sha256':sha(P/'original-assets-manifest.json'),'all_other_prior_frozen_files_unchanged':{p:h for p,h in fr['bound_files'].items()if Path(p)not in[P/'source-facts.json',bp]},'independent_recheck':'pending'}
for p,h in report['all_other_prior_frozen_files_unchanged'].items():assert sha(p)==h,p
write(P/'source-revision-2-delta.json',report)
new=deepcopy(fr);new.update(revision=2,created_at=datetime.now(timezone.utc).isoformat(),scope='Complete supplied 13-page main plus 13-page SI extraction; bounded Tauc left/right wording correction, independent recheck pending.',prior_freeze_sha256=oldhash,revision_delta_sha256=sha(P/'source-revision-2-delta.json'))
new['bound_files'].update({str(p):sha(p)for p in[P/'source-facts.json',bp,P/'source-revision-2-delta.json',Path(__file__)]})
write(P/'package-freeze.json',new)
print(json.dumps({'freeze':sha(P/'package-freeze.json'),'facts':sha(P/'source-facts.json'),'delta':sha(P/'source-revision-2-delta.json'),'bound_files':len(new['bound_files'])}))
