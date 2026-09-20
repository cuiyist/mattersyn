"""Private author checks against actual immutable inputs and rendered-data contract.

This is not the separate scientific or live-browser audit. No Site mutation.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,re

O=Path(__file__).resolve().parent;B=O.parent
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def resolve(o,ptr):
    for t in ptr.strip('/').split('/') if ptr else []:
        t=t.replace('~1','/').replace('~0','~');o=o[int(t)] if isinstance(o,list) else o[t]
    return o
def display(q):
    if q.get('value') is not None:return q['value']
    a,b=q.get('minimum'),q.get('maximum')
    if a is not None and b is not None:return f'{a:g}–{b:g}'
    if a is not None:return ('> ' if q.get('minimum_exclusive') else '≥ ')+f'{a:g}'
    if b is not None:return ('< ' if q.get('maximum_exclusive') else '≤ ')+f'{b:g}'
    return 'Not reported' if q.get('status')=='not_reported' else q.get('raw_text') or q.get('status','Unspecified')

r=read(O/'gu2004.json');cov=read(O/'source-item-coverage.json');cm=read(O/'canonical-measurement-coverage.json');bind=read(O/'reader-bindings-proposal.json')
inv=read(B/'source-inventory.json');src=read(B/'canonical-source-coverage.json');ca=read(B/'canonical-records-audit.json');manifest=read(B/'canonical-record-manifest.json')
recs={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')};crops=read(B/'reader-assets/crop-manifest.json')['assets']
items={i['id']:i for s in r['reader_sections'] for i in s['items']};checks=[]
def check(ok,label,details=None):checks.append({'passed':bool(ok),'check':label,**({'details':details} if details else {})})
check(len(items)==sum(len(s['items']) for s in r['reader_sections']),'Unique reader item IDs')
check([s['title'] for s in r['reader_sections']]==['Precursors','Synthesis protocol','Final structures','Properties','Chemical intuition','Sources and limitations'],'Five academic sections and sources appendix')
check(r['review_scope']=='supplied_main_and_matched_si','Matched main-plus-SI scope')
check({d['role']:d['page_count'] for d in r['documents']}=={'main':2,'si':3},'All five supplied pages included')
for d in r['documents']:
    original=inv['source_documents'][d['role']]
    check(d['sha256']==original['sha256']==sha(original['path']),'Actual unchanged PDF hash: '+d['role'])
    check([p['page'] for p in d['pages']]==list(range(1,d['page_count']+1)) and all(p['text_read'] and p['visual_review'] for p in d['pages']),'Page coverage: '+d['role'])
check(cov['source_inventory_sha256']==sha(B/'source-inventory.json') and cov['source_facts_sha256']==sha(B/'source-facts.json'),'Exact source-input bindings')
check(set(cov['unit_to_reader_items'])=={u['id'] for u in inv['units']} and not cov['unmapped_units'],'All 126 source units mapped')
for uid,targets in cov['unit_to_reader_items'].items():
    check(bool(targets) and all(t in items and uid in items[t]['source_audit_unit_ids'] for t in targets),'Bidirectional unit mapping: '+uid)
check(set(cov['fact_to_reader'])=={f['source_fact_id'] for f in src['facts']},'All 95 source facts mapped')

actual_quantities={};allfacts={};expected_measurements=set();expected_parameters=set();expected_materials=set();expected_operations=set()
for rid,d in recs.items():
    check(cm['draft_sha256'][rid]==sha(B/'canonical-drafts'/f'{rid}.json'),'Frozen record hash: '+rid)
    check(rid in {x for v in r['recipe_inventory'] for x in v['record_ids']},'Recipe inventory link: '+rid)
    for n,m in enumerate(d['measurements']):
        expected_measurements.add(rid+'::'+m['id']);actual_quantities[(rid,f'/measurements/{n}')]=m['value']
    for n,o in enumerate(d['operations']):
        expected_operations.add(rid+'::'+o['id'])
        for k,q in o['parameters'].items():
            expected_parameters.add(rid+'::'+o['id']+'::'+k);actual_quantities[(rid,f'/operations/{n}/parameters/{k}')]=q
    for n,m in enumerate(d['materials']):
        for k,q in m['quantities'].items():
            expected_materials.add(rid+'::'+m['id']+'::'+k);actual_quantities[(rid,f'/materials/{n}/quantities/{k}')]=q
    check(not d.get('stocks'),'No omitted stock quantities: '+rid)
check(set(cm['measurement_to_reader_item'])==expected_measurements,'Every canonical measurement/context entry mapped')
check(set(cm['operation_to_reader_item'])==expected_operations,'Every canonical operation mapped')
check(set(cm['operation_parameter_to_reader_item'])==expected_parameters,'Every operation parameter mapped')
check(set(cm['material_quantity_to_reader_item'])==expected_materials,'Every reagent quantity mapped')
check(len(expected_measurements)==132 and len(expected_operations)==33,'Actual audited canonical counts')
seen_quantities=[]
for iid,i in items.items():
    check(bool(i['title']) and bool(i['text']) and bool(i['evidence']),'Readable evidenced item: '+iid)
    check(i['training_eligible'] is False,'No item training approval: '+iid)
    check(i['sample_scope']['physical_batch_id'] is None,'No invented batch identity: '+iid)
    for l in i['canonical_links']:
        try:resolve(recs[l['record_id']],l['json_pointer']);ok=True
        except (KeyError,IndexError,ValueError):ok=False
        check(ok,'Resolvable canonical item link: '+iid+' / '+l['record_id']+l['json_pointer'])
    for f in i['facts']:
        check(f['id'] not in allfacts,'Unique typed fact: '+f['id']);allfacts[f['id']]=(iid,f)
        key=(f['canonical_record_id'],f['json_pointer']);seen_quantities.append(key)
        check(key in actual_quantities and f['canonical_quantity']==actual_quantities[key],'Exact canonical typed payload: '+f['id'])
        q=f['canonical_quantity']
        check(f['value']==display(q) and f['unit']==q.get('unit') and f['approximate']==q.get('approximate',False) and f['status']==q.get('status'),'Value/bound/unit/status presentation: '+f['id'])
        check(f['training_eligible'] is False,'No typed-fact training approval: '+f['id'])
        if f.get('sample_id'):
            obj=resolve(recs[f['canonical_record_id']],f['json_pointer'])
            check(obj['sample_id']==f['sample_id'],'Canonical sample identity: '+f['id'])
        if q.get('status') in ['inherited','author_derived']:
            check(q['status'] in f['basis'] or bool(f['qualifier']),'Special provenance remains visible: '+f['id'])
    for j in i['sample_scope']['canonical_sample_links']:
        check(resolve(recs[j['record_id']],j['json_pointer'])['sample_id']==j['sample_id'],'Scoped sample pointer: '+iid+' / '+j['record_id']+' / '+j['sample_id'])
check(Counter(seen_quantities)==Counter(actual_quantities.keys()),'Every quantitative field displayed exactly once')
for row in src['facts']:
    m=cov['fact_to_reader'][row['source_fact_id']]
    check(all(i in items for i in m['reader_item_ids']),'Source-fact reader targets: '+row['source_fact_id'])
    for b in m['canonical_bindings']:
        iid,f=allfacts[b['reader_fact_id']]
        check(iid==b['reader_item_id'] and row['source_fact_id'] in f['source_fact_ids'],'Exact source-fact displayed-row binding: '+row['source_fact_id']+' / '+b['reader_fact_id'])
        p=b['pointer']
        check(f['canonical_record_id']==b['record_id'] and (f['json_pointer']==p or f['json_pointer']+'/value'==p),'Source-fact canonical pointer preserved: '+row['source_fact_id'])
for key,iid in cm['operation_to_reader_item'].items():
    rid,oid=key.split('::');n=next(n for n,o in enumerate(recs[rid]['operations']) if o['id']==oid);o=recs[rid]['operations'][n]
    check(items[iid]['operation_context']['environment']==o['environment'],'Exact operation environment retained: '+key)
    check(any(l['record_id']==rid and l['json_pointer']==f'/operations/{n}' for l in items[iid]['canonical_links']),'Direct operation link: '+key)

published={a['id']:a for group in ['figures','schemes','equations','source_notes'] for a in r[group]}
check(set(published)=={a['id'] for a in crops},'All twelve unique original crops in source-level groups')
for a in crops:
    p=published[a['id']]
    check(sha(a['path'])==a['sha256']==p['public_asset_sha256'],'Original crop bytes unchanged: '+a['id'])
    check(p['asset_provenance']['source_sha256']==a['source_sha256'] and p['page']==a['pdf_page'] and p['document_role']==a['source_role'],'Original source/page identity: '+a['id'])
    check(not Path(p['public_asset']).is_absolute() and p['public_asset'].startswith('assets/figures/gu2004/'),'Safe proposed public asset path: '+a['id'])
    check(not p['reviewed'] and not p['reader_render_verified'],'Asset presentation approval still pending: '+a['id'])
    check(any(a['id'] in [x['id'] for x in i['original_assets']] for i in items.values()),'Original asset reachable from reader: '+a['id'])
    for j in p['canonical_sample_links']:
        check(j['sample_id'] in [x['sample_id'] for x in recs[j['record_id']]['products']],'Valid original-asset specimen link: '+a['id']+' / '+j['sample_id'])
check(published['gu2004-figure-s2']['sample_links']==['gu-2004-fept-control'] and published['gu2004-figure-s3']['sample_links']==['gu-2004-fept-control'],'SI controls are not final-product specimen evidence')
check(published['gu2004-figure-s1']['sample_links']==['gu-2004-xrf'],'XRF software table stays in XRF context')
check(r['tables'][0]['public_asset']==published['gu2004-figure-s1']['public_asset'] and r['tables'][0]['row_count']==6,'Embedded XRF table reuses actual original crop')
check('saed-4' in [x['sample_id'] for x in published['gu2004-figure-1']['canonical_sample_links']],'Actual final-product SAED reachable')
check(len([x for x in items if x.startswith('reference-')])==26,'All expanded references and internal SI note retained')
check(len([x for x in r['referenced_methods'] if x['inspection_status']=='not_inspected_in_this_extraction'])==25,'External reference access honestly scoped')
for formula,rids in r['material_evidence_records'].items():
    check(set(rids)<=set(recs),'Material evidence records resolve: '+formula)
for formula,aids in r['material_original_asset_ids'].items():
    check(set(aids)<=set(published),'Material original asset IDs resolve: '+formula)
check([x['record_type'] for x in r['recipe_inventory']].count('literature_protocol')==1,'One true FePt–CdS synthesis route')
check('No CIF' in ' '.join(items['gap-no-exact-atomic-structure']['notes']),'No invented atomic-coordinate download')
for key,need in [('chemical-oleylamine','97%'),('chemical-diol','Technical 90%'),('chemical-topo','Technical 90%'),('chemical-water','Only the CdCl2'),('chemical-hexane','n-hexane')]:
    check(need in items[key]['text']+' '+' '.join(items[key]['notes']),'Source-specific identity caveat: '+key)
preheat=next(f for f in items['hetero-preheat']['facts'] if f.get('canonical_parameter')=='duration')
check(preheat['approximate'] is True and preheat['value']==5,'About five minutes retained')
check(items['xrf-table-rh']['facts'][1]['value']=='Not reported' or any(f['value']=='Not reported' and f['unit']=='mol%' for f in items['xrf-table-rh']['facts']),'Blank Rh amount is not zero')
check(not r['source_review_promoted'] and not r['training_eligible'] and not bind['publication_approved'],'No integration/publication/training promotion')
text=json.dumps(r,ensure_ascii=False)
check(not re.search(r'[A-Z]:[[local path redacted] reader contains no local filesystem paths')
check(bind['reader_sha256']==sha(O/'gu2004.json'),'Binding proposal matches exact reader')
errors=[c for c in checks if not c['passed']]
report={'schema':'mattersyn-private-reader-author-validation/1','source_id':'gu2004','created_at':datetime.now(timezone.utc).isoformat(),
        'status':'passed' if not errors else 'failed','scope':'Author contract, completeness, source/canonical pointer, quantity/sample and original-byte checks. Not independent scientific review, browser QA or publication.',
        'reader_sha256':sha(O/'gu2004.json'),'counts':r['counts'],'check_count':len(checks),'failure_count':len(errors),'failures':errors,
        'input_hashes':{str(p):sha(p) for p in [B/'source-inventory.json',B/'source-facts.json',B/'canonical-source-coverage.json',B/'canonical-record-manifest.json',B/'canonical-records-audit.json',B/'reader-assets/crop-manifest.json']},
        'draft_sha256':cm['draft_sha256'],'checks':checks,'independent_reader_audit_passed':False,'browser_qa_performed':False,'published':False}
(O/'proposal-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(checks),'failures':errors},ensure_ascii=False))
raise SystemExit(bool(errors))
