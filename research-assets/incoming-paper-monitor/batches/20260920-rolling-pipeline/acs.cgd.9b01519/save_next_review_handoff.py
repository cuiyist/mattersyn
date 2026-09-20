from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
N=Path(__file__).resolve().parent;MON=N.parents[2];M=N.parents[4]
read=lambda p:json.loads(p.read_text('utf8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
sys.path.insert(0,str(MON));import monitor
e=read(MON/'public-progress-editorial.json')
e['current_work'].append({'short_label':'DOI 10.1021/la8031286','title':'Next evidence-ranked source from the fixed collection','stage':'Main/SI identity checks and separate source reading','summary':'The next available review slot has been filled from the screened fixed collection. A separate author and reviewer are checking the supplied main article and SI before admitting any scientific data.','stages':[{'label':'Source identity and main/SI pairing','status':'in_progress','detail':'Two supplied files have intake hashes; title/content checks and complete source reading are underway.'},{'label':'Independent scientific audit','status':'in_progress','detail':'A distinct reader is preparing source evidence. No reviewed recipe or public contribution is claimed.'}],'gaps':['Complete extraction and final independent comparison remain pending.']})
e['estimate']['current_batch']='Sommer supplied-main contribution is published; its declared SI remains unverified. Matuhina CsMnCl₃ and the next evidence-ranked main/SI source are under separate extraction and independent review. Whole-corpus throughput and finish date remain unvalidated.'
save(MON/'public-progress-editorial.json',e)
monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='10.1021_la8031286',note='Review capacity refilled from fixed-cutoff evidence-ranked queue. Peng authors source extraction; Norberg independently reads main/SI while Matuhina comparison awaits author freeze.',data={'current_step':'Source identity/pairing and independent full-source reading','review_folder':str(N.parent/'la8031286'),'intake_manifest':str(N.parent/'intake-20260920T114139Z/intake-manifest.json')})
counts=read(MON/'deadline-20260920/sommer-release-scope-20260920.json')['counts']
text=f'''## 2026-09-20 — Rolling review handoff after verified Sommer release

Sommer is publicly verified at science commit d91090111c2ae39639fc0064cef09872b93b46e1, built 11:39:37 UTC. Its 94 anonymous endpoint checks and both 37-citation READMEs passed. The final publication labels were applied only after this proof; a progress-only deployment is being prepared. Do not redo closed Sommer, Ghosh or Lian scientific work. Dataset 0.29.0: 586 structured records, 114 synthesis routes/variants, 47 material/component hubs, 37 source groups and 32 formal readers. Exact structure–recipe pairs remain zero.

Two active fixed-cutoff claims: Matuhina (2023), DOI 10.1021/acsanm.2c04342, has 13 main and 13 SI pages. Backlog has read and assembled extraction (39 operations, 28 materials/five stocks, seven tables/55 rows, 30 crops) and is finishing its first source freeze; Norberg completed independent original reading and table baseline and awaits that freeze. The next paper DOI 10.1021/la8031286 is admitted from intake-20260920T114139Z, bundle b90762f8d91a417cdecfdd62da360d015e6dc40902529806048dfc5635a28db3. Peng authors extraction; Norberg independently checks main/SI. Work roots are batches/20260920-rolling-pipeline/acsanm.2c04342 and la8031286. Root alone mutates Site and ledger. Preserve separate authorship, all source contradictions, and unknown sample assignments.

Current cutoff partition: {counts['included_known_canonical_groups']:,} provisional scopes, {counts['included_pending_scopes']:,} pending and {counts['included_terminal_scopes']} terminal within their reviewed scope; three nested identity cases and 238 manual format/text cases remain. Later arrivals: {counts['later_arrival_group_candidates']} groups / {counts['later_arrival_file_candidates']} file candidates, separate from the deadline collection. Duplicate reconciliation can change provisional counts. Screening is not complete scientific reading and the two-month capacity remains unvalidated. Existing heartbeat continues; no duplicate automation, new downloads or paid API run.
'''
p=M/'MEMORY.md';p.write_text(text+'\n'+p.read_text('utf8'),'utf8')
print('Next claims, memory and current work saved; no added scientific publication claim.')
