"""Save separately evidenced queue milestones after the verified Morrison release."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, subprocess, sys

R=Path(__file__).resolve().parent; MON=R.parents[1]; M=MON.parents[1]
sys.path.insert(0,str(MON)); import monitor
sys.path.insert(0,str(M/'research-assets')); import public_projection_policy as policy
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
now=datetime.now(timezone.utc).isoformat(); L=R/'acsami.1c18038'; G=R/'ja212032q'
audit=L/'canonical-reader-independent-audit/independent-audit-v1.json'
assert read(audit)['status']=='passed'
molecules=L/'visuals/molecules/package-freeze.json'
monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='legacy::10.1021_acsami.1c18038',note='Complete supplied source and canonical/reader audits passed. Molecular package frozen for separate independent audit; apparatus preparation active. No Site import or publication.',data={'current_step':'Source and structured-data audits passed; molecular and apparatus review underway','canonical_reader_audit':{'path':str(audit),'sha256':sha(audit)},'molecular_proposal':{'path':str(molecules),'sha256':sha(molecules),'independent_status':'pending'}},milestones={'extract':{'status':'complete','evidence':[str(audit),str(L/'canonical-proposal/v1/package-manifest.json')],'note':'16 records, 21 operations, 1,149 measurement/context entries and 224 reader items independently checked.'},'audit':{'status':'partial','evidence':[str(audit)],'note':'Source and canonical/reader passed; visual and integration gates remain.'}})
identity=read(G/'intake-identity.json')
for doc in identity['documents']:
 assert policy.exclude_path(Path(doc['identity_preview']).relative_to(M).as_posix())=='source_page_render'
monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='10.1021_ja212032q',note='First-page title/byline identity checked for local 10-page main and 9-page SI. Duplicate incoming/legacy copies have matching hashes. Complete reading and extraction assigned to an independent paper author; full scientific audit pending.',data={'current_step':'Complete main/SI reading and extraction underway','intake_identity':{'path':str(G/'intake-identity.json'),'sha256':sha(G/'intake-identity.json')},'source_bundle_sha256':identity['bundle_sha256'],'source_reading_assigned_to':'/root/backlog_eta'},milestones={'read':{'status':'partial','evidence':[str(G/'intake-identity.json')],'note':'First-page identity only has been checked by root; complete supplied 19-page review underway.'}})
deadline=MON/'deadline-20260920'; cutoff=read(deadline/'active-cutoff.json')
partition=deadline/'admission-20260920T082035Z/post-alias-scope-partition.json'
subprocess.run([sys.executable,str(deadline/'partition_deadline_scope.py'),'--cutoff-manifest',cutoff['cutoff_manifest']['path'],'--ledger',str(MON/'ledger.json'),'--output',str(partition)],check=True,capture_output=True)
counts=read(partition)['counts']
ed=read(MON/'public-progress-editorial.json')
ed['current_work']=[{
 'short_label':'Lian et al. (2021)',
 'title':'Realizing Near-Unity Quantum Efficiency of Zero-Dimensional Antimony Halides through Metal Halide Structural Modulation',
 'stage':'Source and structured-data audits passed; illustrations under review',
 'summary':'All 34 supplied main/SI pages were reviewed. The 16 structured records and 224 reader items passed a separate audit. Molecular illustrations cover 45 material slots and five stocks; their independent review and the 21 operation diagrams are still in progress.',
 'stages':[
  {'label':'Complete source reading and extraction','status':'complete','detail':'Eight main pages and 26 SI pages; 53 selected crops and nine tables with 891 cells.'},
  {'label':'Independent source and structured-data audits','status':'complete','detail':'Bulk crystals, nanocrystals, films and calculated results retain separate sample assignments.'},
  {'label':'Molecular and apparatus review','status':'in_progress','detail':'Distinct author and reviewer; no new product coordinates or training approval.'},
  {'label':'Website integration and publication','status':'pending','detail':'Release follows visual, integration and browser checks.'}],
 'gaps':['Separate crystal-data ZIP and video attachments mentioned by the source are absent from the supplied local pair.','Bulk-crystal coordinate tables do not establish an exact nanocrystal structure–recipe pair.']
},{
 'short_label':'Ghosh et al. (2012)',
 'title':'New Insights into the Complexities of Shell Growth and the Strong Influence of Particle Volume in Nonblinking “Giant” Core/Shell Nanocrystal Quantum Dots',
 'stage':'Complete main/SI reading and extraction underway',
 'summary':'The local 10-page main paper and nine-page SI have matching title/byline identities. Content-identical copies were reconciled without changing original filenames. Full synthesis, structure and property review has begun.',
 'stages':[
  {'label':'Stable local source bundle','status':'complete','detail':'Main/SI identity and content fingerprints saved; duplicate copies retained as provenance.'},
  {'label':'Complete reading and extraction','status':'in_progress','detail':'First-page intake is complete; no full-source approval is claimed yet.'},
  {'label':'Independent scientific audit and website release','status':'pending','detail':'Separate per-paper audit required before integration.'}],
 'gaps':['Recipe variants, figure assignments and shell/core sample lineage remain under review.']
}]
ed['estimate']['summary']=f"The two-month target covers the fixed existing collection. {counts['included_pending_scopes']:,} provisional cutoff scopes remain pending, plus three nested identity cases. Roughly 159 closures per day over 60 days, or 190 per day over 50 production days, would be required. Achievable capacity and the recipe-bearing fraction remain unverified."
ed['estimate']['current_batch']='The retained five-paper pilot and Evans/Morrison rolling contributions are published. Lian illustrations and Ghosh complete source extraction proceed in parallel, with separate audits. The throughput required for the two-month goal remains unvalidated.'
ed['workflow']['fixed_pending_provisional_scopes']=counts['included_pending_scopes']
ed['workflow']['scope_counts_updated_at']=now
ed['workflow']['later_arrival_groups_current']=counts['later_arrival_group_candidates']
ed['recent_milestones'].insert(0,{'at':now,'text':'Lian complete source and structured-data audits passed; illustrations remain under review. The completed Morrison slot was refilled with Ghosh (2012), on giant CdSe/CdS quantum dots. Both retain distinct review and publication gates.'})
ed['recent_milestones'][1]['text']='Morrison CdSe/CdS contribution published and anonymously verified: 2 synthesis routes, 8 supporting procedures and 8 observation records. Dataset 0.26.0 has 530 records, 103 routes/variants and 44 material/component hubs.'
save(MON/'public-progress-editorial.json',ed)
memory=f'''## 2026-09-20 — Parallel review handoff after verified Morrison publication

Saved {now}. Live dataset 0.26.0 contains 530 structured records, 103 synthesis routes/variants, 44 material/component hubs, 34 source groups and 29 formal readers. Morrison science commit 22e894390eae26cfcf4eb84c4c69157f49cf617b was built at 2026-09-20T08:10:47Z and passed all 47 anonymous checks. Final progress/status publication follows separately. Exact structure–recipe pairs remain zero. Morrison publication-label metadata independently passed audit 60f55e991afd5d4d6e317a3c161be581727857bde30d40008b015bb406b1ed42; scientific content is unchanged.

Lian DOI 10.1021/acsami.1c18038: source revision 2 and canonical/reader v1 independently passed. Canonical audit {sha(audit)} checks 16 records, 21 operations, 1,149 measurement/context entries, 224 reader items and 891 table cells. Molecular freeze {sha(molecules)} covers 45 slots, five stocks/14 components and 27 allowlisted assets; Peng independently audits. Norberg prepares apparatus outside Site. No new product coordinates, training approval or Site publication. Missing local crystal ZIP/video remain explicit.

Ghosh DOI 10.1021/ja212032q: generation 2 bundle {identity['bundle_sha256']}, local main 10 pages plus SI nine pages. Root checked first-page title/byline identity only; Backlog now reads/extracts the complete pair under batches/20260920-rolling-pipeline/ja212032q. Preserve every shell-growth variant and sample/figure assignment; source audit remains pending. Incoming/legacy duplicates have identical hashes, original filenames unchanged. Identity page renders are in source-render and explicitly excluded from public projection; generic private folder names alone are not an exclusion rule.

Post-alias fixed-cutoff partition: {counts['included_pending_scopes']:,} pending provisional scopes, {counts['included_terminal_scopes']} terminal scopes, {counts['later_arrival_group_candidates']} later-arrival groups and three held nested identity cases. These are worklist scopes, not verified unique papers/materials/recipes. Keep the existing single heartbeat, fixed-cutoff evidence priority, no source downloads and no paid API runs.

The Windows long-path synchronization correction passed separate audit bea2f99f57c81bd22bb522d2bc723e70d5da1210d216c850e4b5ca9567c13c25 (21 cases, 484-character source/destination paths). Preserve logical relative paths and non-dereferencing symlink checks. Both public GitHub projections exclude source binaries, full text and complete pages. Current publication paths remain mattersyn-github-project and mattersyn-github-public-clean/mattersyn-site.
'''
p=M/'MEMORY.md';p.write_text(memory+'\n'+p.read_text(encoding='utf8'),encoding='utf8')
print(json.dumps({'saved_at':now,'active_papers':['Lian 2021','Ghosh 2012'],'cutoff_counts':counts,'full_page_exclusion_verified':True}))
