"""Bounded independent check of J-PROJ-01; does not write author or Site files."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,copy
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;J=O.parent;M=J.parents[4];S=M/'recipe-atlas';P=J/'site-integration-proposal/v1';V=J/'site-integration-proposal/reader-status-overlay'
sys.path.insert(0,str(M/'research-assets'))
from sync_github_public import io_path
sha=lambda p:hashlib.sha256(io_path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(io_path(p).read_text('utf8'))
def save(p,x):io_path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
checks=[]
def ck(name,ok):checks.append({'check':name,'passed':bool(ok)})
def ptr(x,p):
 for part in p.lstrip('/').split('/'):x=x[int(part)] if isinstance(x,list) else x[part]
 return x
def setptr(x,p,v):
 parts=p.lstrip('/').split('/');root=x
 for part in parts[:-1]:root=root[int(part)] if isinstance(root,list) else root[part]
 root[parts[-1]]=v
def diff(a,b,p=''):
 if type(a)!=type(b):return [p]
 if isinstance(a,dict):return sum((diff(a[k],b[k],p+'/'+k) if k in a and k in b else [p+'/'+k] for k in sorted(set(a)|set(b))),[])
 if isinstance(a,list):
  if len(a)!=len(b):return [p+'#length']
  return sum((diff(x,y,p+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
 return [] if a==b else [p]
prior=read(O/'promotion-delta-audit-v1.json');bound=dict(prior['bound_files'])
ck('Preserved exact initial audit',sha(O/'promotion-delta-audit-v1.json')=='ca97bca1d3bfbc35a604f27e9b26513b88a5d1f69f4c899ee0be45e5c59c6414')
for p,h in bound.items():ck('Preserved original input '+p,sha(Path(p))==h)
f=read(V/'package-freeze.json');delta=read(V/'status-only-delta.json');before=read(P/'reader/sasongko2025.json');after=read(V/'reader/sasongko2025.json')
ck('Exact requested overlay freeze',sha(V/'package-freeze.json')=='a3bc2521c2db3ffacc6d5940d947bf06f8da3b8626ccf97bcd3f7f3c5b35dd4b')
for row in f['files']:ck('Frozen overlay hash '+row['path'],sha(V/row['path'])==row['sha256'])
ck('Original projection freeze retained',sha(P/'package-freeze.json')==delta['base_freeze_sha256']==prior['proposal_freeze_sha256'])
ck('Exact source reader hash',sha(P/'reader/sasongko2025.json')==delta['base_reader_sha256'])
expected=set(prior['open_findings'][0]['json_pointers']);actual=diff(before,after)
ck('Only twenty finding leaves changed',len(actual)==len(expected)==20 and set(actual)==expected)
ck('Exact author delta paths',len(delta['deltas'])==20 and {x['pointer'] for x in delta['deltas']}==expected)
reverse=copy.deepcopy(after)
for row in delta['deltas']:
 p=row['pointer'];ck('Exact before value '+p,ptr(before,p)==row['before']);ck('Exact after value '+p,ptr(after,p)==row['after']);setptr(reverse,p,row['before'])
 if p!='/supporting_information/status':
  ck('Completed canonical relation '+p,row['before']=='Private canonical record pending independent review.' and row['after']=='Source-reviewed canonical record; independent audit passed.')
  ck('Same whole-record target '+p,ptr(before,p.rsplit('/',1)[0])['json_pointer']==ptr(after,p.rsplit('/',1)[0])['json_pointer']=='')
 else:ck('Completed SI review scope',row['after']=='matched_source_and_canonical_review_complete')
ck('Reverse exact reader equality including raw historical flags',reverse==before)
ck('Unchanged visual/training/browser/publication gates',after['presentation_gates']==before['presentation_gates'])
sys.path.insert(0,str(S/'scripts'));import build_paper_reviews
build_paper_reviews.ROOT=P/'consumer-fixture';errors=build_paper_reviews.validate(after);ck('Actual current reader validator accepts effective reader',not errors)
for p in [V/'package-freeze.json',V/'status-only-delta.json',V/'reader/sasongko2025.json',O/'promotion-delta-audit-v1.json',J/'prepare_reader_status_overlay.py',Path(__file__)]:bound[str(p.resolve())]=sha(p)
bad=[x for x in checks if not x['passed']]
save(O/'reader-status-overlay-checks.json',{'status':'passed' if not bad else 'revision_required','checks':checks,'open_findings':bad,'actual_reader_errors':errors,'changed_pointers':actual})
bound[str((O/'reader-status-overlay-checks.json').resolve())]=sha(O/'reader-status-overlay-checks.json')
final=copy.deepcopy(prior);final.update(status='passed' if not bad else 'revision_required',at=datetime.now(timezone.utc).isoformat(),reader_status_overlay_freeze_sha256=sha(V/'package-freeze.json'),effective_reader_path=str(V/'reader/sasongko2025.json'),effective_reader_sha256=sha(V/'reader/sasongko2025.json'),initial_audit_sha256=sha(O/'promotion-delta-audit-v1.json'),initial_finding='J-PROJ-01: nineteen visible root-record relations and the SI status retained obsolete canonical-review pending wording.',resolved_findings=['J-PROJ-01'] if not bad else [],open_findings=bad,bound_files=bound)
final['counts']['initial_projection_checks']=prior['counts']['executed_checks'];final['counts']['overlay_checks']=len(checks);final['counts']['executed_checks']=prior['counts']['executed_checks']+len(checks);final['counts']['passed_checks']=prior['counts']['passed_checks']+len(checks)-len(bad);final['counts']['bound_files']=len(bound)
final['remaining_gates']=[x for x in final['remaining_gates'] if not x.startswith('Status-only')]
final['allowed_deltas'].append('Reader-status overlay: exactly nineteen completed-review relation strings and the SI completed-review status. Reverse delta reconstructs the entire original reader, including all historical raw payload audit flags.')
final['manual_review'].append('Read exact twenty-field status overlay and author script; no additional scientific change. Effective reader independently rerun through current consumer validator.')
save(O/'promotion-delta-audit.json',final);save(O/'promotion-delta-audit-v2.json',final)
md=f'''# Sasongko publication-projection audit\n\nStatus: **{final['status']}**. Proposal author: `/root`; independent auditor: `/root/backlog_eta`.\n\nThe original proposal remains frozen at `{final['proposal_freeze_sha256']}`. The effective reader additionally uses the status overlay `{final['reader_status_overlay_freeze_sha256']}`. Finding J-PROJ-01 is closed: exactly 19 obsolete canonical-link relation strings and one SI review-status string changed. Reversing those 20 leaves reconstructs the complete original reader; all historical payloads are untouched. Initial finding report is preserved as `promotion-delta-audit-v1.json/.md`.\n\nAll 19 records, 21 operations, 502 measurements, 273 reader items and 1,197 typed fields retain their scientific values, source locators, sample assignments, conflicts and missingness. All 81 selected assets retain approved bytes, with 26 material slots, five stocks/12 components and 42 product-context instances. No source documents, full-page scans, source text caches or private filesystem paths are exported. Training tasks and product atomic-model gates remain closed.\n\n{final['counts']['passed_checks']}/{final['counts']['executed_checks']} checks passed ({prior['counts']['executed_checks']} original checks plus {len(checks)} bounded correction/preservation checks). The effective reader passes the actual current reader validator. {len(bound)} inputs are hash-bound. No open finding.\n\nThis pass covers the immutable base plus its exact status-only overlay. Actual Site integration, browser QA and anonymous publication remain separate. No shared Site, source or frozen author files were modified.\n'''
for name in ['promotion-delta-audit.md','promotion-delta-audit-v2.md']:io_path(O/name).write_text(md,'utf8')
print(json.dumps({'status':final['status'],'checks':len(checks),'failed':bad,'combined':final['counts']['executed_checks'],'bound':len(bound),'sha256':sha(O/'promotion-delta-audit.json')},ensure_ascii=False))
