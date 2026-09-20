"""Independent read-only checks for frozen Heo canonical/reader v1."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,collections,re
A=Path(__file__).resolve().parent;V=A.parent/'v1';H=V.parents[1];S=H.parents[4]/'recipe-atlas'
checks=[];bound={};cache={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):p=Path(p).resolve();bound[str(p)]=sha(p);return p
def load(p):
    p=bind(p)
    if str(p) not in cache:cache[str(p)]=json.loads(p.read_bytes())
    return cache[str(p)]
def ck(scope,label,ok,detail=None):checks.append({'scope':scope,'check':label,'passed':bool(ok),'detail':detail})
def ptr(x,p):
    for t in p.lstrip('/').split('/') if p else []:
        t=t.replace('~1','/').replace('~0','~');x=x[int(t)] if isinstance(x,list) else x[t]
    return x
def walk(x,p=''):
    yield p,x
    if isinstance(x,dict):
        for k,v in x.items():yield from walk(v,p+'/'+k.replace('~','~0').replace('/','~1'))
    elif isinstance(x,list):
        for i,v in enumerate(x):yield from walk(v,p+'/'+str(i))
package=load(V/'proposal-package-manifest.json')
for rel,h in package['files'].items():
    p=V/rel;ck('frozen package',rel,p.is_file() and sha(bind(p))==h)
for rel,h in package['external_input_hashes'].items():
    p=H/rel;ck('external frozen input',rel,p.is_file() and sha(bind(p))==h)
for name,expected in {
    '10.1021_jp0219348.pdf':'03e6f3be5375a0e2023a6850c1c6931904be8e3c85c37e0c30effdf6ecf73c01',
    '10.1021_jp0219348_si_1.pdf':'3b2e262af1932ed04cfddd596958c92d89c37099ab9dad8c4ce1f11254d4acc6',
}.items():
    source=Path('[local path redacted]')/name
    ck('original source identity',name,source.is_file() and sha(bind(source))==expected)
records={p.stem:load(p) for p in (V/'canonical-drafts').glob('*.json')}
reader=load(V/'public-review-proposal/heo2003.json');items=[i for s in reader['reader_sections'] for i in s['items']];byitem={i['id']:i for i in items}
facts=load(H/'source-facts.json');inv=load(H/'source-inventory.json');tables=load(H/'main-tables.json');si=load(H/'si-complete-candidate/all-reflections.json')
for n in ('source-facts.json','source-inventory.json','main-tables.json','si-complete-candidate/all-reflections.json','si-complete-candidate/all-reflections.tsv','si-complete-candidate/independent-audit.json','si-complete-candidate/package-freeze.json'):
    ck('exact source payload',n,(H/n).read_bytes()==(V/'source-payloads'/n).read_bytes())
sys.path.insert(0,str(S/'scripts'))
try:
    import dataset_lib
    schema_runtime_issue=None
except (PermissionError,ImportError) as error:
    dataset_lib=None;schema_runtime_issue=str(error)
bind(S/'scripts/dataset_lib.py');bind(S/'scripts/schema_definition.py')
for rid,r in records.items():
    if dataset_lib:
        errors=dataset_lib.validate_record(r);ck(rid,'Current canonical schema/semantic validation',not errors,errors)
    ck(rid,'No structure asset or requested training tasks',not r['structure_assets'] and not r['quality'].get('requested_tasks',[]))
    ck(rid,'Source group and primary DOI correct',r['lineage']['source_group']=='heo2003' and r['sources'][0]['doi']=='10.1021/jp0219348')
    ck(rid,'All measurement sample IDs resolve',all(m['sample_id'] in {p['sample_id'] for p in r['products']} for m in r['measurements']))
    ck(rid,'No measured batch ID fabricated',all(p['batch_id'] is None for p in r['products']))
ck('counts','10 records /1 route /3 procedures /6 contexts',len(records)==10 and collections.Counter(r['record_type'] for r in records.values())=={'literature_protocol':1,'procedure':3,'observation':6})
for field,n in [('operations',14),('materials',14),('stocks',1),('measurements',473),('products',188)]:ck('counts',field,sum(len(r[field]) for r in records.values())==n)
ck('counts','372 reader items with unique IDs',len(items)==len(byitem)==372)

fc=load(V/'source-fact-coverage.json');ck('source fact coverage','114 unique complete facts',len(fc['bindings'])==114 and {b['source_fact_id'] for b in fc['bindings']}=={f['id'] for f in facts['facts']})
for b in fc['bindings']:
    source=ptr(facts,b['json_pointer']);ck(b['source_fact_id'],'Source payload exact',source==b['source_payload'])
    for l in b['canonical_links']:
        q=ptr(records[l['record_id']],l['json_pointer']);value=ptr(facts,l['source_value_pointer'])
        esd=re.fullmatch(r'([-+]?\d+(?:\.\d+)?)\((\d+)\)',value) if isinstance(value,str) else None
        exact=q['value']==value or (esd and q['value']==float(esd.group(1)) and q.get('raw_text')==value and 'estimated standard deviation' in q.get('qualifier',''))
        ck(b['source_fact_id'],'Canonical value exact or raw-preserving ESD split',exact and l['source_value']==value)
        m=ptr(records[l['record_id']],l['json_pointer'].rsplit('/',1)[0])
        ck(b['source_fact_id'],'Source scope retained',m['sample_id']==l['sample_id'] and m['conditions']==source['sample_scope'])
        ck(b['source_fact_id'],'Original status explicitly retained',('Source status: '+source['status']+'.') in (q.get('note','')+q.get('basis','')+q.get('qualifier','')))
        if isinstance(value,(int,float)) and not isinstance(value,bool):
            unit=source['unit'] or ''
            if b['source_fact_id']=='heo2003-refinement-stages':unit='dimensionless' if l['source_value_pointer'].endswith('/R1') else 'atoms per conventional unit cell'
            if b['source_fact_id']=='heo2003-table2-fixed-sites':unit='site multiplicity' if l['source_value_pointer'].endswith('/1') else 'atoms per conventional unit cell'
            ck(b['source_fact_id'],'Unit/approximation retained',q.get('unit','')==unit and q.get('approximate')==source.get('approximate',False))

tc=load(V/'table-field-coverage.json');allquantitypaths={p for p,x in walk(tables) if isinstance(x,dict) and {'raw','value','status','unit'}<=x.keys()}
# The package's 209 count is table-row quantities. Fourteen duplicate
# condition-conflict quantities and the oxygen-radius derivation reference
# are auxiliary metadata, retained by the exact source payload checks above.
auxiliarypaths={p for p in allquantitypaths if p.startswith('/conflicts/') or p=='/tables/4/derivation/oxygen_reference'}
quantitypaths=allquantitypaths-auxiliarypaths
ck('table coverage','15 auxiliary quantities retained in exact source payload',len(auxiliarypaths)==15 and (H/'main-tables.json').read_bytes()==(V/'source-payloads/main-tables.json').read_bytes())
ck('table coverage','209 table quantity objects independently enumerated',len(quantitypaths)==209 and {b['source_quantity_pointer'] for b in tc['quantity_bindings']}==quantitypaths,{'enumerated':len(quantitypaths),'missing_bindings':sorted(quantitypaths-{b['source_quantity_pointer'] for b in tc['quantity_bindings']}),'extra_bindings':sorted({b['source_quantity_pointer'] for b in tc['quantity_bindings']}-quantitypaths)})
for b in tc['quantity_bindings']:
    src=ptr(tables,b['source_quantity_pointer']);q=ptr(records[b['record_id']],b['json_pointer'])
    ck(b['source_quantity_pointer'],'Raw quantity payload exact',src==b['source_quantity'])
    ck(b['source_quantity_pointer'],'Canonical scalar/null unit and raw precision retained',q.get('value')==src['value'] and q.get('unit','')==(src['unit'] or '') and q.get('raw_text','')==(src.get('raw_cell') or src['raw'] or ''))
    ck(b['source_quantity_pointer'],'Source sample association resolves',ptr(records[b['record_id']],b['json_pointer'].rsplit('/',1)[0])['sample_id']==b['sample_id'])
for b in tc['rows']:
    ck(b['json_pointer'],'Entire table row retained',ptr(tables,b['json_pointer'])==b['row_payload'])
ck('table coverage','198 populated numeric /11 blank quantities retained',sum(ptr(tables,p)['value'] is not None for p in quantitypaths)==198 and sum(ptr(tables,p)['value'] is None for p in quantitypaths)==11)

ic=load(V/'source-inventory-coverage.json');rc=load(V/'public-review-proposal/source-item-coverage.json')
ck('inventory coverage','Canonical and reader maps contain same433units',ic['units']==rc['units'] and len(ic['units'])==433)
sources={'source-facts.json':facts,'source-inventory.json':inv,'main-tables.json':tables}
for u in ic['units']:
    if u['source_file'] not in sources:sources[u['source_file']]=load(H/u['source_file'])
    src=ptr(sources[u['source_file']],u['source_json_pointer'])
    payload=u['source_payload'];same=src==payload
    if u['source_unit_id'].endswith('-metadata') or u['source_unit_id']=='inventory-identity':same=all(k in src and v==src[k] for k,v in payload.items())
    if u['source_unit_id']=='si-aggregate-reflections':same=payload['counts']==si['counts'] and (V/payload['exact_payload_path']).read_bytes()==(H/'si-complete-candidate/all-reflections.json').read_bytes()
    ck(u['source_unit_id'],'Exact inventoried object or labeled metadata projection',same)
    ck(u['source_unit_id'],'Every mapped reader item exists',bool(u['item_ids']) and all(i in byitem for i in u['item_ids']))
    for l in u['canonical_links']:ptr(records[l['record_id']],l['json_pointer'])
for category,key in [('equation_bindings','chemical_equations'),('reference_bindings','references')]:
    ck(category,'All source objects bound',len(ic[category])==len(inv[key]))
    for b in ic[category]:
        src=ptr(inv,b['json_pointer']);ck(b['json_pointer'],'Exact source payload',src==b['source_payload'])
        val=src.get('formula',src.get('raw_bibliographic_text'))
        for l in b['canonical_links']:ck(b['json_pointer'],'Canonical literal source statement',ptr(records[l['record_id']],l['json_pointer'])['value']==val)

mc=load(V/'public-review-proposal/canonical-measurement-coverage.json');rfacts=[f for i in items for f in i.get('facts',[])]
ck('reader facts','535 typed fact bindings',len(rfacts)==len(mc['bindings'])==535)
for i in items:
    ck(i['id'],'No training eligibility assigned',i['training_eligible'] is False)
    for l in i['canonical_links']:
        try:ptr(records[l['record_id']],l['json_pointer']);valid=True
        except (KeyError,IndexError,ValueError):valid=False
        ck(i['id'],'Canonical JSON pointer resolves '+l['json_pointer'],valid)
    links=i['sample_scope'].get('canonical_sample_links',[])
    ck(i['id'],'No duplicate sample link',len(links)==len({(l['record_id'],l['sample_id']) for l in links}))
    for l in links:
        matches=[p for p in records[l['record_id']]['products'] if p['sample_id']==l['sample_id']];ck(i['id'],'Sample link resolves to exactly one canonical product',len(matches)==1)
    for f in i.get('facts',[]):
        q=ptr(records[f['canonical_record_id']],f['json_pointer'])
        ck(i['id'],'Exact typed canonical quantity '+f['id'],q==f['canonical_quantity'])
        ck(i['id'],'Fact display status/unit/approximation agree',f['status']==q['status'] and f.get('unit','')==q.get('unit','') and f.get('approximate',False)==q.get('approximate',False))
for b in mc['bindings']:
    f=next(f for f in byitem[b['item_id']]['facts'] if f['id']==b['fact_id'])
    ck(b['fact_id'],'Coverage pointer and reader fact agree',f['json_pointer']==b['json_pointer'] and f['canonical_record_id']==b['record_id'] and f['canonical_quantity']==b['canonical_quantity'])
meas={(rid,f'/measurements/{i}/value') for rid,r in records.items() for i,m in enumerate(r['measurements'])}
boundq={(f['canonical_record_id'],f['json_pointer']) for f in rfacts}
ck('reader measurement coverage','All473 canonical measurements reach typed reader facts',meas<=boundq,sorted(meas-boundq))

sc=load(V/'si-row-coverage.json');ck('SI aggregate','1209 rows and full exact payload preserved',len(sc['rows'])==len(si['rows'])==1209 and sc['counts']==si['counts'])
for b,row in zip(sc['rows'],si['rows']):
    ck(row['row_id'],'Full row identity/index/cell mappings retained',ptr(si,b['source_json_pointer'])==row and b['source_row_id']==row['row_id'] and b['source_hkl']==row['hkl'] and b['cell_ids']==[c['cell_id'] for c in row['cells']])
    ck(row['row_id'],'Reader reflection context exists without new per-row recipe',b['reader_item_id'] in byitem and b['canonical_context_record_id']=='heo-2003-refinement-comparison' and 'no per-row synthesis sample' in b['mapping_role'])
numcells=[c for row in si['rows'] for c in row['cells'] if c['evidence']['column_key']!='marker'];unresolved=[c for c in numcells if c['numeric_value'] is None]
ck('SI aggregate','7254 positions /7252 resolved /2 sign nulls',len(numcells)==7254 and len(unresolved)==2 and {c['cell_id'] for c in unresolved}=={'si-p11-R-r035-Fobs2','si-p12-L-r012-Fcal2'})
ck('SI aggregate','Two exact unresolved-cell payloads retained',sc['unresolved_cells']==si['unresolved_cells'])
ck('SI aggregate','137 negative intensities and one zero retained',sum(c['evidence']['column_key']=='Fobs2' and c['numeric_value'] is not None and c['numeric_value']<0 for c in numcells)==137 and sum(c['evidence']['column_key']=='Fobs2' and c['numeric_value']==0 for c in numcells)==1)
sia=load(H/'si-complete-candidate/independent-audit.json')
ck('SI aggregate','Separate independent audit hash authority retained',reader['si_aggregate_evidence']['audit_sha256']==sha(H/'si-complete-candidate/independent-audit.json') and sc['independent_aggregate_audit_sha256']==sha(H/'si-complete-candidate/independent-audit.json'))

assets=load(V/'public-review-proposal/reader-original-assets-manifest.json')['assets']
ck('original assets','39 original asset IDs',len(assets)==39)
for aid,x in assets.items():
    ck(aid,'Exact original asset hash',Path(x['path']).is_file() and sha(bind(x['path']))==x['sha256'])
    projected=V/'reader-compatibility-projection/dist/assets/figures/heo2003'/Path(x['path']).name
    ck(aid,'Private projected image exact',projected.is_file() and sha(projected)==x['sha256'])
for i in items:
    for x in i.get('original_assets',[]):
        aid=x.get('id',x.get('asset_id'));ck(i['id'],'Original asset resolves '+str(aid),aid in assets)
ck('scope gates','Canonical/reader/model/viewer/browser/integration not preapproved',all(x is False for x in reader['presentation_gates'].values()) and reader['training_eligible'] is False and reader['independent_audit']['status']=='pending')
ck('scope gates','No structure arrays or CIF accepted by canonical records',all(not r['structure_assets'] for r in records.values()))
api=V/'public-review-proposal'/reader['si_aggregate_evidence']['audit_path']
ck('dependency paths','Reader SI audit path resolves relative to its JSON file',api.is_file(),str(api.resolve()))
fail=[c for c in checks if not c['passed']]
report={'schema':'mattersyn.heo_v1_transport_checks/1','at':datetime.now(timezone.utc).isoformat(),'author':'/root/peng1998_reader_assets','auditor':'/root/backlog_eta','status':'passed' if not fail else 'findings','checks':checks,'counts':{'checks':len(checks),'failed':len(fail)},'findings':fail,'bound_files':bound,'schema_runtime_issue':schema_runtime_issue,'scope':'Mechanical exact transport and independent pointer/quantity/coverage checks. Manual scientific findings are recorded separately; this is not a new SI-cell visual audit.'}
(A/'transport-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':len(checks),'failed':len(fail),'findings':fail[:40]},ensure_ascii=False))
