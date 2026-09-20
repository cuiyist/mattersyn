"""Independent read-only transport and projection checks; outputs only beside this script."""
import json, hashlib, pathlib, re, collections, sys
E=pathlib.Path(__file__).resolve().parents[1]
VERSION=sys.argv[1] if len(sys.argv)>1 else 'v2'
C=E/'canonical-proposal'/VERSION
P=E/'public-review-proposal'/VERSION
OUT=pathlib.Path(__file__).parent
checks=collections.Counter(); failures=[]; bound={}
def ck(ok,cat,detail):
    checks[cat]+=1
    if not ok: failures.append({'category':cat,'detail':detail})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    p=pathlib.Path(p);bound[str(p)]=sha(p);return json.loads(p.read_text(encoding='utf-8-sig'))
def ptr(o,p):
    for key in p.lstrip('/').split('/') if p else []:
        key=key.replace('~1','/').replace('~0','~');o=o[int(key)] if isinstance(o,list) else o[key]
    return o
def walk(o,p=''):
    yield p,o
    if isinstance(o,dict):
        for k,v in o.items():yield from walk(v,p+'/'+k.replace('~','~0').replace('/','~1'))
    elif isinstance(o,list):
        for k,v in enumerate(o):yield from walk(v,p+'/'+str(k))
def prose_equal(a,b):
    if isinstance(a,str) and isinstance(b,str):return re.sub(r'\s+','',a)==re.sub(r'\s+','',b)
    if type(a)!=type(b):return a==b
    if isinstance(a,dict):return set(a)==set(b) and all(prose_equal(a[k],b[k]) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(prose_equal(x,y) for x,y in zip(a,b))
    return a==b
def display_matches(f,q):
    value=q.get('value');display=f['value']
    if value is not None:
        if f['presentation_kind']=='curated_source_inventory':return prose_equal(json.loads(value),display)
        return display==value
    if q.get('minimum') is not None and q.get('maximum') is None:
        return display==('> ' if q.get('minimum_exclusive') else '≥ ')+str(q['minimum'])
    if q.get('maximum') is not None and q.get('minimum') is None:
        return display==('< ' if q.get('maximum_exclusive') else '≤ ')+str(q['maximum'])
    if q.get('minimum') is not None and q.get('maximum') is not None:
        return display==('(' if q.get('minimum_exclusive') else '[')+str(q['minimum'])+', '+str(q['maximum'])+(')' if q.get('maximum_exclusive') else ']')
    return display=='Not reported' and q['status']=='not_reported'
freeze=read(E/('proposal-freeze-'+VERSION+'.json'))
for x in freeze['bound_files']:
    p=pathlib.Path(x['path']);ck(p.exists() and sha(p)==x['sha256'],'freeze_hash',str(p))
    if p.exists():bound[str(p)]=sha(p)
source=read(E/'source-extraction-revision-2/source-facts.json')
inventory=read(E/'source-inventory.json');sourceaudit=read(E/'source-scientific-audit.json')
facts={f['id']:f for f in source['facts']}
records={p.stem:read(p) for p in sorted(C.glob('evans-2010-*.json'))}
coverage=read(C/'source-to-field-coverage.json');lossless=read(C/'lossless-source-map.json')
ck(lossless['facts']==source['facts'],'lossless','effective revision2 facts')
for k in ['units','materials','stocks','sample_lineage','procedures','tables','equations','references','source_conflicts','missingness']:
    ck(lossless[k]==inventory[k],'lossless',k)
ck(set(facts)=={x['source_fact_id'] for x in coverage['facts']},'source_fact_coverage','all457facts')
sourcebindingcount=0
for row in coverage['facts']:
    f=facts[row['source_fact_id']]
    ck(bool(row['canonical_bindings']),'source_fact_coverage',f['id'])
    for b in row['canonical_bindings']:
        sourcebindingcount+=1;q=ptr(records[b['record_id']],b['pointer']);v=ptr(f['value'],b['source_value_pointer'])
        ck(q.get('value')==v or (v==[] and q.get('value')=='[]'),'source_value',{'fact':f['id'],'binding':b,'expected':str(v)[:150],'actual':str(q.get('value'))[:150]})
        if not b['source_value_pointer']:
            for k in ['minimum','maximum','unit','approximate','minimum_exclusive','maximum_exclusive']:
                if k in q:ck(q[k]==f.get(k) or (k=='unit' and f.get(k) is None and q[k]==''),'source_quantity',{'fact':f['id'],'field':k,'binding':b})
            if 'raw_text' in q:ck(q['raw_text']==f.get('raw_text') or (f.get('raw_text') is None and q['raw_text']==''),'source_raw',f['id'])
        text=' '.join(str(q.get(k,'')) for k in ['basis','note','qualifier'])
        ck(f['sample_scope'] in text,'source_scope',{'fact':f['id'],'binding':b})
        ck(f['source_unit_id'] in text,'source_unit_qualifier',{'fact':f['id'],'binding':b})
        ck(bool(q.get('evidence')),'source_evidence',{'fact':f['id'],'binding':b})
ck({x['id'] for x in inventory['units']}=={x['source_unit_id'] for x in coverage['source_units']},'source_unit_coverage','all198units')
for row in coverage['source_units']:
    ck(bool(row['canonical_bindings']),'source_unit_coverage',row['source_unit_id'])
    for b in row['canonical_bindings']:ck(ptr(records[b['record_id']],b['pointer']) is not None,'source_unit_pointer',b)
for b in coverage['source_objects']:ck(ptr(records[b['record_id']],b['pointer']) is not None,'source_object_pointer',b)
measurementset=set();opset=set();allquantityset=set()
for rid,r in records.items():
    ck(r['record_id']==rid,'record_identity',rid)
    ck(r['quality']['review_status']=='imported_unreviewed','admission',rid)
    ck(r['quality']['requested_tasks']==[],'admission',rid+' tasks')
    ids=[x['id'] for k in ['materials','stocks','material_states','operations'] for x in r[k]]
    ck(len(ids)==len(set(ids)),'internal_ids',rid)
    materialids={x['id'] for k in ['materials','stocks','material_states'] for x in r[k]}
    opids={x['id'] for x in r['operations']};samples={x['sample_id'] for x in r['products']}
    ck(len(samples)==len(r['products']),'sample_ids',rid)
    for o in r['operations']:
        opset.add((rid,o['id']))
        ck(set(o.get('inputs',[])+o.get('optional_inputs',[])+o.get('outputs',[]))<=materialids,'operation_resolve',rid+' '+o['id'])
        ck(set(o.get('depends_on',[]))<=opids,'operation_dependency',rid+' '+o['id'])
    for s in r['material_states']:ck(set(s.get('parent_ids',[]))<=materialids,'state_parent_resolve',rid+' '+s['id'])
    for ix,m in enumerate(r['measurements']):
        measurementset.add((rid,'/measurements/'+str(ix)+'/value'))
        ck(m.get('sample_id') in samples,'measurement_sample',rid+' '+m['id'])
    for p,x in walk(r):
        if isinstance(x,dict) and 'value' in x and 'status' in x and 'evidence' in x:
            allquantityset.add((rid,p))
    ck(not r['structure_assets'],'no_coordinate_admission',rid)
reader=read(P/'evans2010.json');rcov=read(P/'source-item-coverage.json');bindings=read(P/'reader-bindings-proposal.json')
items=[i for s in reader['reader_sections'] for i in s['items']];itemmap={i['id']:i for i in items}
ck(len(items)==len(itemmap),'reader_id_unique','items')
rfields=set();rfieldlocations={};rmeasurementset=set()
for i in items:
    ck(i['training_eligible'] is False,'admission',i['id'])
    sl=i.get('sample_scope',{}).get('canonical_sample_links',[])
    pairs=[(x['record_id'],x['sample_id']) for x in sl]
    ck(len(pairs)==len(set(pairs)),'sample_link_unique',i['id'])
    for x in sl:
        product=ptr(records[x['record_id']],x['json_pointer']);ck(product['sample_id']==x['sample_id'],'reader_sample_pointer',i['id'])
    for x in i.get('canonical_links',[]):ck(ptr(records[x['record_id']],x['json_pointer']) is not None,'reader_link',i['id'])
    for f in i['facts']:
        key=(f['canonical_record_id'],f['json_pointer']);q=ptr(records[key[0]],key[1]);rfields.add(key);rfieldlocations.setdefault(key,[]).append((i['id'],f['id']))
        ck(f['canonical_quantity']==q,'reader_exact_quantity',f['id'])
        ck(display_matches(f,q),'reader_display_value',f['id'])
        for k in ['unit','status','approximate']:
            ck(f.get(k)==q.get(k,False if k=='approximate' else None),'reader_display_semantics',f['id']+' '+k)
        ck(f.get('training_eligible') is False,'admission',f['id'])
        if key in measurementset:
            rmeasurementset.add(key);m=ptr(records[key[0]],key[1].rsplit('/',1)[0]);ck(f.get('sample_id')==m['sample_id'],'reader_measurement_sample',f['id'])
ck(rmeasurementset==measurementset,'reader_measurement_complete',{'missing':sorted(measurementset-rmeasurementset)})
reader_required={x for x in allquantityset if not x[1].startswith('/intended_target/')}
ck(reader_required<=rfields,'reader_all_canonical_fields',{'missing':sorted(reader_required-rfields)})
for x in rcov['canonical_field_map']:
    key=(x['record_id'],x['json_pointer']);ck((x['reader_item_id'],x['reader_fact_id']) in rfieldlocations.get(key,[]),'reader_coverage_pointer',x)
ck(set(rcov['source_units'])=={x['id'] for x in inventory['units']},'reader_unit_complete','198')
for uid,ii in rcov['source_units'].items():
    ck(bool(ii),'reader_unit_complete',uid)
    for itemid in ii:ck(uid in itemmap[itemid]['source_audit_unit_ids'],'reader_unit_reverse',uid+' '+itemid)
ck(set(rcov['source_facts'])==set(facts),'reader_fact_complete','457')
for fid,bb in rcov['source_facts'].items():
    for b in bb:
        ck((b['reader_item_id'],b['reader_fact_id']) in rfieldlocations.get((b['record_id'],b['pointer']),[]),'reader_fact_pointer',fid)
ck(bindings['molecular_apparatus_bindings_approved'] is False and bindings['publication_approved'] is False,'admission','binding gates')
assets=read(E/'selected-original-assets.json')['assets'];assetmap={x['id']:x for x in assets}
publicassetrefs=[]
for p,x in walk(reader):
    if isinstance(x,dict) and 'public_asset' in x:
        publicassetrefs.append((p,x));aid=x['public_asset'].split('/')[-1].rsplit('.',1)[0]
        ck(aid in assetmap,'public_asset_allowlist',p)
        if aid in assetmap:
            a=assetmap[aid];ck(x.get('sha256',x.get('public_asset_sha256'))==a['sha256'],'public_asset_hash',p)
            ck(x['public_asset']=='assets/figures/evans2010/'+aid+'.png','public_asset_path',p)
            if 'document_role' in x:ck(x['document_role']==a['source_role'],'public_asset_role',p)
            if 'page' in x:ck(x['page']==a['pdf_page'],'public_asset_page',p)
            if 'asset_provenance' in x:
                v=x['asset_provenance'];ck(v['source_sha256']==a['source_sha256'] and v['crop_pdf_points']==a['crop_pdf_points'],'asset_provenance',p)
    if isinstance(x,str):
        ck(not re.search(r'(?i)([A-Z]:[[local path redacted]
for a in assets:
    path=pathlib.Path(a['path']);bound[str(path)]=sha(path);ck(sha(path)==a['sha256'],'actual_asset_bytes',a['id'])
ck({x['public_asset'].split('/')[-1].rsplit('.',1)[0] for _,x in publicassetrefs}==set(assetmap),'original_assets_complete','25')
for key in ['published','training_eligible']:ck(freeze[key] is False,'admission','freeze '+key)
for key in ['training_eligible','source_review_promoted']:ck(reader[key] is False,'admission','reader '+key)
for mat,rr in reader['material_evidence_records'].items():
    ck(set(rr)<=set(records),'material_record_resolve',mat)
    if mat in ['CdSe','PbSe']:ck('evans-2010-molecular9-structure' not in rr,'molecular_crystal_scope',mat)
report={'schema':'mattersyn-independent-proposal-checks/1','version':VERSION,'reviewer':'/root/peng1998_reader_assets','check_count':sum(checks.values()),'checks_by_category':dict(checks),'failures':failures,'counts':{'records':len(records),'operations':len(opset),'source_facts':len(facts),'source_bindings':sourcebindingcount,'reader_items':len(items),'reader_fields':len(rfields),'measurements':len(measurementset),'assets':len(assets)},'bound_files':bound,'limits':'Mechanical checks supplement independent manual source, specimen and process review; no browser/integration/molecular model approval.'}
(OUT/('mechanical-'+VERSION+'.json')).write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['bound_files','checks_by_category']},ensure_ascii=False,indent=2)[:10000])
