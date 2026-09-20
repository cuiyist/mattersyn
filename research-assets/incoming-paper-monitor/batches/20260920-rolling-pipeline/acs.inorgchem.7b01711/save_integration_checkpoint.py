"""Save current independently established gates without claiming publication."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
N=Path(__file__).resolve().parent;MON=N.parents[2];M=N.parents[4];O=N/'site-integration-proposal'
sys.path.insert(0,str(MON));import monitor
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
now=datetime.now(timezone.utc).isoformat()
proofs={k:N/v for k,v in {'source':'source-independent-audit/independent-audit-v2.json','canonical':'canonical-reader-independent-audit/independent-audit-v2.json','molecules':'visuals/molecules-independent-audit/independent-audit-v1.json','apparatus':'visuals/apparatus-independent-audit/independent-audit-v1.json'}.items()}
assert all(read(p)['status']=='passed' for p in proofs.values())
monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='10.1021_acs.inorgchem.7b01711',note='Source, canonical/reader, molecular and 24-scene apparatus audits passed separately. Root prepares bounded metadata and symbolic-product projections for independent audit before shared Site integration.',data={'current_step':'Root website integration; independent promotion and symbolic-product checks','individual_audits':{k:{'path':str(p),'sha256':sha(p)} for k,p in proofs.items()}},milestones={'read':{'status':'complete','evidence':[str(proofs['source']),str(N/'page-coverage.json')],'note':'Complete supplied 10 main and 17 SI pages read and independently source-audited.'},'extract':{'status':'complete','evidence':[str(proofs['canonical']),str(N/'canonical-proposal/v2/package-manifest.json')],'note':'18 canonical records and reader passed separate source-linked review; printed conflicts retained.'},'audit':{'status':'partial','evidence':[str(p) for p in proofs.values()],'note':'Four individual scientific/visual gates passed; integration review remains pending.'}})
ed=read(MON/'public-progress-editorial.json')
for item in ed['current_work']:
 if item['short_label'].startswith('Morrison'):
  item['stage']='Scientific and illustration audits passed; website integration underway'
  item['summary']='All 27 supplied main/SI pages, 18 structured records, 252 reader items, 29 chemical references and 24 operation diagrams passed separate audits. Root is integrating the reviewed data and checking source-linked product illustrations before browser review and publication.'
  item['stages'][-1].update(status='in_progress',detail='Molecular and apparatus audits passed. Website promotion, symbolic-product bindings, actual browser checks and live release remain separate gates.')
  item['gaps'][-1]='Printed amount, condition and caption conflicts are preserved in the reviewed data; no unsupported correction is substituted.'
 if item['short_label'].startswith('Lian'):
  item['stage']='Source extraction revision 2 in independent review; structured records underway'
  item['summary']='Both reviewers have read and visually inspected all 34 supplied main/SI pages. The extraction preserves 57 facts, 134 quantities, nine tables with 891 cells and 53 selected figure crops. Two bounded wording/identifier corrections are retained in revision 2. Canonical records and a reader are being prepared outside the website.'
save(MON/'public-progress-editorial.json',ed)
entry=f'''## 2026-09-20 — Morrison integration and Lian parallel review

Saved {now}. Live science remains dataset 0.25.0 (512 records, 101 routes, 44 material/component hubs, 33 source groups); no Morrison or Lian contribution is published yet. Morrison's separate source, canonical/reader, molecular and apparatus audits passed. Apparatus audit {sha(proofs['apparatus'])} covers all 24 scenes and source conditions. Root promotion freeze c57dc9d7d1de1436df92fedc86ce1ed41a6a08cfba10e648059dbd51a84dc175 and symbolic product-context freeze 6dd95e3b575e66fdea40927174ad73808fdd6656509cf72b3e10ebe67e52ac08 are under independent review before Site import. They preserve 18 records (2 routes, 8 supporting procedures, 8 observations), 822 measurement fields, 30 selected crops, 29 chemical identities and no new training eligibility. Seventeen explicit product contexts use audited symbols only; no precursor coordinates are assigned to nanocrystals.

Lian's all-34-page extraction revision 2 is frozen at 2eca0b5181f3b60156227095e51833af870c7a3ea7e0590c4d3e782931555ae7. The independent reviewer found two bounded fixes: scope nitrogen to TGA rather than XPS and make inventory namespaces distinct. Revision 1 is preserved; final source audit pending. Author prepares unapproved canonical/reader data in parallel, retaining bulk, nanocrystal, film and calculation scopes. Missing cited crystal ZIP/video remain explicit; no downloads or paid processing.

Intake scan 2026-09-20T07:45:18.388180Z found 14,012 document copies (6,639 incoming plus 7,373 legacy), 28 new groups and no changed existing groups; two active claims remain. Provisional scopes are not verified unique papers, materials or recipes. Fixed-cutoff priority remains active, later arrivals separate. Continue the current frozen packages and per-paper audits; do not restart completed work or add a second scheduler.

'''
p=M/'MEMORY.md';p.write_text(entry+p.read_text(encoding='utf8'),encoding='utf8')
save(O/'integration-preparation-checkpoint.json',{'at':now,'status':'pending_integration_and_publication','source_audits':{k:sha(p) for k,p in proofs.items()},'public_science_version':'0.25.0'})
print('Saved truthful source/visual gates, current handoffs and memory; publication still pending.')
