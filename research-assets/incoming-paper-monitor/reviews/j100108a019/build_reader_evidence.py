"""Private source-item reconciliation. Does not edit records, Site, or source PDFs."""
from pathlib import Path
import hashlib
import json
import re
from collections import Counter

HERE=Path(__file__).resolve().parent
def load(name): return json.loads((HERE/name).read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
D=load('source-extraction.json')
SPEC=load('reader-integration-spec.json')
MAN=load('crop-assets/manifest.json')
files=[p for folder in ['canonical-drafts','procedure-drafts','context-drafts'] for p in sorted((HERE/folder).glob('*.json'))]
R={json.loads(p.read_text(encoding='utf-8'))['record_id']:json.loads(p.read_text(encoding='utf-8')) for p in files}
assert len(R)==13
protected={str(p):sha(p) for p in files+[HERE/'source-extraction.json',HERE/'reader-integration-spec.json',HERE/'crop-assets/manifest.json']}
FLOW=['littau-1993-si-aerosol-'+s for s in ['6p0','2p0','1p0']]
P={
 'acid-activation':'littau-1993-si-acid-activation', 'concentrate':'littau-1993-si-colloid-concentration',
 'dry-powder':'littau-1993-si-powder-preparation', 'HPLC':'littau-1993-si-hplc-fractionation',
 'TEM':'littau-1993-si-tem-characterization', 'IR':'littau-1993-si-ir-characterization',
 'powder-XRD':'littau-1993-si-xrd-characterization','optical-acquisition':'littau-1993-si-optical-characterization',
 'time-resolved-PL':'littau-1993-si-time-resolved-pl'}
AKS='littau-1993-aks41-context'
ITEMS=[]
UNITS=[]

def enc(s): return str(s).replace('~','~0').replace('/','~1')
def resolve(obj, ptr):
    for part in ptr.strip('/').split('/') if ptr else []:
        key=part.replace('~1','/').replace('~0','~')
        obj=obj[int(key)] if isinstance(obj,list) else obj[key]
    return obj
def leaves(obj,p=''):
    if isinstance(obj,dict) and obj:
        for k,v in obj.items(): yield from leaves(v,p+'/'+enc(k))
    elif isinstance(obj,list) and obj:
        for i,v in enumerate(obj): yield from leaves(v,p+'/'+str(i))
    else: yield p,obj
def E(page,locator):
    return {'source_id':'littau1993','document':'main','pdf_page':page,'printed_page':1223+page,'locator':locator}
def evidence_of(x):
    found=[]
    def walk(v):
        if isinstance(v,dict):
            if {'pdf_page','section_or_item'} <= v.keys():
                z=E(v['pdf_page'],v['section_or_item'])
                if z not in found:found.append(z)
            for val in v.values():walk(val)
        elif isinstance(v,list):
            for val in v:walk(val)
    walk(x)
    return found
def scope(formulations=None,state='Not assigned',kind='study_context',note=''):
    return {'formulations':formulations or [],'state':state,'scope_kind':kind,'physical_batch_id':None,
            'collector_fraction':None,'link_limit':note or 'No exact physical batch/collector-fraction join is established.'}
def links(rids,field=None,ids=None):
    result=[]
    for rid in ([rids] if isinstance(rids,str) else rids):
        assert rid in R
        if field is None:result.append({'record_id':rid,'json_pointer':'','coverage':'Related record; not evidence that every staged detail is already encoded.'});continue
        rows=R[rid][field]
        for i,row in enumerate(rows):
            idkey='sample_id' if field=='products' else 'id'
            if ids is None or row[idkey] in ids:
                result.append({'record_id':rid,'json_pointer':f'/{field}/{i}',
                               'coverage':'This specific canonical object; additional source context is preserved below.'})
    return result
def spec_section(section):
    return ['/section_rules/'+enc(section)] if section in SPEC['section_rules'] else ['/review_scope']
def spec_item(field,id):
    return ['/'+field+'/'+str(i) for i,x in enumerate(SPEC[field]) if x.get('id')==id]
def add(ptr,title,text,section,claim,sample,disposition='readercontext',canonical=None,evidence=None,notes=None,
        spec=None,details=None,id=None,reason=None):
    src=resolve(D,ptr) if ptr else None
    uid=id or ('source-'+ptr.strip('/').replace('/','-').replace('~1','-'))
    item={'id':uid,'source_pointer':ptr or None,'title':title,'text':text,'reader_section':section,
          'claim_type':claim,'sample_scope':sample,'disposition':disposition,
          'disposition_reason':reason or ('Preserve source-linked reader context; numeric values here are not new training targets.' if disposition=='readercontext'
                                       else 'Mapped to existing private canonical content; downstream reader validation remains pending.' if disposition=='canonicalrecord'
                                       else 'Source linkage or information remains unresolved; preserve the limitation.' if disposition=='unresolved'
                                       else 'Administrative provenance retained privately, not a scientific reader claim.'),
          'evidence':evidence if evidence is not None else evidence_of(src),
          'canonical_links':canonical or [],'reader_spec_pointers':spec or spec_section(section),
          'notes':notes or [],'training_eligible':False,'reader_render_status':'pending_root_integration_and_visual_check'}
    if details is not None:item['reader_details']=details
    # Curated staging payload, never the full article text. Ensures nested numeric details and missingness remain inspectable.
    if ptr and disposition!='excludedreason':item['staged_detail']=src
    ITEMS.append(item)
    if ptr:UNITS.append({'id':uid,'source_pointer':ptr,'disposition':disposition,'reader_evidence_id':uid,
                         'canonical_links':item['canonical_links'],'reason':item['disposition_reason']})
    return item

# Administrative fields are accounted separately rather than copied as public paper content.
for key in ['extraction_schema','status','training_eligible','website_published']:
    add('/'+key,'Private extraction state',str(D[key]),'Sources and limitations','curation_metadata',scope(),
        'excludedreason',reason='Private workflow metadata; source-to-view completion and publication must be verified independently.')
for key,val in D['source'].items():
    public=key in ['title','authors','journal','year','volume','pages','doi','pdf_pages','si_status']
    add('/source/'+key,'Source '+key.replace('_',' '),str(val),'Sources and limitations','bibliographic_or_review_metadata',scope(),
        'readercontext' if public else 'excludedreason',evidence=[E(1,'Title/author/journal block')] if key not in ['si_status','pdf_pages','main_file','sha256','source_folder_unmodified','doi_provenance'] else [],
        reason='Bibliographic/review context; source identities are reused, not a second unique paper.' if public else 'Local filesystem/provenance bookkeeping; keep private.')
for key,val in D['review'].items():
    add('/review/'+key,'Review '+key.replace('_',' '),str(val),'Sources and limitations','curation_metadata',scope(),
        'excludedreason',reason='Historical extraction-stage workflow text, not the current integration completion status. See latest audits separately.')
for key,val in D['relevance'].items():
    add('/relevance/'+key,'Source relevance: '+key.replace('_',' '),str(val),'Sources and limitations','curation_scope',scope(['6.0','2.0','1.0','AKS41']),
        evidence=[E(1,'Title/Introduction'),E(5,'Results A structure limitations')])
for i,val in enumerate(D['new_field_requirements']):
    add('/new_field_requirements/'+str(i),'Data concept: '+val,val,'Sources and limitations','schema_requirement',scope(),
        'readercontext',spec=['/implementation_issues','/acceptance_checks'],
        reason='Implementation/interpretation requirement; not an independently measured datum or proof of a new schema field.')

# Chemical cards preserve roles; ambiguous short names are not silently resolved by model generation.
aliases={'sodium-methoxide':['sodium-methylate'],'tetrabutylammonium-bromide':['tbab'],
         'polystyrene-sulfonate-sodium':['polymer-calibrants'],'potassium-bromide':['kbr'],'rhodamine-6g':['r6g']}
for i,c in enumerate(D['chemicals']):
    ids=[c['id']]+aliases.get(c['id'],[])
    refs=[z for rid in R for z in links(rid,'materials',ids)]
    add(f'/chemicals/{i}',c['id'].replace('-',' ').capitalize(),c['summary'],'Precursors','reported_material_identity_and_role',
        scope(state=c['role'],kind='procedure_input_or_reference'), 'canonicalrecord' if refs else 'unresolved',
        canonical=refs,spec=spec_item('chemical_registry_plan',c['id']),
        notes=['Molecular asset/registry validation is separate from formula/text extraction. Analytical reagents are not mandatory furnace inputs.',
               'Full curated identity notes and reported missing quantities remain in staged_detail.'])
for i,s in enumerate(D['stocks']):
    refs=links(FLOW,'stocks',['disilane-He-stock']) if i==0 else links(P['acid-activation'],'stocks',['acidic-water'])
    add(f'/stocks/{i}','Disilane/He supply stock' if i==0 else 'Acidified water',
        'The gas stock contains 0.1% disilane in helium; percentage reference basis is unstated.' if i==0 else 'Added water is at pH 1 using sulfuric acid; acid concentration and charge are not given.',
        'Precursors','reported_stock',scope(['6.0','2.0','1.0'],'Gas feed stock' if i==0 else 'Activation additive'),
        'canonicalrecord',canonical=refs)
for i,s in enumerate(D['shared_continuous_protocol']):
    add(f'/shared_continuous_protocol/{i}',s['id'].capitalize(),s['summary'],'Synthesis protocol','reported_shared_protocol_with_context',
        scope(['6.0','2.0','1.0'],'Continuous aerosol stage '+s['id'],'shared_protocol'),
        'canonicalrecord',canonical=links(FLOW,'operations',[s['id']]),spec=spec_item('scene_stages',s['id']) or ['/scene_stages'],
        notes=['Study-wide ranges and operational observations must not become variant-specific tuning labels. Staged nested conditions/notes remain inspectable.'])
for i,v in enumerate(D['synthesis_variants']):
    rid=FLOW[i] if i<3 else AKS
    add(f'/synthesis_variants/{i}','Formulation '+('6.0','2.0','1.0','AKS41')[i],v['summary'],
        'Synthesis protocol' if i<3 else 'Final structures','formulation_definition' if i<3 else 'contextual_prior_apparatus_sample',
        scope([('6.0','2.0','1.0','AKS41')[i]],'Multiple analytical/post-treatment states; do not collapse','formulation_family'),
        'canonicalrecord',canonical=links(rid),notes=['AKS41 has no quantified recipe and is not a fourth reconstructed flow method.'] if i==3 else [])
for i,p in enumerate(D['supporting_procedures']):
    section='Synthesis protocol' if p['id'] in ['acid-activation','concentrate','dry-powder','HPLC'] else ('Properties' if p['id'] in ['IR','optical-acquisition','time-resolved-PL'] else 'Final structures')
    forms=['1.0'] if p['id']=='time-resolved-PL' else ['6.0'] if p['id']=='IR' else []
    add(f'/supporting_procedures/{i}',p['id'].replace('-',' '),p['summary'],section,'supporting_procedure',
        scope(forms,'Procedure-specific input/output states','shared_or_contextual_procedure'),
        'canonicalrecord',canonical=links(P[p['id']]),
        notes=['Not a new independent synthesis recipe or experimental batch. Preserve activation, dried-powder and HPLC-fraction states.',
               'Complete nested calibration values and missing quantities are preserved in staged_detail, even if displayed as reader context.'])

# Table I is reconciled cell by cell, including missing/not-observed cells.
add('/table_I/evidence','Table I provenance','Original Table I is on PDF page 2, printed page 1225.','Final structures','table_provenance',
    scope(['6.0','2.0','1.0'],'Cross-technique formulation comparison'),evidence=evidence_of(D['table_I']))
for i,row in enumerate(D['table_I']['rows']):
    rid=FLOW[i];label=row['sample'];slug=label.replace('.','p')
    for key,val in row.items():
        if key=='sample':refs=links(rid,'products');claim='formulation_label'
        elif key=='activated_PL_peak_nm':refs=links(P['acid-activation'],'measurements',['activated-pl-peak-'+slug]);claim='reported_activated_property'
        else:refs=links(rid,'measurements',[key]);claim='reported_or_author_derived_technique_specific_measurement'
        add(f'/table_I/rows/{i}/{key}',f'Table I · {label} · {key}',str(val),'Properties' if key=='activated_PL_peak_nm' else 'Final structures',claim,
            scope([label],'Acid-activated colloid' if key=='activated_PL_peak_nm' else 'Technique-specific colloid, grid or powder; same-batch identity unresolved','table_cell'),
            'canonicalrecord',canonical=refs,evidence=evidence_of(D['table_I']),
            notes=['Do not interpret not-observed values as numeric zero or assign diamond-Si crystallinity to 1.0.'])
add('/table_I/notes','Table I interpretation','Values compare formulation families across methods and specimen preparation states. Luminescence belongs to activated colloids.',
    'Final structures','source_join_limitation',scope(['6.0','2.0','1.0'],'Mixed analytical states'),evidence=evidence_of(D['table_I']))

# Hand-reconciled observations: all descriptive and numeric content remains reader-visible/contextual.
OBS={
 '6.0-TEM-distribution':('Final structures','author_derived_TEM_dimensions',['6.0'],'TEM specimens',
   'The 6.0 formulation has a mean overall TEM diameter of 7.5 nm and a 2.5 nm standard deviation. Its average core is about 5 nm and oxide shell about 1.2 nm.',
   links(FLOW[0],'measurements',['TEM_bright_field_nm','TEM_dark_field_core_nm'])+links(P['TEM'],'measurements',['tem-6p0-total-diameter-standard-deviation','tem-6p0-oxide-shell-thickness'])),
 '6.0-HPLC-conflict':('Final structures','source_conflict',['6.0'],'HPLC distribution',
   'Table I gives a 5–13 nm FWHM interval; Results A gives 5.5–13 nm. Both refer to the broader chromatographic distribution, distinct from the approximately 6.5 nm monomer peak.',links(FLOW[0],'measurements',['HPLC_distribution_fwhm_nm','HPLC_monomer_equivalent_size_nm'])),
 '2.0-HPLC-conflict':('Final structures','source_conflict',['2.0'],'HPLC distribution',
   'Table I lists a 4.2 nm monomer-equivalent size; the prose describes a barely resolved shoulder near 4.5 nm. Retain both source statements.',links(FLOW[1],'measurements',['HPLC_monomer_equivalent_size_nm'])),
 '1.0-structure-limit':('Final structures','author_inference_and_detection_limit',['1.0'],'Dry powder/structural characterization',
   'The 1.0 powder shows diffuse X-ray background without a resolved crystalline signal. The authors infer that any crystalline Si, if present, would be below 2 nm; they explicitly report no direct structural information. This is not a measured 2 nm crystal.',links(FLOW[2],'products')+links(FLOW[2],'measurements',['XRD_coherence_nm'])),
 'lattice':('Final structures','author_fit_with_bulk_reference',['6.0','2.0'],'Dry powder',
   'A simultaneous fit places both lattice parameters within 0.25% of the bulk-Si reference value 5.43 Å. The article does not supply exact measured nanocrystal lattice constants or atomic coordinates.',links(P['powder-XRD'],'measurements')),
 'AKS41-TEM':('Final structures','measured_contextual_TEM',['AKS41'],'Population and distinct depicted particle',
   'AKS41 is from an earlier apparatus. The individually imaged particle has a 13 nm core, a 1.5 nm amorphous shell and 3.1 Å (111) fringes. Population-average individual crystallite size is 14 nm with 3 nm standard deviation; the averaging sentence does not clearly distinguish outer diameter from core extent. Prose mentions diamond-Si diffraction rings but no SAED image is supplied.',links(AKS,'measurements',['population-tem-mean','population-tem-sd','fig3-core','fig3-shell','fig3-fringes'])),
 'aggregation':('Final structures','fractionation_observation_and_author_interpretation',['AKS41'],'HPLC fractions and reinjection',
   'AKS41 fractions share similar individual-crystallite size distributions: the excluded large-size peak contains aggregates; the approximately 16 nm equivalent-size peak mostly dimers/trimers; and the approximately 11 nm peak mostly single crystallites. Fractions retain their elution times on reinjection, supporting permanent aggregation. The source says reinjection persistence also occurs in the other colloids.',links(AKS,'products')+links(AKS,'measurements',['excluded-size','middle-size','monomer-size','exclusion-elution'])),
 'IR-peaks':('Properties','spectral_observation_with_author_assignments',['6.0'],'Washed dry powder/KBr',
   'IR shows bands near 1100 cm⁻¹ (strong) and 800 cm⁻¹ (weak), assigned to oxide, and an OH stretch near 3300 cm⁻¹. Sharp 1350 and 1700 cm⁻¹ features depend on washing and are tentatively attributed to residual organics. The near absence of a 2100 cm⁻¹ SiH band is qualitative, not zero hydrogen.',links(P['IR'],'measurements')+links(P['IR'],'products')),
 'absorption':('Properties','experimental_spectral_shape_with_bulk_model_comparison',['6.0','2.0','1.0','AKS41'],'Colloids; not assumed acid-activated',
   'The 6.0 and AKS41 colloids have similar bulk-like UV absorption: a weak visible tail starting near 370 nm and stronger absorption over 370–240 nm. The 2.0/1.0 spectra lose inflections without a clear blue shift or discrete structure. The actual indirect gap is not directly observed at the low concentration used.',links(P['optical-acquisition'],'operations',['uv-vis'])),
 'activation-state':('Properties','reported_state_dependent_optical_observation',['6.0','2.0','1.0'],'As-made and acid-activated kept separate',
   'As-made emission is weak; the 6.0 broad initial peak lies near 900–950 nm. After acidic activation, the reported peaks are 970, 770 and 660 nm for 6.0, 2.0 and 1.0. Peak positions and chromatograms vary between runs.',links(P['acid-activation'],'measurements',['activated-pl-peak-6p0','activated-pl-peak-2p0','activated-pl-peak-1p0'])+links(P['optical-acquisition'],'measurements',['as-made-6p0-weak-pl'])),
 'PL-yield':('Properties','author_estimated_quantum_yield_with_dye_reference',['6.0','2.0','1.0'],'Activated formulation cohort',
   'All three activated formulations have estimated quantum yields slightly above 5%. The comparison uses dilute R6G in ethanol with reference yield 0.9, initial-absorbance correction and integrated emission. This is one cohort-level statement, not three independently measured exact 5% outcomes.',links(P['acid-activation'],'measurements',['activated-qy-shared-estimate'])),
 'PL-decay':('Properties','author_multiexponential_fit',['1.0'],'Activated-colloid optical context',
   'The preliminary decay is multiexponential; major fitted components of 17 and 76 μs are reported. Amplitudes, full fit details and uncertainties are absent. These are not independently measured radiative lifetimes.',links(P['time-resolved-PL'],'measurements')),
 'pH-quenching':('Properties','qualitative_post_treatment_observation',['6.0','2.0','1.0'],'Activated cohort; exact specimen unspecified',
   'Making the dispersion more basic than approximately pH 5 quenches room-temperature emission. A second acidic reflux can partly restore it, but extended strong-base storage can prevent recovery. Base identity, dose and exposure time are not provided; there is no complete base-treatment recipe.',links(P['acid-activation'],'measurements',['activated-qy-shared-estimate'])),
 'mass-accounting':('Synthesis protocol','reported_throughput_and_author_model_mass_estimate',['6.0','2.0','1.0'],'Continuous production and separate collectors',
   'For the 6.0 formulation, the Si feed rate is 21 mg/day. Comparing measured optical density with a Mie calculation suggests approximately one-third of input Si is collected as colloidal crystallites, with day-to-day variation; 2.0/1.0 have similar reported yields. About two-thirds of collected crystallites reach the second bubbler. These denominators differ and do not define one measured batch yield.',links(FLOW,'operations',['collection'])),
 'concentration-calibration':('Properties','author_model_calibration',[],'Hypothetical bulk-crystalline-Si particle optical response',
   'The authors calculate an optical density of 1.85 at 295 nm for 1 mg/cm³ crystalline Si and a 1 mm path. They expect approximate diameter independence below 50 nm only when quantum effects and strong aggregation-driven Rayleigh scattering are absent. This is model calibration, not measured colloid absorbance or concentration.',[]),
 'stability':('Synthesis protocol','qualitative_colloid_stability_observation',[],'Collected colloids',
   'Collected colloids reportedly resist flocculation for months under air and during reflux, centrifuging and concentration. This does not establish months-long activated photoluminescence stability or provide a quantified centrifugation protocol.',links(FLOW,'products')),
 'unwashed-powder':('Final structures','experimental_impurity_observation_and_unresolved_identity',[],'Powder before washing',
   'Reference note 41 reports additional sharp XRD lines and unidentified crystallites tens of nanometers across when powder is not washed. The authors suggest an oxidized molecular pyrolysis product, but its composition is unresolved.',links(P['dry-powder'],'products')),
 'current-colloid-electron-diffraction':('Final structures','prose_only_diffraction_observation',['6.0','2.0','1.0'],'TEM/electron diffraction contexts',
   'The 6.0 colloid gives intense crystalline-Si electron diffraction. Discussion of the smaller colloids mentions weak broadened rings, but the authors explicitly state that 1.0 lacks direct structural information. No electron-diffraction/SAED image is shown, and the prose cannot establish an unambiguous crystalline phase for 1.0.',links(P['TEM'],'products')+links(FLOW[2],'products')),
 '2.0-TEM-size-bias':('Final structures','experimental_subset_and_author_sampling_bias',['2.0'],'Occasional lattice-resolved particles',
   'Occasional 2.0 particles show 3–4 nm lattice-resolved cores. The 2–4 nm dark-field cores are near the imaging limit and likely represent the larger part of the population relative to the 2 nm XRD coherence length. These dimensions use different techniques and sampling scopes.',links(P['TEM'],'measurements',['tem-2p0-occasional-lattice-core-size'])+links(FLOW[1],'measurements',['TEM_dark_field_core_nm','XRD_coherence_nm'])),
 '1.0-excitation-spectrum':('Properties','prose_only_spectral_observation',['1.0'],'Acid-activated colloid',
   'The source states that the 1.0 luminescence excitation spectrum follows the UV absorption spectrum. No separate excitation-spectrum plot is displayed, and Figure 2 itself shows 6.0/2.0 absorption, not a new 1.0 trace.',[]),
 'bulk-silicon-optical-control':('Properties','external_bulk_reference_control',[],'High-quality bulk Si; room versus liquid-helium temperature',
   'Bulk crystalline Si gives no detectable room-temperature emission in the authors’ apparatus. At liquid-helium temperature it gives a sharp 1060 nm line. Neither a numeric zero intensity nor an exact helium temperature is reported. This is not a nanoparticle synthesis outcome.',links(P['optical-acquisition'],'measurements',['bulk-si-low-temperature-emission'])+links(P['optical-acquisition'],'products',['bulk-si-optical-control']))
}
for i,o in enumerate(D['observations']):
    section,claim,forms,state,text,refs=OBS[o['id']]
    extra=[]
    if o['id'] in ['6.0-HPLC-conflict','2.0-HPLC-conflict']:extra=[E(2,'Table I')]
    if o['id']=='absorption':extra=[E(3,'Results A, Figure 2 and Mie comparison')]
    add(f'/observations/{i}',o['id'].replace('-',' '),text,section,claim,scope(forms,state),canonical=refs,
        evidence=evidence_of(o)+extra,
        reason='Reader context preserves the full observation and its limits; linked canonical objects cover only the explicitly listed measurements or notes.')

# Quantities in narrative-only items are typed without promoting them to measured targets.
extra_quantities={
 'mass-accounting':[{'name':'Si_input_rate_6p0','value':21,'unit':'mg/day','status':'source_reported_rate'},
                    {'name':'estimated_capture_fraction_of_input_Si','value':1/3,'raw':'about one-third','unit':'fraction','status':'author_model_derived_estimate'},
                    {'name':'second_bubbler_fraction_of_collected_crystallites','value':2/3,'raw':'about two-thirds','unit':'fraction','status':'source_reported_approximate_partition'}],
 'concentration-calibration':[{'name':'model_crystalline_Si_concentration','value':1,'unit':'mg/cm3','status':'model_input'},
                              {'name':'model_optical_density','value':1.85,'unit':'dimensionless','status':'author_model_output'},
                              {'name':'wavelength','value':295,'unit':'nm','status':'model_condition'},
                              {'name':'path_length','value':1,'unit':'mm','status':'model_condition'},
                              {'name':'size_independence_upper_context','value':50,'unit':'nm','qualifier':'below_about','status':'conditional_model_validity_claim'}],
 'pH-quenching':[{'name':'quenching_pH_context','value':5,'unit':'pH','qualifier':'above_about','status':'qualitative_experimental_threshold'}],
 'absorption':[{'name':'strong_absorption_region','minimum':240,'maximum':370,'unit':'nm','status':'reported_spectral_region'},
               {'name':'visible_tail_start','value':370,'unit':'nm','status':'reported_spectral_region'}]
}
for o in D['observations']:
    if o['id'] in extra_quantities:
        item=next(x for x in ITEMS if x['source_pointer']==f"/observations/{D['observations'].index(o)}")
        item['reader_details']={'quantities':extra_quantities[o['id']], 'join':'context_unlinked_to_physical_batch','training_target':False}

# All original assets are referenced, not recopied or digitized.
ASSETS=[]
asset_scopes={
 'figure-1':(['6.0','2.0','1.0'],'Shared current apparatus','Synthesis protocol','apparatus_schematic'),
 'figure-2':(['6.0','2.0'],'Colloid absorption; top 6.0, bottom 2.0','Properties','experimental_spectra'),
 'figure-3':(['AKS41'],'Aggregate and one lattice-resolved particle','Final structures','experimental_TEM'),
 'figure-4':(['AKS41'],'HPLC distribution/fractions','Final structures','experimental_chromatogram_with_calibrated_axis'),
 'figure-5':(['6.0'],'HPLC distribution, monomer and aggregates','Final structures','experimental_chromatogram_with_calibrated_axis'),
 'figure-6':(['6.0','2.0'],'Dry powders; top 6.0, bottom 2.0','Final structures','measured_pattern_plus_author_fit'),
 'figure-7':(['6.0'],'Dry washed powder, IR','Properties','experimental_spectrum'),
 'figure-8':(['1.0'],'HPLC monomer and aggregates; crystallinity unresolved','Final structures','experimental_chromatogram_with_calibrated_axis'),
 'figure-9':(['6.0'],'Lower as-made; upper acid-activated','Properties','experimental_state_comparison'),
 'figure-10':(['2.0'],'Activated, established by surrounding Results B','Properties','experimental_spectrum'),
 'figure-11':(['1.0'],'Activated, not structural proof','Properties','experimental_spectrum'),
 'figure-12':(['1.0'],'Activated optical context; measured decay and fit components distinct','Properties','experimental_decay_with_author_fit'),
 'table-1':(['6.0','2.0','1.0'],'Mixed techniques/states; PL column acid-activated','Final structures','cross_technique_summary_table')}
for a in MAN['items']:
    forms,state,section,claim=asset_scopes[a['id']]
    src=HERE/'crop-assets'/a['file']
    assert sha(src)==a['sha256']
    sp=spec_item('original_assets',a['id']);assert sp
    asset={'id':a['id'],'relative_path':'crop-assets/'+a['file'],'sha256':a['sha256'],'source_sha256':MAN['source_sha256'],
           'evidence':[E(a['pdf_page'],a['id'])],'sample_scope':scope(forms,state,'original_asset'),
           'reader_section':section,'evidence_class':claim,'spec_pointer':sp[0],'disposition':'readercontext',
           'crop_visual_review':a['visual_review'],'reader_render_status':'pending_root_integration_and_visual_check',
           'raw_curve_digitized':False,'caption_axes_labels_retained':a['caption_axes_labels_retained'],
           'restriction':'Do not relabel AKS41 as a current formulation; do not treat fit/background curves as extra measured samples.'}
    ASSETS.append(asset)
for i,f in enumerate(D['figures']):
    a=next(x for x in ASSETS if x['id']==f['id'])
    add(f'/figures/{i}',f['id'].replace('-',' ').title(),f['summary'],a['reader_section'],a['evidence_class'],a['sample_scope'],
        evidence=a['evidence'],spec=[a['spec_pointer']],details={'asset_id':a['id'],'relative_path':a['relative_path'],'sha256':a['sha256']},
        notes=[f['caveat'],'An original figure crop is source evidence, not digitized numeric raw data or proof of a complete reader join.'])
for key,val in D['other_items'].items():
    add('/other_items/'+key,'Original '+key.replace('_',' '),
        'Table I is retained as an original crop and reconciled cell by cell.' if key=='tables' else
        'No numbered display equations or unnumbered schemes were identified in the supplied main document.' if key in ['display_equations','unnumbered_schemes'] else
        'The bibliography contains 47 entries, including experimental notes. Cited works were not independently reviewed; reference 36 and 41 notes are evidence in this article itself.',
        'Sources and limitations','source_inventory' if key!='references' else 'bibliographic_context',scope(),
        evidence=[E(7,'References and Notes')] if key=='references' else [E(2,'Table I')] if key=='tables' else [],
        spec=spec_item('original_assets','table-1') if key=='tables' else ['/review_scope'])

INTUITION_TEXT={
 'high-temperature':'The authors choose high-temperature gas-phase synthesis because strongly covalent Si may require more energy to anneal into ordered crystallites than partially ionic II–VI materials in coordinating solvents.',
 'carrier':'The stated rationale for helium is that hydrogen suppresses homogeneous nucleation. Higher pressure is said to improve thermal conduction and reduce aggregation, wall loss and contamination. These are author rationales, not a controlled isolated comparison in this paper.',
 'quench':'Rapid dilution and cooling are intended to arrest further growth and aggregation before deliberate surface oxidation.',
 'collection':'Ethylene glycol is selected for silica affinity and low vapor pressure. A first bubbler saturates the gas with glycol vapor, stabilizes the second-bubbler liquid volume and reduces losses on its frit.',
 'HPLC-surface-chemistry':'The authors propose that base ionizes surface hydroxyls on particles and packing, reducing adsorption, while the added electrolyte screens repulsion so particles can enter smaller pores.',
 'HPLC-column-stability':'Reference note 36 states that nonaqueous mobile phase and silanized packing appear to slow silica-column degradation. Calibration performance is reported stable over several months; this is column stability, not colloid or emission stability.',
 'surface-activation':'Further oxidation of residual nonradiative traps and a change in the crystallite Fermi level are proposed explanations for acidic activation. Neither mechanism is established by the reported measurements.',
 'confinement':'The authors consider both confined Si states and participation of the Si/oxide interface. For the smallest emitters, polymeric or noncrystalline silicon species cannot be ruled out. These alternatives are hypotheses, not additional measured phases.',
 'outlook':'Narrower size distributions and better sample-linked structural and spectroscopic characterization are needed to distinguish size, aggregation and surface effects. The expected narrowing of emission with a narrower size distribution is an outlook, not a demonstrated optimization.'}
for i,c in enumerate(D['chemical_intuition']):
    related=links(P['HPLC']) if c['id'].startswith('HPLC') else links(P['acid-activation']) if c['id']=='surface-activation' else links(FLOW) if c['id'] in ['carrier','quench','collection'] else []
    add(f'/chemical_intuition/{i}',c['id'].replace('-',' ').capitalize(),INTUITION_TEXT[c['id']],'Chemical intuition',c['claim_type'],
        scope(['6.0','2.0','1.0'] if c['id']=='surface-activation' else [],'Source rationale/interpretation','author_intuition'),
        canonical=related,notes=['Cited antecedent studies are not treated as independently inspected evidence.'])
for i,g in enumerate(D['gaps']):
    add(f'/gaps/{i}','Source limitation',g,'Sources and limitations','missing_or_unresolved_information',scope(),
        'unresolved',evidence=[],notes=['This is a source-review limitation, not a measured failure or evidence that unavailable data never existed.'])

# Supplemental reader notes from the already-read same source. No new paper was consulted.
add(None,'Operating regime observations',
    'The source describes 2–8 nm crystalline particles at the first-zone exit, amorphous particles with substantially faster flow or temperatures below 700 °C, and no apparent operational change over 850–1050 °C. These are study-level observations without complete matched parameter sets; they do not define additional reproducible recipes.',
    'Synthesis protocol','study_level_experimental_observation',scope(['6.0','2.0','1.0'],'First furnace; study-wide context'),
    id='context-operating-regime',evidence=[E(2,'Experimental A')],canonical=links(FLOW,'operations',['pyrolysis']),
    details={'quantities':[{'name':'zone_exit_particle_size','minimum':2,'maximum':8,'unit':'nm','scope':'study_level'},
                          {'name':'amorphous_temperature_context','value':700,'unit':'degC','qualifier':'below','other_condition':'substantially faster flow alternative; numerical value absent'},
                          {'name':'no_apparent_change_temperature_range','minimum':850,'maximum':1050,'unit':'degC','scope':'study_level'}]})
add(None,'Operating consumption and collection balance',
    'Dilution consumes approximately one 1A tank of compressed helium per 24 hours; the tank capacity is not supplied. The prebubbler loses 2–3 cm³ ethylene glycol per 24 hours. Neither statement sets a synthesis run duration, and collector partition must stay separate from Si-feed capture efficiency.',
    'Synthesis protocol','reported_operational_context',scope(['6.0','2.0','1.0'],'Continuous apparatus; exact run unspecified'),
    id='context-operational-consumption',evidence=[E(2,'Experimental A, oxidation and collection')],canonical=links(FLOW,'operations',['oxidation','collection']),
    details={'quantities':[{'name':'He_consumption','value':1,'unit':'1A tank/24 h','qualifier':'about','tank_capacity':None},
                          {'name':'prebubbler_EG_loss','minimum':2,'maximum':3,'unit':'cm3/24 h'}]})
add(None,'UV absorption across chromatographic fractions',
    'For 6.0, UV spectral shape does not change appreciably across the particle-elution range. Molecular-region absorption near 14.8 minutes is small compared with particle absorption at earlier times. This supports the authors’ optical concentration estimate but does not identify the molecular byproducts.',
    'Properties','experimental_fraction_spectrum_observation_and_model_support',scope(['6.0'],'HPLC eluate fractions'),
    id='context-hplc-uv-fractions',evidence=[E(4,'Results A, Figure 5 discussion')],canonical=links(P['HPLC']),
    details={'molecular_elution_context':{'value':14.8,'unit':'min','meaning':'elution time, not reaction time'}})
add(None,'No resolved structural change after activation',
    'HPLC, TEM, UV absorbance and powder XRD showed no significant change after acidic reflux. This observation supports the distinction between optical activation and a gross change in measured structure or aggregation, but it does not prove unchanged atomic surface chemistry.',
    'Properties','reported_cross_technique_comparison',scope(['6.0','2.0','1.0'],'Before/after acidic reflux; physical specimen mapping unresolved'),
    id='context-activation-structure-comparison',evidence=[E(5,'Results B')],canonical=links(P['acid-activation'],'operations'))
add(None,'Low-angle XRD background',
    'The prose places a broad feature at about 2θ = 9°, attributing it to soap binder with possible oxide contribution. Figure 6 describes an arbitrary Gaussian near 10° used in the fit. This is background/model context, not proof of a crystalline oxide phase or a separate measured compound.',
    'Final structures','measured_background_with_author_fit',scope(['6.0','2.0'],'Prepared powders with mounting background'),
    id='context-xrd-background',evidence=[E(4,'Results A and Figure 6 caption')],canonical=links(P['powder-XRD']),
    details={'prose_feature':{'value':9,'unit':'degree 2theta','qualifier':'about'},'caption_fit_component':{'value':10,'unit':'degree 2theta','qualifier':'near'}})
add(None,'Silica surface chemistry context',
    'The discussion cites a hydroxylated-silica point of zero charge near pH 2 and negative charging with slow dissolution above about pH 6 when water is present. Base-induced oxide damage is offered as one possible explanation for quenching. These cited surface-chemistry statements are not measured pH titrations of each colloid.',
    'Chemical intuition','cited_surface_chemistry_and_author_hypothesis',scope([],'General hydroxylated-silica context'),
    id='context-silica-charge',evidence=[E(5,'Results B, citing reference 44'),E(7,'Reference 44')],
    details={'quantities':[{'name':'cited_point_of_zero_charge','value':2,'unit':'pH'},
                          {'name':'cited_negative_charge_and_dissolution_context','value':6,'unit':'pH','qualifier':'above_about','water_required':True}],
             'cited_work_independently_reviewed':False})
add(None,'Model comparisons and research limits',
    'The discussion compares the UV response with bulk-Si optical transitions and cites a predicted approximately 0.2 eV red shift at 1.5 nm, rather than treating that calculation as a measured colloid shift. It notes only rough consistency of decay times with predicted radiative lifetimes for 1.5–2.5 nm particles. Neither comparison determines the measured 1.0 core size or its crystal phase.',
    'Chemical intuition','cited_theoretical_comparison',scope([],'External theory compared with observations'),
    id='context-theory-comparisons',evidence=[E(5,'Results B, citing reference 42'),E(6,'Results C, citing references 18 and 20')],
    details={'quantities':[{'name':'cited_predicted_red_shift','value':0.2,'unit':'eV','qualifier':'about'},
                          {'name':'cited_prediction_particle_diameter','value':1.5,'unit':'nm'},
                          {'name':'cited_radiative_lifetime_comparison_size_range','minimum':1.5,'maximum':2.5,'unit':'nm'}],
             'cited_works_independently_reviewed':False})

# Conflicts retain source-specific locations and cannot become selectable experimental options.
CONFLICTS=[
 {'id':'pyrolysis-temperature','statements':[{'text':'860 °C', 'evidence':E(2,'Experimental A')},{'text':'865 °C','evidence':E(1,'Figure 1')}], 'scope':scope(['6.0','2.0','1.0'],'First furnace'), 'handling':'Show both source values; do not average or make an experimental temperature choice.'},
 {'id':'6p0-hplc-fwhm','statements':[{'text':'5–13 nm','evidence':E(2,'Table I')},{'text':'5.5–13 nm','evidence':E(4,'Results A')}], 'scope':scope(['6.0'],'HPLC distribution'),'handling':'Preserve both distribution bounds; not a core-size interval.'},
 {'id':'2p0-hplc-monomer','statements':[{'text':'4.2 nm','evidence':E(2,'Table I')},{'text':'about 4.5 nm shoulder','evidence':E(5,'Results A')}], 'scope':scope(['2.0'],'HPLC equivalent monomer size'),'handling':'Retain table and prose separately.'},
 {'id':'excitation-wavelength','statements':[{'text':'355 nm','evidence':E(5,'Figure 9 caption')},{'text':'350 nm for Figures 9–11','evidence':E(6,'Results B')}], 'scope':scope(['6.0','2.0','1.0'],'Steady-state PL figures'),'handling':'Source disagreement, not a condition-options menu. Figure 12 separately states 355 nm pulsed excitation.'},
 {'id':'aks41-caption-spelling','statements':[{'text':'AKS41','evidence':E(3,'Results A and Figure 3')},{'text':'ASK41','evidence':E(3,'Figure 4 caption')}], 'scope':scope(['AKS41'],'Contextual earlier-apparatus sample'),'handling':'Use AKS41 as paper context and preserve caption spelling; do not create a second sample.'},
 {'id':'ir-xrd-cross-reference','statements':[{'text':'IR paragraph refers to X-ray scattering in Figure 5','evidence':E(4,'Results A, IR paragraph')},{'text':'Actual XRD is Figure 6; Figure 5 is HPLC','evidence':E(4,'Figures 5 and 6')}], 'scope':scope(['6.0'],'Powder IR/XRD'),'handling':'Route to actual Figure 6 with a source cross-reference note.'},
 {'id':'aks41-aggregate-cross-reference','statements':[{'text':'AKS41 aggregate paragraph says as in Figure 1','evidence':E(4,'Results A, AKS41 HPLC paragraph; visually checked')},{'text':'Figure 1 is apparatus; aggregate TEM appears in Figure 3','evidence':E(1,'Figure 1')},{'text':'Aggregate TEM','evidence':E(3,'Figure 3')}], 'scope':scope(['AKS41'],'Aggregate morphology'),'handling':'Retain apparent source cross-reference error; do not depict apparatus as TEM evidence.'},
 {'id':'wash-solvent-naming','statements':[{'text':'ethylene chloride for TEM HPLC-fraction preparation','evidence':E(2,'Experimental B, TEM')},{'text':'ethylene dichloride for powder washing','evidence':E(2,'Experimental B, dry crystallites')}], 'scope':scope([],'Distinct analytical preparation procedures'),'handling':'Short TEM name is unresolved; do not silently assign it a molecular identity from the powder wash.'},
 {'id':'dilution-convention','statements':[{'text':'1:23 dilution','evidence':E(2,'Experimental A')},{'text':'300 sccm aerosol feed; added O2 1000 and He 6000 sccm','evidence':E(2,'Experimental A')},{'text':'Added dilution flows','evidence':E(1,'Figure 1')}], 'scope':scope(['6.0','2.0','1.0'],'Gas dilution'),'handling':'Preserve reported ratio. Flow arithmetic does not license replacement with an exact ratio; final/feed versus added/feed convention is not fully explicit.'}
]

REFS=[]
roles={29:'Earlier aerosol Si synthesis discussed as precedent; not a reconstructed recipe here.',30:'Gas-phase silane kinetics/modeling precedent.',31:'Gas-phase silane chemistry review precedent.',33:'Aerosol agglomeration/growth modeling rationale.',34:'Prior colloid chromatography context.',35:'Prior colloid chromatography context.',36:'Article footnote: column stability observation and interpretation.',37:'Equivalent-hard-sphere calibration reference; equation 2.23 cited, not reproduced or independently inspected.',38:'Mie optical model and crystalline-Si dielectric input references, not measured colloid raw data.',40:'Comparison with oxide-coated Si films in IR discussion.',41:'Article footnote: unwashed powder impurity observations and tentative interpretation.',44:'General silica surface-charge/dissolution context, not source-specific titration data.'}
for num in D['other_items']['references']['particularly_relevant']:
    REFS.append({'reference_number':num,'evidence':[E(7,f'Reference/Note {num}')],'reader_role':roles[num],
                 'evidence_class':'same_article_experimental_note' if num in [36,41] else 'bibliographic_context_only',
                 'cited_work_independently_reviewed':False,'training_eligible':False})

# Prove coverage at the extraction-tree leaf level, including nulls, empty lists and metadata.
leaf_coverage=[]
for pointer,val in leaves(D):
    matches=[u for u in UNITS if pointer==u['source_pointer'] or pointer.startswith(u['source_pointer']+'/')]
    assert len(matches)==1,(pointer,len(matches))
    u=matches[0]
    leaf_coverage.append({'source_pointer':pointer,'unit_id':u['id'],'disposition':u['disposition'],'value_sha256':digest(val)})
for item in ITEMS:
    for link in item['canonical_links']:resolve(R[link['record_id']],link['json_pointer'])
    for pointer in item['reader_spec_pointers']:resolve(SPEC,pointer)
assert len(ASSETS)==13 and {a['id'] for a in ASSETS}=={f'figure-{i}' for i in range(1,13)}|{'table-1'}
assert protected=={path:sha(Path(path)) for path in protected},'Read-only source/record/spec snapshot changed during reconciliation.'

evidence={'schema':'mattersyn-private-reader-evidence-1','source_id':'littau1993','doi':D['source']['doi'],
          'status':'private_source_item_reconciliation; root_reader_integration_and_render_check_pending',
          'review_scope':'supplied_main_only_si_unverified',
          'supporting_information':{'status':'not_located_or_verified','note':'No main-plus-SI completion claim; absence from the local search does not establish that no SI exists.'},
          'source_extraction_sha256':sha(HERE/'source-extraction.json'),'reader_spec_sha256':sha(HERE/'reader-integration-spec.json'),
          'source_pdf_sha256':D['source']['sha256'],'full_text_included':False,'training_eligible':False,'website_published':False,
          'scope_note':'Reconciles every item of the audited staging extraction with the current 13 private records and reader plan. It does not independently prove exhaustive original-PDF coverage or a completed source-to-view rendering.',
          'items':ITEMS,'original_assets':ASSETS,'source_conflicts':CONFLICTS,'reference_contexts':REFS,
          'record_snapshot':[{'record_id':json.loads(p.read_text(encoding='utf-8'))['record_id'],'private_path':str(p.relative_to(HERE)),'sha256':sha(p)}for p in files]}
(HERE/'reader-evidence.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
ledger={'schema':'mattersyn-private-source-coverage-1','status':'all_staged_items_accounted_for; source_to_view_validation_pending',
        'review_scope':'supplied_main_only_si_unverified',
        'supporting_information':{'status':'not_located_or_verified','note':'The ledger reconciles the reviewed main-source extraction; matching SI remains unverified.'},
        'source_extraction_sha256':sha(HERE/'source-extraction.json'),'reader_evidence_sha256':sha(HERE/'reader-evidence.json'),
        'reader_spec_sha256':sha(HERE/'reader-integration-spec.json'),'source_pdf_sha256':D['source']['sha256'],
        'basis':'JSON-pointer reconciliation of the supplied staging extraction; not a claim of canonical numeric coverage for every narrative or completion of the final website.',
        'counts':{'staging_units':len(UNITS),'staging_leaves':len(leaf_coverage),'unassigned_leaves':0,'multiply_assigned_leaves':0,
                  'reader_items':len(ITEMS),'private_records':len(R),'original_figures':12,'original_tables':1,
                  'dispositions':dict(Counter(u['disposition']for u in UNITS))},
        'staging_units':UNITS,'leaf_coverage':leaf_coverage,
        'original_assets':[{'id':a['id'],'sha256':a['sha256'],'relative_path':a['relative_path'],'disposition':a['disposition'],'render_status':a['reader_render_status']}for a in ASSETS],
        'open_work':['Root review of this reconciliation and supplemental context before import.',
                     'Root must integrate and render all original figures and Table I with correct formulation/state joins.',
                     'Reader-visible source text needs a final prose/formatting pass; staged_detail is archival curated data, not a block to dump into a page.',
                     'Molecular assets, continuous-flow scenes and chemical-intuition context need viewer integration/verification.',
                     'No SI is located/verified; no complete main-plus-SI claim.',
                     'All records/context remain excluded from training promotion and publication until the root performs the remaining scoped checks.'],
        'protected_files_unchanged':True,'protected_hashes':protected}
(HERE/'coverage-ledger.json').write_text(json.dumps(ledger,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
summary=['# Littau source-item reconciliation','',
         f"Accounted for **{len(UNITS)} staging units / {len(leaf_coverage)} leaves** with zero unassigned or multiply assigned leaves. '",
         f"Reader evidence includes **{len(ITEMS)} items**, all **12 figures + Table I**, {len(CONFLICTS)} source-conflict notes and {len(REFS)} reference-context entries.",'',
         'This proves reconciliation of the staged extraction, not a complete rendered source-to-view website. No canonical records, source PDFs, Site files or assets were edited.', '',
         'Reader-only context explicitly preserves operational consumption, mass accounting, Mie concentration calibration, pH response, stability, aggregation, spectral shape, null measurements, source conflicts, hypotheses and cited-theory limits. No context value is promoted into a training label.','',
         'AKS41 stays separate. Its nominal 13 nm introduction, individual-particle 13 nm core, population 14 nm mean and HPLC equivalent sizes have different scopes. No SAED image or crystalline phase for 1.0 is invented.','',
         'The additional p. 1227 AKS41 aggregate cross-reference to Figure 1 was visually checked; the actual TEM is Figure 3. Both this and the IR-to-XRD cross-reference error are retained.','',
         'Import `reader-evidence.json` selectively using its section, claim type, sample scope, evidence and links. Do not dump archival `staged_detail` verbatim into the reader. `coverage-ledger.json` retains every source pointer and hash so later changes are detectable.']
(HERE/'coverage-ledger.md').write_text('\n'.join(summary).replace("leaves. '\n","leaves.\n")+'\n',encoding='utf-8')
print(json.dumps(ledger['counts'],indent=2))
