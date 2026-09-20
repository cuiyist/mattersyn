"""Unapproved Friedfeld canonical draft, entirely inside canonical-proposal."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import json,hashlib,re,sys,argparse
sys.dont_write_bytecode=True
C=Path(__file__).resolve().parent;F=C.parent
argspec=argparse.ArgumentParser();argspec.add_argument('--output-version',default='draft-v2');argspec.add_argument('--source-overlay');argspec.add_argument('--source-audit');argspec.add_argument('--source-audit-sha256');args=argspec.parse_args()
assert re.fullmatch('draft-v[0-9]+',args.output_version)
O=C/args.output_version;O.mkdir(exist_ok=True)
assert not(O/'package-freeze.json').exists()and not(O/'author-checkpoint-source-v1.json').exists(),'Preserve frozen canonical versions and earlier checkpoints.'
S=Path('[local path redacted]');sys.path.insert(0,str(S/'scripts'))
from record_helpers import record,source,fact,qty,material,operation,state,product,measurement
from dataset_lib import validate_record,eligibility,build_groups
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):
    p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(x):return re.sub('[^a-z0-9]+','-',str(x).lower()).strip('-')
def key(x):return norm(x).replace('-','_')
def esc(x):return str(x).replace('~','~0').replace('/','~1')
def compact(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def resolve(x,p):
    for z in p.strip('/').split('/')if p else[]:
        z=z.replace('~1','/').replace('~0','~');x=x[int(z)]if isinstance(x,list)else x[z]
    return x
replacement={};overlay=None;audit=None
if args.source_overlay:
    overlay=Path(args.source_overlay);replacement=read(overlay/'effective-file-map.json')['replacements']
    for x in replacement.values():assert sha(x['path'])==x['sha256']
def effective(name):return Path(replacement[name]['path'])if name in replacement else F/name
if args.source_audit:
    audit=Path(args.source_audit);assert args.source_audit_sha256 and sha(audit)==args.source_audit_sha256
    assert read(audit)['status']=='passed','Require a distinct passed source audit before an effective-source final draft.'
D=read(effective('source-facts.json'));I=read(effective('source-inventory.json'));T=read(effective('source-tables.json'));A=read(effective('original-assets-manifest.json'))
FR=read(F/'package-freeze.json');EXPECTED='7599e47c1ef1d43d56b2f4f835e4b550a1ef652aecca2e9dd8e593abc5769c04'
assert sha(F/'package-freeze.json')==EXPECTED
for p,h in FR['bound_files'].items():assert sha(F/p)==h['sha256'],p
if overlay:
    OF=read(overlay/'package-freeze.json')
    for p,h in OF['bound_files'].items():assert sha(p)==h,p
    EXPECTED=sha(overlay/'package-freeze.json')
PLAN=read(C/'mapping-draft-v1/record-boundary-plan.json');MAP=read(C/'mapping-draft-v1/source-to-schema-map.json')
SID=D['source_id'];PRE='friedfeld-2019-';FM={x['id']:x for x in D['facts']};MM={x['id']:x for x in D['materials']};ST={x['id']:x for x in D['stocks']};SC={x['id']:x for x in D['sample_contexts']};PP={x['id']:x for x in D['protocols']}
CON={x['id']:x for x in D['conflicts']};GAP={x['id']:x for x in D['missingness']};PAY={'source-facts.json':D,'source-tables.json':T}
OWN={x['source_fact_id']:x['primary_record_id'].removeprefix(PRE)for x in MAP['facts']}
SOWN={x['sample_id']:x['record_id'].removeprefix(PRE)for x in MAP['sample_contexts']}
TO={x['table_id']:x['record_id'].removeprefix(PRE)for x in MAP['table_cells']}
EO={x['equation_id']:x['record_id'].removeprefix(PRE)for x in MAP['equations']}
FO={x['figure_id']:[r.removeprefix(PRE)for r in x['record_ids']]for x in MAP['figures']}
R={};FL={i:[]for i in FM};UL={u['id']:[]for u in I['units']};OB=[];TC=[];OP=[];TYPED=[]
def E(es):return[{'source_id':SID,'locator':e['document_role'].upper()+' PDF p. '+str(e['pdf_page'])+' (printed '+str(e.get('printed_page'))+'), '+e['locator']+'; original source SHA256 '+e['source_sha256']}for e in es]
def fe(i):return E(FM[SID+'-'+i]['evidence'])
def qualify(ids):return ' '.join(i+': '+(CON.get(i)or GAP.get(i))['description']for i in ids if i in CON or i in GAP)
def Q(q,scope='',basis='',force=None,numeric=False):
    ev=E(q['evidence']);qual=qualify(q.get('conflict_ids',[])+q.get('gap_ids',[]))
    extra={k:q[k]for k in ['uncertainty','ordered_endpoints']if q.get(k)is not None}
    if extra:qual+=' Preserved source qualifiers: '+compact(extra)+'.'
    qual+=' Raw source status: '+q['status']+'.'
    if q['status'].startswith('reported_'):
        if not numeric:return fact(q['raw_text'],ev,note='Scope: '+scope+'. '+qual+' '+basis)
        return qty(None,q.get('unit')or'',ev,'not_reported',raw_text=q['raw_text'],qualifier='Reported qualitative token, with no numeric value: '+q['raw_text']+'. '+qual,basis=scope+' '+basis)
    v=q['value'];lo=(q.get('range')or{}).get('min');hi=(q.get('range')or{}).get('max');cmp=q.get('comparison')
    if cmp in['<','<=']:hi=v;v=None
    if cmp in['>','>=']:lo=v;v=None
    status=force or ('author_derived'if q['status']in['source_calculation','author_calculated','author_derived']else'reported')
    if v is None and lo is None and hi is None:status='not_reported'
    return qty(v,q.get('unit')or'',ev,status,minimum=lo,maximum=hi,approximate=q.get('approximate',False),raw_text=q['raw_text'],
        qualifier=qual,basis='Source scope: '+scope+'. '+basis,minimum_exclusive=cmp=='>'if cmp in['>','>=']else None,maximum_exclusive=cmp=='<'if cmp in['<','<=']else None)
STATUS=('The frozen effective source extraction passed distinct independent source audit. Canonical/reader review remains pending; this private draft has no scientific promotion.'if audit else'Private canonical/reader draft from frozen source author extraction. Independent source audit and canonical/reader review are separate and pending; no scientific promotion is inferred.')
COMMON=[STATUS,'Context identifiers are not physical batch IDs or independent replicates.','No current QD atomic coordinates, supplied CIF, exact structure–recipe pair or training admission.','Cited prior cluster/precursor syntheses do not fill missing current recipes.']
SRC=source(SID,D['doi'],D['title'],'; '.join(D['authors']),D['year'],si='Matched 25-page supplied SI; author completed reading and viewing; independent source audit pending.')
SRC['main_status']='Eight supplied main pages; author completed reading and viewing; independent source audit pending.'
if audit:
    SRC['main_status']='All eight supplied main pages passed distinct source audit; canonical/reader review is separate.'
    SRC['si_status']='All 25 matched SI pages passed distinct source audit; canonical/reader review is separate.'
for cfg in PLAN['records']:
    k=cfg['record_id'].removeprefix(PRE);formula='PhCH2-13CO2H'if k in['labeled-acid-synthesis','acid-nmr']else'InP'if k not in['source-context','source-materials','cited-phosphine-context']else'Study source context'
    rr=record(PRE+k,'Friedfeld et al. (2019) · '+cfg['title'],formula,'InP cluster conversion',cfg['title'],deepcopy(SRC),'Exact source document/page/figure locators',cfg['proposed_record_type'])
    rr['schema_version']='1.3.0';rr['lineage'].update(source_group=SID,recipe_family=SID+'-cluster-conversion-study',parent_record_id=PRE+'conversion-representative'if cfg['proposed_record_type']=='protocol_variant'else None)
    rr['intended_target']['composition']=fact(cfg['intended_target_proposal'],fe('identity'),note='Source-scoped intended target only; unassigned observation records have no invented target.')
    rr['quality'].update(review_status='imported_unreviewed',review_scope=STATUS,requested_tasks=[],experimental_outcome='not_established',missing_fields=COMMON+cfg['notes'],conflicts=[])
    rr['context_links']=[{'label':'Source document reader draft','url':'/paper-review.html?id='+SID,'relation':'private_unapproved_reader'}]
    R[k]=rr
def bindobj(cat,sourceid,r,ptr,sourceptr=None):
    b={'category':cat,'source_id':sourceid,'record_id':r['record_id'],'pointer':ptr}
    if sourceptr:b['source_pointer']=sourceptr
    OB.append(b);return b
def sample(r,sid,es,label=None):
    if not any(x['sample_id']==sid for x in r['products']):
        src=SC.get(sid);p=product(sid,src['reported_whole_composition']if src else None,E(es),link='general_context',notes=['A source context is not a new physical replicate or an exact cross-technique aliquot join.'])
        p['source_sample_label']=label or(src['label']if src else sid)
        if src:p['notes'].append(src['physical_batch_join'])
        if sid=='phenylacetate-reference':p['notes'].append('Composition and atomistic structure originate in cited prior work; no current coordinate file is supplied.')
        r['products'].append(p)
    return sid
def addm(r,mid,stage='precursor_preparation'):
    if any(m['id']==mid for m in r['materials']):return mid
    m=MM[mid];q={}
    for f in D['facts']:
        for v in f['quantities']:
            if(mid in['indium-acetate','myristic-acid','phenylacetic-acid']and v['meaning']==mid.replace('-',' ')+' purity')or(mid=='labeled-co2'and'enrichment'in v['meaning']):q['reported_'+key(v['meaning'])]=Q(v,mid)
    r['materials'].append(material(mid,m['name'],m['source_formula_or_abbreviation'],m['role'],stage,E(m['evidence']),quantities=q,notes=[m['scope_note'],'Printed identity/formula is not an approved graph, conformer or solution coordination model.']))
    bindobj('material',mid,r,f'/materials/{len(r["materials"])-1}');return mid
for mid in MM:addm(R['source-materials'],mid)
def adds(r,sid,changed=False):
    s=ST[sid];actual='msc-injection-varied'if changed else sid
    if any(x['id']==actual for x in r['stocks']):return actual
    cs=[]
    for c in s['components']:
        qs={}
        for v in c.get('amount_quantities',[]):
            if changed and v['meaning']in['MSC mass','MSC amount']:continue
            qs[key(v['meaning'])]=Q(v,sid,force='inherited'if changed else None,basis='Inherited common solvent volume; changed solute charge is not reported.'if changed else'')
        if changed and c['material_id']=='msc-myristate':qs['condition_specific_mass']=qty(None,'mg',E(s['evidence']),qualifier='Changed-concentration mass not supplied; representative charge excluded.')
        cs.append({'material_id':addm(r,c['material_id']),'quantities':qs})
    conc={key(v['meaning']):Q(v,sid)for v in s['quantities']if v.get('unit')in['M','mM']}
    if sid.endswith('-additive'):conc['stock_concentration']=qty(None,'M',E(s['evidence']),qualifier='Source does not report stock concentration; reaction equivalents are separate conditions.')
    prep=['sonicate-msc']if sid=='msc-injection'else[]
    x={'id':actual,'name':s['name'].replace('Representative','Condition-specific')if changed else s['name'],'components':cs,'concentrations':conc,'preparation_operation_ids':prep,
       'scope':s['scope_note']+' '+s['preparation']+' Stock preparation volume and storage conditions are unreported. '+('Representative solute charge explicitly excluded from this concentration variant.'if changed else''),'evidence':E(s['evidence'])}
    r['stocks'].append(x);bindobj('stock',sid,r,f'/stocks/{len(r["stocks"])-1}');return actual
for sm in MAP['stocks']:
    for rid in sm['proposed_record_ids']:adds(R[rid.removeprefix(PRE)],sm['source_id'])
adds(R['conversion-concentration'],'msc-injection',True)
EXTERNAL={'liquid-nitrogen','dry-ice','acetone'}
RETAIN={'distill-solvent':'distilled-reaction-residue','transfer-purify':'purified-product-fractions','acid-extract':'ether-extracts','acid-wash-dry':'dried-organic-solution','acid-filter-evaporate':'crude-acid','acid-isolate':'acid-isolated'}
STATE_KIND={'growth-data':'analysis_data','reaction-mixture':'reaction_batch','growing-mixture':'reaction_batch','preinjection-mixture':'mixture','heated-baseline-mixture':'mixture','distilled-reaction-residue':'fraction','solvent-distillate':'fraction','purified-product-fractions':'sample_set','ether-extracts':'fraction','aqueous-raffinate':'fraction','mother-liquor':'fraction','acid-isolated':'product','nmr-labeled':'product','nmr-acid-exchange':'sample_set','nmr-indium-exchange':'sample_set'}
def stateadd(r,sid,parents=(),kind='sample_set',name=None):
    if not any(s['id']==sid for s in r['material_states']):r['material_states'].append(state(sid,name or sid.replace('-',' '),list(dict.fromkeys(parents)),kind))
    return sid
for cfg in PLAN['records']:
    if not cfg['source_protocol_id']:continue
    k=cfg['record_id'].removeprefix(PRE);r=R[k];pr=PP[cfg['source_protocol_id']];produced={};outmap={}
    for oi,so in enumerate(pr['operations']):
        oid=so['id'];ins=[];optional=[];notes=[];qtys={};changed=k=='conversion-concentration';inherited=k.startswith('conversion-')and k!='conversion-representative'
        conv=lambda s:'msc-injection-varied'if changed and s=='msc-injection'else s
        for z0 in so['inputs']:
            z=conv(z0)
            if z=='dry-flask':continue
            if z=='selected-additive-stock':
                sid='myristic-acid-additive'if k=='conversion-acid-additive'else'indium-myristate-additive'if k=='conversion-indium-additive'else None
                if sid:optional.append(adds(r,sid))
                notes.append('Only the selected additive is used; the zero-equivalent control has no additive.');continue
            if z in EXTERNAL or(oid=='acid-quench'and z=='water'):
                addm(r,z,'precursor_preparation');notes.append(MM[z]['name']+' belongs to an external cooling bath, not the reaction charge.');continue
            if oid=='acid-charge'and z=='labeled-co2':addm(r,z);notes.append('The CO2 bulb is attached here; its contents enter during the following condensation.');continue
            if z in MM:ins.append(addm(r,z))
            elif z in ST or z=='msc-injection-varied':ins.append(z)
            elif z in outmap:ins.append(outmap[z])
            else:ins.append(stateadd(r,z,kind='sample_set',name='Separate source specimen/context: '+z.replace('-',' ')))
        if oid=='acid-condense':ins.append(addm(r,'labeled-co2'))
        # Distinguish the prepared stock state from its stock identifier.
        outs=[]
        for raw in so['outputs']:
            if raw=='dry-flask':continue
            z=conv(raw);z=z+'-prepared-state'if z in {s['id']for s in r['stocks']}else z
            parents=[i for i in ins if i!='nitrogen']
            kind='analysis_data'if raw.endswith('-data')else STATE_KIND.get(raw,'mixture')
            if oid in['nmr-analyze','uvvis-analyze','tem-analyze','xrd-analyze','tga-analyze','dsc-analyze','optical-analysis-analyze','kinetic-analysis-analyze','scherrer-analysis-analyze','acid-nmr-analyze']:kind='analysis_data'
            if oid=='acid-filter-evaporate':
                stateadd(r,'acid-filtered-solution',parents,'fraction','Filtered organic solution before evaporation');parents=['acid-filtered-solution']
                notes.append('Filter retains the organic filtrate, then evaporation retains the nonvolatile crude acid; no aqueous or drying-agent fraction is retained as product.')
            stateadd(r,z,parents,kind);outs.append(z);outmap[raw]=z
        for qi,v in enumerate(so['quantities']):
            if changed and v['meaning']in['MSC mass','MSC amount']:notes.append('Representative '+v['meaning']+' is excluded; this variant has unreported condition-specific injection charge.');continue
            if oid in['add-labeled-acid','add-labeled-indium']or(oid=='pretreat-msc'and'time'in v['meaning']):notes.append('Alternative comparison level: '+v['meaning']+' = '+v['raw_text']+' '+str(v['unit'])+'.');continue
            if oid=='nmr-analyze'and'Figure4'in v['meaning']:notes.append('The literal Figure 4 202 Hz caption is separately retained as source evidence; it is not a universal instrument setting.');continue
            pk=key(v['meaning']);qtys[pk]=Q(v,k,basis='Inherited common procedure, not a separately reported run-specific measurement.'if inherited else'',force='inherited'if inherited else None,numeric=True)
            TYPED.append({'source_file':'source-facts.json','source_pointer':f'/protocols/{D["protocols"].index(pr)}/operations/{oi}/quantities/{qi}','record_id':r['record_id'],'pointer':f'/operations/{oi}/parameters/{esc(pk)}'})
        if changed and oid=='sonicate-msc':qtys['condition_specific_msc_mass']=qty(None,'mg',E(so['evidence']),qualifier='Changed-concentration injection mass not reported.')
        stage='characterization'if pr['kind'].startswith(('measurement','analysis'))or oid.endswith('-analyze')else'surface_exchange'if k in['exchange-acid','exchange-indium']else'precursor_preparation'if k in['labeled-acid-synthesis','labeled-msc-cited']or oid in['dry-flask','sonicate-msc']else'workup'if oid in['distill-solvent','transfer-purify']else'synthesis'
        if oid.startswith('acid-')and oid in['acid-quench','acid-acidify','acid-extract','acid-wash-dry','acid-filter-evaporate','acid-layer','acid-crystallize','acid-isolate']:stage='workup'
        env=None
        if oid=='heat-baseline':env='Nitrogen; pressure not reported.'
        if oid=='acid-condense':env='Evacuated and then static vacuum; numerical pressure unreported.'
        if k in['tga','dsc']:notes.append('The general reaction-nitrogen rule does not specify this analysis atmosphere.')
        if pr['kind'].startswith(('measurement','analysis'))or oid.endswith('-analyze'):notes.append('Inputs represent separate specimens or data contexts; they are not physically pooled.')
        if inherited:notes.append('Procedure inherited explicitly from the representative conversion. Selected source-paired conditions remain alternatives, not a Cartesian experiment matrix.')
        if oid=='pretreat-msc':notes.append('30 h and 72 h descriptions remain distinct alternatives with unresolved cross-panel identity; subsequent conversion evidence is linked context.')
        if oid=='transfer-purify':notes.append('GPC-separated InP and In2O3 fractions are distinct; fraction windows, eluent and recoveries are not supplied. Output denotes a set, not a single pure mixture.')
        if oid=='dry-flask':notes.append('Apparatus drying has no material output or chemical precursor; the following charge depends on it.')
        desc=so['action']+'. '+' '.join(notes)+' Missing details: '+', '.join(so['missing_fields'])+'.'
        depends=list(dict.fromkeys(produced[x]for x in so['inputs']if x in produced))
        if oi>0 and oid not in['sonicate-msc']and pr['operations'][oi-1]['id']not in depends:depends.append(pr['operations'][oi-1]['id'])
        o=operation(oid,norm(so['action']),so['action'],E(so['evidence']),ins,outs,depends=depends,parameters=qtys,stage=stage,branch=k,description=desc,environment=fact(env,E(so['evidence'])),retained_fraction=RETAIN.get(oid))
        if optional:o['optional_inputs']=optional
        if oid=='acid-acidify':o['endpoint']=fact('pH 2',E(so['evidence']),note='Source acidification endpoint; no HCl transfer volume is inferred.')
        r['operations'].append(o);r['quality']['missing_fields']+=so['missing_fields'];OP.append({'source_protocol_id':pr['id'],'source_operation_id':oid,'record_id':r['record_id'],'pointer':f'/operations/{oi}','source_pointer':f'/protocols/{D["protocols"].index(pr)}/operations/{oi}','notes':notes})
        for z in so['outputs']:produced[z]=oid
        bindobj('operation',oid,r,f'/operations/{oi}',f'/protocols/{D["protocols"].index(pr)}/operations/{oi}')

# Source-defined alternatives, never Cartesian expansion across independent families.
def option(r,id,label,qs,es,scope):r['condition_options'].append({'id':id,'label':label,'parameters':{k:Q(v,scope,basis='Source-defined alternative; apply only this selected option.')for k,v in qs.items()},'evidence':E(es)})
for c in ['conversion-representative','conversion-acid-additive','conversion-indium-additive','conversion-concentration']:
    r=R[c]
    for sid,s in SC.items():
        match=(c=='conversion-representative'and re.fullmatch('temp-\\d+',sid))or(c=='conversion-acid-additive'and re.fullmatch('acid-\\d+-eq\\d+',sid))or(c=='conversion-indium-additive'and re.fullmatch('indium-\\d+-eq\\d+',sid))or(c=='conversion-concentration'and re.fullmatch('c-\\d+-[0-9p]+',sid))
        if not match:continue
        temp=int(sid.split('-')[1]);tf=FM[SID+'-temperature-series']if c!='conversion-concentration'else FM[SID+'-concentration-series']
        tq=next(q for q in tf['quantities']if q['unit']=='degC'and q['value']==temp);ps={'reaction_temperature':tq}
        if '-eq'in sid:
            eq=int(sid.split('-eq')[1]);ps['selected_additive_equivalents']=next(q for q in FM[SID+'-additive-series']['quantities']if q['value']==eq)
        if sid.startswith('c-'):
            cv=float(sid.split('-')[2].replace('p','.'));ps['initial_reaction_msc_concentration']=next(q for q in FM[SID+'-concentration-series']['quantities']if q['unit']=='mM'and q['value']==cv)
        option(r,sid,s['label'],ps,s['evidence'],sid);sample(r,sid,s['evidence'])
for k in['exchange-acid','exchange-indium']:
    for j,q in enumerate(PP[k]['operations'][0]['quantities']):option(R[k],k+'-level-'+str(j+1),q['raw_text']+' '+q['unit'],{'selected_addition':q},q['evidence'],k+' separate comparison level')
for fid in['pretreat','pretreat72']:
    f=FM[SID+'-'+fid];qs={key(q['meaning']):q for q in f['quantities']if q.get('unit')=='h'}
    option(R['low-temperature-pretreat'],fid,f['title'],qs,f['evidence'],f['sample_scope'])

def addmeasure(r,mid,sid,prop,value,es,tech='Source evidence',conditions=''):
    sample(r,sid,es);r['measurements'].append(measurement(mid,sid,prop,value,tech,E(es),conditions=conditions));return f'/measurements/{len(r["measurements"])-1}/value'
for sid,s in SC.items():
    r=R[SOWN[sid]];sample(r,sid,s['evidence']);pi=next(i for i,p in enumerate(r['products'])if p['sample_id']==sid);bindobj('sample_context',sid,r,f'/products/{pi}')
    if sid=='acid-isolated'and r is R['labeled-acid-synthesis']:
        r['products'][pi].update(recipe_link='explicit',material_state_id='acid-isolated',link_evidence=E(s['evidence']))
for fid,f in FM.items():
    r=R[OWN[fid]];sid='fact-context-'+fid.removeprefix(SID+'-');note='Source claim class: '+f['claim_class']+'. '+qualify(f['conflict_ids']+f['gap_ids'])
    ptr=addmeasure(r,fid+'-claim',sid,'source_claim',fact(f['claim'],E(f['evidence']),note=note),f['evidence'],conditions=f['sample_scope']);FL[fid].append({'record_id':r['record_id'],'pointer':ptr,'source_pointer':'/claim'})
    for j,q in enumerate(f['quantities']):
        derived='author_derived'if f['claim_class']in['source_calculation','reported_analysis']else None
        ptr=addmeasure(r,fid+'-q'+str(j+1),sid,key(q['meaning']),Q(q,f['sample_scope'],note,force=derived),q['evidence'],conditions=f['sample_scope'])
        FL[fid].append({'record_id':r['record_id'],'pointer':ptr,'source_pointer':'/quantities/'+str(j)})
    r['quality']['conflicts']+=[qualify([x])for x in f['conflict_ids']]
for ti,t in enumerate(T['tables']):
    r=R[TO[t['id']]]
    for ri,row in enumerate(t['rows']):
        sid='table-context-'+t['id']+'-'+row['id'];scope=row.get('sample_context',row.get('source_context',row.get('context',row['id'])))
        for ci,q in enumerate(row['cells']):
            sp=f'/tables/{ti}/rows/{ri}/cells/{ci}';note='Row and column metadata: '+compact({k:v for k,v in row.items()if k!='cells'})+'. No source fit or number was recalculated.'
            fitted=t['id']not in['acid-nmr'] and not(t['id']in['table-1','table-s22']and ci==0)
            ptr=addmeasure(r,t['id']+'-'+row['id']+'-c'+str(ci),sid,key(q['meaning']),Q(q,str(scope),note,force='author_derived'if fitted else None),q['evidence'],'Published fit/calculation'if fitted else'Reported condition or NMR measurement',str(scope))
            TC.append({'source_file':'source-tables.json','source_pointer':sp,'table_id':t['id'],'row_id':row['id'],'column_index':ci,'record_id':r['record_id'],'pointer':ptr})

# Exact structured objects are retained in addition to typed claims. Full-page text is excluded.
def object_owner(category,obj):
    if category=='facts':return OWN[obj['id']]
    if category=='materials':return 'source-materials'
    if category=='stocks':return next(x['proposed_record_ids'][0].removeprefix(PRE)for x in MAP['stocks']if x['source_id']==obj['id'])
    if category=='protocols':return 'conversion-representative'if obj['id']=='conversion-family'else obj['id']
    if category=='sample_contexts':return SOWN[obj['id']]
    if category=='figures':return FO[obj['id']][0]
    if category=='schemes':return 'mechanistic-context'
    if category=='equations':return EO[obj['id']]
    return 'source-context'
PAYB={}
for category in['facts','materials','stocks','protocols','sample_contexts','figures','schemes','equations','conflicts','missingness','references']:
    for j,obj in enumerate(D[category]):
        r=R[object_owner(category,obj)];oid=obj.get('id',str(j));es=obj.get('evidence')or FM[SID+'-identity']['evidence'];sp=f'/{category}/{j}'
        ptr=addmeasure(r,'payload-'+category+'-'+norm(oid),'source-payload-context','source_'+category+'_payload',fact(compact(obj),E(es),note='Exact frozen structured source object. Embedded author-stage pending flags are historical; this draft is independently unapproved. Not a full-text page cache.'),es,'Structured source inventory')
        PAYB[('source-facts.json',sp)]={'record_id':r['record_id'],'pointer':ptr};bindobj(category,oid,r,ptr,sp)
for j,obj in enumerate(T['tables']):
    r=R[TO[obj['id']]];sp=f'/tables/{j}';es=obj.get('evidence')or obj['rows'][0]['cells'][0]['evidence']
    ptr=addmeasure(r,'payload-table-'+obj['id'],'source-table-context','source_table_payload',fact(compact(obj),E(es),note='Exact printed numeric listing and row/column definitions; typed cell values are separately mapped.'),es,'Structured source table')
    PAYB[('source-tables.json',sp)]={'record_id':r['record_id'],'pointer':ptr};bindobj('table',obj['id'],r,ptr,sp)
for u in I['units']:
    for t in u['extraction_targets']:
        if(t['file'],t.get('json_pointer'))in PAYB:UL[u['id']].append(PAYB[(t['file'],t['json_pointer'])])
        else:
            r=R['mechanistic-context'if u['kind']=='conceptual_figure'else'source-context'];es=u['evidence']
            safe={'id':u['id'],'kind':u['kind'],'title':u['title'],'summary':u['summary'],'source_payload_ids':u['source_payload_ids'],'source_role':'Original document/page provenance only; no full text or internal cache paths copied','source_target_kind':'original graphical abstract'if u['kind']=='conceptual_figure'else'original SI contents page'}
            ptr=addmeasure(r,'payload-'+u['id'],'source-unit-context','source_unit_definition',fact(compact(safe),E(es),note='Complete source text stays private. A source-content locator or original graphical abstract is not an experimental measurement.'),es,'Source inventory')
            UL[u['id']].append({'record_id':r['record_id'],'pointer':ptr})
for r in R.values():
    r['quality']['missing_fields']=list(dict.fromkeys(r['quality']['missing_fields']));r['quality']['conflicts']=list(dict.fromkeys(r['quality']['conflicts']))
    if r['record_type']in['literature_protocol','protocol_variant']:
        for k in['structural-results','temperature-results','concentration-results','additive-results','pretreatment-results']:
            r['context_links'].append({'label':R[k]['method'],'url':'/records/'+R[k]['record_id']+'.html','relation':'comparative_source_context_not_exact_sample_pair'})
errors=[e for r in R.values()for e in validate_record(r)]
save('draft-schema-errors.json',errors);assert not errors,errors[:25]
assert all(FL.values())and all(UL.values())and len(TC)==185
assert not any(v['eligible']for r in R.values()for v in eligibility(r).values())
assert len(set(build_groups(list(R.values())).values()))==1
records=[]
for k,r in R.items():
    p=O/'records'/(r['record_id']+'.json');save('records/'+p.name,r);records.append({'record_id':r['record_id'],'path':str(p),'sha256':sha(p),'record_type':r['record_type'],'operations':len(r['operations']),'measurements':len(r['measurements'])})
save('source-to-field-coverage.json',{'status':'private_author_draft_pending_independent_review','facts':[{'source_fact_id':fid,'canonical_bindings':bs}for fid,bs in FL.items()],
    'source_units':[{'source_unit_id':uid,'canonical_bindings':bs}for uid,bs in UL.items()],'source_objects':OB,'table_cells':TC,'operation_quantities':TYPED,'operations':OP,
    'source_freeze_sha256':EXPECTED,'source_fact_sha256':sha(effective('source-facts.json'))})
save('source-owner-map.json',{'fact_owner':OWN,'sample_owner':SOWN,'table_owner':TO,'equation_owner':EO,'figure_owner':FO,'section_by_record':{p['record_id']:p['reader_section']for p in PLAN['records']}})
save('record-manifest.json',{'status':'unfrozen_private_draft_pending_source_and_canonical_audits','author':'/root/norberg2004_extract','source_id':SID,'source_freeze_sha256':EXPECTED,'records':records,
    'counts':{'records':len(R),'source_operations':34,'operation_instances':len(OP),'materials':sum(len(r['materials'])for r in R.values()),'stocks':sum(len(r['stocks'])for r in R.values()),'measurements':sum(len(r['measurements'])for r in R.values()),'condition_options':sum(len(r['condition_options'])for r in R.values())},
    'eligible_training_tasks':0,'current_source_audit_status':'passed'if audit else'pending','source_audit_path':str(audit)if audit else None,'source_audit_sha256':sha(audit)if audit else None,
    'effective_source_files':{n:{'path':str(effective(n)),'sha256':sha(effective(n))}for n in['source-facts.json','source-inventory.json','source-tables.json','original-assets-manifest.json','page-coverage.json']},
    'source_overlay_path':str(overlay)if overlay else None,'final_freeze_allowed':False})
print(json.dumps({'status':'draft_schema_passed','records':len(R),'ops':len(OP),'measurements':sum(len(r['measurements'])for r in R.values()),'record_manifest_sha256':sha(O/'record-manifest.json')}))
