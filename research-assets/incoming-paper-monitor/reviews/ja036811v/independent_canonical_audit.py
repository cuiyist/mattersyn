from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json,hashlib,runpy
B=Path(__file__).resolve().parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();C=[]
R={p.stem.removeprefix('schwartz-2003-'):read(p)for p in(B/'canonical-drafts').glob('*.json')}
def ck(n,v):C.append({'check':n,'passed':bool(v)})
def op(r,i):return next(o for o in R[r]['operations']if o['id']==i)
def m(r,i):return next(x for x in R[r]['measurements']if x['id']==i)
def q(n,x,v=None,lo=None,hi=None,u=None):
 ck(n+'/values',(x.get('value'),x.get('minimum'),x.get('maximum'))==(v,lo,hi))
 if u is not None:ck(n+'/unit',x.get('unit')==u)
def p(r,o,k,**kw):q(r+'/'+o+'/'+k,op(r,o)['parameters'][k],**kw)
def z(r,i,**kw):q(r+'/'+i,m(r,i)['value'],**kw)
generated=runpy.run_path(str(B/'build_records.py'))['records']
for r in generated:ck(r['record_id']+'/actual data equals manually reviewed authoring',r==R[r['record_id'].removeprefix('schwartz-2003-')])
ck('30records',len(R)==30);ck('95operations',sum(len(r['operations'])for r in R.values())==95);ck('277measurements',sum(len(r['measurements'])for r in R.values())==277);ck('96slots',sum(len(r['materials'])for r in R.values())==96)
def walk(x,n):
 if isinstance(x,dict):
  for e in x.get('evidence',[]):ck(n+'/source',e['source_id']=='schwartz2003'and bool(e['locator']))
  for k,v in x.items():walk(v,n+'/'+str(k))
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,n+'/'+str(i))
for name,r in R.items():
 walk(r,name);mats={x['id']for x in r['materials']};states={x['id']for x in r['material_states']};stocks={x['id']for x in r['stocks']};ops={x['id']for x in r['operations']};samples={x['sample_id']for x in r['products']}
 ck(name+'/unknown batch',r['lineage']['batch_id']is None);ck(name+'/no measured atomic geometry',r['structure_assets']==[]);ck(name+'/matched SI','Four supplied SI pages'in r['sources'][0]['si_status'])
 for x in r['measurements']:ck(name+'/'+x['id']+'/sample',x['sample_id']in samples)
 for x in r['operations']:
  ck(name+'/'+x['id']+'/inputs',set(x['inputs'])<=mats|states|stocks);ck(name+'/'+x['id']+'/outputs',set(x['outputs'])<=states);ck(name+'/'+x['id']+'/dependencies',set(x['depends_on'])<=ops)
 for x in r['products']:
  if x['material_state_id']:ck(name+'/'+x['sample_id']+'/physicalstate',x['material_state_id']in states)
 ck(name+'/training scope',r['quality']['requested_tasks']==(['precursor_selection','partial_protocol']if name in['zno-route','co-route','ni-route']else[]))
for row in read(B/'canonical-record-manifest.json')['records']:ck(row['id']+'/manifest hash',row['sha256']==sha(B/'canonical-drafts'/(row['id']+'.json')))
for r in ['zno-route','co-route','ni-route']:
 for o,k,v,u in [('prepare-metal','solution_volume',90,'mL'),('prepare-metal','total_metal_concentration',.101,'mol/L'),('prepare-base','solution_volume',30,'mL'),('prepare-base','base_concentration',.552,'mol/L'),('add-base','addition_rate',2,'mL/min'),('add-base','base_equivalents',1.8,'equiv')]:p(r,o,k,v=v,u=u)
 p(r,'add-base','temperature',u='°C');ck(r+'/rate approximate',op(r,'add-base')['parameters']['addition_rate']['approximate']);ck(r+'/metal scope',op(r,'prepare-metal')['parameters']['total_metal_concentration']['status']==('reported'if r=='zno-route'else'inherited'))
 ck(r+'/ORprecipitation',' or 'in op(r,'precipitate')['label']);ck(r+'/ORredispersion',' or 'in op(r,'redisperse')['label'])
 ck(r+'/alternative lineage',next(s for s in R[r]['material_states']if s['id']=='precipitated')['parent_ids']==['as-grown']and next(s for s in R[r]['material_states']if s['id']=='colloid')['parent_ids']==['washed'])
 ck(r+'/condition options',bool(R[r].get('condition_options')))
 ck(r+'/no fixed target size',R[r]['intended_target']['size']['value']is None)
ck('No nickelacetate substitution',next(x for x in R['ni-route']['materials']if x['id']=='nickel-perchlorate-hexahydrate')['formula']=='Ni(ClO4)2·6H2O')
p('clarity-restoration','add-zinc','zinc_acetate_mass',v=10,u='mg');ck('Additive hydration unknown','hydration unspecified'in R['clarity-restoration']['materials'][1]['name'].lower())
for r in ['topo-zno','topo-co','topo-ni']:
 p(r,'heat-topo','temperature',v=180,u='°C');p(r,'heat-topo','duration',lo=30,u='min');p(r,'cool','target_temperature',hi=80,u='°C');ck(r+'/strict cool',op(r,'cool')['parameters']['target_temperature']['maximum_exclusive']);p(r,'repeat-cycle','total_cycles',v=2,u='cycles');p(r,'redisperse','additional_topo_mass',v=1,u='mg');p(r,'heat-topo','topo_mass',u='g');z(r,'concentration',lo=.4,u='g/mL');ck(r+'/strict concentration',m(r,'concentration')['value']['minimum_exclusive']);ck(r+'/technical mixture',next(x for x in R[r]['materials']if x['id']=='topo-technical')['formula']is None);ck(r+'/component not independently dosed',next(x for x in R[r]['materials']if x['id']=='topo-component')['role']=='named_reagent_component');ck(r+'/unknown hot atmosphere',op(r,'heat-topo')['environment']['value']is None)
ck('PureTOPO removal contextual','pure ZnO'in m('topo-zno','cleaning')['value']['value']or'undoped'in m('topo-zno','cleaning')['value']['value'])
ck('Aggregation air',op('aggregation','evaporate')['environment']['value']=='Air');p('aggregation','evaporate','temperature',u='°C');p('aggregation','evaporate','duration',u='h')
for i,v,u in [('dopant',3.6,'%'),('size-results',5,'nm'),('size-discussion',4.9,'nm')]:z('aggregation',i,v=v,u=u)
p('pure-kinetics','prepare','stock_volume',v=250,u='µL');p('pure-kinetics','add-base','base_volume',v=30,u='µL');p('pure-kinetics','add-base','base_equivalents_prose',v=.6,u='equiv');p('pure-kinetics','measure','sampling_interval',v=30,u='s');p('pure-kinetics','measure','last_measurement',v=10,u='min');ck('Arithmetic conflictexplicit',bool(R['pure-kinetics']['quality']['conflicts']))
for r in ['pure-titration','co-titration']:p(r,'titrate','aliquot_base_equivalents',v=.2,u='equiv');ck(r+'/not independent aliquot recipes',R[r]['record_type']=='procedure')
for i,v,u in [('early-energy',32500,'cm^-1'),('early-size',2,'nm'),('later-energy',30000,'cm^-1'),('later-size',3.2,'nm')]:z('pure-titration',i,v=v,u=u)
for i,v,u in [('precursor',19000,'cm^-1'),('final',33000,'cm^-1'),('intermediate',17500,'cm^-1'),('intermediate-discussion',19000,'cm^-1'),('internal',16500,'cm^-1'),('iso1',18550,'cm^-1'),('iso2',20750,'cm^-1'),('intercept',.36,'equiv')]:z('co-titration',i,v=v,u=u)
for s in R['dopant-series']['stocks']:ck('Series no codoped stock/'+s['id'],not {'cobalt-acetate-tetrahydrate','nickel-perchlorate-hexahydrate'}<={x['material_id']for x in s['components']})
p('dopant-series','add-base','base_equivalents',v=.66,u='equiv');p('dopant-series','prepare','specimen_volume',v=250,u='µL');p('dopant-series','measure','independent_measurements',v=3,u='measurements')
for s in ['co','ni']:
 for n in [0,2,4,6,8]:z('dopant-series',s+'-nominal-'+str(n),v=n,u='mol %');ck(s+str(n)+'/figure-read',m('dopant-series',s+'-nominal-'+str(n))['value']['status']=='inferred')
 z('dopant-series',s+'-slope',v=-9 if s=='co'else-6,u='% nucleation / % dopant');z('dopant-series',s+'-two-percent',v=35,u='%')
p('thermal-ripening','heat','temperature',v=50,u='°C')
for t in [2,5,20,40,120]:z('thermal-ripening','time-'+str(t),v=t,u='min')
p('room-aging','age','duration',v=2,u='day');z('room-aging','bandgap',v=29500,u='cm^-1')
ck('S2 temperature inherited',op('surface-cleaning-control','treat')['parameters']['temperature']['status']=='inherited')
for t in [0,30,120]:z('surface-cleaning-control','time-'+str(t),v=t,u='min')
p('microscopy','image','tem_accelerating_voltage',v=200,u='kV')
for s,v,w,o in [('pure',3.8,.6,3.8),('co5',2.9,.3,2.8)]:
 for k,n in [('mean',v),('width',w),('optical',o)]:z('microscopy',s+'-'+k,v=n,u='nm')
 z('microscopy',s+'-count',v=100,u='particles')
 for k,n in [('overview',20),('hrtem',5)]:z('microscopy',s+'-'+k+'-scale',v=n,u='nm')
z('microscopy','ni-scale',v=200,u='nm');z('microscopy','aggregate-scale',v=50,u='µm');ck('SI Ni not merged','not proven identical'in m('microscopy','ni-diffraction')['value']['value'])
p('optical-absorption','room','optical_path_length',v=1,u='cm');p('optical-absorption','cool','temperature',v=7,u='K');ck('Quartz/He not incorporated',all('quartz'not in s['parent_ids']and'helium'not in s['parent_ids']for s in R['optical-absorption']['material_states']))
for i,v,u in [('co17-doping',1.7,'%'),('ni15-doping',1.5,'%'),('co17-diameter',5,'nm'),('ni15-diameter',4,'nm'),('co-lf',15900,'cm^-1'),('co-oscillator',.002,'dimensionless'),('bulk-oscillator',.005,'dimensionless'),('ni-origin-a1',15163,'cm^-1'),('ni-origin-e',15198,'cm^-1'),('ni-linewidth',30,'cm^-1'),('co-fano',17700,'cm^-1')]:z('optical-absorption',i,v=v,u=u)
for s,rows in [('co17',[('ligand-field',.36,15432),('charge-transfer',.081,25000),('band-gap',.0032,28000)]),('ni15',[('ligand-field',.057,15163),('charge-transfer',.016,23000),('band-gap',.00088,28000)])]:
 for k,v,e in rows:z('mcd',s+'-'+k+'-ratio',v=v,u='');z('mcd',s+'-'+k+'-energy',v=e,u='cm^-1')
for i,v in [('co-lf-caption',15600),('co-lf-prose',15700),('ni-caption',15400),('ni-prose',15165),('co-bg',27200)]:z('mcd',i,v=v,u='cm^-1')
z('mcd','co-ct-bound',lo=25200,u='cm^-1');p('mcd','field-scan','temperature',v=5,u='K');p('mcd','field-scan','figure7_field',v=7,u='T');p('zeeman','acquire','field_range',lo=0,hi=7,u='T');z('zeeman','average',v=53,u='cm^-1/T');z('zeeman','high-field',v=65,u='cm^-1/T')
for i,v,u in [('coercivity',105,'Oe'),('remanence',.000465,'emu/g'),('saturation',.00256,'emu/g'),('ferro-fraction',10,'%'),('per-co',.3,'Bohr magneton/Co')]:z('magnetometry',i,v=v,u=u)
z('magnetometry','tc',lo=350,u='K');ck('TC strict instrument bound',m('magnetometry','tc')['value']['minimum_exclusive']and'instrumental'in m('magnetometry','tc')['conditions'])
z('luminescence','quenching',lo=99,u='%');ck('PL not QY','not an absolute'in m('luminescence','quenching')['conditions']);z('topo-optical-comparisons','co-topo-fraction',v=5,u='%')
for i in ['zno-before','zno-after']:z('topo-optical-comparisons',i+'-diameter',v=4.2,u='nm')
z('topo-optical-comparisons','toluene',v=35000,u='cm^-1')
for i,v,u in [('k',.69503,'cm^-1/K'),('beta',.46686,'cm^-1/T'),('co-zfs',5.5,'cm^-1'),('ni-first',160,'cm^-1'),('ni-second',260,'cm^-1'),('ni-level-accuracy',25,'cm^-1')]:z('mcd-intensity-model',i,v=v,u=u)
for s,dq,b,cb,spe,chi in [('co',390,775,4.5,8440,1.9),('ni',420,770,4.8,4370,2)]:
 for k,v,u in [('dq',dq,'cm^-1'),('racah-b',b,'cm^-1'),('c-over-b',cb,'dimensionless'),('delta-spe',spe,'cm^-1'),('chi-opt',chi,'dimensionless')]:z('charge-transfer-model',s+'-'+k,v=v,u=u)
for i,v,u in [('halide-gap',6600,'cm^-1'),('calculated-gap',6770,'cm^-1'),('ni-onset',19500,'cm^-1'),('co-predicted',26300,'cm^-1'),('bound-oxide',2.4,'dimensionless'),('molecular-oxide',3.2,'dimensionless'),('pure-oxide',2,'dimensionless'),('confinement',.02,'dimensionless')]:z('charge-transfer-model',i,v=v,u=u)
z('charge-transfer-model','oxidation-ease',lo=2,u='eV');ck('MLCT wording preserved',bool(R['charge-transfer-model']['quality']['conflicts']))
for i,v,u in [('alpha-ev',.2,'eV'),('alpha-cm',1600,'cm^-1'),('valence-split',56,'cm^-1'),('beta-co',-2.3,'eV'),('beta-co-width',.3,'eV'),('beta-co-cm',-18500,'cm^-1'),('beta-co-cm-width',2400,'cm^-1'),('geff',200,'dimensionless'),('beta-ni',-4.5,'eV'),('beta-ni-width',.6,'eV'),('beta-ni-cm',-36300,'cm^-1'),('ratio',1.9,'dimensionless'),('a',3.2495,'Å'),('c',5.2067,'Å')]:z('exchange-model',i,v=v,u=u)
for dop,host,v in [('co','cdte',-2.33),('co','cdse',-2.12),('co','znte',-3.03),('mn','cdte',-.83),('mn','cdse',-1.30),('mn','znte',-1.1),('mn','zno',-2.7)]:z('exchange-model','ref-'+dop+'-'+host,v=v,u='eV');ck(dop+host+'/cited only','no current synthesis'in m('exchange-model','ref-'+dop+'-'+host)['conditions'])
ck('Ni estimate not fit','not a direct Ni Zeeman fit'in m('exchange-model','beta-ni')['value']['qualifier'])
for i,v,u in [('domain-spin',8000,'dimensionless'),('domain-co',5000,'ions'),('dots-per-domain',25,'nanocrystals')]:z('magnetization-model',i,lo=v,u=u);ck(i+'/model status',m('magnetization-model',i)['value']['status']=='author_derived')
notes={
'zno-route':'Six-operation typical framework; printed quantities retained, no invented exact room temperature, atmosphere, yield or target diameter. Solvent alternatives typed explicitly.',
'co-route':'Shared framework quantities inherited, Zn reduced to hold total metal fixed, dopant dose unknown and feed distinct from measured composition. No universal 2% or1.7% charge.',
'ni-route':'Explicit Ni perchlorate hexahydrate retained despite generic acetatecaption. Shared framework inherited, no codoping or exact occupancy.',
'clarity-restoration':'Optional approximately10mg zinc acetate; hydration and colloid volume unknown, separate from known startingdihydrate.',
'topo-zno':'Complete11-operation treatment sequence, two total solventcycles,180°C≥30min,<80°Ccool,1mgadditionalTOPO; unknownbathamount/atmosphere. Dopantremoval discussion contextual only forpureZnO.',
'topo-co':'Same generalprocessing applies separately; technicalTOPO mixture andpurecomponent distinct, no unknownimpurity moleculeor universalremovalyield assigned.',
'topo-ni':'Same generalprocessing, no invented specimen-size increase or exact treatmenttime for optical4nmNi sample.',
'aggregation':'Air,roomtemperature,concentratedEtOH; noanneal.3.6%composition and4.9/5.0nm sourceconflict retained.',
'pure-kinetics':'30µL/.554M into250µL/.101M,stated.6equiv retained againstarithmetic;30ssamplingto10min. One evolvingrun, not independentrecipes.',
'pure-titration':'Sequential.2equiv, caption/prosemolarityconflict,32500/~2nm and30000/~3.2nm opticalmodelestimates, no curve digitization.',
'co-titration':'98/2feed,titration/intermediate/internalCo/isosbesticfeatures and SVDintercept preserved.17500/19000sourcewording conflict retained.',
'dopant-series':'Separate pure/Co/Nisolutions,nominal0/2/4/6/8%,.66equiv,triplicateFigure4means; S1two-percentcontexts separate. No codopedstock or inventedfittedrates.',
'thermal-ripening':'50°C DMSO and2/5/20/40/120min acquisition; no fitted per-timeparticle sizes.',
'room-aging':'Two-dayDMSOaging tiedFigure2 only; TEMdistribution width andopticalestimate distinct.',
'surface-cleaning-control':'S2 intentionallysurfaceboundCo;180°C inheritedsharedprotocol,0/30/120min labels. No fulladsorptionrecipe or substitutionalcontrol invented.',
'microscopy':'Pure,asgrown~5%Co,SIunquantifiedNi,aggregateSEM cohorts separate;200kVTEM and all sourcebars/histograms retained. No Ni1.5%/4nm samplejoin inferred.',
'diffraction':'PowderXRD/Scherrermethod andqualitativewurtzite/aggregatecomparison, no fabricated curves,size table,latticefit or currentCIF.',
'icp':'JarrelAsh955, no guessed digestion or completefeed-to-incorporation data.',
'optical-absorption':'RT1cm and7K film/glass methods,Co1.7%5nm frozen versusNi1.5%4nmfilm. Separatebulk oscillatorcomparator; Ni thicknessdifference explicitlypreserved.',
'mcd':'5K0–6.5T and7T highresolution,all sixTable1ratio/energyrows,source-conflictingFigure8 energies,distinctC/Bdefinitions andCTlowerbound.',
'zeeman':'5K0–7Ttransmission,53mean/65highfieldcm−1T−1,1–3Tturnover; modeledlines distinct.',
'magnetometry':'MPMSandholderbackground,300K105Oe/.000465/.00256emu/g;TC>350Kinstrumentbound, isolateddot/aggregatecontrast,author-derivedmagneticfraction.',
'luminescence':'S4pureversus2%Co inEtOH300K,>99%quenchrelative notabsoluteQY; excitationandcollection unknown.',
'topo-optical-comparisons':'S5cleaned5%Co distinctfromothercohorts;ICSandbulkpriorreferencesonly. S6~4.2nmpureZnO,toluenerise35000notZnOpeak.',
'nucleation-model':'Criticalnucleusexclusion,acetateclusterhypothesis,GibbsThompson,coordination/strainarguments andScheme1 remainauthorinterpretation,not atomistic labels.',
'mcd-intensity-model':'Equations1/2,constants and cited5.5/160/260±25cm−1 levels retained; C/Bdefinitions andspinmixing notdirectsynthesisoutcomes.',
'charge-transfer-model':'Equations4–7,allRacah/ligandfield/electronegativityparameters andonsets retained; NiLMCTassignment,Coambiguity,weakMLCTwording conflict explicit.',
'exchange-model':'Equations8/9;CoN0β fitted,Ni−4.5±.6 calculated;fixedalpha,bulka/c andTable2citedotherhosts remainreferencecontexts withno trainingtasks.',
'magnetization-model':'Equation10,attempttime,spin/Co/QDdomainlowerbounds aremodels. Interfacialcarriers/doubleexchange/RKKY/Zener hypotheses notprovenmechanism.',
'source-context':'All18pages,figures/tables/scheme/equations/refs covered;missing sourcecoordinates,externalrecipe dependencies andconflictregister explicit.'}
ck('Every record manually covered',set(notes)==set(R))
rows=[{'record_id':r['record_id'],'sha256':sha(B/'canonical-drafts'/(r['record_id']+'.json')),'manual_source_review':'passed','operations_reviewed':[o['id']for o in r['operations']],'measurement_rows_reviewed':[x['id']for x in r['measurements']],'findings':notes[k]}for k,r in sorted(R.items())];fail=[x for x in C if not x['passed']]
out={'status':'passed'if not fail else'failed','source_id':'schwartz2003','audited_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':'48bb96493905290ae44c58f2346c6313677041e68ec5a9d50bdc428011c2be9f','si_sha256':'aba65f3549f74271d5d716e49c343977a43891fb9bd58dac76b0bb3bb59d08ef','source_inventory_sha256':sha(B/'source-audit.json'),'canonical_manifest_sha256':sha(B/'canonical-record-manifest.json'),'record_hashes':{x['record_id']:x['sha256']for x in rows},'record_count':len(R),'operation_count':sum(len(r['operations'])for r in R.values()),'measurement_count':sum(len(r['measurements'])for r in R.values()),'material_slots':sum(len(r['materials'])for r in R.values()),'record_type_counts':dict(Counter(r['record_type']for r in R.values())),'manual_review_scope':'Full14main+4SI source independently read/viewed. Complete authoring and actual30recorddata compared against source; every operation,measurementrow,stock,material,product,state andscope reviewed. Assertions supplement scientificreview.','records':rows,'check_count':len(C),'checks':C,'failure_count':len(fail),'failures':fail,'limits':['No unique sourcebatch joins beyond explicitcohorts.','No suppliedatomiccoordinates, rawcurves or full citedexternalrecipes.','Fits,calculations,priorbulkcomparisons andmeasurementlimits retain attribution.'],'site_mutated':False,'browser_verified':False}
(B/'canonical-records-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(B/'canonical-records-audit.md').write_text('# Schwartz 2003 canonical source audit\n\n'+out['status']+f'; {len(R)} records, {out["operation_count"]} operations, {out["measurement_count"]} measurements. {len(C)} supporting checks; {len(fail)} failures.\n\n'+'\n\n'.join('**'+k+'**: '+v for k,v in notes.items())+'\n\nExact current hashes in JSON. No Site change or browser validation.\n',encoding='utf8');print(json.dumps({'status':out['status'],'checks':len(C),'failures':fail},ensure_ascii=False))
