"""Stage typed synthesis variants privately; no Site edits or training approval."""
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
SITE = Path(r'[local path redacted]')
sys.path.insert(0, str(SITE / 'scripts'))
from record_helpers import ev, fact, qty, source, record, material, operation, product, state, measurement

D = json.loads((HERE / 'source-extraction.json').read_text(encoding='utf-8'))
SID = 'littau1993'
def evidence(page, section):
    return ev(SID, f'Main PDF p. {page}, printed p. {1223 + page}, {section}')
def convert_evidence(items):
    return [x for a in items for x in evidence(a['pdf_page'], a['section_or_item'])]
def convert_quantity(x, fallback, name):
    if x is None:
        return qty(evidence=fallback, basis=name.replace('_',' ') + ' not reported')
    e = convert_evidence(x['evidence'])
    value = x['value']
    options = dict(unit=x['unit'] or '', evidence=e, approximate=x['qualifier'] in ['approximate','near'],
                   qualifier=x['qualifier'] if x['qualifier'] != 'reported' else '', basis=x['meaning'] or '', raw_text=x['raw'] or '')
    if isinstance(value, list):
        return qty(minimum=value[0], maximum=value[1], **options)
    if isinstance(value,str):
        # Preserve ratios with their explicit component basis, never convert to molarity.
        assert value in ['1:23','1:6']
        options['basis'] = ('Interpretation as added-diluent/aerosol-feed ratio follows the apparatus flow labels; ratio convention not fully explicit, not an unambiguous final/feed factor' if value == '1:23' else 'He per O2 in dilution stream') + '; reported raw ratio ' + value
        options['raw_text'] = value
        return qty(value=int(value.split(':')[1]), status='inferred' if value=='1:23' else 'reported', **options)
    return qty(value=value, **options)

src = source(SID, D['source']['doi'], D['source']['title'], '; '.join(D['source']['authors']),1993,
             si='Not located or verified in either local collection; no main-plus-SI completion claim.')
src['main_status']='All 7 supplied main pages read and visually inspected; independent full-main review and targeted staging-extraction audit completed. Canonical record audit pending.'
names = {'disilane':'Disilane','helium':'Helium','oxygen':'Oxygen','ethylene-glycol':'Ethylene glycol',
         'dichlorosilane':'Dichlorosilane (printed SiH2Cl2)','toluene':'Toluene'}
roles = {'disilane':'nonmetal_precursor','helium':'carrier_gas','oxygen':'oxidant',
         'ethylene-glycol':'collection_medium','dichlorosilane':'apparatus_pretreatment','toluene':'apparatus_pretreatment_solvent'}

records=[]
for variant,table in zip(D['synthesis_variants'][:3],D['table_I']['rows']):
    label=table['sample']; suffix=label.replace('.','p'); rid=f'littau-1993-si-aerosol-{suffix}'
    r=record(rid,f'Littau et al. (1993) · Surface-oxidized silicon colloid {label}', 'Si/SiOx',
             'Surface-oxidized silicon colloids','Continuous aerosol pyrolysis and oxidative passivation',src,
             'Main pp. 1225–1226, Experimental A and Results A',kind='protocol_variant')
    r['material'].update(elements=['Si','O'],components=['Si','SiOx'],architecture='core_shell' if label!='1.0' else 'unresolved')
    r['lineage']['recipe_family']='littau1993-si-aerosol'
    r['collection']='reviewed_literature'
    r['quality'].update(review_status='imported_unreviewed',requested_tasks=[],experimental_outcome='reported_product',
        review_scope='Private typed-record staging. Full main source and source-extraction audits exist; these canonical joins have not yet passed independent review, viewer validation or publication. IDs denote formulation families, not individually documented physical batches.',
        missing_fields=list(D['gaps']),conflicts=[
            'Main p.1225 says 860 °C; Figure1 labels 865 °C. Retain both.',
            'TableI HPLC size intervals/monomer size differ from descriptive prose for6.0/2.0.',
            'Figure9 specifies355nm excitation; p.1229 calls Figures9–11 350nm. No preferred setting inferred.'])
    r['intended_target']['phase']=fact(evidence=evidence(1,'Introduction'),note='Do not place a measured outcome in the prospective target. The1.0 formulation lacks direct core-crystallinity proof.')
    for c in D['chemicals']:
        if c['id'] not in names:continue
        stage='apparatus_pretreatment' if c['id'] in ['dichlorosilane','toluene'] else 'synthesis'
        qs={}
        if c['id']=='ethylene-glycol':
            qs={'prebubbler_volume':qty(9,'cm3',evidence(2,'Experimental A')),
                'collector_volume':qty(9,'cm3',evidence(2,'Experimental A'))}
        elif c['id'] in ['dichlorosilane','toluene']:
            qs={'charge':qty(evidence=convert_evidence(c['evidence']),basis='Frit pretreatment amount not reported')}
        r['materials'].append(material(c['id'],names[c['id']],c['formula'],roles[c['id']],stage,
            convert_evidence(c['evidence']),quantities=qs,notes=[c['summary']]))
    r['stocks']=[{'id':'disilane-He-stock','name':'0.1% disilane in He',
                 'components':[{'material_id':'disilane','quantities':{}},{'material_id':'helium','quantities':{}}],
                 'concentrations':{'reported_disilane_fraction':qty(0.1,'%',evidence(2,'Experimental A'),basis='Commercial gas-mixture fraction; percentage/reference basis not expressly stated')},
                 'preparation_operation_ids':[],'scope':'Matheson supplied gas stock; sample label is flow of this mixture, not pure Si2H6.',
                 'evidence':evidence(2,'Experimental A')}]
    r['material_states']=[
      state('mixed-feed','Diluted gas feed',['disilane-He-stock','helium']),
      state('raw-aerosol','Silicon aerosol after pyrolysis',['mixed-feed']),
      state('wall-deposit','Silicon deposited on quartz',['mixed-feed'],kind='waste'),
      state('quenched-aerosol','Diluted and cooled aerosol',['raw-aerosol','oxygen','helium']),
      state('oxidized-aerosol','Surface-oxidized aerosol',['quenched-aerosol']),
      state('prebubbler-colloid','Prebubbler dispersion',['oxidized-aerosol','ethylene-glycol'],kind='fraction'),
      state('collector-colloid','Frit-collector dispersion',['oxidized-aerosol','ethylene-glycol'],kind='fraction')]
    transitions=[(['disilane-He-stock','helium'],['mixed-feed']),(['mixed-feed'],['raw-aerosol','wall-deposit']),
                 (['raw-aerosol','oxygen','helium'],['quenched-aerosol']),(['quenched-aerosol'],['oxidized-aerosol']),
                 (['oxidized-aerosol','ethylene-glycol'],['prebubbler-colloid','collector-colloid'])]
    action_names=['gas_feed','aerosol_pyrolysis','gas_dilution_quench','aerosol_oxidation','sequential_bubbler_collection']
    labels=['Blend gas feed','Pyrolyze the feed','Dilute and cool the aerosol','Oxidize the particle surface','Collect both colloidal fractions']
    for i,(op,(inputs,outputs),action,heading) in enumerate(zip(D['shared_continuous_protocol'],transitions,action_names,labels)):
        e=convert_evidence(op['evidence']); params={k:convert_quantity(v,e,k) for k,v in op['conditions'].items()}
        if 'oxygen_to_helium' in params:
            params['helium_per_oxygen_ratio']=params.pop('oxygen_to_helium')
        if i<4:
            params['reactor_pressure']=qty(1.4,'atm',evidence(2,'Experimental A'),basis='Reactor operating pressure; absolute/gauge reference not stated. Do not transfer to collection or later procedures.')
        else:
            params['collection_pressure']=qty(unit='atm',evidence=e,basis='Not separately reported for collection bubblers')
        if i==0:
            params['study_wide_disilane_concentration_range']=params.pop('disilane_concentration_range')
            params['study_wide_disilane_concentration_range']['basis']='Study-wide context (3–30ppm), not a tunable range independently assigned to this fixed stock-flow formulation. Exclude from variant-specific training features.'
            params['stock_gas_flow']=convert_quantity(variant['stock_gas_flow'],e,'stock_gas_flow')
            params['stock_gas_flow']['basis']='0.1% Si2H6/He mixture; not pure-disilane flow. Standard-volume reference conditions unstated.'
            params['disilane_partial_pressure']=convert_quantity(variant['disilane_partial_pressure'],e,'disilane_partial_pressure')
        desc=op['summary']+' '+' '.join(op.get('notes',[]))+' '+' '.join(op.get('observations',[]))
        if i==4:
            desc+=' Frit pretreatment uses printed SiH2Cl2 in toluene; amount, concentration, treatment duration and wash/dry details are unreported. This upstream treatment is not a simultaneous gas feed.'
        r['operations'].append(operation(op['id'],action,heading,e,inputs,outputs,
            depends=[] if i==0 else [D['shared_continuous_protocol'][i-1]['id']],parameters=params,
            description=desc.strip(),environment=fact('Dilute Si2H6 in He' if i<2 else 'O2/He dilution stream' if i<4 else None,e,
                note='Collection pressure/temperature history beyond reported reactor conditions is not fully resolved.' if i==4 else ''),
            endpoint=fact(evidence=e)))
    p=product('colloid-'+suffix,'Si/SiOx',evidence(3,'Results A'),link='general_context',
         phase='Diamond-lattice Si core' if label!='1.0' else None,
         surface='Surface oxide described by authors as silicon dioxide; no atomic shell structure established.',
         notes=['Characterization is linked at formulation-label level; exact run and pre-/collector-fraction identity unresolved.',
                'Not an AKS41 sample; its Figure3 TEM cannot become this recipe outcome.',
                'For1.0, authors explicitly lack direct structural proof of crystallineSi.'])
    p['source_sample_label']=label
    p['phase']['evidence']=evidence(5,'Results A crystal-structure limits and lattice-parameter comparison')
    p['phase']['note']='No direct structural proof for1.0; p.1229 also leaves noncrystalline emitters possible.' if label=='1.0' else 'Formulation-level structural assignment; not a deposited experimental atomistic model.'
    if label=='1.0':p['phase']['evidence']+=evidence(6,'Results C')
    p['surface']['evidence']=evidence(4,'Results A, shell microscopy and Figure7 IR')+evidence(5,'Results A, smaller-particle limitations')
    p['surface']['note']='Shell measurement must not be inherited as a measured1.0 shell structure.' if label=='1.0' else 'Amorphous surface-oxide description, not an independently measured exact shell stoichiometry.'
    r['products'].append(p)
    for key,prop,technique,basis in [
      ('TEM_bright_field_nm','overall_particle_diameter','Bright-field TEM','Overall particle diameter; not crystalline-core size'),
      ('TEM_dark_field_core_nm','crystalline_core_diameter','Dark-field TEM','Crystalline-core extent; resolution-limited'),
      ('XRD_coherence_nm','coherence_length','Powder X-ray diffraction','Line-broadening coherence length, not total diameter'),
      ('HPLC_monomer_time_min','monomer_elution_time','Size-exclusion HPLC','Monomer peak elution time'),
      ('HPLC_monomer_equivalent_size_nm','equivalent_HPLC_diameter','Size-exclusion HPLC','Polymer-calibrated equivalent hard-sphere size, not TEM/core diameter'),
      ('HPLC_distribution_fwhm_nm','HPLC_distribution_FWHM_interval','Size-exclusion HPLC','Interval bounds spanning aggregate-containing distribution; not a scalar FWHM or symmetric error')]:
        x=table[key]; unit='min' if key.endswith('_min') else 'nm'; e=evidence(2,'Table I')
        if isinstance(x,dict) and x.get('status')=='not_observed':
            val=qty(unit=unit,evidence=e,qualifier='not_observed',basis=basis+'; source reports not observed, not zero')
        elif isinstance(x,dict) and 'less_than' in x:
            val=qty(x['less_than'],unit,e,qualifier='less_than',basis=basis)
        elif isinstance(x,dict):
            val=qty(unit=unit,evidence=e,minimum=x['range'][0],maximum=x['range'][1],approximate=x['approximate'],basis=basis)
        elif isinstance(x,list):
            val=qty(unit=unit,evidence=e,minimum=x[0],maximum=x[1],basis=basis)
        else:val=qty(x,unit,e,basis=basis)
        if key in ['XRD_coherence_nm','HPLC_monomer_equivalent_size_nm','HPLC_distribution_fwhm_nm'] and val['status']!='not_reported':
            val['status']='author_derived'
        if key.startswith('XRD'):
            conditions='Dried, washed powder; AOT-bound or Mylar-enclosed mounting, Mo K-alpha diffraction. Line-broadening-derived coherence, not an in-dispersion diameter. Exact physical batch/fraction unresolved.'
        elif key.startswith('TEM'):
            conditions='JEOL2000-FX at200keV; direct aerosol collection or evaporated colloid on holey carbon; exact preparation branch, batch and collector fraction not assigned.'
        else:
            conditions='HPLC formulation/fractionation context; sequential ZORBAX60-S/300-S,50degC,0.75cm3/min mobile phase; polymer-calibrated equivalent size, exact batch/collector fraction unresolved.'
        method_evidence=evidence(2,'Experimental B, characterization and specimen preparation')
        if key.startswith('XRD'):method_evidence+=evidence(3,'Experimental B continuation, X-ray acquisition')
        r['measurements'].append(measurement(key,'colloid-'+suffix,prop,val,technique,e+method_evidence,
            conditions=conditions))
    # Optical values belong to acid-activated material and are deliberately not
    # attached to these as-collected synthesis records. The audited full staging
    # extraction retains them for separate transformation/procedure records.
    r['context_links']=[{'label':'Original paper','url':'https://doi.org/10.1021/j100108a019','relation':'source'}]
    records.append(r)

out=HERE/'canonical-drafts';out.mkdir(exist_ok=True)
for r in records:
    (out/(r['record_id']+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report={'status':'private_drafts_not_integrated', 'source_extraction_sha256':hashlib.sha256((HERE/'source-extraction.json').read_bytes()).hexdigest(),
        'records':[r['record_id'] for r in records], 'schema_version':'1.0.0',
        'source_audit_reused':True,'canonical_audit_completed':False,'training_eligible':False,'published':False,
        'remaining':['Canonical source-to-record audit','Nine supporting procedures and associated activated/dry/fractionated sample measurements','AKS41 contextual evidence','Coverage ledger and original figures','Continuous-flow reader scenes and molecular assets','Inventory reconciliation and site checks','Publication']}
(HERE/'canonical-drafts-status.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
