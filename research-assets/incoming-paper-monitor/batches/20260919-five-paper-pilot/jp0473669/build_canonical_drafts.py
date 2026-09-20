"""Private Ribeiro 2004 drafts from the independently audited source package.

Writes only this batch directory. The Site schema and helpers are read-only.
This author validation is not an independent canonical scientific audit.
"""
from pathlib import Path
from copy import deepcopy
from collections import Counter
from datetime import datetime, timezone
import sys, json, hashlib, re
sys.dont_write_bytecode = True
B = Path(__file__).resolve().parent
S = Path(r'[local path redacted]')
sys.path.insert(0, str(S/'scripts'))
from record_helpers import record, source, fact, qty, material, operation, state, product, measurement
from dataset_lib import validate_record, eligibility

SID='ribeiro2004'; PRE='ribeiro-2004-'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d): Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
I=read(B/'source-inventory.json'); FF=read(B/'source-facts.json'); A=read(B/'source-scientific-audit.json')
assert A['status']=='passed' and not A['open_findings']
for p,h in A['author_file_hashes'].items(): assert sha(B/p)==h, 'Audited extraction changed: '+p
DOCUMENTS=read(B/'screening.json')['documents']
for d in DOCUMENTS:
    assert d['sha256']==A['source_hashes'][d['location']] and sha(d['path'])==d['sha256'], 'Source PDF changed: '+d['path']
for asset in I['assets']:
    assert asset['sha256']==A['asset_hashes'][asset['id']] and sha(B/asset['filename'])==asset['sha256'], 'Original crop changed: '+asset['id']
F={f['id'].removeprefix(SID+'-fact-'):f for f in FF['facts']}
assert len(F)==63 and sum(len(p['steps']) for p in I['protocols'])==9
fact_links={k:[] for k in F}; records={}; unit_links={}; U={}

def ev(items):
    return [{'source_id':SID,'locator':f"Main PDF p. {e['pdf_page']} (printed p. {e.get('printed_page',15611+e['pdf_page'])}), {e.get('section','source context')}"} for e in items]
def E(page,section): return ev([{'pdf_page':page,'section':section}])
def fe(k): return ev(F[k]['evidence'])
def status(f):
    return {'reported_qualitative':'reported','author_model':'author_derived',
            'author_interpretation':'author_derived','cited_reference':'reported',
            'cited_prior_work':'reported'}.get(f['status'],f['status'])
RANGES={'concentration-range','ph-range','pl-range','uv-range','prior-range'}
BOUNDS={'stability':('maximum','months',False),'monitor-low':('maximum','h',False),
        'tem-n':('minimum','particles',False),'number-linear-scope':('maximum','mol/L',True)}
def fq(k,index=None):
    f=F[k]; v=f['value']; e=fe(k)
    provenance=f"Source status: {f['status']}. Source scope: {f['sample_scope']}."
    if f['status'].startswith('cited_'): provenance+=' Cited reference context only; the external full text has not been inspected.'
    if f['status'] in ('author_model','author_interpretation','author_derived'):
        provenance+=' Author model, interpretation or derived estimate; not a direct experimental measurement.'
    if isinstance(v,str): return fact(v,e,status(f),note=provenance+' '+f['qualifier'])
    args=dict(evidence=e,status=status(f),approximate=f['approximate'],qualifier=f['qualifier'],basis=provenance,
              raw_text=json.dumps(v,ensure_ascii=False))
    if k=='water-ratio':
        return qty(500,'water:Sn2+ relative ratio',**{**args,'raw_text':'approximately 500:1',
            'basis':provenance+' One relative Sn2+ part; molar, mass and volume bases are all unreported.'})
    if k in RANGES:
        return qty(unit=f['unit'] or ('pH' if k=='ph-range' else ''),minimum=v[0],maximum=v[1],**args)
    if k in BOUNDS:
        bound,unit,exclusive=BOUNDS[k]
        return qty(unit=unit,**{bound:v,bound+'_exclusive':exclusive},**args)
    if isinstance(v,list):
        assert index is not None, 'Ordered cohorts require individual sample mapping: '+k
        return qty(v[index],f['unit'] or 'pH',**{**args,'basis':provenance+f' Ordered source array entry {index}; raw array retained in coverage.'})
    return qty(v,f['unit'] or ('pH' if k=='final-ph' else ''),**args)
def bind(r,k,pointer,index=None):
    fact_links[k].append({'record_id':r['record_id'],'pointer':pointer,'source_array_index':index})
def add_unit(uid,kind,pointer,payload,evidence,claim=None):
    assert uid not in U
    U[uid]={'id':uid,'kind':kind,'source_inventory_pointer':pointer,'source_payload':deepcopy(payload),
            'evidence':evidence,'claim':claim or json.dumps(payload,ensure_ascii=False,separators=(', ',': '))}
    unit_links[uid]=[]
def ub(r,uid,pointer): unit_links[uid].append({'record_id':r['record_id'],'pointer':pointer})

# The frozen inventory has no units[] field. This separate index provides exact
# JSON-pointer coverage without changing that inventory or claiming new extraction.
metadata_keys=['source_id','doi','title','authors','journal','year','volume','issue','pages',
               'online_publication_date','received','final_form','source_sha256','source_scope']
add_unit('identity','metadata','/',{k:I[k] for k in metadata_keys},E(1,'Title, author block and article metadata'))
for k,kind in [('materials','material'),('protocols','protocol'),('figures','figure'),('equations','equation'),
               ('references','reference'),('assets','asset'),('remaining_gaps','missingness'),
               ('evidence_conflicts','conflict'),('source_pages','coverage')]:
    for n,x in enumerate(I[k]):
        token=x.get('id',x.get('asset_id',str(x.get('number',n+1)))) if isinstance(x,dict) else str(n+1)
        uid=k+'-'+str(token).removeprefix(SID+'-')
        e=ev(x['evidence']) if isinstance(x,dict) and x.get('evidence') else E(x.get('pdf_page',1) if isinstance(x,dict) else 1,
            'Source inventory: '+k+' '+str(n+1))
        # Protocol steps are independently mapped, while this entry preserves the group metadata.
        payload={a:b for a,b in x.items() if a!='steps'} if k=='protocols' else x
        add_unit(uid,kind,f'/{k}/{n}',payload,e)
        if k=='protocols':
            for j,st in enumerate(x['steps']):
                add_unit('step-'+x['id'].removeprefix(SID+'-')+'-'+st['id'],'operation',
                    f'/protocols/{n}/steps/{j}',st,ev(st['evidence']),st['description'])
for k in ['tables','schemes','acknowledgment']:
    add_unit(k,'source_context','/'+k,I[k],E(6 if k=='acknowledgment' else 1,'Source inventory '+k))

SRC=source(SID,I['doi'],I['title'],
    'Caue Ribeiro; Eduardo J. H. Lee; Tania R. Giraldi; Elson Longo; Jose A. Varela; Edson R. Leite',2004,
    si='No matched supporting information located or verified. SI existence remains unverified; no absence inferred.')
SRC['main_status']='All six supplied main pages were read and visually inspected in the passed source-extraction audit. Canonical scientific audit remains pending. Main SHA256: '+I['source_sha256']
SRC['reuse_status']='Private bibliographic/factual extraction. Original article and figure rights remain separate; no public-use license inferred.'
MISSING=deepcopy(I['remaining_gaps'])
CONFLICTS=[x['description'] for x in I['evidence_conflicts']]
def base(key,title,kind='observation',method='Source-scoped observation or model'):
    r=record(PRE+key,'Ribeiro et al. (2004) · '+title,'SnO2','Cassiterite tin dioxide colloids',method,
             deepcopy(SRC),'All six supplied main pages; SI unverified',kind)
    r['schema_version']='1.3.0'
    r['material'].update(elements=['Sn','O'],components=['SnO2'],architecture='single_material')
    r['lineage'].update(source_group=SID,recipe_family='ribeiro2004-controlled-hydrolysis')
    r['quality'].update(review_status='imported_unreviewed',requested_tasks=[],
        review_scope='Private canonical draft from the independently audited main-source extraction. A separate canonical scientific audit, presentation audit and publication gate remain pending.',
        missing_fields=deepcopy(MISSING),conflicts=deepcopy(CONFLICTS),
        experimental_outcome='reported_product' if kind=='literature_protocol' else 'not_established')
    if kind!='literature_protocol':
        r['intended_target']['composition']=fact(None,E(1,'Study scope'),note='Procedure or source context, not an independently instantiated target-synthesis batch.')
    records[key]=r; return r
def sample(r,sid,label,e,formula='SnO2',state_id=None,parent=None,explicit=False,notes=None):
    p=product(sid,formula,e,link='explicit' if explicit else 'general_context',state=state_id,
        notes=(notes or [])+['No author-assigned physical batch identifier is supplied. Matching concentration labels do not establish identical aliquots across figures.'])
    p['source_sample_label']=label;p['parent_sample_id']=parent;r['products'].append(p);return p
def link(r,key,label,relation):
    r['context_links'].append({'label':label,'url':'../records/'+PRE+key+'.html','relation':relation})
MS={m['id']:m for m in I['materials']}
ROLE={'sncl2-dihydrate':'metal_precursor','ethanol':'solvent','hydrolysis-water':'hydrolysis_reagent',
      'dialysis-water':'dialysis_medium','nitric-acid':'ph_adjustment_reagent','tbaoh-aqueous':'redispersion_reagent',
      'carbon-copper-grid':'substrate','sno2-colloid':'specimen','sn-hydroxide-model':'proposed_intermediate'}
def mat(r,k,stage='synthesis',name=None,role=None):
    d=MS[k];e=ev(d['evidence']);m=material(k,name or d['name'],
        None if k in ('tbaoh-aqueous','carbon-copper-grid') else d['formula'],role or ROLE[k],stage,e,
        notes=[str(d.get('amount_status',''))]+(['Supplier: '+d['supplier']] if d.get('supplier') else []))
    if k=='tbaoh-aqueous':
        m['notes']+=['Aqueous reagent, not a single molecular formula. Source identity: '+d['formula']]
        m['quantities']['stock_concentration']=fq('tbaoh-stock')
    elif k=='carbon-copper-grid':m['notes'].append('Support is carbon coating on copper, not a stoichiometric compound or product component.')
    elif k=='sn-hydroxide-model':m['notes'].append('Author-proposed solution intermediate; not an isolated reagent, demonstrated stock or measured speciation.')
    n=len(r['materials']);r['materials'].append(m);ub(r,'materials-'+k,f'/materials/{n}')
    if k=='tbaoh-aqueous':bind(r,'tbaoh-stock',f'/materials/{n}/quantities/stock_concentration')
    return m
def specimen(r,k,label,e):
    r['materials'].append(material(k,label,'SnO2','specimen','characterization',e,
        notes=['Source-labelled specimen or specimen set. Independent batch identity is not supplied.']))
def meas(r,k,sid,tech,index=None,property_name=None):
    f=F[k];n=len(r['measurements']);q=fq(k,index)
    mid=k+'-'+sid+(('-'+str(index)) if index is not None else '')
    r['measurements'].append(measurement(mid,sid,property_name or k.replace('-','_'),q,tech,fe(k),conditions=f['sample_scope']))
    bind(r,k,f'/measurements/{n}/value',index);return n
def context(r,uid,sid,st='reported'):
    u=U[uid];n=len(r['measurements']);note='Retained source-inventory '+u['kind']+'; pointer '+u['source_inventory_pointer']+'.'
    if u['kind']=='reference':note+=' Citation only; external full text not inspected.'
    if u['kind']=='asset':note+=' Original crop is private and not yet integrated into a reader. The asset is not atomic coordinates.'
    r['measurements'].append(measurement('source-'+uid,sid,'source_'+u['kind'],fact(u['claim'],u['evidence'],st,note=note),
        'Source text / original figure / inventory context',u['evidence']))
    ub(r,uid,f'/measurements/{n}/value');return n
def source_op(r,protocol,step,label,inputs,out,stage='synthesis',parameters=None,kind='mixture',parents=None):
    d=next(p for p in I['protocols'] if p['id']==SID+'-'+protocol)
    st=next(s for s in d['steps'] if s['id']==step);uid='step-'+protocol+'-'+step
    # Supports a family/set of source states, not fabricated independently quantified runs.
    r['material_states'].append(state(out,label+' — resulting source state',parents if parents is not None else inputs,kind))
    n=len(r['operations']);prior=[r['operations'][-1]['id']] if r['operations'] else []
    r['operations'].append(operation(protocol+'-'+step,st['operation'].replace(' ','_'),label,ev(st['evidence']),
        inputs,[out],depends=prior,parameters=parameters or {},stage=stage,description=st['description']))
    ub(r,uid,f'/operations/{n}');return n
def param(r,n,key,fid):
    r['operations'][n]['parameters'][key]=fq(fid);bind(r,fid,f'/operations/{n}/parameters/{key}')
def analysis(r,oid,label,inputs,e,parameters=None):
    out=oid+'-data';r['material_states'].append(state(out,label+' data',inputs,'analysis_data'))
    r['operations'].append(operation(oid,oid,label,e,inputs,[out],stage='characterization',parameters=parameters or {},
        depends=[r['operations'][-1]['id']] if r['operations'] else [],
        description='Acquisition explicitly described in the source. Inputs identify an analytical specimen set, not mixing of all measurement samples. Unreported parameters remain unknown.'))
    return len(r['operations'])-1

route=base('hydrolysis','Controlled-hydrolysis concentration-series framework','literature_protocol','Controlled hydrolysis and dialysis')
for k in ['sncl2-dihydrate','ethanol','hydrolysis-water']:mat(route,k)
mat(route,'dialysis-water','workup')
route['materials'][0]['quantities']['absolute_mass']=qty(unit='g',evidence=fe('sn-precursor'),qualifier='No absolute precursor charge is reported.')
route['materials'][1]['quantities']['volume']=qty(unit='mL',evidence=fe('solvent'),qualifier='Absolute ethanol volume is not reported.')
n=source_op(route,'hydrolysis','dissolve','Prepare the ethanolic tin(II) precursor series',['sncl2-dihydrate','ethanol'],'ethanolic-precursor-series',kind='sample_set')
param(route,n,'initial_tin_concentration','concentration-range')
route['stocks'].append({'id':'ethanolic-stock-series','name':'Initial ethanolic Sn(II) concentration series',
    'components':[{'material_id':k,'quantities':{}} for k in ['sncl2-dihydrate','ethanol']],
    'concentrations':{'initial_tin_concentration':fq('concentration-range')},
    'preparation_operation_ids':['hydrolysis-dissolve'],
    'scope':'Reported 0.0025–0.1 mol/L range of initial ethanolic precursor concentrations; not one stock, an enumerated batch list, or final aqueous SnO2 concentration.',
    'evidence':fe('concentration-range')})
bind(route,'concentration-range','/stocks/0/concentrations/initial_tin_concentration')
n=source_op(route,'hydrolysis','hydrolyze','Hydrolyze the precursor at room temperature',
    ['ethanolic-stock-series','hydrolysis-water'],'turbid-hydrolysis-series',kind='sample_set',parameters={
        'temperature':qty(unit='°C',evidence=fe('temperature'),qualifier='Room temperature; no numerical value.'),
        'duration':qty(unit='min',evidence=fe('temperature'),qualifier='Hydrolysis duration is unreported; the separate 2 h monitoring window is not a hold time.')})
param(route,n,'water_to_tin_relative_ratio','water-ratio')
route['operations'][n]['environment']=fq('temperature');bind(route,'temperature',f'/operations/{n}/environment')
route['operations'][n]['endpoint']=fq('white-product');bind(route,'white-product',f'/operations/{n}/endpoint')
n=source_op(route,'hydrolysis','dialyze','Dialyze against deionized water and retain the colloid',
    ['turbid-hydrolysis-series','dialysis-water'],'dialyzed-colloid-series',stage='workup',kind='sample_set',parameters={
        'duration':qty(unit='h',evidence=fe('dialysis-water'),qualifier='Duration, membrane and water-exchange schedule are unreported.')})
route['operations'][n]['endpoint']=fq('final-dispersion');bind(route,'final-dispersion',f'/operations/{n}/endpoint')
route['operations'][n]['retained_fraction']='dialyzed-colloid-series'
sample(route,'final-series','As-prepared colloidal product series',fe('final-dispersion'),state_id='dialyzed-colloid-series',explicit=True,
    notes=['One literature framework representing a concentration series; no exact number of independent syntheses is inferred.'])
for k in ['sn-precursor','solvent','dialysis-water','final-ph','stability','phase']:
    meas(route,k,'final-series','Source synthesis / general product description')
route['products'][0]['phase']=fq('phase');bind(route,'phase','/products/0/phase')
context(route,'protocols-hydrolysis','final-series')

ph=base('ph-treatment','Acid-set aging and optical redispersion','procedure','pH modification, aging and probe sonication')
mat(ph,'sno2-colloid','characterization');mat(ph,'nitric-acid','characterization');mat(ph,'tbaoh-aqueous','characterization')
n=source_op(ph,'ph-treatment','acidify','Set the treatment pH of 0.025 M-origin colloids',
    ['sno2-colloid','nitric-acid'],'acid-set-series','characterization',kind='sample_set')
param(ph,n,'treatment_pH_range','ph-range')
n=source_op(ph,'ph-treatment','age','Age the acid-set samples for 24 hours',['acid-set-series'],'aged-treatment-series','characterization',kind='sample_set')
param(ph,n,'duration','age-before-redispersion')
n=source_op(ph,'ph-treatment','redisperse','Add aqueous TBAOH for spectroscopic redispersion',
    ['aged-treatment-series','tbaoh-aqueous'],'redispersed-series','characterization',kind='sample_set',parameters={
        'addition_volume':qty(unit='mL',evidence=fe('tbaoh-stock'),qualifier='TBAOH stock addition volume is unreported.'),
        'measurement_pH_after_base':qty(unit='pH',evidence=fe('tbaoh-stock'),qualifier='Final pH after basic TBAOH addition is unreported; acid-set treatment labels cannot replace it.')})
n=source_op(ph,'ph-treatment','sonicate','Probe-sonicate the redispersed optical samples',
    ['redispersed-series'],'sonicated-optical-series','characterization',kind='sample_set')
param(ph,n,'duration','sonicate')
for sid,label,st in [('treatment-series','Acid-set treatment states before base addition','aged-treatment-series'),
                     ('optical-series','After TBAOH and probe sonication; final pH unknown','sonicated-optical-series')]:
    sample(ph,sid,label,fe('ph-range'),state_id=st,parent='treatment-series' if sid=='optical-series' else None)
for k in ['parent-ph-series','acid','tbaoh']:meas(ph,k,'treatment-series' if k!='tbaoh' else 'optical-series','Source pH-treatment procedure')
context(ph,'protocols-ph-treatment','treatment-series')
link(ph,'hydrolysis','Parent synthesis framework','Parent concentration is explicitly 0.025 mol/L in ethanol; final colloidal concentration and physical batch identity are unreported.')

tem=base('microscopy','TEM grid preparation and acquisition','procedure','Transmission and high-resolution electron microscopy')
mat(tem,'carbon-copper-grid','characterization');mat(tem,'sno2-colloid','characterization')
n=source_op(tem,'tem-preparation','wet-grid','Wet a carbon-coated copper grid with one colloid drop',
    ['sno2-colloid','carbon-copper-grid'],'wet-grid','characterization',kind='sample_set',parents=['sno2-colloid'])
param(tem,n,'wetting_duration','grid-wet-duration')
n=source_op(tem,'tem-preparation','air-dry','Dry the TEM specimen in air',['wet-grid'],'dry-grid-specimens','characterization',kind='sample_set')
tem['operations'][n]['environment']=fq('grid-dry');bind(tem,'grid-dry',f'/operations/{n}/environment')
n=analysis(tem,'tem-acquisition','Acquire TEM images and measure particle radii',['dry-grid-specimens'],fe('tem-instrument'))
param(tem,n,'accelerating_voltage','tem-voltage');param(tem,n,'particle_count_lower_bound','tem-n')
sample(tem,'acquisition-context','Common TEM method; each distribution contains at least 200 particle measurements',fe('tem-instrument'),state_id='dry-grid-specimens')
for k in ['tem-instrument','grid','grid-drop']:meas(tem,k,'acquisition-context','TEM preparation/acquisition')
context(tem,'protocols-tem-preparation','acquisition-context')

uv=base('uv-visible','Optical absorption acquisition and concentration trend','procedure','UV–visible absorption')
pl=base('photoluminescence','Photoluminescence acquisition and concentration trend','procedure','Photoluminescence spectroscopy')
for r,k in [(uv,'uv'),(pl,'pl')]:
    mat(r,'sno2-colloid','characterization')
    sample(r,'concentration-series','Figure 1 concentration-series optical specimens',fe('optical-trend'),
        notes=['The full curve-to-concentration key is absent. No exact peak coordinates or specimen identities are reconstructed.'])
    n=analysis(r,k+'-acquisition','Acquire '+('UV–visible absorption' if k=='uv' else 'photoluminescence')+' spectra',
        ['sno2-colloid'],fe(k+'-instrument'))
    param(r,n,'wavelength_interval' if k=='uv' else 'emission_interval',k+'-range')
    if k=='pl':param(r,n,'excitation_wavelength','pl-excitation')
    r['operations'][n]['environment']=fq('optical-state');bind(r,'optical-state',f'/operations/{n}/environment')
    meas(r,k+'-instrument','concentration-series','Optical acquisition')
    meas(r,'optical-trend','concentration-series','Reported concentration-series spectral trend')
    context(r,'figures-figure-1','concentration-series')
sample(uv,'low-concentration-monitor','0.0025 M-origin optical monitoring, no new independent batch',fe('monitor-low'))
meas(uv,'monitor-low','low-concentration-monitor','Time-window observation by optical absorption')
sample(pl,'ph-optical-series','Figure 6b post-redispersion optical specimens; labelled by acid-set pH',fe('ph-growth'))
link(pl,'ph-treatment','Preparation of pH-series optical specimens','TBAOH/probe treatment is explicitly for spectroscopy. Final measurement pH remains unreported.')

zeta=base('zeta-potential','pH-dependent zeta potential','procedure','Electrokinetic zeta-potential measurement')
mat(zeta,'sno2-colloid','characterization')
sample(zeta,'zeta-series','Figure 6a / 0.025 M-origin pH series',fe('isoelectric'),
    notes=['The spectroscopic TBAOH/probe treatment is not automatically inherited by the zeta-potential acquisition.'])
analysis(zeta,'zeta-acquisition','Measure zeta potential versus pH',['sno2-colloid'],fe('zeta-instrument'))
meas(zeta,'zeta-instrument','zeta-series','Zeta-potential acquisition');meas(zeta,'isoelectric','zeta-series','Zeta potential versus pH')

cs=base('concentration-structure','Concentration-dependent HRTEM and TEM radius distributions',method='Original HRTEM and TEM distribution evidence')
for sid,label in [('hrtem-a','Figure 4a: 0.1 mol/L initial Sn(II)'),('hrtem-b','Figure 4b: 0.0025 mol/L initial Sn(II)'),
    ('hrtem-comparison','Figure 4 comparative defect interpretation'),('hist-0025','Figure 5: 0.0025 mol/L'),
    ('hist-005','Figure 5: 0.005 mol/L'),('hist-025','Figure 5: 0.025 mol/L'),('hist-comparison','Figure 5 radius-distribution comparison')]:
    sample(cs,sid,label,E(4,'Figures 4–5'),notes=['Concentration is initial ethanolic precursor concentration, not final colloid concentration.'])
for i,sid in enumerate(['hrtem-a','hrtem-b']):
    meas(cs,'hrtem-concentrations',sid,'Figure 4 caption',i,property_name='initial_precursor_concentration')
    meas(cs,'hrtem-scale',sid,'Original HRTEM image scale bar',property_name='image_scale_bar')
meas(cs,'hrtem-defects','hrtem-comparison','Source HRTEM interpretation')
for i,sid in enumerate(['hist-0025','hist-005','hist-025']):meas(cs,'tem-histogram-cohorts',sid,'Figure 5 labels',i,property_name='initial_precursor_concentration')
meas(cs,'tem-histogram-trend','hist-comparison','TEM radius histograms')
context(cs,'figures-figure-4','hrtem-comparison');context(cs,'figures-figure-5','hist-comparison')
link(cs,'microscopy','Shared TEM acquisition method','Same method scope; individual image/histogram aliquot joins are not supplied.')

pc=base('ph-comparison','Treatment-pH-dependent coarsening and HRTEM',method='PL-derived radius and HRTEM comparison')
for sid,label,page in [('pl-radius-series','Figure 6b: optical-derived radius versus acid-set treatment pH',5),
    ('hrtem-ph6','Figure 7a: treatment pH 6.0',5),('hrtem-ph27','Figure 7b: treatment pH 2.7',5),
    ('hrtem-comparison','Figure 7 morphological comparison',5)]:
    sample(pc,sid,label,E(page,'Figures 6–7'),notes=['Source cohort originates from 0.025 mol/L ethanolic Sn(II). Treatment labels are not verified post-TBAOH measurement pH.'])
meas(pc,'ph-growth','pl-radius-series','Author PL-derived radius trend')
for i,sid in enumerate(['hrtem-ph6','hrtem-ph27']):
    meas(pc,'ph-hrtem',sid,'Figure 7 caption',i,property_name='acid_set_treatment_pH')
    meas(pc,'ph-hrtem-scale',sid,'Original HRTEM image scale bar',property_name='image_scale_bar')
meas(pc,'ph-hrtem-observation','hrtem-comparison','HRTEM morphological comparison')
context(pc,'figures-figure-6','pl-radius-series');context(zeta,'figures-figure-6','zeta-series')
context(pc,'figures-figure-7','hrtem-comparison')
link(pc,'ph-treatment','Acid-set treatment and optical redispersion','Only optical specimens explicitly receive the complete TBAOH/probe sequence. TEM specimen preparation is independently described.')

om=base('optical-size-model','Optical effective-mass radius estimates',method='Author effective-mass model and cited constants')
for sid,label in [('reference','Bulk/reference constants'),('radius-analysis','Equation 1 and comparison of optical radius estimates'),
    ('abs-radius','Figure 2a absorption-onset-derived radii'),('pl-radius','Figure 2b PL-peak-derived radii')]:
    sample(om,sid,label,E(2,'Equation 1; continued discussion p. 3'),formula=None,
        notes=['Analytical/reference context, not an independently prepared specimen, directly measured TEM radius, or exact crystal structure.'])
for k,sid in [('bulk-gap','reference'),('bohr-radius','reference'),('gap-radius-model','radius-analysis'),
              ('abs-pl-gap','radius-analysis'),('pl-preference','radius-analysis')]:meas(om,k,sid,'Author optical model / cited reference context')
context(om,'figures-figure-2','radius-analysis','author_derived');context(om,'equations-equation-1','radius-analysis','author_derived')

gm=base('growth-model','Nucleation, particle-number estimates and oriented attachment',method='Author models, derived estimates and mechanistic reasoning')
mat(gm,'sn-hydroxide-model','characterization')
for sid,label in [('nucleus-model','Equation 2 and supersaturation assumptions'),('number-model','Equations 3–4 and optical-derived particle-number estimates'),
    ('attachment-model','Figure 3 collision/attachment schematic'),('mechanism','Author growth/coarsening interpretation')]:
    sample(gm,sid,label,E(3,'Section 3.1; continued discussion pp. 4–6'),formula=None,
        notes=['Author model/interpretation, not measured kinetic trajectories or a separate synthesis.'])
for k,sid in [('density','nucleus-model'),('critical-radius','nucleus-model'),('nucleation-fast','nucleus-model'),
    ('supersaturation-assumptions','nucleus-model'),('intermediate','mechanism'),('dilute-model','mechanism'),
    ('number-equation','number-model'),('number-linear-scope','number-model'),('number-fit-intercept','number-model'),
    ('number-fit-slope','number-model'),('oa-scheme','attachment-model'),('ph-mechanism','mechanism'),('summary-mechanism','mechanism')]:
    meas(gm,k,sid,'Author model / mechanistic interpretation / reference constant, as individually labelled')
# Source-printed fit uncertainties are retained numerically in addition to original qualifiers.
for mid,value,unit in [('number-fit-intercept',0.14e18,'particles/L; preceding-text basis'),
                       ('number-fit-slope',0.07e20,'coefficient multiplying c in mol/L')]:
    gm['measurements'].append(measurement(mid+'-uncertainty','number-model',mid.replace('-','_')+'_reported_uncertainty',
        qty(value,unit,fe(mid),status='author_derived',qualifier='Source-printed ± uncertainty; no confidence level specified.',
            basis='PL-derived linear-regression coefficient, not a direct particle count.'),
        'Author linear regression',fe(mid),conditions='Equation 4; c below 0.04 mol/L'))
for uid,sid in [('figures-figure-3','attachment-model'),('equations-equation-2','nucleus-model'),
                ('equations-equation-3','number-model'),('equations-equation-4','number-model')]:context(gm,uid,sid,'author_derived')
context(gm,'figures-figure-2','number-model','author_derived')

lit=base('source-context','Source identity, references and unresolved information',method='Bibliographic and source-scope context')
sample(lit,'references','Source/reference context',E(1,'Identity and study scope; references p. 6'),formula=None)
meas(lit,'prior-range','references','Prior cited Leite preparation; external full text uninspected')

# Every residual retained inventory entry remains accessible. Source gaps, source
# hash/crop metadata and references are documentary facts, not synthesized samples.
ASSET_CONTEXT={
 'figure-1':[(uv,'concentration-series'),(pl,'concentration-series')],
 'figure-2':[(om,'radius-analysis'),(gm,'number-model')],
 'figure-3':[(gm,'attachment-model')], 'figure-4':[(cs,'hrtem-comparison')],
 'figure-5':[(cs,'hist-comparison')], 'figure-6':[(zeta,'zeta-series'),(pc,'pl-radius-series')],
 'figure-7':[(pc,'hrtem-comparison')], 'equation-1':[(om,'radius-analysis')],
 'equation-2':[(gm,'nucleus-model')], 'equation-3':[(gm,'number-model')],
 'equation-4':[(gm,'number-model')], 'experimental-procedure':[(route,'final-series'),(ph,'treatment-series'),(tem,'acquisition-context')],
 'water-ratio-context':[(route,'final-series'),(gm,'nucleus-model')],
 'references':[(lit,'references')], 'references-continuation':[(lit,'references')]}
for uid,u in U.items():
    if unit_links[uid]:continue
    if u['kind']=='asset':
        key=u['source_payload']['id'].removeprefix(SID+'-')
        for r,sid in ASSET_CONTEXT[key]:context(r,uid,sid)
    else:context(lit,uid,'references')
for r in records.values():
    if r is not route:link(r,'hydrolysis','Controlled-hydrolysis source framework','Related literature context; individual experimental batches and cross-technique specimen joins remain unresolved.')
for key,r in records.items():
    if r is not route:link(route,key,r['title'].split(' · ',1)[1],'Associated source evidence retains its own preparation, specimen and model/reference scope.')

def resolve(obj,pointer):
    v=obj
    for t in pointer.strip('/').split('/'):v=v[int(t)] if isinstance(v,list) else v[t]
    return v
byid={r['record_id']:r for r in records.values()};checks=[]
def check(name,condition):
    checks.append({'check':name,'passed':bool(condition)})
    assert condition,name
for r in records.values():
    errors=validate_record(r);check(r['record_id']+' schema and semantic validation',not errors)
    check(r['record_id']+' private training gate',r['quality']['review_status']=='imported_unreviewed' and not r['quality']['requested_tasks'] and all(not e['eligible'] for e in eligibility(r).values()))
    check(r['record_id']+' no fabricated atomic data or batches',not r['structure_assets'] and r['lineage']['batch_id'] is None and all(p['batch_id'] is None for p in r['products']))
for k,links in fact_links.items():
    check('Source fact bound: '+k,bool(links))
    for v in links:check('Exact canonical fact conversion: '+k+' '+v['pointer'],resolve(byid[v['record_id']],v['pointer'])==fq(k,v['source_array_index']))
for uid,links in unit_links.items():
    check('Source inventory entry bound: '+uid,bool(links))
    for v in links:check('Source inventory pointer resolves: '+uid,resolve(byid[v['record_id']],v['pointer']) is not None)
check('One synthesis framework only',sum(r['record_type']=='literature_protocol' for r in records.values())==1)
check('All nine source preparation operations represented',sum(u['kind']=='operation' for u in U.values())==9)
check('Thirteen operations: nine source preparations plus four reported acquisitions',sum(len(r['operations']) for r in records.values())==13)
check('Ratio basis is unreported',route['operations'][1]['parameters']['water_to_tin_relative_ratio']['basis'].endswith('molar, mass and volume bases are all unreported.'))
check('Treatment pH is not substituted after base',ph['operations'][2]['parameters']['measurement_pH_after_base']['status']=='not_reported')
check('Monitoring window is not hydrolysis hold',route['operations'][1]['parameters']['duration']['status']=='not_reported')
check('No conversion of radii into diameter labels',not any(m['property']=='diameter' for r in records.values() for m in r['measurements']))
check('All original assets retained as contexts',sum(u['kind']=='asset' for u in U.values())==15)
check('All 31 uninspected citations retained',sum(u['kind']=='reference' for u in U.values())==31)
check('No source file was modified',all(sha(B/p)==h for p,h in A['author_file_hashes'].items()))

OUT=B/'canonical-drafts';OUT.mkdir(exist_ok=True)
for r in records.values():write(OUT/(r['record_id']+'.json'),r)
counts={'records':len(records),'record_types':dict(Counter(r['record_type'] for r in records.values())),
        'operations':sum(len(r['operations']) for r in records.values()),'source_preparation_operations':9,'reported_acquisition_operations':4,
        'measurements':sum(len(r['measurements']) for r in records.values()),'material_slots':sum(len(r['materials']) for r in records.values()),
        'stock_contexts':sum(len(r['stocks']) for r in records.values()),'products_and_contexts':sum(len(r['products']) for r in records.values()),
        'source_facts':len(F),'source_fact_bindings':sum(map(len,fact_links.values())),
        'inventory_units':len(U),'inventory_unit_bindings':sum(map(len,unit_links.values())),'original_assets':15,'references':31}
pending=['Independent canonical scientific audit; the prior passed audit covers source extraction only.',
         'Reader, molecular identity, apparatus and original-figure specimen mapping require separate presentation authoring/audits.',
         'SI is unverified; fuller preparations in references 7 and 25 remain uninspected.',
         'No exact atomic coordinates, CIF, supplied XRD trace or SAED pattern are available.',
         'All training eligibility and publication remain disabled.']
write(B/'canonical-source-unit-index.json',{'schema':'mattersyn-derived-inventory-unit-index/1','source_id':SID,
    'scope':'Separate pointer index of every retained inventory entry; no source file modified or new source extraction claimed.',
    'source_inventory_sha256':sha(B/'source-inventory.json'),'units':list(U.values())})
write(B/'canonical-source-coverage.json',{'schema':'mattersyn-canonical-source-coverage/1','source_id':SID,
    'status':'author_mapping_pending_independent_canonical_audit',
    'source_facts_sha256':sha(B/'source-facts.json'),'source_inventory_sha256':sha(B/'source-inventory.json'),
    'source_units_sha256':sha(B/'canonical-source-unit-index.json'),
    'facts':[{'source_fact_id':F[k]['id'],'source_fact':F[k],'canonical_bindings':v} for k,v in fact_links.items()],
    'source_units':[{'source_unit_id':k,'canonical_bindings':v} for k,v in unit_links.items()],
    'normalizations':{'source_status':'Reported qualitative/cited contexts use schema reported, with original status and cited scope in basis/note. Author models/interpretations use author_derived, never measured status.',
        'ranges':'Concentration, pH, acquisition intervals and prior size interval use bounds; raw arrays retained here.',
        'ratio':'The ordered approximately 500:1 water/Sn2+ ratio becomes 500 relative water parts per one relative Sn2+ part with basis explicitly unreported; no molarity, dose or unit conversion is inferred.',
        'cohorts':'Ordered concentration/pH arrays become separate scalar context labels, never new synthesis records.',
        'bounds':'At least 200 particles is a minimum; up to 12 months and up to 2 h are observation maxima; below 0.04 mol/L is exclusive.',
        'uncertainties':'Equation 4 reported ± coefficients are additionally typed; these remain author-derived estimates without a claimed confidence level.'}})
manifest={'schema':'mattersyn-canonical-draft-manifest/1','source_id':SID,'created_at':datetime.now(timezone.utc).isoformat(),
    'status':'private_draft_schema_valid_pending_canonical_scientific_audit','counts':counts,'published':False,'training_eligible':False,
    'source_pdf_hashes':{d['path']:d['sha256'] for d in DOCUMENTS},'source_extraction_audit_sha256':sha(B/'source-scientific-audit.json'),
    'source_inventory_sha256':sha(B/'source-inventory.json'),'source_facts_sha256':sha(B/'source-facts.json'),
    'build_script_sha256':sha(__file__),'dataset_validator_sha256':sha(S/'scripts/dataset_lib.py'),
    'schema_definition_sha256':sha(S/'scripts/schema_definition.py'),'record_helpers_sha256':sha(S/'scripts/record_helpers.py'),
    'records':[{'record_id':r['record_id'],'record_type':r['record_type'],'path':str(OUT/(r['record_id']+'.json')),
        'sha256':sha(OUT/(r['record_id']+'.json')),'operations':[o['id'] for o in r['operations']],
        'samples':[p['sample_id'] for p in r['products']],'measurements':[m['id'] for m in r['measurements']],
        'training_tasks':eligibility(r)} for r in records.values()], 'pending_links_and_gates':pending}
write(B/'canonical-record-manifest.json',manifest)
write(B/'canonical-draft-validation.json',{'schema':'mattersyn-private-draft-validation/1','status':'passed',
    'validation_scope':'Current Draft2020-12 schema plus existing semantic validator, exact fact conversions, inventory coverage and source-boundary author checks. Not independent scientific review.',
    'counts':counts,'checks':checks,'check_count':len(checks),'schema_errors':[],
    'record_hashes':{r['record_id']:sha(OUT/(r['record_id']+'.json')) for r in records.values()},
    'canonical_manifest_sha256':sha(B/'canonical-record-manifest.json'),'coverage_sha256':sha(B/'canonical-source-coverage.json'),
    'published':False,'training_eligible':False,'pending_links_and_gates':pending})
print(json.dumps(counts,ensure_ascii=False))
