from pathlib import Path
import ast,hashlib,json,difflib
from datetime import datetime,timezone
O=Path(__file__).resolve().parent;J=O.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text('utf8'))
prior=read(O/'preexecution-review.json');current=J/'import_reviewed_sasongko.py'
expected_prior=prior['bound_files'][str(current)]
matches=[p for p in (O/'reviewed-scripts').glob('import_reviewed_sasongko*.py') if sha(p)==expected_prior]
assert len(matches)==1
baseline=matches[0];before=baseline.read_text('utf8');after=current.read_text('utf8')
insert="overlay=O/'reader-status-overlay'\nassert a['reader_status_overlay_freeze_sha256']==sha(overlay/'package-freeze.json')\nfor f in read(overlay/'package-freeze.json')['files']:assert sha(overlay/f['path'])==f['sha256']\n"
anchor="for f in read(P/'package-freeze.json')['files']:assert sha(P/f['path'])==f['sha256']\n"
assert before.count(anchor)==1
expected=before.replace(anchor,insert+anchor).replace("reader=read(P/'reader/sasongko2025.json')","reader=read(overlay/'reader/sasongko2025.json')")
checks=[]
def ck(n,b):checks.append({'check':n,'passed':bool(b)});assert b,n
ck('exactly three inserted gate lines and one reader substitution, apart from final blank line',after.rstrip()==expected.rstrip())
ast.parse(after);ck('updated importer parses',True)
ck('gate precedes all shared mutation',after.index(insert)<after.index("for f in read(P/'promotion-manifest.json')['public_assets']:"))
overlay=J/'site-integration-proposal/reader-status-overlay';fr=read(overlay/'package-freeze.json')
ck('effective reader is in audited overlay freeze',sum(f['path']=='reader/sasongko2025.json' for f in fr['files'])==1)
for f in fr['files']:ck('overlay bound bytes '+f['path'],sha(overlay/f['path'])==f['sha256'])
gate="assert a['status']=='passed' and not a.get('open_findings') and not a.get('findings') and a['proposal_freeze_sha256']==proposal\nassert a['reader_status_overlay_freeze_sha256']==overlay_hash"
good={'status':'passed','open_findings':[],'proposal_freeze_sha256':'p','reader_status_overlay_freeze_sha256':'o'}
cases=[('correct exact hashes',good,True),('stale overlay',{**good,'reader_status_overlay_freeze_sha256':'old'},False),('stale proposal',{**good,'proposal_freeze_sha256':'old'},False),('pending audit',{**good,'status':'revision_required'},False),('open finding',{**good,'open_findings':['x']},False),('missing overlay hash',{k:v for k,v in good.items() if k!='reader_status_overlay_freeze_sha256'},False)]
for name,a,accept in cases:
 try:exec(gate,{'__builtins__':{}},{'a':a,'proposal':'p','overlay_hash':'o'});ok=True
 except (AssertionError,KeyError):ok=False
 ck('gate case '+name,ok==accept)
bound={str(p):sha(p) for p in [current,baseline,O/'preexecution-review.json',overlay/'package-freeze.json']+[overlay/f['path'] for f in fr['files']]}
r={'status':'passed_bounded_importer_delta_review','scope':'Only added overlay audit/hash gate and reader source substitution. Overlay science and status edits require the distinct promotion audit. No importer execution.','check_count':len(checks),'checks':checks,'open_findings':[],'baseline_importer_sha256':expected_prior,'effective_importer_sha256':sha(current),'overlay_freeze_sha256':sha(overlay/'package-freeze.json'),'pending':'Distinct promotion audit must explicitly pass and bind this overlay before execution; code rejects pending or stale receipts.','bound_files':bound,'created_utc':datetime.now(timezone.utc).isoformat(),'site_mutated':False}
(O/'reader-overlay-importer-addendum.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
(O/'reader-overlay-importer-addendum.md').write_text('Passed the narrow importer delta review. Exactly three gate lines and one reader substitution were added. The audit must pass with no findings and bind both the original projection freeze and exact reader overlay freeze; all overlay files are hash-checked before any shared write. The reader is explicitly included in that freeze. Pending, missing or stale receipts are rejected. No other importer behavior changed. No importer execution or Site mutation.\n','utf8')
(O/'reader-overlay-importer.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='reviewed importer',tofile='overlay-gated importer')),'utf8')
print(json.dumps({'status':r['status'],'checks':len(checks),'report_sha256':sha(O/'reader-overlay-importer-addendum.json'),'importer_sha256':sha(current)},indent=2))
