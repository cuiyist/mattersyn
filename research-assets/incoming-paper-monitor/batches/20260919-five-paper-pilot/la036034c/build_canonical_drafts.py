"""Private Nagasaki canonical authoring from the passed complete-source extraction.
No Site/source/shared ledger files are written. Source statements remain scoped.
"""
from pathlib import Path
from copy import deepcopy
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,sys,re
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent
S=Path(r'[local path redacted]')
sys.path.insert(0,str(S/'scripts'))
from record_helpers import record,source,fact,qty,material,operation,state,product,measurement
from dataset_lib import validate_record,eligibility,build_groups
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
D=read(B/'source-facts.json');I=read(B/'source-inventory.json');A=read(B/'source-scientific-audit.json');PAGES=read(B/'page-coverage.json')
assert A['status']=='passed_with_preserved_source_ambiguities'
for name,h in A['author_artifact_sha256'].items():assert sha(B/name)==h,(name,'changed audited source artifact')
for d in A['original_copies_independently_verified']:assert sha(d['path'])==d['sha256'],('source bytes changed',d['path'])
SID='nagasaki2004';PRE='nagasaki-2004-'
F={f['id']:f for f in D['facts']};U={u['id']:u for u in I['source_units']};M={m['id']:m for m in D['materials']};PRO={p['id']:p for p in D['protocols']}
assert len(F)==49 and len(U)==32
fact_links={k:[] for k in F};unit_links={k:[] for k in U};object_links=[];records={}
def evidence(items):
    return [{'source_id':SID,'locator':('SI' if e['source_id'].endswith('-si') else 'Main')+f" PDF p. {e['pdf_page']}"+(f" (printed {e['printed_page']})" if e.get('printed_page') else '')+', '+e.get('section','Source text')+(('; '+str(e['item'])) if e.get('item') else '')} for e in items]
def E(uid):return evidence(U[uid]['evidence'])
def fid(short):return short if short.startswith(SID+'-') else SID+'-'+short
def norm(s):return re.sub('[^a-z0-9]+','-',s.lower()).strip('-')
def bind_fact(r,short,pointer,index=None,conversion='exact_scalar'):
    fact_links[fid(short)].append({'record_id':r['record_id'],'pointer':pointer,'source_array_index':index,'conversion':conversion})
def bind_unit(r,uid,pointer):
    if uid in U:unit_links[uid].append({'record_id':r['record_id'],'pointer':pointer})
def bind_obj(category,objid,r,pointer):object_links.append({'category':category,'source_object_id':objid,'record_id':r['record_id'],'pointer':pointer})
conflicts={c['id']:f"{c['id']} — {c['topic']}. Source claim: {c['source_claim']} Visual observation: {c['visual_observation']} Resolution: {c['resolution']}" for c in D['contradictions']}
gaps=[f"{g['id']} ({g['scope']}): {g['missing']} {g['impact']}" for g in D['gaps']]
SRC=source(SID,D['doi'],D['title'],'; '.join(D['authors']),2004,si='Matched three-page SI verified by manuscript metadata/content and identical copies. All three pages text-read and visually inspected in the independent source audit.')
SRC['main_status']='All five supplied main pages completely read and visually inspected; source audit passed with four preserved source ambiguities. These canonical drafts await independent canonical scientific audit.'
SRC['reuse_status']='Private source-linked factual extraction; original article/figure rights remain separate. No public reuse license inferred.'
def base(key,title,kind='observation',formula='CdS',method='Source-scoped observation',surface=None):
    r=record(PRE+key,'Nagasaki et al. (2004) · '+title,formula,'Polymer-stabilized CdS and related source procedures',method,deepcopy(SRC),'Supplied five-page main article and matched three-page SI',kind)
    r['schema_version']='1.3.0' # optional collection deliberately absent for private imported drafts
    r['lineage'].update(source_group=SID,recipe_family='nagasaki2004-aqueous-polymer-cds')
    if formula=='CdS':r['material'].update(elements=['Cd','S'],components=['CdS'],architecture='single_material')
    r['quality'].update(review_status='imported_unreviewed',requested_tasks=[],review_scope='Private canonical author draft from complete independently audited main+SI extraction. Canonical scientific, reader/visual and publication review remain pending; no independent experimental replicate is claimed.',missing_fields=deepcopy(gaps),conflicts=list(conflicts.values()),experimental_outcome='reported_product' if kind=='literature_protocol' else 'not_established')
    if kind not in ['literature_protocol','protocol_variant']:r['intended_target']['composition']=fact(None,E('cho-cds-representative'),note='Supporting procedure or context record, not a separately verified target-synthesis experiment.')
    if surface:r['intended_target']['surface']=fact(surface,E('biotin-cds' if key=='biotin-cds' else 'cho-cds-representative'),note='Named stabilizer/end group; no numerical grafting density or atomistic surface geometry.')
    records[key]=r;return r
def mat(r,key,stage='precursor_preparation',role=None):
    if any(m['id']==key for m in r['materials']):return key
    m=M[key];notes=[m['notes'],f"Source role: {m['role']}.",f"Supplier: {m['supplier_as_reported'] or 'not reported'}.",f"Pretreatment/storage: {m['pretreatment_storage']}.",'Source supplies no verified molecular coordinates; null formula is not an inferred chemical identity.']
    notes=[s for s in notes if s]
    role=role or {'cdcl2':'metal_precursor','na2s':'chalcogen_precursor','water':'solvent','cho-peg-pama':'ligand','biotin-peg-pama':'ligand'}.get(key,norm(m['role']).replace('-','_'))
    mm=material(key,m['name'],m['formula_as_printed'],role,stage,evidence(m['evidence']),quantities={'purity':qty(unit='%',evidence=evidence(m['evidence']),qualifier='Reagent purity is not reported.')},notes=notes)
    idx=len(r['materials']);r['materials'].append(mm);bind_obj('materials',key,r,f'/materials/{idx}');return key
def specimen(r,key,name,formula='CdS',uid='cho-cds-representative',notes=None):
    if any(m['id']==key for m in r['materials']):return key
    r['materials'].append(material(key,name,formula,'specimen','characterization',E(uid),notes=notes or ['Source-described specimen identity only; exact batch, end-group identity and cross-technique aliquot linkage are not inferred.']))
    return key
def add_sample(r,sid,label,formula='CdS',uid='cho-cds-representative',state_id=None,link='general_context',notes=None):
    found=next((p for p in r['products'] if p['sample_id']==sid),None)
    if found:return found
    p=product(sid,formula,E(uid),link=link,state=state_id,notes=notes or ['Context/sample label, not a verified unique experiment or shared physical aliquot across techniques.'])
    p['source_sample_label']=label;r['products'].append(p);return p
def qvalue(short,index=None):
    short=short.removeprefix(SID+'-')
    f=F[fid(short)];v=f['value'];ev=evidence(f['evidence']);status={'author_model_derived':'author_derived','reported_qualitative':'reported'}.get(f['status'],f['status'])
    qual=f['qualifier'];basis='Source scope: '+f['source_unit_id']+'.'
    if f['source_unit_id'] in ['figure2-series','cho-cds-low-amine','cho-cds-high-amine','figure2-absorption-sample-unresolved'] or short in ['amine-mid','amine-low','amine-high','fig2-cds-concentration']:
        qual+=' C1 remains unresolved; caption concentration labels and prose trend are not reconciled.'
    if f['id'].endswith('fig4-protein-labels'):qual+=' C4: explicit text/caption identifies streptavidin, although graph abbreviates Tex-Avidin. Legend labels are not independent replicate rows.'
    if f['status']=='reported_qualitative':return fact(f['raw_text'],ev,status,note=qual)
    if f['status']=='author_model_derived':basis+=' Author band-gap-model estimate, not a measured TEM diameter; original sizing equation is not reproduced or recomputed.'
    if f['unit'] is None:basis+=' Unit is not explicitly supplied; empty unit does not assert dimensionless quantity.'
    if isinstance(v,list):
        if f['id'].endswith(('zeta-ph-range','xrd-range')):return qty(unit=f['unit'],minimum=v[0],maximum=v[1],evidence=ev,status=status,approximate=f['approximate'],qualifier=qual,basis=basis,raw_text=f['raw_text'])
        assert index is not None,(short,'ordered list requires explicit member')
        v=v[index];basis+=f' Ordered source list index {index}; original array preserved in coverage.'
    return qty(v,f['unit'] or '',ev,status=status,approximate=f['approximate'],qualifier=qual,basis=basis,raw_text=f['raw_text'])
def param(r,op,key,short,index=None):
    q=qvalue(short,index);assert 'unit' in q,'Nonquantitative source value cannot be an operation parameter'
    op['parameters'][key]=q;i=r['operations'].index(op)
    conv='bounds_from_reported_range' if isinstance(F[fid(short)]['value'],list) and index is None else 'ordered_list_member' if index is not None else 'exact_scalar'
    bind_fact(r,short,f'/operations/{i}/parameters/{key}',index,conv)
def m_fact(r,short,sid,tech,index=None,property_name=None):
    f=F[fid(short)];q=qvalue(short,index);id_=norm(f['property'])+(('-'+str(index)) if index is not None else '')
    if any(m['id']==id_ for m in r['measurements']):id_+='-'+sid
    mm=measurement(id_,sid,property_name or norm(f['property']).replace('-','_'),q,tech,evidence(f['evidence']),conditions=f['source_unit_id'])
    i=len(r['measurements']);r['measurements'].append(mm)
    conv='bounds_from_reported_range' if isinstance(f['value'],list) and index is None else 'ordered_list_member' if index is not None else 'qualitative_raw_text' if f['status']=='reported_qualitative' else 'exact_scalar'
    bind_fact(r,short,f'/measurements/{i}/value',index,conv);return i
def context(r,id_,sid,text,ev,prop='source_context',status='reported',note=''):
    idx=len(r['measurements']);r['measurements'].append(measurement(id_,sid,prop,fact(text,ev,status,note), 'Source text / original figure context',ev));return f'/measurements/{idx}/value'
def link(r,target,label,relation):r['context_links'].append({'label':label,'url':'../records/'+PRE+target+'.html','relation':relation})

# Record boundaries distinguish synthesis, upstream preparation, assays and source context.
poly=base('polymer-preparation','PDP and acetal-PEG/PAMA preparation','procedure','PEG/PAMA','Sequential EO/AMA polymerization and purification')
ald=base('aldehyde-polymer','Acetal-to-aldehyde polymer conversion','procedure','CHO-PEG/PAMA','End-group hydrolysis and dialysis')
bio=base('biotin-polymer','Biotin installation before dialysis','procedure','biotin-PEG/PAMA','Hydrazide coupling and reduction')
route=base('cho-cds','CHO-PEG/PAMA-stabilized CdS coprecipitation','literature_protocol',method='Aqueous coprecipitation',surface='CHO-PEG/PAMA stabilizer')
variant=base('biotin-cds','Biotin-PEG/PAMA CdS variant; incompletely quantified','protocol_variant',method='Aqueous coprecipitation using the reported similar-manner framework',surface='Biotin-PEG/PAMA stabilizer')
controls=base('stabilizer-controls','No-polymer, PEG and PAMA stabilization controls',method='Source-reported coprecipitation controls')
series=base('concentration-series','Figure 2 polymer-concentration variants and unresolved PL trend',method='Source formulation comparison, not independent replicate records')
salt=base('salt-challenge','Salt-dependent dispersion and fluorescence comparisons','procedure',method='Source-scoped salt stability comparison')
opt=base('optical','Absorption, fluorescence and author-derived size','procedure',method='UV–visible and steady-state fluorescence')
zeta=base('zeta','pH-dependent zeta-potential series','procedure',method='Electrophoretic zeta-potential measurement')
fret=base('fret','Biotin-CdS/TexasRed-streptavidin recognition series','procedure',method='Source-reported fluorescence resonance energy transfer assay')
competition=base('recognition-controls','Unlabeled streptavidin and BSA competition contexts','procedure',method='Recognition inhibition controls; concentration identity unresolved')
tem=base('tem','Generic PEG/PAMA-CdS TEM specimen preparation and imaging','procedure',method='Energy-filtered transmission electron microscopy')
xrd=base('xrd','Generic PEG/PAMA-CdS and polymer XRD specimen contexts','procedure',method='Powder X-ray diffraction')
intuition=base('chemical-intuition','Author interpretations, alternatives and outlook',method='Source-supported interpretation with uncertainty')
refs=base('source-context','Bibliography, source limitations and administrative context',method='Bibliographic and source-scope context')
PRO_MAP={'pdp-preparation':poly,'acetal-block-polymer':poly,'aldehyde-polymer':ald,'biotin-polymer':bio,'cho-cds-representative':route,'biotin-cds':variant,'no-polymer-control':controls,'peg-control':controls,'pama-control':controls,'cho-cds-low-amine':series,'cho-cds-high-amine':series,'salt-challenge':salt,'zeta-assay':zeta,'fret-assay':fret,'streptavidin-competition':competition,'bsa-control':competition,'tem-preparation':tem,'xrd-preparation':xrd}
LABELS={
'pdp-form':'Prepare PDP initiator solution in THF','eo-add':'Add condensed ethylene oxide via a cooled syringe','eo-react':'Allow the EO reaction for two days','ama-block':'Add AMA and stir for a further 60 minutes','polymer-precipitate':'Precipitate the block copolymer in excess 2-propanol','pama-protonate':'Protonate the PAMA segment','soxhlet-clean':'Remove residual PEG prepolymer by THF Soxhlet extraction','hydrolyze-acetal':'Hydrolyze the acetal end group at 35 °C','neutralize':'Neutralize with NaOH','dialyze-polymer':'Dialyze the CHO polymer against water','biotin-condense':'React biocytin hydrazide before polymer dialysis','biotin-reduce':'Reduce the formed Schiff base with NaBH₄','biotin-dialysis-context':'Retain the reported before-dialysis branch context','polymer-medium':'Prepare the 8 mL aqueous polymer medium','cd-add':'Add cadmium chloride first','s-add':'Add sodium sulfide second','cds-stir':'Stir the coprecipitation mixture for one hour','cds-dialyze':'Purify the CdS dispersion by water dialysis','biotin-cds-coprecipitate':'Use biotin-PEG/PAMA in the similar-manner CdS preparation','no-polymer-control-prepare':'Compare coprecipitation without a polymer','peg-control-prepare':'Compare coprecipitation with PEG-OH','pama-control-prepare':'Compare coprecipitation with PAMA homopolymer','cho-cds-low-amine-prepare':'Retain Figure 2a as a low-amine formulation variant','cho-cds-high-amine-prepare':'Retain Figure 2c as a high-amine formulation variant','salt-expose':'Compare prepared dispersions across reported salt conditions','zeta-medium':'Adjust and measure the zeta-potential series','fret-mix':'Combine biotin-CdS with TexasRed-streptavidin for fluorescence','streptavidin-competition-premix':'Premix unlabeled streptavidin before the labeled-protein assay','bsa-control-premix':'Premix unlabeled BSA before the labeled-protein assay','tem-grid-dry':'Deposit a dilute specimen and allow the grid to dry in air','xrd-freeze-dry':'Prepare separate freeze-dried specimens on glass slides','xrd-scan':'Acquire the powder diffraction pattern'}
PARAM_KEYS={'pdp-amount':'reported_PDP_amount','thf-volume':'THF_volume','eo-amount':'ethylene_oxide_amount','eo-time':'duration','ama-amount':'AMA_amount','ama-time':'duration','hydrolysis-time':'duration','hydrolysis-temperature':'temperature','biotin-time':'duration','aqueous-volume':'initial_polymer_solution_volume','amine-mid':'amine_group_concentration','cdcl2-concentration':'reported_CdCl2_concentration_basis_unresolved','na2s-concentration':'reported_Na2S_concentration_basis_unresolved','cds-stir-time':'duration','peg-control-mn':'PEG_control_Mn_unit_unreported','pama-control-mn':'PAMA_control_Mn_unit_unreported','amine-low':'amine_group_concentration','amine-high':'amine_group_concentration','fig2-cds-concentration':'nominal_CdS_concentration','salt-stability':'NaCl_challenge_concentration','zeta-ph-range':'measurement_pH_range','zeta-nacl':'NaCl_measurement_concentration','zeta-ph-adjusters':'pH_adjuster_reported_concentration','fret-ionic-strength':'ionic_strength','fret-cds-concentration':'initial_nominal_CdS_concentration','pl-excitation':'excitation_wavelength','xrd-voltage':'tube_voltage','xrd-current':'tube_current','xrd-range':'two_theta_range','xrd-step':'two_theta_step'}
INPUT_OVERRIDE={
'eo-add':['pdp-solution','eo'],'eo-react':['eo-reaction-mixture'],'ama-block':['peg-prepolymer-reaction-mixture','ama'],'polymer-precipitate':['acetal-block-reaction-mixture','2-propanol'],'pama-protonate':['precipitated-acetal-block-polymer','protonating-agent-unspecified'],'soxhlet-clean':['protonated-acetal-block-polymer','thf'],
'neutralize':['aldehyde-polymer-acid-mixture','naoh'],'dialyze-polymer':['neutralized-cho-peg-pama-mixture','water'],'biotin-condense':['cho-polymer-before-dialysis','biocytin-hydrazide'],'biotin-reduce':['biotin-schiff-base-polymer-mixture','nabh4'],'biotin-dialysis-context':['biotin-peg-pama-mixture','water'],
'cd-add':['aqueous-cho-polymer-medium','cdcl2'],'s-add':['cadmium-polymer-mixture','na2s'],'cds-stir':['cds-coprecipitation-mixture'],'cds-dialyze':['cho-polymer-cds-dispersion','water'],
'salt-expose':['salt-no-polymer-specimen','salt-peg-specimen','salt-pama-specimen','salt-cho-specimen','nacl'],
'zeta-medium':['zeta-dispersion','nacl'],'fret-mix':['biotin-cds-specimen','texasred-streptavidin'],'streptavidin-competition-premix':['biotin-cds-specimen','streptavidin','texasred-streptavidin'],'bsa-control-premix':['biotin-cds-specimen','bsa','texasred-streptavidin'],
'tem-grid-dry':['si-tem-dispersion','tem-grid'],'xrd-freeze-dry':['si-xrd-cds-dispersion','polymer-only-xrd','glass-slide'],'xrd-scan':['freeze-dried-xrd-specimens']}
specimen(bio,'cho-polymer-before-dialysis','Neutralized CHO-PEG/PAMA mixture before dialysis',None,'biotin-polymer',['Branch starts before the preceding polymer-dialysis operation, not from an assumed already-dialyzed stock. Exact amount and composition remain unreported.'])
bio['materials'][-1]['stage']='precursor_preparation';bio['materials'][-1]['role']='polymer_intermediate'
for r,items in [(salt,[('salt-no-polymer-specimen','CdS without polymer'),('salt-peg-specimen','PEG-OH/CdS control'),('salt-pama-specimen','PAMA/CdS control'),('salt-cho-specimen','CHO-PEG/PAMA-CdS')]),(zeta,[('zeta-dispersion','Figure 3 CdS dispersion; exact Figure 2 member unresolved')]),(fret,[('biotin-cds-specimen','Preformed biotin-PEG/PAMA-CdS dispersion')]),(competition,[('biotin-cds-specimen','Preformed biotin-PEG/PAMA-CdS dispersion')]),(tem,[('si-tem-dispersion','Dilute PEG/PAMA-CdS; end group and batch unresolved')]),(xrd,[('si-xrd-cds-dispersion','PEG/PAMA-CdS dispersion; end group and batch unresolved')])]:
    uid=next(pid for pid,rr in PRO_MAP.items() if rr is r)
    for k,n in items:specimen(r,k,n,uid=uid)
last_by_proto={};out_by_proto={};op_source_map=[]
for proto in D['protocols']:
    r=PRO_MAP[proto['id']];prev=None
    if proto['id']=='acetal-block-polymer':prev='pdp-form'
    for item in proto['operations']:
        oid=item['id'];stage='precursor_preparation' if r in [poly,ald,bio] else 'synthesis' if r in [route,variant,controls,series] else 'characterization'
        if oid in ['polymer-precipitate','soxhlet-clean','dialyze-polymer','biotin-dialysis-context','cds-dialyze']:stage='workup'
        inputs=INPUT_OVERRIDE.get(oid,item['input_material_ids'])
        for key in inputs:
            if key in M:mat(r,key,stage)
            else:assert any(s['id']==key for s in r['material_states']) or any(m['id']==key for m in r['materials']),(oid,key)
        output=item['output_state_id'];kind='sample_set' if r in [salt,zeta,fret,competition] or oid=='xrd-freeze-dry' else 'analysis_data' if oid=='xrd-scan' else 'fraction' if item['retained_fraction'] else 'reaction_batch'
        r['material_states'].append(state(output,LABELS[oid]+' — source output',inputs,kind))
        extras=[]
        if item['conditions']:extras.append('Source conditions: '+json.dumps(item['conditions'],ensure_ascii=False,separators=(',',':')))
        if item['discarded_fraction']:extras.append('Source-described discarded fraction: '+item['discarded_fraction']+'. No additional chemical identity is inferred.')
        extras.append('Unreported: '+', '.join(item['unreported_fields'])+'.')
        if proto['notes']:extras.append(proto['notes'])
        if proto['inherited_framework']:extras.append('Framework relation: '+json.dumps(proto['inherited_framework'],ensure_ascii=False,separators=(',',':'))+'. No unreported quantitative values are copied.')
        if r in [controls,series,salt,fret,competition]:extras.append('This operation denotes a source comparison or series scope; it does not enumerate independent experimental replicates.')
        if oid=='salt-expose':extras.append('Inputs denote separate prepared comparison specimens, not a mixture of stabilizers or new salt inputs to the base synthesis.')
        if oid=='zeta-medium':extras.append('HCl or NaOH are alternative pH adjusters; no simultaneous addition or titration sequence is assumed.')
        if oid=='xrd-freeze-dry':extras.append('Polymer-only and polymer-CdS samples are separate preparations; no physical mixing or polymer-background subtraction is asserted.')
        op=operation(oid,norm(LABELS[oid]).replace('-','_'),LABELS[oid],evidence(proto['evidence']),inputs,[output],depends=[prev] if prev else [],stage=stage,branch=proto['id'],description=item['action']+' '+' '.join(extras),retained_fraction=item['retained_fraction'],environment=fact('Air',evidence(proto['evidence']),note='Only TEM grid drying explicitly occurs in air.') if oid=='tem-grid-dry' else fact(None,evidence(proto['evidence']),note='No atmosphere or pressure is assigned beyond the source statement.'))
        if oid in ['ama-block','cds-stir']:op['environment']['note']+=' Ambient temperature is qualitative, not a numerical temperature.'
        r['operations'].append(op);idx=len(r['operations'])-1
        bind_unit(r,proto['id'],f'/operations/{idx}');op_source_map.append({'source_protocol_id':proto['id'],'source_operation_id':oid,'record_id':r['record_id'],'pointer':f'/operations/{idx}','input_normalization':'Source stage/output state replaces previously present ingredients; removed impurity is not treated as an added input.'})
        if oid=='zeta-medium':
            op['optional_inputs']=[mat(r,'hcl','characterization'),mat(r,'naoh','characterization')]
        for ff in item['quantity_fact_ids']:
            short=ff.removeprefix(SID+'-')
            if short in ['fig1-ionic-strength-labels','fig4-protein-labels','tem-voltage']:continue
            if short=='hydrolysis-media':
                param(r,op,'acetic_acid_relative_volume_parts',short,0);param(r,op,'water_relative_volume_parts',short,1)
            else:param(r,op,PARAM_KEYS[short],short)
        if oid in ['cd-add','s-add']:
            op['parameters']['addition_volume']=qty(unit='mL',evidence=evidence(proto['evidence']),qualifier='Unreported; initial 8 mL polymer medium is not the added precursor volume.')
        if oid in ['ama-block','cds-stir','biotin-cds-coprecipitate']:
            op['parameters']['temperature']=qty(unit='degC',evidence=evidence(proto['evidence']),qualifier='No numerical value; ambient is qualitative for the representative preparation. No numerical condition is inherited for the biotin variant.')
        if oid=='biotin-cds-coprecipitate':
            for k,u in [('biotin_polymer_amine_concentration','mol/L of amine groups'),('initial_solution_volume','mL'),('CdCl2_added_volume','mL'),('Na2S_added_volume','mL')]:op['parameters'][k]=qty(unit=u,evidence=evidence(proto['evidence']),qualifier='Not independently supplied for the biotin variant.')
        prev=oid;last_by_proto[proto['id']]=oid;out_by_proto[proto['id']]=output
    bind_obj('protocols',proto['id'],r,'/operations')

# Source-described stocks are not invented complete stock solutions.
mat(poly,'pdp');mat(poly,'peg-prepolymer',role='removed_impurity');mat(poly,'acetal-peg-pama',role='product_identity')
poly['stocks'].append({'id':'pdp-thf-stock','name':'Reported PDP solution in THF','components':[{'material_id':'pdp','quantities':{'reported_amount':qvalue('pdp-amount')}},{'material_id':'thf','quantities':{'reported_medium_volume':qvalue('thf-volume')}}],'concentrations':{'PDP_concentration':qty(unit='mol/L',evidence=E('pdp-preparation'),qualifier='No concentration derived from the reported amount and medium volume.')},'preparation_operation_ids':['pdp-form'],'scope':'Same reported initiator preparation, not an independent stock recipe or verified quantitative yield.','evidence':E('pdp-preparation')})
bind_fact(poly,'pdp-amount','/stocks/0/components/0/quantities/reported_amount');bind_fact(poly,'thf-volume','/stocks/0/components/1/quantities/reported_medium_volume');bind_obj('stocks','pdp-thf-solution',poly,'/stocks/0')
route['stocks'].append({'id':'aqueous-polymer-stock','name':'Initial aqueous CHO-PEG/PAMA medium','components':[{'material_id':'cho-peg-pama','quantities':{}},{'material_id':'water','quantities':{}}],'concentrations':{'amine_group_concentration':qvalue('amine-mid')},'preparation_operation_ids':['polymer-medium'],'scope':'8 mL is the initial total polymer-solution volume in the operation. Concentration counts amine groups, not polymer chains; no exact medium preparation, storage or water-only volume is given.','evidence':E('cho-cds-representative')})
bind_fact(route,'amine-mid','/stocks/0/concentrations/amine_group_concentration');bind_obj('stocks','aqueous-polymer-medium',route,'/stocks/0')
for r,key in [(ald,'cho-peg-pama'),(bio,'biotin-peg-pama'),(route,'cds')]:mat(r,key,'workup',role='product_identity')

# Source samples keep their own scope. None is made a measured exact recipe join.
SMAP={'cho-cds-representative':route,'no-polymer-control':controls,'peg-control':controls,'pama-control':controls,'cho-cds-salt-challenge':salt,'cho-cds-low-amine':series,'cho-cds-mid-amine':series,'cho-cds-high-amine':series,'figure2-absorption-sample-unresolved':opt,'zeta-series':zeta,'biotin-cds-generic':variant,'figure4-fret-series':fret,'figure5-competition-series':competition,'figure5-bsa-series':competition,'figure6-response-series':fret,'si-tem-grid':tem,'si-xrd-cds':xrd,'si-xrd-polymer':xrd}
UID_BY_SAMPLE={'cho-cds-mid-amine':'figure2-series','figure2-absorption-sample-unresolved':'figure2-absorption-sample-unresolved','zeta-series':'zeta-assay','biotin-cds-generic':'biotin-cds','figure4-fret-series':'fret-assay','figure5-competition-series':'streptavidin-competition','figure5-bsa-series':'bsa-control','figure6-response-series':'fret-assay','si-tem-grid':'tem-preparation','si-xrd-cds':'xrd-preparation','si-xrd-polymer':'xrd-preparation','cho-cds-salt-challenge':'salt-challenge'}
for ss in D['samples']:
    r=SMAP[ss['id']];uid=UID_BY_SAMPLE.get(ss['id'],ss['id']);state_id=out_by_proto.get(ss['protocol_id'])
    if ss['id'] in ['cho-cds-mid-amine','figure6-response-series']:state_id=None
    if ss['id']=='si-xrd-cds':state_id='freeze-dried-xrd-specimens'
    if ss['id']=='si-xrd-polymer':state_id='freeze-dried-xrd-specimens'
    p=add_sample(r,ss['id'],ss['id'].replace('-',' '),'PEG/PAMA' if ss['id']=='si-xrd-polymer' else 'CdS',uid,state_id,link='explicit' if ss['id']=='cho-cds-representative' else 'unresolved' if ss['id'] in ['figure2-absorption-sample-unresolved','zeta-series','si-tem-grid','si-xrd-cds','si-xrd-polymer'] else 'general_context',notes=['State: '+ss['state'],'Source linkage: '+ss['link_status'],ss['measurement_scope'],'Unique experimental batch/replicate not verified; shared labels do not establish cross-technique aliquot identity.'])
    if ss['id'] in ['si-xrd-cds','si-xrd-polymer']:p['notes'].append('The shared sample-set state denotes separate supported specimens, not a physically mixed sample.')
    bind_obj('samples',ss['id'],r,f"/products/{r['products'].index(p)}")
for r,sid,formula,uid,st in [(poly,'purified-acetal-polymer','PEG/PAMA','purified-acetal-block-polymer','purified-acetal-block-polymer'),(ald,'dialyzed-aldehyde-polymer','CHO-PEG/PAMA','aldehyde-polymer','cho-peg-pama-in-water'),(bio,'biotin-polymer-preparation','biotin-PEG/PAMA','biotin-polymer','biotin-peg-pama-preparation')]:add_sample(r,sid,sid.replace('-',' '),formula,uid,st,'general_context')
for r,sid,uid in [(opt,'cho-cds-generic','cho-cds-generic'),(opt,'biotin-cds-optical-context','biotin-cds-generic'),(series,'figure2-series-context','figure2-series'),(salt,'figure1-label-context','salt-challenge'),(intuition,'interpretation-context','cho-cds-representative'),(refs,'source-context','abstract-biotin-cds')]:add_sample(r,sid,sid.replace('-',' '),None if r in [intuition,refs] else 'CdS',uid)
add_sample(variant,'abstract-size-context','Abstract biotin-CdS size summary','CdS','abstract-biotin-cds',notes=['Abstract-level approximate size statement; no verified biotin-specific TEM/XRD or unique measured size specimen.'])

def analysis_op(r,oid,label,inputs,ev,description,depends=None,parameters=None):
    out=oid+'-data';r['material_states'].append(state(out,label+' data',inputs,'analysis_data'))
    op=operation(oid,norm(label).replace('-','_'),label,ev,inputs,[out],depends=depends,stage='characterization',parameters=parameters,description=description)
    r['operations'].append(op);return op
# TEM voltage belongs to acquisition, not grid drying.
temop=analysis_op(tem,'tem-acquire','Acquire EF-TEM at 200 kV',['air-dried-tem-grid'],E('si-tem'),'LEO 922 OMEGA energy-filtered TEM; original two images and scale bars remain separate from acquisition settings.',depends=['tem-grid-dry'])
param(tem,temop,'accelerating_voltage','tem-voltage');bind_unit(tem,'si-tem',f"/operations/{tem['operations'].index(temop)}")
# Shared optical apparatus setting is scoped to a set of separate specimens.
specimen(opt,'uv-specimen','Figure 2d optical specimen; member identity unresolved',uid='uv-vis-measurement')
specimen(opt,'fluorescence-specimen-contexts','Separate source fluorescence specimen contexts; not a mixed sample',uid='fluorescence-measurement')
uvop=analysis_op(opt,'uv-vis','Measure UV–visible absorption',['uv-specimen'],E('uv-vis-measurement'),'Shimadzu UV-2400PC with quartz cell; Figure 2d exact concentration-series member is unresolved.')
param(opt,uvop,'cell_path_length','uv-cell');bind_unit(opt,'uv-vis-measurement',f"/operations/{opt['operations'].index(uvop)}")
plop=analysis_op(opt,'fluorescence','Measure steady-state fluorescence',['fluorescence-specimen-contexts'],E('fluorescence-measurement'),'Hitachi F-2500. The same stated settings do not establish the same physical specimen across the polymer comparison and recognition assay.')
param(opt,plop,'excitation_wavelength','pl-excitation');param(opt,plop,'excitation_bandwidth','pl-bandwidths',0);param(opt,plop,'emission_bandwidth','pl-bandwidths',1);bind_unit(opt,'fluorescence-measurement',f"/operations/{opt['operations'].index(plop)}")
specimen(poly,'purified-acetal-nmr-specimen','Purified acetal-ended block polymer for reported 1H NMR',None,'polymer-nmr')
nmrop=analysis_op(poly,'polymer-nmr','Assess end-acetal functionality by ¹H NMR',['purified-acetal-nmr-specimen'],E('polymer-nmr'),'Author reports almost quantitative functionality; no spectrum, instrument field, solvent, integrations or percentage is supplied.')
bind_unit(poly,'polymer-nmr',f"/operations/{poly['operations'].index(nmrop)}")

# Typed outcomes and source labels never become invented recipe targets.
MEASURE=[(poly,'purified-acetal-polymer','Polymer characterization',['peg-segment-mw','pama-segment-mw','polymer-dispersity','acetal-functionality']),
(opt,'figure2-absorption-sample-unresolved','UV–visible absorption; author Henglein band-gap estimate',['absorption-edge','optical-diameter']),
(opt,'cho-cds-generic','Author reported CHO-polymer CdS emission',['cho-pl-peak']),
(opt,'biotin-cds-optical-context','Separate author biotin-polymer CdS emission claim',['biotin-pl-peak']),
(zeta,'zeta-series','Region-level zeta-potential prose values',['zeta-acid','zeta-alkaline']),
(fret,'figure4-fret-series','Acceptor emission assignment in reported fluorescence spectra',['fret-acceptor-peak']),
(variant,'abstract-size-context','Abstract source description, not separate measured size',['abstract-size'])]
for r,sid,tech,ff in MEASURE:
    for f in ff:m_fact(r,f,sid,tech)
for i in range(3):m_fact(salt,'fig1-ionic-strength-labels','figure1-label-context','Printed ionic-strength labels; not numerical independent challenge recipes',i)
for i in range(11):m_fact(fret,'fig4-protein-labels','figure4-fret-series','Printed concentration legend; not curve-digitized data or independent replicates',i)
for i in range(2):m_fact(tem,'tem-scale-bars','si-tem-grid','Original TEM scale bars, not measured particle diameters',i)
# Midpoint concentration appears in Figure 2b without an asserted common preparation batch.
m_fact(series,'amine-mid','cho-cds-mid-amine','Figure 2b caption; no exact representative-batch join')
for ff in ['peg-control-mn','pama-control-mn']:
    sid='peg-control' if ff.startswith('peg-') else 'pama-control';m_fact(controls,ff,sid,'Reported homopolymer Mn, units not printed')
phase=next(x for x in D['author_interpretations_and_outlook'] if x['id']=='author-phase')
xp=next(p for p in xrd['products'] if p['sample_id']=='si-xrd-cds');xp['phase']=fact('hexagonal wurtzite',evidence(phase['evidence']),'author_derived',note=phase['limits']);bind_obj('author_interpretations_and_outlook','author-phase',xrd,f"/products/{xrd['products'].index(xp)}/phase")

# All descriptive source objects have explicit canonical destinations and retained scope.
for meas in D['measurements']:
    r={'uv-vis-measurement':opt,'fluorescence-measurement':opt,'zeta-measurement':zeta,'si-tem':tem,'si-xrd':xrd,'polymer-nmr':poly}[meas['id']]
    sid={'uv-vis-measurement':'figure2-absorption-sample-unresolved','fluorescence-measurement':'cho-cds-generic','zeta-measurement':'zeta-series','si-tem':'si-tem-grid','si-xrd':'si-xrd-cds','polymer-nmr':'purified-acetal-polymer'}[meas['id']]
    ptr=context(r,'acquisition-context-'+meas['id'],sid,meas['technique']+'. Instrument: '+(meas['instrument'] or 'not reported')+'. '+meas['data_status'],evidence(meas['evidence']),prop='acquisition_scope',note='Source specimen labels: '+', '.join(meas['sample_ids'])+'. Lists denote separate contexts, not pooled specimens.')
    bind_unit(r,meas['id'],ptr);bind_obj('measurements',meas['id'],r,ptr)
for j,obs in enumerate(D['observations']):
    for sid in obs['sample_ids']:
        r=SMAP[sid];ptr=context(r,f'outcome-{j}-{sid}',sid,obs['outcome'],evidence(obs['evidence']),prop='reported_observation',note=obs['status']+'; qualitative/source context only, no calibrated success label.')
        bind_obj('observations',str(j),r,ptr)
for it in D['author_interpretations_and_outlook']:
    ptr=context(intuition,it['id'],'interpretation-context',it['claim'],evidence(it['evidence']),prop='author_interpretation',status='author_derived',note=it['status']+'. '+it['limits']);bind_obj('author_interpretations_and_outlook',it['id'],intuition,ptr)
for it in D['unperformed_options']:
    ptr=context(intuition,it['id'],'interpretation-context',it['description'],evidence(it['evidence']),prop='discussed_unperformed_option',status='author_derived',note='Discussed, not performed; no recipe operation or numeric condition is created.');bind_obj('unperformed_options',it['id'],intuition,ptr)
FIGMAP={'main-figure1':(salt,'figure1-label-context'),'main-figure2':(series,'figure2-series-context'),'main-figure3':(zeta,'zeta-series'),'main-figure4':(fret,'figure4-fret-series'),'main-figure5':(competition,'figure5-competition-series'),'main-figure6':(fret,'figure6-response-series'),'si-figure1':(tem,'si-tem-grid'),'si-figure2':(xrd,'si-xrd-cds')}
for fig in D['figures']:
    r,sid=FIGMAP[fig['id']]
    axes='; '.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in fig['axes_and_labels'].items())
    ptr=context(r,'figure-context-'+fig['id'],sid,fig['label']+'. '+fig['content'],evidence(fig['evidence']),prop='original_figure_context',note='Axes and printed labels: '+axes+'. '+fig['disposition']+'. Source sample labels: '+', '.join(fig['sample_ids'])+'. Original asset: '+fig['asset_id']+'.')
    bind_obj('figures',fig['id'],r,ptr)
for ref in D['references']:
    text=ref.get('bibliography_as_printed_normalized_spacing') or ref.get('text') or json.dumps({k:v for k,v in ref.items() if k not in ['evidence']},ensure_ascii=False)
    ptr=context(refs,ref['id'],'source-context',text,evidence(ref['evidence']),prop='bibliographic_reference',note=ref.get('use_in_current_paper','')+'. '+ref.get('access_level','Citation/context only; external full text not inspected')+'. External references do not fill current missing fields.')
    bind_obj('references',ref['id'],refs,ptr)
for c in D['contradictions']:
    for r in [series,opt] if c['id']=='C1' else [competition] if c['id']=='C2' else [fret]:
        sid='figure2-series-context' if r is series else 'figure2-absorption-sample-unresolved' if r is opt else 'figure5-competition-series' if r is competition else 'figure6-response-series' if c['id']=='C3' else 'figure4-fret-series'
        ptr=context(r,'unresolved-'+c['id'],sid,conflicts[c['id']],evidence(c['evidence']),prop='unresolved_source_conflict');bind_obj('contradictions',c['id'],r,ptr)
for g in D['gaps']:
    ptr=context(refs,'gap-'+g['id'],'source-context',g['missing'],E('abstract-biotin-cds'),prop='source_missingness',note='Scope: '+g['scope']+'. '+g['impact']+' This gap is an audited full-source assessment across the supplied 5 main + 3 SI pages, not a claim that the abstract contains all details.');bind_obj('gaps',g['id'],refs,ptr)
for adm in I['administrative_and_footnote_units']:
    ptr=context(refs,'administrative-'+adm['id'],'source-context',adm['disposition'],evidence(adm['evidence']),prop=adm['kind'],status='author_derived' if adm['id']=='reference-note11' else 'reported');bind_obj('administrative_and_footnote_units',adm['id'],refs,ptr)
ptr=context(refs,'publication-metadata','source-context',D['title']+'. '+('; '.join(D['authors']))+'. '+D['bibliography']['journal']+' '+str(D['bibliography']['year'])+', '+str(D['bibliography']['volume'])+'('+str(D['bibliography']['issue'])+'), '+D['bibliography']['pages']+'. DOI '+D['doi'],evidence(I['administrative_and_footnote_units'][0]['evidence']),prop='bibliographic_identity',note='Received '+D['bibliography']['received']+'; final form '+D['bibliography']['final_form']+'; web publication '+D['bibliography']['published_web']+'.');bind_obj('bibliography','identity',refs,ptr)
ptr=context(refs,'source-structure-status','source-context','Author phase assignment: '+D['structure_status']['reported_phase']+'. '+D['structure_status']['basis'],E('si-xrd'),prop='structure_scope',note='No exact measured atomic coordinates, supplied CIF, imported external structure or verified recipe–structure specimen join.');bind_obj('structure_status','scope',refs,ptr)
ptr=context(route,'precursor-concentration-basis','cho-cds-representative','CdCl₂ and Na₂S are printed as 2.5×10⁻³ mol/L concentration statements, not verified complete stock formulations.',E('cho-cds-representative'),prop='stock_scope',note='Aqueous overall method; separate stock composition, addition volumes and final reaction volume unresolved. No added moles or yields are calculated.');bind_obj('stocks','cdcl2-na2s-concentration-statements',route,ptr)

# Map remaining reviewed scope units to the precise sample/context they qualify.
REST={'purified-acetal-block-polymer':(poly,'purified-acetal-polymer'),'figure2-series':(series,'figure2-series-context'),'cho-cds-salt-challenge':(salt,'cho-cds-salt-challenge'),'figure2-absorption-sample-unresolved':(opt,'figure2-absorption-sample-unresolved'),'cho-cds-generic':(opt,'cho-cds-generic'),'biotin-cds-generic':(variant,'biotin-cds-generic'),'figure4-fret-series':(fret,'figure4-fret-series'),'abstract-biotin-cds':(variant,'abstract-size-context')}
for uid,u in U.items():
    if not unit_links[uid]:
        r,sid=REST[uid];ptr=context(r,'scope-'+uid,sid,u['title']+'. '+u['disposition'],evidence(u['evidence']),prop='source_scope',note='Scope label only; numerical source facts remain individually mapped.');bind_unit(r,uid,ptr)
for ff,links in fact_links.items():assert links,('unmapped fact',ff)
for uid,links in unit_links.items():assert links,('unmapped unit',uid)

# All material identities are retained, including product, impurity and support contexts.
seen={b['source_object_id'] for b in object_links if b['category']=='materials'}
for key,m in M.items():
    if key in seen:continue
    r=PRO_MAP[m['scope_ids'][0]];mat(r,key,'characterization' if r in [tem,xrd,zeta,fret,competition,salt] else 'precursor_preparation',role='source_material_context')
for key,r in records.items():
    if r is not route:link(r,'cho-cds','Representative CdS preparation','Same source and nominal material family only; no inferred common physical batch, exact structural sample join or borrowed quantitative conditions.')
for key,label in [('polymer-preparation','PDP and acetal-polymer preparation'),('aldehyde-polymer','Aldehyde polymer preparation'),('biotin-polymer','Biotin polymer branch'),('biotin-cds','Biotin CdS variant'),('stabilizer-controls','Stabilizer controls'),('concentration-series','Concentration-series conflict'),('salt-challenge','Salt stability'),('optical','Optical data and derived size'),('zeta','Zeta potential'),('fret','Recognition assay'),('recognition-controls','Competition controls'),('tem','Original TEM context'),('xrd','Original XRD context'),('chemical-intuition','Author chemical interpretation'),('source-context','References and gaps')]:link(route,key,label,'Separate source-linked record; sample identity and review/task gates remain explicit.')
link(variant,'biotin-polymer','Biotin polymer preparation','Ligand installation occurs before CdS; no quantitative surface density or isolated lot identity is inferred.')
link(bio,'aldehyde-polymer','Pre-dialysis aldehyde branch point','The biotin branch begins before dialysis; it does not consume an assumed dialyzed aldehyde stock.')

def resolve(obj,pointer):
    for x in pointer.strip('/').split('/'):obj=obj[int(x)] if isinstance(obj,list) else obj[x]
    return obj
by_id={r['record_id']:r for r in records.values()};errors=[];checks=[]
def check(ok,label):checks.append({'check':label,'passed':bool(ok)});assert ok,label
for r in records.values():
    ee=validate_record(r);errors.extend(ee);check(not ee,r['record_id']+' schema and semantics')
    check(r['quality']['review_status']=='imported_unreviewed' and r['quality']['requested_tasks']==[] and 'collection' not in r,r['record_id']+' private imported status')
    check(not any(x['eligible'] for x in eligibility(r).values()) and not r['structure_assets'],r['record_id']+' no training or atomic assets')
    check(all(p['batch_id'] is None for p in r['products']),r['record_id']+' no invented physical batch IDs')
for ff,links in fact_links.items():
    for b in links:check(resolve(by_id[b['record_id']],b['pointer'])==qvalue(ff,b['source_array_index']),ff+' source-to-field value equality')
for uid,links in unit_links.items():
    for b in links:resolve(by_id[b['record_id']],b['pointer']);check(True,uid+' source-unit pointer resolves')
for b in object_links:resolve(by_id[b['record_id']],b['pointer'])
for category in ['materials','stocks','protocols','samples','measurements','author_interpretations_and_outlook','figures','references','contradictions','gaps','unperformed_options']:
    expected={x['id'] for x in D[category]}
    actual={x['source_object_id'] for x in object_links if x['category']==category}
    check(expected==actual,category+' every original source object has a canonical binding')
check({str(i) for i in range(len(D['observations']))}=={x['source_object_id'] for x in object_links if x['category']=='observations'},'Every source observation has a canonical binding')
check({a['id'] for a in I['administrative_and_footnote_units']}=={x['source_object_id'] for x in object_links if x['category']=='administrative_and_footnote_units'},'Every administrative and substantive footnote unit has a canonical binding')
check(len(set(build_groups(list(records.values())).values()))==1,'All records share one source split group')
check(len(route['operations'])==5 and len(variant['operations'])==1,'One representative recipe and one incomplete similar-manner variant')
check(len(fret['products'])==2,'Eleven protein legend labels do not create eleven experimental samples')
check(all(p['phase']['value'] is None for r in records.values() if r is not xrd for p in r['products']),'XRD phase is not silently inherited by recipe or biotin specimens')
check(not any('measured'==m['value']['status'] for r in records.values() for m in r['measurements']),'No invented measured status')
check(next(m for m in opt['measurements'] if m['property']=='band_gap_theory_derived_cds_size')['value']['status']=='author_derived','4.8 nm remains author-derived')
check('protonating-agent-unspecified' in next(o for o in poly['operations'] if o['id']=='pama-protonate')['inputs'],'No HCl borrowed from zeta assay for polymer protonation')
check(next(o for o in poly['operations'] if o['id']=='soxhlet-clean')['inputs']==['protonated-acetal-block-polymer','thf'],'Removed PEG impurity is not treated as a new input')
check('cds' not in next(o for o in route['operations'] if o['id']=='cds-stir')['inputs'],'Already formed CdS is represented by preceding state, not new reagent')
check(next(o for o in tem['operations'] if o['id']=='tem-grid-dry')['parameters']=={},'TEM voltage is attached to acquisition only')
check(not errors,'No schema errors')
out=B/'canonical-drafts';out.mkdir(exist_ok=True)
for r in records.values():save(out/(r['record_id']+'.json'),r)
counts={'records':len(records),'record_types':dict(Counter(r['record_type'] for r in records.values())),'representative_cds_routes':1,'incompletely_quantified_biotin_protocol_variants':1,'operations':sum(len(r['operations']) for r in records.values()),'measurements':sum(len(r['measurements']) for r in records.values()),'material_slots':sum(len(r['materials']) for r in records.values()),'stocks':sum(len(r['stocks']) for r in records.values()),'samples_and_contexts':sum(len(r['products']) for r in records.values()),'source_facts':len(F),'source_fact_bindings':sum(map(len,fact_links.values())),'source_units':len(U),'source_unit_bindings':sum(map(len,unit_links.values())),'source_objects_bound':len(object_links)}
counts['representative_route_complete_SOP']=False
pending=['Independent canonical scientific audit against this exact source/record set.','Reader/figure and original-asset integration, molecules/apparatus and final browser visual review.','Source C1–C4 conflicts and all G1–G10 gaps remain unresolved.','No complete-SOP, exact-structure, optical benchmark, calibrated success or public-release approval.']
manifest={'schema':'mattersyn-canonical-draft-manifest/1','source_id':SID,'status':'private_draft_schema_valid_pending_canonical_scientific_audit','created_at':datetime.now(timezone.utc).isoformat(),'counts':counts,'source_extraction_audit_sha256':sha(B/'source-scientific-audit.json'),'source_inventory_sha256':sha(B/'source-inventory.json'),'source_facts_sha256':sha(B/'source-facts.json'),'page_coverage_sha256':sha(B/'page-coverage.json'),'original_sources':[{'path':d['path'],'sha256':sha(d['path'])} for d in A['original_copies_independently_verified']],'build_script_sha256':sha(__file__),'dataset_validator_sha256':sha(S/'scripts/dataset_lib.py'),'schema_definition_sha256':sha(S/'scripts/schema_definition.py'),'record_helpers_sha256':sha(S/'scripts/record_helpers.py'),'split_groups':build_groups(list(records.values())),'records':[{'record_id':r['record_id'],'record_type':r['record_type'],'path':str(out/(r['record_id']+'.json')),'sha256':sha(out/(r['record_id']+'.json')),'operations':[o['id'] for o in r['operations']],'samples':[p['sample_id'] for p in r['products']],'training_tasks':eligibility(r)} for r in records.values()],'pending_links_and_gates':pending,'published':False,'training_eligible':False}
save(B/'canonical-record-manifest.json',manifest)
coverage={'schema':'mattersyn-canonical-source-coverage/1','source_id':SID,'status':'complete_author_mapping_not_independent_audit','source_facts_sha256':sha(B/'source-facts.json'),'source_inventory_sha256':sha(B/'source-inventory.json'),'facts':[{'source_fact_id':ff,'source_fact':F[ff],'canonical_bindings':links} for ff,links in fact_links.items()],'source_units':[{'source_unit_id':uid,'source_unit':U[uid],'canonical_bindings':links} for uid,links in unit_links.items()],'source_objects':object_links,'source_operations':op_source_map,'status_normalizations':{'author_model_derived':'author_derived; original status and qualifier preserved','reported_qualitative':'reported fact with original raw text, not a fabricated numerical percentage'},'list_normalizations':'Reported pH and 2theta intervals become bounds; other ordered arrays become individually indexed values within a common source scope, never invented experimental samples. Original arrays are preserved above. Empty units preserve not-explicitly-stated molecular-weight/label units.','input_normalizations':'Inputs use preceding reaction states instead of re-adding products/intermediates; removed PEG is a discarded fraction. Assay inputs are preformed specimens. Separate comparison specimens are not pooled. TEM voltage is moved from combined source preparation/acquisition scope to the actual acquisition operation.'}
save(B/'canonical-source-coverage.json',coverage)
save(B/'canonical-draft-validation.json',{'schema':'mattersyn-private-draft-validation/1','status':'passed','created_at':datetime.now(timezone.utc).isoformat(),'scope':'Current Site Draft 2020-12 schema/semantic validator read only; complete source fact/unit pointers and record boundary checks. Author validation, not independent canonical audit.','author_source_rechecks':{'all_49_typed_facts_read':True,'all_32_source_units_read':True,'source_protocols_materials_samples_measurements_observations_interpretations_figures_conflicts_and_gaps_read':True,'visually_reopened_source_pages':['main-02.png','si-01.png'],'prior_full_source_audit':'The existing passed complete 5-main/3-SI audit remains the full-source checkpoint; this canonical task did not repeat all eight source pages.','sources_hash_reverified':4},'counts':counts,'checks':checks,'schema_errors':errors,'record_hashes':{r['record_id']:sha(out/(r['record_id']+'.json')) for r in records.values()},'canonical_manifest_sha256':sha(B/'canonical-record-manifest.json'),'coverage_sha256':sha(B/'canonical-source-coverage.json'),'published':False,'training_eligible':False,'pending_links_and_gates':pending})
print(json.dumps(counts,ensure_ascii=False))
