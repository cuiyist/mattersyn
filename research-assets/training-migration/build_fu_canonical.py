import sys
sys.dont_write_bytecode = True
import json
from pathlib import Path

BASE = Path('[local path redacted]')
sys.path.insert(0,str(BASE/'recipe-atlas/scripts'))
from record_helpers import ev,fact,qty,source,record,material,operation,product,state,measurement

AUDIT = json.loads((BASE/'research-assets/training-migration/third-family-audit.json').read_text(encoding='utf-8'))
OUT = BASE/'research-assets/training-migration/canonical/fu-2007-zno-s1.json'
SOURCE_ID = 'fu2007'

def evidence(locator_id):
    loc=AUDIT['source_locators'][locator_id]
    pages=loc.get('printed_pages',[loc.get('printed_page')])
    document='Supporting Information' if loc['document_id'].endswith('.si') else 'Main article'
    return ev(SOURCE_ID,document+', p. '+', '.join(map(str,pages))+', '+loc['section'])

def quantity(key,*,qualifier=None,basis=None):
    old=AUDIT['quantities'][key]
    statuses={'missing':'not_reported','reported':'reported','calculated':'calculated','author_model':'author_derived','adopted_reference_value':'reported','adopted_value':'reported','reported_upper_bound':'reported'}
    derivation=old.get('expression')
    if derivation:
        derivation+='; inputs: '+', '.join(old.get('input_quantity_ids',[]))
    qual=qualifier or old.get('note','')
    if old.get('operator')=='less_than':qual='Less than this limit; '+qual
    return qty(old['value'],old['unit'],evidence(old['source_locator_id']),status=statuses[old['status']],approximate=old.get('approximate',False),qualifier=qual,basis=basis or '',raw_text='',derivation=derivation)

prep=evidence('main.preparation')
struct=evidence('main.structure')
optical=evidence('main.optical')
qy=evidence('si.qy')
src=source(SOURCE_ID,'10.1021/ja075604i',AUDIT['source']['title'],'; '.join(AUDIT['source']['authors']),2007,si='Matching four-page SI verified by title/authors and corresponding main-text references; all SI text read and QY page visually inspected.')
src['main_status']='All five main-article pages read; synthesis and key structural/optical pages visually inspected.'
r=record('fu-2007-zno-s1','ZnO quantum dots in water: Fu et al. (2007), sample S1','ZnO','metal_oxide','Aqueous solution synthesis with diethanolamine and oleic acid',src,'Main article p. 16030, Experimental Section / Sample Preparation')
r['lineage']['recipe_family']='fu2007-zno-aqueous-dea-oa'
r['intended_target']['composition']=fact('ZnO',prep)
r['intended_target']['phase']=fact(evidence=prep,note='A prespecified target phase is not given in the synthesis description; wurtzite is an observed product assignment.')
r['intended_target']['size']=qty(unit='nm',evidence=prep,qualifier='No prespecified numerical size target; 3.8 nm is the measured outcome.')
r['intended_target']['morphology']=fact('quantum dots',ev(SOURCE_ID,'Main article p. 16029, title, abstract and final introduction paragraph'),note='Authors aim for water-stable ZnO quantum dots with strong blue emission; no prespecified shape dimensions are provided.')

chemical_roles={
 'diethanolamine':('base_and_complexing_reagent','synthesis'),
 'zinc_nitrate_hexahydrate':('metal_precursor','synthesis'),
 'oleic_acid':('surface_modifying_reagent','synthesis'),
 'water':('solvent','synthesis'),
 '1_butanol':('purification_solvent','workup'),
 '1_propanol':('purification_solvent','workup'),
 'ethanol':('purification_solvent','workup'),
}
for chem in AUDIT['chemical_entities']:
    role,stage_name=chemical_roles[chem['id']]
    notes=['Supplier and numerical purity not reported in the inspected recipe.','Formula is normalized from the named chemical identity; no PubChem CID or SMILES has been independently verified here.']
    amounts={}
    if chem['id']=='oleic_acid':
        amounts={'amount':quantity('OA.amount',basis='Charge added together with both aqueous stocks'),'mass':quantity('OA.mass'),'volume':quantity('OA.volume')}
    if chem['id']=='water':notes+=['Distilled water is reported for preparation of the two stocks. Water is also the final dispersion medium; its final volume is unspecified.']
    if chem['id']=='diethanolamine':notes+=['26.3 mg is charged once to its stock; see stock and preparation operation. Surface association is an author interpretation from characterization.']
    if chem['id']=='zinc_nitrate_hexahydrate':notes+=['The zinc reagent is the hexahydrate, not anhydrous Zn(NO3)2. 37.2 mg is charged once to its stock.']
    r['materials'].append(material(chem['id'],chem['name'],chem['formula'],role,stage_name,prep,quantities=amounts,notes=notes))

r['stocks']=[
 {'id':'dea-stock','name':'DEA aqueous starting stock','components':[{'material_id':'diethanolamine','quantities':{'mass':quantity('stock.DEA.mass'),'nominal_amount':quantity('stock.DEA.nominal_amount',basis='Calculated from reported 5.0 mM and 50 mL water charge')}},{'material_id':'water','quantities':{'volume':quantity('stock.DEA.water_volume')}}],'concentrations':{'dea':quantity('stock.DEA.concentration',basis='Starting stock, before mixing')} ,'preparation_operation_ids':['prepare-dea-stock'],'scope':'The stated prepared solution is combined with the zinc stock and OA. Measured final stock volume is not independently given. Stock charges repeated in operation parameters are the same charges, not additional inputs.','evidence':prep},
 {'id':'zinc-stock','name':'Zinc nitrate aqueous starting stock','components':[{'material_id':'zinc_nitrate_hexahydrate','quantities':{'mass':quantity('stock.zinc_nitrate_hexahydrate.mass'),'nominal_zinc_amount':quantity('stock.zinc.nominal_amount',basis='Calculated from reported 2.5 mM and 50 mL water charge')}},{'material_id':'water','quantities':{'volume':quantity('stock.zinc.water_volume')}}],'concentrations':{'zinc_nitrate':quantity('stock.zinc.concentration',basis='Starting stock, before mixing')},'preparation_operation_ids':['prepare-zinc-stock'],'scope':'The stated prepared solution is combined with the DEA stock and OA. Starting stock molarity is not post-mixing reaction molarity.','evidence':prep},
]

r['material_states']=[
 state('combined-mixture','Both aqueous stocks combined with OA',['dea-stock','zinc-stock','oleic_acid']),
 state('stirred-mixture','Mixture stirred at room temperature',['combined-mixture']),
 state('as-prepared-dispersion','ZnO dispersion after the 80 C treatment',['stirred-mixture'],kind='product'),
 state('filtered-dispersion','Filtered as-prepared dispersion',['as-prepared-dispersion'],kind='fraction'),
 state('recovered-product','Product recovered by centrifugation',['filtered-dispersion'],kind='fraction'),
 state('alcohol-purified-product','Product sequentially redispersed in alcohols',['recovered-product','1_butanol','1_propanol','ethanol'],kind='fraction'),
 state('final-qd-product','QDs obtained by final centrifugation',['alcohol-purified-product'],kind='product'),
 state('aqueous-s1','S1 product dispersed in water',['final-qd-product','water'],kind='product'),
]

def unknown_environment(note='Atmosphere, pressure and reactor construction are not reported.'):
    return fact(evidence=prep,note=note)

r['operations']=[
 operation('prepare-dea-stock','dissolve','Prepare DEA aqueous stock',prep,['diethanolamine','water'],['dea-stock'],stage='precursor_preparation',parameters={'dea_mass':quantity('stock.DEA.mass'),'water_volume':quantity('stock.DEA.water_volume'),'stock_concentration':quantity('stock.DEA.concentration'),'preparation_temperature':qty(unit='degC',evidence=prep),'preparation_duration':qty(unit='min',evidence=prep)},environment=unknown_environment('Stock dissolution temperature, duration and atmosphere are not specified.'),description='Dissolve 26.3 mg DEA in 50 mL distilled water; authors state 5.0 mM.'),
 operation('prepare-zinc-stock','dissolve','Prepare zinc nitrate aqueous stock',prep,['zinc_nitrate_hexahydrate','water'],['zinc-stock'],stage='precursor_preparation',parameters={'precursor_mass':quantity('stock.zinc_nitrate_hexahydrate.mass'),'water_volume':quantity('stock.zinc.water_volume'),'stock_concentration':quantity('stock.zinc.concentration'),'preparation_temperature':qty(unit='degC',evidence=prep),'preparation_duration':qty(unit='min',evidence=prep)},environment=unknown_environment('Stock dissolution temperature, duration and atmosphere are not specified.'),description='Dissolve 37.2 mg zinc nitrate hexahydrate in 50 mL distilled water; authors state 2.5 mM.'),
 operation('combine-stocks-oa','combine','Combine both stocks and OA',prep,['dea-stock','zinc-stock','oleic_acid'],['combined-mixture'],depends=['prepare-dea-stock','prepare-zinc-stock'],parameters={'oleic_acid_amount':quantity('OA.amount'),'nominal_water_charge_sum':quantity('reaction.nominal_water_sum'),'measured_final_volume':quantity('reaction.final_volume'),'nominal_DEA_to_Zn_ratio':quantity('reaction.nominal_DEA_to_Zn'),'nominal_OA_to_Zn_ratio':quantity('reaction.nominal_OA_to_Zn')},environment=unknown_environment(),description='The two above solutions and 0.35 mmol OA are added to a reactor together. Order within this combination, addition rates and any separate aliquot are not specified. The nominal 100 mL water-charge sum is not a measured final volume.'),
 operation('stir-room-temperature','stir','Stir at room temperature for 30 min',prep,['combined-mixture'],['stirred-mixture'],depends=['combine-stocks-oa'],parameters={'duration':quantity('reaction.room_temperature.duration'),'temperature':quantity('reaction.room_temperature.numeric_temperature'),'stirring_speed':quantity('reaction.stirring.speed')},environment=fact('room temperature',prep,note='No numerical room-temperature value, atmosphere or pressure reported.'),description='Stir the combined mixture at room temperature for 30 min; no stirring speed is supplied.'),
 operation('heat-stir-80c','heat_and_stir','Increase to 80 C and continue stirring for 2.0 h',prep,['stirred-mixture'],['as-prepared-dispersion'],depends=['stir-room-temperature'],parameters={'temperature':quantity('reaction.heating.temperature'),'duration':quantity('reaction.heating.duration'),'heating_ramp':quantity('reaction.heating.ramp'),'stirring_speed':quantity('reaction.stirring.speed'),'pressure':quantity('reaction.pressure')},environment=unknown_environment(),description='Increase the temperature to 80 C with continuous stirring for another 2.0 h. Exact heating ramp and whether any ramp time enters that duration are unresolved; do not assume reflux, a sealed vessel or inert gas.'),
 operation('filter-dispersion','filter','Filter the as-prepared dispersion',prep,['as-prepared-dispersion'],['filtered-dispersion'],depends=['heat-stir-80c'],stage='workup',parameters={'filter_pore_size':quantity('workup.filter.pore')},environment=unknown_environment(),description='Filter the dispersion. Filter material and explicit filtrate/residue terminology are not stated; the subsequent operation acts on the dispersion.'),
 operation('initial-centrifugation','centrifuge','Recover product by centrifugation',prep,['filtered-dispersion'],['recovered-product'],depends=['filter-dispersion'],stage='workup',parameters={'speed':quantity('workup.centrifuge.speed'),'relative_force':quantity('workup.centrifuge.force'),'duration':quantity('workup.centrifuge.duration')},environment=unknown_environment(),description='Centrifuge the dispersion and recover product for redispersion. The paper does not explicitly name pellet/supernatant or give centrifuge settings.'),
 operation('alcohol-purification','sequential_redispersion','Redisperse sequentially in 1-butanol, 1-propanol and ethanol',prep,['recovered-product','1_butanol','1_propanol','ethanol'],['alcohol-purified-product'],depends=['initial-centrifugation'],stage='workup',parameters={'1_butanol_volume':quantity('workup.1_butanol.volume'),'1_propanol_volume':quantity('workup.1_propanol.volume'),'ethanol_volume':quantity('workup.ethanol.volume')},environment=unknown_environment(),description='Reported solvent order is 1-butanol, then 1-propanol, then ethanol, to remove unreacted molecules. Intermediate solvent-exchange mechanics, centrifugation counts and wash repetitions are not specified.'),
 operation('final-centrifugation','centrifuge','Obtain QDs by final centrifugation',prep,['alcohol-purified-product'],['final-qd-product'],depends=['alcohol-purification'],stage='workup',parameters={'speed':quantity('workup.centrifuge.speed'),'relative_force':quantity('workup.centrifuge.force'),'duration':quantity('workup.centrifuge.duration'),'isolated_product_mass':quantity('workup.product.mass'),'isolated_synthesis_yield':quantity('workup.product.yield')},environment=unknown_environment(),description='Obtain QDs by centrifugation. Neither product mass nor isolated synthesis yield is reported.'),
 operation('disperse-in-water','disperse','Disperse final S1 QDs in water',prep,['final-qd-product','water'],['aqueous-s1'],depends=['final-centrifugation'],stage='workup',parameters={'water_volume':quantity('workup.final_water.volume')},environment=unknown_environment(),description='Disperse the QDs in water for further characterization. Final volume and concentration are not supplied. Freeze drying is specific to XRD specimen preparation, not this aqueous-product workup.'),
]

p=product('fu2007-s1','ZnO',prep+struct,link='explicit',state='aqueous-s1',notes=[
 'S1 is the author-defined recipe/sample label, not a verified unique physical batch identifier. Batch and replicate counts remain unknown.',
 'The Sample Preparation paragraph explicitly defines S1; Figures 1, 2(a), 3 and 4 explicitly identify S1. Shared condition linkage is established, but identity of physical aliquots across instruments is not.',
 'No experimentally refined atomic-coordinate file/CIF is supplied. Any future reference lattice must be marked external reference.',
 'Blue emission is discussed as interface-related ZnO/OA emission, not an ordinary measured band-edge PL line.',
])
p['source_sample_label']='S1'
p['phase']=fact('wurtzite',struct,note='Observed XRD assignment matched to JCPDS 89-1397; not a prespecified target or a refined sample-specific CIF.')
p['morphology']=fact('uniform and dispersed quantum dots',struct,note='Author description; exact geometric shape is not independently parameterized.')
p['surface']=fact('OA-associated surface with DEA/hydroxyl species',evidence('main.surface'),status='author_derived',note='Interpretation of FTIR from purified/dried nanoparticles. Binding geometry, coverage and a unique molecular surface structure are not resolved.')
r['products']=[p]
r['measurements']=[
 measurement('s1-diameter','fu2007-s1','diameter',quantity('product.S1.diameter',qualifier='Approximate average diameter; separately reported +/- term is stored in diameter_spread'),'HRTEM',struct,conditions='Figure 2(a); dilute product on carbon-coated copper grids; FEI Tecnai G2 F20 at 200 kV. Main p16032 reiterates average diameter from TEM statistics.'),
 measurement('s1-diameter-spread','fu2007-s1','diameter_spread',quantity('product.S1.diameter.plus_minus',qualifier='Reported +/-0.4 nm; spread definition unreported; do not assume standard deviation or standard error'),'HRTEM',struct,conditions='Paired with the reported approximately 3.8 nm S1 diameter; number of measured particles and statistical definition of +/- are unreported.'),
 measurement('s1-pl-peak','fu2007-s1','photoluminescence_peak',quantity('product.S1.PL_peak'),'photoluminescence',optical,conditions='Aqueous dispersion, room temperature, 350 nm excitation; Hitachi F-4500. PLE detection at 432 nm is a separate measurement setting, not the PL peak.'),
 measurement('s1-pl-energy','fu2007-s1','photoluminescence_energy',quantity('product.S1.PL_energy'),'photoluminescence',optical,conditions='Energy reported by authors alongside approximately 440 nm blue emission; not an independent synthesized specimen.'),
 measurement('s1-optimal-excitation','fu2007-s1','optimal_excitation_wavelength',quantity('product.S1.optimal_excitation'),'photoluminescence excitation',optical,conditions='Aqueous dispersion, room temperature; PLE recorded with detection wavelength 432 nm.'),
 measurement('s1-optimal-excitation-energy','fu2007-s1','optimal_excitation_energy',quantity('product.S1.optimal_excitation_energy'),'photoluminescence excitation',optical,conditions='Authors report 3.54 eV alongside 350 nm optimal excitation; no independent additional specimen inferred.'),
 measurement('s1-relative-pl-qy','fu2007-s1','relative_photoluminescence_quantum_yield',quantity('product.S1.relative_QY',qualifier='Relative PL QY against quinine sulfate; not isolated synthesis yield'),'relative photoluminescence quantum-yield comparison',optical+qy,conditions='S1 in water; quinine sulfate reference in 0.5 M H2SO4 with adopted Phi=0.55. Five concentrations each, absorbance <0.1 at 350 nm; integrated PL-versus-absorbance slope comparison, refractive index 1.33 for each solvent. Excitation 350 nm, 1.00 cm quartz cuvette, excitation/emission slit widths 2.5 nm. Five optical concentrations do not establish five synthesis replicates. Quinine sulfate/H2SO4 are calibration materials, not recipe ingredients.'),
 measurement('s1-optical-onset','fu2007-s1','optical_absorption_onset',quantity('product.S1.optical_absorption_onset'),'UV-visible absorption with author extrapolation',evidence('main.bandgap'),conditions='Figure 5b: linear extrapolation of (alpha*h*nu)^2 versus h*nu; author-extracted optical onset, not a quasiparticle-gap measurement.'),
 measurement('s1-model-gap','fu2007-s1','modeled_optical_gap',quantity('product.S1.theoretical_gap'),'author quantum-confinement calculation',evidence('main.bandgap'),conditions='Calculation uses TEM diameter and bulk/effective-mass parameters; separate from the author-extracted 3.94 eV optical onset.',derives=['s1-diameter']),
 measurement('s1-photostability-loss','fu2007-s1','photoluminescence_intensity_decrease',quantity('product.S1.PL_initial_drop'),'continuous-irradiation photoluminescence stability',optical+evidence('main.characterization'),conditions='9.4% loss during first 6 h monitoring 440 nm emission under 350 nm irradiation at 130 uW/cm2; thereafter described as almost unchanged. Not a dark-storage lifetime.'),
]

r['quality']['experimental_outcome']='reported_product'
r['quality']['review_scope']='One author-defined S1 ZnO protocol condition, with original main/SI contents and explicit sample-label linkage reviewed; key synthesis, characterization and QY pages visually inspected. No unique physical batch or replicate count is inferred. Operational omissions remain explicit.'
r['quality']['missing_fields']=AUDIT['missing_fields']
r['quality']['conflicts']=[]
r['quality']['requested_tasks']=['precursor_selection','partial_protocol','size_conditioned_recipe','exact_structure_recipe']
r['context_links']=[
 {'label':'Original article and associated supporting information','url':'https://doi.org/10.1021/ja075604i','relation':'primary_source'},
]

OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

from dataset_lib import validate_record,eligibility
errors=validate_record(r)
if errors:
    print('\n'.join(errors))
    raise SystemExit(1)
serialized=OUT.read_text(encoding='utf-8')
assert 'C:/' not in serialized and 'C:\\' not in serialized
assert all(m['identity']['pubchem_cid'] is None and m['identity']['smiles'] is None for m in r['materials'])
assert r['products'][0]['source_sample_label']=='S1' and r['products'][0]['batch_id'] is None
assert r['intended_target']['phase']['value'] is None
gates=eligibility(r)
assert not gates['exact_structure_recipe']['eligible']
assert gates['size_conditioned_recipe']['eligible']
print(json.dumps({'file':str(OUT),'validation_errors':errors,'eligibility':gates,'operation_count':len(r['operations']),'measurement_count':len(r['measurements']),'bytes':OUT.stat().st_size}))
