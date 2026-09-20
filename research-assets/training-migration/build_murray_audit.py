import hashlib
import json
from pathlib import Path

ROOT = Path('[local path redacted]')
ASSETS = ROOT / 'research-assets'
SITE = ROOT / 'recipe-atlas/dist/assets'
OUT = ASSETS / 'training-migration/murray-audit.json'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

legacy = read(ASSETS / 'murray1993-recipe.json')
characterization = read(SITE / 'murray1993-characterization.json')
structure_manifest = read(SITE / 'cdse-structures/download-manifest.json')

sources = {
    'general': {'source_id':'murray1993.main','pdf_pages':[1,2],'printed_pages':[8706,8707],'section':'II. Experimental Section / General'},
    'm1': {'source_id':'murray1993.main','pdf_pages':[2],'printed_pages':[8707],'section':'Method 1 / CdSe'},
    'm1_cdte': {'source_id':'murray1993.main','pdf_pages':[2],'printed_pages':[8707],'section':'Method 1 / final CdTe paragraph'},
    'm2': {'source_id':'murray1993.main','pdf_pages':[2],'printed_pages':[8707],'section':'Method 2'},
    'isolation': {'source_id':'murray1993.main','pdf_pages':[2],'printed_pages':[8707],'section':'Isolation and Purification of Crystallites'},
    'selection': {'source_id':'murray1993.main','pdf_pages':[2],'printed_pages':[8707],'section':'Size-Selective Precipitation'},
    'exchange': {'source_id':'murray1993.main','pdf_pages':[2],'printed_pages':[8707],'section':'Surface Exchange'},
    'fig1': {'source_id':'murray1993.main','pdf_pages':[3],'printed_pages':[8708],'section':'Figure 1 and Size-Selective Precipitation discussion'},
    'tem': {'source_id':'murray1993.main','pdf_pages':[5],'printed_pages':[8710],'section':'TEM discussion and Figure 6'},
    'small_structure': {'source_id':'murray1993.main','pdf_pages':[7],'printed_pages':[8712],'section':'Discussion of smallest clusters after Figure 11'},
    'overall_structure': {'source_id':'murray1993.main','pdf_pages':[9],'printed_pages':[8714],'section':'Final structural summary'},
    'optical_methods': {'source_id':'murray1993.main','pdf_pages':[2],'printed_pages':[8707],'section':'Optical Characterization'},
    'tem_methods': {'source_id':'murray1993.main','pdf_pages':[2],'printed_pages':[8707],'section':'Transmission Electron Microscopy'},
    'xrd_methods': {'source_id':'murray1993.main','pdf_pages':[2],'printed_pages':[8707],'section':'X-ray Powder Diffraction'},
    'steigerwald1988': {'source_id':'steigerwald1988.main','doi':'10.1021/ja00218a008','pdf_pages':[3],'printed_pages':[3047],'section':'Preparation of Powders of II–VI Materials with Silylchalcogenide Reagents'},
}

def q(value, unit, source, *, approximate=False, status='reported', basis=None, note=None):
    result = {'value':value,'unit':unit,'status':status,'approximate':approximate,'source_locator_id':source}
    if basis is not None: result['basis'] = basis
    if note is not None: result['note'] = note
    return result

def interval(low, high, unit, source, *, approximate=False, note=None):
    result = {'value':None,'range':{'minimum':low,'maximum':high},'unit':unit,'status':'reported_range','approximate':approximate,'source_locator_id':source}
    if note: result['note'] = note
    return result

def missing(unit=None, source=None, reason='not_reported'):
    return {'value':None,'unit':unit,'status':'missing','missing_reason':reason,'source_locator_id':source}

def text_fact(value, source, status='reported'):
    return {'value':value,'status':status,'source_locator_id':source}

def calc(value, unit, expression, inputs, *, assumptions=None, basis=None):
    r = q(value,unit,'m1',status='calculated',basis=basis)
    r.update({'expression':expression,'input_quantity_ids':inputs,'assumptions':assumptions or []})
    return r

Q = {
 'topo.distill.temperature': interval(260,300,'degC','general'),
 'topo.distill.pressure': q(1,'Torr','general',approximate=True),
 'topo.distill.duration': missing('min','general'),
 'me2cd.filter.pore': q(0.250,'um','general'),
 'me2cd.vacuum_transfer.pressure': missing('Torr','general'),
 'me2cd.vacuum_transfer.temperature': missing('degC','general'),
 'me2cd.vacuum_transfer.duration': missing('min','general'),
 'selenium.purity': {'value':99.99,'unit':'percent','status':'reported_lower_bound','qualifier':'99.99+%','source_locator_id':'general'},
 'topse.stock.concentration': q(1.0,'mol/L','general',basis='named TOPSe stock in TOP'),
 'topse.stock.se_mass': missing('g','general'),
 'topse.stock.top_volume': missing('mL','general'),
 'topse.stock.final_volume': missing('mL','general'),
 'topse.stock.preparation_temperature': missing('degC','general'),
 'topse.stock.preparation_duration': missing('min','general'),
 'm1.topo.mass': q(50,'g','m1'),
 'm1.degas.temperature': q(200,'degC','m1',approximate=True,basis='reaction vessel/medium; not specified heater setpoint'),
 'm1.degas.pressure': q(1,'Torr','m1',approximate=True),
 'm1.degas.duration': q(20,'min','m1',approximate=True),
 'm1.stabilize.temperature': q(300,'degC','m1',approximate=True,basis='reaction flask before injection'),
 'm1.stabilize.pressure': q(1,'atm','m1',approximate=True,basis='argon atmosphere'),
 'm1.stabilize.duration': missing('min','m1'),
 'm1.A.me2cd.volume': q(1.00,'mL','m1'),
 'm1.A.me2cd.amount': q(13.35,'mmol','m1'),
 'm1.A.top.volume': q(25.0,'mL','m1'),
 'm1.A.measured_volume': missing('mL','m1'),
 'm1.B.topse_stock.volume': q(10.0,'mL','m1',basis='aliquot of 1.0 M TOPSe stock, not neat TOPSe or extra Se shot'),
 'm1.B.topse.amount': q(10.00,'mmol','m1'),
 'm1.B.top.volume': q(15.0,'mL','m1',basis='additional TOP, beyond TOP already present in stock'),
 'm1.B.measured_volume': missing('mL','m1'),
 'm1.syringe.capacity': q(50,'mL','m1',basis='nominal syringe capacity; not measured injection volume'),
 'm1.injection.measured_volume': missing('mL','m1'),
 'm1.injection.duration': missing('s','m1'),
 'm1.injection.stirring_speed': missing('rpm','m1'),
 'm1.post_injection.temperature': q(180,'degC','m1',approximate=True,basis='observed temperature after injection; not independent programmed hold'),
 'm1.post_injection.absorption_feature': interval(440,460,'nm','m1',note='Immediate absorption feature, not final PL peak'),
 'm1.reheat.temperature_range': interval(230,260,'degC','m1'),
 'm1.reheat.ramp': missing('degC/min','m1'),
 'm1.reheat.duration': missing('min','m1'),
 'm1.monitor.interval': interval(5,10,'min','m1'),
 'm1.monitor.aliquot_volume': missing('mL','m1'),
 'm1.growth.exact_duration': missing('min','m1'),
 'm1.withdraw.volume': missing('mL','m1'),
 'm1.withdraw.temperature': missing('degC','m1'),
 'm1.withdraw.elapsed_time': missing('min','m1'),
 'm1.product.size_span': interval(1.5,11.5,'nm','m1',approximate=True,note='Converted from approximately 15–115 A; major-axis size series obtainable from one preparation, not one product size or distribution'),
 'workup.input_aliquot.volume': q(10,'mL','isolation',basis='reaction solution aliquot'),
 'workup.cool.temperature': q(60,'degC','isolation',approximate=True),
 'workup.cool.duration': missing('min','isolation'),
 'workup.methanol.first': q(20,'mL','isolation'),
 'workup.butanol.redispersion': q(25,'mL','isolation'),
 'workup.methanol.second': q(25,'mL','isolation'),
 'workup.methanol.rinse': q(50,'mL','isolation'),
 'workup.centrifuge.speed': missing('rpm','isolation'),
 'workup.centrifuge.force': missing('g_relative','isolation'),
 'workup.centrifuge.duration': missing('min','isolation'),
 'workup.dry.pressure': missing('Torr','isolation'),
 'workup.dry.temperature': missing('degC','isolation'),
 'workup.dry.duration': missing('min','isolation'),
 'workup.product.mass': q(300,'mg','isolation',approximate=True,basis='TOP/TOPO-capped powder from a 10-mL aliquot; not whole-batch or bare-CdSe yield'),
 'workup.product.percent_yield': missing('percent','isolation'),
 'selection.butanol.volume': missing('mL','selection'),
 'selection.methanol.volume': missing('mL','selection'),
 'selection.methanol.rate': missing('mL/min','selection'),
 'selection.cycles': missing('count','selection'),
 'selection.recovered_mass': missing('mg','selection'),
 'exchange.input.mass': q(50,'mg','exchange',approximate=True,basis='TOP/TOPO-capped crystallites'),
 'exchange.pyridine.volume': interval(5,10,'mL','exchange'),
 'exchange.temperature': q(60,'degC','exchange',approximate=True),
 'exchange.duration': missing('min','exchange'),
 'exchange.hexane.volume': missing('mL','exchange'),
 'exchange.cycles': missing('count','exchange'),
 'm2.precursor.storage_temperature': q(-35,'degC','general',basis='prepared (TMS)2Se and (BDMS)2Te in drybox'),
 'm2.precursor.storage_duration': missing('h','general'),
 'm2.tms2se.mass': missing('g','m2'),
 'm2.tms2se.amount': missing('mmol','m2'),
 'm2.tms2se.volume': missing('mL','m2'),
 'm2.stock.concentration': missing('mol/L','m2'),
 'm2.stock.solvent_volume': missing('mL','m2'),
 'm2.me2cd.amount': missing('mmol','m2',reason='not_independently_specified_in_modification'),
 'm2.top.volume': missing('mL','m2',reason='not_independently_specified_in_modification'),
 'm2.topo.mass': missing('g','m2',reason='not_independently_specified_in_modification'),
 'm2.injection.temperature': missing('degC','m2',reason='general_CdSe_thermal_program_not_independently_specified'),
 'm2.injection.volume': missing('mL','m2'),
 'm2.injection.duration': missing('s','m2'),
 'm2.growth.temperature': missing('degC','m2',reason='general_CdSe_thermal_program_not_independently_specified'),
 'm2.growth.duration': missing('min','m2'),
 'm2.small.injection.temperature': q(100,'degC','m2',approximate=True),
 'm2.small.growth.temperature': q(100,'degC','m2',approximate=True),
 'm2.small.product.size': q(1.2,'nm','m2',approximate=True,basis='reported approximately 12 A smallest CdSe species; not exact atomistic structure'),
 'm2.small.growth.duration': missing('min','m2'),
 'm2.small.product.quantity': missing('mg','m2'),
 'm2.cds.growth.temperature': interval(290,320,'degC','m2',approximate=True,note='CdS only; forbidden in CdSe default conditions'),
 'm1.cdte.injection.temperature': q(240,'degC','m1_cdte',approximate=True),
 'm1.cdte.growth.temperature': interval(190,220,'degC','m1_cdte',approximate=True),
 'm1.cdte.topte.stock_concentration': q(1.0,'mol/L','general'),
}
Q['m1.feed.cd_to_se'] = calc(1.335,'dimensionless','13.35 / 10.00',['m1.A.me2cd.amount','m1.B.topse.amount'],basis='initial elemental feed molar ratio')
Q['m1.A.nominal_volume'] = calc(26.0,'mL','1.00 + 25.0',['m1.A.me2cd.volume','m1.A.top.volume'],assumptions=['additive liquid volumes'])
Q['m1.B.nominal_volume'] = calc(25.0,'mL','10.0 + 15.0',['m1.B.topse_stock.volume','m1.B.top.volume'],assumptions=['additive liquid volumes'])
Q['m1.injection.nominal_volume'] = calc(51.0,'mL','26.0 + 25.0',['m1.A.nominal_volume','m1.B.nominal_volume'],assumptions=['additive liquid volumes; no loss assumed for arithmetic only'],basis='component sum, not observed injection volume')
Q['m1.A.nominal_concentration'] = calc(13.35/26.0,'mol/L','13.35 mmol / 26.0 mL',['m1.A.me2cd.amount','m1.A.nominal_volume'],assumptions=['additive liquid volumes'])
Q['m1.B.nominal_concentration'] = calc(0.400,'mol/L','10.00 mmol / 25.0 mL',['m1.B.topse.amount','m1.B.nominal_volume'],assumptions=['additive liquid volumes'])
Q['m1.injection.nominal_cd_concentration'] = calc(13.35/51.0,'mol/L','13.35 mmol / 51.0 mL',['m1.A.me2cd.amount','m1.injection.nominal_volume'],assumptions=['additive liquid volumes'])
Q['m1.injection.nominal_se_concentration'] = calc(10.00/51.0,'mol/L','10.00 mmol / 51.0 mL',['m1.B.topse.amount','m1.injection.nominal_volume'],assumptions=['additive liquid volumes'])

entities = []
for reagent in legacy['reagents']:
    entities.append({'id':'chemical.'+reagent['id'],'record_type':'chemical_identity','name':reagent['name'],'formula':reagent.get('normalized_formula',reagent.get('formula')),'supplier':reagent.get('supplier'),'grade':reagent.get('grade'),'purity_reported':reagent.get('purity_as_reported'),'source_locator_id':'general','scope':'reagent specification, not a physical reagent lot','numeric_purity_missing':reagent['id'] not in ['selenium']})
entities.extend([
 {'id':'chemical.tms2se','record_type':'chemical_identity','name':'bis(trimethylsilyl)selenium','formula':'C6H18SeSi2','supplier':None,'source_locator_id':'general','preparation':'literature methods, Murray references 3a and 4 jointly','storage_temperature_quantity':'m2.precursor.storage_temperature','storage_environment':'drybox; gas identity not stated'},
 {'id':'chemical.chloroform','record_type':'chemical_identity','name':'chloroform','formula':'CHCl3','source_locator_id':'selection','role':'alternative solvent; not mandatory input'},
])

states = {}
def state(id, label, *, composition=None, role=None, source='m1'):
    states[id] = {'id':id,'record_type':'material_state_template','label':label,'composition':composition,'role':role,'source_locator_id':source,'physical_batch_id':None,'physical_sample_id':None,'identity_status':'procedural placeholder, not an author-assigned experimental specimen'}

for sid,label,composition in [
 ('state.topo.purified','Distilled TOPO','TOPO'),('state.me2cd.filtered','Filtered Me2Cd','Me2Cd'),('state.me2cd.purified','Vacuum-transferred Me2Cd','Me2Cd'),
 ('state.topse.stock','1.0 M TOPSe stock in TOP',['TOPSe','TOP']),('state.m1.A','Solution A',['Me2Cd','TOP']),('state.m1.B','Solution B',['TOPSe','TOP']),
 ('state.m1.injection','Combined A+B injection mixture',['Me2Cd','TOPSe','TOP']),('state.m1.topo.dry','Dried and degassed TOPO','TOPO'),
 ('state.m1.topo.hot','TOPO stabilized before injection','TOPO'),('state.m1.reaction.initial','Reaction mixture immediately after injection','CdSe-containing mixture'),
 ('state.m1.reaction.growing','Adaptively grown reaction mixture','CdSe-containing mixture'),('state.m1.monitor.aliquot','Growth-monitoring aliquot','CdSe-containing mixture'),
 ('state.m1.product.portion','Size-selected-by-withdrawal growth-solution portion','CdSe-containing mixture')]:
    state(sid,label,composition=composition)
for sid,label in [
 ('state.workup.input','A 10-mL reaction aliquot'),('state.workup.cooled','Aliquot cooled to about 60 C'),('state.workup.first_flocculate','First nanocrystal-rich flocculate'),
 ('state.workup.first_supernatant','Supernatant separated at first centrifugation'),('state.workup.butanol_dispersion','Flocculate dispersed in 1-butanol'),
 ('state.workup.clear','Clear nanocrystal-containing supernatant'),('state.workup.gray','Gray Cd/Se-rich byproduct precipitate'),('state.workup.second_flocculate','Reflocculated nanocrystals'),
 ('state.workup.rinsed','Methanol-rinsed flocculate'),('state.workup.powder','Free-flowing TOP/TOPO-capped CdSe powder')]: state(sid,label,source='isolation')
for sid,label in [('state.selection.input','Purified nanocrystals supplied to size selection'),('state.selection.dispersion','Optically clear dispersion'),('state.selection.flocculate','Large-particle-enriched precipitate'),('state.selection.supernatant','Other fraction after size-selection centrifugation'),('state.selection.final','Endpoint-selected fraction')]: state(sid,label,source='selection')
for sid,label in [('state.exchange.input','TOP/TOPO-capped crystallites supplied to exchange'),('state.exchange.dispersion','Crystallites gradually dispersed in pyridine'),('state.exchange.flocculate','Hexane-flocculated crystallites'),('state.exchange.final','Repeatedly exchanged crystallites')]: state(sid,label,source='exchange')
for sid,label in [('state.m2.tms2se.prepared','Literature-prepared (TMS)2Se'),('state.m2.tms2se.stored','Prepared (TMS)2Se stored in drybox'),('state.m2.injection','Unquantified Method 2 injection formulation'),('state.m2.product','CdSe produced by the referenced Method 2 framework'),('state.m2.small.product','Approximately 1.2-nm CdSe species from the mild variant')]: state(sid,label,source='m2')

ops = []
def op(id, action, inputs, outputs, source, *, quantity_ids=None, conditions=None, after=None, note=None, status='reported'):
    d={'id':id,'action':action,'inputs':inputs,'outputs':outputs,'source_locator_id':source,'evidence_status':status,'quantity_ids':quantity_ids or [],'conditions':conditions or {},'depends_on':after or []}
    if note: d['note']=note
    ops.append(d)

op('prep.topo.distill','distill_and_collect_fraction',['chemical.topo'],['state.topo.purified'],'general',quantity_ids=['topo.distill.temperature','topo.distill.pressure','topo.distill.duration'],note='Separate precursor purification. Not reactor drying or injection temperature.')
op('prep.me2cd.filter','filter',['chemical.dimethylcadmium'],['state.me2cd.filtered'],'general',quantity_ids=['me2cd.filter.pore'])
op('prep.me2cd.transfer','vacuum_transfer',['state.me2cd.filtered'],['state.me2cd.purified'],'general',quantity_ids=['me2cd.vacuum_transfer.pressure','me2cd.vacuum_transfer.temperature','me2cd.vacuum_transfer.duration'],after=['prep.me2cd.filter'])
op('prep.topse.stock','prepare_named_stock_by_dissolving',['chemical.selenium','chemical.top'],['state.topse.stock'],'general',quantity_ids=['topse.stock.concentration','topse.stock.se_mass','topse.stock.top_volume','topse.stock.final_volume','topse.stock.preparation_temperature','topse.stock.preparation_duration'],conditions={'handling':'standard airless procedures'},note='Exact stock species beyond named TOPSe are not resolved. Total stock-preparation scale is unreported.')
op('m1.prepare.A','add_and_mix',['state.me2cd.purified','chemical.top'],['state.m1.A'],'m1',quantity_ids=['m1.A.me2cd.volume','m1.A.me2cd.amount','m1.A.top.volume'],conditions={'environment':'drybox','drybox_gas':None},after=['prep.me2cd.transfer'])
op('m1.prepare.B','dilute_stock',['state.topse.stock','chemical.top'],['state.m1.B'],'m1',quantity_ids=['m1.B.topse_stock.volume','m1.B.topse.amount','m1.B.top.volume'],after=['prep.topse.stock'],note='TOPSe stock is an aliquot input, not its entire unspecified prepared batch. Specific drybox placement of B preparation is not separately stated; general airless handling applies.')
op('m1.prepare.injection','combine_and_load_syringe',['state.m1.A','state.m1.B'],['state.m1.injection'],'m1',quantity_ids=['m1.syringe.capacity','m1.injection.measured_volume'],conditions={'environment':'drybox','transferred_fraction':'combined solutions as described'},after=['m1.prepare.A','m1.prepare.B'],note='50 mL is reported syringe capacity; nominal component sum is 51 mL. Do not normalize one into the other.')
op('m1.degas','heat_under_reduced_pressure_with_periodic_flush',['state.topo.purified','chemical.argon'],['state.m1.topo.dry'],'m1',quantity_ids=['m1.topo.mass','m1.degas.temperature','m1.degas.pressure','m1.degas.duration'],conditions={'gas':'argon','flush_frequency':'periodic; numerical frequency unknown','gas_flow':None,'bath_medium':None},after=['prep.topo.distill'])
op('m1.stabilize','stabilize_temperature_under_gas',['state.m1.topo.dry','chemical.argon'],['state.m1.topo.hot'],'m1',quantity_ids=['m1.stabilize.temperature','m1.stabilize.pressure','m1.stabilize.duration'],conditions={'gas':'argon','bath_medium':None},after=['m1.degas'])
op('m1.inject','remove_heat_and_inject_once',['state.m1.injection','state.m1.topo.hot'],['state.m1.reaction.initial'],'m1',quantity_ids=['m1.injection.duration','m1.injection.measured_volume','m1.injection.stirring_speed'],conditions={'addition':'single rapid injection through rubber septum','stirring':'vigorous','heat':'removed before injection'},after=['m1.prepare.injection','m1.stabilize'],note='Rapid is qualitative; no numerical injection time or mixing time.')
op('m1.reheat','restore_heat_and_gradually_raise_temperature',['state.m1.reaction.initial'],['state.m1.reaction.growing'],'m1',quantity_ids=['m1.reheat.temperature_range','m1.reheat.ramp','m1.reheat.duration'],after=['m1.inject'])
op('m1.monitor','withdraw_monitoring_aliquot_and_measure_absorption',['state.m1.reaction.growing'],['state.m1.monitor.aliquot'],'m1',quantity_ids=['m1.monitor.interval','m1.monitor.aliquot_volume'],after=['m1.reheat'],note='Repeated during growth. Do not assign the later 10-mL purification volume to monitoring aliquots.')
op('m1.adjust','adapt_growth_temperature',['state.m1.reaction.growing'],['state.m1.reaction.growing'],'m1',quantity_ids=['m1.growth.exact_duration'],conditions={'duration_text':'a few hours of steady growth for best-quality samples','numerical_controller_thresholds':None,'rule_if_distribution_spreads':'lower temperature','rule_if_growth_appears_to_stop':'increase temperature'},after=['m1.monitor'],note='Feedback loop, not a fixed schedule; output is an updated state of the same procedural stream.')
op('m1.withdraw','transfer_portion_by_cannula_and_store',['state.m1.reaction.growing'],['state.m1.product.portion'],'m1',quantity_ids=['m1.withdraw.volume','m1.withdraw.temperature','m1.withdraw.elapsed_time'],conditions={'endpoint':'desired absorption characteristics','destination':'vial','storage_temperature':None,'storage_duration':None},after=['m1.reheat'],note='Can branch at multiple growth stages. No fixed time or temperature is linked to each size.')
op('workup.withdraw_cool','withdraw_by_cannula_and_cool',['state.workup.input'],['state.workup.cooled'],'isolation',quantity_ids=['workup.input_aliquot.volume','workup.cool.temperature','workup.cool.duration'],conditions={'cooling_method':None})
op('workup.first_flocculation','add_nonsolvent_then_centrifuge',['state.workup.cooled','chemical.methanol'],['state.workup.first_flocculate','state.workup.first_supernatant'],'isolation',quantity_ids=['workup.methanol.first','workup.centrifuge.speed','workup.centrifuge.force','workup.centrifuge.duration'],conditions={'methanol_grade':'anhydrous','retain':'state.workup.first_flocculate'},after=['workup.withdraw_cool'])
op('workup.redisperse','disperse',['state.workup.first_flocculate','chemical.butanol'],['state.workup.butanol_dispersion'],'isolation',quantity_ids=['workup.butanol.redispersion'],conditions={'butanol_grade':'anhydrous'},after=['workup.first_flocculation'])
op('workup.clarify','centrifuge_and_select_supernatant',['state.workup.butanol_dispersion'],['state.workup.clear','state.workup.gray'],'isolation',quantity_ids=['workup.centrifuge.speed','workup.centrifuge.force','workup.centrifuge.duration'],conditions={'retain':'state.workup.clear','discard':'state.workup.gray'},after=['workup.redisperse'])
op('workup.reflocculate','add_nonsolvent',['state.workup.clear','chemical.methanol'],['state.workup.second_flocculate'],'isolation',quantity_ids=['workup.methanol.second'],conditions={'methanol_grade':'anhydrous','separation_mechanics_after_flocculation':'not separately specified'},after=['workup.clarify'])
op('workup.rinse','rinse',['state.workup.second_flocculate','chemical.methanol'],['state.workup.rinsed'],'isolation',quantity_ids=['workup.methanol.rinse'],after=['workup.reflocculate'])
op('workup.dry','vacuum_dry',['state.workup.rinsed'],['state.workup.powder'],'isolation',quantity_ids=['workup.dry.pressure','workup.dry.temperature','workup.dry.duration'],after=['workup.rinse'])
op('selection.disperse','disperse_to_optical_clarity',['state.selection.input','chemical.butanol'],['state.selection.dispersion'],'selection',quantity_ids=['selection.butanol.volume'],conditions={'butanol_grade':'anhydrous','endpoint':'optically clear'})
op('selection.precipitate','add_nonsolvent_dropwise_then_centrifuge',['state.selection.dispersion','chemical.methanol'],['state.selection.flocculate','state.selection.supernatant'],'selection',quantity_ids=['selection.methanol.volume','selection.methanol.rate'],conditions={'methanol_grade':'anhydrous','endpoint':'opalescence persists upon stirring or sonication','retain':'state.selection.flocculate','retained_fraction_description':'enriched with largest crystallites','centrifugation_speed':None,'centrifugation_time':None},after=['selection.disperse'])
op('selection.repeat','repeat_redispersion_and_size_selection',['state.selection.flocculate'],['state.selection.final'],'selection',quantity_ids=['selection.cycles','selection.recovered_mass'],conditions={'repeat_operations':['selection.disperse','selection.precipitate'],'stop_condition':'no further sharpening of optical absorption'},after=['selection.precipitate'],note='Figure 1 illustrates one series; do not encode a universal three-cycle recipe.')
op('exchange.disperse','heat_with_competing_ligand_until_dispersed',['state.exchange.input','chemical.pyridine'],['state.exchange.dispersion'],'exchange',quantity_ids=['exchange.input.mass','exchange.pyridine.volume','exchange.temperature','exchange.duration'])
op('exchange.flocculate','add_excess_nonsolvent_then_centrifuge',['state.exchange.dispersion','chemical.hexane'],['state.exchange.flocculate'],'exchange',quantity_ids=['exchange.hexane.volume'],conditions={'hexane_amount_description':'excess','retain':'crystallite flocculate','centrifugation_speed':None,'centrifugation_time':None},after=['exchange.disperse'])
op('exchange.repeat','repeat_dispersion_and_flocculation',['state.exchange.flocculate'],['state.exchange.final'],'exchange',quantity_ids=['exchange.cycles'],conditions={'repeat_operations':['exchange.disperse','exchange.flocculate'],'repeat_text':'a number of times'},after=['exchange.flocculate'])
op('m2.prepare_precursor','prepare_by_cited_literature',['chemical.tms2se'],['state.m2.tms2se.prepared'],'general',status='literature_preparation_reported_procedure_not_reproduced',note='Identity-level placeholder: this is NOT a reaction with (TMS)2Se as starting reagent. Resolve actual input chemicals only through a separately scoped verified precursor-preparation record; refs 3a and 4 are jointly cited.')
ops[-1]['inputs'] = []
ops[-1]['external_preparation_refs'] = ['murray1993.reference3a','murray1993.reference4']
op('m2.store_precursor','store_in_drybox',['state.m2.tms2se.prepared'],['state.m2.tms2se.stored'],'general',quantity_ids=['m2.precursor.storage_temperature','m2.precursor.storage_duration'],conditions={'environment':'drybox','gas_identity':None},after=['m2.prepare_precursor'])
op('m2.substitute','substitute_chalcogen_precursor_in_referenced_framework',['state.m2.tms2se.stored','chemical.dimethylcadmium','chemical.top','chemical.topo'],['state.m2.injection','state.m2.product'],'m2',quantity_ids=['m2.tms2se.mass','m2.tms2se.amount','m2.tms2se.volume','m2.stock.concentration','m2.stock.solvent_volume','m2.me2cd.amount','m2.top.volume','m2.topo.mass','m2.injection.temperature','m2.injection.volume','m2.injection.duration','m2.growth.temperature','m2.growth.duration'],status='partial_protocol_by_reference',after=['m2.store_precursor'],note='Not an executable one-step reaction. Cd source and TOP/TOPO framework inherited by reference; no independently quantified formulation. Do not duplicate all Method 1 values as direct Method 2 measurements.')
op('m2.small.inject_grow','inject_and_grow_under_mild_conditions',['state.m2.injection'],['state.m2.small.product'],'m2',quantity_ids=['m2.small.injection.temperature','m2.small.growth.temperature','m2.small.growth.duration'],status='reported_partial_variant',note='Separate variant replacing general thermal assumptions; no measured complete batch identity. Quantity formulation remains unknown.')

def eligibility(tasks, excluded, reasons):
    return {'eligible_tasks':tasks,'ineligible_tasks':excluded,'reasons':reasons,'physical_experiment_count':None,'fully_linked_exact_structure_recipe_pairs':0}

strict = ['exact_CIF_to_complete_recipe_supervision','exact_size_to_fixed_growth_schedule_supervision','autonomous_lab_execution_without_completion_and_validation']
records = [
 {'id':'murray1993.protocol.cdse.method1','record_type':'literature_protocol_template','source_locator_id':'m1','label':'CdSe Method 1 / TOPSe','physical_experiment_id':None,'author_batch_id':None,'variant_of':None,
  'intended_target':{'composition':text_fact('CdSe','m1'),'specific_size':missing('nm','m1'),'specified_atomic_coordinates':None,'desired_endpoint':text_fact('desired absorption characteristics; numerical endpoint not provided','m1'),'cap_description':text_fact('TOP/TOPO capped','m1')},
  'observed_product_claims':[{'id':'claim.m1.size_series','quantity_id':'m1.product.size_span','kind':'method-level reported achievable size series','specimen_link':'unresolved; no individual time/temperature history'},{'id':'claim.m1.post_injection','temperature_quantity_id':'m1.post_injection.temperature','absorption_quantity_id':'m1.post_injection.absorption_feature','color':text_fact('deep yellow/orange','m1'),'stage':'immediately after injection','not_final_target':True}],
  'operation_ids':[o['id'] for o in ops if o['id'].startswith(('prep.','m1.'))],
  'branch_record_ids':['murray1993.procedure.cdse.isolation','murray1993.procedure.cdse.size_selection','murray1993.procedure.cdse.pyridine_exchange'],
  'eligibility':eligibility(['source_to_structured_recipe','operation_order_and_dependency_extraction','composition_conditioned_route_retrieval','partial_recipe_recommendation_with_missingness'],strict,['Adaptive recipe with missing exact thermal trajectory and sample-specific outcomes','No experimentally linked product CIF']),
  'critical_missing':['reaction vessel geometry/capacity','stirring speed','injection duration and measured volume','stock dissolution time/temperature','ramp and specimen-specific growth trajectory','feedback thresholds','monitoring aliquot volume','complete workup settings','whole-batch yield','specific figure-to-method sample links']},
 {'id':'murray1993.protocol.cdse.method2','record_type':'literature_protocol_modification','source_locator_id':'m2','label':'CdSe Method 2 / (TMS)2Se','physical_experiment_id':None,'author_batch_id':None,'variant_of':'murray1993.protocol.cdse.method1',
  'intended_target':{'composition':text_fact('CdSe','m2'),'specific_size':missing('nm','m2'),'specified_atomic_coordinates':None},
  'observed_product_claims':[{'id':'claim.m2.cdse_production','value':'CdSe nanocrystallites produced using silyl precursor substitution','source_locator_id':'m2','scope':'route-level report; no separately identified complete experimental batch'}],
  'operation_ids':['m2.prepare_precursor','m2.store_precursor','m2.substitute'],'variant_record_ids':['murray1993.protocol.cdse.method2.small100c'],
  'inheritance':{'parent':'murray1993.protocol.cdse.method1','type':'author_references_method_framework','explicit_override':{'selenium_precursor':{'from':'TOPSe','to':'(TMS)2Se'}},'inherit_as_direct_numeric_facts':False,'inherited_context':['cadmium source','coordinating TOP/TOPO framework','airless handling'],'quantities_need_independent_evidence':True},
  'branch_record_ids':['murray1993.procedure.cdse.isolation','murray1993.procedure.cdse.size_selection','murray1993.procedure.cdse.pyridine_exchange'],
  'eligibility':eligibility(['source_to_partial_recipe','precursor_substitution_extraction','composition_conditioned_route_retrieval'],strict+['fully_quantified_recipe_generation_target'],['Independent injection stock and general CdSe temperature program unreported','Unknown inherited numerical details must not be completed by copying Method 1']),
  'critical_missing':['all independent reagent charges','injection-stock solvent composition and concentration','injection volume and duration','general CdSe injection/growth temperatures','duration','method-specific yield','figure-to-method specimen links']},
 {'id':'murray1993.protocol.cdse.method2.small100c','record_type':'literature_protocol_variant','source_locator_id':'m2','label':'CdSe Method 2 / mild conditions / approximately 1.2 nm','physical_experiment_id':None,'author_batch_id':None,'variant_of':'murray1993.protocol.cdse.method2',
  'intended_target':{'composition':text_fact('CdSe','m2'),'size_target':{'value':None,'unit':'nm','status':'not_reported_as_prespecified_target'},'description':text_fact('production of smallest species','m2'),'specified_atomic_coordinates':None},
  'observed_product_claims':[{'id':'claim.m2.small_size','quantity_id':'m2.small.product.size','kind':'method-variant-level outcome','phase':{'value':None,'status':'bulk_polytype_assignment_not_meaningful_at_this_size','source_locator_id':'small_structure'}}],
  'operation_ids':['m2.small.inject_grow'],'precursor_context_from':'murray1993.protocol.cdse.method2',
  'explicit_overrides':['m2.small.injection.temperature','m2.small.growth.temperature'],
  'eligibility':eligibility(['source_to_partial_recipe','partial_size_condition_relation','variant_specific_route_retrieval'],strict+['fully_quantified_recipe_generation_target'],['About 100 C injection/growth and about 1.2 nm outcome explicitly linked only at variant level','Not a demonstrated figure-to-batch or exact structural-coordinate pairing','No charges, duration or method-specific isolated quantity']),
  'counting':'Separate addressable variant record; grouped with parent; not an independently identified experimental run or additional fully labeled training pair'},
 {'id':'murray1993.procedure.cdse.isolation','record_type':'reusable_literature_procedure','source_locator_id':'isolation','label':'Common CdSe isolation / 10-mL reaction aliquot','physical_experiment_id':None,'author_batch_id':None,
  'intended_target':{'description':'recover capped CdSe powder from reaction solution','specific_size':None},'operation_ids':[o['id'] for o in ops if o['id'].startswith('workup.')],
  'observed_product_claims':[{'id':'claim.workup.recovery','quantity_id':'workup.product.mass','route_assignment':'not established as Method 2-specific','state':'state.workup.powder'},{'id':'claim.workup.gray','composition':'mostly elemental Cd and Se','source_locator_id':'isolation','state':'state.workup.gray','evidence':'XRD and EDX','retained_product':False}],
  'applicability':'article-level common workup; attach as referenced procedure, not proof of execution for every specimen','eligibility':eligibility(['workup_action_extraction','fraction_tracking','partial_procedure_completion_with_explicit_masks'],['structure_to_synthesis_training_as_independent_experiment'],['Common procedure is reused, not a new independent synthesis'])},
 {'id':'murray1993.procedure.cdse.size_selection','record_type':'reusable_literature_procedure','source_locator_id':'selection','label':'Endpoint-controlled size-selective precipitation','physical_experiment_id':None,'author_batch_id':None,
  'intended_target':{'description':'narrower particle-size distribution','specific_size':None},'operation_ids':[o['id'] for o in ops if o['id'].startswith('selection.')],
  'observed_product_claims':[],'observation_refs':['murray1993.observation.figure_1'],'observation_link_status':'Figure 1 explicitly illustrates fractionation; input synthesis batch/route remains unknown',
  'alternatives':[{'solvent':'pyridine','nonsolvent':'hexane'},{'solvent':'chloroform','nonsolvent':'methanol'}],'alternatives_are_additional_mandatory_inputs':False,
  'eligibility':eligibility(['fractionation_action_extraction','partial_before_after_size_selection_relation'],['structure_to_synthesis_training_as_independent_experiment'],['No universal cycle count or isolated synthesis batch identity'])},
 {'id':'murray1993.procedure.cdse.pyridine_exchange','record_type':'optional_reusable_literature_procedure','source_locator_id':'exchange','label':'Optional repeated pyridine surface exchange','physical_experiment_id':None,'author_batch_id':None,
  'intended_target':{'description':'change surface derivatization and solvent dispersibility','resolved_ligand_coverage':None},'operation_ids':[o['id'] for o in ops if o['id'].startswith('exchange.')],
  'observed_product_claims':[{'value':'readily disperses in pyridine, methanol and aromatics; no longer in aliphatics','status':'reported_qualitative','source_locator_id':'exchange'}],
  'mandatory_for_base_synthesis':False,'eligibility':eligibility(['surface_exchange_operation_extraction','partial_solubility_change_relation'],['structure_to_synthesis_training_as_independent_experiment','exact_surface_structure_supervision'],['No resolved ligand binding geometry or coverage'])},
]

observations = []
for collection in ['structural_experiments','structural_model_comparisons','optical_properties']:
    for original in characterization[collection]:
        obs = {'id':'murray1993.observation.'+original['id'],'record_type':'source_observation','original_observation_key':original['id'],'source_collection':collection,'author_sample_id':None,'physical_experiment_id':None,'physical_batch_id':None,'sample_identity_status':'observation-specific placeholder; actual shared or distinct specimen identity unresolved','method_record_id':None,'method_link_status':'not_established','reported_evidence':original}
        if 'sample_id' in original:
            obs['legacy_display_sample_id'] = original['sample_id']
            obs['legacy_id_warning'] = 'This ID was created for the figure/observation; it is not an author-assigned batch identifier.'
        if original['id'] in ['figure_3','figure_11']:
            obs['series_policy'] = 'Can split into curve/panel observation records for measurement tasks; cannot infer independent batches, pair optical and XRD arrays by index, or attach each size to the general recipe.'
        observations.append(obs)

audit = {
 'schema_version':'migration-audit/1.0',
 'created_date':'2026-09-16',
 'record_type':'read_only_scientific_migration_mapping',
 'purpose':'Canonical source-grounded record plan for training-oriented migration; not a completed execution schema or laboratory SOP.',
 'identity_policy':{'no_new_physical_experiment_ids':True,'all_generated_ids_describe':'literature records, procedural stream templates or observations; never asserted physical batch identities','page_is_not_training_example':True,'do_not_count_variants_aliquots_or_shared_procedures_as_independent_experiments':True},
 'input_files':[{'path':str(p).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [ASSETS/'murray1993-recipe.json',ASSETS/'murray1993-source.txt',SITE/'cdse-material-record.json',SITE/'murray1993-method1.json',SITE/'murray1993-method2.json',SITE/'murray1993-characterization.json',SITE/'cdse-structures/download-manifest.json']],
 'sources':{'murray1993.main':legacy['source'],'steigerwald1988.main':{'doi':'10.1021/ja00218a008','title':'Surface Derivatization and Isolation of Semiconductor Cluster Molecules','year':1988,'local_pdf':str(ASSETS/'steigerwald1988-main.pdf').replace('\\','/'),'scope':'separate precursor preparation, not Murray injection-stock formulation'}},
 'source_locators':sources,
 'canonical_records':records,
 'chemical_entities':entities,
 'quantities':Q,
 'material_state_templates':list(states.values()),
 'operations':ops,
 'graph_rules':{
  'edges':'operation inputs/outputs and depends_on define preparation dependencies; stream self-updates and explicit loops are valid',
  'independent_preparations':['TOPO preparation and stock preparation both precede injection; paper presentation order does not prove they must occur serially'],
  'loops':[{'record':'murray1993.protocol.cdse.method1','operations':['m1.monitor','m1.adjust'],'end_condition':'desired absorption; numerical threshold unreported'},{'record':'murray1993.procedure.cdse.size_selection','operations':['selection.disperse','selection.precipitate'],'end_condition':'no further optical sharpening'},{'record':'murray1993.procedure.cdse.pyridine_exchange','operations':['exchange.disperse','exchange.flocculate'],'repeat_count':None}],
  'branch_connections':[{'from':'state.m1.product.portion','to':'state.workup.input','relation':'optional selection of 10-mL portion for described common workup','identity':'procedural, not an observed sample join'},{'from':'state.m2.product','to':'state.workup.input','relation':'common referenced workup possible; no Method 2-specific yield','identity':'not a verified experimental execution'},{'from':'state.workup.powder','to':'state.selection.input','relation':'size-selection refinement'},{'from':'state.workup.powder','to':'state.exchange.input','relation':'optional separate surface-exchange branch'}],
  'no_double_counting':['TOPSe stock includes TOP already; the additional 15 mL TOP in B is separate','Se shot is consumed in stock preparation, not injected as another elemental reagent','10-mL workup aliquot is neither entire batch nor monitoring aliquot volume','Solvent alternatives and optional exchange chemicals are not all mandatory inputs']},
 'observations':observations,
 'unresolved_links':[
  {'from':'all characterization observations','to':['murray1993.protocol.cdse.method1','murray1993.protocol.cdse.method2'],'status':'unestablished','reason':'No complete figure-specific synthesis schedule/batch mapping; do not assign just because the paper or webpage contains both'},
  {'from':'figure_5 optical 3.5-nm sample','to':'figure_6 TEM 3.5-by-3.0-nm sample','status':'identity_unestablished','rule':'Neither assert same specimen nor assert physically distinct specimens solely from separate figure records'},
  {'from':'figure_3 optical series','to':'figure_11 XRD series','status':'identity_unestablished','rule':'Different size-label arrays; cannot zip by array index or automatically join equal sizes'},
  {'from':'m2.small.product','to':'figure_3/figure_11 1.2-nm panels','status':'plausible_but_not_explicitly_verified','rule':'Approximate size match alone does not establish provenance'},
  {'from':'workup 300 mg capped powder','to':'Method 2 specific product recovery','status':'not_established','rule':'Preserve common-workup scope'}],
 'structure_training_policy':{
  'experimental_product_atomic_coordinates':None,
  'exact_CIF_to_complete_recipe_eligible_pairs':0,
  'reference_bulk_CIF':{'record_type':'independent_experimental_bulk_reference','doi':'10.1107/S0567739477000977','cod_id':'9016056','measured_on_Murray_product':False,'allowed_use':['visual reference','external prior with explicit provenance'],'forbidden_use':['ground-truth atomic coordinates of Murray product','proof of exact 1993 recipe-to-CIF correspondence']},
  'illustrative_cluster':{'record_type':'derived_illustrative_structure','composition':'Cd288Se294','atom_count':582,'envelope_nm':[3.5,3.0],'source_of_envelope':'Figure 6 TEM dimensions','source_of_atoms':'separate bulk-reference lattice','training_ground_truth':False,'vacuum_cell_angstrom':[80,80,80],'caveats':structure_manifest['clusterCaveats']},
  'paper_level_structural_claim':{'value':'predominantly wurtzite, slightly prolate, stacking faults and possible surface disorder','source_locator_id':'overall_structure','label_scope':'author interpretation of study; not exact coordinates or automatically a route-specific specimen label'},
  'small_cluster_exception':{'size_quantity_id':'m2.small.product.size','polytype_label':None,'reason':'original authors state bulk wurtzite/zincblende distinction is not meaningful for smallest clusters','source_locator_id':'small_structure'}},
 'precursor_preparation_boundary':{
  'separate_review_file':str(ASSETS/'murray1993-precursor-method2-review.json').replace('\\','/'),
  'Murray_references':['3a: Steigerwald et al.; source bibliography prints 1987, verified publication year 1988','4: Detty and Seidler 1982, DOI 10.1021/jo00346a041'],
  'one_to_one_reference_to_chalcogen_assignment':'not explicitly printed; shared citation group',
  'storage_Murray':{'quantity_id':'m2.precursor.storage_temperature','environment':'drybox'},
  'steigerwald_1988_separate_record':{'id':'steigerwald1988.precursor.tms2se.thf_example','record_type':'external_partial_precursor_preparation','inputs':[{'chemical':'selenium powder','mass':q(0.53,'g','steigerwald1988'),'amount':q(6.7,'mmol','steigerwald1988',status='unit_normalized',note='Original 6.7 mg-atom')},{'chemical':'lithium triethylborohydride in THF','volume':q(13,'mL','steigerwald1988'),'amount':q(13,'mmol','steigerwald1988')},{'chemical':'chlorotrimethylsilane','mass':q(1.45,'g','steigerwald1988'),'amount':q(13,'mmol','steigerwald1988')}],'product':{'chemical':'(TMS)2Se','solvent':'THF','concentration':q(0.3,'mol/L','steigerwald1988',approximate=True)},'storage_in_that_paper':'0 C drybox; does not override Murray -35 C','sequence_temperature_duration_total_THF_volume_yield':'not provided in this precursor example','Murray_injection_stock_identity':'unestablished','downstream_HgSe_reaction_excluded':True},
  'Detty_1982_full_procedure_status':'not directly verified; identity only',
  'Beecher_2014':'Separate later route uses isolated Li2Se then TMSBr. Never use its conditions or its independently scaled example steps to complete Murray silently.'},
 'other_variants_plan':[
  {'suggested_id':'murray1993.protocol.cdte.method1','action':'separate material/protocol record if CdTe is in scope','quantity_ids':['m1.cdte.topte.stock_concentration','m1.cdte.injection.temperature','m1.cdte.growth.temperature'],'batch_id':None,'copy_CdSe_yield_or_figures':False},
  {'suggested_id':'murray1993.protocol.cds.method2','action':'separate material/protocol modification if CdS is in scope','precursor':'(TMS)2S, Fluka, used as purchased','quantity_ids':['m2.cds.growth.temperature'],'batch_id':None},
  {'suggested_id':'murray1993.protocol.cdte.method2','action':'separate material/protocol modification if CdTe is in scope','precursor':'(BDMS)2Te, formula C12H30Si2Te','storage':'-35 C drybox','batch_id':None},
  {'action':'CdS and CdTe small-species approximately 100 C cases may each have partial variant records','source_locator_id':'m2','same_observation_sentence_as_CdSe':True,'independent_batch_count':None},
  {'action':'Do not manufacture a separate complete synthesis recipe for every Figure 3 or Figure 11 size','reason':'No sample-specific operation settings or trajectories supplied'}],
 'deduplication_and_splits':{'source_group_id':'doi:10.1021/ja00072a025','protocol_family_id':'murray1993.hot_injection','same_split_ids':[r['id'] for r in records]+['all child observations and figure-panel records','all page-generated variants','copied common procedures'],'precursor_family_links':['doi:10.1021/ja00218a008','doi:10.1021/jo00346a041'],'counting':'Count eligible evidence-linked examples per task separately from literature records, pages, operations and physical experiments. Physical experiment count is unknown.'},
 'migration_warnings':[
  'Current method1/method2 JSON quantity strings and two-column fields need typed normalization; do not use UI labels as semantic keys.',
  'Current Method 2 JSON embeds the common purification block and its approximately 300 mg recovery without machine-readable route qualification. Move to shared procedure and keep routeAssignment null.',
  'Current Method 2 JSON puts 0.3 M THF in the stocks list beside the injection precursor. Move it to external precursor preparation with relation=reference, not relation=actual_input_stock.',
  'Current characterization sample_id values are generated observation identifiers, not reported batch IDs.',
  'Current illustrative CIF and measured bulk reference must be explicitly excluded from product-structure supervision.',
  'Legacy extraction calls reactor medium a bath and recommends separate figure examples: retain reaction-flask temperature semantics, and never equate separate observation records with proven distinct physical samples.',
  'Missing original SI is not evidence no SI existed; status remains not located or verified.'
 ],
 'validation':{'all_sources_and_records_read_only':True,'created_files_outside_site_checkout':True,'new_experimental_batch_claims':0}
}

OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Referential checks are migration integrity checks, not evidence of experimental reproducibility.
record_ids={r['id'] for r in records}
operation_ids={o['id'] for o in ops}
entity_ids={e['id'] for e in entities}|set(states)
for o in ops:
    assert o['source_locator_id'] in sources, o['id']
    assert set(o['inputs']+o['outputs']) <= entity_ids, o['id']
    assert set(o['quantity_ids']) <= set(Q), o['id']
    assert set(o['depends_on']) <= operation_ids, o['id']
for r in records:
    assert r['physical_experiment_id'] is None
    assert set(r['operation_ids']) <= operation_ids
assert len(operation_ids)==len(ops)
assert len(record_ids)==len(records)
json.loads(OUT.read_text(encoding='utf-8'))
print(json.dumps({'file':str(OUT),'records':len(records),'quantities':len(Q),'operations':len(ops),'observations':len(observations),'bytes':OUT.stat().st_size}))
