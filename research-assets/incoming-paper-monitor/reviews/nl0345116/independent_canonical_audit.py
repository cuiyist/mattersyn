from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,runpy
B=Path(__file__).resolve().parent;load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();C=[]
R={p.stem.removeprefix('sashchiuk-2004-'):load(p)for p in(B/'canonical-drafts').glob('*.json')}
def ck(n,v):C.append({'check':n,'passed':bool(v)})
def op(r,i):return next(o for o in R[r]['operations']if o['id']==i)
def m(r,i):return next(x for x in R[r]['measurements']if x['id']==i)
def q(n,x,v=None,lo=None,hi=None,u=None):
 ck(n+'/values',(x.get('value'),x.get('minimum'),x.get('maximum'))==(v,lo,hi))
 if u is not None:ck(n+'/unit',x.get('unit')==u)
def p(r,o,k,**kw):q(r+'/'+o+'/'+k,op(r,o)['parameters'][k],**kw)
def z(r,i,**kw):q(r+'/'+i,m(r,i)['value'],**kw)
g=runpy.run_path(str(B/'build_records.py'));generated=g['records']
for r in generated:ck(r['record_id']+'/actual data equals fully read authoring',r==R[r['record_id'].removeprefix('sashchiuk-2004-')]);ck(r['record_id']+'/schema',not g['validate_record'](r))
for name,v,expected in [('records',len(R),15),('operations',sum(len(r['operations'])for r in R.values()),47),('measurements',sum(len(r['measurements'])for r in R.values()),137),('materials',sum(len(r['materials'])for r in R.values()),42)]:ck(name,v==expected)
def walk(x,n):
 if isinstance(x,dict):
  for e in x.get('evidence',[]):ck(n+'/source',e['source_id']=='sashchiuk2004'and bool(e['locator']))
  for k,v in x.items():walk(v,n+'/'+str(k))
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,n+'/'+str(i))
routes=['individual-low','sphere-intermediate','wire-intermediate','wire-high']
for name,r in R.items():
 walk(r,name);mats={x['id']for x in r['materials']};states={x['id']for x in r['material_states']};stocks={x['id']for x in r['stocks']};ops={x['id']for x in r['operations']};samples={x['sample_id']for x in r['products']}
 ck(name+'/unknown batch',r['lineage']['batch_id']is None);ck(name+'/no source atomic geometry',r['structure_assets']==[]);ck(name+'/SI not fabricated','No SI used'in r['sources'][0]['si_status'])
 for x in r['measurements']:ck(name+'/'+x['id']+'/sample',x['sample_id']in samples)
 for x in r['operations']:
  ck(name+'/'+x['id']+'/inputs',set(x['inputs'])<=mats|states|stocks);ck(name+'/'+x['id']+'/outputs',set(x['outputs'])<=states);ck(name+'/'+x['id']+'/dependencies',set(x['depends_on'])<=ops)
 for x in r['products']:
  if x['material_state_id']:ck(name+'/'+x['sample_id']+'/physicalstate',x['material_state_id']in states)
 ck(name+'/training scope',r['quality']['requested_tasks']==(['precursor_selection','partial_protocol']if name in routes else[]))
for row in load(B/'canonical-record-manifest.json')['records']:ck(row['id']+'/manifest hash',row['sha256']==sha(B/'canonical-drafts'/(row['id']+'.json')))
for r,ratio in zip(routes,[[.25,.6,50],[.5,1.2,50],[.5,1.2,50],[1,2.5,50]]):
 mats={x['id']:x for x in R[r]['materials']};ck(r+'/lead formula unknown',mats['lead-chxbu']['formula']is None);ck(r+'/TOPO mixture unknown',mats['topo-reagent']['formula']is None);ck(r+'/TOPO molecule separate',mats['topo-component']['role']=='named_reagent_component')
 ck(r+'/mass ratios',[(x['material_id'],x['quantities']['relative_mass']['value'])for x in R[r]['stocks'][0]['components']]==list(zip(['selenium','lead-chxbu','tbp'],ratio)))
 for k,v in zip(['selenium_mass_part','lead_precursor_mass_part','tbp_mass_part'],ratio):p(r,'prepare-stock',k,v=v,u='mass parts')
 p(r,'prepare-stock','temperature',u='°C');p(r,'heat-topo','temperature',v=150,u='°C');p(r,'heat-topo','topo_mass',v=6,u='g');p(r,'injection','post_injection_temperature',v=118,u='°C');p(r,'injection','stock_injection_volume',u='mL');p(r,'injection','injection_duration',u='s')
 ck(r+'/glovebox gas unknown','gas identity not specified'in op(r,'prepare-stock')['environment']['value']);ck(r+'/mother argon',op(r,'heat-topo')['environment']['value']=='Argon flow')
 ck(r+'/no invented numeric target size',R[r]['intended_target']['size']['value']is None);ck(r+'/no picture-specific size on route',len(R[r]['measurements'])==1)
 ck(r+'/purity alternatives',[x['parameters']['purity']['value']for x in R[r]['condition_options']]==[90,99]);ck(r+'/no methanol whole batch',all('methanol'not in o['inputs']for o in R[r]['operations']))
 if r!='individual-low':p(r,'ramp','initial_temperature',v=118,u='°C');p(r,'ramp','target_temperature',v=150,u='°C');p(r,'ramp','ramp_rate',u='°C/min');p(r,'grow','temperature',v=150,u='°C')
p('individual-low','grow','temperature',v=118,u='°C');p('individual-low','grow','duration',v=15,u='min');p('individual-low','cool','target_temperature',v=70,u='°C');p('sphere-intermediate','grow','duration',lo=10,hi=60,u='min');p('wire-intermediate','grow','duration',v=90,u='min');p('wire-high','grow','duration',v=40,u='min')
ck('High40 explicitly unshown','not shown'in' '.join(R['wire-high']['quality']['conflicts']))
p('aliquot-workup','quench','methanol_volume',v=1,u='mL');p('aliquot-workup','withdraw','aliquot_volume',u='mL');p('aliquot-workup','repeat','cycle_count',u='cycles');ck('Quench only aliquot',op('aliquot-workup','quench')['inputs']==['aliquot','methanol'])
for o,k,v,u in [('deposit','grid_mesh',300,'mesh'),('tem','accelerating_voltage',200,'kV'),('hrtem','accelerating_voltage',300,'kV'),('sem','accelerating_voltage_methods',4,'kV'),('sem','accelerating_voltage_figure5_label',10,'kV'),('saed','accelerating_voltage',200,'kV'),('edax','accelerating_voltage',200,'kV')]:p('microscopy',o,k,v=v,u=u)
ck('EDAX unavailable','no EDAX spectrum'in op('microscopy','edax')['description']);ck('Microdiffraction unshown','not shown'in op('microscopy','microdiffraction')['description'])
ck('Analysis states not mixtures',all(s['kind']=='analysis_data'for s in R['microscopy']['material_states']if s['id'].endswith('-data')))
ck('Separate optical aliquots',next(s for s in R['absorption']['material_states']if s['id']=='optical-specimens')['kind']=='sample_set')
for t in[30,35,40]:z('absorption','time-'+str(t),v=t,u='min')
z('absorption','bands',v=2,u='bands');z('absorption','wavelengths',lo=1000,hi=1600,u='nm');z('absorption','energies',lo=.775,hi=1.240,u='eV');z('absorption','redshift',v=.04,u='eV');z('absorption','blueshift',v=.5,u='eV')
p('device-fabrication','hydrophobize','oxide_thickness',v=200,u='nm');p('device-fabrication','anneal','temperature',u='°C');p('device-fabrication','anneal','duration',u='min');p('device-fabrication','evaporate-contacts','titanium_thickness',u='nm');p('device-fabrication','evaporate-contacts','gold_thickness',u='nm')
ck('Device named silane',next(x for x in R['device-fabrication']['materials']if x['id']=='trimethylsilane')['formula']=='C3H10Si');ck('No measured gate sweep','No gate sweep'in m('device-fabrication','gate')['value']['value'])
p('electrical','measure','applied_electric_field',v=3.5e4,u='V/m');p('electrical','measure','temperature',u='°C')
for sid,w,l in [('square',110,700),('circle',60,1000),('triangle',150,1200)]:z('electrical',sid+'-width',v=w,u='nm');z('electrical',sid+'-length',v=l,u='nm')
for i,v,u in [('building-block',10,'nm'),('resistivity',.15,'Ω cm'),('conductivity',7,'Ω^-1 cm^-1'),('sem-scale',3,'µm')]:z('electrical',i,v=v,u=u)
z('individual-structure','size-range',lo=3.5,hi=10,u='nm');z('individual-structure','distribution',hi=10,u='%');ck('Strict spread<10',m('individual-structure','distribution')['value']['maximum_exclusive'])
for i,v,u in [('f1-time',5,'min'),('f1-temperature',118,'°C'),('f1-size',5,'nm'),('f1-spacing',3.05,'Å'),('f1-scale',5,'nm')]:z('individual-structure',i,v=v,u=u)
ck('5min is approximate',m('individual-structure','f1-time')['value']['approximate'])
for t,panel in[(10,'B'),(25,'C'),(40,'D')]:z('sphere-structure','f1'+panel+'-time',v=t,u='min');z('sphere-structure','f1'+panel+'-scale',v=200,u='nm')
z('sphere-structure','body-range',lo=50,hi=450,u='nm');z('sphere-structure','abstract-range',lo=50,hi=500,u='nm');z('sphere-structure','onset',v=5,u='min');z('sphere-structure','plateau',lo=50,u='min');ck('Plateau strict>50',m('sphere-structure','plateau')['value']['minimum_exclusive'])
for i,lo,hi,u in [('width-typical',60,150,'nm'),('length-typical',1,5,'µm'),('width-growth',20,150,'nm'),('orientation',1,2,'degree')]:z('wire-structure',i,lo=lo,hi=hi,u=u)
for i,v,u in [('junction-fraction',5,'%'),('f2a-scale',40,'nm'),('f2b-scale',500,'nm'),('f2b-time',90,'min'),('f2-cell',6.1,'Å'),('f3-cell',6.1,'Å'),('f3-fringe',3.05,'Å'),('f3-block',10,'nm'),('f3-scale',10,'nm')]:z('wire-structure',i,v=v,u=u)
ck('Fig3 time not assigned','no growth time'in m('wire-structure','f3-scope')['value']['value'])
for i,v,u in [('present-separation',1.1,'nm'),('heated-gap',.6,'nm'),('pbse-dielectric',24,'dimensionless'),('topo-dielectric',2.1,'dimensionless'),('model-diameter',10,'nm'),('dipole',500,'D'),('epsilon0',8.9e-12,'C² J^-1 m^-1'),('enthalpy',-28,'kJ/mol'),('impurity-effect',15,'%')]:z('assembly-model',i,v=v,u=u);ck('Model status/'+i,m('assembly-model',i)['value']['status']=='author_derived')
z('assembly-model','exchange-threshold',hi=.5,u='nm');z('assembly-model','dipolar-threshold',lo=.5,u='nm');z('assembly-model','sphere-time',lo=10,hi=60,u='min');z('assembly-model','ordered-time',lo=60,u='min')
ck('Entropy caveat','alone does not establish'in m('assembly-model','free-energy')['value']['value']);ck('Unsquaredμ literal','with μ rather than a silently inserted μ²'in m('assembly-model','interaction-equation')['value']['value'])
for i,v,u in [('diameter',10,'nm'),('gap',1.1,'nm'),('voltage',35,'mV'),('field',7e3,'V/m'),('resistance',18,'kΩ'),('capacitance',1.5e-18,'F'),('time',2.7e-14,'s'),('transfer',76,'meV'),('spacing',100,'meV'),('drop',7,'µeV'),('barrier',20,'µeV'),('film-conductivity',.055,'Ω^-1 cm^-1')]:z('transport-model',i,v=v,u=u);ck('Transport model/citedstatus/'+i,m('transport-model',i)['value']['status']=='author_derived')
ck('Literal dielectric grouping','1/2r/(r + D)'in m('transport-model','dielectric-equation')['value']['value']);z('transport-model','well-conductivity',lo=10,hi=20,u='Ω^-1 cm^-1')
z('source-context','maximum-extended-duration',hi=150,u='min');z('source-context','mass',hi=.1,u='m*');z('source-context','prior-gap',lo=.5,hi=1.1,u='eV');z('source-context','prior-core-shell',lo=2.5,hi=7,u='nm')
for i,v,u in [('gap',.28,'eV'),('temperature',300,'K'),('dielectric',24,'dimensionless'),('bohr',46,'nm'),('ratio',8,'dimensionless'),('wire-width',20,'nm'),('wire-length',1,'µm'),('rod-width',20,'nm'),('rod-length',100,'nm'),('cube',100,'nm')]:z('source-context',i,v=v,u=u)
judgments={
'individual-low':'Complete low-stock15min118°C→70°C route;5min image andtime-dependent sizepopulation are separate.',
'sphere-intermediate':'10–60min morphological regime with common injection framework; no one exact batch endpoint manufactured.',
'wire-intermediate':'Body mediumstock90min route; captionhigh-stock conflict remains explicit.',
'wire-high':'Body highstock40min unshown route; no exactFigure2/3 specimen imposed.',
'aliquot-workup':'1mL methanol quenches each removed aliquot; continuing mother batch separate; butanol isomer and washsettings unknown.',
'microscopy':'TEM/HRTEM/SEM/SAED acquisition separate from resultcohorts; EDAX no supplied spectrum and unshownmicrodiffraction caveats.',
'absorption':'Three separatetime-selected spheres; two bands are windows rather than fittedpeaks; stockcaptionconflict retained.',
'device-fabrication':'Support/resist/contact materials only; source-named trimethylsilane retained; missinganneal/lithographyparameters explicit.',
'electrical':'Three width×length pairs mapped to correctsymbols; normalizedσ/ρ representative, not falsely replicatedperwire values.',
'individual-structure':'General3.5–10nm/<10% population separate from5minimage; cubic/spherical wording retained.',
'sphere-structure':'Three10/25/40minmicroscopyaliquots; polycrystallineSAED;50–450/500nm scopes remainconflicted.',
'wire-structure':'Typical/intermediate widths distinct; junctionfraction contextscoped;HRTEM/SAEDmodel limited,Fig3timeunknown.',
'assembly-model':'Spacing/dipole/energy/entropy/facet claims explicitly authorinterpretation, not measuredatomicgeometry.',
'transport-model':'All source modelvalues/equations retained, internalfield differs fromappliedfield; comparisonfilms/wells separate.',
'source-context':'Bibliography/background/SImissingness/conflictingratio/maximum150min typedfacts retained; no newcited-materialrecipes.'}
failed=[x for x in C if not x['passed']]
report={'status':'failed'if failed else'passed_independent_complete_source_audit','source_id':'sashchiuk2004','audited_utc':datetime.now(timezone.utc).isoformat(),'source_audit_sha256':sha(B/'source-audit.json'),'source_sha256':load(B/'source-identity.json')['source_sha256'],'record_hashes':{p.stem:sha(p)for p in sorted((B/'canonical-drafts').glob('*.json'))},'record_count':15,'operation_count':47,'measurement_count':137,'material_slots':42,'check_count':len(C),'checks':C,'failed_checks':failed,'manual_record_judgments':judgments,'scope':'Independently compared all15records,47operations and137measurements plus identities/stocks/lineage/missingness against complete7page source and184unit inventory. Exact actualJSON agrees with fully read authoring. Source paragraphs/equations/figures audited scientifically; schema/dependency checks support but do not replace that review. Seven contextanchors and literal dielectric-grouping correction accepted.','limitations':['No SI found/verified; no cited fulltexts used.','Sourceconflicts remain unresolved; no exact size/property/crystal targets are admitted fromgeneral orambiguouscohorts.','Apparatus/browser/rendering independently audited elsewhere.'],'site_mutated':False}
(B/'canonical-records-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'canonical-records-audit.md').write_text('# Independent canonical source audit\n\n'+('Passed'if not failed else'Failed')+' '+str(len(C))+' supporting checks after complete scientific review of15records,47operations,137measurements and42materialslots. Four synthesis routes, five procedures and six observations remain distinct. Exact record hashes are bound in JSON.\n\n'+'\n'.join('- '+k+': '+v for k,v in judgments.items())+'\n\nNo SI, source conflict or missing setting was repaired by assumption. No Site or queue edits.\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(C),'failed':failed}))
if failed:raise SystemExit(1)
