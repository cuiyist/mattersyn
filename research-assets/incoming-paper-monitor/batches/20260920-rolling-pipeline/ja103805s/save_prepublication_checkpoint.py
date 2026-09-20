from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
E=Path(__file__).resolve().parent;MON=E.parents[2];M=E.parents[4];N=E.parent/'acs.inorgchem.7b01711';O=E/'site-integration-proposal'
sys.path.insert(0,str(MON));import monitor
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
ia=E/'site-integration-independent-audit/integration-code-audit.json';ba=O/'browser-validation.json';sa=N/'source-independent-audit/independent-audit.json'
assert all(read(p)['status']=='passed' for p in [ia,ba,sa]);assert sha(ia)=='5ac0c755534466db683eb1bc459b17eb5773d9e9be9d076e872dd8f380c3eb4b'
for p in [MON/'latest-publication.json',M/'research-assets/github-public-delivery-verification.json']:
 dest=O/('prior-'+p.name)
 if not dest.exists():save(dest,read(p))
now=datetime.now(timezone.utc).isoformat()
milestones={k:{'status':'complete','evidence':v,'note':note} for k,v,note in [
 ('read',[str(E/'source-scientific-audit.json')],'Complete supplied3main+21SIpages and molecularspecies9CIF independently reviewed.'),
 ('extract',[str(E/'proposal-freeze-v3.json'),str(E/'proposal-independent-audit/independent-audit-v3.json')],'32source records/reader passed separate canonical review; controls and source gaps retained.'),
 ('audit',[str(ia),str(E/'proposal-independent-audit/independent-audit-v3.json')],'Source, canonical, molecular, apparatus, promotion and integration audits passed separately.'),
 ('integrate',[str(ia),str(ba),str(O/'build-check-output.json')],'Actual integrated browser exercised46stages and species9model. All480previous scientific records unchanged; new32records have no training promotion.') ]}
monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='10.1021_ja103805s',note='All individual scientific/integration/browser gates passed; deployment and anonymous verification are pending.',data={'current_step':'Publishing audited Evans contribution; awaiting anonymous release verification','integration_audit':{'path':str(ia),'sha256':sha(ia)},'browser_validation':{'path':str(ba),'sha256':sha(ba)}},milestones=milestones)
monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='10.1021_acs.inorgchem.7b01711',note='Source revision2 independently passed. Canonical audit identified one analysis-data classification correction; author preserves v1. Molecular illustrations and apparatus proceed independently outside Site.',data={'current_step':'Canonical revision review; molecular and apparatus authoring in parallel','source_scientific_audit':{'path':str(sa),'sha256':sha(sa)},'effective_source_freeze':{'path':str(N/'package-freeze.json'),'sha256':sha(N/'package-freeze.json')}},milestones={'read':{'status':'complete','evidence':[str(sa),str(N/'page-coverage.json')],'note':'All10main+17SIpages read and source-audited with revisions retained.'},'extract':{'status':'partial','evidence':[str(N/'canonical-proposal/v1/package-manifest.json')],'note':'18records drafted; one canonical output-kind correction pending independent approval.'}})
ed=read(MON/'public-progress-editorial.json');ev=ed['current_work'][0];mo=ed['current_work'][1]
ev.update(stage='Integrated website passed; public deployment in progress',summary='The32source records,50chemical references,46operation diagrams and qualified molecular9viewer passed their separate audits. Actual browser controls and source figures were checked. The completed contribution is being deployed; public access and exact release bytes are checked before closure.')
ev['stages'][-1].update(status='in_progress',detail='Integration audit and actual browser checks passed; anonymous public release verification pending.')
mo.update(stage='Source audit passed; canonical correction and illustrations in parallel',summary='All27main/SIpages were independently checked. The revised extraction contains72facts and471tablecells. A separate canonical/reader audit covers18records and252readeritems; one output classification is being corrected with the original preserved. Molecular references and24operation illustrations proceed separately.')
mo['stages'][1].update(status='complete',detail='Source revision2 passed; bounded quantities and source conflicts preserved.')
mo['stages'].insert(2,{'label':'Canonical records and reader audit','status':'in_progress','detail':'18records,252readeritems; analysis-data output classification correction in progress.'})
mo['stages'][-1].update(status='in_progress',detail='Chemical and apparatus proposals under separate authoring; no website or training approval yet.')
save(MON/'public-progress-editorial.json',ed)
entry=f'''## 2026-09-20 — Evans integrated and audited; release verification pending

Saved {now}. Local dataset0.25.0 contains512records/101routes/44material hubs/33sourcegroups/28formalreaders. The current verified public science remains0.24.0 until the new release passes anonymous verification. Evans adds3routes,13supportingprocedures and16analyticalobservations; these32records are not32experiments. Separate integration audit{sha(ia)} passed42,511checks. Root actualbrowser exercisedall46stages, species9rotation/zoom/highlighting, filteredfigures and390pxlayout. Existing480canonicalfiles and trainingeligibility stayunchanged; exactpairs0.

Evans promotionv2 freeze1a512c3089df906dbf499761ad79ca88ee8872bcd744c30350990b75e02cbebd and productadapter47fa08d95c2a553768bd190966ab9cf5a15201d5bdf1bc1faf4e2f037c3d5e33 are independently passed. Molecularspecies9coordinates remain two explicitly qualified molecular contexts only. Reader maps distinguish3127structural,193property and367additional sourcefields without losing data;13stock objects display readable fields. Reusable navigation templates retain Reviewprogress. Finalpaths underja103805s/site-integration-proposal andsite-integration-independent-audit. No sourcebinaries/rawtext/fullpages are public.

Morrison source revision2 independently PASSED ({sha(sa)}),72facts/185quantities/176units/471tablecells. Canonicalv1 18records/24ops/822measurementcontexts and252readeritems; independentreview requests one output-kind correction toanalysis_data. Author preservesv1; molecule+apparatus work continues separately. Do not count Morrison as published. No paidAPI, paperdownloads or additional scheduler. Resume the current frozen packages, not extraction fromscratch.

'''
p=M/'MEMORY.md';p.write_text(entry+p.read_text(encoding='utf8'),encoding='utf8')
save(O/'prepublication-checkpoint.json',{'at':now,'integration_audit_sha256':sha(ia),'browser_validation_sha256':sha(ba),'candidate_dataset':'0.25.0','public_verification_pending':True,'source_exclusions_retained':True})
print('Saved exact integrated handoffs, audit gates and pending publication state.')
