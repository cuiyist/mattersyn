from pathlib import Path
import json,hashlib,sys
E=Path(__file__).resolve().parent;MON=E.parents[2];N=E.parent/'acs.inorgchem.7b01711'
sys.path.insert(0,str(MON));import monitor
read=lambda p:json.loads(p.read_text(encoding='utf8'))
p=MON/'public-progress-editorial.json';d=read(p);m,l=d['current_work']
a=N/'visuals/molecules-independent-audit/independent-audit-v1.json';assert read(a)['status']=='passed'
digest=hashlib.sha256(a.read_bytes()).hexdigest();assert digest=='ba09f9a79ad75b075bf20ab5b68485c838ffd9a8944278f0ce818bd0a2283f6a'
monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='10.1021_acs.inorgchem.7b01711',note='Independent molecular/slot/stock audit passed. Apparatus package is being finalized for a separate independent audit; shared Site integration is pending.',data={'current_step':'Molecular audit passed; apparatus independent review next','molecular_independent_audit':{'path':str(a),'sha256':digest}})
m['stage']='Source, structured-data and molecular audits passed; apparatus review next'
m['summary']='All 27 main-paper and SI pages, 72 facts and 471 table cells passed source review. A separate audit passed 18 structured records and 252 reader items after one preserved classification correction. The chemical illustrations also passed their independent audit. Operation diagrams are being finalized and checked before website integration.'
m['stages'][1]['detail']='Source revision 2 passed; quantity bounds and source conflicts remain explicit.'
m['stages'][2]['detail']='18 records and 252 reader items independently passed in preserved revision 2; no new training eligibility.'
m['stages'][-1]['detail']='29 chemical references, 64 material slots and 10 stock components independently passed. The 24 operation diagrams have a separate audit before integration and publication.'
l['summary']='The local 8-page main paper and 26-page SI have matching titles and authors. The extracting reviewer has read and visually inspected all 34 pages and is organizing the recipes, crystallographic tables and property evidence. Independent source review remains pending.'
l['stages'][0]['detail']='Original main/SI files retained with SHA-256 identities; selected by synthesis and structure evidence.'
l['stages'][1]['detail']='Author reading completed; detailed extraction is in progress. This does not establish independent scientific approval.'
l['gaps']=['The source mentions separate crystal-data and video attachments; they are absent from the current intake pair. Matching local files are being checked.','Synthesis variants, structure availability and property/sample assignments require complete extraction and independent audit.']
d['estimate']['summary']='The two-month target covers the fixed existing collection. Following completed reviews and duplicate reconciliation, 9,511 provisional cutoff scopes remain pending, plus three nested identity cases. Roughly 159 closures per day over 60 days, or 190 per day over 50 production days, would be required. Achievable capacity and the recipe-bearing fraction remain unverified.'
d['estimate']['current_batch']='The original five-paper pilot is 5/5 published, and the later Evans contribution is also published. Morrison has passed source, structured-data and molecular audits; Lian is undergoing source extraction. Later arrivals remain separate.'
for row in d['recent_milestones']:
 if row['at']=='2026-09-20T07:12:53Z':row['text']='Evans complete main/SI contribution published and anonymously verified: dataset 0.25.0, 512 records, 101 routes/variants and 44 material/component collections. All 46 operation controls and the species 9 viewer were checked; the molecular CIF is not a quantum-dot structure. Morrison source and structured-data audits passed; illustrations continue.'
 if 'refilled' in row['text'] and 'Lian2021' in row['text']:row['text']='The completed Evans slot was refilled from the screened fixed collection with Lian (2021), on antimony halides. Morrison illustrations continue in parallel. The latest folder scan found 13,984 document copies; later-arrival papers remain outside the fixed deadline collection.'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Readable public progress updated with the passed Morrison molecular audit.')
