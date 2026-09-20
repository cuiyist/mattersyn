import pathlib,json,hashlib,sys,copy
E=pathlib.Path(__file__).resolve().parents[1];O=pathlib.Path(__file__).parent
bound={};checks=[];fail=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):bound[str(p)]=sha(p);return json.loads(p.read_text(encoding='utf-8-sig'))
def ck(x,name):checks.append(name);fail.extend([] if x else [name])
def diff(a,b,p=''):
    if type(a)!=type(b):return [p]
    if isinstance(a,dict):
        out=[]
        for k in sorted(set(a)|set(b)):
            path=p+'/'+k.replace('~','~0').replace('/','~1')
            out.extend([path] if k not in a or k not in b else diff(a[k],b[k],path))
        return out
    if isinstance(a,list):
        if len(a)!=len(b):return [p]
        return sum((diff(x,y,p+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
    return [] if a==b else [p]
oldfreeze=read(E/'proposal-freeze-v2.json')
for x in oldfreeze['bound_files']:
    p=pathlib.Path(x['path']);ck(p.exists() and sha(p)==x['sha256'],'preserved-v2 '+str(p))
records={};changed=[]
for p in sorted((E/'canonical-proposal/v3').glob('evans-2010-*.json')):
    old=read(E/'canonical-proposal/v2'/p.name);new=read(p);records[p.stem]=new
    if sha(p)!=sha(E/'canonical-proposal/v2'/p.name):changed.append(p.stem)
    for k in ['materials','stocks','products','measurements','sources','quality','condition_options','intended_target','structure_assets']:
        ck(old[k]==new[k],p.stem+' unchanged '+k)
ck(changed==['evans-2010-topse-distillation'],'exactly one changed record')
rid=changed[0];old=read(E/'canonical-proposal/v2'/f'{rid}.json');new=records[rid]
actual=diff(old,new)
ck(set(actual)=={'/material_states','/operations/1/description','/operations/1/outputs','/operations/2/inputs/0','/revision'},'exact canonical delta paths')
states={x['id']:x for x in new['material_states']};base=rid+'-op-1-state';cuts=rid+'-op-2-state';pot=rid+'-op-2-pot-state';residue=rid+'-op-3-state'
ck(states[pot]['parent_ids']==[base],'pot from charged mixture')
ck(states[cuts]['parent_ids']==[base],'cuts from charged mixture')
ck(states[residue]['parent_ids']==[pot],'residue from residual pot')
ck(new['operations'][1]['outputs']==[cuts,pot],'separate distillation outputs')
ck(new['operations'][2]['inputs']==[pot],'retention consumes residual pot')
ck(all(a['depends_on']==b['depends_on'] for a,b in zip(old['operations'],new['operations'])),'chronology unchanged')
ck(all(a['parameters']==b['parameters'] for a,b in zip(old['operations'],new['operations'])),'operation quantities unchanged')
ro=read(E/'public-review-proposal/v2/evans2010.json');rn=read(E/'public-review-proposal/v3/evans2010.json')
readerchanges=diff(ro,rn)
expected=['/reader_sections/0/items/85/notes/1','/reader_sections/0/items/85/operation_context/material_flow_labels/'+pot,'/reader_sections/0/items/85/operation_context/outputs','/reader_sections/0/items/85/text','/reader_sections/0/items/86/notes/0','/reader_sections/0/items/86/operation_context/inputs/0','/reader_sections/0/items/86/operation_context/material_flow_labels/'+pot,'/reader_sections/0/items/86/operation_context/material_flow_labels/'+cuts]
ck(set(readerchanges)==set(expected),'exact eight reader delta paths')
for so,sn in zip(ro['reader_sections'],rn['reader_sections']):
    for a,b in zip(so['items'],sn['items']):
        for k in ['id','facts','sample_scope','evidence','canonical_links','source_audit_unit_ids','source_fact_ids','original_assets']:
            ck(a[k]==b[k],a['id']+' unchanged '+k)
        if 'operation_context' not in b:continue
        c=b['operation_context'];r=records[c['record_id']];op=next(x for x in r['operations'] if x['id']==c['operation_id'])
        for k in ['stage','branch','depends_on','environment','inputs','outputs','retained_fraction','endpoint','optional_inputs']:
            ck(c[k]==op.get(k,[] if k=='optional_inputs' else None),b['id']+' operation '+k)
        names={x['id']:x['name'] for category in ['materials','stocks','material_states'] for x in r[category]}
        for k,v in c['material_flow_labels'].items():ck(v==names[k],b['id']+' flow label '+k)
sys.path.insert(0,r'[local path redacted]')
import dataset_lib
for rid,r in records.items():
    errors=dataset_lib.validate_record(r);ck(not errors,'schema '+rid+' '+repr(errors));ck(not any(x['eligible'] for x in dataset_lib.eligibility(r).values()),'zero admission '+rid)
report={'schema':'mattersyn-independent-proposal-delta/1','reviewer':'/root/peng1998_reader_assets','status':'passed' if not fail else 'failed','check_count':len(checks),'failures':fail,'changed_records':changed,'canonical_delta_paths':actual,'reader_delta_paths':readerchanges,'resolved_finding':'EVANS-PROP-01','manual_resolution':'Read the new residual-pot state, its parent, both output identities, retained-fraction input and all eight revised reader paths. They now distinguish the residual material from the collected cuts and agree with the actual SI page 6 image revisited during this audit.','bound_files':bound}
path=O/'delta-v3.json';assert not path.exists();path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print(report['status'],report['check_count'],report['failures'],sha(path))
