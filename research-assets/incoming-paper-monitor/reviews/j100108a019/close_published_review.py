from pathlib import Path
import json,sys,hashlib
from datetime import datetime,timezone
B=Path(__file__).resolve().parent;M=B.parents[1];P=B.parents[3]
sys.path.insert(0,str(M));import monitor
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
release=read(B/'publication-checkpoint.json');assert release['deployment_status']=='succeeded'
release['archive_sha256']=hashlib.sha256((P/release['archive']).read_bytes()).hexdigest();write(B/'publication-checkpoint.json',release)
cp=read(B/'checkpoint.json')
cp.update(canonical_records_created=13,training_eligible='Three formulation records: precursor_selection and partial_protocol only; all other source records excluded',website_published=True,publication=release,next_action='This supplied-main contribution is published. At the next scheduled continuation, scan and claim the oldest eligible remaining review unit. Reopen this source if additional or changed local SI arrives.',current_work_items=[],site_implementation_status='Published: all thirteen records, full source evidence, original figures/table, molecules, stage-specific apparatus, illustrative crystal models, material hubs, inventory and gated exports.',source_item_coverage_status='Staged coverage reconciled and reader data-retention independently checked; targeted actual browser QA passed. Scope remains supplied main only, SI unverified.',draft_schema_validation='Final 168-record dataset build, record/asset/site checks and exact Littau measurement/product/lineage preservation passed.',known_duplicate='Both local main copies freshly hashed identical; existing source identity reused.')
cp['private_molecular_assets']['imported']=True
write(B/'checkpoint.json',cp)
stages=read(B/'milestones.json')
updates={
 'extract':(['coverage-ledger.json','final-record-delta.json','final-build-validation.json'],'All relevant supplied-main items reconciled across typed records, context, unresolved gaps and explicit exclusions; 3 variants, 9 procedures, 1 observation, 48 measurement/reference entries and 13 source crops.'),
 'audit':(['independent-audit.json','canonical-drafts-audit.json','procedure-drafts-independent-audit.json','context-draft-audit.json','frontend-render-audit.json','frontend-evidence-crystal-audit.json'],'Source, records and bounded reader mapping independently reviewed; 30 final frontend/evidence checks passed. Original scientific caveats retained; SI unverified.'),
 'integrate':(['browser-qa.json','final-build-validation.json','final-record-delta.json'],'Actual browser checks and final dataset/site/asset checks passed; 136 source evidence items, molecular/apparatus/crystal interactions, sample-scoped figures and material evidence views integrated.'),
 'publish':(['publication-checkpoint.json'],'Native Sites deployment succeeded for public version 12 with the exact pushed source and validated archive. This closes only the supplied-main scope; it does not assert verified or absent SI.')}
for stage,(files,note) in updates.items():stages[stage]={'status':'complete','evidence':[str(B/f) for f in files],'note':note}
write(B/'milestones.json',stages)
result=monitor.checkpoint(M/'ledger.json','mattersyn-primary','complete',cp,'Published Littau supplied-main contribution; SI unverified; five evidence stages complete.',milestones=stages)
(B/'NEXT_ACTION.md').write_text('# Littau contribution published\n\nRead publication-checkpoint.json and final-build-validation.json. Version12 is published; the queue claim is closed for the seven supplied main pages only. SI remains unverified. Resume oldest remaining eligible local review unit on next scheduled continuation; late or changed SI reopens this source.\n',encoding='utf-8')
# Keep the historic release checkpoint intact; point the queue report to this release.
report=M/'build_queue_report.py';text=report.read_text(encoding='utf-8').replace('DEFAULT_RELEASE = PROJECT / "research-assets/quality-20260918/release-checkpoint.json"','DEFAULT_RELEASE = HERE / "reviews/j100108a019/publication-checkpoint.json"')
text=text.replace('These published records predate the current two-folder backfill. They are not newly completed queue items and do not exempt their papers from completeness re-audit.','Published totals include earlier contributions and completed queue work. Consult each source’s five milestones; publication alone does not waive any outstanding completeness review.')
text=text.replace('These are not newly completed queue items; prior publication does not waive re-audit.','Published totals and completed queue counts are separate measures; prior publication does not waive outstanding review.')
report.write_text(text,encoding='utf-8')
memory=P/'MEMORY.md';existing=memory.read_text(encoding='utf-8')
note='''## 2026-09-18 — Littau silicon contribution published; supplied main only

Published public Site version12, dataset0.5.0, source commit a06e661de477982de4715d9ad802dd1c4698fc5d. Native deployment succeeded at2026-09-19T04:14:04Z; exact IDs/archive evidence are in incoming-paper-monitor/reviews/j100108a019/publication-checkpoint.json. Public URL remains https://mattersyn-recipe-atlas.cuiy781513.chatgpt.site. Seven supplied main pages read and independently reviewed; matchingSI not located/verified. Both local main copies remain byte-identical. This is one completed supplied-main review unit, not completion of the corpus or a claim that SI does not exist.

Thirteen canonical records comprise3synthesis variants,9supporting procedures and1AKS41 contextual observation. All48measurement/reference entries retain their specimen/state scope;136reader evidence items,12original figures andTableI are integrated. Stage-specific flow reactors and analysis apparatus,19new chemical registry entries,7illustrative molecular conformers, and distinct ideal Si unit-cell/finite-reference views are available. The reference models are not measured atomic structures or DFT-ready experimental inputs. Only the3variants enter precursor-selection and partial-protocol exports; no new size, exact-structure, optical-outcome or success labels.

Current public inventory:168canonical records (35routes,9controls,23procedures,1observation,100benchmark rows),15material hubs (11direct systems,4component-only),11source groups. Legacy indexing counts remain7,373documents/4,176groups and do not count newly arriving papers as reviewed. Five formal matched-main/SI reviews cover74pages; the new formal main-only review covers7pages separately. Dataset/link/privacy/asset checks passed;30bounded independent reader checks and actual browser protocol/molecule/crystal/figure-filter/mobile/search checks passed. Three method cards stay separate from all13material-level evidence records. Final source fingerprint unchanged. All five queue milestones complete for this scoped contribution; next continuation resumes oldest remaining eligible paper.

The user’s5–8hour concern is valid: that was not measured per-paper throughput and conflated reusable infrastructure with curation. Earlier note below is retained as history, superseded by the correction. Avoid redundant bookkeeping and reuse validated work. Memory and installed MatterSyn skill timing guidance updated.

Windows publication note: the .mjs wrapper could not find Bash; the official package-site.sh succeeded via explicit Git Bash --login with /c/Users/... absolute paths under the host runtime. C:/ archive paths are interpreted by GNU tar as remote hosts. Source push needed a command-scoped safe.directory because sandbox/host account ownership differs. No persistent credentials or global Git changes were made.

'''
memory.write_text(note+existing,encoding='utf-8')
print(json.dumps({'group_id':result['group_id'],'status':result['status'],'claim_retained':result['claim_retained'],'public_version':release['public_live_version']}))
