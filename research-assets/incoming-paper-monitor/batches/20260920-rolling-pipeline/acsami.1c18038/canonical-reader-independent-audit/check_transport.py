"""Independent read-only transport checks; a manual frozen-package audit is separate."""
from pathlib import Path
import json, hashlib, sys
sys.stdout.reconfigure(encoding='utf-8')
A=Path(__file__).resolve().parent
B=A.parent
VERSION=sys.argv[1] if len(sys.argv)>1 else 'v1'
C=B/'canonical-proposal'/VERSION
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ptr(obj,path):
    for part in path.strip('/').split('/') if path else []:
        part=part.replace('~1','/').replace('~0','~')
        obj=obj[int(part)] if isinstance(obj,list) else obj[part]
    return obj
checks=[]
def ck(label,ok,detail=None):
    checks.append({'check':label,'passed':bool(ok),**({'detail':detail} if not ok else {})})
source=load(B/'source-facts.json'); inventory=load(B/'source-inventory.json')
tables=load(B/'source-tables.json')['tables']; cm=load(C/'source-to-field-coverage.json')
records={p.stem:load(p) for p in C.glob('lian-*.json')}
facts={f['id']:f for f in source['facts']}
cells={c['id']:(t,row,c) for t in tables for row in t['rows'] for c in row['cells']}
manifest=load(C/'record-manifest.json')
for r in manifest['records']: ck('canonical hash '+r['record_id'],sha(r['path'])==r['sha256'])
ck('source freeze bound',sha(B/'package-freeze.json')==cm['source_freeze_sha256'])
ck('source independent audit bound',sha(B/'source-independent-audit/independent-audit-v2.json')==manifest['independent_source_audit_sha256'])
lossless=load(C/'lossless-source-map.json')
for key in ['facts','materials','stocks','protocols','samples','tables','figures','schemes','equations','references','conflicts','gaps']:
    ck('lossless source '+key,lossless[key]==source[key])
ck('57 fact universe',len(facts)==57 and set(facts)=={x['source_fact_id'] for x in cm['facts']})
ck('167 unit universe',{x['id'] for x in inventory['inventory_units']}=={x['source_unit_id'] for x in cm['source_units']} and len(cm['source_units'])==167)
ck('891 cell universe',len(cells)==891 and set(cells)=={x['source_cell_id'] for x in cm['table_cells']})
def quantity(src,dst,label):
    if not isinstance(src,dict):
        ck(label+' literal claim',dst.get('value')==src);return
    # Text, ratio and mesh source tokens remain categorical, never a coerced scalar.
    if src.get('status') in ('reported_text','reported_ratio_parts','reported_mesh') or src.get('unit')=='identifier':
        ck(label+' literal context',dst.get('value')==src.get('raw_text'),[dst.get('value'),src.get('raw_text')])
        ck(label+' categorical evidence',bool(dst.get('evidence')))
        return
    for key in ['raw_text','unit','approximate']:
        expected=src.get(key)
        if key=='unit' and expected is None: expected=''  # canonical schema uses an empty string for an unstated unit
        ck(label+' '+key,expected==dst.get(key),[expected,dst.get(key)])
    if src.get('unit') is None: ck(label+' missing unit explained','unit' in dst.get('qualifier','').lower())
    value=src.get('value'); low=high=None
    if src.get('range'):
        low,high=src['range']['min'],src['range']['max'];value=None
    comp=src.get('comparison')
    if comp in ('<','<=','≤'): high=value;value=None
    if comp in ('>','>=','≥'): low=value;value=None
    for key,expected in [('value',value),('minimum',low),('maximum',high)]:
        ck(label+' '+key,dst.get(key)==expected,[dst.get(key),expected])
    ck(label+' exclusive lower',bool(dst.get('minimum_exclusive'))==(comp=='>'))
    ck(label+' exclusive upper',bool(dst.get('maximum_exclusive'))==(comp=='<'))
    if src.get('uncertainty') is not None:
        ck(label+' uncertainty',str(src['uncertainty']) in dst.get('qualifier',''))
        if src.get('uncertainty_definition'):ck(label+' uncertainty definition',src['uncertainty_definition'] in dst.get('qualifier',''))
    ck(label+' printed scale',str(src.get('printed_to_value_scale',1)) in dst.get('basis',''))
    ck(label+' source evidence',bool(dst.get('evidence')))
for row in cm['facts']:
    src=facts[row['source_fact_id']]
    ck('fact has bindings '+src['id'],bool(row['canonical_bindings']))
    for binding in row['canonical_bindings']:
        target=ptr(records[binding['record_id']],binding['pointer'])
        original=ptr(src,binding['source_pointer'])
        quantity(original,target,src['id']+binding['source_pointer']+' '+binding['record_id']+binding['pointer'])
        if binding['pointer'].startswith('/measurements/'):
            measurement=ptr(records[binding['record_id']],binding['pointer'].rsplit('/',1)[0])
            ck('fact specimen '+src['id']+binding['pointer'],measurement['sample_id']==src['sample_scope'])
for row in cm['table_cells']:
    table,srow,cell=cells[row['source_cell_id']]
    for binding in row['canonical_bindings']:
        r=records[binding['record_id']];target=ptr(r,binding['pointer'])
        quantity(cell,target,cell['id'])
        measurement=ptr(r,binding['pointer'].rsplit('/',1)[0])
        expected=table['sample_scope']
        if table['id']=='table-s1': expected={'A':'bulk-a-crystal','B':'bulk-b-crystal'}[cell['column']]
        ck('table specimen '+cell['id'],measurement['sample_id']==expected,[measurement['sample_id'],expected])
for row in cm['source_units']:
    ck('unit has bindings '+row['source_unit_id'],bool(row['canonical_bindings']))
    for binding in row['canonical_bindings']:
        try: ptr(records[binding['record_id']],binding['pointer']);ok=True
        except (KeyError,IndexError,ValueError):ok=False
        ck('unit pointer '+row['source_unit_id']+binding['pointer'],ok)
for rid,r in records.items():
    ck('no tasks '+rid,r['quality']['requested_tasks']==[])
    ck('author approval pending '+rid,r['quality']['review_status']=='imported_unreviewed')
    ck('no new atomistic assets '+rid,r['structure_assets']==[])
    ids={x['id'] for key in ['materials','stocks','material_states'] for x in r[key]}
    ops={o['id'] for o in r['operations']}; samples={p['sample_id'] for p in r['products']}
    for op in r['operations']:
        ck('I/O '+rid+op['id'],set(op['inputs']+op['outputs'])<=ids)
        ck('dependencies '+rid+op['id'],set(op['depends_on'])<=ops)
        ck('retained output '+rid+op['id'],not op.get('retained_fraction') or op['retained_fraction'] in op['outputs'])
    for state in r['material_states']:ck('lineage '+rid+state['id'],set(state['parent_ids'])<=ids)
    for m in r['measurements']:ck('measurement sample '+rid+m['id'],m['sample_id'] in samples)
    source_materials={x['id']:x for x in source['materials']}
    for material in r['materials']:
        original=source_materials[material['id']]
        ck('material name '+rid+material['id'],material['name']==original['name'])
        ck('material source caveat '+rid+material['id'],original['scope_note'] in material['notes'])
report={'status':'mechanical_checks_only_not_final_audit','auditor':'/root/peng1998_reader_assets','version':VERSION,'checks':checks,'check_count':len(checks),'failures':[x for x in checks if not x['passed']],'record_hashes':{rid:sha(C/(rid+'.json')) for rid in records}}
(A/('transport-checks-'+VERSION+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':len(checks),'failures':len(report['failures']),'first_failures':report['failures'][:10]},ensure_ascii=False,indent=2))
