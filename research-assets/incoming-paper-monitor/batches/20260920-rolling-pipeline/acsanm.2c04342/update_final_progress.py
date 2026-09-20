"""Save current reviewed milestones without reopening completed contributions."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys
A=Path(__file__).resolve().parent;MON=A.parents[2];M=A.parents[4];P=A.parent/'la8031286'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
now=datetime.now(timezone.utc).isoformat()
assert read(MON/'latest-publication.json')['dataset_version']=='0.30.0'
assert read(P/'canonical-reader-independent-audit/independent-audit-v2.json')['status']=='passed'
assert read(P/'product-context-independent-audit/independent-audit.json')['status']=='passed'
ed=read(MON/'public-progress-editorial.json')
apparatus=P/'visuals/apparatus-independent-audit/independent-audit.json';molecule=P/'visuals/molecules-independent-audit/independent-audit.json'
def passed(p):return p.exists() and read(p).get('status')=='passed'
appok,molok=passed(apparatus),passed(molecule)
visual='Apparatus and chemical-identity audits are still in progress.'
if appok:visual='Apparatus audit passed; chemical-identity audit remains in progress.'
if appok and molok:visual='Apparatus and chemical-identity audits passed; Site integration and browser/publication checks remain.'
ed['current_work']=[{'short_label':'Pati et al. (2009)','title':'Precipitation of Nanocrystalline CeO2 Using Triethanolamine','stage':'Source, structured data and product-context audits passed; remaining visual and publication checks continue','summary':'All four main and four matched SI pages are read and independently audited. The proposal retains three separate alcohol routes, 19 records, 35 illustrated operations, six stocks, 20 original crops and the complete XPS fitting table. Local microscopy, bulk diffraction, calcination, dispersion size and X-ray exposure histories remain distinct.','stages':[{'label':'Main/SI pairing, complete source reading and extraction','status':'complete','detail':'Independent source review passed. SI pairing is supported by the main-paper declaration, matching content and embedded document metadata.'},{'label':'Structured records and full reader','status':'complete','detail':'19 records and 243 reader items independently audited. One reader metadata token was corrected in a preserved revision; all scientific record bytes remain unchanged.'},{'label':'Illustrations and exact specimen assignments','status':'in_progress','detail':'39 symbolic product-context mappings and 117 explicit exclusions passed root review. '+visual},{'label':'Website integration and publication','status':'pending','detail':'The proposal remains outside the live dataset until all gates pass; no publication or training admission is inferred from screening.'}],'gaps':['As-prepared whole composition remains unresolved despite local CeO2 fringes and SAED.','Source formula, DLS radius/diameter and XPS-label conflicts remain explicit.','No source atomic coordinate model or exact structure–recipe pair is supplied.']}]
ed['estimate']['current_batch']='Matuhina CsMnCl₃ is published. Pati CeO₂ source, structured-data/reader and symbolic product-context audits passed. '+visual+' Whole-corpus capacity and finish date remain unvalidated.'
D=MON/'deadline-20260920';active=read(D/'active-cutoff.json');partpath=D/'matuhina-published-scope-20260920.json'
if not partpath.exists():subprocess.run([sys.executable,str(D/'partition_deadline_scope.py'),'--cutoff-manifest',active['cutoff_manifest']['path'],'--ledger',str(MON/'ledger.json'),'--output',str(partpath)],check=True)
part=read(partpath);n=part['counts']['included_pending_scopes']
ed['workflow'].update(fixed_pending_provisional_scopes=n,scope_counts_updated_at=now,later_arrival_groups_current=part['counts']['later_arrival_group_candidates'],later_arrival_file_candidates_current=part['counts']['later_arrival_file_candidates'])
ed['estimate']['summary']=f'The two-month target covers the fixed existing collection. {n:,} provisional cutoff scopes remain pending, plus three nested identity cases. Roughly {n/60:.0f} closures per day over 60 days, or {n/50:.0f} per day over 50 production days, would be required. Achievable capacity and the recipe-bearing fraction remain unverified.'
save(MON/'public-progress-editorial.json',ed)
sys.path.insert(0,str(MON));import monitor
monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='10.1021_la8031286',note='Pati source, canonical/reader v2 and symbolic product-context audits passed; remaining visual and integration/publication gates stay separate.',data={'current_step':'Independent visual audits; preparing reviewed Site integration','canonical_audit':{'path':str(P/'canonical-reader-independent-audit/independent-audit-v2.json'),'sha256':sha(P/'canonical-reader-independent-audit/independent-audit-v2.json')},'product_context_audit':{'path':str(P/'product-context-independent-audit/independent-audit.json'),'sha256':sha(P/'product-context-independent-audit/independent-audit.json')}})
p=M/'MEMORY.md';p.write_text(f'''## 2026-09-20 — Screen-first workflow and parallel review handoff

Saved {now}. Matuhina CsMnCl3 dataset0.30.0 is anonymously verified at science commit bfdb06744a991fb26ea64781691ba5035c2ea5ee:607records115routes48material/component hubs38sourcegroups33formalreaders. All219 endpoints and both38-citation READMEs passed. Claim is closed within complete supplied13main+13SI scope. Exact atomic pairs remain0; prior586records and task-specific training exports are unchanged. Publication labels and this progress snapshot are being delivered as a metadata-only update.

Pati2009 CeO2 complete4main+4SI source audit passed. Canonical v2 freeze20626581e2d01f7a25904dd133d9b8edc63759850cb7562bb81703f527ee1832 passed independent audit e59bfbcec0f265178bb502b814993c40649bf57ac006ced6394648146dcad55a. All19record bytes preserved; only reader review_scope token changed. Root product-context audit59c8ac1ff603a61c0550b95e704f72764b45b2b61327beff99c2ac12b8bf0036 passed1932checks for39mappings/117exclusions/11symbols. {visual} Existing frozen apparatus35scenes and molecule20identities/45slots/6stocks remain under distinct checks. No Pati Site integration, publication or training promotion yet. Root has actually read all8original pages and saved source distinctions in la8031286/root-preview-reading.md.

Fixed-cutoff screening accounts for13,831top-level copies; three nested identity cases remain held. Current partition has{n}pending provisional scopes; later arrivals stay separate. Screening is not full reading or an evidenced no-recipe exclusion. No new source downloads or paid API run. Existing five-minute heartbeat remains the single continuation mechanism; four simultaneous agent slots including root, up tofivepaperclaims. Finished papers may be batched for publication without bypassing their individual gates. Two-month capacity is unvalidated, not promised.

Resume Pati's final visual audits and then reviewed-data Site integration, browser checks and a verified science release. Keep author freezes/v1audit intact; v2metadata receipt proves unchanged scientific bytes. Public GitHub projections include code/memory/skills/history/references while sourcePDFs/SI/fulltext/fullpages remain local.

'''+p.read_text('utf8'),'utf8')
print(json.dumps({'status':'saved','pending_cutoff_scopes':n,'partition_counts':part['counts'],'apparatus_passed':appok,'molecules_passed':molok}))
