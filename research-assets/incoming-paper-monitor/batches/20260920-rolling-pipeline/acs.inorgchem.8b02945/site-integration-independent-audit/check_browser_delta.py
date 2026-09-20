"""Read-only final display/gate recheck; does not claim auditor browser interaction."""
import copy,datetime,hashlib,html,json,sys
from pathlib import Path
M=Path('[local path redacted]');S=M/'recipe-atlas';O=Path(__file__).parent;F=O.parent;P=F/'site-integration-proposal'
sys.path.insert(0,str(M/'research-assets'));from sync_github_public import io_path
checks=[];bound={}
def sha(p):return hashlib.sha256(io_path(Path(p)).read_bytes()).hexdigest()
def bind(p):p=Path(p);bound[str(p)]=sha(p);return bound[str(p)]
def read(p):bind(p);return json.loads(io_path(Path(p)).read_text(encoding='utf-8-sig'))
def ck(n,v,detail=None):checks.append({'check':n,'pass':bool(v),**({'detail':detail} if detail is not None else {})})
def leaves(v,p=''):
 if isinstance(v,dict):return {kk:vv for k,x in v.items() for kk,vv in leaves(x,p+'/'+k).items()}
 if isinstance(v,list):return {kk:vv for i,x in enumerate(v) for kk,vv in leaves(x,p+'/'+str(i)).items()}
 return {p:v}
def save(p,x):io_path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

previous=read(O/'integration-audit.json');before=read(O/'integration-baseline-reader.json');after=read(S/'data/paper-reviews/friedfeld2019.json')
receipt=read(P/'browser-validation.json');delta=read(P/'browser-gate-delta.json');pre=read(P/'reader-pre-browser-gate.json');bind(F/'record_browser_checks.py')
ck('prior independent audit unchanged',sha(O/'integration-audit.json')=='f470a005fa0637cbf68acdb2bb8e26f7e3bb5ba6f1f8fe2d9ea5a1b54e84dba9')
ck('root pre-browser snapshot equals independent preserved snapshot',pre==before and bind(P/'reader-pre-browser-gate.json')==sha(O/'integration-baseline-reader.json')==delta['before_sha256'])
ck('root delta binds exact current reader and browser receipt',delta['after_sha256']==sha(S/'data/paper-reviews/friedfeld2019.json') and delta['receipt_sha256']==sha(P/'browser-validation.json'))
old='Completeoriginalpageincludingcaptions,notes,plotsandtables; finalsmallfitboxesreadfromnativecrops.'
new='Complete original page reviewed, including captions, notes, plots and tables; small fit labels checked in native crops.'
b=leaves(before);a=leaves(after);changed=[{'path':p,'old':b.get(p),'new':a.get(p)} for p in sorted(b.keys()|a.keys()) if b.get(p)!=a.get(p)]
notes=[x for x in changed if x['old']==old and x['new']==new]
ck('exactly33 spaced page-note leaves plus browser flag',len(changed)==34 and len(notes)==33)
for x in changed:ck('permitted reader leaf '+x['path'],x in notes or (x['path']=='/presentation_gates/browser_render' and x['old'] is False and x['new'] is True))
ck('publication and exact model gates remain false',after['presentation_gates']['publication'] is False and after['presentation_gates']['exact_product_atomic_structure_binding'] is False)
pub=read(S/'dist/data/paper-reviews/friedfeld2019.json');pe=copy.deepcopy(after);pe['review_scope_label']='Complete supplied main + matched SI review'
ck('public reader equals current reader plus scope label',pub==pe)
ck('all417 reader items retained',sum(len(s['items']) for s in after['reader_sections'])==417)

# Reproduce the initial script from its retained baseline, verifying that initial
# text bytes exactly match the independent report before allowing the new clause.
cd=read(P/'code-delta.json');base=P/'base-site-inputs/scripts/build_dataset.py';bind(base)
initial=io_path(base).read_text(encoding='utf-8')
for row in cd['changes']:
 if row['file']=='scripts/build_dataset.py':initial=initial.replace(row['before'],row['after'])
initial=initial.replace('0.31.0-r1','0.32.0-r1').replace('0.31.0-r2','0.32.0-r2')
ck('reconstructed prior dataset builder matches audit hash',hashlib.sha256(initial.replace('\n','\r\n').encode()).hexdigest()==previous['bound_files'][str(S/'scripts/build_dataset.py')])
oldcode="esc(l['relation'])";newcode="esc(l['relation'].replace('_',' ') if r['lineage']['source_group']=='friedfeld2019' else l['relation'])"
actual=io_path(S/'scripts/build_dataset.py').read_text(encoding='utf-8');bind(S/'scripts/build_dataset.py')
ck('one source-scoped relation-display expression only',initial.count(oldcode)==1 and initial.replace(oldcode,newcode)==actual)
ck('browser receipt current scoped builder hash',receipt['bound_files']['scripts/build_dataset.py']==sha(S/'scripts/build_dataset.py'))

changed_inputs=[];old_reader_hash=sha(O/'integration-baseline-reader.json');new_reader_hash=sha(S/'data/paper-reviews/friedfeld2019.json')
permitted={str(S/'scripts/build_dataset.py'),str(S/'data/paper-reviews/friedfeld2019.json'),str(S/'dist/data/paper-reviews/friedfeld2019.json'),str(S/'data/inventory-summary.json'),str(S/'dist/data/inventory-summary.json')}
for rid in ['friedfeld-2019-conversion-representative','friedfeld-2019-conversion-acid-additive','friedfeld-2019-conversion-indium-additive','friedfeld-2019-conversion-concentration']:permitted.add(str(S/'dist/records'/(rid+'.html')))
for path,h in previous['bound_files'].items():
 current=bind(path)
 if current!=h:changed_inputs.append(path)
 ck('initial input preserved or explicitly allowed '+path,current==h or path in permitted)
ck('exactly nine initial inputs affected',set(changed_inputs)==permitted)
for rel in ['data/inventory-summary.json','dist/data/inventory-summary.json']:
 p=S/rel;raw=io_path(p).read_bytes();restored=raw.replace(new_reader_hash.encode(),old_reader_hash.encode())
 ck('inventory only current reader provenance digest '+rel,raw.count(new_reader_hash.encode())==1 and hashlib.sha256(restored).hexdigest()==previous['bound_files'][str(p)])
for path in changed_inputs:
 p=Path(path)
 if p.suffix!='.html':continue
 r=read(S/'data/records'/(p.stem+'.json'));raw=io_path(p).read_bytes()
 for relation in {x['relation'] for x in r['context_links']}:
  if '_' in relation:
   oldspan=('<span>'+html.escape(relation)+'</span>').encode();newspan=('<span>'+html.escape(relation.replace('_',' '))+'</span>').encode();raw=raw.replace(newspan,oldspan)
 ck('generated route HTML differs only by relation spacing '+p.name,hashlib.sha256(raw).hexdigest()==previous['bound_files'][str(p)])

bindings=read(F/'visuals/apparatus/canonical-bindings.json')['bindings'];expected={(x['record_id'],x['operation_id']) for x in bindings};actualstages={(x['record_id'],x['operation_id']) for x in receipt['stages']}
ck('root actual browser receipt accounts for58exact stages19records',receipt['status']=='passed' and receipt['author']=='/root' and len(expected)==58 and actualstages==expected and len({x[0] for x in actualstages})==19 and all(x['scene_label_present_after_selection'] for x in receipt['stages']))
ck('root browser receipt reports desktop/mobile no body overflow',receipt['desktop']['client_width']==receipt['desktop']['scroll_width'] and receipt['mobile']['client_width']==receipt['mobile']['scroll_width'] and receipt['console_errors']==0)
for rel,h in receipt['bound_files'].items():
 if rel=='site-integration-proposal/build-check-output.json':continue
 path=F/rel if rel.startswith('site-integration-') else S/rel
 ck('browser receipt current immutable/code binding '+rel,bind(path)==h)
build=read(P/'build-check-output.json');ck('final root build/check rerun all successful',bool(build['runs']) and all(x['exit_code']==0 for x in build['runs']))
ck('final build later than browser receipt',build['at']>receipt['at'])
quality=[x for x in build['runs'] if any(str(y).endswith('check_quality.py') for y in x['args'])]
ck('final quality log38035checks',len(quality)==1 and json.loads(quality[0]['stdout'])['passed'] and json.loads(quality[0]['stdout'])['counts']['checks']==38035)
bind(Path(__file__))
ck('final bound file rehash stable',all(sha(p)==h for p,h in bound.items()))
assert checks[-1]['pass'],'Files changed before audit freeze'
status='passed' if all(x['pass'] for x in checks) else 'findings_required'
report={'audit_id':'friedfeld2019-final-browser-display-delta-independent-audit','status':status,'author':'/root','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'scope':'Independent exact metadata/display transport recheck; browser interactions were performed by root, not repeated by this auditor.',
 'proposal_freeze_sha256':previous['proposal_freeze_sha256'],'prior_integration_audit_sha256':sha(O/'integration-audit.json'),'browser_receipt_sha256':sha(P/'browser-validation.json'),
 'findings':[x for x in checks if not x['pass']],'open_findings':[x for x in checks if not x['pass']],
 'summary':{'executed':len(checks),'passed':sum(x['pass'] for x in checks),'source_reader_changed_leaves':len(changed),'readable_page_notes':len(notes),'affected_initial_bound_inputs':len(changed_inputs),'canonical_record_changes':0,'measurement_value_changes':0,'public_asset_changes':0,'publication_flag':after['presentation_gates']['publication']},
 'reader_delta':changed,'changed_initial_bound_inputs':changed_inputs,
 'code_delta':{'path':str(S/'scripts/build_dataset.py'),'before':oldcode,'after':newcode,'occurrences':1},
 'build_provenance':{'historical_browser_receipt_build_sha256':receipt['bound_files']['site-integration-proposal/build-check-output.json'],'current_final_build_path':str(P/'build-check-output.json'),'current_final_build_sha256':sha(P/'build-check-output.json'),'current_run_count':len(build['runs']),'note':'The established root helper overwrote its timestamped build log during the final successful rerun. The browser receipt retains the earlier successful-log digest as historical provenance; it is not asserted to match the current log. This audit separately binds and checks the final rerun.'},
 'conclusion':'Only 33 page-note spacing updates and the supported browser flag changed in the reader. The only builder change is Friedfeld-only underscore-to-space formatting. Four generated route HTML files reverse exactly to their old hashes after restoring relation text; inventory reverses exactly after restoring only the reader provenance digest. All other initial audit inputs, including 656 canonical records, public assets, maps and six task exports, remain unchanged.',
 'manual_scope':['Read root browser receipt and its recording script, exact reader leaf delta and source-scoped builder expression.','Assessed hash-preserving reversal of generated display and inventory changes; did not perform or claim independent browser interactions.'],
 'remaining_gates':['Actual publication and anonymous delivery verification by root; publication remains false.'],
 'checks':checks,'bound_files':dict(sorted(bound.items()))}
save(O/'browser-gate-delta-audit.json',report)
io_path(O/'browser-gate-delta-audit.md').write_text(f'''# Friedfeld final display and browser-gate delta

**{status.upper()}** — root authored the changes and performed browser QA; `/root/backlog_eta` independently checked the exact file delta.

The reader changes exactly 33 page-review notes for spacing and `browser_render` from false to true. Publication remains false. The sole builder edit formats underscores as spaces only in Friedfeld context-relation labels. Four route HTML files and two inventory provenance copies reverse exactly to their previous hashes after restoring those display strings or the reader digest.

All 656 canonical records, scientific measurements, approved assets, binding/display maps and six training exports retain the initial integration audit hashes. The receipt covers the same 58 stages across 19 records and reports successful desktop/mobile controls. This audit does not claim its own browser interaction.

All {report['summary']['executed']:,} bounded checks passed. The final build log is separately bound; its successful rerun supersedes the earlier timestamped log hash recorded historically by the browser receipt. Live publication remains a separate root gate.
''',encoding='utf-8')
print(json.dumps({'status':status,'summary':report['summary'],'audit_sha256':sha(O/'browser-gate-delta-audit.json'),'findings':report['findings']},ensure_ascii=False,indent=2))
