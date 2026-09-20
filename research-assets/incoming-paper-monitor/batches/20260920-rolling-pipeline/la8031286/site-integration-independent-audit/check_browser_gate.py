"""Independent root browser receipt/one-field audit; no Site writes."""
from pathlib import Path
import json,hashlib,copy,datetime,sys
A=Path(__file__).resolve().parent;N=A.parent;O=N/'site-integration-proposal';S=Path('[local path redacted]');sys.dont_write_bytecode=True;sys.path.insert(0,str(S/'scripts'))
import build_paper_reviews
from review_scope import source_review_scope
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
bound={};checks=[]
def bind(p):p=Path(p);bound[str(p)]=sha(p);return json.loads(p.read_text('utf8'))
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
delta=bind(O/'browser-gate-delta.json');receipt=bind(O/'browser-validation.json');before=bind(O/'reader-pre-browser-gate.json');readerpath=S/'data/paper-reviews/pati2009.json';after=bind(readerpath);transport=bind(A/'integration-transport-audit.json')
ck('Exact root receipt',sha(O/'browser-validation.json')==delta['receipt_sha256']=='d57b78032ead93f750bb04525b736a59b76456402a04a7ff8ed554f499a33232')
ck('Exact transport-bound prior reader',sha(O/'reader-pre-browser-gate.json')==delta['before_sha256']==transport['bound_files'][str(readerpath)]=='16042a7a7dd51a73fbc3d12dac0fb2fa90f5dd40840f67c284edc3e02fd80c71')
ck('Exact current reader',sha(readerpath)==delta['after_sha256']=='b25434ccdb3de28e9e8bcd4adf215ad6c72c6d07bcf2736cb401ab00b3c2b282')
ck('Exactly one declared leaf',delta['changes']==[{'pointer':'/presentation_gates/browser_render','before':False,'after':True}])
expected=copy.deepcopy(before);ck('Prior browser gate false',expected['presentation_gates']['browser_render']is False);expected['presentation_gates']['browser_render']=True
ck('Every other science and metadata field deeply equal',after==expected)
ck('Publication remains false',after['presentation_gates']['publication']is False);ck('Atomic structure approval remains false',after['presentation_gates']['exact_product_atomic_structure_binding']is False)
ck('Root actual browser status',receipt['author']=='/root'and receipt['status']=='passed'and receipt['all_stage_selectors_tested'])
for p,h in receipt['bound_files'].items():bound[p]=sha(p);ck('Current receipt dependency '+p,sha(p)==h)
records={p.stem:json.loads(p.read_text('utf8'))for p in (N/'canonical-proposal/v2').glob('pati-2009-*.json')};pairs={(rid,o['id'])for rid,r in records.items()for o in r['operations']}
ck('All35 operation instances across14records covered',len(pairs)==len(receipt['stages'])==receipt['stage_count']==35 and {(x['record_id'],x['operation_id'])for x in receipt['stages']}==pairs and len({x[0]for x in pairs})==14 and all(x['selected_correct_scene']for x in receipt['stages']))
ck('167 condition rows',receipt['condition_rows']==167)
ck('Nine actual gallery modal views distinct from20links',receipt['original_figure_modal_count']==9 and receipt['full_reader_original_asset_links']==20 and receipt['original_figures_loaded']and receipt['original_tem_saed_and_si_xps_enlargements_visually_inspected'])
ck('Lazy image loading limitation explicit','lazy-loaded'in receipt['full_reader_image_loading_note']and'nine'in receipt['full_reader_image_loading_note'])
ck('Chemical and stock scope documented','Four stock selectors'in receipt['chemical_check']and'no invented Ce-O'in receipt['chemical_check']and'Named TEA/printed formula'in receipt['chemical_check'])
ck('Four XPS histories documented','four XPS'in receipt['sample_phase_check']and'no invented55% complement'in receipt['sample_phase_check']and'unknown solvent and batch'in receipt['sample_phase_check'])
ck('Mobile no document overflow',receipt['mobile']['viewport']['width']==390 and receipt['mobile']['document_width']==receipt['mobile']['scroll_width']==375)
ck('No browser errors/warnings reported',receipt['console_errors']==receipt['console_warnings']==0)
ck('Rotation and qualification limits preserved',any('rotation was not separately exercised'in x for x in receipt['limitations'])and any('does not qualify an atomic structure'in x for x in receipt['limitations']))
public=bind(S/'dist/data/paper-reviews/pati2009.json');generated=copy.deepcopy(after);generated['review_scope_label']=source_review_scope(after)['label'];ck('Public reader regenerated with exact metadata only',public==generated)
ck('Actual current reader consumer passes',build_paper_reviews.validate(after)==[])
bound[str(S/'scripts/build_paper_reviews.py')]=sha(S/'scripts/build_paper_reviews.py');bound[str(Path(__file__))]=sha(Path(__file__))
r={'schema':'mattersyn-browser-gate-delta-audit/1','source_id':'pati2009','author':'/root','auditor':'/root/norberg2004_extract','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed','open_findings':[],'check_count':len(checks),'baseline_reader_sha256':delta['before_sha256'],'after_reader_sha256':delta['after_sha256'],'browser_receipt_sha256':delta['receipt_sha256'],'exact_allowed_changes':delta['changes'],'all_other_fields_deep_equal':True,'checks':checks,'scope':'Independent metadata and receipt consistency audit. Actual CUA observations belong to root, not a new browser session by this auditor. Nine loaded/enlarged gallery images are distinct from20 reader links. Untested drag rotation remains explicit.','bound_files':bound,'site_changed':False,'publication_approved':False,'atomic_or_training_approval':False}
(A/'browser-gate-delta-audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
(A/'browser-gate-delta-audit.md').write_text(f'# Pati browser metadata delta\n\nPassed {len(checks)} checks. Only browser_render changes from false to true; all other reader fields are identical to the transport-bound baseline. Root receipt covers35 exact stage instances across14 records,167 rows,nine loaded gallery enlargements,four stock selectors,four XPS contexts and390px mobile. Twenty source links do not mean all20 were newly opened in this browser session. Drag rotation was not separately exercised. The regenerated reader also passes the actual current consumer.\n\nThis is receipt/metadata verification, not a second browser or source-science review. Publication, training and exact atomic-structure gates remain unapproved.\n','utf8')
print(json.dumps({'status':r['status'],'checks':len(checks),'sha256':sha(A/'browser-gate-delta-audit.json')}))
