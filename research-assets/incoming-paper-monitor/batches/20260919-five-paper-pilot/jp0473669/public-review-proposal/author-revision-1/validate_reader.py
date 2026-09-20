"""Author checks for private Ribeiro reader; writes only beside this file."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone
import hashlib, importlib.util, json, re, shutil, subprocess, sys

O=Path(__file__).resolve().parent;B=O.parent;SITE=Path(r'[local path redacted]')
SID='ribeiro2004';P='ribeiro-2004-';checks=[]
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def objsha(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def resolve(x,p):
    for k in p.strip('/').split('/') if p else []:
        k=k.replace('~1','/').replace('~0','~');x=x[int(k)] if isinstance(x,list) else x[k]
    return x
def check(name,condition):
    checks.append({'check':name,'passed':bool(condition)})
    if not condition:raise AssertionError(name)
def write(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

reader=read(O/(SID+'.json'));source=read(O/'source-item-coverage.json');fields=read(O/'canonical-field-coverage.json');bindings=read(O/'reader-bindings-proposal.json');manifest=read(O/'reader-author-manifest.json')
canonical={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')};units=read(B/'canonical-source-unit-index.json')['units'];cov=read(B/'canonical-source-coverage.json');inv=read(B/'source-inventory.json')
flat=[i for s in reader['reader_sections'] for i in s['items']];items={i['id']:i for i in flat}
check('unique reader item IDs',len(items)==len(flat)==93)
check('five academic sections and Sources',[(s['id'],s['title']) for s in reader['reader_sections']]==[('precursors','Precursors'),('protocol','Synthesis protocol'),('structures','Final structures'),('properties','Properties'),('intuition','Chemical intuition'),('sources','Sources and limitations')])
for p,h in manifest['input_hashes'].items():check('unchanged frozen input '+Path(p).name,sha(p)==h)
for p,h in manifest['source_pdf_hashes'].items():check('actual original source '+p,sha(p)==h)
for n,h in manifest['output_hashes'].items():check('author output hash '+n,sha(O/n)==h)
for p,h in manifest['site_readonly_contract_hashes'].items():check('unchanged current consumer '+Path(p).name,sha(p)==h)
check('builder exact',sha(O/'build_reader.py')==manifest['builder_sha256'])
check('source and canonical audit passed separately',read(B/'source-scientific-audit.json')['status']=='passed' and read(B/'canonical-records-audit.json')['status']=='passed_with_preserved_source_limits')
check('reader remains pending different independent audit',reader['presentation_gates']['independent_reader_audit']=='pending' and manifest['independent_reader_audit'] is False)
check('main-only scope explicit',reader['review_scope']=='supplied_main_only_si_unverified' and reader['supporting_information']['status']=='not_located_or_verified')
check('six supplied pages with prior reviewed coverage',len(reader['documents'])==1 and reader['documents'][0]['page_count']==6 and all(p['text_read'] and p['visual_review'] for p in reader['documents'][0]['pages']))
check('all 101 units covered exactly',set(source['unit_to_reader_items'])=={u['id'] for u in units} and len(units)==101)
for u in units:
    ids=source['unit_to_reader_items'][u['id']]
    check('unit reachable '+u['id'],bool(ids) and all(k in items and u['id'] in items[k]['source_audit_unit_ids'] for k in ids))
for row in cov['source_units']:
    for b in row['canonical_bindings']:
        check('unit canonical field '+row['source_unit_id']+' '+b['record_id']+b['pointer'],any(any(l['record_id']==b['record_id'] and l['json_pointer']==b['pointer'] for l in items[k]['canonical_links']) for k in source['unit_to_reader_items'][row['source_unit_id']]))
check('all 63 source facts covered',set(source['fact_to_reader'])=={r['source_fact_id'] for r in cov['facts']} and len(cov['facts'])==63)
for row in cov['facts']:
    f=source['fact_to_reader'][row['source_fact_id']]
    check('source fact preserved '+row['source_fact_id'],f['source_fact_sha256']==objsha(row['source_fact']))
    check('source binding count '+row['source_fact_id'],len(f['canonical_bindings'])==len(row['canonical_bindings']))
    for b in f['canonical_bindings']:
        check('source fact destination '+row['source_fact_id']+b['pointer'],row['source_fact_id'] in items[b['reader_item_id']]['source_fact_ids'] and any(l['record_id']==b['record_id'] and l['json_pointer']==b['pointer'] for l in items[b['reader_item_id']]['canonical_links']))

expected={k:set() for k in ['measurement_to_reader','operation_to_reader_item','material_slot_to_reader_item','stock_to_reader_item','sample_context_to_reader_item']}
for rid,r in canonical.items():
    check('canonical hash '+rid,sha(B/'canonical-drafts'/(rid+'.json'))==fields['record_hashes'][rid])
    for index,m in enumerate(r['measurements']):
        k=rid+'::'+m['id'];expected['measurement_to_reader'].add(k);x=fields['measurement_to_reader'][k]
        check('measurement exact object '+k,x['json_pointer']==f'/measurements/{index}' and x['sample_id']==m['sample_id'] and x['canonical_value_sha256']==objsha(m) and x['reader_item_id'] in items)
    for name,field,identifier in [('operations','operation_to_reader_item','id'),('materials','material_slot_to_reader_item','id'),('stocks','stock_to_reader_item','id'),('products','sample_context_to_reader_item','sample_id')]:
        for n,x in enumerate(r.get(name,[])):
            k=rid+'::'+x[identifier];expected[field].add(k);key=fields[field][k]
            check('entity exact pointer '+k,any(l['record_id']==rid and l['json_pointer']==f'/{name}/{n}' for l in items[key]['canonical_links']))
            if name=='operations':
                oc=items[key]['operation_context']
                check('operation flow preserved '+k,all(oc[part]==x[part] for part in ['inputs','outputs','depends_on','retained_fraction','optional','stage','branch']))
            if name=='products':check('sample remains scoped '+k,any(j['record_id']==rid and j['sample_id']==x['sample_id'] for j in items[key]['sample_scope']['canonical_sample_links']) and x['batch_id'] is None)
for k,expect in expected.items():check('complete entity map '+k,set(fields[k])==expect)
check('exact entity counts',[len(expected[k]) for k in expected]==[147,13,13,1,29])
for k,x in fields['typed_field_to_reader'].items():
    value=resolve(canonical[x['record_id']],x['json_pointer']);check('typed field object '+k,objsha(value)==x['canonical_value_sha256'])
    if x['rendering']=='typed_quantity':
        fact=next(f for f in items[x['reader_item_id']]['facts'] if f['id']==x['reader_fact_id'])
        check('typed quantity lossless '+k,fact['canonical_quantity']==value and fact['status']==value['status'])
        if value.get('value') is None and value.get('minimum') is None and value.get('maximum') is None:check('missing is not zero '+k,fact['value']=='Not reported')
        elif 'water_to_tin_relative_ratio' in x['json_pointer']:check('ratio display retains both terms',fact['value']=='500:1' and 'unreported' in fact['unit'])
        elif value.get('value') is not None:check('visible value unchanged '+k,fact['value']==value['value'])
        if value.get('maximum_exclusive'):check('exclusive maximum '+k,str(fact['value']).startswith('< '))
        if value.get('minimum') is not None and value.get('maximum') is None:check('lower bound intact '+k,str(fact['value']).startswith('> ' if value.get('minimum_exclusive') else '≥ '))
for ii in flat:
    check('required reader fields '+ii['id'],all(k in ii for k in reader['reader_contract']['item_fields']))
    check('unpromoted item '+ii['id'],ii['training_eligible'] is False and ii['sample_scope']['physical_batch_id'] is None)
    check('nonempty scientific source locator '+ii['id'],bool(ii['evidence']) and all(e['document_role']=='main' and 1<=e['pdf_page']<=6 for e in ii['evidence']))
    for l in ii['canonical_links']:resolve(canonical[l['record_id']],l['json_pointer'])
    for j in ii['sample_scope']['canonical_sample_links']:check('valid specimen join '+ii['id']+' '+j['sample_id'],resolve(canonical[j['record_id']],j['json_pointer'])['sample_id']==j['sample_id'])
check('all 11 records reachable',{x['record_ids'][0] for x in reader['recipe_inventory']}==set(canonical))
check('no new route or training admission',reader['counts']['record_types']=={'observation':5,'literature_protocol':1,'procedure':5} and reader['training_eligible'] is False and not bindings['publication_approved'])
check('molecular and apparatus binding gates stay pending',reader['presentation_gates']['molecular_bindings']=='pending' and reader['presentation_gates']['apparatus_bindings']=='pending' and not bindings['molecular_or_apparatus_bindings_approved'])
check('all bibliography citations exact',[(r['citation'],r['inspection_status']) for r in reader['referenced_methods']]==[(r['raw_bibliographic_text'],r['source_access']) for r in inv['references']])
check('31 references retained',len(reader['referenced_methods'])==31)
check('four source conflicts retained',{c['id'] for c in reader['evidence_conflicts']}=={c['id'] for c in inv['evidence_conflicts']})
check('all nine scientific missingness entries retained',len(reader['remaining_gaps'])==9)
check('no full SI or structure claim',reader['counts']['matched_si_pages']==0 and reader['presentation_gates']['atomic_geometry']=='not_supplied')
check('ratio basis prominent','molar, mass or volume basis' in items['water-ratio-excerpt']['text'])
check('pH states distinct','final measurement pH' in items['overview-ph-treatment']['text'] and 'acid-set' in items['overview-ph-comparison']['text'])
check('radius and diameter distinct','particle radius' in items['overview-concentration-structure']['text'] and 'not assigned particle diameters' in items['overview-concentration-structure']['text'])
check('XRD prose without trace and SAED','no XRD trace, SAED pattern' in items['material-sno2-colloid']['text'])
check('nucleation assumptions preserved','assume concentration-independent supersaturation' in items['overview-growth-model']['text'])
check('ion-deposition contradiction visible','ion-deposition' in items['overview-growth-model']['text'])
check('fit uncertainty and scope preserved','c < 0.04' in items['equation-4']['text'] and '0.14' in items['equation-4']['text'] and '0.07' in items['equation-4']['text'])
check('prior sizes stay prior','cited Leite route' in items['overview-source-context']['text'])
serialized=json.dumps(reader,ensure_ascii=False)
check('public proposal contains no private absolute paths',not re.search(r'[A-Za-z]:\\|/Users/|/incoming-paper-monitor/',serialized))
check('source-unit JSON not dumped in visible fact values',all(not isinstance(f['value'],str) or not f['value'].startswith('{"') for ii in flat for f in ii['facts']))

assets=reader['figures']+reader['equations']+reader['source_notes'];asset_by={a['id']:a for a in assets}
check('15 unique original assets',len(asset_by)==len(assets)==15)
check('7 figures 4 equations 4 excerpts',len(reader['figures'])==7 and len(reader['equations'])==4 and len(reader['source_notes'])==4)
check('Figure 3 not double counted',len(reader['schemes'])==1 and reader['schemes'][0]['separate_asset_count']==0 and not reader['tables'])
for a in bindings['original_assets']:
    published=asset_by[a['id']];check('source crop actual hash '+a['id'],sha(a['private_path'])==a['sha256']==published['public_asset_sha256'])
    check('crop source identity '+a['id'],published['asset_provenance']['source_sha256']==inv['source_sha256'])
    check('asset reachable '+a['id'],any(any(x['id']==a['id'] for x in ii['original_assets']) for ii in flat))
    check('asset not independently promoted '+a['id'],published['reviewed'] is False and published['reader_render_verified'] is False)
    for j in published['canonical_sample_links']:check('asset specimen pointer '+a['id']+' '+j['sample_id'],resolve(canonical[j['record_id']],j['json_pointer'])['sample_id']==j['sample_id'])
check('Figure 4 panel identities',[(j['record_id'],j['sample_id']) for j in asset_by[SID+'-figure-4']['canonical_sample_links']]==[(P+'concentration-structure',x) for x in ['hrtem-a','hrtem-b','hrtem-comparison']])
check('Figure 7 stays pH specimen context',all(j['record_id']==P+'ph-comparison' for j in asset_by[SID+'-figure-7']['canonical_sample_links']))
check('Figure 2 is author model',asset_by[SID+'-figure-2']['evidence_class']=='author_model')
check('Figure 6 preserves mixed analytical context',asset_by[SID+'-figure-6']['evidence_class']=='mixed_measurement_and_author_model')

# Exercise the unchanged current Site consumer against exact private copies.
# This is a compatibility fixture, not a Site integration or browser assertion.
fixture=O/'compatibility-fixture';(fixture/'data/records').mkdir(parents=True,exist_ok=True)
for rid in canonical:shutil.copyfile(B/'canonical-drafts'/(rid+'.json'),fixture/'data/records'/(rid+'.json'))
for a in bindings['original_assets']:
    dest=fixture/'dist'/a['public_asset'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a['private_path'],dest)
sys.path.insert(0,str(SITE/'scripts'))
spec=importlib.util.spec_from_file_location('ribeiro_site_reader_contract',SITE/'scripts/build_paper_reviews.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.ROOT=fixture
check('current Site coverage validator accepts private proposal',module.validate(reader)==[])
bad=deepcopy(reader);bad['documents'][0]['pages'].pop();check('consumer rejects missing page',bool(module.validate(bad)))
bad=deepcopy(reader);bad['figures'][0]['public_asset_sha256']='0'*64;check('consumer rejects wrong asset hash',bool(module.validate(bad)))
bad=deepcopy(reader);bad['review_scope']='supplied_main_and_matched_si';check('consumer rejects false matched-SI scope',bool(module.validate(bad)))
bad=deepcopy(reader);bad['recipe_inventory'][0]['record_ids']=['ribeiro-unknown'];check('consumer rejects unresolved record',bool(module.validate(bad)))

node=Path(r'[local path redacted]')
result=subprocess.run([str(node),str(O/'check_reader_render.mjs')],capture_output=True,text=True,encoding='utf8')
check('current source-evidence renderer smoke checks',result.returncode==0)
render=read(O/'reader-render-check.json');check('all source items rendered',render['rendered_items']==93 and render['checks_passed'])
for p,h in manifest['input_hashes'].items():check('post-validation unchanged '+Path(p).name,sha(p)==h)

out={'schema':'mattersyn-private-reader-author-validation/1','source_id':SID,'author':'/root/backlog_eta','validated_at':datetime.now(timezone.utc).isoformat(),'status':'passed_author_checks_pending_independent_reader_audit','check_count':len(checks),'checks':checks,'reader_sha256':sha(O/(SID+'.json')),'author_manifest_sha256':sha(O/'reader-author-manifest.json'),'validator_sha256':sha(__file__),'counts':reader['counts'],'visual_source_crop_review':{'all_15_original_crops_viewed':True,'method':'Actual original PNGs viewed during this authoring pass; axes, scale bars, captions, equations and bibliography inspected. No new plot digitization.','asset_hashes':{a['id']:a['public_asset_sha256'] for a in assets}},'compatibility':{'site_validator':'Unmodified current build_paper_reviews.validate executed using exact private record and asset copies','renderer':'Unmodified source-evidence.mjs exercised in a minimal DOM harness; not an actual browser layout or interaction audit','negative_checks':['missing page','wrong crop hash','false matched-SI scope','unresolved record']},'independent_reader_audit':False,'browser_qa':False,'site_modified':False,'canonical_modified':False,'ledger_modified':False,'remaining_gates':['Independent reader scientific audit by a different agent','Molecular and apparatus binding qualification','Site integration, actual browser checks and publication']}
write('proposal-validation.json',out)
print(json.dumps({'status':out['status'],'checks':len(checks),'reader_sha256':out['reader_sha256'],'render_checks':render['check_count']}))
