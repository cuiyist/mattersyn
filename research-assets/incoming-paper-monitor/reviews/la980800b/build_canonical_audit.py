"""Independent supplied-main source-to-eight-record audit. Private files only."""
from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
paths=sorted((B/'canonical-drafts').glob('*.json'));records={p.stem.removeprefix('stiger-1999-'):read(p)for p in paths}
draft=read(B/'characterization-draft.json');checks=[];findings=[]
def check(n,b,detail=''):checks.append({'name':n,'passed':bool(b),'detail':detail})
def finding(i,title,b,detail):findings.append({'id':i,'title':title,'status':'resolved'if b else'open','detail':detail})
def op(k,i):return next(o for o in records[k]['operations']if o['id']==i)
def mat(k,i):return next(m for m in records[k]['materials']if m['id']==i)
def stock(k,i):return next(s for s in records[k]['stocks']if s['id']==i)
def val(k,i,p,v):return op(k,i)['parameters'][p]['value']==v
check('Expected8records36operations145measurements',len(records)==8 and sum(len(r['operations'])for r in records.values())==36 and sum(len(r['measurements'])for r in records.values())==145)
for k,r in records.items():
 check(k+' correct source1999',r['sources'][0]['doi']=='10.1021/la980800b'and r['sources'][0]['year']==1999)
 check(k+' private unreviewed and training disabled',r['quality']['review_status']=='imported_unreviewed'and not r['quality']['requested_tasks'])
 check(k+' no invented physicalbatch',all(p.get('batch_id')is None for p in r['products']))
 check(k+' every operation source-linked',all(o['evidence']for o in r['operations']))
 check(k+' no unreported separation apparatus',not any(o['action']in ['centrifugation','filtration']for o in r['operations']))
 if k not in ['electrodeposition','open-circuit-control','silver-free-pulse-control']:check(k+' intended synthesis target not inferred for analysis',r['intended_target']['composition']['value']is None and r['intended_target']['host']['value']is None)
r=records['electrodeposition']
check('Only one full synthesis route',sum(x['record_type']=='literature_protocol'for x in records.values())==1)
check('Sb-doped n++ substrate dimensions and concentration',mat('electrodeposition','si-npp')['quantities']['dopant_number_density']['value']==1e20 and mat('electrodeposition','si-npp')['quantities']['wafer_diameter']['value']==5 and mat('electrodeposition','si-npp')['quantities']['coupon_area']['value']==1)
check('Ohmic contact distinct from Agfeed',mat('electrodeposition','ga-in')['formula']is None and mat('electrodeposition','silver-paint')['formula']is None and op('electrodeposition','paint')['inputs']==['ohmic-contact','silver-paint'])
check('Backside scratch beforecontact',op('electrodeposition','scratch')['depends_on']==['cut']and op('electrodeposition','contact')['depends_on']==['scratch'])
check('Acid oxidation80C~10min',val('electrodeposition','oxidize','temperature',80)and val('electrodeposition','oxidize','duration',10)and op('electrodeposition','oxidize')['parameters']['duration']['approximate'])
acid=mat('electrodeposition','h2so4')['quantities']['reagent_concentration'];check('H2SO495–98percent sourcebasisnotinvented',acid['minimum']==95 and acid['maximum']==98 and acid['unit']=='%')
check('HF49percent supplied reagent',mat('electrodeposition','hf')['quantities']['reagent_concentration']['value']==49)
etch=stock('electrodeposition','etchant');check('1:1HFethanol volume ratio and5min',etch['concentrations']['hf_volume_parts']['value']==1 and etch['concentrations']['ethanol_volume_parts']['value']==1 and val('electrodeposition','etch','duration',5))
check('Rinses andnoinventedpreplateairdry',op('electrodeposition','rinse2')['depends_on']==['etch']and op('electrodeposition','mount')['depends_on']==['rinse2','purge'])
check('NoH2O2orotherinventedoxidant',not any(m.get('formula')=='H2O2'for m in r['materials']))
check('Silverperchloratehydrate retained',mat('electrodeposition','agclo4')['formula']=='AgClO4·H2O')
check('LiClO4hydrate notinvented',mat('electrodeposition','liclo4')['formula']=='LiClO4')
for k,rr in records.items():
 for mm in rr['materials']:
  if mm['id'] in ['agclo4','liclo4']:
   pp=mm['quantities']['reagent_purity'];check(k+' '+mm['id']+' supplier purity distinct from bath',pp['value']==(99.9 if mm['id']=='agclo4' else 99.99) and pp['unit']=='%' and 'supplier specification' in pp['basis'] and 'not a measured bath composition' in pp['basis'] and 'Main PDF p. 2' in pp['evidence'][0]['locator'])
ps=stock('electrodeposition','plating-solution')['concentrations'];check('Recipe bath1mMAg0.1MLi',ps['agclo4_molarity']['value']==1 and ps['agclo4_molarity']['unit']=='mmol/L'and ps['liclo4_molarity']['value']==.1)
check('N2purge doesnotclaimdryglovebox','water not rigorously excluded'in op('electrodeposition','purge')['environment']['value'])
check('Exposed area0.28notcoupon1',val('electrodeposition','mount','exposed_electrode_area',.28))
check('Working/reference/counter materialroles',op('electrodeposition','mount')['inputs']==['prepared-electrode','purged','ag-wire','pt-wire'])
qp=op('electrodeposition','pulse')['parameters'];check('−800mVAgscale2–25msfromopencircuit',qp['applied_potential']['value']==-800 and 'silver'in qp['applied_potential']['basis']and qp['duration']['minimum']==2 and qp['duration']['maximum']==25 and 'open circuit'in op('electrodeposition','pulse')['label'])
check('PostpulseOCPremoveMeCNairdryorder',[op('electrodeposition',x)['depends_on']for x in ['open-circuit','remove','rinse-product','dry-product']]==[['pulse'],['open-circuit'],['remove'],['rinse-product']])
check('Noextra24h drying orsolutiontemperature',not any(p in op('electrodeposition',i)['parameters']for i in ['mix','purge','pulse','dry-product']for p in ['temperature','duration'])or('duration'in qp and set(qp)=={'applied_potential','duration'}and not op('electrodeposition','dry-product')['parameters']))
check('Eight source cohortoptionsnot8inventedproducts',len(r['condition_options'])==8 and len(r['products'])==1 and [o['parameters']['duration']['value']for o in r['condition_options']]==[2,7,12,22,5,10,15,25])
check('Fullroute phase explicitly transferredSAEDcontext','transferred specimen pulse duration unspecified'in r['products'][0]['phase']['note'])
cv=records['cyclic-voltammetry'];check('BothdopingclassesinCV',mat('cyclic-voltammetry','si-npp')['quantities']['dopant_number_density']['value']==1e20 and mat('cyclic-voltammetry','si-n')['quantities']['dopant_number_density']['value']==1e15)
check('CV1vs10mM unresolved',stock('cyclic-voltammetry','plating-solution')['concentrations']['agclo4_molarity']['value']is None)
check('CV alternatives not combined experiment',cv['products'][0]['composition']['value']is None and 'alternative'in op('cyclic-voltammetry','prepare')['description'])
check('CV20mVsandnosweepwindowinvented',val('cyclic-voltammetry','scan','scan_rate',20)and set(op('cyclic-voltammetry','scan')['parameters'])=={'scan_rate'})
check('CVphysicalSCE vsreportedAgscale','SCE reference physically used'in stock('cyclic-voltammetry','blank-electrolyte')['scope'])
check('Transient1.5mMseparatefromrecipe',stock('current-transients','plating-solution')['concentrations']['agclo4_molarity']['value']==1.5)
check('Transient3potentialsandno200mspulseassumption',[o['parameters']['applied_potential']['value']for o in records['current-transients']['condition_options']]==[-600,-800,-1000]and not op('current-transients','step')['parameters'])
check('Figure4fitnotforcedontoFigure3bath','separate fit context'in op('current-transients','record')['description'])
check('AFM5random3umfields andfrequency90–120',val('afm','scan','fields_per_sample',5)and val('afm','scan','scan_width',3)and op('afm','scan')['parameters']['nc_resonance_frequency']['minimum']==90 and op('afm','scan')['parameters']['nc_resonance_frequency']['maximum']==120)
check('AFMheightnotlateraldiameter','lateral widths are not true diameters'in op('afm','analyze')['description'])
check('TEMgoldcarbongrid notCu','gold'in mat('tem-saed','carbon-grid')['name'].lower())
check('TEM200keVsourcewording retained',val('tem-saed','image','source_accelerating_voltage_label',200)and op('tem-saed','image')['parameters']['source_accelerating_voltage_label']['unit']=='keV')
check('SAED500mmand10umaperture',val('tem-saed','diffract','camera_length',500)and val('tem-saed','diffract','selected_area_aperture',10))
check('TEM product is transferred carbon-supported gold-grid specimen',records['tem-saed']['products'][0]['composition']['value']=='Ag nanocrystals mechanically transferred from Si(100) to a carbon-supported gold TEM grid' and records['tem-saed']['products'][0]['material_state_id']=='transferred')
for k in ['open-circuit-control','silver-free-pulse-control']:
 rr=records[k];check(k+' noAgproductmetadata',rr['material']['elements']==['Si']and rr['material']['formula']=='Si'and 'control'in rr['intended_target']['composition']['value'])
 check(k+' control-specificdopingnotinvented','not reported'in rr['intended_target']['host']['value'])
check('OCPcontrol noappliedpulse',op('open-circuit-control','immerse')['action']=='open_circuit_exposure'and not op('open-circuit-control','immerse')['parameters'])
check('Agfreepulseunknownpotentialandduration',all(q['value']is None for q in op('silver-free-pulse-control','pulse')['parameters'].values()))
check('Agfreecontrol noAgreagent/reference',not any(m['id']in ['agclo4','ag-wire']for m in records['silver-free-pulse-control']['materials']))
check('Controlroughnessstrictupperbound','less than'in records['silver-free-pulse-control']['measurements'][0]['value']['qualifier'])

# All143 source rows were manually read against nine-page source inventory before this mapping audit.
# The following checks verify their preservation, not the truth of an unreviewed extraction.
c=records['characterization'];measurements={m['id']:m for m in c['measurements']};products={p['sample_id']:p for p in c['products']}
check('All143reviewedrows onceonly',len(measurements)==143 and len(c['measurements'])==143 and set(measurements)=={x['id']for x in draft['measurement_rows']})
for row in draft['measurement_rows']:
 m=measurements[row['id']];sid='shared-'+'-and-'.join(row['sample_id'])if isinstance(row['sample_id'],list)else row['sample_id']
 good=m['sample_id']==sid and m['property']==row['property']and bool(m['evidence'])
 if 'quantity'in row:
  q=row['quantity'];v=m['value'];good=good and v['value']==q.get('value')and v['minimum']==q.get('lower_bound')and v['maximum']==q.get('upper_bound')and v['unit']==(q.get('unit')or'')and v['basis']==row['basis']and v['raw_text']==q.get('raw_text','')and v['approximate']==q.get('approximate',False)
 else:good=good and m['value']['value']==row['fact']and 'Evidence basis: '+row['basis']in m['conditions']
 check(row['id']+' audited transcription and specimen scope preserved',good)
 if row['scope_type']in ['cited_context','model_context','method_context']and sid!='tem-saed-context':check(row['id']+' not fabricatedphysicalproduct',products[sid]['composition']['value']is None)
check('OnlytransferredSAEDcohortassignedFCC',all(p['phase']['value']is None for sid,p in products.items()if sid!='tem-saed-context'))
for label,value in [('111',2.37),('200',2.04),('220',1.42),('311',1.22)]:check('MeasuredSAED'+label,measurements['char-saed-'+label]['value']['value']==value and measurements['char-saed-'+label]['sample_id']=='tem-saed-context')
check('ICDDreference1112.32notrepaired',measurements['char-reference-d-111']['value']['value']==2.32 and measurements['char-reference-d-111']['sample_id']=='icdd-reference')
check('Expectedintensitiesnotmeasuredsample',all(measurements['char-reference-intensity-'+x]['sample_id']=='icdd-reference'for x in ['111','200','220','311']))
check('F5mCandF7uCbothpreserved',measurements['char-f5-a-charge']['value']['unit']=='mC/cm^2'and measurements['char-f7-1-charge']['value']['unit']=='uC/cm^2')
check('HistogrammeansandSDsourceconflictretained',[measurements[f'char-f7-{j}-mean']['value']['value']for j in range(1,5)]==[2.2,7.5,13.5,17.1]and [measurements[f'char-f7-{j}-sigma']['value']['value']for j in range(1,5)]==[2.4,4.3,5.3,6.1]and measurements['char-histogram-small-body-height']['value']['value']==2.4)
check('RatesmsversussourceSummarysretained',measurements['char-nucleation-rate-body']['value']['unit']=='cm^-2 ms^-1'and measurements['char-summary-rate']['value']['unit']=='cm^-2 s^-1')
check('RnotR2and modelNnotmeasuredparticlecount',measurements['char-transient-fit-R-inset']['value']['value']==.99947 and measurements['char-transient-site-density']['value']['status']=='author_derived')
check('Eq3constantNnotphysicalfixednucleationcount',products['height-charge-series']['composition']['value']is None and 'instantaneous'in measurements['char-height-Q-fit-density']['conditions'])
check('NoSI/fullsourcepublicationpromotion','not located or verified'in c['quality']['review_scope']and all(not rr['quality']['requested_tasks']for rr in records.values()))
finding('F01','Controls must not inherit Ag product or n++ substrate metadata',all(records[k]['material']['elements']==['Si']and 'not reported'in records[k]['intended_target']['host']['value']for k in ['open-circuit-control','silver-free-pulse-control']),'Ag-free control has no introduced silver; open-circuit background particles have unknown chemistry. Source does not separately identify control doping.')
finding('F02','Analytical contexts must not imply one intended Ag synthesis',all(records[k]['intended_target']['composition']['value']is None and records[k]['intended_target']['host']['value']is None for k in ['cyclic-voltammetry','current-transients','afm','tem-saed','characterization']),'CV, transferred TEM and mixed analytical/model contexts have cohort-specific conditions.')
cal=op('tem-saed','calibrate');finding('F03','HOPG calibration must not rewrite Ag diffraction retrospectively',cal['inputs']==['hopg']and not cal['depends_on'],'Source describes microscope astigmatism correction; actual ordering unreported. Supporting calibration branch is independent of measured Ag data.')
boundids=['char-transient-fast-rise','char-aqueous-instability','char-coverage-study-range','char-blank-transient-decay','char-density-time-limit']
finding('F04','Bounds need visible directional qualifiers',all(measurements[mid]['value']['qualifier'].strip()for mid in boundids),'Raw source t<30ms, diameter<5nm, strict0.005<Γ<0.20, within3ms and no observations>30ms must remain visible beyond raw_text. Preserve original values, not reconstructed equality.')
out={'status':'passed'if all(x['passed']for x in checks)and not any(f['status']=='open'for f in findings)else'must_fix','source_id':'stiger1999','scope':'Independent full supplied-main source-to-eight-record scientific audit. All9pages text+visual read; all143characterization rows individually reviewed; all36operations/material flows checked.','source_audit_sha256':sha(B/'source-audit.json'),'characterization_draft_sha256':sha(B/'characterization-draft.json'),'records':[{'record_id':r['record_id'],'basename':r['record_id']+'.json','sha256':sha(B/'canonical-drafts'/(r['record_id']+'.json'))}for r in records.values()],'record_count':len(records),'operation_count':36,'measurement_count':145,'check_count':len(checks),'checks':checks,'findings':findings,'open_findings':[f for f in findings if f['status']=='open'],'scope_limits':['202sourceunits include citedpriorcontext, figures and intuition represented outsidecanonicalmeasurements. No claim allpapercontentisnumericrecipeoutput.','Eight condition options describe source Fig5/7 cohorts; they are not eight independently identified batches.','Comparison procedures use explicitly stated alternatives, not combined experiments; no operation training tasks enabled.','SI remains unverified. Root owns reader rendering, finalintegration andpublication.']}
(B/'canonical-records-audit.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
(B/'canonical-records-audit.md').write_text('# Independent Stiger canonical audit\n\nStatus: **'+out['status']+'**.8records,36operations,145measuremententries;'+str(len(checks))+'boundedchecks.\n\n'+ '\n'.join('- '+f['id']+' '+f['status']+': '+f['title']+'. '+f['detail']for f in findings)+'\n\nAll9suppliedmainpagesreadtextandvisually;all143characterizationrowschecked. ExactcurrentrecordhashesinJSON. SIunverified;notrainingorpublicationpromotion.\n',encoding='utf8')
print(json.dumps({'status':out['status'],'checks':len(checks),'failed':[c for c in checks if not c['passed']],'open_findings':out['open_findings']},indent=2))
