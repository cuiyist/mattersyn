"""Apply independent source-audit corrections and import attributed benchmark rows."""
import json,sys,copy,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]/'recipe-atlas'
sys.path.insert(0,str(ROOT/'scripts'))
from record_helpers import *
P=ROOT/'data/records'
def read(n):return json.loads((P/(n+'.json')).read_text(encoding='utf-8'))
def save(r):(P/(r['record_id']+'.json')).write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def by(items,key='id'):return {x[key]:x for x in items}

r=read('nakonechnyi-2017-zb-cdse-core');ops=by(r['operations']);e=ops['s2']['evidence']
ops['s2']['environment']=fact('ambient conditions',e,note='Retain author wording; humidity and atmospheric composition are not quantified.')
ops['s2']['endpoint']=fact('total dissolution of CdO',e)
m=by(r['materials']);m['oleic_acid']['role']='surface_ligand'
m['selenium_dispersion']['name']='Black selenium powder';m['selenium_dispersion']['formula']='Se'
r['materials'].append(material('ode_se_dispersion','1-Octadecene','C18H36','solvent','synthesis',e,{'volume':qty(unit='mL',evidence=e)},['Carrier for 0.24 mmol Se; volume unreported.']))
r['stocks'].append({'id':'se-ode-stock','name':'Selenium dispersion in 1-octadecene','components':[{'material_id':'selenium_dispersion','quantities':m['selenium_dispersion']['quantities']},{'material_id':'ode_se_dispersion','quantities':{'volume':qty(unit='mL',evidence=e)}}],'concentrations':{'concentration':qty(unit='mol/L',evidence=e)},'preparation_operation_ids':[],'scope':'Separate black-Se solid and ODE carrier; preparation mechanics and carrier amount unreported.','evidence':e})
ops['s3']['inputs']=['clear_cadmium_solution','se-ode-stock'];ops['s5']['inputs'].append('isopropanol')
ops['s7']['parameters']['centrifugation_force']=qty(3000,'g_relative',e,'inherited',basis='Paragraph-wide centrifugation condition')
states=by(r['material_states'])
for op in r['operations']:
 for output in op['outputs']:
  if output in states and output not in op['inputs']:states[output]['parent_ids']=op['inputs']
for material_ in r['materials']:
 for q in material_['quantities'].values():
  if q['unit']=='mL per purification cycle':q['unit']='mL';q['basis']='per purification cycle'
for link in r['context_links']:link['url']=r['sources'][0]['url']
save(r)

for name in ['peng-2000-cdse-typical','peng-2000-cdse-high-aspect']:
 r=read(name);ops=by(r['operations']);states=by(r['material_states']);e=ev('peng2000','Main p. 60; typical synthesis paragraph')
 states['collected']['name']='Stopped reaction mixture';states['collected']['kind']='reaction_batch'
 if name.endswith('typical'):
  ops['heat']['inputs']=['topo'];ops['heat']['optional_inputs']=['hpa'];states['hot-medium']['parent_ids']=['topo']
  ops['heat']['description']='Use TOPO alone or TOPO with HPA; HPA is an optional additive across this typical family. Select one paired temperature alternative.'
  by(r['materials'])['hpa']['notes'].append('Optional additive: source specifies TOPO or TOPO + HPA.')
 else:
  ops['heat']['description']='High-aspect variant: 8% HPA in TOPO and 360 °C injection temperature. Independent medium mass and post-injection setpoint are unreported.'
  for oid in ['grow','reinject','stop']:
   ops[oid]['branch']='inherited_typical_context';ops[oid]['evidence']=e
   ops[oid]['description']='Context inherited from the typical synthesis paragraph; not independently specified for this variant. '+ops[oid]['description'].replace('Paired post-injection temperatures are alternatives, not a time trace. ','')
  r['products'][0]['morphology']=fact('high-aspect-ratio rods',ev('peng2000','Main p. 60; high-aspect-ratio synthesis paragraph'),note='Qualitative outcome; no specific figure dimensions assigned to this formulation.')
 for link in r['context_links']:link['url']=r['sources'][0]['url']
 save(r)

r=read('murray-1993-cdse-method2');s=by(r['material_states'])['state.m2.injection'];s['parent_ids']=['state.m2.tms2se.stored'];s['name']='Unquantified Method 2 injection formulation; remaining composition unresolved';save(r)
r=read('murray-1993-cdse-size-selection');o=by(r['operations'])['selection.repeat'];o['endpoint']=fact('no further sharpening of optical absorption',o['evidence']);save(r)
for name in ['murray-1993-cdse-method1','murray-1993-cdse-isolation']:
 r=read(name);e=ev('murray1993','Main p. 8707; Isolation and Purification of Crystallites')
 r['products'][0]['surface']=fact('TOP/TOPO-capped',e,note='Authors’ surface description; coverage, exact species and binding geometry unresolved.')
 if name.endswith('isolation'):
  r['products'][0]['material_state_id']='state.workup.powder'
  r['measurements'].append(measurement('capped-powder-mass',r['products'][0]['sample_id'],'capped_product_mass',qty(300,'mg',e,approximate=True,basis='per 10 mL reaction aliquot'), 'Isolated capped powder mass',e,'Shared isolation example, not whole-batch yield or Method 2-specific result.'))
 else:
  e=ev('murray1993','Main p. 8707; Method 1, initial injection observations')
  by(r['operations'])['m1.inject']['parameters']['observed_post_injection_temperature']=qty(180,'degC',e,approximate=True,basis='Observed temperature immediately after injection; not a setpoint')
  prod=product('m1-initial-observation','CdSe',e,link='general_context',state='state.m1.reaction.initial',notes=['Initial reaction observation, not a final isolated size target.']);r['products'].append(prod)
  r['measurements'].append(measurement('initial-absorption-feature',prod['sample_id'],'initial_absorption_feature',qty(unit='nm',evidence=e,minimum=440,maximum=460),'Absorption spectroscopy',e,'Immediately after injection; no linkage to a final isolated particle size.'))
 save(r)

benchmark=json.loads((HERE/'pbs2019-selected-100.json').read_text(encoding='utf-8'));src=benchmark['source'];defs={f['name']:f for f in benchmark['inputFeatureDefinitions']}
for row in benchmark['records']:
 sid='voznyy2019';loc='Dataset SI full.dat, row '+str(row['sourceRowNumber'])+' (one-based, excluding header)';e=ev(sid,loc)
 source_=source(sid,src['paperDoi'],'Machine Learning Accelerates Discovery of Optimal Colloidal Quantum Dot Synthesis','Voznyy, O.; Levina, L.; Fan, J. Z.; et al.',2019,'Official published numeric dataset verified; full per-run procedures not individually audited')
 source_['main_status']='Dataset columns and benchmark context checked against primary paper and author code; numeric row verified against source file'
 source_['reuse_status']=src['attribution']+' '+src['changes']+' License: '+src['license']['url']
 r=record(row['id'],'PbS hot injection · published experiment '+str(row['sourceRowNumber']),'PbS','lead chalcogenides','hot injection',source_,loc,kind='experiment');r['collection']='published_benchmark'
 r['lineage']['recipe_family']='pbs2019-'+row['recipeGroupId']
 r['lineage']['batch_id']=None
 features={k:qty(v,defs[k]['unit'],e,basis=defs[k]['description']) for k,v in row['inputFeatures'].items()}
 r['materials']=[material('lead-oleate','Lead oleate stock','C36H66O4Pb','metal_precursor','synthesis',e,{'stock_volume':features['lead_oleate_stock_volume']},['Stock concentration is not encoded in this row.']),material('ode','1-Octadecene','C18H36','solvent','synthesis',e,{'reaction_volume':features['ode_reaction_volume'],'sulfur_stock_volume':features['ode_sulfur_stock_volume']}),material('oleylamine','Oleylamine','C18H37N','ligand','synthesis',e,{'volume':features['oleylamine_volume']}),material('tms2s','Bis(trimethylsilyl)sulfide','C6H18SSi2','chalcogen_precursor','synthesis',e,{'volume':features['bis_trimethylsilyl_sulfide_volume']}),material('chloride','Author-pooled chloride parameter',None,'additive','synthesis',e,{'at_high_temperature':features['chloride_high_temperature_concentration'],'at_60c':features['chloride_60c_concentration']},['Chemical identities are pooled and some concentrations rescaled by the authors; no exact historical chloride species is assigned.'])]
 r['material_states']=[state('reported-run','Reported experimental row',kind='reaction_batch')]
 r['operations']=[operation('reported-features','published_experiment_features','Reported synthesis features',e,[],['reported-run'],parameters=features,description='This row specifies nine model inputs, not a complete chronological protocol. The outdoor temperature proxy is not a reaction condition. Numeric zero is retained as reported; missing duration, phase and coordinates remain unknown.')]
 sample=product('reported-outcome','PbS',e,link='explicit',state='reported-run',notes=['Source-row identity is known; physical batch identifiers and exact atomic structure are not supplied.',row['cohortBasis']])
 sample['source_sample_label']='full.dat row '+str(row['sourceRowNumber']);r['products']=[sample]
 for key,prop in [('absorption_peak_wavelength','absorption_peak'),('absorption_peak_valley_ratio','absorption_peak_valley_ratio')]:
  value=row['outcomes'][key];q=qty(value['value'],value['unit'],e,qualifier='Failure placeholder excluded from continuous target' if row['failurePlaceholder'] else '')
  r['measurements'].append(measurement(prop,sample['sample_id'],prop,q,'Optical absorption',e,'Author-published row; acquisition details not individually resolved.'))
 r['quality'].update(review_status='structured_data_verified',review_scope='Published experimental row checked against the source dataset; not an individually curated complete recipe or laboratory reproduction.',missing_fields=['Per-run growth duration','Exact chloride reagent identity','Sample-resolved crystal phase and atomic coordinates','Direct particle-size measurement','Complete stock preparation, workup and storage for this row'],requested_tasks=['optical_outcome'],experimental_outcome='reported_failure' if row['failurePlaceholder'] else 'reported_product')
 r['quality']['conflicts']=['Outdoor temperature is a seasonal proxy, not measured laboratory temperature.','Author-defined cohort: '+row['authorRuleCohort']+'; not verified chronology.','Source full.dat SHA-256: '+row['sourceDataSha256']]
 if row['failurePlaceholder']:r['quality']['conflicts'].append('Author failure code: 650 nm and peak/valley 0.5 are placeholders, not measured continuous outcomes. Both targets are null.')
 r['context_links']=[{'label':'Official source dataset and license','url':src['datasetUrl'],'relation':src['attribution']+' '+src['changes']}]
 save(r)

for p in P.glob('*.json'):
 r=json.loads(p.read_text(encoding='utf-8'));r.setdefault('collection','reviewed_literature');save(r)
allrecords=[json.loads(p.read_text()) for p in P.glob('*.json')];curated={s['doi'] for r in allrecords for s in r['sources']}
queue=json.loads((HERE/'diverse-pilot-source-queue.json').read_text(encoding='utf-8'));candidates=[]
for x in queue['queue']:
 if x['doi'] in curated:continue
 candidates.append({'priority':x['priority'],'doi':x['doi'],'url':x['doiUrl'],'title':x['title'],'year':x['year'],'family':x['candidateMaterialFamily'],'composition':x['candidateComposition'],'status':'first_page_screened_unreviewed','training_eligible':False,'main_identity_confidence':x['mainIdentityConfidence'],'si_pairing_confidence':x['mainSiMatchConfidence'],'next_action':'Verify full main/SI contents and extract one coherent protocol with sample links.'})
(ROOT/'data/pilot-source-queue.json').write_text(json.dumps({'version':'0.1.0','scope':'Remaining candidates from 42 prioritized local papers; initial screening only. Local file paths excluded.','candidates':candidates},indent=2),encoding='utf-8')
for name in ['pbs2019-baseline-report.json','pbs2019-benchmark-validation.json','pbs2019-sample-selection.json']:
 shutil.copyfile(HERE/name,ROOT/'dist/data'/('baseline-report.json' if name=='pbs2019-baseline-report.json' else name))
print('Canonical records:',len(allrecords),'remaining source candidates:',len(candidates))
