from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
A=Path(__file__).resolve().parent;MON=A.parents[2];M=A.parents[4];P=A.parent/'la8031286'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read(A/'site-integration-proposal/progress-release-anonymous-verification.json')
assert v['status']=='passed' and len(v['anonymous']['checks'])==219
assert read(MON/'latest-publication.json')['dataset_version']=='0.30.0'
current={'source':P/'source-independent-audit/independent-audit-v1.json','canonical':P/'canonical-reader-independent-audit/independent-audit-v2.json','apparatus':P/'visuals/apparatus-independent-audit/independent-audit.json','product':P/'product-context-independent-audit/independent-audit.json'}
assert all(read(p)['status']=='passed' for p in current.values())
molecules=P/'visuals/molecules-independent-audit/independent-audit.json'
molnote='Molecular audit is pending a bounded correction: nitrate N+ atoms were incorrectly tagged as tertiary amine nitrogen; the graph, formula and coordinates are unaffected. Preserve the original freeze and the finding, then audit the overlay before import.'
if molecules.exists() and read(molecules).get('status')=='passed':
 current['molecules']=molecules;molnote='Molecular audit passed with a preserved correction to nitrate functional-group annotations. Use its final effective-file map and bounded correction receipt, not the original incorrect highlight metadata.'
now=datetime.now(timezone.utc).isoformat()
handoff={'saved_at':now,'dataset_version':'0.30.0','scientific_site_commit':'bfdb06744a991fb26ea64781691ba5035c2ea5ee','progress_site_commit':v['site_commit'],'anonymous_verified_endpoints':219,'next_paper':'pati2009','next_actions':['Resolve and audit remaining molecular correction if open.','Prepare a root-owned promotion from exact independently passed canonical v2, apparatus and final chemical/product packages.','Keep all previously published607records and approved task exports unchanged unless a separately justified revision is audited.','Run actual reader/data consumers before freezing promotion, then independently inspect transport, build and mounted browser operation/figure/sample controls.','Publish completed scientific contributions together and verify exact deployed bytes; close paper only after that verification.'],'passed_audits':{k:{'path':str(p),'sha256':sha(p)} for k,p in current.items()},'molecular_state':molnote,'no_pati_science_imported':True,'new_downloads_or_paid_api_authorized':False}
(A/'site-integration-proposal/final-handoff.json').write_text(json.dumps(handoff,indent=2)+'\n','utf8')
p=M/'MEMORY.md';p.write_text(f'''## 2026-09-20 — Verified delivery and exact resume point

Saved {now}. This checkpoint supersedes stale Pati preparation wording in earlier release-history notes. Live science is dataset0.30.0,607records115routes48hubs38sourcegroups33readers; science commit bfdb06744a991fb26ea64781691ba5035c2ea5ee. Latest progress-only site commit {v['site_commit']} built {v['build']['updated_at']};219anonymous endpoints and both38-citation READMEs passed. Actual public CsMnCl3 hub and progress page were loaded in the browser. The Matuhina claim is complete within supplied13main+13SI scope. Original sourcePDFs/SI/fulltext/fullpages stay local. All existing586records and training exports remained unchanged; no exact atomic pair admitted.

Pati is the one active review claim. Source, canonical/reader v2,35scene apparatus and39mapping symbolic-product audits all passed. {molnote} No Pati scientific records are in Site yet. Root alone must prepare/import the independently passed packages and run transport, actual reader/browser and publication gates. Do not claim the source fully published or infer measured atom positions from phase names. Main/SI eightpages are fully read,20selectedoriginalcrops and fullSI XPS table retained. Use final-handoff.json in the Matuhina site-integration-proposal folder for exact audit hashes and next actions.

The installed/project MatterSyn skill now requires chemically validated functional-group labels using neighbor identity, bond order and charge: nitrate N is not an amine. Both skill copies match hash117fa4d7e7dcd3e94c954bea483dda6c8a9eab13123f2333fbfffaeb48f1c307 and quick validation passed. Canonical reader schema must pass the actual consumer before proposal freezing; preserve narrow correction receipts. Current user instruction remains screen all cutoff files first, evidence-priority parallel independent reviews and batched publication. Fixed pending scopes9503,threeheldnested; later379groups390files remain separate in the latest saved partition. Counts are provisional scope/file counts, not verified recipes. Whole-corpus finish capacity remains unvalidated.

Existing active five-minute heartbeat mattersyn-sequential-paper-review was inspected and already contains this authorization, quiet-when-unchanged behavior and GitHub hosting/publication policy. Do not duplicate it. No paid API run, source downloads or expanded infrastructure. Next GitHub project-only commit will save this exact deployment proof and handoff without changing website science.

'''+p.read_text('utf8'),'utf8')
print(json.dumps({'saved':str(A/'site-integration-proposal/final-handoff.json'),'passed_audits':list(current),'molecular_state':molnote}))
