"""Independent bounded browser/status and presentation transport check; no Site writes."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,copy,subprocess
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;J=O.parent;M=J.parents[4];S=M/'recipe-atlas';I=J/'site-integration-proposal';B=I/'base-site-inputs'
sys.path.insert(0,str(M/'research-assets'));from sync_github_public import io_path
checks=[];bound={}
sha=lambda p:hashlib.sha256(io_path(p).read_bytes()).hexdigest()
def bind(p):p=Path(p);h=sha(p);bound[str(p.resolve())]=h;return h
def read(p):bind(p);return json.loads(io_path(p).read_text('utf8'))
def ck(name,ok,detail=None):checks.append({'check':name,'passed':bool(ok),**({'detail':detail} if detail is not None else {})})
def save(p,x):io_path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def diff(a,b,p=''):
 if type(a)!=type(b):return [p]
 if isinstance(a,dict):return sum((diff(a[k],b[k],p+'/'+k) if k in a and k in b else [p+'/'+k] for k in sorted(set(a)|set(b))),[])
 if isinstance(a,list):
  if len(a)!=len(b):return [p+'#length']
  return sum((diff(x,y,p+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
 return [] if a==b else [p]
integration=read(O/'integration-audit.json');receipt=read(I/'browser-validation.json');delta=read(I/'browser-gate-delta.json');before=read(I/'reader-before-browser-gate.json');after=read(S/'data/paper-reviews/sasongko2025.json');public=read(S/'dist/data/paper-reviews/sasongko2025.json')
ck('Exact root actual browser receipt',sha(I/'browser-validation.json')==delta['browser_validation_sha256']=='ebc3c8e3eaf240d714bb940d314ff65849505b6d9bde0f2e584c10cfa8d44ca8')
ck('Receipt reports actual CUA passed',receipt['status']=='passed' and receipt['author']=='/root' and not receipt['open_findings'])
ck('Exact before/after reader byte identities',sha(I/'reader-before-browser-gate.json')==delta['before_sha256'] and sha(S/'data/paper-reviews/sasongko2025.json')==delta['after_sha256'])
ck('Prebrowser snapshot matches independent integration baseline',before==read(O/'integration-baseline-source-reader.json'))
paths=diff(before,after);ck('Exactly two authorized reader leaves',set(paths)=={'/presentation_gates/browser_render','/publication_status'} and len(paths)==2)
ck('Browser flag false to true',before['presentation_gates']['browser_render'] is False and after['presentation_gates']['browser_render'] is True)
ck('Publication remains explicitly false',after['presentation_gates']['publication'] is False and delta['publication'] is False and receipt['public_release_verified'] is False)
ck('Pending anonymous verification wording',after['publication_status']=='Source, canonical, illustration and actual desktop/mobile browser reviews passed; anonymous deployment verification remains pending.')
expected=copy.deepcopy(after);expected['review_scope_label']='Complete supplied main + matched SI review';ck('Public reader only established derived label',public==expected)
for rel,h in receipt['bound_presentation_files'].items():ck('Current browser-tested presentation hash '+rel,bind(S/rel)==h)
bind(J/'save_browser_validation.py')
# Reconstruct the pre-browser0.33 source from immutable preimport backups and
# verify it against this auditor's saved initial integration hashes.
changes=[]
for rel in ['dist/paper-review.mjs','scripts/build_reader_views.py']:
 bind(B/rel);pre=io_path(B/rel).read_text('utf8').replace('0.32.0-r1','0.33.0-r1').replace('0.32.0-r2','0.33.0-r2')
 # Root uses Path.write_text on Windows; bind native CRLF bytes, not LF text hash.
 prebytes=pre.replace('\n','\r\n').encode('utf8')
 ck('Reconstructed prebrowser source hash '+rel,hashlib.sha256(prebytes).hexdigest()==integration['bound_files'][str((S/rel).resolve())])
 if rel.endswith('.mjs'):
  needle='table entries inventoried. Complete source reading';replacement='original table attachments inventoried. Extracted numerical data collections are listed in the source evidence sections. Complete source reading'
 else:needle='href="paper-review.css"';replacement='href="paper-review.css?v=0.33.0-r1"'
 ck('One precise presentation text change '+rel,pre.count(needle)==1)
 current=io_path(S/rel).read_text('utf8');changed=pre.replace(needle,replacement)
 ck('Only declared presentation text delta '+rel,current==changed or (rel.endswith('.py') and current==changed+'\n'))
 changes.append({'file':rel,'before':needle,'after':replacement,'one_final_blank_line_added':current==changed+'\n'})
# Read a pinned existing public Git blob, without checkout/network/API operations.
public_repo=Path('[local path redacted]');commit='af272e24721d321cf1bdd3634733ec78c133cd3e'
cssrun=subprocess.run(['git','-c','safe.directory='+str(public_repo),'show',commit+':paper-review.css'],cwd=public_repo,capture_output=True)
if cssrun.returncode:raise RuntimeError(cssrun.stderr.decode('utf8',errors='replace'))
cssblob=cssrun.stdout
baseline=O/'pre-browser-public-paper-review.css';io_path(baseline).write_bytes(cssblob);bind(baseline)
css=io_path(S/'dist/paper-review.css').read_text('utf8');oldcss=cssblob.decode('utf8').replace('\r\n','\n')
ck('CSS only overflow-wrap rule appended',css==oldcss+'#review-body { overflow-wrap: anywhere; }\n')
basehtml=io_path(B/'dist/paper-review.html').read_text('utf8');bind(B/'dist/paper-review.html')
expectedhtml=basehtml.replace('0.32.0-r1','0.33.0-r1').replace('0.32.0-r2','0.33.0-r2').replace('href="paper-review.css"','href="paper-review.css?v=0.33.0-r1"')
ck('Regenerated review HTML only cache revisions',io_path(S/'dist/paper-review.html').read_text('utf8')==expectedhtml)
manifest=read(I/'v1/promotion-manifest.json');records={r['record_id']:read(S/'data/records'/(r['record_id']+'.json')) for r in manifest['records']}
pairs={(rid,o['id']) for rid,r in records.items() for o in r['operations']};ck('Browser receipt covers exact21operations',len(receipt['stages'])==21 and {(r['record_id'],r['operation_id']) for r in receipt['stages']}==pairs)
ck('All17 source dialogs and scoped selectors recorded',receipt['original_asset_dialogs_opened']==17 and receipt['original_assets_all_loaded_positive_natural_width'] is True and receipt['route_product_selector_contexts_tested']==13 and receipt['stock_component_selections_tested']==18)
ck('Responsive root outcome and honest rotation scope',receipt['responsive']['mobile_viewport']==[390,844] and receipt['responsive']['source_reader_scroll_width_after_fix']==375 and receipt['molecular_viewer']['rotation_drag_tested_this_release'] is False)
typed={x['id'] for s in public['reader_sections'] for x in s['items'] if x['id'].startswith('table-')}
ck('Clarified one attachment and six typed collections',len(public['tables'])==1 and typed=={'table-ligand-numeric','table-wash-numeric','table-growth-numeric','table-pl-slopes','table-reference-cells','table-table-s1'})
mutable={str((S/p).resolve()) for p in ['data/paper-reviews/sasongko2025.json','dist/data/paper-reviews/sasongko2025.json','dist/paper-review.mjs','scripts/build_reader_views.py','data/inventory-summary.json','dist/data/inventory-summary.json']}
mutable|={str((I/p).resolve()) for p in ['inventory-summary.json','build-check-output.json']}
actual_changed=[]
for p,h in integration['bound_files'].items():
 current=bind(Path(p))
 if current!=h:actual_changed.append(p)
 ck('Prior input unchanged or exact authorized presentation/metadata scope '+p,current==h or p in mutable)
inventory=read(S/'data/inventory-summary.json');pubinventory=read(S/'dist/data/inventory-summary.json');privateinventory=read(I/'inventory-summary.json')
ck('Refreshed inventory copies equal',inventory==pubinventory==privateinventory)
ck('Current inventory reader hash refreshed',inventory['provenance']['summary_artifact_sha256']['data/paper-reviews/sasongko2025.json']==sha(S/'data/paper-reviews/sasongko2025.json'))
# If only its current-reader digest is reversed, the original immutable audited
# inventory hash must be recovered using the original serialization.
oldinv=copy.deepcopy(inventory);oldinv['provenance']['summary_artifact_sha256']['data/paper-reviews/sasongko2025.json']=delta['before_sha256']
invbytes=(json.dumps(oldinv,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode('utf8')
ck('Inventory change only reader provenance hash',hashlib.sha256(invbytes).hexdigest()==integration['bound_files'][str((S/'data/inventory-summary.json').resolve())])
build=read(I/'build-check-output.json');ck('Current final build successful',len(build['runs'])==18 and all(x['exit_code']==0 for x in build['runs']))
postbuild=read(I/'post-browser-check-output.json');ck('Post-browser inventory/static supplement successful',postbuild['status']=='passed' and len(postbuild['runs'])==3 and all(x['exit_code']==0 for x in postbuild['runs']))
sys.path.insert(0,str(S/'scripts'));import build_paper_reviews
build_paper_reviews.ROOT=S;err=build_paper_reviews.validate(after);ck('Actual final reader validator',not err,err);bind(S/'scripts/build_paper_reviews.py');bind(S/'scripts/review_scope.py')
for p,h in list(bound.items()):ck('Final bound input stable '+p,sha(Path(p))==h)
bad=[c for c in checks if not c['passed']]
save(O/'browser-gate-delta-checks.json',{'checks':checks,'open_findings':bad,'reader_leaf_paths':paths,'changed_prior_inputs':actual_changed,'presentation_changes':changes})
bind(O/'browser-gate-delta-checks.json');bind(Path(__file__))
report={'schema':'mattersyn-independent-browser-display-delta-audit/1','status':'passed' if not bad else 'revision_required','author':'/root','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta','at':datetime.now(timezone.utc).isoformat(),'doi':'10.1021/acs.jpcc.5c05144','scope':'Bounded exact reader gate/display/provenance delta after root actual CUA review. Browser execution is attributed to root, not independently repeated. Prior complete scientific and integration audits remain in force.','browser_validation_sha256':sha(I/'browser-validation.json'),'initial_integration_audit_sha256':sha(O/'integration-audit.json'),'source_reader_sha256':sha(S/'data/paper-reviews/sasongko2025.json'),'public_reader_sha256':sha(S/'dist/data/paper-reviews/sasongko2025.json'),'publication':False,'counts':{'checks':len(checks),'passed':len(checks)-len(bad),'reader_leaf_changes':2,'source_dialogs_recorded':17,'stages_recorded':21,'source_typed_collections_preserved':6,'bound_files':len(bound)},'allowed_changes':['Source reader browser_render false→true and publication_status prose only. Public reader retains only established derived review_scope_label.','Original-table summary explicitly distinguishes one original table attachment from six extracted numeric collections; no content/count source changes.','One CSS overflow-wrap rule and its versioned stylesheet href in generator/regenerated review HTML.','Inventory current-input provenance refreshed only for the changed source reader hash; final build log may supersede earlier successful log.'],'build_logs':{'initial_successful_build_sha256':integration['build_check_output_sha256'],'current_successful_build_sha256':sha(I/'build-check-output.json'),'current_at':build['at'],'historical_log_treatment':'The earlier integration audit remains an immutable historical receipt. The current successful build is bound separately; timestamps/log bytes are not scientific changes.'},'public_css_baseline':{'repository':str(public_repo),'commit':commit,'path':'paper-review.css','retained_blob':str(baseline),'sha256':sha(baseline)},'findings_resolved':['Clarified original-table count vs six typed collections','Root browser responsive overflow fix, independently bounded to one CSS rule','Current source-reader provenance refreshed after browser status changed'],'open_findings':bad,'bound_files':bound,'limitations':['No new full-source reading or scientific re-audit; exact unchanged source science/asset hashes were checked.','Actual browser interactions and responsive measurements belong to root browser-validation.json; this auditor performed no browser actions.','Anonymous release remains pending; publication gate is false.'],'actions_performed':{'site_modified':False,'frozen_packages_modified':False,'browser_exercised':False,'network_accessed':False,'publication_approved':False}}
save(O/'browser-gate-delta-audit.json',report)
md=f'''# Sasongko browser and presentation delta audit\n\nStatus: **{report['status']}**. Auditor: `/root/backlog_eta`; actual browser reviewer and change author: `/root`.\n\nExactly two source-reader leaves changed: browser_render became true and publication_status now records completed browser review with anonymous deployment pending. The public reader differs only by its established derived review-scope label. All scientific content,19 record bytes,81 approved assets,sample maps,prior656 records and six exports remain unchanged.\n\nThe presentation change is limited to clearer original-table wording, one overflow-wrap CSS rule and a versioned stylesheet URL. All six typed data collections remain present alongside one original table attachment. The current inventory differs only in the source-reader provenance hash. Root's receipt records21 scenes,17 loaded source dialogs,13 route contexts,18 stock selections and responsive checks; rotation dragging is explicitly not claimed.\n\n{len(checks)-len(bad)}/{len(checks)} checks passed; {len(bound)} inputs bound. This audit does not repeat root's browser actions. Publication remains false and anonymous release verification is separate.\n'''
io_path(O/'browser-gate-delta-audit.md').write_text(md,'utf8')
print(json.dumps({'status':report['status'],'checks':len(checks),'bound':len(bound),'failures':bad[:15],'sha256':sha(O/'browser-gate-delta-audit.json')},ensure_ascii=False))
