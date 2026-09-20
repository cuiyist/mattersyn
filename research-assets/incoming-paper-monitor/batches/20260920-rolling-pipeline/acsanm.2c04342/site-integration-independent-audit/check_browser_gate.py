"""Audit the root-authored one-leaf browser receipt promotion; no Site writes."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy
A=Path(__file__).resolve().parent;N=A.parent;O=N/'site-integration-proposal';S=Path('[local path redacted]')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
bound={};checks=[]
def bind(p):bound[str(p)]=sha(p);return read(p)
def ck(label,v):checks.append({'check':label,'passed':bool(v)});assert v,label
delta=bind(O/'browser-gate-delta.json');receipt=bind(O/'browser-validation.json');before=bind(O/'reader-pre-browser-gate.json');p=S/'data/paper-reviews/matuhina2023.json';after=bind(p)
ck('Exact root receipt',sha(O/'browser-validation.json')==delta['receipt_sha256']=='2552db9168b67ce7bdd5a48dedcab505645f2502ff16157d0d81f45ca796d890')
ck('Exact before hash',sha(O/'reader-pre-browser-gate.json')==delta['before_sha256']=='cff3d2c1882686e81f935edf71aba588c37c8762a2771a6b1e079c0e97005cd4')
ck('Exact after hash',sha(p)==delta['after_sha256']=='e5618aaf111c8bbbbe4a42096b1b2fa934a6b461e962a292d0b083b0dd3e6771')
ck('Single declared leaf',delta['changes']==[{'pointer':'/presentation_gates/browser_render','before':False,'after':True}])
expected=copy.deepcopy(before);ck('Browser prior false',expected['presentation_gates']['browser_render'] is False);expected['presentation_gates']['browser_render']=True
ck('ALL other scientific and metadata fields deeply equal',after==expected)
ck('Publication remains false',after['presentation_gates']['publication'] is False)
ck('Exact atomic binding remains false',after['presentation_gates']['exact_product_atomic_structure_binding'] is False)
ck('Passed actual browser receipt',receipt['status']=='passed'and receipt['author']=='/root'and receipt['all_stage_selectors_tested'])
for path,h in receipt['bound_files'].items():bound[path]=sha(path);ck('Receipt current dependency '+path,sha(path)==h)
rm=bind(N/'canonical-proposal/v1/record-manifest.json');pairs=[]
for r in rm['records']:
 record=read(r['path']);pairs.extend((record['record_id'],op['id'])for op in record['operations'])
ck('All 39 exact operation selectors covered',len(receipt['stages'])==receipt['stage_count']==len(pairs)==39 and {(s['record_id'],s['operation_id'])for s in receipt['stages']}==set(pairs) and all(s['selected_correct_scene']for s in receipt['stages']))
ck('168 condition rows',receipt['condition_rows']==168)
ck('20 figure modals loaded',receipt['original_figure_modal_count']==20 and receipt['original_figures_loaded'])
ck('22 table/equation link occurrences observed',receipt['table_and_equation_link_occurrences_observed']==22)
ck('Mobile no document overflow',receipt['mobile']['viewport']['width']==390 and receipt['mobile']['document_width']==receipt['mobile']['scroll_width']==375)
ck('No reported browser errors',receipt['console_errors']==receipt['console_warnings']==0)
ck('Rotation and source rereading limits retained',any('rotation was not separately tested' in x for x in receipt['limitations']) and any('second scientific rereading' in x for x in receipt['limitations']))
bound[str(Path(__file__))]=sha(Path(__file__))
out={'schema':'mattersyn-browser-gate-delta-audit/1','source_id':'matuhina2023','author':'/root','auditor':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'status':'passed','open_findings':[],'check_count':len(checks),'baseline_reader_sha256':delta['before_sha256'],'after_reader_sha256':delta['after_sha256'],'browser_receipt_sha256':delta['receipt_sha256'],'exact_allowed_changes':delta['changes'],'all_other_fields_deep_equal':True,'checks':checks,'scope':'Independent metadata/receipt consistency check. Actual CUA observations belong to root browser receipt, not a second browser session by this auditor.','bound_files':bound,'site_changed':False,'publication_approved':False,'atomic_or_training_approval':False}
(A/'browser-gate-delta-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(A/'browser-gate-delta-audit.md').write_text(f"# Matuhina browser gate delta\n\nPassed {len(checks)} checks. Only `/presentation_gates/browser_render` changes from false to true; every other parsed field is identical. The root receipt is hash-bound and covers all 39 operation selectors, 168 condition rows, original-figure loading and mobile checks. Its untested rotation and source-rereading limitations are retained. Publication and exact atomic-structure gates remain false.\n",encoding='utf8')
print(json.dumps({'status':'passed','checks':len(checks),'sha256':sha(A/'browser-gate-delta-audit.json')}))
