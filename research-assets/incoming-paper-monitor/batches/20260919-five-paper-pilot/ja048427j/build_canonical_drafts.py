"""Private Norberg canonical authoring. Reads audited source and current Site schema only.
All writes stay in this paper's private batch directory. No source, Site or ledger edits.
"""
from pathlib import Path
from copy import deepcopy
from collections import Counter
from datetime import datetime, timezone
import hashlib, json, re, sys
sys.dont_write_bytecode = True
B = Path(__file__).resolve().parent
S = Path(r'[local path redacted]')
sys.path.insert(0, str(S/'scripts'))
from record_helpers import record, source, fact, qty, material, operation, state, product, measurement
from dataset_lib import validate_record, eligibility, build_groups
def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d): Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def compact(d): return json.dumps(d,ensure_ascii=False,separators=(',',':'))
def norm(s): return re.sub('[^a-z0-9]+','-',s.lower()).strip('-')
def esc(s): return str(s).replace('~','~0').replace('/','~1')
def resolve(obj,pointer):
    for x in pointer.strip('/').split('/'):
        x=x.replace('~1','/').replace('~0','~')
        obj=obj[int(x)] if isinstance(obj,list) else obj[x]
    return obj
D=read(B/'source-facts.json'); I=read(B/'source-inventory.json'); A=read(B/'source-scientific-audit.json')
ASSETS={a['id']:a for a in read(B/'reader-assets/asset-manifest.json')['assets']}
assert A['status']=='passed' and A['independent'] is True
for name,h in A['audited_artifacts'].items(): assert sha(B/name)==h,('Changed audited artifact',name)
for doc in A['source_documents']: assert sha(doc['path'])==doc['sha256'],('Source bytes changed',doc['path'])
SID='norberg2004'; PRE='norberg-2004-'
F={f['id']:f for f in D['facts']}; M={m['id']:m for m in I['materials']}; P={p['id']:p for p in I['protocols']}; ST={s['id']:s for s in I['stocks']}; SS={s['id']:s for s in I['samples']}
assert len(F)==201 and len(SS)==22
CATEGORIES=['materials','stocks','protocols','samples','figures_tables_schemes','equations','tables','chemical_intuition','references','gaps','other_source_content']
O={}
for cat in CATEGORIES:
    for ix,item in enumerate(I[cat]): O[(cat,item.get('id',item.get('kind',str(ix))))]=(ix,item)
U=set(A['reviewed_source_unit_ids']) | {f['source_unit_id'] for f in F.values()}
fact_links={k:[] for k in F}; unit_links={k:[] for k in U}; object_links=[]; op_links=[]; records={}; OP={}
def fid(short): return short if short.startswith(SID+'-') else SID+'-'+short
def evidence(items):
    return [{'source_id':SID,'locator':('SI' if e.get('source_role')=='si' or e.get('source_id','').endswith('-si') else 'Main')+f" PDF p. {e['pdf_page']}"+(f" (printed {e['printed_page']})" if e.get('printed_page') else '')+', '+e.get('locator','Source text')} for e in items]
def E(unit):
    ev=[]
    for (cat,key),(ix,obj) in O.items():
        if key==unit: ev.extend(obj.get('evidence',[]))
    if not ev:
        for f in F.values():
            if f['source_unit_id']==unit: ev.extend(f['evidence'])
    if not ev and unit in SS:
        x=SS[unit]
        if x.get('parent_protocol') in P: ev.extend(P[x['parent_protocol']]['evidence'])
    if not ev: return [{'source_id':SID,'locator':'Complete supplied main (12 pages) and matched SI (4 pages); source inventory scope '+unit}]
    return list({compact(e):e for e in evidence(ev)}.values())
def bindf(r,short,ptr,subpath=''):
    fact_links[fid(short)].append({'record_id':r['record_id'],'pointer':ptr,'source_value_pointer':subpath})
def bindu(r,unit,ptr):
    if unit in unit_links: unit_links[unit].append({'record_id':r['record_id'],'pointer':ptr})
def bindo(cat,key,r,ptr,mode='semantic_field'):
    ix,obj=O[(cat,key)]
    object_links.append({'category':cat,'source_object_id':key,'source_pointer':f'/{cat}/{ix}','record_id':r['record_id'],'pointer':ptr,'mode':mode})
GAPS={g['id']:g for g in I['gaps']}
gaptext=[g['id']+' ('+g['scope']+'): '+g['issue']+' '+g['resolution'] for g in I['gaps']]
conflicts=[g['id']+': '+g['issue']+' '+g['resolution'] for g in I['gaps'] if g['id'] in ['g-tmah-formula','g-base','g-s4-count','g-poisson','g-si-curve-table']]
SRC=source(SID,I['doi'],I['title'],'; '.join(I['authors']),I['year'],si='Matched four-page SI; all supplied pages text-read and visually inspected in passed independent full-source audit.')
SRC['main_status']='All 12 main pages read and visually inspected in the passed independent source audit. Canonical drafts await their own scientific audit.'
SRC['reuse_status']='Private factual extraction with original locators. No public rights or figure reuse permission inferred.'
def base(key,title,kind='observation',method='Source-scoped observations'):
    r=record(PRE+key,'Norberg et al. (2004) · '+title,'Mn:ZnO','Mn-doped ZnO, surface controls and nanocrystalline films',method,deepcopy(SRC),'Main pp. 9387–9398 and matched SI pp. S-1–S-4',kind)
    r['schema_version']='1.3.0'
    r['material'].update(elements=['Mn','Zn','O'],components=['Mn:ZnO'],architecture='single_material')
    r['lineage'].update(source_group=SID,recipe_family='norberg2004-acetate-hydrolysis-mn-zno')
    r['quality'].update(review_status='imported_unreviewed',requested_tasks=[],experimental_outcome='not_established',review_scope='Private canonical author draft from the independently audited 12-page main and four-page SI. Record and sample IDs are curation identifiers, not experimental replicate or batch claims. Canonical scientific, reader, visual and publication gates remain pending.',missing_fields=deepcopy(gaptext),conflicts=deepcopy(conflicts))
    if kind!='literature_protocol': r['intended_target']['composition']=fact(None,E('protocol-hydrolysis'),note='Procedure, specimen, model or reference context; not an independent target-synthesis experiment.')
    else: r['intended_target']['composition']=fact('Mn2+:ZnO',E('protocol-hydrolysis'),note='Generic composition family, variable Mn feed x. The 0.50% feed/0.20% ICP outcome is a separately identified specimen, not a universal target.')
    records[key]=r; return r
route=base('hydrolysis','Colloidal Mn²⁺:ZnO by acetate hydrolysis','literature_protocol','Solution hydrolysis and condensation; partial common preparation')
clean=base('amine-cleaning','Dodecylamine surface cleaning','procedure','Ligand-mediated surface cleaning and concurrent ripening')
surface=base('surface-control','Deliberately surface-bound Mn control','procedure','Post-synthetic surface doping control')
titr=base('titration','Base-addition reaction monitoring','procedure','Successive base addition and absorption aliquots')
topo=base('topo','TOPO-treated MCD specimen','procedure','Cited partial TOPO treatment and frozen-solution MCD')
films=base('films-a-c','Spin coating and air annealing of films A–C','procedure','Layer-by-layer spin coating and 525 °C air annealing')
df=base('films-d-f','Films D–F: incomplete preparation and conflicting magnetic labels')
oxid=base('oxidation-controls','Manganese precursor oxidation controls','procedure','DMSO solution stability under separate chemical and atmospheric conditions')
growth=base('growth-series','0.02% feed growth aliquots and EPR','procedure','Aliquot growth progression; distinct washed and cleaned specimen contexts')
struct=base('structure','0.20% Mn specimen: ICP, TEM and XRD','procedure','Composition, microscopy and diffraction of identified colloid, powder and film states')
opt=base('optical','Undoped, 0.13% and 1.3% optical specimens','procedure','Normalized absorption and photoluminescence comparison')
mag=base('magnetism','Colloid and films A–C magnetic behavior','procedure','SQUID magnetometry, residual-paramagnetism analysis and EPR')
epr=base('epr-model','EPR Hamiltonian fit and bulk reference constants')
ct=base('charge-transfer-model','Ligand-field and charge-transfer interpretation')
dopant=base('dopant-statistics','Dopant-number model with unresolved notation')
reagents=base('reagent-properties','Reagent identities, purity and source formula discrepancy')
methods=base('acquisition-methods','Acquisition methods and analysis conventions','procedure','Separate instrument and sample contexts')
intuition=base('chemical-intuition','Chemical interpretation and unresolved mechanism')
refs=base('source-context','Bibliography, missing information and source notes')
PMAP={'protocol-hydrolysis':route,'protocol-amine-cleaning':clean,'protocol-surface-control':surface,'protocol-titration':titr,'protocol-topo':topo,'protocol-films':films,'protocol-oxidation-controls':oxid}
def mat(r,key,stage='precursor_preparation',role=None):
    if any(m['id']==key for m in r['materials']): return key
    m=M[key]; ev=evidence(m['evidence'])
    mm=material(key,m['name'],m['formula'],role or {'dmso':'solvent','ethanol':'solvent','toluene':'solvent','ethyl-acetate':'antisolvent','heptane':'antisolvent','dodecylamine':'ligand','topo':'ligand','zinc-acetate-dihydrate':'host_precursor','manganese-acetate-tetrahydrate':'dopant_precursor'}.get(key,'source_material'),stage,ev,notes=[s for s in [m['notes'],'Source roles: '+', '.join(m['roles'])+'.','Supplier: '+str(m['supplier'] or 'not reported')+'.','Pretreatment: '+str(m['pretreatment'] or 'not reported')+'.',m['formula_status'],'No molecular or atomic coordinates supplied.'] if s])
    mm['quantities']['purity']=qty(m['purity_percent'],'%',ev,qualifier='Source reagent purity; not synthesis yield or product purity.' if m['purity_percent'] is not None else 'Not reported.')
    r['materials'].append(mm);i=len(r['materials'])-1;bindo('materials',key,r,f'/materials/{i}');bindu(r,key,f'/materials/{i}');return key
def specimen(r,key,label,unit,formula=None):
    if any(m['id']==key for m in r['materials']): return key
    r['materials'].append(material(key,label,formula,'specimen','characterization',E(unit),notes=['Source-defined starting specimen/state; no additional preparation quantities or independent batch/replicate inferred.']))
    return key
def sample(r,key,formula=None,state_id=None,link='general_context',notes=None,unit=None):
    old=next((p for p in r['products'] if p['sample_id']==key),None)
    if old: return old
    ev=E(unit or key);p=product(key,formula,ev,link=link,state=state_id,notes=notes or ['Source specimen or context, not an independently enumerated synthesis replicate.'])
    p['source_sample_label']=key.replace('-',' ');r['products'].append(p);bindu(r,key,f'/products/{len(r["products"])-1}');return p
def context(r,key,text,ev=None,sid='source-context',prop='source_context',status='reported',note=''):
    sample(r,sid,unit=key);i=len(r['measurements'])
    r['measurements'].append(measurement(norm(key),sid,prop,fact(text,ev or E(key),status,note),'Source text / original figure context',ev or E(key)))
    ptr=f'/measurements/{i}/value';bindu(r,key,ptr);return ptr
def normstatus(f,subpath=''):
    s=f['status']
    if 'MnZnS_cited_experimental' in subpath: return 'reported'
    if s in ['author_model_input','cited_model_input','cited_model_input_si','author_model_assumption','reference_quantum_number'] or s.startswith('cited') or s=='contextual_reference_constant': return 'reported'
    if s.startswith('author_'): return 'author_derived'
    return 'reported'
RANGES={'abs-size-estimate','lum-abs-range','context-prior-Tc','context-ligand-epsilon'}
LOWER={'tc-bound':True,'domain-spin-bound':True,'lower-ferro-a':False,'lower-ferro-b':False,'lower-ferro-c':False,'solubility-context':True,'synthesis-ratio-context':True,'context-prior-surface':False}
UPPER={'zn-magnetic-impurities':True,'cool-limit':True,'mn900-context':True}
KEY_UNITS={'frequency_GHz':'GHz','path_length_cm':'cm','temperature_K':'K','field_T_range':'T','cuvette_cm':'cm','excitation_cm-1':'cm−1','accelerating_voltage_kV':'kV','instrument_temperature_ceiling_K':'K','mass_ug':'µg','Ms_emu_g':'emu/g','Ms_muB_per_Mn2+':'µB/Mn2+'}
def qvalue(short,subpath=''):
    f=F[fid(short)]; key=f['id'].removeprefix(SID+'-');v=f['value'];ev=evidence(f['evidence'])
    if subpath: v=resolve(v,subpath)
    unit=f['unit'] or '';member=subpath.strip('/').split('/')[0] if subpath else ''
    if member in KEY_UNITS:unit=KEY_UNITS[member]
    elif member.endswith('_cm-1'):unit='cm−1'
    status=normstatus(f,subpath)
    basis='Source unit: '+f['source_unit_id']+'. Sample scope: '+f['sample_scope']+'. Original source status: '+f['status']+'.'
    qual=f['qualifier'] or ''
    if f.get('uncertainty'): qual+=' Reported uncertainty: '+compact(f['uncertainty'])+'. It is not reclassified as a standard deviation or confidence interval.'
    if subpath:basis+=' Original value member '+subpath+'.'
    if f['status'] in ['author_model_input','cited_model_input','cited_model_input_si','author_model_assumption']:basis+=' Reported model input/assumption, not a measured specimen outcome.'
    elif f['status'].startswith('cited') or f['status'] in ['contextual_reference_constant','reference_quantum_number']:basis+=' Cited/reference-system statement, not a measurement of this paper’s synthesis product.'
    elif f['status'].startswith('author_'):basis+=' Author fit, estimate, model or interpretation; not recomputed here and not converted into a direct measurement.'
    if key.startswith('table-s3-'):
        basis+=' Mixed row: MnZnO/MnZnS calculated columns are author model outputs; MnZnS cited experimental column is from SI reference 5. No column is a measured MnZnO nanocrystal outcome.'
    if not f['unit'] and not member in KEY_UNITS and not member.endswith('_cm-1'):basis+=' Empty unit means no explicit unit is supplied for this member; it does not assert dimensionality.'
    if isinstance(v,str):return fact(v,ev,status,note=basis+' '+qual)
    if isinstance(v,list):
        assert key in RANGES or member=='field_T_range',(key,subpath,'array requires explicit indexed members')
        return qty(unit=unit,minimum=v[0],maximum=v[1],evidence=ev,status=status,approximate=f['approximate'],qualifier=qual,basis=basis,raw_text=f.get('raw_text') or '')
    assert not isinstance(v,dict),(key,'object requires scalar field mapping')
    opts={}
    if not subpath and key in LOWER:opts={'minimum':v,'minimum_exclusive':LOWER[key]};v=None
    if not subpath and key in UPPER:opts={'maximum':v,'maximum_exclusive':UPPER[key]};v=None
    if key=='titration-clouding':qual+=' Threshold marker only; observation is beyond this approximate addition, not a fixed hold or exact failure boundary.'
    return qty(v,unit,ev,status,approximate=f['approximate'],qualifier=qual,basis=basis,raw_text=f.get('raw_text') or '',**opts)
def param(r,oid,name,short,subpath=''):
    op=OP[oid];q=qvalue(short,subpath);assert 'unit' in q
    op['parameters'][name]=q;bindf(r,short,f'/operations/{r["operations"].index(op)}/parameters/{esc(name)}',subpath)
def m_fact(r,short,sid,subpath='',tech='Source-reported quantity, outcome or analysis'):
    f=F[fid(short)];sample(r,sid,unit=f['source_unit_id']);q=qvalue(short,subpath)
    mid=f['id']+('-'+norm(subpath) if subpath else '')
    assert all(m['id']!=mid for m in r['measurements']),(mid,'duplicate fact binding in record')
    prop=norm(f['property']).replace('-','_')+(('_'+norm(subpath).replace('-','_')) if subpath else '')
    condition='Source unit '+f['source_unit_id']+'; source sample scope '+f['sample_scope']+'.'
    if f['source_unit_id']=='table-s4':condition+=' 300 K; table values remain as printed. D/F plot-vs-table conflict g-si-curve-table is unresolved.'
    i=len(r['measurements']);r['measurements'].append(measurement(mid,sid,prop,q,tech,evidence(f['evidence']),conditions=condition))
    ptr=f'/measurements/{i}/value';bindf(r,short,ptr,subpath);bindu(r,f['source_unit_id'],ptr)
    return ptr

# Source stocks remain incomplete, without inferred preparation masses or volumes.
STOCK_NAMES={'stock-metal-acetates':'Combined Mn/Zn acetate solution in DMSO','stock-tmah':'Ethanolic tetramethylammonium hydroxide','stock-lioh-control':'Ethanolic LiOH control solution','stock-mn-oxidation':'Manganese acetate oxidation-control solution','stock-nitrate-control':'Manganese nitrate substitution control'}
def stock(r,key,prep=None):
    if any(s['id']==key for s in r['stocks']):return key
    x=ST[key];ev=evidence(x['evidence']);comps=[]
    for k in x['components']+[x['solvent']]:
        mat(r,k);comps.append({'material_id':k,'quantities':{}})
    ff={'stock-metal-acetates':'metal-conc','stock-tmah':'tmah-conc','stock-mn-oxidation':'stock-mn-conc'}.get(key)
    cc=qvalue(ff) if ff else qty(x['concentration']['value'],'mol/L',ev,qualifier='Nitrate replacement control, not acetate-plus-nitrate mixture.') if key=='stock-nitrate-control' else qty(unit='mol/L',evidence=ev,qualifier='LiOH concentration is not reported; do not copy the TMAH concentration.')
    obj={'id':key,'name':STOCK_NAMES[key],'components':comps,'concentrations':{'combined_metal_concentration' if key=='stock-metal-acetates' else 'solute_concentration':cc},'preparation_operation_ids':prep or [],'scope':'Exact source stock identity. Absolute volume and solute charge are not supplied. '+('x Mn/(1−x) Zn composition; x is specimen-specific. ' if key=='stock-metal-acetates' else '')+('Source storage/control scope: '+x['storage'] if x.get('storage') else 'Storage conditions are not reported.'),'evidence':ev}
    r['stocks'].append(obj);j=len(r['stocks'])-1;bindo('stocks',key,r,f'/stocks/{j}');bindu(r,key,f'/stocks/{j}')
    if ff:bindf(r,ff,f'/stocks/{j}/concentrations/'+next(iter(obj['concentrations'])))
    return key

LABELS={
'protocol-hydrolysis':['Prepare the combined metal acetate solution','Add ethanolic base dropwise with stirring','Allow growth and select a reported ripening alternative','Precipitate the nanocrystals with ethyl acetate','Resuspend the precipitate in ethanol','Repeat heptane precipitation and ethanol washing','Cap with dodecylamine and transfer into toluene'],
'protocol-amine-cleaning':['Heat the capped colloids in dodecylamine under nitrogen','Cool below 80 °C','Precipitate and wash with ethanol','Disperse the cleaned product in a nonpolar solvent'],
'protocol-surface-control':['Prepare and wash the undoped ZnO control','Add manganese acetate to the washed ZnO','Add the ethanolic LiOH control charge','Wash, cap and transfer the surface-bound control'],
'protocol-titration':['Prepare the 2% Mn feed titration solution','Add successive base increments','Measure, dilute and remeasure withdrawn aliquots'],
'protocol-topo':['Apply the incompletely restated TOPO treatment','Prepare a drop-coated frozen-solution MCD specimen'],
'protocol-films':['Spin-coat the precursor on fused silica','Anneal each deposited layer in air','Repeat the coating and annealing cycle for A, B or C'],
'protocol-oxidation-controls':['Prepare the manganese acetate reference solution','Set up separate chemical and atmospheric controls','Age the separate solutions and measure absorption']}
EXTERNAL={
'dodecylamine-capped-colloids':('Preformed dodecylamine-capped colloids','protocol-amine-cleaning','Mn:ZnO'),
'undoped-zno-control':('Pure ZnO prepared without manganese feed','protocol-surface-control','ZnO'),
'grown-colloids':('Preformed nanocrystals for the cited TOPO alternative','protocol-topo','Mn:ZnO'),
'cleaned-final-colloids':('Dodecylamine-treated 0.20 ± 0.01% Mn precursor colloids','protocol-films','Mn:ZnO')}
OUT={}; OP_SOURCE={}
for pid,proto in P.items():
    r=PMAP[pid];prev=None
    for j,x in enumerate(proto['operations']):
        oid=PRE+x['id'].removeprefix('protocol-');inputs=[]
        for k in x['inputs']:
            if k in M:inputs.append(mat(r,k,'synthesis' if r is route else 'precursor_preparation'))
            elif k in ST:inputs.append(stock(r,k,[PRE+'hydrolysis-op-1'] if k=='stock-metal-acetates' and r is route else []))
            elif k in OUT.get(pid,{}):inputs.append(OUT[pid][k])
            else:
                label,unit,formula=EXTERNAL[k];inputs.append(specimen(r,k,label,unit,formula))
        output=x['output']+'-state'
        OUT.setdefault(pid,{})[x['output']]=output
        stage='synthesis' if r is route else 'surface_exchange' if r in [clean,surface,topo] else 'characterization' if r is titr else 'precursor_preparation'
        if r is route and j>=3 or r is clean and j>=2 or r is surface and j==3:stage='workup'
        if r is route and j==0:stage='precursor_preparation'
        if r is topo and j==1:stage='characterization'
        if r is films:stage='synthesis'
        if r is oxid and j==2:stage='storage'
        kind='fraction' if x.get('retained_fraction') else 'sample_set' if r in [films,oxid,titr] else 'reaction_batch'
        if r is titr and j==2:kind='analysis_data'
        r['material_states'].append(state(output,LABELS[pid][j]+' — source state',inputs,kind))
        note=x['conditions']+'. Source scope: '+proto['scope']+'. Missing: '+', '.join(proto['missing_fields'])+'.'
        if r is films:note+=' This executable preparation applies only to A–C. D–F have a separate incomplete-outcome record; no coat count, parent batch or annealing conditions are assigned to them.'
        if r is oxid:note+=' Comparison/sample-set state, not a physical mixture or enumerated independent replicates. Manganese nitrate substitutes for manganese acetate; it is not added to it. The anaerobic gas is unspecified.'
        if r is surface and j==0:note+=' The source says to synthesize pure ZnO by the common route without Mn, then wash and resuspend in ethanol. This is an upstream protocol reference, not a claim that preformed ZnO is resynthesized.'
        env=fact(None,E(pid),note='No numerical pressure or unreported apparatus geometry is inferred.')
        if r is route:env=fact('atmospheric conditions',E(pid),note='Room-temperature synthesis under atmospheric conditions. No nitrogen or numerical pressure is assigned.')
        if r is clean and j==0:env=qvalue('clean-atmosphere')
        if r is films and j==1:env=qvalue('film-anneal-atmosphere')
        op=operation(oid,x['action'],LABELS[pid][j],E(pid),inputs,[output],depends=[prev] if prev else [],stage=stage,branch=pid,description=note,environment=env,retained_fraction=output if x.get('retained_fraction') else None)
        r['operations'].append(op);OP[oid]=op;OP_SOURCE[x['id']]=oid
        ptr=f'/operations/{len(r["operations"])-1}';bindu(r,pid,ptr)
        op_links.append({'source_protocol_id':pid,'source_operation_id':x['id'],'source_pointer':f'/protocols/{list(P).index(pid)}/operations/{j}','record_id':r['record_id'],'pointer':ptr,'input_state_normalization':'Existing mixtures and prepared specimens are stage-specific states, not newly charged product ingredients. Source fraction descriptions map to retained output IDs.'})
        prev=oid
    bindo('protocols',pid,r,'/operations')
# The stock prepared by hydrolysis op 1 has a distinct output state and stock ID.
stock(route,'stock-metal-acetates',[PRE+'hydrolysis-op-1'])
stock(oxid,'stock-nitrate-control')
oxid['operations'][1]['optional_inputs']=[mat(oxid,'zinc-acetate-dihydrate'),mat(oxid,'sodium-acetate'), 'stock-nitrate-control']
oxid['operations'][1]['description']+=' optional_inputs list alternatives across separate controls, never jointly added to a single solution.'
for r,oid,key,ff,sub in [
(route,'hydrolysis-op-1','combined_metal_concentration','metal-conc',''),(route,'hydrolysis-op-2','base_equivalents','base-eq',''),(route,'hydrolysis-op-2','base_stock_concentration','tmah-conc',''),
(clean,'amine-cleaning-op-1','temperature','clean-temp',''),(clean,'amine-cleaning-op-1','duration','clean-time',''),(clean,'amine-cleaning-op-2','precipitation_temperature_limit','cool-limit',''),
(surface,'surface-control-op-2','Mn_relative_to_Zn','surface-mn',''),(surface,'surface-control-op-3','LiOH_charge_basis_unspecified','surface-lioh',''),
(titr,'titration-op-1','Mn_feed_fraction','titration-feed',''),(titr,'titration-op-1','combined_metal_concentration','metal-conc',''),(titr,'titration-op-2','base_increment','titration-increment',''),(titr,'titration-op-2','base_stock_concentration','tmah-conc',''),(titr,'titration-op-3','remeasurement_dilution','titration-dilution',''),
(films,'films-op-1','substrate_length','film-substrate','/0'),(films,'films-op-1','substrate_width','film-substrate','/1'),(films,'films-op-2','temperature','film-anneal-t',''),(films,'films-op-2','per_layer_duration','film-anneal-time',''),
(oxid,'oxidation-controls-op-1','Mn_concentration','stock-mn-conc',''),(oxid,'oxidation-controls-op-3','storage_duration','stock-storage-time',''),(oxid,'oxidation-controls-op-3','absorption_probe','stock-probe','')]:param(r,PRE+oid,key,ff,sub)
bindf(clean,'clean-atmosphere','/operations/0/environment');bindf(films,'film-anneal-atmosphere','/operations/1/environment')
route['condition_options']=[{'id':'ambient-ripening','label':'Alternative: several days at room temperature; qualitative duration, no exact hold','parameters':{'temperature':qty(unit='degC',evidence=E('protocol-hydrolysis'),qualifier='Room temperature; no numeric value supplied.'),'duration':qty(unit='days',evidence=E('protocol-hydrolysis'),qualifier='Several days; no fixed number supplied.')},'evidence':E('protocol-hydrolysis')},{'id':'accelerated-ripening','label':'Alternative: accelerate ripening by heating near 60 °C; duration unspecified','parameters':{'temperature':qvalue('ripening-heat'),'duration':qty(unit='h',evidence=E('protocol-hydrolysis'),qualifier='Common route does not specify duration; 2 h belongs only to the 0.02% feed series.')},'evidence':E('protocol-hydrolysis')}]
bindf(route,'ripening-heat','/condition_options/1/parameters/temperature')
for letter in 'abc':
    ff='film-'+letter+'-coats';films['condition_options'].append({'id':'film-'+letter,'label':'Film '+letter.upper()+' only: total coating/annealing cycles','parameters':{'coating_cycles':qvalue(ff)},'evidence':evidence(F[fid(ff)]['evidence'])});bindf(films,ff,f'/condition_options/{len(films["condition_options"])-1}/parameters/coating_cycles')
for r,oid,fields in [(route,'hydrolysis-op-1',[('reaction_volume','mL')]),(route,'hydrolysis-op-2',[('addition_duration','min'),('stirring_speed','rpm')]),(route,'hydrolysis-op-7',[('initial_capping_temperature','degC'),('initial_capping_duration','min'),('dodecylamine_charge','g')]),(topo,'topo-op-1',[('temperature','degC'),('duration','min'),('TOPO_charge','g')]),(films,'films-op-1',[('spin_speed','rpm'),('spin_duration','s'),('dispensed_volume','mL')])]:
    for name,unit in fields:OP[PRE+oid]['parameters'][name]=qty(unit=unit,evidence=OP[PRE+oid]['evidence'],qualifier='Not reported for this operation. Conditions from other specimens/treatments are not borrowed.')

# Sample identity is independent of nominal formula, observed size and measurement.
SAMPLE_RECORD={s:(titr if s=='titration-series' else surface if s=='surface-control-epr' else growth if s.startswith('growth-') else struct if s.startswith('cleaned-0.20') else topo if s=='topo-1.1pct' else opt if s.startswith('optical-') else films if s in ['film-a','film-b','film-c'] else df if s.startswith('film-') else oxid) for s in SS}
for sid,ss in SS.items():
    r=SAMPLE_RECORD[sid]
    form='ZnO' if sid=='optical-pure-zno' else 'Mn:ZnO' if not sid.startswith('oxidation-') else None
    notes=['Source composition/state/linkage: '+compact(ss),'No unique experimental batch ID, independent replicate or calibrated success label is inferred.']
    if sid.startswith('growth-'):notes.append('An aliquot progression: a later aliquot is not produced by recycling the earlier measured aliquot.')
    if sid in ['film-d','film-e','film-f']:notes.append('Coat count, parent batch and independently stated annealing conditions remain unknown. g-film-df and g-si-curve-table remain unresolved.')
    p=sample(r,sid,form,notes=notes,link='unresolved' if sid in ['film-d','film-e','film-f'] else 'general_context')
    p['source_sample_label']=sid.replace('-',' ')
    bindo('samples',sid,r,f'/products/{r["products"].index(p)}')
    if sid=='cleaned-0.20pct-powder':p['parent_sample_id']='cleaned-0.20pct'
    if sid=='growth-02-d':p['parent_sample_id']='growth-02-c';p['notes'].append('Parent denotes later-growth material lineage only, not re-use of the physical EPR aliquot c.')
sample(route,'common-variable-feed-product','Mn:ZnO',OUT['protocol-hydrolysis']['dodecylamine-capped-colloids'],notes=['Common variable-x framework, not a unique specimen or complete recipe. Initial capping is distinct from subsequent 180 °C cleaning.'])
sample(clean,'cleaned-final-colloids','Mn:ZnO',OUT['protocol-amine-cleaning']['cleaned-final-colloids'],notes=['Generic cleaned colloid output. Several-month stability has no stated storage conditions.'])
for r in [films,mag]:
    sample(r,'cleaned-0.20pct','Zn0.998Mn0.002O',unit='cleaned-0.20pct',notes=['Explicit 0.20 ± 0.01% Mn precursor/material identity. Nominal formula is source reported, not refined occupancies or exact atomic coordinates.'])
for sid in ['film-a','film-b','film-c']:
    p=sample(films,sid);p['parent_sample_id']='cleaned-0.20pct';p['material_state_id']=OUT['protocol-films']['film-series'];p['notes'].append('Shared sample-set state represents separate films A–C, not one physical mixed film. Per-film coat count remains a condition option.')
for sid in ['cleaned-0.20pct-powder','film-a','film-b','film-c']:
    sample(mag,sid,'Mn:ZnO',unit=sid,notes=['Source-linked specimen context. Measurements at multiple temperatures/fields are not additional synthesis replicates.'])
for sid in ['film-a','cleaned-0.20pct']:
    sample(struct,sid,'Mn:ZnO',unit=sid)
sample(epr,'growth-02-d','Mn:ZnO',unit='growth-02-d',notes=['Nominal 0.02% feed basis. Fitted parameters are model outputs, not atomic-coordinate refinement.'])
for sid in ['optical-0.13pct','optical-1.3pct']:sample(dopant,sid,'Mn:ZnO',unit=sid,notes=['Shared optical/model concentration label, not counted dopant atoms. 6.5 nm is a model input; printed λ definition is ambiguous.'])

def addop(r,key,label,inputs,unit,description,stage='characterization',depends=None,output_kind='analysis_data'):
    oid=PRE+key;out=key+'-state';r['material_states'].append(state(out,label+' — source state',inputs,output_kind))
    op=operation(oid,norm(label).replace('-','_'),label,E(unit),inputs,[out],depends=depends,stage=stage,description=description)
    r['operations'].append(op);OP[oid]=op;bindu(r,unit,f'/operations/{len(r["operations"])-1}');return oid,out
# A sampling progression uses two distinct bulk-state inputs to avoid reusing a measured aliquot.
specimen(growth,'early-growth-bulk','Common-route reaction with 0.02% Mn feed','growth-0.02pct-series','Mn:ZnO')
g1,g1out=addop(growth,'early-aliquot','Collect the early washed and capped aliquot',['early-growth-bulk'],'growth-02-b','Withdraw after 10 min at room temperature; source says all spectra use washed, capped specimens in toluene. Exact washing/capping quantities are unreported. The remaining reaction bulk is not the measured aliquot.',output_kind='aliquot')
specimen(growth,'remaining-growth-bulk','Continuation of the original growth reaction after early sampling','growth-0.02pct-series','Mn:ZnO')
g2,g2out=addop(growth,'continue-ripening','Continue the original reaction at 60 °C',['remaining-growth-bulk'],'growth-02-c','2 h growth at 60 °C; c is a later aliquot. The input is original reaction bulk, not the already measured early aliquot.',stage='synthesis',output_kind='reaction_batch')
g3,g3out=addop(growth,'later-aliquot','Collect the later washed and capped aliquot',[g2out],'growth-02-c','Later aliquot after the stated growth; washed/capped for EPR. This sampling does not assert use of the analyzed aliquot in the subsequent cleaning.',depends=[g2],output_kind='aliquot')
specimen(growth,'later-growth-product','Nanocrystal product from the later-growth stage, independent of the analyzed aliquot c','growth-02-d','Mn:ZnO')
mat(growth,'dodecylamine')
g4,g4out=addop(growth,'clean-growth-product','Wash and heat the later-growth nanocrystal product',['later-growth-product','dodecylamine'],'growth-02-d','Source p. 9390 specifies washing then 180 °C for 30 min for the d specimen. Nitrogen and cooling/workup belong to the linked common amine treatment; this grouped stage is not a fully enumerated independent SOP.',stage='surface_exchange',output_kind='product')
param(growth,g1,'time_after_base_addition','aliquot-early-time');param(growth,g2,'temperature','aliquot-growth-t');param(growth,g2,'duration','aliquot-growth-time');param(growth,g4,'duration','aliquot-clean-time')
OP[g4]['parameters']['temperature']=qty(180,'degC',E('growth-02-d'),qualifier='Explicit specimen d description on main p. 9390; not inferred from a neighboring plot.')
sample(growth,'growth-02-b')['material_state_id']=g1out;sample(growth,'growth-02-c')['material_state_id']=g3out;sample(growth,'growth-02-d')['material_state_id']=g4out
# Acquisition metadata is explicit, with distinct instrument contexts and no fabricated sample joins.
for f in F.values():
    if not f['id'].startswith(SID+'-instrument-'):continue
    key=f['id'].removeprefix(SID+'-instrument-');x=f['value'];unit=f['source_unit_id'];sp='acquisition-specimens-'+key
    specimen(methods,sp,x.get('sample','Specimen or computation context for '+x['technique']),unit,None)
    oid,out=addop(methods,'acquire-'+key,'Acquire or analyze '+x['technique'],[sp],unit,compact(x)+' These are shared method descriptions, not an assertion that every instrument used the same specimen or that simulation curves are measured data.')
    for member,v in x.items():
        if member in KEY_UNITS and isinstance(v,(int,float)) or member=='field_T_range':param(methods,oid,member,f['id'],'/'+member)
        elif member=='cuvette_cm':
            for k in range(2):param(methods,oid,'cuvette_dimension_'+str(k+1),f['id'],'/cuvette_cm/'+str(k))
# The 70-fold dilution belongs specifically to titration remeasurement, not every absorption scan.
OP[PRE+'acquire-abs']['description']+=' The 70-fold redilution refers to the reaction-titration aliquot procedure only.'
for r,key,sid,unit,desc in [
(struct,'prepare-powder','cleaned-0.20pct','cleaned-0.20pct-powder','Rapid precipitation from toluene for powder diffraction/magnetometry. Antisolvent and precise isolation settings are not restated for this rapid specimen preparation; do not assume every powder is the same physical aliquot.'),
(struct,'characterize-structure','cleaned-0.20pct','figure-3','TEM/HRTEM, powder XRD and thin-film XRD apply to the distinct Figure 3 panels. No SAED, refined lattice constants, atomic coordinates or CIF are supplied.'),
(opt,'acquire-optics','optical-series','figure-7','Separate undoped, estimated 0.13% and reported 1.3% dodecylamine-capped colloids. Absorption is normalized at the excitation and emission scaled proportionally; no common exact feed or physical batch is inferred.'),
(mag,'acquire-magnetism','magnetic-specimen-set','figure-8','Separate colloid powder and films A–C measured by SQUID. Preserve temperature, field and model-specific contexts in each reported measurement.'),
(mag,'zfc-series','films-a-b','figure-9','ZFC series for films A and B at 80 Oe; no transition in 5–350 K. This is not a universal impurity-detection limit.'),
(mag,'film-epr','film-a','figure-10','Film A and its precursor have separate spectra. New sharp g = 2.00 resonance has tentative radical/redox interpretation, not measured carrier polarity or nitrogen content.')]:
    sp='input-'+key;specimen(r,sp,sid.replace('-',' '),unit,'Mn:ZnO' if r is not opt else None)
    addop(r,key,key.replace('-',' ').capitalize(),[sp],unit,desc,stage='workup' if key=='prepare-powder' else 'characterization',output_kind='fraction' if key=='prepare-powder' else 'analysis_data')
param(opt,PRE+'acquire-optics','excitation_wavenumber','lum-excitation');param(opt,PRE+'acquire-optics','excitation_absorbance_range','lum-abs-range');param(mag,PRE+'zfc-series','measurement_field','zfc-field')

# All 201 facts have typed destinations. Model/reference numbers keep their own scope.
def destination(f):
    key=f['id'].removeprefix(SID+'-');u=f['source_unit_id']
    if u in M:return reagents,u
    if key.startswith('instrument-'):return methods,u
    if u in ['ct-model','table-s1','table-s2','table-s3'] or key in ['context-MnCl-CB','context-MnBr-CB']:return ct,u
    if '-model-' in key and key.startswith('optical-'):return dopant,u
    if key.startswith('epr-') and key not in ['epr-surface-splitting','epr-clean-splitting']:return epr,u
    if key=='domain-spin-bound':return mag,'films-a-b-c-collective'
    if u=='table-s4':
        sid='film-'+f['value']['film'].lower();return films if sid in ['film-a','film-b','film-c'] else df,sid
    if u in ['theory-context','solubility-reference','oxidation-reference','zno-reference'] or key.startswith('context-'):return refs,u
    if u in PMAP:return PMAP[u],u
    if u in ST:return route if u in ['stock-metal-acetates','stock-tmah'] else surface if u=='stock-lioh-control' else oxid,u
    if u=='cleaned-final-colloids':return clean,u
    if u in ['titration-series','spectral-aliquots']:return titr,u
    if u=='surface-control-epr':return surface,u
    if u.startswith('growth-'):return growth,u
    if u.startswith('cleaned-0.20'):return struct,u
    if u.startswith('oxidation-'):return oxid,u
    if u=='topo-1.1pct':return topo,u
    if u.startswith('optical-'):return opt,u
    if u in ['films-a-b','films-a-b-c']:return mag,u
    if u in ['film-d','film-e','film-f']:return df,u
    if u in ['film-a','film-b','film-c']:
        if key in ['xrd-phase-film','film-xrd-size','film-bandgap']:return struct,u
        if key.startswith(('film-a-','film-b-','film-c-')):return films,u
        return mag,u
    raise AssertionError(('Unassigned source fact',key,u))
def scalar_paths(v,path='',range_root=False):
    if isinstance(v,dict):
        for k,x in v.items():
            p=path+'/'+esc(k)
            if k=='field_T_range':yield p
            else:yield from scalar_paths(x,p)
    elif isinstance(v,list):
        if range_root:yield path
        else:
            for j,x in enumerate(v):yield from scalar_paths(x,path+'/'+str(j))
    else:yield path
for f in F.values():
    r,sid=destination(f);key=f['id'].removeprefix(SID+'-')
    for sub in scalar_paths(f['value'],range_root=key in RANGES):m_fact(r,f['id'],sid,sub)
# Attach specimen-specific descriptive results to product fields as well.
for r,sid,key,ff in [(struct,'cleaned-0.20pct','morphology','morphology'),(struct,'cleaned-0.20pct-powder','phase','xrd-phase-colloids'),(struct,'film-a','phase','xrd-phase-film')]:
    p=sample(r,sid);p[key]=qvalue(ff);bindf(r,ff,f'/products/{r["products"].index(p)}/{key}')
sample(struct,'cleaned-0.20pct')['composition']=fact('Zn0.998Mn0.002O',evidence(F[fid('product-mn')]['evidence']),note='Source-reported nominal composition associated with 0.20 ± 0.01% Mn by ICP-AES, after a 0.50% feed. This is not refined occupancy or a supplied atomic structure.')
for r,keys in [(struct,['cleaned-0.20pct','cleaned-0.20pct-powder']),(growth,['growth-02-b','growth-02-c','growth-02-d']),(opt,['optical-pure-zno','optical-0.13pct','optical-1.3pct'])]:
    for sid in keys:sample(r,sid)['surface']=fact('dodecylamine-capped',E(sid),note='Named capping ligand only; no surface coverage, binding geometry or retained nitrogen concentration is inferred.')
sample(topo,'topo-1.1pct')['surface']=fact('TOPO-capped',E('topo-1.1pct'),note='Alternative treatment; exact ligand density and atomistic surface geometry unreported.')
sample(surface,'surface-control-epr')['material_state_id']=OUT['protocol-surface-control']['surface-control-epr']
sample(topo,'topo-1.1pct')['material_state_id']=OUT['protocol-topo']['topo-frozen-solution']
sample(titr,'titration-series')['material_state_id']=OUT['protocol-titration']['titration-series']
sample(struct,'cleaned-0.20pct-powder')['material_state_id']='prepare-powder-state'
for key in M:mat(reagents,key,'characterization','source_material_identity')

# Preserve complete source inventory objects with exact inventory pointers, including
# all table cells, source variants, notes, unresolved joins and the full bibliography.
# The serialized payload is context, not a new recipe or measured property target.
FIG_DEST={'figure-1':titr,'figure-2':growth,'figure-3':struct,'figure-4':oxid,'figure-5':epr,'figure-6':topo,'figure-7':opt,'figure-8':mag,'figure-9':mag,'figure-10':mag,'figure-s1-equations':dopant,'figure-s2':mag,'figure-s3':df,'table-s1':ct,'table-s2':ct,'table-s3':ct,'table-s4':df,'scheme-1':intuition}
EQ_DEST={'equation-1':epr,'equation-2':oxid,'equation-3':ct,'equation-4':mag,'equation-s1':dopant,'equation-s2':dopant,'mcd-definition':methods}
OBJECT_DEST={}
for (cat,key),(ix,obj) in O.items():
    if cat=='materials':r=reagents
    elif cat=='stocks':r=route if key in ['stock-metal-acetates','stock-tmah'] else surface if key=='stock-lioh-control' else oxid
    elif cat=='protocols':r=PMAP[key]
    elif cat=='samples':r=SAMPLE_RECORD[key]
    elif cat=='figures_tables_schemes':r=FIG_DEST[key]
    elif cat=='equations':r=EQ_DEST[key]
    elif cat=='tables':r=ct if key!='table-s4' else df
    elif cat=='chemical_intuition':r=intuition
    else:r=refs
    OBJECT_DEST[(cat,key)]=r
    ev=evidence(obj['evidence']) if obj.get('evidence') else E(key)
    if cat=='references':ev=[{'source_id':SID,'locator':('SI' if obj['source_role']=='si' else 'Main')+f" PDF p. {obj['pdf_page']}, reference {obj['reference_number']}"}]
    ptr=context(r,'inventory-'+cat+'-'+key,compact(obj),ev,prop='source_inventory_'+cat,note='Exact source-inventory payload. Classification and source scope apply to all fields. This is not a measured target or an additional experimental record.')
    bindo(cat,key,r,ptr,'lossless_inventory_context_payload');bindu(r,key,ptr)
    if cat=='chemical_intuition':
        ptr=context(intuition,key,obj['claim'],ev,prop='author_interpretation',status='author_derived',note=obj['classification']+'; do not treat as a demonstrated mechanism or measured outcome.');bindo(cat,key,intuition,ptr)
    if cat=='equations':
        ptr=context(r,key,obj['expression'],ev,prop='source_equation',status='author_derived' if key!='mcd-definition' else 'reported',note=obj['classification']+'. '+obj['meaning']);bindo(cat,key,r,ptr)
    if cat=='figures_tables_schemes':
        ptr=context(r,key,obj.get('title',key.replace('-',' ').capitalize())+'. '+obj.get('notes',''),ev,prop='original_figure_scope',note='Original asset ID '+obj['asset_id']+'. Numeric plot traces remain undigitized; measured, reference and model panels retain their individual sample scopes.');bindo(cat,key,r,ptr)
        asset=ASSETS[obj['asset_id']]
        r['context_links'].append({'label':obj.get('title',key.replace('-',' ').capitalize()),'url':'../'+asset['path'].replace('\\','/'),'relation':'Existing private original evidence asset '+obj['asset_id']+'; SHA-256 '+asset['sha256']+'. Relative to this private canonical-drafts folder. Reader integration must establish the eventual public evidence route; this is not an atomic-structure download.'})
    if cat=='references':
        ptr=context(refs,key,obj.get('bibliography_extracted_text',obj.get('bibliography_transcription')),ev,prop='cited_bibliography',note=obj['inspection_status']+' '+obj['role']);bindo(cat,key,refs,ptr)
    if cat=='gaps':bindo(cat,key,refs,f'/quality/missing_fields/{ix}')
# Complete source-unit mapping uses the union of independently reviewed source units
# and typed-fact scopes; unnumbered intuition/gap/administrative objects are also
# exhaustively covered by the separate full inventory-object mapping.
for unit,links in unit_links.items():
    assert links,('Unmapped source unit',unit)
for ff,links in fact_links.items():assert links,('Unmapped source fact',ff)
for key,r in records.items():
    if r is not route:r['context_links'].append({'label':'Common Mn:ZnO hydrolysis preparation','url':'../records/'+PRE+'hydrolysis.html','relation':'Same source family, not a claim of identical specimen, exact batch or complete quantitative preparation. Source group is shared to prevent training/test leakage.'})
for key,r in records.items():
    if r is not route:route['context_links'].append({'label':r['title'].split(' · ',1)[1],'url':'../records/'+r['record_id']+'.html','relation':'Distinct source procedure, sample, property or interpretation scope; not another independently enumerated synthesis recipe.'})

# Author validation: schema, all exact source-to-field values, coverage and boundaries.
checks=[];errors=[]
def check(ok,label):checks.append({'check':label,'passed':bool(ok)});assert ok,label
by_id={r['record_id']:r for r in records.values()}
for r in records.values():
    err=validate_record(r);errors.extend(err)
    if err:print(r['record_id'],compact(err))
    check(not err,r['record_id']+' current schema and semantic validation')
    check(r['quality']['review_status']=='imported_unreviewed' and not r['quality']['requested_tasks'] and 'collection' not in r,r['record_id']+' private imported state')
    check(not any(x['eligible'] for x in eligibility(r).values()),r['record_id']+' zero training eligibility')
    check(not r['structure_assets'] and r['intended_target']['size']['value'] is None,r['record_id']+' no exact atomic assets or inferred size target')
    check(r['lineage']['batch_id'] is None and all(p['batch_id'] is None for p in r['products']),r['record_id']+' no invented experimental batch identity')
for ff,links in fact_links.items():
    for binding in links:check(resolve(by_id[binding['record_id']],binding['pointer'])==qvalue(ff,binding['source_value_pointer']),ff+' exact typed source binding '+binding['source_value_pointer'])
for unit,links in unit_links.items():
    for binding in links:resolve(by_id[binding['record_id']],binding['pointer'])
    check(bool(links),unit+' mapped source-unit scope')
for binding in object_links:
    v=resolve(by_id[binding['record_id']],binding['pointer']);obj=resolve(I,binding['source_pointer'])
    if binding['mode']=='lossless_inventory_context_payload':check(json.loads(v['value'])==obj,binding['source_pointer']+' complete exact inventory payload')
for cat in CATEGORIES:
    expected={key for c,key in O if c==cat};actual={b['source_object_id'] for b in object_links if b['category']==cat and b['mode']=='lossless_inventory_context_payload'}
    check(expected==actual,cat+' complete original-object coverage')
for op in op_links:check(resolve(by_id[op['record_id']],op['pointer'])['id']==OP_SOURCE[op['source_operation_id']],op['source_operation_id']+' operation binding')
check(len(op_links)==26,'All 26 original protocol operations mapped once')
check(sum(r['record_type']=='literature_protocol' for r in records.values())==1,'One common nanocrystal route, not an inflated recipe count')
check(len(df['operations'])==0,'Films D–F have no invented preparation operations')
check(all(p['parent_sample_id'] is None for p in df['products']),'Films D–F have no invented parent batches')
check(not any('amine-cleaning' in o['id'] or o['parameters'].get('temperature',{}).get('value')==180 for o in surface['operations']),'Surface-bound reference does not receive surface-stripping treatment')
check(OP[PRE+'topo-op-1']['parameters']['temperature']['value'] is None and OP[PRE+'topo-op-1']['parameters']['duration']['value'] is None,'TOPO temperature and duration remain unknown')
check(OP[PRE+'amine-cleaning-op-1']['parameters']['duration']['approximate'] is True and OP[g4]['parameters']['duration']['approximate'] is False,'Common ca. 30 min and specific growth d 30 min remain distinct')
check(OP[PRE+'amine-cleaning-op-2']['parameters']['precipitation_temperature_limit']['maximum']==80 and OP[PRE+'amine-cleaning-op-2']['parameters']['precipitation_temperature_limit']['maximum_exclusive'] is True,'Cooling is strictly below 80 °C, not a hold at 80 °C')
check(OP[g2]['inputs']==['remaining-growth-bulk'] and OP[g4]['inputs'][0]=='later-growth-product','Later specimens do not consume earlier measured aliquots')
db=fact_links[fid('domain-spin-bound')]
check(all(next(m for m in by_id[b['record_id']]['measurements'] if m['value']==resolve(by_id[b['record_id']],b['pointer']))['sample_id']=='films-a-b-c-collective' for b in db),'S > 800 is collective A–C/unspecified-film scope, never film A alone')
for ff in ['film-d-Ms-emu','film-d-Ms-per-Mn','film-f-Ms-emu','film-f-Ms-per-Mn','table-s4-row-4','table-s4-row-6']:
    for b in fact_links[fid(ff)]:
        q=resolve(by_id[b['record_id']],b['pointer']);check('unresolved' in (q.get('qualifier','')+q.get('note','')),ff+' exports unresolved D/F labels with the value')
check(not any(o['parameters'].get('pressure',{}).get('value') is not None for r in records.values() for o in r['operations']),'No cited 1 kbar or 900 °C oxygen-pressure context becomes process pressure')
check(all(not any(p['phase']['value'] for p in r['products']) for r in records.values() if r is not struct),'XRD phase claims restricted to the identified structural specimen record')
groups=build_groups(list(records.values()));check(len(set(groups.values()))==1,'All records belong to one source split group')
for name,h in A['audited_artifacts'].items():check(sha(B/name)==h,name+' unchanged audited source artifact')
for doc in A['source_documents']:check(sha(doc['path'])==doc['sha256'],doc['path']+' original source unchanged')
for asset in ASSETS.values():check(sha(B/asset['path'])==asset['sha256'],asset['id']+' existing original evidence asset unchanged')
out=B/'canonical-drafts';out.mkdir(exist_ok=True)
for r in records.values():save(out/(r['record_id']+'.json'),r)
counts={'records':len(records),'record_types':dict(Counter(r['record_type'] for r in records.values())),'common_nanocrystal_routes':1,'complete_laboratory_SOPs':0,'operations':sum(len(r['operations']) for r in records.values()),'original_protocol_operations':len(op_links),'measurements_and_context_claims':sum(len(r['measurements']) for r in records.values()),'material_slots':sum(len(r['materials']) for r in records.values()),'stock_slots':sum(len(r['stocks']) for r in records.values()),'samples_and_contexts':sum(len(r['products']) for r in records.values()),'source_facts':len(F),'source_fact_bindings':sum(map(len,fact_links.values())),'source_units':len(U),'audited_source_inventory_units':len(set(A['reviewed_source_unit_ids'])),'source_unit_bindings':sum(map(len,unit_links.values())),'original_inventory_objects':len(O),'source_object_bindings':len(object_links),'source_references':len(I['references']),'source_figures_tables_schemes':len(I['figures_tables_schemes']),'source_equations':len(I['equations']),'source_tables':len(I['tables']),'source_gaps':len(I['gaps'])}
pending=['Independent canonical scientific audit against exact files and source joins.','All 14 source gaps and printed D/F, TMAH and statistical-notation conflicts remain preserved; canonical validity does not resolve them.','Reader/figure, molecule, apparatus and crystal/product scope integration followed by independent visual/source review.','No exact-structure, full-SOP, success-label, raw-curve, training-task or public-release approval.']
manifest={'schema':'mattersyn-canonical-draft-manifest/1','source_id':SID,'status':'private_draft_schema_valid_pending_canonical_scientific_audit','created_at':datetime.now(timezone.utc).isoformat(),'counts':counts,'source_extraction_audit_sha256':sha(B/'source-scientific-audit.json'),'source_inventory_sha256':sha(B/'source-inventory.json'),'source_facts_sha256':sha(B/'source-facts.json'),'page_coverage_sha256':sha(B/'page-coverage.json'),'original_sources':[{'path':d['path'],'sha256':sha(d['path'])} for d in A['source_documents']],'build_script_sha256':sha(__file__),'dataset_validator_sha256':sha(S/'scripts/dataset_lib.py'),'schema_definition_sha256':sha(S/'scripts/schema_definition.py'),'record_helpers_sha256':sha(S/'scripts/record_helpers.py'),'split_groups':groups,'records':[{'record_id':r['record_id'],'record_type':r['record_type'],'path':str(out/(r['record_id']+'.json')),'sha256':sha(out/(r['record_id']+'.json')),'operations':[o['id'] for o in r['operations']],'samples':[p['sample_id'] for p in r['products']],'training_tasks':eligibility(r)} for r in records.values()],'pending_links_and_gates':pending,'published':False,'training_eligible':False}
save(B/'canonical-record-manifest.json',manifest)
coverage={'schema':'mattersyn-canonical-source-coverage/1','source_id':SID,'status':'complete_author_mapping_not_independent_audit','source_facts_sha256':sha(B/'source-facts.json'),'source_inventory_sha256':sha(B/'source-inventory.json'),'source_scientific_audit_sha256':sha(B/'source-scientific-audit.json'),'facts':[{'source_fact_id':key,'source_fact':F[key],'canonical_bindings':links} for key,links in fact_links.items()],'source_units':[{'source_unit_id':u,'in_independent_source_inventory_audit':u in A['reviewed_source_unit_ids'],'canonical_bindings':links} for u,links in sorted(unit_links.items())],'source_objects':object_links,'source_operations':op_links,'status_normalization':'Source statuses remain in every field basis/note and the exact source fact here. Author model/fit/estimate/interpretation maps to author_derived. Reported inputs to a model and cited/reference values map to reported with explicit nonmeasurement/model-input scope. Source-table mixed calculated and cited columns remain separately keyed. No model is recomputed.','numeric_normalization':'Ordered lists and object fields map to individually indexed typed members; reported intervals map to bounds. Explicit strict limits retain exclusive bounds. Source uncertainty objects are preserved verbatim in field qualifiers and in the full source fact; their statistical definition is not invented. Empty units preserve the absence of an explicit source unit.','inventory_payload_policy':'Every original object is losslessly preserved in a schema-valid source-context field plus semantic fields where appropriate. Administrative notes, bibliography, models and incomplete procedures are not new synthesis records.','source_unit_universe':'Union of independently audited source-unit IDs and the 201 typed facts’ source_unit_id values. Complete inventory objects, including unnumbered administrative, gap and intuition entries, are exhaustively counted and bound separately.','input_and_sample_normalization':'Named preceding states replace re-added products. Fractions retain source-described precipitates. Aliquot c is later growth, not reuse of measured b; d uses later-growth material, not a recycled analyzed aliquot. A–C recipe fields are not assigned to D–F; controls and instrument sample sets are not pooled mixtures or invented replicates.'}
save(B/'canonical-source-coverage.json',coverage)
save(B/'canonical-draft-validation.json',{'schema':'mattersyn-private-draft-validation/1','status':'passed','created_at':datetime.now(timezone.utc).isoformat(),'scope':'Author current schema/semantics, exact fact-field equality, complete source/object/operation coverage, missingness and sample/recipe-boundary checks. Not independent canonical scientific approval.','author_source_rechecks':{'all_201_typed_facts_read':True,'all_inventory_categories_read':True,'targeted_original_visual_rechecks':['main-03.png','main-04.png','si-4.png'],'full_source_audit_scope':'The existing independent source audit is authoritative for all 12 main and four SI pages; this task did not redundantly re-audit all 16 pages.','original_copies_rehashed':4},'counts':counts,'checks':checks,'schema_errors':errors,'record_hashes':{r['record_id']:sha(out/(r['record_id']+'.json')) for r in records.values()},'canonical_manifest_sha256':sha(B/'canonical-record-manifest.json'),'coverage_sha256':sha(B/'canonical-source-coverage.json'),'published':False,'training_eligible':False,'pending_links_and_gates':pending})
print(compact(counts))
