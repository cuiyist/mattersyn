from pathlib import Path
from datetime import datetime, timezone
import json
HERE=Path(__file__).resolve().parent
MON=HERE.parent.parent
ROOT=MON.parent.parent
now=datetime.now(timezone.utc).isoformat()
p=MON/'public-progress-editorial.json'; d=json.loads(p.read_bytes())
d['workflow']={
 'summary':'Screen the fixed collection first, prioritize usable synthesis evidence, and review papers in parallel with a separate independent audit for each.',
 'screening_scope':'The 20 September screening snapshot accounts for all 13,831 top-level cutoff files: 13,593 have text-based candidate screening and 238 need manual format/text inspection. Three additional nested PDFs were also screened and remain held for identity and queue reconciliation. Thirty-one later-arrival files in this snapshot are queued separately. Screening is not full reading or a no-recipe exclusion.',
 'steps':[
  'Preserve stable filenames and verify main-paper/SI associations against content and hashes.',
  'Use synthesis and structure evidence to rank papers; retain partial recipes, unsuccessful outcomes and unresolved cases.',
  'Extract one paper while a different reviewer audits another. Every contribution retains its own source, sample and figure checks.',
  'Generate academic readers from reviewed records and reusable illustrations, checking each source-specific condition and chemical identity.',
  'Publish completed, independently passed contributions together; leave unfinished papers in review.'],
 'capacity':'Up to five active paper claims; current runtime supports four simultaneous agents including the coordinating agent. These are different limits. Completed members can free review slots while earlier work continues.',
 'paid_processing':'The paid API pilot is deferred. Work continues with the existing local setup.',
 'screened_at':'2026-09-20T04:15:45.301305+00:00',
 'fixed_pending_provisional_scopes':9514,
 'manual_file_dispositions':238,
 'nested_identity_cases':3,
 'later_arrival_files_at_screen':31}
d['current_work'][0]['stage']='Independent canonical and illustration audits; integration pending'
d['current_work'][0]['stages'][3]['detail']='Frozen canonical/reader proposal under a distinct reviewer; corrections stay versioned'
evans={'short_label':'Evans et al. (2010)',
 'title':'Mysteries of TOPSe Revealed: Insights into Quantum Dot Nucleation',
 'stage':'Source pairing, inventory and extraction assigned',
 'summary':'A high-priority candidate with a three-page main paper, 21-page supplement and CIF in the existing local collection. It covers phosphine precursor purity, nucleation controls and quantum-dot reactions. Source identity, specimen assignments and CIF scope require review before scientific publication.',
 'stages':[{'label':'Source files fingerprinted','status':'complete','detail':'Three unchanged local files; original names preserved'},
           {'label':'Main/SI/CIF pairing and reading','status':'in_progress','detail':'Content verification and complete page inventory'},
           {'label':'Extraction and independent audit','status':'pending','detail':'Separate author and auditor; negative controls retained'},
           {'label':'Illustrated reader and publication','status':'pending','detail':'After scientific and website checks'}],
 'gaps':['A CIF file does not establish measured quantum-dot coordinates; its chemical species and specimen association must be verified.']}
d['current_work']=[d['current_work'][0],evans]
d['recent_milestones'].insert(0,{'at':now,'text':'Corpus screening refreshed and fixed-cutoff selection activated. A rolling review slot admitted Evans 2010 alongside Heo; original four published batch contributions and their audits remain unchanged.'})
d['estimate']['summary']='The two-month target covers the fixed existing collection. After mapping the 45 previously ungrouped cutoff files, the known backlog is 9,514 pending provisional scopes, plus three nested identity cases. The required pace is about 159 closures/day over 60 days, or 190/day over 50 production days. Achievable capacity and the recipe-bearing fraction remain unverified.'
d['estimate']['current_batch']='Heo remains in final data/illustration review; Evans has entered source pairing and extraction. No new measured completion-time forecast is claimed from this workflow change.'
d['estimate']['scenarios']=[]
d['estimate']['notes']=[
 'A closure is either an independently evidenced no-recipe exclusion or a retained contribution passing reading, extraction, audit, website and publication checks.',
 'The frozen collection has 13,831 top-level document copies and three nested document candidates. File copies, provisional scopes and synthesis recipes are different counts.',
 'Later-arrival papers remain separate. Late or changed supporting information for an included paper reopens the relevant review.',
 'The paid pilot decision is deferred. Screening speed cannot be used as the detailed-review rate; throughput will be updated from completed audited contributions.']
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for rel in ('progress.html','index.html'):
 p=ROOT/'recipe-atlas/dist'/rel
 p.write_text(p.read_text(encoding='utf8').replace('progress.mjs?v=1','progress.mjs?v=2'),encoding='utf8')

skill=ROOT/'skills/mattersyn-paper-to-site'
p=skill/'references/incoming-corpus.md'; t=p.read_text(encoding='utf8')
t=t.replace('Resume the remaining batch before selecting the next one.', 'Keep unfinished papers active. With the September 20 authorization, explicitly refill free active-paper slots after screening; keep each completed member and its audit/release in history.')
t=t.replace('Use `claim-batch --reviewer mattersyn-primary --size 5` to resume an unfinished batch or select eligible scopes by the active evidence-priority policy.', 'Use `claim-batch --reviewer mattersyn-primary --size 5` to resume work. The September 20 pipeline authorization also allows `--refill` to admit screened papers into free active slots; keep at most five active paper claims and preserve all original members and audits. Claim only as many papers as can be usefully progressed within current runtime capacity.')
t+='''\n\n## Screen-first rolling review (September 20 authorization)\n\nThe user explicitly approved full-collection screening, independent extraction/audit work across papers, websites generated from reviewed data and reusable illustrations, and batched publication. This supersedes the old requirement to finish every original batch member before admitting another paper. Runtime concurrency remains four agents including root; five claimed papers is a queue bound, not five simultaneous workers. A different author audits each extraction. Release ready contributions together without waiting for unresolved papers.\n\nRefresh screening from a frozen ledger, reusing only hash-verified caches. In the original project, run `deadline-20260920/partition_deadline_scope.py` against the current ledger, then `activate_screened_cutoff.py --ledger ... --report ... --partition ... --output <new-directory>`. It requires complete per-file dispositions, fresh cutoff mapping and immutable dependency hashes. It activates only cutoff-member ranking rows; the existing `require_screened` gate keeps later-arrival groups out of automatic and explicit new claims. Use this wrapper for subsequent activations rather than installing the unrestricted whole-growing-corpus ranking. Preserve manual/unreadable cases and nested identity cases; never turn a low automated score into a no-recipe exclusion.\n\nUse `claim-batch --reviewer mattersyn-primary --size N --refill` only after that gate is active and a useful worker slot is available. Refill preserves the batch ID, old members, per-paper checkpoints and deployment history; it does not promote completed status or bypass changed-source checks. Keep source-neutral models separate from each paper's amounts, grades, conditions and specimen associations. Apply bounded audited metadata overlays when reusing a model rather than silently altering a frozen source package. The API pilot decision is deferred: continue existing local processing without starting paid requests or new infrastructure.\n'''
p.write_text(t,encoding='utf8')
p=skill/'SKILL.md'; t=p.read_text(encoding='utf8'); t=t.replace('Several individually passed contributions may be published together.', 'Several individually passed contributions may be published together. The September 20 screen-first workflow permits refilling completed active-paper slots while unfinished papers retain their individual claims and audits; see the incoming-corpus reference.')
p.write_text(t,encoding='utf8')

p=ROOT/'MEMORY.md'; t=p.read_text(encoding='utf8')
entry=f'''## 2026-09-20 — Screen-first workflow activated; paid pilot deferred\n\nSaved {now}. The user explicitly approved: screen everything first; prioritize papers with usable synthesis information; extract and independently audit different papers in parallel; generate websites from reviewed data/reusable illustrations with paper-specific checks; publish passed contributions together. The paid API proposal decision is deferred. No paid requests or new infrastructure are authorized.\n\nScreen refresh completed in57.6seconds by reusing13473exact-hash caches and387new extractions (plus2bounded manual dispositions), not by reading/reviewing that many papers. All13862snapshot files were actually hashed and assigned dispositions. Fixed cutoff:13831top-level copies =13593text-screened candidates+238manual format/text cases;31later-arrival copies separate. All45previously unmapped cutoff files now map to44additional provisional scopes:9536includedscopes,9514pending and22closed. Three nested unique PDFs were hash-checked and text-screened separately; retain them for identity/queue reconciliation. Do not silently drop them or count them as fully read. Full coverage proof and exact report/ledger hashes: research-assets/incoming-paper-monitor/deadline-20260920/workflow-20260920T0412/.\n\nNew `activate_screened_cutoff.py` installed9536cutoff-only rankings. Later arrivals receive no eligible rank; all original claims, review statuses and arrival order are unchanged by activation. Regenerate the partition against the current ledger before future activations and always use this cutoff wrapper. New optional monitor `claim-batch --refill` permits a rolling pipeline up to five ACTIVE papers while preserving original members, independent audits and release history.44selection/batch/view tests passed. The original five-paper pilot stays4/5published; no Heo scientific publication is claimed.\n\nHeo: backlog independently audits frozen canonical/reader v1; norberg independently audits molecules; peng prepares exact slot/stock bindings and a preserved locator correction (In66-X Table2footnotec belongs PDFp5/printed1124). Initial canonical findings include duplicate reader sample links and a broken local SI-audit relative reference; keep v1 and author corrections separate.\n\nOne new high-priority scope is claimed alongside Heo: Evans, Evans and Krauss (2010), Mysteries of TOPSe Revealed: Insights into Quantum Dot Nucleation, DOI10.1021/ja103805s. Main3pages+SI21pages+CIF; bundle177861643fc55cc830f504a68ce9e6d62cacbc7a7182376e76e1dc036a21a1bb. Main3867a60f67a10f4f28f9aa960ed4cd13b621d039e8472fcac6d10713a5e86f81; SI017dfc31dcaa290c2a7c08a8a4dbb0a672b973449ec3a74e0e690141bd558ed9; CIFabd4ecdae2c4a445921b9fdde415fda76208d11fe0df40cc510c7fa94b510ef4. Pairing/species scope remains unverified; a supplied CIF is not automatically a QD structure pair. Manifest: batches/20260920-rolling-pipeline/intake-manifest.json. Extraction assigned to norberg after their Heo molecule audit; another agent will audit Evans. No source filenames changed or new papers downloaded.\n\nPublic progress/memory/skill synchronization is prepared in this checkpoint; verify deployment before claiming this update live. Existing published science remains dataset0.23.0/470records/31primarysources. Keep source papers/SI and fulltext/page caches local under the current public projection policy.\n\n'''
if '## 2026-09-20 — Screen-first workflow activated; paid pilot deferred' not in t:p.write_text(entry+t,encoding='utf8')
print(json.dumps({'saved_at':now,'editorial_updated':True,'project_skill_updated':True,'memory_updated':True,'paid_run_started':False}))
