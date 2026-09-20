"""Save memory and current-generation milestone evidence after native deployment success."""
from pathlib import Path
from datetime import datetime,timezone
import json
B=Path(__file__).resolve().parent;M=B.parents[3];Q=B.parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=read(B/'publication-checkpoint.json')
assert p['deployment_status']=='succeeded' and p['source_pushed']
assert p['site_project_id']=='appgprj_6aaad65d939881918d6b5d5254e0f0d9'
now=datetime.now(timezone.utc).isoformat()
milestones={}
for stage,refs in {'read':['source-manifest.json','source-identity.json','source-audit.json'],'extract':['canonical-records-audit.json','public-review-proposal/source-item-coverage.json','crop-assets/manifest.json'],'audit':['source-audit.json','canonical-records-audit.json','apparatus-source-audit.json','reader-assets/canonical-to-reader-audit.json'],'integrate':['build-validation.json','browser-qa.json','reader-assets/canonical-to-reader-audit.json','inventory-proposal/validation.json'],'publish':['publication-checkpoint.json']}.items():
    assert all((B/r).is_file()for r in refs)
    milestones[stage]={'status':'complete','evidence':[str(B/r)for r in refs],'note':'Completed supplied-main contribution only: all13pages reviewed. Matching SI not located or verified; no SI-absence or corpus-completion claim.'}
write(B/'milestones.json',milestones)
c=read(B/'checkpoint.json');c.update(checkpoint_at=now,website_published=True,publication_checkpoint=str(B/'publication-checkpoint.json'),review_scope='supplied_main_only_si_unverified',current_work_items=[{'label':'Dabbousi1997 supplied-main contribution','status':'complete','scope':'Read, extracted, independently audited, integrated and published to the existing MatterSyn Site; SI unverified.'}],next_action='Clear this completed claim and review the oldest remaining eligible local source on the next continuation. Reopen if new or changed SI arrives.');write(B/'checkpoint.json',c)
qa=read(B/'browser-qa.json');qa['remaining_before_release']=[];qa['checks']+=['All25original figure/table/equation/note dialog targets exercised; Figure1 andNote22 additionally inspected in browser.','Final source-link relation text retains specimen limits and no pending canonical audit.'];write(B/'browser-qa.json',qa)
memory=f'''## 2026-09-19 — Dabbousi CdSe/ZnS and CdSe/CdS contribution published

Published public Site version {p['public_live_version']}, dataset 0.8.0, commit {p['source_commit']} at {p['published_at']}. Same MatterSyn Site and audience. Selecting Cd + Se exposes the new CdSe/ZnS material page; Dabbousi CdSe/CdS joins the existing CdSe/CdS hub with equal method cards. CdSe and ZnS/CdS component context remains explicit. Release proof: research-assets/incoming-paper-monitor/reviews/jp971091y/publication-checkpoint.json.

Dabbousi et al. (1997), DOI 10.1021/jp971091y: all13 supplied main pages read and visually inspected; independent source, canonical, apparatus/reference and reader audits completed. Both local copies remain byte-identical (SHA256 dac183303049a3275d4f1874c66ac0ceece9895bc175f7f7e9727ef7c9cd8f9d), generation2 bundle unchanged at final fingerprint. Matching SI not located or verified. This closes only the supplied-main scope.

17 records =2 overgrowth routes +10 supporting procedures +5 contextual observations;120 measurement entries;101 reader items mapped to204 source-audit units;16 original figures,Table1,5 numbered equations,2 unnumbered formula-context crops andNote22 (25 original assets);all40 references/notes inventoried. Six Note22 size/temperature pairs are choices within the general ZnS route, not six independent runs. The CdS branch retains its explicit180°C/approximately1mL/min conditions and equal hexane/butanol storage wording with unknown basis. Source dimensional and model conflicts remain visible; Table1,TEM/WDS, XPS,air exposure and separate solution-SAXS cohorts are not silently joined. No fictitious SAED,Raman,raw curves or measured core/shell coordinates.

All60 operations have source-specific diagrams (35 action types), including addition funnel,N2,TOPO conditioning,particle-state changes and analytical specimen preparation.71 chemical bindings retain17 reused identities and17 new entries (octane conformer plus16 honest identity cards). Pure bulk COD9016056 CdSe reference remains separate from measured structures and training labels. Browser checks covered periodic-table discovery,both material hubs,method switching,temperature pairs,molecules,bulk-reference controls,all25asset dialogs,source search and mobile layout. Full build,scientific/link/hash/privacy checks and5 unchanged review-scope tests passed; bounded independent audits are saved privately.

Dataset totals:201 canonical records =42 synthesis routes +11 controls +38 procedures +10 observations +100 benchmark rows;19 hubs =13 direct synthesis systems +6 component pages;14 source groups. Four formal main-only reviews cover34pages;five matched-main/SI reviews cover74pages separately. Training:42 precursor-selection,58 partial-protocol,6 size-conditioned,0 exact-structure,0 success,95 optical-outcome entries. No new size,exact,success oroptical labels enabled. Corpus totals remain unknown;7,373legacy documents/4,176indexedgroups are historical indexing counts. Latest combined scan at06:31:13Z:12,771copies and8,601provisional reviewunits, not verifiedunique papers.

All five milestones completed. Continue oldest eligible local paper next; keep local-only review and existing5-minute heartbeat. Scientific workflow lessons synchronized to project and installed skill. Deferred chatbot/DFT/theory features remain deferred.

'''
mf=M/'MEMORY.md';old=mf.read_text(encoding='utf-8');heading=memory.splitlines()[0]
if heading not in old:mf.write_text(memory+old,encoding='utf-8')
lesson='''
For shell-growth papers, preserve discrete seed-size/temperature pairs in numbered endnotes and display them beside the relevant operation. A missing single scalar temperature does not mean no temperature was reported when condition alternatives exist. Do not invent interpolation, a seventh setting, or one batch per alternative. Distinguish dropwise addition funnels from syringe pumps, and storage cosolvents from chemical quenching.

Equal nominal coverage or composition does not establish physical identity between TEM/WDS tables, XPS specimens and optical series. Keep general baselines separate from successive exposure states unless the source explicitly joins them; repeated source observations are not independent replicates. Separate model fits, acquisition settings, nominal doses and measured outcomes. Source notes with actual methods or reference constants deserve their own original assets and source-reader links. Finalize pending source-link audit wording only after the corresponding audit; audit page content and scientific linkage separately.

When a PDF renderer corrupts unembedded Symbol glyphs, compare a second installed renderer against the source page and preserve the verified original crop; do not redraw equations from uncertain extracted text. Bulk reference structures may be reused across papers with broadened comparison notes, unchanged coordinates and explicit exclusions from measured structure labels.
'''
skill=M/'skills/mattersyn-paper-to-site/references/incoming-corpus.md';old=skill.read_text(encoding='utf-8')
if 'For shell-growth papers, preserve discrete seed-size/temperature pairs' not in old:skill.write_text(old.rstrip()+'\n'+lesson,encoding='utf-8')
report=Q/'build_queue_report.py';t=report.read_text(encoding='utf-8');t=t.replace('reviews/cm9503137/publication-checkpoint.json','reviews/jp971091y/publication-checkpoint.json').replace('"cm9503137" / "publication-checkpoint.json"','"jp971091y" / "publication-checkpoint.json"').replace("'cm9503137' / 'publication-checkpoint.json'","'jp971091y' / 'publication-checkpoint.json'");report.write_text(t,encoding='utf-8')
print('Saved completed-scope milestones, memory and reusable workflow. Run guarded monitor checkpoint and synchronize installed skill next.')
