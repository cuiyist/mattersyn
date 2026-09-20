"""Save independently passed visual work and the next frozen source handoff."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
R=Path(__file__).resolve().parents[2];M=R.parents[1]
sys.path.insert(0,str(R));import monitor
E=Path(__file__).resolve().parent/'ja103805s';N=E.parent/'acs.inorgchem.7b01711'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
now=datetime.now(timezone.utc).isoformat();ap=E/'visuals/apparatus-independent-audit/independent-audit-v1.json';nf=N/'package-freeze.json'
assert read(ap)['status']=='passed' and sha(nf)=='ca9640453f84ee64649ea34f723b717d8e418b3454936faf8e065280268f2594'
monitor.checkpoint(R/'ledger.json','mattersyn-primary',group_id='10.1021_ja103805s',note='Independent apparatus audit passed all46scenes/153conditions; source/canonical/molecule/apparatus gates passed. Shared Site integration and its separate audit/browser/publication gates remain.',data={'current_step':'Ready for shared Site integration and independent integration checks','apparatus_independent_audit':{'path':str(ap),'sha256':sha(ap)}})
monitor.checkpoint(R/'ledger.json','mattersyn-primary',group_id='10.1021_acs.inorgchem.7b01711',note='Complete author source extraction frozen; separate independent scientific audit active. Canonical/reader drafting proceeds without approval claims.',data={'current_step':'Independent source audit; canonical/reader author drafting in parallel','source_freeze':{'path':str(nf),'sha256':sha(nf)}},milestones={'read':{'status':'complete','evidence':[str(nf),str(N/'source-inventory.json'),str(N/'page-coverage.json')],'note':'All10main+17SI pages author-read/viewed; independent verification remains its own gate.'},'extract':{'status':'partial','evidence':[str(nf)],'note':'Author source extraction complete:71facts,29materials,24ops,471tablecells,30selectedcrops; canonical/reader drafts and independent audits pending.'}})
d=read(R/'public-progress-editorial.json');e=d['current_work'][0];n=d['current_work'][1]
e['stage']='Source, structured-data, molecular and apparatus audits passed; website integration next'
e['summary']='All 24 main/SI pages and the molecular CIF were independently checked. The 32 structured records and reader passed a separate audit after preserving the distinction between distillation residue and collected fractions. Fifty chemical references and all 46 operation-specific diagrams also passed their individual audits. Shared website integration and public browser checks remain.'
e['stages'][-1]={'label':'Apparatus illustration audit','status':'complete','detail':'46 scenes and 153 condition rows independently checked; explanatory geometry remains qualified'}
e['stages'].append({'label':'Integrated website and publication','status':'pending','detail':'Reader, routes, models and controls must pass integrated checks before publication'})
n['stage']='Full source extraction complete; independent audit and reader drafting in parallel'
n['summary']='The extracting reviewer read and visually inspected all 10 main-paper and 17 SI pages. The frozen extraction contains 29 materials, 24 operations, 471 table cells and 30 selected figure/table crops. A distinct reviewer is checking the original sources while structured records and the reader are drafted.'
n['stages'][1]['detail']='Frozen source extraction; separate scientific audit underway. Ten source discrepancies and ten gaps remain explicit.'
d['recent_milestones'].insert(0,{'at':now,'text':'Evans apparatus audit passed all 46 scenes and 153 conditions. Morrison complete source extraction was frozen after all 27 main/SI pages and 30 selected crops were inspected; independent scientific review remains active. No new scientific records published by this progress update.'})
save(R/'public-progress-editorial.json',d)
entry=f'''## 2026-09-20 — Evans visual audits passed; Morrison frozen for independent review

Saved {now}. Evans apparatus independent audit PASSED ({sha(ap)}), bound to root freeze474a21a8b43326cc94058063c040019aa68810567a5c2592186f997c85e41025. It checked all46scenes/153conditions, reopened10sourcepages and passed1200binding/module checks. Evans source, canonical/reader v3, molecular revision2 and apparatus gates have passed. Next: root prepares preserved promotion/public-projection overlays, integrates into shared Site, then obtains distinct integration audit and actual browser checks before publication. No Evans scientific record is live yet.

Morrison source freeze {sha(nf)} contains all10main+17SIpages,71facts,29materials,5stocks,10procedure/branch families/24operations,8tables/471cells,30selectedcrops,175sourceunits and52references. All1270authorchecks passed. Ten printed discrepancies/qualifications and ten gaps are retained. Peng independently audits sources; backlog drafts canonical/reader proposals outside Site with unapproved status. No new downloads or paid calls. Continue the current frozen handoffs rather than restarting extraction.

Published science stays dataset0.24.0/480records/98routes/44hubs. The public progress dashboard is being updated as a separate release; final exact commit verification is recorded below when complete. Source exclusions and the single five-minute heartbeat remain in effect.

'''
p=M/'MEMORY.md';p.write_text(entry+p.read_text(encoding='utf8'),encoding='utf8')
save(E.parent/'ready-for-integration-checkpoint.json',{'at':now,'evans_apparatus_audit':sha(ap),'morrison_source_freeze':sha(nf),'science_publication_changed':False,'shared_site_integration_pending':True})
print(json.dumps({'apparatus':'passed','morrison':'source frozen; independent audit active','scientific_records_published_this_checkpoint':0}))
