"""Root-only queue, memory and public progress checkpoint after source audit."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,subprocess
F=Path(__file__).resolve().parent;MON=F.parents[2];M=F.parents[4];D=MON/'deadline-20260920'
sys.path.insert(0,str(MON));import monitor
read=lambda p:json.loads(p.read_text('utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n','utf8')
now=datetime.now(timezone.utc).isoformat();proof=F/'source-independent-audit/independent-audit.json';audit=read(proof)
assert audit['overall_pass'] and audit['revision']==2 and sha(proof)=='0da964026bc39b05289890fbcda3a51ab307dfd95c7227a7f01d686a25622f6d'
freeze=F/'source-extraction-revision-2/package-freeze.json';assert sha(freeze)==audit['source_freeze_sha256']
group='legacy::10.1021_acs.inorgchem.8b02945'
current=monitor.read_ledger(MON/'ledger.json')['groups'][group];assert current['generation']==1
result=monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id=group,
 data={'source_extraction_revision':2,'source_extraction_freeze':str(freeze),'source_extraction_sha256':sha(freeze),'source_independent_audit':str(proof),'source_independent_audit_sha256':sha(proof),'source_audit_passed':True,'canonical_status':'drafts awaiting distinct canonical audit','molecular_proposal':str(F/'visuals/molecules/package-freeze.json'),'molecular_status':'frozen author proposal; independent audit in progress','publication_status':'not published'},
 note='Complete main8/SI25 source reading and independent extraction audit passed revision2 after four bounded corrections. Canonical, visual, browser and publication gates remain pending.',
 milestones={'read':{'status':'complete','evidence':[str(F/'source-independent-audit/independent-reading-checkpoint.json'),str(proof)]},'extract':{'status':'complete','evidence':[str(freeze),str(proof)]},'audit':{'status':'partial','evidence':[str(proof)],'note':'Source comparison passed; separate canonical and scientific visual audits remain pending.'}})
active=read(D/'active-cutoff.json');scope=D/'friedfeld-source-reviewed-scope-20260920.json'
subprocess.run([sys.executable,str(D/'partition_deadline_scope.py'),'--cutoff-manifest',active['cutoff_manifest']['path'],'--ledger',str(MON/'ledger.json'),'--output',str(scope)],check=True,capture_output=True)
counts=read(scope)['counts'];active['counts']=counts;active['recorded_at']=now;active['latest_status_partition']={'path':str(scope),'sha256':sha(scope)};save(D/'active-cutoff.json',active)
ed=read(MON/'public-progress-editorial.json')
ed['current_work']=[
 {'short_label':'Friedfeld et al. (2019)','title':'Conversion of InP Clusters to Quantum Dots','stage':'Source audit passed; structured records and illustrations under review',
 'summary':'All eight main-paper pages and 25 SI pages were read and compared independently. The extraction audit passed after four preserved corrections to evidence locators, uncertainty wording and a figure’s specimen assignment. Thirty draft records and 51 selected source crops are being prepared for separate data and website checks.',
 'stages':[{'label':'Main/SI pairing and complete source reading','status':'complete','detail':'33 supplied pages inspected independently; original source hashes matched intake.'},{'label':'Extraction and independent source audit','status':'complete','detail':'Corrected revision 2 passed. Reported numeric values and original figure-crop bytes were retained.'},{'label':'Structured records and scientific illustrations','status':'in_progress','detail':'Thirty record drafts; 39 chemical identities, 30 connectivity graphs, 21 reference or computed conformers and five stock definitions. These are proposals pending independent validation and exact record binding.'},{'label':'Website checks and publication','status':'pending','detail':'No Friedfeld contribution is in the live dataset yet.'}],
 'gaps':['Prior cluster coordinates are cited, not supplied as the measured quantum-dot structure.','Source uncertainties, undefined batch links and concentration-specific stock quantities remain explicit.']},
 {'short_label':'Sasongko et al. (2025)','title':'High-Temperature Photoluminescence Enhancement up to 350 K of Monophase α-FAPbI3 Quantum Dots Synthesized via Tailored Hot Injection','stage':'Main-paper and supporting-information extraction',
 'summary':'A separate worker is reading the nine-page main article and eleven-page SI. The supplied sources describe precursor preparation, hot injection, purification and structural and optical measurements.',
 'stages':[{'label':'Source identity and main/SI pairing','status':'complete','detail':'Content-level author pairing checked against the stable local filenames; independent review will verify it separately.'},{'label':'Complete reading and recipe extraction','status':'in_progress','detail':'Retain ligand, washing and growth-condition comparisons with their own specimen evidence.'},{'label':'Independent audit and website publication','status':'pending','detail':'This paper has no published contribution yet.'}],
 'gaps':['Reference crystal parameters must remain separate from measured quantum-dot geometry.']}]
ed['estimate']['current_batch']='Pati CeO2 is published. Friedfeld InP has passed the source audit and is in canonical/visual preparation. Sasongko FAPbI3 is being extracted separately. Completed contributions will be published together when their individual checks pass.'
ed['estimate']['summary']=f"The fixed existing collection has {counts['included_pending_scopes']:,} provisional scopes still pending and three nested identity cases. Screening is complete at the file-disposition level; it is not full scientific review. A validated whole-collection finish forecast is not yet available."
save(MON/'public-progress-editorial.json',ed)
for name in ['build_queue_report.py','build_public_progress.py']:subprocess.run([sys.executable,str(MON/name)],check=True)
note=f'''## 2026-09-20 — InP source audit passed; parallel next paper

Saved {now}. Screen-first, evidence-priority review is operating on the fixed cutoff; later arrivals remain separate. Friedfeld2019 DOI10.1021/acs.inorgchem.8b02945 main8+SI25 complete source audit passed revision2 (audit SHA {sha(proof)}; corrected source freeze {sha(freeze)}). All33 pages independently read; 65 facts,153 typed fact quantities,185 table fields,34 source operations and51 original crops retained. Four resolved extraction issues: two exact-page locators, unspecified statistical definition of the TEM ±0.5nm, and the labeled-cluster specimen in SI FigureS1. Original source/extraction versions remain immutable; no source numeric values or crop bytes changed.

Norberg has30 draft canonical records,58 operation instances,750 measurements and a417-item reader with51 selected crops; separate canonical audit remains pending. Root molecular proposal freeze7c1a864dbdf6b3177d2aa907b4f3c5893232b0c7d213ab18312d12655d4f4c0f contains39 identities,30graphs2D,21reference/computed3D andfive stock definitions; Backlog is independently auditing it. Its198bound files remain immutable. Root inspected10 key source pages for presentation, not all33. New computed molecule conformers are illustrative and are not product crystal structures or training pairs. In particular, a varied-concentration MSC stock must not inherit the representative20mg charge. Canonical bindings, apparatus/product views, browser and publication checks remain pending; no Friedfeld Site import.

Peng is extracting the separately admitted Sasongko2025 FAPbI3 DOI10.1021/acs.jpcc.5c05144 main9+SI11. Current two paper claims remain distinct. Latest intake/admission20260920T141934Z preserves original filenames and content hashes. Source revision corrections were a bounded interruption; resume Sasongko from its existing work. Four runtime agent slots are used for source extraction, independent audit, canonical/illustration work and root integration. No new task/automation or paid API run; no paper downloads. PubChem chemical identity metadata was retrieved for molecule qualification only.

Live science remains dataset0.31.0:626records,118routes,49hubs,39sourcegroups,34formalreaders; exact atomic pairs0. Current progress files are regenerated locally and await their own deployment verification. Science commit3b22523e24834b0789e8b0fd01ca3a9018f66a21 and previously verified progress7d34e4d9e0a0d5d192939823cde4bdf01fdb2d9b remain the last verified public states until a new receipt. Existing source-excluding public projection, citations, memory/skills/history publication and batched individually passed contributions continue. Relevant workflow remains recorded in mattersyn-paper-to-site; no skill behavior change is required for this milestone.

'''
p=M/'MEMORY.md';p.write_text(note+p.read_text('utf8'),'utf8')
save(F/'progress-publication/local-checkpoint.json',{'at':now,'source_audit_sha256':sha(proof),'source_freeze_sha256':sha(freeze),'queue_group':group,'cutoff_counts':counts,'public_science_version':'0.31.0','new_science_published':False,'progress_deployment':'pending','memory_saved':True})
print(json.dumps({'source_audit':'passed','active_claims':result['active_review_claims'],'cutoff_counts':counts,'progress_deployment':'pending'}))
