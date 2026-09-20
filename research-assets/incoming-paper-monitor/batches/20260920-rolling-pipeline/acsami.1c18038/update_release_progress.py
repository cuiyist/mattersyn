from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,subprocess
L=Path(__file__).resolve().parent;MON=L.parents[2];M=L.parents[4];G=L.parent/'ja212032q';O=L/'site-integration-proposal'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
part=read(MON/'deadline-20260920/lian-release-scope-20260920T0938Z.json');n=part['counts']['included_pending_scopes'];ed=read(MON/'public-progress-editorial.json')
for x in ed['current_work']:
 if x['short_label']=='Ghosh et al. (2012)':
  x.update(stage='Source audit passed; revised data and illustrations under independent review',summary='The complete 10-page paper and nine-page SI have passed independent source review, including all 272 table cells and 36 selected crops. The 21-record dataset and 325-item reader are undergoing final review. A correction keeps comparison specimen sets separate from individual reaction batches. Molecular and operation illustrations retain their own audits.',stages=[{'label':'Complete main/SI reading and independent source audit','status':'complete','detail':'Source revision 2 preserves 71 facts, 194 quantities and all supplied figures and tables.'},{'label':'Independent structured-data and reader audit','status':'in_progress','detail':'Revision 2 corrects grouped specimen typing and labels; all source values and operations are preserved.'},{'label':'Molecular and apparatus audits','status':'in_progress','detail':'25 chemical identities cover 88 material slots and three stocks. The 33 operation scenes are checked separately.'},{'label':'Website publication','status':'pending','detail':'Release follows all individual review and browser checks.'}])
ed['recent_milestones'][0]['text']='Lian antimony-halide contribution published and anonymously verified: three synthesis routes or variants, 21 illustrated operations, 53 selected source crops and two qualified partial bulk-crystal views. Dataset 0.27.0 contains 546 records, 106 routes and 46 material/component pages.'
ed['estimate']['summary']=f'The two-month target covers the fixed existing collection. {n:,} provisional cutoff scopes remain pending, plus three nested identity cases. Roughly 159 closures per day over 60 days, or 190 per day over 50 production days, would be required. Achievable capacity and the recipe-bearing fraction remain unverified.'
save(MON/'public-progress-editorial.json',ed)
sys.path.insert(0,str(MON));import monitor
manifest=G/'canonical-proposal/v2/package-manifest.json'
monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='10.1021_ja212032q',note='Source revision2 passed; canonical/reader revision2 preserves all scientific values while correcting grouped specimen-state classification and labels. Final independent delta review and visual audits remain separate.',data={'current_step':'Canonical revision2 in final independent review; molecular and33operation visuals in parallel audit/preparation','canonical_proposal':{'path':str(manifest),'sha256':sha(manifest)}})
for name in ['build_queue_report.py','build_public_progress.py']:subprocess.run([sys.executable,str(MON/name)],check=True)
note=f'''## 2026-09-20 — Current queue and verified Lian release

Saved {datetime.now(timezone.utc).isoformat()}. Lian is publicly verified at science commit e9ce1ecd12b6647ac92b8cceb39832951b4349a0 (Pages built 09:35:45 UTC). Dataset 0.27.0: 546 structured records, 106 synthesis routes/variants, 46 material/component hubs, 35 cited source groups and 30 formal readers. Both public README reference lists contain 35 sources. All 63 anonymous endpoints match. A separate final status/progress release is now being prepared; preserve the scientific release identity.

The fresh intake scan at 09:36:37 UTC found 14,082 document copies, 31 new groups and no changed existing groups. The immutable-cutoff partition has 9,534 provisional scopes: 9,508 pending and 26 terminal, with three nested identity cases held. There are 249 later-arrival groups represented by 251 later files; keep those separate. These are worklist scopes and copies, not verified unique papers or recipes. Screening still has 238 manual format/text cases; full-corpus review is not complete.

Ghosh source revision 2 independently passed. Canonical/reader revision 2 is frozen at {sha(manifest)}, preserving all scientific values and operations while correcting five sample-set state kinds, one FTIR specimen name and four reader labels. Norberg independently rechecks; Backlog prepares an overlay-only molecular rebind and later independently audits Norberg apparatus. Peng independently audits molecules. Do not integrate Ghosh until all source/data/visual gates pass. The molecular v1 freeze is a0a288171e559c3ebf2664cda6d312e1a9b0992888dc4435dd1cd51e860c3391; use its eventual v2 canonical rebind overlay, not stale input hashes.

The existing heartbeat resumes this latest memory. Continue evidence-priority screening, separate per-paper audit histories and batch publication. No paper downloads, paid API runs or duplicate automation. Original PDFs/SI, raw full text and complete-page images remain local. Root temporary preview server 5193 remains for final checks and should be stopped after delivery. Source/data/illustration gates are distinct from publication flags and training eligibility.
'''
p=M/'MEMORY.md';p.write_text(note+'\n'+p.read_text(encoding='utf8'),encoding='utf8');print('Saved precise queue, cutoff partition and public progress.')
