"""Private author completeness and exact-binding checks; no independent approval.

Runs the current read-only Site's real paper-review validator against a private
projection of frozen records and original assets. It never runs the Site build.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import hashlib,importlib.util,json,re,shutil,struct,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;B=O.parent
SITE=Path(r'[local path redacted]')
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def esc(s):return s.replace('~','~0').replace('/','~1')
def resolve(o,p):
    for s in p.strip('/').split('/') if p else []:
        s=s.replace('~1','/').replace('~0','~');o=o[int(s)] if isinstance(o,list) else o[s]
    return o
def display(q):
    if q.get('value') is not None:return q['value']
    lo,hi=q.get('minimum'),q.get('maximum')
    if lo is not None and hi is not None:return f'{lo:g}–{hi:g}'
    if lo is not None:return ('> ' if q.get('minimum_exclusive') else '≥ ')+f'{lo:g}'
    if hi is not None:return ('< ' if q.get('maximum_exclusive') else '≤ ')+f'{hi:g}'
    return 'Not reported' if q.get('status')=='not_reported' else q.get('raw_text') or q.get('status','Unspecified')
checks=[]
def check(ok,label,details=None):checks.append({'passed':bool(ok),'check':label,**({'details':details} if details is not None else {})})
R=read(O/'norberg2004.json');C=read(O/'source-item-coverage.json');CM=read(O/'canonical-measurement-coverage.json');BI=read(O/'reader-bindings-proposal.json');M=read(O/'reader-author-manifest.json')
I=read(B/'source-inventory.json');F=read(B/'source-facts.json');CC=read(B/'canonical-source-coverage.json');CA=read(B/'canonical-records-audit.json');SA=read(B/'source-scientific-audit.json');AM=read(B/'reader-assets/asset-manifest.json');MAN=read(B/'canonical-record-manifest.json')
ORIGINAL_AM=AM
if (O/'reader-original-assets-manifest.json').is_file():AM=read(O/'reader-original-assets-manifest.json')
RECS={m['record_id']:read(m['path']) for m in MAN['records']}
BOUND={str(p):sha(p) for p in [B/'source-inventory.json',B/'source-facts.json',B/'canonical-source-coverage.json',B/'canonical-record-manifest.json',B/'canonical-records-audit.json',B/'source-scientific-audit.json',B/'page-coverage.json',B/'reader-assets/asset-manifest.json',SITE/'scripts/build_paper_reviews.py',SITE/'scripts/review_scope.py',SITE/'dist/source-evidence.mjs']+[Path(m['path']) for m in MAN['records']]}
if AM is not ORIGINAL_AM:BOUND[str(O/'reader-original-assets-manifest.json')]=sha(O/'reader-original-assets-manifest.json')
ITEMS={i['id']:i for s in R['reader_sections'] for i in s['items']};ALLF={};EXPECTED={};SEEN=[]
check(len(ITEMS)==sum(len(s['items']) for s in R['reader_sections'])==288,'Unique 288 reader item IDs')
check([s['title'] for s in R['reader_sections']]==['Precursors','Synthesis protocol','Final structures','Properties','Chemical intuition','Sources and limitations'],'Five academic sections and sources appendix')
check(R['review_scope']=='supplied_main_and_matched_si','Full main-plus-matched-SI scope')
check(CA['status']=='passed' and SA['status']=='passed' and CA['manifest_sha256']==sha(B/'canonical-record-manifest.json'),'Previously passed source and canonical audit boundaries')
check(len(RECS)==19 and Counter(r['record_type'] for r in RECS.values())=={'literature_protocol':1,'procedure':11,'observation':7},'One route plus separate procedure/observation contexts')
check({r['lineage']['source_group'] for r in RECS.values()}=={'norberg2004'},'All records share one source group for leakage control')
for m in MAN['records']:
    rid=m['record_id'];check(m['sha256']==sha(m['path'])==CM['draft_sha256'][rid]==CA['record_hashes'][rid], 'Frozen independently audited record: '+rid)
    check(RECS[rid]['quality']['review_status']=='imported_unreviewed' and not RECS[rid]['quality']['requested_tasks'] and not RECS[rid].get('collection'),'No canonical training or collection promotion: '+rid)
check({d['role']:d['page_count'] for d in R['documents']}=={'main':12,'si':4},'All 12 main and four SI pages included')
for d in R['documents']:
    check([p['page'] for p in d['pages']]==list(range(1,d['page_count']+1)) and all(p['text_read'] and p['visual_review'] for p in d['pages']),'Previously audited complete page coverage: '+d['role'])
    check(d['sha256']==next(x['sha256'] for x in I['source_documents'] if x['role']==d['role']),'Reader document hash: '+d['role'])
for d in SA['source_documents']:check(sha(d['path'])==d['sha256'],'Original source copy unchanged: '+d['location']+'/'+d['role'])
for p,h in M['input_hashes'].items():check(sha(p)==h,'Reader author froze exact source/canonical input: '+p)
for p,h in M['outputs'].items():check(sha(O/p)==h,'Manifest output hash: '+p)
check(C['source_inventory_sha256']==sha(B/'source-inventory.json') and C['source_facts_sha256']==sha(B/'source-facts.json') and C['canonical_coverage_sha256']==sha(B/'canonical-source-coverage.json'),'Exact coverage input hashes')
check(set(C['unit_to_reader_items'])=={u['source_unit_id'] for u in CC['source_units']} and len(C['unit_to_reader_items'])==180 and not C['unmapped_units'],'All 180 canonical source-unit scopes mapped')
for uid,ids in C['unit_to_reader_items'].items():check(bool(ids) and all(i in ITEMS and uid in ITEMS[i]['source_audit_unit_ids'] for i in ids),'Bidirectional source-unit reader links: '+uid)
for iid,item in ITEMS.items():
    for uid in item['source_audit_unit_ids']:check(iid in C['unit_to_reader_items'][uid],'Reverse unit map: '+iid+'/'+uid)

MAP_EXPECT={k:{} for k in ['measurement_to_reader_item','operation_to_reader_item','operation_parameter_to_reader_item','material_to_reader_item','material_quantity_to_reader_item','stock_to_reader_item','stock_quantity_to_reader_item','product_to_reader_item','product_quantity_to_reader_item','condition_option_quantity_to_reader_item','operation_environment_endpoint_to_reader_item']}
def expect(mapname,key,rid,ptr,quantity=False):
    MAP_EXPECT[mapname][key]=(rid,ptr)
    if quantity:EXPECTED[(rid,ptr)]=resolve(RECS[rid],ptr)
for rid,r in RECS.items():
    for n,m in enumerate(r['measurements']):expect('measurement_to_reader_item',rid+'::'+m['id'],rid,f'/measurements/{n}/value',True)
    for n,o in enumerate(r['operations']):
        key=rid+'::'+o['id'];ptr=f'/operations/{n}';expect('operation_to_reader_item',key,rid,ptr)
        for k in o['parameters']:expect('operation_parameter_to_reader_item',key+'::'+k,rid,ptr+'/parameters/'+esc(k),True)
        for k in ['environment','endpoint']:expect('operation_environment_endpoint_to_reader_item',key+'::'+k,rid,ptr+'/'+k,True)
    for n,m in enumerate(r['materials']):
        key=rid+'::'+m['id'];ptr=f'/materials/{n}';expect('material_to_reader_item',key,rid,ptr)
        for k in m['quantities']:expect('material_quantity_to_reader_item',key+'::'+k,rid,ptr+'/quantities/'+esc(k),True)
    for n,s in enumerate(r['stocks']):
        key=rid+'::'+s['id'];ptr=f'/stocks/{n}';expect('stock_to_reader_item',key,rid,ptr)
        for k in s['concentrations']:expect('stock_quantity_to_reader_item',key+'::'+k,rid,ptr+'/concentrations/'+esc(k),True)
        for j,c in enumerate(s['components']):
            for k in c.get('quantities',{}):expect('stock_quantity_to_reader_item',key+'::'+str(j)+'::'+k,rid,ptr+f'/components/{j}/quantities/'+esc(k),True)
    for n,p in enumerate(r['products']):
        key=rid+'::'+p['sample_id'];ptr=f'/products/{n}';expect('product_to_reader_item',key,rid,ptr)
        for k in ['composition','phase','morphology','surface']:expect('product_quantity_to_reader_item',key+'::'+k,rid,ptr+'/'+k,True)
    for n,c in enumerate(r['condition_options']):
        for k in c['parameters']:expect('condition_option_quantity_to_reader_item',rid+'::'+c['id']+'::'+k,rid,f'/condition_options/{n}/parameters/'+esc(k),True)
for name,expected in MAP_EXPECT.items():
    check(set(CM[name])==set(expected),'Complete canonical map: '+name)
    for k,(rid,ptr) in expected.items():
        iid=CM[name].get(k);check(iid in ITEMS and any(l['record_id']==rid and l['json_pointer']==ptr for l in ITEMS.get(iid,{}).get('canonical_links',[])), 'Exact canonical map link: '+name+'/'+k)
check(len(EXPECTED)==1218 and len(MAP_EXPECT['operation_to_reader_item'])==47 and len(MAP_EXPECT['measurement_to_reader_item'])==590,'Actual audited operation/context and typed-field totals')
for iid,item in ITEMS.items():
    check(bool(item['title']) and bool(item['text']) and bool(item['evidence']),'Academic prose and source evidence: '+iid)
    check(item['training_eligible'] is False and item['sample_scope']['physical_batch_id'] is None,'No invented physical batch or training approval: '+iid)
    for ev in item['evidence']:check(ev['source_id']=='norberg2004' and ev['document_role'] in ['main','si'] and (ev['pdf_page'] is None or 1<=ev['pdf_page']<=({'main':12,'si':4}[ev['document_role']])), 'In-bounds source locator: '+iid+'/'+str(ev['locator']))
    for l in item['canonical_links']:
        try:resolve(RECS[l['record_id']],l['json_pointer']);ok=True
        except (KeyError,IndexError,ValueError,TypeError):ok=False
        check(ok,'Resolvable canonical reader link: '+iid+'/'+l['record_id']+l['json_pointer'])
    for j in item['sample_scope']['canonical_sample_links']:check(resolve(RECS[j['record_id']],j['json_pointer'])['sample_id']==j['sample_id'],'Exact record-scoped specimen link: '+iid+'/'+j['record_id']+'/'+j['sample_id'])
    for f in item['facts']:
        check(f['id'] not in ALLF,'Unique fact ID: '+f['id']);ALLF[f['id']]=(iid,f);key=(f['canonical_record_id'],f['json_pointer']);SEEN.append(key)
        check(key in EXPECTED and f['canonical_quantity']==EXPECTED[key],'Exact unchanged canonical quantity: '+f['id'])
        q=f['canonical_quantity'];check(f['status']==q.get('status') and f['unit']==q.get('unit') and f['approximate']==q.get('approximate',False),'Visible status, unit and approximation: '+f['id'])
        check(f['training_eligible'] is False,'Typed field not training-approved: '+f['id'])
        if f['presentation_kind']=='exact_quantity':check(f['value']==display(q),'Exact visible quantity or source bound: '+f['id'])
        else:check(f['presentation_kind']=='academic_inventory_summary' and bool(f['value']) and not isinstance(f['value'],str) or f['presentation_kind']=='academic_inventory_summary' and not f['value'].lstrip().startswith('{'),'Readable inventory summary replaces JSON display: '+f['id'])
        if f.get('sample_id'):check(resolve(RECS[f['canonical_record_id']],f['json_pointer'].rsplit('/',1)[0])['sample_id']==f['sample_id'],'Canonical measurement specimen retained: '+f['id'])
        if q.get('basis'):check(q['basis'] in f['qualifier'],'Quantity basis is visible: '+f['id'])
        if q.get('qualifier'):check(q['qualifier'] in f['qualifier'],'Quantity qualifier is visible: '+f['id'])
check(Counter(SEEN)==Counter(EXPECTED.keys()),'Every canonical quantitative/context field appears exactly once')
check(len(CM['displayed_field_map'])==len(EXPECTED),'Complete displayed-field map length')
for b in CM['displayed_field_map']:
    iid,f=ALLF[b['reader_fact_id']];check((iid,f['canonical_record_id'],f['json_pointer'])==(b['reader_item_id'],b['record_id'],b['json_pointer']),'Displayed-field exact binding: '+b['reader_fact_id'])
check(set(C['fact_to_reader'])=={f['id'] for f in F['facts']} and len(C['fact_to_reader'])==201,'All 201 original source facts mapped')
for src in CC['facts']:
    fid=src['source_fact_id'];m=C['fact_to_reader'][fid]
    check(m['source_unit_id']==src['source_fact']['source_unit_id'] and all(i in ITEMS for i in m['reader_item_ids']),'Source-fact scope and target IDs: '+fid)
    check([{k:v for k,v in b.items() if k not in ['reader_item_id','reader_fact_id']} for b in m['canonical_bindings']]==src['canonical_bindings'],'Every original typed source-to-canonical binding preserved: '+fid)
    for b in m['canonical_bindings']:
        iid,f=ALLF[b['reader_fact_id']];check(iid==b['reader_item_id'] and f['canonical_record_id']==b['record_id'] and f['json_pointer']==b['pointer'] and fid in f['source_fact_ids'] and fid in ITEMS[iid]['source_fact_ids'] and f['presentation_kind']=='exact_quantity','Source fact reaches exact visible canonical quantity: '+fid+'/'+b['reader_fact_id'])

cats=['materials','stocks','protocols','samples','figures_tables_schemes','equations','tables','chemical_intuition','references','gaps','other_source_content']
OBJ={(cat,o.get('id',o.get('kind',str(n)))):(f'/{cat}/{n}',o) for cat in cats for n,o in enumerate(I[cat])}
check(len(OBJ)==174 and {(s['category'],s['source_object_id']) for s in C['source_objects']}==set(OBJ),'All 174 original inventory objects mapped')
for s in C['source_objects']:
    key=(s['category'],s['source_object_id']);p,obj=OBJ[key]
    check(s['source_pointer']==p and resolve(I,p)==obj and s['reader_item_id'] in ITEMS,'Exact original source-object pointer: '+str(key))
    check(s['canonical_bindings']==[b for b in CC['source_objects'] if (b['category'],b['source_object_id'])==key],'All original source-object canonical destinations preserved: '+str(key))
PAY=[b for b in CC['source_objects'] if b['mode']=='lossless_inventory_context_payload']
check(len(C['lossless_inventory_payload_map'])==len(PAY)==174,'All 174 lossless payloads retained with reader summaries')
for b in C['lossless_inventory_payload_map']:
    iid,f=ALLF[b['reader_fact_id']];obj=OBJ[(b['category'],b['source_object_id'])][1]
    check(iid==b['reader_item_id'] and (f['canonical_record_id'],f['json_pointer'])==(b['record_id'],b['json_pointer']) and f['presentation_kind']=='academic_inventory_summary','Payload exact reader binding: '+b['reader_fact_id'])
    check(json.loads(f['canonical_quantity']['value'])==obj,'Complete original payload survives readable presentation: '+b['reader_fact_id'])

for key,(rid,ptr) in MAP_EXPECT['operation_to_reader_item'].items():
    op=resolve(RECS[rid],ptr);item=ITEMS[CM['operation_to_reader_item'][key]];c=item['operation_context']
    for k in ['stage','branch','depends_on','environment','inputs','outputs','retained_fraction','endpoint']:check(c[k]==op[k],'Source operation '+k+': '+key)
    check(c['condition_options']==RECS[rid]['condition_options'] and c['optional_inputs']==op.get('optional_inputs',[]),'Separate alternatives remain scoped: '+key)
    labels={m['id']:m['name'] for m in RECS[rid]['materials']}|{s['id']:s['name'] for s in RECS[rid]['stocks']}|{s['id']:s['name'] for s in RECS[rid]['material_states']}
    check(c['material_flow_labels']=={k:labels[k] for k in op['inputs']+op.get('optional_inputs',[])+op['outputs']},'Named source-state inputs/outputs: '+key)
    check(c['diagram_binding_status']=='pending_independent_visual_binding','No apparatus approval: '+key)

GROUPS=[a for g in ['figures','tables','equations','schemes','source_notes'] for a in R[g]];GA={a['id']:a for a in GROUPS};PRIVATE={a['source_asset_id']:a for a in BI['original_assets']}
check(len(GA)==len(GROUPS)==43 and len(PRIVATE)==40 and len({a['public_asset'] for a in GROUPS})==40,'43 source entries reuse exactly 40 unchanged original assets')
check(Counter(a['source_role'] for a in AM['assets'] if a['kind']=='full_page')=={'main':12,'si':4},'All 16 complete original pages retained')
check({a['id'] for a in AM['assets']}==set(PRIVATE),'Every original page and crop assigned a private binding')
for a in AM['assets']:
    p=GA['norberg2004-'+a['id']];bp=PRIVATE[a['id']];file=B/a['path']
    check(sha(file)==a['sha256']==p['public_asset_sha256']==bp['sha256'] and Path(bp['private_path'])==file,'Unchanged original asset bytes: '+a['id'])
    check(p['asset_provenance']['source_sha256']==a['source_sha256'] and p['page']==a['pdf_page'] and p['document_role']==a['source_role'],'Original asset source/page identity: '+a['id'])
    check(p['public_asset']==bp['public_asset'] and p['public_asset'].startswith('assets/figures/norberg2004/') and '..' not in Path(p['public_asset']).parts,'Safe proposed original-asset route: '+a['id'])
    with file.open('rb') as fh:hdr=fh.read(24)
    check(hdr[:8]==b'\x89PNG\r\n\x1a\n' and list(struct.unpack('>II',hdr[16:24]))==a['dimensions']==p['asset_provenance']['pixel_dimensions'],'Original readable pixel dimensions: '+a['id'])
    check(any(p['id'] in [x['id'] for x in item['original_assets']] for item in ITEMS.values()),'Original asset reachable within reader: '+a['id'])
    if a.get('reader_specific_rerender'):
        old=next(x for x in ORIGINAL_AM['assets'] if x['id']==a['id'])
        check(sha(B/old['path'])==old['sha256']==a['replaces_asset']['sha256'],'Archived original render remains unchanged: '+a['id'])
        check(a['crop']==old['crop'] and a['dimensions']==old['dimensions'] and a['source_sha256']==old['source_sha256'],'Reader rerender preserves exact source and crop extent: '+a['id'])
        check(p['asset_provenance']['renderer']==AM['render_engine'] and p['asset_provenance']['replaces_archived_render']['sha256']==old['sha256'],'Reader advertises actual replacement renderer/provenance: '+a['id'])
for p in GROUPS:
    check(not p['reviewed'] and not p['reader_render_verified'] and not p['training_eligible'],'Reader asset approval still pending: '+p['id'])
    for l in p['canonical_sample_links']:check(resolve(RECS[l['record_id']],l['json_pointer'])['sample_id']==l['sample_id'],'Exact record-scoped original-asset specimen: '+p['id']+'/'+l['record_id']+'/'+l['sample_id'])
for item in ITEMS.values():
    for a in item['original_assets']:check(a['id'] in GA and (a['public_asset'],a['public_asset_sha256'])==(GA[a['id']]['public_asset'],GA[a['id']]['public_asset_sha256']),'Reader original-asset link exact: '+item['id']+'/'+a['id'])
for table in I['tables']:
    p=GA['norberg2004-'+table['id']];check(p['source_rows']==table['rows'] and p['columns']==table['columns'] and p['row_count']==len(table['rows']) and p['table_status']==table['status'],'Complete source table with original row/column status: '+table['id'])
    if 'final_averages' in table:check(p['source_final_averages']==table['final_averages'],'Full source final averages: '+table['id'])
    if 'temperature_K' in table:check(p['source_temperature_K']==table['temperature_K'],'Full source table temperature: '+table['id'])
check(len(R['figures'])==13 and len(R['tables'])==4 and len(R['equations'])==7 and len(R['schemes'])==1 and sum(a['row_count'] for a in R['tables'])==21,'All 18 figure/table/scheme items, seven equations and 21 table rows')
check(len(R['referenced_methods'])==68 and {x['id'] for x in R['referenced_methods']}=={x['id'] for x in I['references']},'All 68 source references individually reachable')
for ref in R['referenced_methods']:
    original=next(x for x in I['references'] if x['id']==ref['id']);check(ref['inspection_status']==original['inspection_status'] and ref['citation']==original.get('bibliography_extracted_text',original.get('bibliography_transcription')) and ref['reader_item_id'] in ITEMS,'Exact citation and uninspected-reference status: '+ref['id'])
for formula,ids in R['material_evidence_records'].items():check(set(ids)<=set(RECS),'Material evidence records resolve: '+formula)
for formula,ids in R['material_original_asset_ids'].items():check(set(ids)<=set(GA),'Material original assets resolve: '+formula)

# Bounded author scope assertions against the already independently audited data.
def facts(fid):return [ALLF[b['reader_fact_id']][1] for b in C['fact_to_reader']['norberg2004-'+fid]['canonical_bindings']]
def every(fid,fn,label):check(all(fn(f) for f in facts(fid)),label)
every('clean-time',lambda f:f['value']==30 and f['approximate'] is True,'General cleaning approximately 30 min')
every('aliquot-clean-time',lambda f:f['value']==30 and f['approximate'] is False,'Specific growth-series treatment 30 min without approximation')
every('cool-limit',lambda f:f['canonical_quantity'].get('maximum')==80 and f['canonical_quantity'].get('maximum_exclusive') is True,'Cooling strictly below 80 degrees C')
every('domain-spin-bound',lambda f:f['sample_id']=='films-a-b-c-collective' and f['canonical_quantity'].get('minimum')==800 and f['canonical_quantity'].get('minimum_exclusive') is True,'Collective S > 800 remains non-film-A-specific')
every('tc-bound',lambda f:f['canonical_quantity'].get('minimum')==350 and f['canonical_quantity'].get('minimum_exclusive') is True,'Tc > 350 K is a bound, not measured transition')
for letter in 'df':
    for suffix in ['mass-si','Ms-emu','Ms-per-Mn']:
        every('film-'+letter+'-'+suffix,lambda f:'g-si-curve-table' in f['qualifier'] or 'unresolved' in f['qualifier'].lower(),'Unresolved D/F identity travels with outcome: '+letter+'/'+suffix)
for letter,value in [('a',40),('b',20),('c',20)]:every('film-'+letter+'-coats',lambda f:f['value']==value,'Correct film coating count: '+letter)
for aid in ['figure-s3','table-s4']:check('unresolved' in ' '.join(GA['norberg2004-'+aid]['notes']).lower(),'D/F discrepancy explicit at original asset: '+aid)
check(ITEMS['u-zno-reference']['sample_scope']['scope_kind']=='cited_context' and ITEMS['u-context-maximum-mn']['sample_scope']['scope_kind']=='model_context','Reference Bohr radius and assumed maximum moment are not source measurements')
check('not a measured particle radius' in ITEMS['u-zno-reference']['text'],'Reference length distinguished from particle size')
check('does not receive' in ITEMS['u-protocol-surface-control']['text'],'Surface-bound reference is not amine-stripped')
check('not restated' in ITEMS['u-protocol-topo']['text'],'Partial TOPO method retains missing time/temperature/amount')
check('not receive' not in ITEMS['u-protocol-amine-cleaning']['text'],'Amine procedure remains its own actual treatment')
check('One kilobar is not assigned' in ITEMS['u-solubility-reference']['text'],'Reference pressure never presented as current film pressure')
check('not observed' in ITEMS['u-optical-series']['text'],'Performed negative Mn-emission observation remains visible')
check('SAED' in ' '.join(GA['norberg2004-figure-3']['notes']) and 'No SAED' in ' '.join(GA['norberg2004-figure-3']['notes']),'No invented SAED for this source')
check(not R['source_review_promoted'] and not R['training_eligible'] and not BI['publication_approved'] and not BI['molecular_or_apparatus_bindings_approved'],'Publication, training and visual binding approvals remain closed')
check(BI['reader_sha256']==sha(O/'norberg2004.json'),'Binding proposal matches exact reader')
check(not re.search(r'[A-Z]:[\\/]|file://|miniforge|canonical-drafts',json.dumps(R,ensure_ascii=False)),'Public reader contains no local filesystem paths')

# Current Site validator, with only ROOT changed in memory to a private projection.
projection=O/'validation-view';projection.mkdir(exist_ok=True)
for row in MAN['records']:
    dst=projection/'data/records'/(row['record_id']+'.json');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(row['path'],dst)
for a in BI['original_assets']:
    dst=(projection/'dist'/a['public_asset']).resolve()
    if not dst.is_relative_to((projection/'dist').resolve()):raise ValueError('Unsafe private asset path')
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a['private_path'],dst)
sys.path.insert(0,str(SITE/'scripts'))
spec=importlib.util.spec_from_file_location('norberg_private_site_review_contract',SITE/'scripts/build_paper_reviews.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.ROOT=projection
site_errors=mod.validate(R);check(not site_errors,'Current Site build_paper_reviews.validate passes on private copied projection',site_errors)
for p,h in BOUND.items():check(sha(p)==h,'Read-only source, canonical and Site contract unchanged after checks: '+p)
errors=[x for x in checks if not x['passed']]
result={'schema':'mattersyn-private-reader-author-validation/1','source_id':'norberg2004','created_at':datetime.now(timezone.utc).isoformat(),'status':'passed' if not errors else 'failed','scope':'Author exact-file, pointer, numeric/status, specimen, source-object and original-asset completeness checks, plus actual current Site contract in a private copied projection. This is not independent scientific approval, new source visual review, browser QA, figure readability approval or publication.','reader_sha256':sha(O/'norberg2004.json'),'reader_author_manifest_sha256':sha(O/'reader-author-manifest.json'),'validator_sha256':sha(__file__),'counts':R['counts'],'check_count':len(checks),'failure_count':len(errors),'failures':errors,'input_hashes':BOUND,'output_hashes':{n:sha(O/n) for n in ['norberg2004.json','source-item-coverage.json','canonical-measurement-coverage.json','reader-bindings-proposal.json','reader-items-summary.json']},'site_contract':{'path':str(SITE/'scripts/build_paper_reviews.py'),'sha256':sha(SITE/'scripts/build_paper_reviews.py'),'function':'validate','private_projection':str(projection),'errors':site_errors,'site_written':False},'checks':checks,'independent_reader_audit_passed':False,'browser_qa_performed':False,'published':False}
(O/'proposal-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':len(checks),'failures':errors},ensure_ascii=False))
raise SystemExit(bool(errors))
