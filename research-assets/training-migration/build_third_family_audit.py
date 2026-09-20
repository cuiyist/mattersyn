import hashlib
import json
from pathlib import Path

BASE = Path('[local path redacted]')
OUT = BASE / 'research-assets/training-migration/third-family-audit.json'
MAIN = BASE / 'downloaded_papers/10.1021_ja075604i.pdf'
SI = BASE / 'downloaded_papers/10.1021_ja075604i_si_1.pdf'

def q(value, unit, source, *, approximate=False, status='reported', note=None):
    d={'value':value,'unit':unit,'status':status,'approximate':approximate,'source_locator_id':source}
    if note: d['note']=note
    return d

def missing(unit, source='main.preparation'):
    return {'value':None,'unit':unit,'status':'missing','missing_reason':'not_reported','source_locator_id':source}

def calc(value,unit,expression,inputs):
    d=q(value,unit,'main.preparation',status='calculated')
    d.update(expression=expression,input_quantity_ids=inputs)
    return d

locators={
 'main.preparation':{'document_id':'fu2007.main','pdf_page':2,'printed_page':16030,'section':'Experimental Section / Sample Preparation, first paragraph'},
 'main.characterization':{'document_id':'fu2007.main','pdf_page':2,'printed_page':16030,'section':'Experimental Section / Characterization'},
 'main.structure':{'document_id':'fu2007.main','pdf_page':2,'printed_page':16030,'section':'Results and Discussion / Figures 1 and 2'},
 'main.surface':{'document_id':'fu2007.main','pdf_pages':[2,3],'printed_pages':[16030,16031],'section':'Figure 3 and FTIR discussion'},
 'main.optical':{'document_id':'fu2007.main','pdf_page':3,'printed_page':16031,'section':'Figure 4 and PL/PLE/QY/photostability discussion'},
 'main.bandgap':{'document_id':'fu2007.main','pdf_pages':[3,4],'printed_pages':[16031,16032],'section':'Figure 5 and absorption onset analysis'},
 'main.mechanism':{'document_id':'fu2007.main','pdf_pages':[4,5],'printed_pages':[16032,16033],'section':'Controls and proposed interface-state blue-emission mechanism'},
 'main.SI_notice':{'document_id':'fu2007.main','pdf_page':5,'printed_page':16033,'section':'Supporting Information Available'},
 'si.identity':{'document_id':'fu2007.si','pdf_page':1,'printed_page':'S1','section':'Title and authors'},
 'si.low_temperature':{'document_id':'fu2007.si','pdf_page':2,'printed_page':'S2','section':'Part 1 / Figure S1'},
 'si.qy':{'document_id':'fu2007.si','pdf_page':3,'printed_page':'S3','section':'Part 2 / Figure S2 / quantum-yield measurement'},
 'si.S4':{'document_id':'fu2007.si','pdf_page':4,'printed_page':'S4','section':'Part 3 / Figure S3'},
}

quantities={
 'stock.DEA.mass':q(26.3,'mg','main.preparation'),
 'stock.DEA.water_volume':q(50,'mL','main.preparation',note='Distilled water charge; final solution volume not independently measured'),
 'stock.DEA.concentration':q(5.0,'mmol/L','main.preparation',note='Reported stock concentration, before mixing with zinc stock'),
 'stock.zinc_nitrate_hexahydrate.mass':q(37.2,'mg','main.preparation'),
 'stock.zinc.water_volume':q(50,'mL','main.preparation',note='Distilled water charge; final solution volume not independently measured'),
 'stock.zinc.concentration':q(2.5,'mmol/L','main.preparation',note='Reported zinc nitrate stock concentration, before mixing'),
 'OA.amount':q(0.35,'mmol','main.preparation'),
 'OA.mass':missing('mg'),
 'OA.volume':missing('mL'),
 'reaction.room_temperature.duration':q(30,'min','main.preparation'),
 'reaction.room_temperature.numeric_temperature':missing('degC'),
 'reaction.heating.temperature':q(80,'degC','main.preparation'),
 'reaction.heating.duration':q(2.0,'h','main.preparation'),
 'reaction.heating.ramp':missing('degC/min'),
 'reaction.stirring.speed':missing('rpm'),
 'reaction.pressure':missing('Pa'),
 'reaction.final_volume':missing('mL'),
 'workup.filter.pore':missing('um'),
 'workup.centrifuge.speed':missing('rpm'),
 'workup.centrifuge.force':missing('g_relative'),
 'workup.centrifuge.duration':missing('min'),
 'workup.1_butanol.volume':missing('mL'),
 'workup.1_propanol.volume':missing('mL'),
 'workup.ethanol.volume':missing('mL'),
 'workup.final_water.volume':missing('mL'),
 'workup.product.mass':missing('mg'),
 'workup.product.yield':missing('percent'),
 'product.S1.diameter':q(3.8,'nm','main.structure',approximate=True,note='Average/statistical diameter; main p16032 reiterates mean diameter 3.8 nm'),
 'product.S1.diameter.plus_minus':q(0.4,'nm','main.structure',note='Reported as 3.8 +/- 0.4 nm; definition of +/- term is not supplied, so do not silently label standard deviation or standard error'),
 'product.S1.PL_peak':q(440,'nm','main.optical',approximate=True),
 'product.S1.PL_energy':q(2.82,'eV','main.optical'),
 'product.S1.optimal_excitation':q(350,'nm','main.optical'),
 'product.S1.optimal_excitation_energy':q(3.54,'eV','main.optical'),
 'product.S1.relative_QY':q(76,'percent','main.optical',approximate=True,note='Relative comparison to quinine sulfate; SI Part 2 supplies procedure'),
 'product.S1.optical_absorption_onset':q(3.94,'eV','main.bandgap',note='Author-extracted optical onset from extrapolation in Figure 5b, not measured electronic quasiparticle gap'),
 'product.S1.theoretical_gap':q(3.92,'eV','main.bandgap',status='author_model',note='Quantum-confinement calculation using TEM radius; not another measured value'),
 'product.S1.PL_initial_drop':q(9.4,'percent','main.optical',note='Decrease of 440-nm emission during first 6 h of the specified irradiation test'),
 'product.S1.PL_initial_drop_time':q(6,'h','main.optical'),
 'measurement.photostability.excitation':q(350,'nm','main.characterization'),
 'measurement.photostability.power_density':q(130,'uW/cm2','main.characterization'),
 'measurement.photostability.monitoring_wavelength':q(440,'nm','main.characterization'),
 'measurement.PL.excitation':q(350,'nm','main.characterization'),
 'measurement.PLE.detection':q(432,'nm','main.characterization'),
 'measurement.QY.reference_value':q(0.55,'dimensionless','si.qy',status='adopted_reference_value'),
 'measurement.QY.reference_acid':q(0.5,'mol/L','si.qy',note='H2SO4 solvent for quinine sulfate calibration only'),
 'measurement.QY.concentration_count':q(5,'count','si.qy',note='Five concentrations of each sample/reference; not five synthesis batches'),
 'measurement.QY.absorbance_limit':{'value':0.1,'unit':'dimensionless','status':'reported_upper_bound','operator':'less_than','source_locator_id':'si.qy','wavelength_nm':350},
 'measurement.QY.path_length':q(1.00,'cm','si.qy'),
 'measurement.QY.excitation_slit':q(2.5,'nm','si.qy'),
 'measurement.QY.emission_slit':q(2.5,'nm','si.qy'),
 'measurement.QY.sample_refractive_index':q(1.33,'dimensionless','si.qy',status='adopted_value'),
 'measurement.QY.reference_refractive_index':q(1.33,'dimensionless','si.qy',status='adopted_value'),
}
quantities['stock.DEA.nominal_amount']=calc(0.250,'mmol','5.0 mmol/L * 0.050 L',['stock.DEA.concentration','stock.DEA.water_volume'])
quantities['stock.zinc.nominal_amount']=calc(0.125,'mmol','2.5 mmol/L * 0.050 L',['stock.zinc.concentration','stock.zinc.water_volume'])
quantities['reaction.nominal_DEA_to_Zn']=calc(2.0,'dimensionless','0.250 / 0.125',['stock.DEA.nominal_amount','stock.zinc.nominal_amount'])
quantities['reaction.nominal_OA_to_Zn']=calc(2.8,'dimensionless','0.35 / 0.125',['OA.amount','stock.zinc.nominal_amount'])
quantities['reaction.nominal_water_sum']=calc(100,'mL','50 + 50',['stock.DEA.water_volume','stock.zinc.water_volume'])
quantities['reaction.nominal_water_sum']['note']='Water-charge arithmetic only; not measured final volume including OA, dissolved solutes, or volume changes.'

chemicals=[
 {'id':'diethanolamine','name':'diethanolamine','abbreviation':'DEA','formula':'C4H11NO2','role':'base/complexing reagent and proposed surface-associated species','stage':'stock and synthesis'},
 {'id':'zinc_nitrate_hexahydrate','name':'zinc nitrate hexahydrate','formula':'Zn(NO3)2.6H2O','normalized_formula':'H12N2O12Zn','role':'zinc precursor','stage':'stock and synthesis'},
 {'id':'oleic_acid','name':'oleic acid','abbreviation':'OA','formula':'C18H34O2','role':'surface-modifying reagent','stage':'synthesis'},
 {'id':'water','name':'water','formula':'H2O','grade':'distilled for stock preparation','role':'synthesis and final dispersion medium','stage':'stock, synthesis and final redispersion'},
 {'id':'1_butanol','name':'1-butanol','formula':'C4H10O','role':'purification/redispersion solvent','stage':'workup'},
 {'id':'1_propanol','name':'1-propanol','formula':'C3H8O','role':'purification/redispersion solvent','stage':'workup'},
 {'id':'ethanol','name':'ethanol','formula':'C2H6O','role':'purification/redispersion solvent','stage':'workup'},
]
for c in chemicals:
    c.update(identity_status='normalized_named_identity',supplier=None,numeric_purity=None,source_locator_id='main.preparation')

state_names={
 'DEA_stock':'5.0 mM DEA aqueous stock', 'zinc_stock':'2.5 mM zinc nitrate aqueous stock',
 'mixed_reagents':'Both aqueous stocks plus 0.35 mmol OA', 'mixed_room_temperature':'Mixture stirred 30 min at room temperature',
 'as_prepared_dispersion':'ZnO dispersion after 80 C treatment', 'filtered_dispersion':'Filtered as-prepared dispersion',
 'recovered_product':'Product recovered by centrifugation', 'purified_product':'Product sequentially redispersed with the three named alcohols',
 'final_QDs':'QDs obtained by final centrifugation', 'aqueous_S1':'Final S1 dispersion in water',
}
states=[{'id':'fu2007.S1.stream.'+k,'record_type':'procedural_material_state','label':v,'physical_batch_id':None,'author_sample_label':'S1','identity_note':'Procedural stream placeholder; author label S1 identifies the formulation/sample condition, not a known unique replicated batch.'} for k,v in state_names.items()]

def op(id,action,inputs,outputs,quantity_ids,after=None,note=None,conditions=None):
    return {'id':'fu2007.S1.operation.'+id,'action':action,'inputs':inputs,'outputs':outputs,'quantity_ids':quantity_ids,'depends_on':['fu2007.S1.operation.'+x for x in (after or [])],'source_locator_id':'main.preparation','evidence_status':'reported','note':note,'conditions':conditions or {}}

operations=[
 op('DEA_stock','dissolve',['diethanolamine','water'],['DEA_stock'],['stock.DEA.mass','stock.DEA.water_volume','stock.DEA.concentration'],note='Reported charge and stock concentration; stock preparation temperature/duration unreported.'),
 op('zinc_stock','dissolve',['zinc_nitrate_hexahydrate','water'],['zinc_stock'],['stock.zinc_nitrate_hexahydrate.mass','stock.zinc.water_volume','stock.zinc.concentration']),
 op('combine','combine_in_reactor',['DEA_stock','zinc_stock','oleic_acid'],['mixed_reagents'],['OA.amount'],['DEA_stock','zinc_stock'],note='The paper says both above solutions and OA were added together. No separate measured aliquot is specified; use the stated prepared stocks without inventing a different transferred fraction.',conditions={'reactor_material':None,'reactor_capacity':None,'addition_order_within_combination':None,'atmosphere':None}),
 op('stir_RT','stir',['mixed_reagents'],['mixed_room_temperature'],['reaction.room_temperature.duration','reaction.room_temperature.numeric_temperature'],['combine'],conditions={'temperature_text':'room temperature','stirring_speed':None}),
 op('heat','increase_temperature_and_continue_stirring',['mixed_room_temperature'],['as_prepared_dispersion'],['reaction.heating.temperature','reaction.heating.duration','reaction.heating.ramp'],['stir_RT'],note='Source wording links increased temperature to 80 C and another 2.0 h of continuous stirring. Ramp profile and whether any ramp time enters the stated duration are not resolved.',conditions={'stirring':'continuous','pressure':None,'atmosphere':None}),
 op('filter','filter',['as_prepared_dispersion'],['filtered_dispersion'],['workup.filter.pore'],['heat'],note='Subsequent step acts on the dispersion; membrane material and explicit retained-fraction instruction are not supplied.'),
 op('centrifuge_initial','centrifuge_and_recover_product',['filtered_dispersion'],['recovered_product'],['workup.centrifuge.speed','workup.centrifuge.force','workup.centrifuge.duration'],['filter'],note='Product is recovered and redispersed. Pellet/supernatant terminology is not explicitly given.'),
 op('sequential_alcohol_redispersion','sequentially_redisperse_for_purification',['recovered_product','1_butanol','1_propanol','ethanol'],['purified_product'],['workup.1_butanol.volume','workup.1_propanol.volume','workup.ethanol.volume'],['centrifuge_initial'],note='Explicit solvent order: 1-butanol, then 1-propanol, then ethanol. Do not invent intermediate centrifugation counts, solvent volumes, or wash repetition.',conditions={'ordered_solvents':['1_butanol','1_propanol','ethanol'],'purpose':'remove unreacted molecules','intermediate_separation_details':None}),
 op('centrifuge_final','centrifuge_and_obtain_QDs',['purified_product'],['final_QDs'],['workup.centrifuge.speed','workup.centrifuge.force','workup.centrifuge.duration'],['sequential_alcohol_redispersion']),
 op('redisperse_water','disperse',['final_QDs','water'],['aqueous_S1'],['workup.final_water.volume'],['centrifuge_final'],conditions={'purpose':'further characterization'}),
]
for operation in operations:
    for field in ['inputs','outputs']:
        operation[field] = ['fu2007.S1.stream.'+value if value in state_names else value for value in operation[field]]

record={
 'id':'fu2007.zno.S1', 'record_type':'literature_sample_condition_recipe', 'chemistry_family':'metal_oxide', 'material':'ZnO',
 'method':'aqueous solution synthesis with diethanolamine and oleic acid', 'author_sample_label':'S1',
 'physical_experiment_id':None, 'physical_batch_id':None, 'physical_batch_count':None,
 'source_locator_id':'main.preparation',
 'intended_target':{'composition':'ZnO','description':'water-stable colloidal quantum dots with strong blue emission','prespecified_diameter_nm':None,'prespecified_space_group':None,'prespecified_atomic_coordinates':None,'note':'Do not relabel the observed 3.8 nm and 76% as experimentally prespecified optimization targets.'},
 'observed_product':{'composition':'ZnO','phase':'wurtzite','phase_evidence':'XRD Figure 1 explicitly labels S1; matched to JCPDS 89-1397','morphology':'uniform and dispersed quantum dots, as described by authors','size_quantity':'product.S1.diameter','size_spread_quantity':'product.S1.diameter.plus_minus','final_medium':'water','surface':'FTIR-supported OA/DEA-associated surface interpretation; exact coverage and geometry unresolved'},
 'operation_ids':[o['id'] for o in operations],
 'product_links':[
  {'observation_id':'fu2007.observation.S1.XRD','link_type':'explicit_author_sample_label','evidence':'Sample Preparation defines S1; Figure 1 and text identify S1 with OA','source_locator_id':'main.structure'},
  {'observation_id':'fu2007.observation.S1.HRTEM','link_type':'explicit_author_sample_label','evidence':'Figure 2(a) and text identify S1 with OA and about 3.8 +/- 0.4 nm','source_locator_id':'main.structure'},
  {'observation_id':'fu2007.observation.S1.PL_QY','link_type':'explicit_author_sample_label','evidence':'Figure 4 and text assign blue emission and about 76% QY to S1; main directs to SI Part 2','source_locator_id':'main.optical'},
  {'observation_id':'fu2007.observation.S1.FTIR','link_type':'explicit_author_sample_label','evidence':'Figure 3 top spectrum S1','source_locator_id':'main.surface'},
 ],
 'linkage_limit':'Shared S1 condition is verified. The article does not identify unique batch/replicate numbers or prove every instrument measured the same physical aliquot.',
 'eligibility':{'eligible_tasks':['source_to_structured_recipe','composition_phase_size_descriptor_to_partial_recipe','condition_linked_product_property_prediction','retrieval_of_evidence_linked_synthesis_candidates'],'ineligible_tasks':['exact_CIF_to_recipe_supervision','fully_specified_executable_SOP_generation_without_completion','independent_batch_count_estimation'],'requires_missingness_masks':True,'qualifier':'Main reagent charges and principal thermal holds are reported; purification settings and other operational details are incomplete.'},
}

audit={
 'schema_version':'seed-audit/1.0','record_type':'additional_non_CdSe_colloidal_seed','created_date':'2026-09-16',
 'selected_family':'metal_oxide','selected_material':'ZnO','canonical_records':[record],
 'source':{'id':'fu2007','title':'Stable Aqueous Dispersion of ZnO Quantum Dots with Strong Blue Emission via Simple Solution Route','authors':['Ying-Song Fu','Xi-Wen Du','Sergei A. Kulinich','Jian-Sheng Qiu','Wen-Jing Qin','Rui Li','Jing Sun','Jim Liu'],'journal':'Journal of the American Chemical Society','year':2007,'volume':129,'issue':51,'pages':'16029-16033','doi':'10.1021/ja075604i','doi_url':'https://doi.org/10.1021/ja075604i','main':{'id':'fu2007.main','local_path':str(MAIN).replace('\\','/'),'page_count':5,'sha256':hashlib.sha256(MAIN.read_bytes()).hexdigest()},'supporting_information':{'id':'fu2007.si','local_path':str(SI).replace('\\','/'),'page_count':4,'sha256':hashlib.sha256(SI.read_bytes()).hexdigest(),'matching_status':'content_verified','identity_evidence':'SI title matches main article and author group; main explicitly references SI Parts 1/2/3 and corresponding contents match. Filename alone was not treated as identity proof.'}},
 'inspection':{'main_text':'all five pages extracted and read','SI_text':'all four pages extracted and read','visually_inspected':[{'file':'zno-fu2007-main-2.png','source_pages':'main PDF 2 / p16030','checked':['sample S1 charges and stock concentrations','operation text','XRD attribution','HRTEM S1 size and +/- notation','130 uW/cm2 photostability condition']},{'file':'zno-fu2007-main-3.png','source_pages':'main PDF 3 / p16031','checked':['PL/PLE wavelengths','76% relative QY','9.4% change in first 6 h','Figure 4 axes and source scope']},{'file':'zno-fu2007-si-3.png','source_pages':'SI PDF 3 / S3','checked':['quantum-yield calibration','quinine sulfate reference','five concentration series','optical path and slit widths','relative-QY equation']}],'render_directory':str(OUT.parent).replace('\\','/'),'render_note':'Poppler emitted font warnings but inspected scientific text, symbols and figures rendered legibly.'},
 'source_locators':locators,'chemical_entities':chemicals,'quantities':quantities,'material_states':states,'operations':operations,
 'graph_notes':['DEA and zinc stock preparations are independent and both precede their combination with OA.','The stock concentrations are 5.0 mM DEA and 2.5 mM zinc nitrate; these are not final reaction concentrations after mixing.','The total aqueous charge is nominally 100 mL, not a measured final mixture volume.','No high-temperature hot injection, TOPO, TOP, oleylamine or octadecene appears in this S1 recipe.','Nitrogen/argon atmosphere, reflux, sealed pressure vessel and a numerical room temperature must not be invented.','The purification sequence has unresolved intermediate separation mechanics; preserve the combined sequential-redispersion action rather than fabricate centrifugation steps.'],
 'observations':[
  {'id':'fu2007.observation.S1.XRD','type':'experiment','author_sample_label':'S1','source_locator_id':'main.structure','finding':'wurtzite ZnO, matched to JCPDS Card 89-1397','specimen_preparation':'freeze-dried product for XRD','instrument':'Rigaku D/max 2500v/pc','note':'Broad feature near 25 degrees is assigned to glass substrate, not an extra ZnO phase. No sample-refined CIF is supplied.'},
  {'id':'fu2007.observation.S1.HRTEM','type':'experiment','author_sample_label':'S1','source_locator_id':'main.structure','figure':'2(a)','diameter_quantity':'product.S1.diameter','spread_quantity':'product.S1.diameter.plus_minus','instrument':'FEI Tecnai G2 F20, 200 kV','sample_preparation':'dilute product dropped onto carbon-coated copper grids','scale_bar_nm':10,'numeric_distribution_type':None},
  {'id':'fu2007.observation.S1.PL_QY','type':'experiment','author_sample_label':'S1','source_locator_id':'main.optical','figure':'4(a)','quantity_ids':['product.S1.PL_peak','product.S1.PL_energy','product.S1.optimal_excitation','product.S1.relative_QY'],'medium':'water','temperature':'room temperature','PL_excitation_nm':350,'PLE_detection_nm':432,'QY_detail_source':'si.qy','QY_standard':'quinine sulfate in 0.5 M sulfuric acid','QY_reference_phi':0.55,'QY_method':'integrated PL-versus-absorbance slopes, five concentrations of each, absorbance <0.1 at 350 nm, refractive-index correction','sample_refractive_index':1.33,'standard_refractive_index':1.33,'QY_is_relative':True,'not_isolated_synthesis_yield':True},
  {'id':'fu2007.observation.S1.photostability','type':'experiment','author_sample_label':'S1','source_locator_id':'main.optical','figure':'4(c)','quantity_ids':['product.S1.PL_initial_drop','product.S1.PL_initial_drop_time','measurement.photostability.excitation','measurement.photostability.power_density','measurement.photostability.monitoring_wavelength'],'finding':'PL intensity falls by 9.4% during first 6 h then remains almost unchanged in the plotted test','note':'This is illumination stability, not a quantitative dark-storage shelf life.'},
  {'id':'fu2007.observation.S1.FTIR','type':'experiment_with_author_surface_interpretation','author_sample_label':'S1','source_locator_id':'main.surface','figure':'3, top spectrum','sample_state':'purified and dried nanoparticles','instrument':'ATR FTIR Nicolet 470','finding':'Authors interpret spectra as evidence of surface-bound OA and surface-associated DEA/hydroxyl groups','resolved_binding_geometry':None,'ligand_coverage':None},
  {'id':'fu2007.observation.S1.absorption_onset','type':'experiment_derived','author_sample_label':'S1','source_locator_id':'main.bandgap','figure':'5','measured_onset_quantity':'product.S1.optical_absorption_onset','separate_theoretical_quantity':'product.S1.theoretical_gap','note':'Do not mix modeled 3.92 eV with measured/extrapolated 3.94 eV.'},
  {'id':'fu2007.interpretation.blue_emission','type':'author_mechanistic_interpretation','source_locator_id':'main.mechanism','finding':'Blue emission attributed to interface states related to ZnO/OA complexes; supporting controls discussed','not_measured_atomistic_structure':True,'note':'Do not label 440-nm emission as ordinary ZnO band-edge emission or a universally established mechanism.'},
 ],
 'calibration_not_synthesis_inputs':['quinine sulfate','0.5 M sulfuric acid'],
 'characterization_not_base_workup':'Freeze drying is stated for XRD specimen preparation; it is not a required final step for the aqueous S1 synthesis record.',
 'missing_fields':['supplier and numerical purity of reagents','OA mass/volume or formulation beyond 0.35 mmol','measured final stock/mixture volumes','stock dissolution temperature and time','reactor capacity/material/geometry','atmosphere and pressure','numeric room temperature','stirring rate','heating ramp and ramp/hold timing boundary','filter type and pore size','centrifugation speed/force/time','individual alcohol volumes and detailed intermediate solvent exchange/separation mechanics','final water volume and product concentration','isolated mass or synthesis yield','replicate or unique batch count','definition of +/-0.4 nm size spread','experimentally refined atomic coordinates/CIF'],
 'other_sample_boundaries':[
  {'label':'S2','difference':'OA omitted','source_locator_id':'main.preparation','do_not_merge':'5.0 +/- 0.5 nm and lack of aqueous luminescence belong to S2, not S1. Dried S2 has different PL and is another measurement state.'},
  {'label':'S3','difference':'DEA replaced by ammonia','source_locator_id':'main.preparation','do_not_merge':'Ammonia amount/formulation not independently quantified; not a required S1 reagent.'},
  {'label':'S4','difference':'4.0 mM aqueous zinc nitrate stock','source_locator_id':'main.preparation','do_not_merge':'Approximately 4.2-nm size and SI Figure S3 belong to S4. Do not overwrite S1 zinc stock concentration.'},
  {'label':'SI Figure S1','difference':'low-temperature 60 C observation about 20 min after reaction starts, approximately 3 nm','source_locator_id':'si.low_temperature','do_not_merge':'Main associates early hydrolysis discussion with S2/no OA; not S1 final 80 C/2 h size or a fully specified standalone new recipe.'},
  {'label':'S2+OA time-series and S1+HCl perturbation','difference':'mechanism controls','source_locator_id':'main.mechanism','do_not_merge':'20 mL S2 + 0.35 mmol OA, or HCl treatment, are distinct control conditions; do not insert into S1 protocol.'},
 ],
 'structure_policy':{'experimentally_supported_phase':'wurtzite','product_CIF':None,'exact_atomistic_structure':None,'reference_CIF_if_later_added':'must remain external reference, not measured product coordinates','phase_size_descriptor_pair_eligible':True,'exact_CIF_recipe_pair_eligible':False},
 'grouping':{'source_group_id':'doi:10.1021/ja075604i','condition_group_id':'fu2007.S1','related_variants_same_split':['S2','S3','S4','SI early-growth observation','mechanism controls'],'curated_recipe_records_in_this_audit':1,'asserted_independent_experiment_count':None,'counting_note':'One source-defined S1 recipe-condition record; no invented number of laboratory runs.'},
 'verification':{'main_SI_identity_verified':True,'key_pages_visually_verified':True,'site_files_modified':False,'numerical_source_conflicts_found':False,'normalization_note':'Formula normalization and molar ratios are marked separately; nominal amount calculations use reported stock concentrations and water charges, not an external density assumption.'},
}

OUT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ids={o['id'] for o in operations}
material_ids={s['id'] for s in states}|{c['id'] for c in chemicals}
for o in operations:
    assert set(o['quantity_ids']) <= set(quantities)
    assert set(o['depends_on']) <= ids
    assert o['source_locator_id'] in locators
    assert set(o['inputs']+o['outputs']) <= material_ids
assert len(ids)==len(operations)
assert record['physical_batch_id'] is None
json.loads(OUT.read_text(encoding='utf-8'))
print(json.dumps({'path':str(OUT),'record_count':1,'operations':len(operations),'quantities':len(quantities),'bytes':OUT.stat().st_size}))
