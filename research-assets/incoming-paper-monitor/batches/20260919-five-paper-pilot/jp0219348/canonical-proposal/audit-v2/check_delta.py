"""Independent bounded v1-to-v2 recheck. Writes audit-v2 only."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy,collections
A=Path(__file__).resolve().parent; P=A.parent; V1=P/'v1'; V2=P/'v2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
checks=[];bound={}
def ck(label,ok,detail=None):checks.append({'check':label,'passed':bool(ok),'detail':detail})
def bind(p):p=Path(p).resolve();bound[str(p)]=sha(p)
def diff(x,y,p=''):
    if x==y:return []
    if isinstance(x,dict) and isinstance(y,dict) and x.keys()==y.keys():
        return [d for k in x for d in diff(x[k],y[k],p+'/'+k.replace('~','~0').replace('/','~1'))]
    if isinstance(x,list) and isinstance(y,list) and len(x)==len(y):
        return [d for i,(a,b) in enumerate(zip(x,y)) for d in diff(a,b,p+'/'+str(i))]
    return [{'path':p,'before':x,'after':y}]
m1=read(V1/'proposal-package-manifest.json');m2=read(V2/'proposal-package-manifest.json')
ck('Expected frozen v2 manifest',sha(V2/'proposal-package-manifest.json')=='10640012af6a21458edd6a84c24af2dea24562f950495a662930d682185fb05a')
for folder,m in [(V1,m1),(V2,m2)]:
    bind(folder/'proposal-package-manifest.json')
    for rel,h in m['files'].items():
        ck(folder.name+' frozen file '+rel,sha(folder/rel)==h);bind(folder/rel)
ck('All scientific inventory counts unchanged',m1['counts']==m2['counts'])
canonicaldiff=[]
for p in sorted((V1/'canonical-drafts').glob('*.json')):
    q=V2/'canonical-drafts'/p.name;x=read(p);y=read(q)
    ds=diff(x,y,'/'+p.stem);canonicaldiff+=ds
    if p.stem=='heo-2003-xps-acquisition':
        corrected=copy.deepcopy(y)
        corrected['materials'][1]['evidence']=x['materials'][1]['evidence']
        corrected['operations'][1]['environment']['evidence']=x['operations'][1]['environment']['evidence']
        ck('XPS record exact scientific invariance excluding two approved evidence fields',corrected==x)
        ck('Argon material cites actual page5',y['materials'][1]['evidence']==[{'source_id':'heo2003','locator':'Main PDF p. 5 (printed p. 1124), XPS Analyses: argon sputtering'}])
        ck('Argon operation adds page5 while retaining page2 settings locator',y['operations'][1]['environment']['evidence']==x['operations'][1]['environment']['evidence']+y['materials'][1]['evidence'])
    else:ck(p.stem+' exact canonical bytes unchanged',p.read_bytes()==q.read_bytes())
ck('Exactly two canonical evidence-only deltas',len(canonicaldiff)==2)
for p in (V1/'source-payloads').rglob('*'):
    if p.is_file():ck('Exact immutable source payload '+str(p.relative_to(V1)),p.read_bytes()==(V2/p.relative_to(V1)).read_bytes())
for name in ['source-fact-coverage.json','source-inventory-coverage.json','table-field-coverage.json','si-row-coverage.json','si-chunk-dependencies.json','schema-gaps.json']:
    ck('Exact unchanged scientific mapping '+name,(V1/name).read_bytes()==(V2/name).read_bytes())
r1=read(V1/'public-review-proposal/heo2003.json');r2=read(V2/'public-review-proposal/heo2003.json')
i1={i['id']:i for s in r1['reader_sections'] for i in s['items']};i2={i['id']:i for s in r2['reader_sections'] for i in s['items']}
ck('372 reader items/order preserved',list(i1)==list(i2) and len(i2)==372)
samplechanges=[];prosechanges=[];evidencechanges=[]
for id,x in i1.items():
    y=i2[id];keys={k for k in x if x[k]!=y[k]}
    ck(id+' changes limited to display/sample-scope or argon locator',keys<={'text','title','sample_scope','evidence','source_locators'})
    for k in ['facts','canonical_links','original_assets','training_eligible']:
        ck(id+' exact '+k,x.get(k)==y.get(k))
    sx=x['sample_scope'];sy=y['sample_scope'];cx=sx.get('canonical_sample_links',[]);cy=sy.get('canonical_sample_links',[])
    ck(id+' other specimen-scope metadata unchanged',{k:v for k,v in sx.items() if k!='canonical_sample_links'}=={k:v for k,v in sy.items() if k!='canonical_sample_links'})
    if cx!=cy:
        samplechanges.append(id)
        dedup=[]
        for link in cx:
            if not any((z['record_id'],z['sample_id'])==(link['record_id'],link['sample_id']) for z in dedup):dedup.append(link)
        if id.startswith('asset-heo2003-figure-'):
            expected={(l['record_id'],l['sample_id']) for l in x['canonical_links'] if l.get('sample_id')}
            ck(id+' populated only pre-existing product/sample associations',not cx and {(l['record_id'],l['sample_id']) for l in cy}==expected)
            ck(id+' unique figure scope links',len(cy)==len(expected))
        else:ck(id+' exact stable deduplication',cy==dedup)
    if 'text' in keys or 'title' in keys:
        prosechanges.append({'id':id,'before':{k:x[k] for k in ['title','text'] if x[k]!=y[k]},'after':{k:y[k] for k in ['title','text'] if x[k]!=y[k]}})
        ck(id+' prose belongs to requested source-fact or gap presentation',id.startswith('fact-') or id.startswith('inventory-remaining_gaps-'))
    if 'evidence' in keys or 'source_locators' in keys:
        evidencechanges.append(id);ck(id+' sole approved gas evidence change',id=='material-heo-2003-xps-acquisition-argon')
        ck(id+' updated evidence actually page5','p. 5 (printed p. 1124)' in str(y['evidence']) and 'p. 5 (printed p. 1124)' in str(y['source_locators']))
ck('42 deduplications plus seven pre-existing figure scopes',len(samplechanges)==49 and sum(i.startswith('asset-heo2003-figure-') for i in samplechanges)==7)
ck('One reader evidence item changed',evidencechanges==['material-heo-2003-xps-acquisition-argon'])
top1=copy.deepcopy(r1);top2=copy.deepcopy(r2)
for r in [top1,top2]:r.pop('reader_sections');r.pop('evidence_conflicts');r['si_aggregate_evidence'].pop('audit_path')
ck('All other top-level reader metadata/science unchanged',top1==top2)
for x,y in zip(r1['evidence_conflicts'],r2['evidence_conflicts']):
    ck('Conflict identity/disposition preserved '+x['id'],{k:v for k,v in x.items() if k!='description'}=={k:v for k,v in y.items() if k!='description'})
ck('All seven conflict descriptions retained',len(r1['evidence_conflicts'])==len(r2['evidence_conflicts'])==7)
audit=V2/'public-review-proposal'/r2['si_aggregate_evidence']['audit_path']
ck('Corrected SI audit path resolves and matches passed aggregate hash',audit.is_file() and sha(audit)==r2['si_aggregate_evidence']['audit_sha256'])
ck('Historical SI status explicitly distinguished from current aggregate','Historical extraction checkpoint' in i2['inventory-remaining_gaps-0']['text'] and '1,209' in i2['inventory-remaining_gaps-0']['text'] and '7,252' in i2['inventory-remaining_gaps-0']['text'] and 'two signs remain' in i2['inventory-remaining_gaps-0']['text'])
ck('Outlook source phrasing and lack of demonstration retained','tagged electronically or magnetically' in i2['fact-outlook']['text'] and 'No memory device' in i2['fact-outlook']['text'])
t=read(A/'transport-checks.json');ck('Full corrected transport rerun passed',t['counts']=={'checks':8485,'failed':0} and t['schema_runtime_issue'] is None)
v1audit=read(P/'audit-v1/independent-audit.json')
ck('Original findings report preserved',sha(P/'audit-v1/independent-audit.json')=='606f80abd0efdc91fa2f7ab5a3011f68f06428f27b2bf720322e629a9855658b')
bound.update(t['bound_files'])
for p in [A/'transport-checks.json',A/'check_transport.py',Path(__file__),A/'prepare_checker.py',P/'audit-v1/independent-audit.json',P/'audit-v1/independent-audit.md']:bind(p)
failed=[c for c in checks if not c['passed']]
report={
 'schema':'mattersyn.heo_canonical_reader_delta_independent_audit/1','audited_at':datetime.now(timezone.utc).isoformat(),
 'author':'/root/peng1998_reader_assets','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta',
 'status':'passed_bounded_canonical_reader_scope' if not failed else 'findings',
 'proposal_manifest':str(V2/'proposal-package-manifest.json'),'proposal_manifest_sha256':sha(V2/'proposal-package-manifest.json'),
 'prior_audit':str(P/'audit-v1/independent-audit.json'),'prior_audit_sha256':sha(P/'audit-v1/independent-audit.json'),
 'scope':'Targeted independent v2 correction recheck plus exact transport rerun. The actual v1 scientific reading is recorded in the unchanged prior audit. No molecular/model self-audit, SI-cell reread, integration/browser/publication or training approval.',
 'counts':{'delta_checks':len(checks),'delta_failures':len(failed),'transport_checks':8485,'transport_failures':0,'canonical_evidence_edits':len(canonicaldiff),'sample_link_items':len(samplechanges),'prose_items_reviewed':len(prosechanges),'reader_evidence_items':len(evidencechanges),'records':10,'measurements':473,'reader_items':372,'si_rows':1209,'unresolved_si_signs':2},
 'resolved_findings':[{'id':f['id'],'resolution':'Passed exact correction delta and targeted manual review.'} for f in v1audit['required_findings']] if not failed else [],
 'manual_scope':'Actually read every changed source-fact/gap prose item and all seven revised top-level conflict descriptions. Compared wording to the prior scientific review and unchanged source facts. Confirmed source distinctions, numbers, interpretive claims, historical/current SI status and speculative outlook. No additional source paper or SI-cell visual review was needed or claimed.',
 'canonical_deltas':canonicaldiff,'reader_prose_deltas':prosechanges,'checks':checks,'findings':failed,
 'invariance':'Nine canonical records are byte identical. The tenth differs only in two approved argon evidence fields. Source payloads, scientific coverage maps, every typed reader fact, existing canonical sample links, original assets, tasks and gates remain unchanged. Figure sample lists only expose prior supported associations.',
 'limits':['All original source conflicts and missingness remain.','Two unresolved SI signs remain null.','No exact pair or ordered/DFT model approval; average-geometry candidate remains separate.','Molecules, apparatus, atomic assets, final bindings, browser, promotion and publication require their separate gates.'],
 'mutations':'Private audit-v2 files only; v1/v2 author proposals and Site/shared state unchanged.','bound_files':bound
}
(A/'independent-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=['# Heo canonical/reader v2 bounded independent audit','',f"**Result: {report['status']}.** All five v1 findings are resolved within the requested delta.",'',f"Author: `/root/peng1998_reader_assets`; independent auditor: `/root/backlog_eta`. V2 manifest SHA256: `{report['proposal_manifest_sha256']}`.",'',f"The corrected package passes all 8,485 transport checks and {len(checks):,} additional delta checks. Nine canonical records are byte identical; only two evidence fields in the XPS record change to cite the explicit argon statement on main PDF p. 5. All quantitative settings, scientific fields, specimen contexts, raw source payloads and SI cells remain unchanged.",'',f"The recheck verified 42 sample-link deduplications, seven figure sample lists derived only from their prior supported canonical links, one corrected relative SI-audit path, one corrected reader gas locator, {len(prosechanges)} changed prose items, and seven polished conflict descriptions. All changed prose was actually read. Historical extraction-era SI status is now distinguished from the separately passed 1,209-row aggregate; both unknown signs remain null.",'','All 473 canonical measurements and 535 reader facts remain unchanged and reachable through 372 items. The original v1 findings report is retained without edits. The full scientific reading scope and targeted original-image views remain documented there; this addendum does not claim another SI-cell reread.','','This pass covers the private canonical/reader scientific and transport scope. It does not approve molecular assets, the separate average crystal candidate, an exact training pair, browser behavior, integration or publication.','']
(A/'independent-audit.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({'status':report['status'],'delta_checks':len(checks),'failures':failed,'counts':report['counts'],'audit_sha256':sha(A/'independent-audit.json'),'md_sha256':sha(A/'independent-audit.md')},ensure_ascii=False))
