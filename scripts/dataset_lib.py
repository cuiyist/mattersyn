"""Validation and leakage-resistant, task-specific views. No source guesses."""
import hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.sites-runtime/python-packages'))
from jsonschema import Draft202012Validator
from schema_definition import SCHEMA
OPTICAL_FEATURES={'ambient_temperature_proxy','lead_oleate_stock_volume','ode_reaction_volume','oleylamine_volume','injection_temperature','bis_trimethylsilyl_sulfide_volume','ode_sulfur_stock_volume','chloride_high_temperature_concentration','chloride_60c_concentration'}

def optical_operation(r):
    return next((o for o in r['operations'] if o['action']=='published_experiment_features' and o['stage']=='synthesis' and OPTICAL_FEATURES <= o['parameters'].keys()),None)

def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def walk(value,path=''):
    if isinstance(value,dict):
        yield path,value
        for k,v in value.items(): yield from walk(v,path+'/'+k)
    elif isinstance(value,list):
        for i,v in enumerate(value): yield from walk(v,path+'/'+str(i))
def validate_record(r):
    errors=[f'{r.get("record_id","?")}: {e.json_path}: {e.message}' for e in Draft202012Validator(SCHEMA).iter_errors(r)]
    if errors:return errors
    rid=r['record_id'];sources={s['id'] for s in r['sources']}
    def fail(msg):errors.append(rid+': '+msg)
    if len(sources)!=len(r['sources']):fail('duplicate source IDs')
    if r['lineage']['source_group'] not in sources:fail('source group must resolve to a primary source')
    for name in ['materials','stocks','material_states','operations','products','measurements','structure_assets']:
        key={'products':'sample_id'}.get(name,'id');ids=[x[key] for x in r[name]]
        if len(set(ids))!=len(ids):fail('duplicate '+name+' IDs')
        if any(not str(x).strip() for x in ids):fail('blank '+name+' ID')
    if not sources or any(not x.strip() for x in sources):fail('blank or absent source IDs')
    material_ids={m['id'] for m in r['materials']};stock_ids={s['id'] for s in r['stocks']};state_ids={s['id'] for s in r['material_states']}
    known=material_ids|stock_ids|state_ids
    if len(known)!=len(material_ids)+len(stock_ids)+len(state_ids):fail('material/stock/state IDs must be distinct')
    op_ids={o['id'] for o in r['operations']};sample_ids={p['sample_id'] for p in r['products']};measurement_ids={m['id'] for m in r['measurements']}
    for path,value in walk(r):
        if 'evidence' in value:
            for ev in value['evidence']:
                if ev['source_id'] not in sources:fail(path+' unresolved source '+ev['source_id'])
        if 'value' in value and 'status' in value:
            numeric='unit' in value
            present=value['value'] is not None or (numeric and (value['minimum'] is not None or value['maximum'] is not None))
            if value['status'] in ['not_reported','not_applicable'] and present:fail(path+' missing status contains a value')
            if value['status'] not in ['not_reported','not_applicable'] and not present:fail(path+' known status lacks a value')
            if present and not value['evidence']:fail(path+' value has no provenance')
            if numeric:
                lo,hi=value['minimum'],value['maximum']
                if (lo is None)!=(hi is None):fail(path+' range must have both endpoints')
                if lo is not None and (lo>hi or value['value'] is not None):fail(path+' invalid or ambiguous range')
                for n in [value['value'],lo,hi]:
                    if n is not None and not math.isfinite(n):fail(path+' nonfinite quantity')
                if value['status']=='calculated' and not value['derivation']:fail(path+' calculation missing derivation')
    seen_ops=set()
    for op in r['operations']:
        for dep in op['depends_on']:
            if dep not in seen_ops:fail(op['id']+' dependency must precede operation: '+dep)
        for item in op['inputs']+op.get('optional_inputs',[])+op['outputs']:
            if item not in known:fail(op['id']+' unresolved material/state '+item)
        if op['retained_fraction'] and op['retained_fraction'] not in known:fail(op['id']+' unresolved retained fraction')
        for stock in r['stocks']:
            if stock['id'] in op['inputs']:
                for prep in stock['preparation_operation_ids']:
                    if prep not in seen_ops:fail(op['id']+' consumes stock before preparation '+prep)
        seen_ops.add(op['id'])
    for state in r['material_states']:
        for parent in state['parent_ids']:
            if parent not in known or parent==state['id']:fail(state['id']+' invalid state parent '+parent)
    def visit_state(sid,chain):
        if sid in chain:fail('cyclic material-state lineage '+sid);return
        state=next((x for x in r['material_states'] if x['id']==sid),None)
        if state:
            for p in state['parent_ids']:visit_state(p,chain|{sid})
    for sid in state_ids:visit_state(sid,set())
    for stock in r['stocks']:
        for c in stock['components']:
            if c['material_id'] not in material_ids:fail('stock unresolved chemical '+c['material_id'])
        for oid in stock['preparation_operation_ids']:
            if oid not in op_ids:fail('stock unresolved operation '+oid)
    for p in r['products']:
        if p['material_state_id'] is not None and p['material_state_id'] not in state_ids:fail('product unresolved material state')
        if p['parent_sample_id'] is not None and p['parent_sample_id'] not in sample_ids:fail('product unresolved parent sample')
        if p['recipe_link']=='explicit' and not p['link_evidence']:fail('explicit product link needs source evidence')
        for ev in p['link_evidence']:
            if ev['source_id'] not in sources:fail('unresolved link source')
    for m in r['measurements']:
        if m['sample_id'] not in sample_ids:fail('measurement unresolved sample')
        for dep in m['derives_from']:
            if dep not in measurement_ids or dep==m['id']:fail('measurement unresolved/cyclic derivation')
    for name,id_key,parent_key in [('measurements','id','derives_from'),('products','sample_id','parent_sample_id')]:
        nodes={x[id_key]:x for x in r[name]}
        def visit(node,chain):
            if node in chain:fail('cyclic '+name+' lineage '+node);return
            value=nodes.get(node,{}).get(parent_key,[])
            for dep in (value if isinstance(value,list) else [value] if value else []):visit(dep,chain|{node})
        for node in nodes:visit(node,set())
    for s in r['structure_assets']:
        if s['sample_id'] is not None and s['sample_id'] not in sample_ids:fail('structure unresolved sample')
        if s['eligible_as_measured_label'] and (s['role']!='measured_sample' or s['sample_id'] is None):fail('reference/illustration cannot become measured label')
    return errors

def chemical_signature(r):
    def quantities(qs):return {k:{z:q[z] for z in ['value','minimum','maximum','unit','status','basis']} for k,q in qs.items()}
    def sorted_rows(rows):return sorted(rows,key=lambda x:json.dumps(x,sort_keys=True))
    identities={m['id']:(m['name'].lower(),m['formula'],m['role'],m['identity']) for m in r['materials']}
    return digest({'material':r['material']['formula'],'method':r['method'],'materials':sorted_rows([(identities[m['id']],quantities(m['quantities'])) for m in r['materials']]),'stocks':sorted_rows([{'components':sorted_rows([(identities[c['material_id']],quantities(c['quantities'])) for c in s['components']]),'concentrations':quantities(s['concentrations'])} for s in r['stocks']]),'alternatives':sorted_rows([quantities(o['parameters']) for o in r['condition_options']]),'operations':[(o['action'],o['stage'],o['optional'],o['branch'],quantities(o['parameters']),o['environment']['value'],o['endpoint']['value']) for o in r['operations']]})

def eligibility(r):
    reviewed=r['quality']['review_status']=='source_reviewed';duplicate=r['lineage']['duplicate_of'] is not None
    precursors=[m for m in r['materials'] if m['role'] in ['metal_precursor','chalcogen_precursor','halide_precursor','nonmetal_precursor'] and m['stage']=='synthesis']
    explicit={p['sample_id'] for p in r['products'] if p['recipe_link']=='explicit'}
    sizes=[m for m in r['measurements'] if m['sample_id'] in explicit and m['property']=='diameter' and m['value']['value'] is not None]
    measured=[s for s in r['structure_assets'] if s['eligible_as_measured_label'] and s['sample_id'] in explicit]
    base=reviewed and not duplicate
    unresolved_protocol=any(v.get('status')=='not_reported' for _,v in walk({'materials':r['materials'],'stocks':r['stocks'],'operations':r['operations']}))
    optical_verified=r['quality']['review_status'] in ['source_reviewed','structured_data_verified'] and not duplicate and r['quality']['experimental_outcome']!='reported_failure' and optical_operation(r) is not None and any(m['sample_id'] in explicit and m['property']=='absorption_peak' and m['value']['value'] is not None for m in r['measurements'])
    candidates={
      'precursor_selection':(base and bool(precursors),'Reviewed synthesis precursors are identified.' if precursors else 'No identified synthesis precursor set.'),
      'partial_protocol':(base and bool(r['operations']),'Preserve missing fields; this is literature protocol supervision, not a complete SOP.'),
      'size_conditioned_recipe':(base and bool(sizes),'Requires an explicitly linked quantitative diameter; author-derived size remains labeled.'),
      'exact_structure_recipe':(base and bool(measured) and not r['quality']['missing_fields'] and not unresolved_protocol,'Requires measured sample coordinates, explicit recipe linkage and no unresolved required fields.'),
      'success_prediction':(False,'Literature and heterogeneous historical failure markers do not establish a calibrated success model.'),
      'optical_outcome':(optical_verified,'Published numeric optical benchmark with explicit row linkage. Failure placeholders are excluded from continuous targets.')}
    return {k:{'eligible':bool(v[0]) and k in r['quality']['requested_tasks'],'reason':v[1] if base or k=='optical_outcome' else 'Source review required, or structured-data verification supports only a separately gated benchmark task.'} for k,v in candidates.items()}

def build_groups(records):
    parent={r['record_id']:r['record_id'] for r in records}
    def root(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    def join(a,b):
        a,b=root(a),root(b)
        if a!=b:parent[max(a,b)]=min(a,b)
    tokens={}
    for r in records:
        rid=r['record_id'];l=r['lineage']
        keys=['source:'+l['source_group'],'recipe:'+l['recipe_family'],'hash:'+chemical_signature(r)]
        if l['batch_id']:keys.append('batch:'+l['batch_id'])
        for s in r['sources']:
            # Shared background references do not merge experiments; main source_group controls source splitting.
            if s['id']==l['source_group'] and s['doi']:keys.append('doi:'+s['doi'].lower())
        for key in keys:
            if key in tokens:join(rid,tokens[key])
            else:tokens[key]=rid
        for key in ['parent_record_id','duplicate_of']:
            if l[key] in parent:join(rid,l[key])
    return {rid:'group-'+digest(root(rid))[:12] for rid in parent}

def training_view(r,task):
    if not eligibility(r).get(task,{}).get('eligible'):raise ValueError('Record is not eligible for '+task)
    # Explicit allowlist: contextual figures, intuition, measured structure illustrations and outcome text never enter recipe inputs.
    inputs={'composition':r['material']['formula'],'method':r['method']}
    output={}
    if task=='optical_outcome':
        inputs={'composition':r['material']['formula'],'features':{k:{f:q[f] for f in ['value','unit','status']} for k,q in optical_operation(r)['parameters'].items() if k in OPTICAL_FEATURES}}
        explicit={p['sample_id'] for p in r['products'] if p['recipe_link']=='explicit'}
        m=next(m for m in r['measurements'] if m['sample_id'] in explicit and m['property']=='absorption_peak' and m['value']['value'] is not None)
        output={'absorption_peak':{k:m['value'][k] for k in ['value','unit','status']}}
    elif task=='precursor_selection':
        output={'precursors':[{'name':m['name'],'formula':m['formula'],'role':m['role']} for m in r['materials'] if m['role'] in ['metal_precursor','chalcogen_precursor','halide_precursor','nonmetal_precursor'] and m['stage']=='synthesis']}
    else:
        output={'materials':r['materials'],'stocks':r['stocks'],'material_states':r['material_states'],'operations':[o for o in r['operations'] if o['stage']!='characterization'],'condition_options':r['condition_options'],'missing_fields':r['quality']['missing_fields']}
    if task=='size_conditioned_recipe':
        linked={p['sample_id']:p for p in r['products'] if p['recipe_link']=='explicit'}
        m=next(m for m in r['measurements'] if m['sample_id'] in linked and m['property']=='diameter' and m['value']['value'] is not None)
        inputs['requested_diameter']={k:m['value'][k] for k in ['value','unit','approximate','status']};inputs['phase']=linked[m['sample_id']]['phase']['value']
        inputs['size_evidence_method']=m['technique']
    if task=='exact_structure_recipe':
        explicit={p['sample_id'] for p in r['products'] if p['recipe_link']=='explicit'}
        inputs['measured_structures']=[s for s in r['structure_assets'] if s['eligible_as_measured_label'] and s['sample_id'] in explicit]
    return {'record_id':r['record_id'],'task':task,'input':inputs,'output':output,'provenance':[{'doi':s['doi'],'url':s['url'],'reuse_status':s['reuse_status']} for s in r['sources']]}

def fmt(q):
    if q['status'] in ['not_reported','not_applicable']:return q['status'].replace('_',' ').capitalize()
    value=f"{q['minimum']:g}–{q['maximum']:g}" if q['minimum'] is not None else f"{q['value']:g}"
    return ('≈' if q['approximate'] else '')+value+' '+q['unit']+(' · '+q['qualifier'] if q['qualifier'] else '')
