"""Independent reader pointer, quantity, sample, asset and private-projection checks."""
from pathlib import Path
import json,hashlib,re,sys
sys.stdout.reconfigure(encoding='utf-8')
A=Path(__file__).resolve().parent;B=A.parent
VERSION=sys.argv[1] if len(sys.argv)>1 else 'v1'
C=B/'canonical-proposal'/VERSION;P=B/'public-review-proposal'/VERSION
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ptr(o,path):
    for k in path.strip('/').split('/') if path else []:
        k=k.replace('~1','/').replace('~0','~');o=o[int(k)] if isinstance(o,list) else o[k]
    return o
checks=[]
def ck(label,ok,detail=None):checks.append({'check':label,'passed':bool(ok),**({'detail':detail} if not ok else {})})
records={p.stem:load(p) for p in C.glob('lian-*.json')}
r=load(P/'lian2021.json');coverage=load(P/'source-item-coverage.json');bindings=load(P/'reader-bindings-proposal.json')
items=[i for s in r['reader_sections'] for i in s['items']];byid={i['id']:i for i in items}
source=load(B/'source-facts.json');inventory=load(B/'source-inventory.json')
source_assets={a['id']:a for a in load(B/'original-assets-manifest.json')['assets']}
ck('unique 224 reader cards',len(items)==len(byid)==224)
ck('reader hash binding',sha(P/'lian2021.json')==bindings['reader_sha256'])
ck('reader bound canonical manifest',sha(C/'record-manifest.json')==coverage['private_canonical_manifest_sha256'])
ck('complete source unit universe',set(coverage['source_units'])=={x['id'] for x in inventory['inventory_units']})
ck('complete source fact universe',set(coverage['source_facts'])=={x['id'] for x in source['facts']})
def fields(obj,path=''):
    if isinstance(obj,dict):
        if 'value' in obj and 'status' in obj:
            yield path,obj;return
        for k,v in obj.items():yield from fields(v,path+'/'+str(k).replace('~','~0').replace('/','~1'))
    elif isinstance(obj,list):
        for j,v in enumerate(obj):yield from fields(v,path+'/'+str(j))
expected={(rid,p):q for rid,record in records.items() for p,q in fields(record)}
seen={}
def sample_links(obj,label):
    links=obj.get('sample_scope',{}).get('canonical_sample_links',[])
    ck(label+' unique sample links',len(links)==len({(x['record_id'],x['sample_id']) for x in links}))
    for link in links:
        try:p=ptr(records[link['record_id']],link['json_pointer']);ok=p['sample_id']==link['sample_id']
        except (KeyError,IndexError,ValueError):ok=False
        ck(label+' sample pointer '+link['sample_id'],ok)
    return {(l['record_id'],l['sample_id']) for l in links}
for i in items:
    links=sample_links(i,i['id'])
    ck('prose not raw JSON '+i['id'],not i['text'].lstrip().startswith(('{','[')))
    for l in i.get('canonical_links',[]):
        try:ptr(records[l['record_id']],l['json_pointer']);valid=True
        except (KeyError,IndexError,ValueError):valid=False
        ck('canonical link '+i['id']+l['json_pointer'],valid)
    for f in i.get('facts',[]):
        key=(f['canonical_record_id'],f['json_pointer']);canonical=ptr(records[key[0]],key[1]);seen[key]=f
        ck('exact canonical payload '+f['id'],f['canonical_quantity']==canonical)
        ck('no field training approval '+f['id'],f.get('training_eligible') is False)
        for k in ('unit','status','approximate'):
            ck('display '+f['id']+' '+k,f.get(k)==canonical.get(k,False if k=='approximate' else None))
        value=canonical.get('value')
        if value is None:
            lo,hi=canonical.get('minimum'),canonical.get('maximum')
            if lo is not None and hi is not None:value=str(lo)+'–'+str(hi)
            elif lo is not None:value=('> ' if canonical.get('minimum_exclusive') else '≥ ')+str(lo)
            elif hi is not None:value=('< ' if canonical.get('maximum_exclusive') else '≤ ')+str(hi)
            else:value='Not reported'
        if isinstance(value,str) and value.startswith('{'):
            try:value=json.loads(value)
            except ValueError:pass
        ck('display value '+f['id'],f.get('value')==value,[f.get('value'),value])
        if key[1].startswith('/measurements/'):
            m=ptr(records[key[0]],key[1].rsplit('/',1)[0])
            ck('field specimen '+f['id'],f.get('sample_id')==m['sample_id'])
            ck('item contains exact measurement specimen '+f['id'],(key[0],m['sample_id']) in links)
ck('all canonical field coverage',set(seen)==set(expected),{'missing':sorted(set(expected)-set(seen)),'extra':sorted(set(seen)-set(expected))})
for row in coverage['canonical_field_map']:
    item=byid[row['reader_item_id']]
    ck('field index '+row['reader_fact_id'],any(f['id']==row['reader_fact_id'] and f['canonical_record_id']==row['record_id'] and f['json_pointer']==row['json_pointer'] for f in item['facts']))
for unit,ids in coverage['source_units'].items():ck('unit reachability '+unit,bool(ids) and all(x in byid for x in ids))
for fact,rows in coverage['source_facts'].items():
    for row in rows:ck('fact reachability '+fact+row['source_pointer'],any(f['id']==row['reader_fact_id'] for f in byid[row['reader_item_id']]['facts']))
cells={cell['id']:cell for t in load(B/'source-tables.json')['tables'] for row in t['rows'] for cell in row['cells']}
ck('all 891 table cells in reader',set(cells)==set(coverage['table_cells']))
for cid,row in coverage['table_cells'].items():ck('table field '+cid,any(f['id']==row['reader_fact_id'] and f['json_pointer']==row['pointer'] for f in byid[row['reader_item_id']]['facts']))
for rid,record in records.items():
    for op in record['operations']:ck('operation reachable '+rid+op['id'],rid+'::'+op['id'] in bindings['operation_to_reader_item'])
    for m in record['measurements']:ck('measurement reachable '+rid+m['id'],rid+'::'+m['id'] in coverage['measurement_to_reader_item'])
    for key,slot,idkey in [('material_to_reader_item','materials','id'),('stock_to_reader_item','stocks','id'),('product_to_reader_item','products','sample_id')]:
        for obj in record[slot]:ck('slot reachable '+rid+obj[idkey],rid+'::'+obj[idkey] in bindings[key])
assets=[a for key in ['figures','tables','schemes','equations','source_notes'] for a in r[key] if a.get('public_asset')]
ck('53 unique selected crop paths',len(assets)==53 and len({a['public_asset'] for a in assets})==53)
for a in assets:
    sid=a['id'].removeprefix('lian2021-');sourceasset=source_assets[sid]
    ck('asset bytes '+sid,sha(sourceasset['path'])==sourceasset['sha256']==a['public_asset_sha256'])
    ck('asset page '+sid,a['page']==sourceasset['pdf_page'] and a['document_role']==sourceasset['source_role'])
    ck('asset selected only '+sid,sourceasset['whole_source_page'] is False and a['public_asset'].startswith('assets/figures/lian2021/'))
    ck('asset no approval '+sid,a['training_eligible'] is False and a['reader_render_verified'] is False)
    sample_links(a,'asset '+sid)
    ck('asset record references '+sid,set(a['sample_links'])<=set(records))
    ck('asset source hash '+sid,a['asset_provenance']['source_sha256']==sourceasset['source_sha256'])
    ck('crop bounds preserved '+sid,a['asset_provenance']['crop_normalized']==sourceasset['bbox_normalized'])
text=json.dumps(r,ensure_ascii=False)
ck('no absolute local source paths',not re.search(r'[A-Z]:[\\/]|file://',text))
ck('no wholepage/fulltext attachments',not any(x in text for x in ['complete-source-payloads','firstPagePreviewPrivate','source-render/','private/text/','text_cache','render_cache']))
ck('no publication or training admission',r['training_eligible'] is False and r['publication_status']!='published' and r['source_review_promoted'] is False)
report={'auditor':'/root/peng1998_reader_assets','status':'mechanical_checks_only_not_final_audit','version':VERSION,'reader_sha256':sha(P/'lian2021.json'),'checks':checks,'check_count':len(checks),'failures':[c for c in checks if not c['passed']],'counts':{'reader_items':len(items),'canonical_fields':len(expected),'reader_unique_fields':len(seen),'selected_crops':len(assets)}}
(A/('reader-checks-'+VERSION+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':len(checks),'failures':len(report['failures']),'first_failures':report['failures'][:12]},ensure_ascii=False,indent=2))
