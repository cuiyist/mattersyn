"""Private Nagasaki reader author checks; reads frozen source/canonical inputs.

No scientific approval, browser QA, Site import, model binding or publication is
granted by this validator. Checks the actual generated proposal, not its builder.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib, json, re

O=Path(__file__).resolve().parent; B=O.parent; SID='nagasaki2004'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ptr(o,p):
    for t in p.strip('/').split('/') if p else []:
        t=t.replace('~1','/').replace('~0','~'); o=o[int(t)] if isinstance(o,list) else o[t]
    return o
def display(q):
    if q.get('value') is not None: return q['value']
    a,b=q.get('minimum'),q.get('maximum')
    if a is not None and b is not None: return f'{a:g}–{b:g}'
    if a is not None: return ('> ' if q.get('minimum_exclusive') else '≥ ')+f'{a:g}'
    if b is not None: return ('< ' if q.get('maximum_exclusive') else '≤ ')+f'{b:g}'
    return 'Not reported' if q.get('status')=='not_reported' else q.get('raw_text') or q.get('status','Not reported')

r=read(O/f'{SID}.json'); cov=read(O/'source-item-coverage.json'); cm=read(O/'canonical-measurement-coverage.json')
bind=read(O/'reader-bindings-proposal.json'); inputs=read(O/'reader-authoring-inputs.json')
I=read(B/'source-inventory.json'); F=read(B/'source-facts.json'); C=read(B/'canonical-source-coverage.json')
M=read(B/'canonical-record-manifest.json'); A=read(B/'canonical-records-audit.json'); SA=read(B/'source-scientific-audit.json')
R={x['record_id']:read(x['path']) for x in M['records']}
items={i['id']:i for s in r['reader_sections'] for i in s['items']}; checks=[]
def ck(ok,label,details=None): checks.append({'passed':bool(ok),'check':label,**({'details':details} if details is not None else {})})
def safe_resolve(rid,p):
    try: ptr(R[rid],p); return True
    except (KeyError,IndexError,ValueError,TypeError): return False

ck(A['status']=='passed_with_preserved_source_ambiguities' and SA['status']=='passed_with_preserved_source_ambiguities','Separate source and canonical audits passed with original ambiguities preserved')
for p,h in inputs['input_hashes'].items(): ck(sha(p)==h,'Unchanged frozen input: '+p)
for x in M['records']:
    rid=x['record_id']; h=sha(x['path'])
    ck(h==x['sha256']==cm['draft_sha256'][rid]==A['record_hashes'][rid],'Exact separately audited canonical hash: '+rid)
    ck(R[rid]['quality']['review_status']=='imported_unreviewed' and R[rid]['quality']['requested_tasks']==[],'Canonical promotion and tasks remain unchanged: '+rid)
ck(len(items)==sum(len(s['items']) for s in r['reader_sections']),'Reader IDs unique')
ck([s['title'] for s in r['reader_sections']]==['Precursors','Synthesis protocol','Final structures','Properties','Chemical intuition','Sources and limitations'],'Five academic sections plus source appendix')
ck(r['paper_id']==SID and r['source_group']==SID and r['doi']==F['doi'] and r['title']==F['title'],'Correct article identity')
ck(r['review_scope']=='supplied_main_and_matched_si','Matched main and SI scope')
ck({d['role']:d['page_count'] for d in r['documents']}=={'main':5,'si':3},'All five main and three SI pages represented')
for d in r['documents']:
    original=next(x for x in I['documents'] if x['role']==d['role'])
    ck(d['sha256']==original['source_sha256']==sha(original['original_path']),'Actual PDF identity: '+d['role'])
    ck([p['page'] for p in d['pages']]==list(range(1,d['page_count']+1)) and all(p['text_read'] and p['visual_review'] for p in d['pages']),'Supplied page coverage: '+d['role'])
ck(inputs['reader_original_text_pages']=={'main':[1,2,3,4,5],'si':[1]} and inputs['reader_visual_pages']=={'main':[1,2,3,4,5],'si':[1,2,3]},'Actual reader reinspection distinguishes text and image-only SI pages')
for key,name in [('source_inventory_sha256','source-inventory.json'),('source_facts_sha256','source-facts.json'),('canonical_coverage_sha256','canonical-source-coverage.json')]:
    ck(cov[key]==sha(B/name),'Bound coverage input: '+name)
ck(set(cov['unit_to_reader_items'])=={u['id'] for u in I['source_units']} and not cov['unmapped_units'],'All 32 source units mapped')
for uid,targets in cov['unit_to_reader_items'].items():
    ck(bool(targets) and all(t in items and uid in items[t]['source_audit_unit_ids'] for t in targets),'Bidirectional source-unit coverage: '+uid)
ck(set(cov['fact_to_reader'])=={f['id'] for f in F['facts']},'All 49 source facts represented')

quantities={}; measurements={}; operations={}; parameters={}; materials={}; stocks={}; slots={}; samples={}
def qadd(rid,p,q,kind,key):
    ck((rid,p) not in quantities,'Unique canonical quantity pointer: '+rid+p); quantities[(rid,p)]=q
    kind[key]=(rid,p)
for rid,d in R.items():
    ck(rid in {x for v in r['recipe_inventory'] for x in v['record_ids']},'Record inventory membership: '+rid)
    for n,m in enumerate(d['measurements']): qadd(rid,f'/measurements/{n}/value',m['value'],measurements,rid+'::'+m['id'])
    for n,o in enumerate(d['operations']):
        operations[rid+'::'+o['id']]=(rid,f'/operations/{n}')
        for k,q in o['parameters'].items(): qadd(rid,f'/operations/{n}/parameters/{k}',q,parameters,rid+'::'+o['id']+'::'+k)
        for j,option in enumerate(o.get('condition_options',[])):
            for k,q in option.get('parameters',{}).items(): qadd(rid,f'/operations/{n}/condition_options/{j}/parameters/{k}',q,parameters,rid+'::'+o['id']+'::option'+str(j)+'::'+k)
    for n,m in enumerate(d['materials']):
        slots[rid+'::'+m['id']]=(rid,f'/materials/{n}')
        for k,q in m.get('quantities',{}).items(): qadd(rid,f'/materials/{n}/quantities/{k}',q,materials,rid+'::'+m['id']+'::'+k)
    for n,s in enumerate(d.get('stocks',[])):
        for k,q in s.get('concentrations',{}).items(): qadd(rid,f'/stocks/{n}/concentrations/{k}',q,stocks,rid+'::'+s['id']+'::'+k)
        for j,c in enumerate(s['components']):
            for k,q in c.get('quantities',{}).items(): qadd(rid,f'/stocks/{n}/components/{j}/quantities/{k}',q,stocks,rid+'::'+s['id']+'::'+str(j)+'::'+k)
    for n,s in enumerate(d['products']): samples[rid+'::'+s['sample_id']]=(rid,f'/products/{n}')
for field,expected in [('measurement_to_reader_item',measurements),('operation_to_reader_item',operations),('operation_parameter_to_reader_item',parameters),('material_quantity_to_reader_item',materials),('stock_quantity_to_reader_item',stocks),('canonical_material_slots',slots),('canonical_sample_contexts',samples)]:
    ck(set(cm[field])==set(expected),'Complete actual canonical universe: '+field)
ck((len(R),len(measurements),len(operations),len(parameters),len(materials),len(stocks),len(slots),len(samples))==(16,122,36,54,48,4,61,28),'Frozen canonical coverage counts')
allfacts={}; seen=[]
for iid,i in items.items():
    ck(bool(i['title']) and bool(i['text']) and bool(i['evidence']),'Readable source-linked item: '+iid)
    ck(i['training_eligible'] is False and i['sample_scope']['physical_batch_id'] is None,'No new task eligibility or batch identity: '+iid)
    for e in i['evidence']:
        ck(e['source_id']==SID and e['document_role'] in ['main','si'] and e['pdf_page'] in range(1,6 if e['document_role']=='main' else 4) and bool(e['locator']),'Source locator resolves to supplied page: '+iid)
    for l in i['canonical_links']: ck(safe_resolve(l['record_id'],l['json_pointer']),'Canonical item pointer: '+iid+' / '+l['record_id']+l['json_pointer'])
    for f in i['facts']:
        ck(f['id'] not in allfacts,'Typed fact ID unique: '+f['id']); allfacts[f['id']]=(iid,f)
        key=(f['canonical_record_id'],f['json_pointer']); seen.append(key)
        ck(key in quantities and f['canonical_quantity']==quantities.get(key),'Exact immutable typed payload: '+f['id'])
        q=f['canonical_quantity']
        ck(f['value']==display(q) and f['unit']==q.get('unit') and f['status']==q.get('status') and f['approximate']==q.get('approximate',False),'Exact value, bounds, unit, status and approximation: '+f['id'])
        ck(f['training_eligible'] is False,'Typed fact not independently training approved: '+f['id'])
        for v in [q.get('basis'),q.get('qualifier'),q.get('note')]:
            if v: ck(str(v) in f['qualifier'],'Canonical qualification visible: '+f['id'])
        if f.get('canonical_measurement_id'):
            m=ptr(R[f['canonical_record_id']],f['json_pointer'].removesuffix('/value'))
            ck(m['id']==f['canonical_measurement_id'] and m['sample_id']==f['sample_id'] and m['technique']==f['basis'],'Exact measurement/specimen/technique association: '+f['id'])
        for e in q.get('evidence',[]):
            if 'locator' in e:
                ck(any(v['locator']==e['locator'] for v in f['evidence']),'Typed fact retains exact source locator: '+f['id'])
            else:
                role='si' if e['source_id'].endswith('-si') else 'main'
                ck(any(v['document_role']==role and v['pdf_page']==e['pdf_page'] for v in f['evidence']),'Typed fact retains exact source page: '+f['id'])
    for s in i['sample_scope']['canonical_sample_links']:
        ck(safe_resolve(s['record_id'],s['json_pointer']) and ptr(R[s['record_id']],s['json_pointer'])['sample_id']==s['sample_id'],'Sample link resolves in its own record: '+iid+' / '+s['sample_id'])
ck(Counter(seen)==Counter(quantities.keys()),'All 228 canonical quantitative/context fields displayed exactly once')
for field,expected in [('measurement_to_reader_item',measurements),('operation_parameter_to_reader_item',parameters),('material_quantity_to_reader_item',materials),('stock_quantity_to_reader_item',stocks)]:
    for key,(rid,p) in expected.items():
        iid=cm[field][key]
        ck(iid in items and any(f['canonical_record_id']==rid and f['json_pointer']==p for f in items[iid]['facts']),'Exact typed-map destination: '+key)
for key,(rid,p) in operations.items():
    i=items[cm['operation_to_reader_item'][key]]; o=ptr(R[rid],p)
    ck(any(l['record_id']==rid and l['json_pointer']==p for l in i['canonical_links']),'Direct operation pointer: '+key)
    ck(i['title']==o['label'] and cm['operation_original_descriptions'][key]==o['description'],'Exact source operation label and original description retained privately: '+key)
    ck(bool(i['text']) and '{' not in i['text'] and 'Source conditions:' not in i['text'] and 'Framework relation:' not in i['text'],'Readable operation prose rather than serialized source context: '+key)
    for k,default in [('inputs',None),('outputs',None),('environment',None),('condition_options',[]),('retained_fraction',None)]: ck(i['operation_context'][k]==o.get(k,default),'Operation '+k+' retained: '+key)
for field,expected in [('canonical_material_slots',slots),('canonical_sample_contexts',samples)]:
    for key,(rid,p) in expected.items():
        x=cm[field][key]; i=items[x['reader_item_id']]
        ck(x['json_pointer']==p and any(l['record_id']==rid and l['json_pointer']==p for l in i['canonical_links']),'Direct material/sample context pointer: '+key)
        if field=='canonical_sample_contexts': ck(any(z['record_id']==rid and z['json_pointer']==p and z['sample']==ptr(R[rid],p) for z in i['canonical_sample_contexts']),'Exact complete sample/context payload: '+key)

for row in C['facts']:
    fid=row['source_fact_id']; d=cov['fact_to_reader'][fid]
    ck(d['original_source_fact']==row['source_fact'],'Original source-fact payload retained: '+fid)
    ck(bool(d['reader_item_ids']) and all(i in items for i in d['reader_item_ids']),'Source-fact reader target exists: '+fid)
    ck(len(d['canonical_bindings'])==len(row['canonical_bindings']),'All source-fact bindings included: '+fid)
    for old,new in zip(row['canonical_bindings'],d['canonical_bindings']):
        ck(all(new[k]==v for k,v in old.items()),'Original source-fact binding unchanged: '+fid)
        iid,f=allfacts[new['reader_fact_id']]
        ck(iid==new['reader_item_id'] and f['canonical_record_id']==old['record_id'] and f['json_pointer']==old['pointer'] and fid in f['source_fact_ids'],'Exact displayed source-fact pointer: '+fid)
obj={}
for cat in ['materials','stocks','protocols','samples','measurements','observations','author_interpretations_and_outlook','figures','references','contradictions','gaps','unperformed_options']:
    for n,x in enumerate(F[cat]): obj[(cat,str(x.get('id',n)))]=x
for x in I['administrative_and_footnote_units']: obj[('administrative_and_footnote_units',x['id'])]=x
obj[('bibliography','identity')]={'title':F['title'],'authors':F['authors'],**F['bibliography']}; obj[('structure_status','scope')]=F['structure_status']
ck(len(cov['source_objects_to_reader'])==len(C['source_objects'])==170,'All original source-object bindings preserved')
for old,new in zip(C['source_objects'],cov['source_objects_to_reader']):
    label=old['category']+' / '+old['source_object_id']+' / '+old['record_id']
    ck(all(new[k]==v for k,v in old.items()),'Exact source-object canonical binding: '+label)
    ck(new['source_object_payload']==obj[(old['category'],old['source_object_id'])],'Exact original source-object payload: '+label)
    i=items[new['reader_item_id']]
    ck(any(l['record_id']==old['record_id'] and l['json_pointer']==old['pointer'] for l in i['canonical_links']),'Source-object canonical pointer reachable: '+label)

assets={a['id']:a for g in ['figures','tables','schemes','equations','source_notes'] for a in r[g]}
ck(set(assets)=={SID+'-'+a['id'] for a in I['assets']},'All eight original figures and no manufactured original assets')
for a in I['assets']:
    aid=SID+'-'+a['id']; p=assets[aid]; f=next(f for f in F['figures'] if f['asset_id']==a['id'])
    ck(sha(a['path'])==a['sha256']==p['public_asset_sha256'],'Original figure bytes unchanged: '+aid)
    ck(p['page']==a['pdf_page'] and p['document_role']==a['source_role'] and p['asset_provenance']['source_sha256']==a['source_sha256'],'Original figure source and page exact: '+aid)
    for k,v in [('crop_normalized',a['crop_rectangle_fraction_top_origin']),('crop_pdf_points',a['crop_rectangle_pdf_points_top_origin']),('render_scale',a['render_scale']),('pixel_dimensions',a['pixel_size']),('transformation',a['creation'])]: ck(p['asset_provenance'][k]==v,'Original crop provenance '+k+': '+aid)
    ck(p['public_asset']=='assets/figures/'+SID+'/'+Path(a['path']).name and '..' not in p['public_asset'],'Proposed public asset path safe: '+aid)
    ck(not p['reviewed'] and not p['reader_render_verified'] and not p['training_eligible'],'Original presentation approval remains pending: '+aid)
    expected={(rid,sid) for sid in f['sample_ids'] for rid,rr in R.items() if sid in {s['sample_id'] for s in rr['products']}}
    ck({(s['record_id'],s['sample_id']) for s in p['canonical_sample_links']}==expected,'Exact source-defined figure/sample joins: '+aid)
    ck(set(p['sample_links'])=={rid for rid,s in expected},'Record-level asset scope follows exact specimen joins: '+aid)
    ck(any(aid in [x['id'] for x in i['original_assets']] for i in items.values()),'Original asset reachable from reader: '+aid)
    ck(p['caption_paraphrase']==f['content'] and any(isinstance(n,dict) and n.get('Original axes and labels')==f['axes_and_labels'] for n in p['notes']),'Original caption and axis payload retained: '+aid)
for iid,i in items.items():
    for a in i['original_assets']: ck(a['id'] in assets and a['public_asset']==assets[a['id']]['public_asset'] and a['public_asset_sha256']==assets[a['id']]['public_asset_sha256'],'Item original asset link: '+iid+' / '+a['id'])
ck(assets[SID+'-si-figure1']['sample_links']==['nagasaki-2004-tem'],'TEM evidence limited to generic SI specimen')
ck(assets[SID+'-si-figure2']['sample_links']==['nagasaki-2004-xrd'] and {s['sample_id'] for s in assets[SID+'-si-figure2']['canonical_sample_links']}=={'si-xrd-cds'},'XRD original not assigned to polymer-only or biotin specimen')
ck(all('nagasaki-2004-biotin-cds' not in assets[SID+'-'+a]['sample_links'] for a in ['si-figure1','si-figure2']),'No specific biotin SI structural join')
ck(not r['tables'] and not r['schemes'] and not r['equations'],'No invented source tables, schemes or numbered equations')
ck({x['id'] for x in r['referenced_methods']}=={x['id'] for x in F['references']} and len(F['references'])==25,'All expanded bibliographic entries included')
for x in F['references']:
    z=next(z for z in r['referenced_methods'] if z['id']==x['id'])
    ck(z['inspection_status']==x['access_level'] and 'not inspected' in z['inspection_status'],'External citation access accurately scoped: '+x['id'])
ck('source-reference-note11' in items and 'graft' in items['source-reference-note11']['text'],'Substantive note 11 retained separately')
for x in F['contradictions']:
    i=items['conflict-'+x['id']]
    ck(x['source_claim'] in i['text'] and x['visual_observation'] in i['text'] and x['resolution'] in i['notes'],'Unresolved original source conflict retained: '+x['id'])
ck('molecular-weight units' in items['purified-acetal-block-polymer']['text'],'Polymer molecular-weight units remain unspecified')
ck('amine-group' in items['stock-aqueous-polymer-medium']['text'] and 'not whole-polymer-chain molarity' in items['stock-aqueous-polymer-medium']['text'],'Amine basis is not chain molarity')
ck('initial polymer-solution volume' in items['cho-cds-representative']['text'] and 'Added moles and final reaction volume therefore remain unknown' in items['cho-cds-representative']['text'],'Initial volume not used as missing addition volume')
ck('does not provide a separately quantified' in items['biotin-cds']['text'],'Biotin route missingness not overwritten by representative charges')
ck('assay conditions are separate from synthesis' in items['zeta-assay']['text'],'Measured pH range not synthesis pH')
ck('eleven' in items['figure4-fret-series']['text'] and 'not eleven newly constructed synthesis records' in items['figure4-fret-series']['text'],'Concentration legend not inflated into recipe count')
ck('No supplied CIF' in items['atomic-structure-availability']['text'],'No recovered atomic-coordinate claim')
ck('discussed_not_performed'==items['post-cds-ligand-installation']['claim_type'],'Unperformed alternative is not a performed recipe')
for formula,rids in r['material_evidence_records'].items(): ck(set(rids)<=set(R),'Material context records resolve: '+formula)
for formula,aids in r['material_original_asset_ids'].items(): ck(set(aids)<=set(assets),'Material original gallery resolves: '+formula)
for rid,rids in r['route_evidence_contexts'].items(): ck(rid in R and set(rids)<=set(R),'Route evidence contexts resolve: '+rid)
ck('nagasaki-2004-tem' not in r['route_evidence_contexts']['nagasaki-2004-biotin-cds'] and 'nagasaki-2004-xrd' not in r['route_evidence_contexts']['nagasaki-2004-biotin-cds'],'Biotin route not linked directly to unresolved generic structural contexts')
ck(Counter(x['record_type'] for x in r['recipe_inventory'])==Counter(d['record_type'] for d in R.values()),'Recipe versus procedure/context counts preserved')
ck(not r['source_review_promoted'] and not r['training_eligible'] and not bind['publication_approved'] and not bind['molecular_or_apparatus_bindings_approved'],'No viewer, training, import or publication approval inferred')
ck(not re.search(r'[A-Za-z]:[\\/]|file://|miniforge|canonical-drafts',json.dumps(r,ensure_ascii=False)),'Public reader contains no private local paths')
ck(bind['reader_sha256']==sha(O/f'{SID}.json'),'Binding proposal names exact generated reader')
failures=[x for x in checks if not x['passed']]
report={'schema':'mattersyn-private-reader-author-validation/1','source_id':SID,'created_at':datetime.now(timezone.utc).isoformat(),'status':'passed' if not failures else 'failed','scope':'Private author completeness, exact JSON-pointer and quantity/specimen/source-byte checks. Not independent scientific review, actual Site build, browser QA or publication.','reader_sha256':sha(O/f'{SID}.json'),'counts':r['counts'],'check_count':len(checks),'failure_count':len(failures),'failures':failures,'input_hashes':inputs['input_hashes'],'draft_sha256':cm['draft_sha256'],'checks':checks,'independent_reader_audit_passed':False,'browser_qa_performed':False,'published':False}
(O/'proposal-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(checks),'failures':failures},ensure_ascii=False))
raise SystemExit(bool(failures))
