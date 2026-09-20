from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json,hashlib,runpy
B=Path(__file__).resolve().parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();C=[]
R={p.stem.removeprefix('banerjee-2003-'):read(p)for p in(B/'canonical-drafts').glob('*.json')}
def ck(n,v):C.append({'check':n,'passed':bool(v)})
def op(r,i):return next(o for o in R[r]['operations']if o['id']==i)
def m(r,i):return next(x for x in R[r]['measurements']if x['id']==i)
def q(n,x,v=None,lo=None,hi=None,u=None):
 ck(n+'/values',(x.get('value'),x.get('minimum'),x.get('maximum'))==(v,lo,hi))
 if u is not None:ck(n+'/unit',x.get('unit')==u)
def p(r,o,k,**kw):q(r+'/'+o+'/'+k,op(r,o)['parameters'][k],**kw)
def z(r,i,**kw):q(r+'/'+i,m(r,i)['value'],**kw)
generated=runpy.run_path(str(B/'build_records.py'))['records']
for r in generated:ck(r['record_id']+'/actual byte-bound data matches read authoring',r==R[r['record_id'].removeprefix('banerjee-2003-')])
ck('14records',len(R)==14);ck('39operations',sum(len(r['operations'])for r in R.values())==39);ck('97measurements',sum(len(r['measurements'])for r in R.values())==97);ck('41slots',sum(len(r['materials'])for r in R.values())==41);ck('Recordtypes',Counter(r['record_type']for r in R.values())=={'literature_protocol':1,'procedure':9,'observation':4})
def walk(x,n):
 if isinstance(x,dict):
  for e in x.get('evidence',[]):ck(n+'/source',e['source_id']=='banerjee2003'and bool(e['locator']))
  for k,v in x.items():walk(v,n+'/'+str(k))
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,n+'/'+str(i))
for name,r in R.items():
 walk(r,name);mats={x['id']for x in r['materials']};states={x['id']for x in r['material_states']};stocks={x['id']for x in r['stocks']};ops={x['id']for x in r['operations']};samples={x['sample_id']for x in r['products']}
 ck(name+'/unknown batch',r['lineage']['batch_id']is None);ck(name+'/no measured geometry',r['structure_assets']==[]);ck(name+'/matched SI','Matched supplied one-page' in r['sources'][0]['si_status']);ck(name+'/whole composite target',r['material']['formula']=='CdTe/MWNT')
 for x in r['measurements']:ck(name+'/'+x['id']+'/sample',x['sample_id']in samples)
 for x in r['operations']:
  ck(name+'/'+x['id']+'/inputs',set(x['inputs'])<=mats|states|stocks);ck(name+'/'+x['id']+'/outputs',set(x['outputs'])<=states);ck(name+'/'+x['id']+'/dependencies',set(x['depends_on'])<=ops)
 for x in r['products']:
  if x['material_state_id']:ck(name+'/'+x['sample_id']+'/physicalstate',x['material_state_id']in states)
for row in read(B/'canonical-record-manifest.json')['records']:ck(row['id']+'/manifest hash',row['sha256']==sha(B/'canonical-drafts'/(row['id']+'.json')))
for r in ['oxidation','growth']:
 p(r,'oxidize','duration',u='h');p(r,'oxidize','temperature',u='°C');p(r,'acid-hcl','concentration',v=35,u='%');p(r,'acid-hf','concentration',v=10,u='%');p(r,'dry-tubes','temperature',v=150,u='°C');p(r,'dry-tubes','duration',u='h')
 ck(r+'/acid order',op(r,'acid-hf')['depends_on']==['acid-hcl']);ck(r+'/no acid basis invented',all('basis' in op(r,o)['parameters']['concentration']['qualifier']for o in ['acid-hcl','acid-hf']));ck(r+'/oven atmosphere unknown',op(r,'dry-tubes')['environment']['value']is None)
 for st in R[r]['stocks'][:2]:ck(r+'/'+st['id']+'/percentage scope','basis is not specified' in st['concentrations']['source_percentage']['qualifier'])
 ck(r+'/no reagent masses',all(not x['quantities']for x in R[r]['materials'][:6]))
z('oxidation','oxygen',lo=5,hi=6,u='atomic %');ck('Impurity detection not zero','below detection' in m('oxidation','cleaning')['value']['value'])
for o,k,v,u in [('heat','temperature',320,'°C'),('adjust','target_temperature',300,'°C'),('injection','temperature',300,'°C'),('grow','temperature',250,'°C'),('grow','duration',20,'min'),('cool','target_temperature',50,'°C'),('solvate','temperature',50,'°C'),('solvate','toluene_volume',5,'mL'),('filter','membrane_pore_size',.2,'µm')]:p('growth',o,k,v=v,u=u)
for o,k,u in [('heat','duration','min'),('injection','injection_volume','mL'),('injection','injection_duration','s'),('precipitate','methanol_volume','mL'),('wash','toluene_wash_volume','mL'),('wash','wash_count','cycles'),('final-dry','temperature','°C'),('final-dry','duration','h')]:p('growth',o,k,u=u)
ck('Argon initial heating only',op('growth','heat')['environment']['value']=='Argon'and all(op('growth',o)['environment']['value']is None for o in ['adjust','injection','grow','final-dry']))
ck('Argon not incorporated',next(s for s in R['growth']['material_states']if s['id']=='hot-cadmium-template')['parent_ids']==['cadmium-template-mixture'])
ck('PTFE not incorporated',next(s for s in R['growth']['material_states']if s['id']=='retained-solid')['parent_ids']==['precipitated-mixture'])
ck('Two wash fractions',op('growth','wash')['outputs']==['washed-heterostructure','cdte-washings']and op('growth','wash')['retained_fraction']=='washed-heterostructure')
ck('Whole composite and removed CdTe distinct',[x['composition']['value']for x in R['growth']['products']]==['CdTe/MWNT','CdTe'])
ck('Unresolved tellurium input',next(x for x in R['growth']['materials']if x['id']=='tellurium-source')['formula']is None);ck('No guessed TDPA ratio',next(x for x in R['growth']['materials']if x['id']=='tdpa')['quantities']['tdpa_cd_ratio']['value']is None)
z('growth','long-axis',lo=1,hi=9,u='nm');z('growth','aspect',lo=1,hi=5,u='dimensionless');ck('Not unique polymorph','stacking faults' in R['growth']['products'][0]['phase']['value'])
p('electron-microscopy','deposit','grid_mesh',v=300,u='mesh');p('electron-microscopy','image-tem','accelerating_voltage',v=120,u='kV');p('electron-microscopy','image-hrtem','accelerating_voltage',v=200,u='kV')
ck('Separate microscopy specimens',all(s['kind']=='sample_set'for s in R['electron-microscopy']['material_states'][:2]));ck('HRTEM acquisition uses physical grid',op('electron-microscopy','image-hrtem')['inputs']==['tem-grids'])
for tag,val in [('1a',20),('1b',125),('1c',7),('1d',8),('2c',180),('2d',75),('2e',112),('3a',5),('3a-inset',5),('3b',20),('3c',5),('3d',10),('4a',20),('4b',10),('4c',10)]:z('electron-microscopy','scale-'+tag,v=val,u='nm')
p('sem','image','accelerating_voltage',lo=2,hi=10,u='kV');p('sem','image','working_distance',v=2,u='mm');z('sem','scale-2a',v=100,u='nm');z('sem','scale-2b',v=200,u='nm');ck('SEM no guessed solvent','No solvent' in op('sem','deposit')['description'])
ck('EDS text versus labels preserved','P and attributes it' in m('eds','elements')['value']['value']and'C, O, Cu, Cd and Te' in m('eds','plotted-elements')['value']['value']);ck('EDS units unresolved',bool(R['eds']['quality']['conflicts'])and'without silently rescaling' in m('eds','energy-units')['value']['value'])
p('xps','evacuate','base_pressure',v=5e-9,u='torr');p('xps','survey','pass_energy',v=80,u='eV');p('xps','survey','energy_step',v=.75,u='eV');p('xps','high-resolution','pass_energy',v=10,u='eV');p('xps','high-resolution','energy_step',v=.1,u='eV')
z('xps','cd-binding',v=405.22,u='eV');z('xps','strong-oxygen',lo=5,hi=6,u='atomic %');z('xps','mild-oxygen',lo=1,hi=2,u='atomic %');z('xps','carboxyl-removal',v=350,u='°C')
ck('TeO3 literal interpreted','TeO3, literally' in m('xps','tellurium')['value']['value']and m('xps','tellurium')['value']['status']=='author_derived');ck('350 not measured stability','not a prescribed extra anneal or measured stability limit' in m('xps','carboxyl-removal')['conditions'])
p('xrd','acquire','radiation_wavelength',v=1.54,u='Å');z('xrd','axis-range',lo=20,hi=70,u='°');ck('XRD redhost/blackCdTe','101/103' in m('xrd','mwnt-indices')['value']['value']and'(103)' in m('xrd','cdte-indices')['value']['value']);ck('No Scherrer invented','no Scherrer calculation' in m('xrd','broadening')['value']['value'])
p('uv-visible','acquire','optical_path_length',v=10,u='mm');z('uv-visible','plot-range',lo=300,hi=1000,u='nm');ck('UV solvents separate',op('uv-visible','dissolve-washings')['inputs']==['washings-specimen','toluene']and op('uv-visible','disperse-composite')['inputs']==['composite-specimen','dimethylformamide'])
ck('No nonexistent exciton','no CdTe exciton can be resolved' in m('uv-visible','composite-spectrum')['value']['value']);ck('No PL implied','No photoluminescence' in m('uv-visible','signal-type')['value']['value'])
ck('SI precursor only',R['infrared']['materials'][0]['id']=='mwnt-oxidized'and R['infrared']['products'][0]['composition']['value']is None);ck('SI unassigned curve','without a peak table or specific vibrational assignments' in m('infrared','assignments')['value']['value']);ck('SI identity multi-evidence','metadata Title naming ja035980c' in m('infrared','identity')['value']['value'])
p('raman','acquire','excitation_wavelength',v=785,u='nm');p('raman','acquire','laser_power',v=10,u='mW');p('raman','acquire','confocal_aperture',v=200,u='µm');z('raman','lo',v=166,u='cm^-1');z('raman','bulk-lo',v=170,u='cm^-1')
for s in ['precursor','composite']:z('raman','g-'+s,v=1590,u='cm^-1');z('raman','d-'+s,lo=1290,hi=1320,u='cm^-1')
ck('Bulk170 cited only','not a separately measured' in m('raman','bulk-lo')['conditions']);ck('Confocal aperture not irradiance','not irradiance' in op('raman','acquire')['description'])
for s,lo,hi in [('strong',5,6),('mild',1,2)]:z('oxidation-controls',s+'-oxygen',lo=lo,hi=hi,u='atomic %')
ck('Controls no reconstructed operations',R['oxidation-controls']['operations']==[]and R['oxidation-controls']['quality']['requested_tasks']==[]);ck('Raw not independently counted','no distinct raw-tube numerical result'in m('oxidation-controls','raw-scope')['value']['value'].lower())
z('free-nanocrystals','free-prose-size',v=5,u='nm');z('free-nanocrystals','no-tube-size',v=5,u='nm');ck('Free versus no-tube conflict explicit',bool(R['free-nanocrystals']['quality']['conflicts']));ck('No comparator synthesis',R['free-nanocrystals']['operations']==[])
for i in ['coordination','ligand-competition','diffusion','site-geometry','tip-preference','junction','passivation']:ck('Mechanisms/'+i+'/author status',m('mechanisms',i)['value']['status']=='author_derived')
ck('Schematic not measured','not measured atomic coordinates' in m('mechanisms','scheme')['value']['value']);ck('No external recipe imported','external full texts are not part of this review' in m('source-context','external-preparations')['value']['value'])
notes={
'oxidation':'Complete reported KMnO4/H2SO4→35%HCl→10%HF sequence, unknown percentage bases, extensive distilled-water washing and150°C oven drying retained. No guessed timing, ratios, final exact surface formula or zero-impurity claim. SI is linked only to this precursor.',
'growth':'All17 operations checked: same upstream five-step template preparation plus CdO/TDPA/TOPO320°C under Ar,300°C Te/TOP injection,250°C20min growth,heat removal,50°C cooling,5mL toluene,methanol precipitation,0.2µm PTFE filtration,toluene wash and unknown final drying. Unknown charges/stock identity preserved. Argon and membrane excluded from incorporated material ancestry. Composite and washed-away CdTe are separate physical outputs.',
'electron-microscopy':'Separate pristine,oxidized and composite specimens; ethanol droplets,300-mesh Cu/lacey-carbon support,120/200kV instruments and all15 TEM/HRTEM scale annotations verified. Source figure motifs remain local images,not exact sample-to-morphology recipes,chemical-group counts or SAED.',
'sem':'Cu-grid/Be-plate preparation,Leo1550,2–10kV,2mm distance and100/200nm bars verified. SEM solvent and sputter coating remain unknown; substrate elements are not hybrid dopants.',
'eds':'Cd/Te/P prose versus visibleC/O/Cu/Cd/Te inset preserved. No Cu doping,P absence,stoichiometric quantification or instrument-specific acquisition guessed. CaptioneV/0–10scale discrepancy explicit; residual-metal statements retain unknown detection limits.',
'xps':'KratosDS800,tape/steel support,~5e−9torr analytical vacuum,MgKα,80eV/.75eV and10eV/.1eV modes,405.22eV Cd assignment and5–6/1–2at%O precursor cohorts verified. TeO3 retained literally as author assignment;350°C carboxyl-removal statement is contextual,not a prescribed anneal or measured complete thermal-stability dataset.',
'xrd':'CuKα1.54Å/Bragg geometry,composite CdTe/MWNT indexing and mixed wurtzite/zinc-blende limits checked.20–70° is display scope. No invented phase fractions,Scherrer size,unit-cell parameters or refined structure.',
'uv-visible':'10mm quartz cells and two distinct solvents/populations verified. DMF sonication settings unknown. Featureless hybrid/no resolved exciton and washings heterogeneity are observations; detachment/background explanations attributed. No PL,bandgap or absolute cross section invented.',
'infrared':'Matched one-pageSI is oxidizedMWNT precursor only. Nexus670/ZnSe ATR context,descending original ticks and absence of specific peak assignments retained. Identity combines main declaration,matching subject and metadata DOI stem,not filename alone.',
'raman':'785nm,10mW,200µm aperture source acquisition;166cm−1 currenthybrid versus170cm−1 citedbulk;~1590G and1290–1320D band contexts separately scoped. No D/G ratio,exact linewidth,phonon model fit or current bulk synthesis invented.',
'oxidation-controls':'Strong/mild/pristine/raw labels remain observation contexts. Only two approximate XPSoxygen ranges and qualitative coverage observations supplied. No fabricated control doses,complete alternate growth recipes or standardized synthesis-failure outcomes.',
'free-nanocrystals':'P7relative-monodispersity/5nm statement and p9less-monodisperse-than-no-tube~5nm comparison remain separate with explicit unresolved wording. No merged population or fabricated comparator recipe.',
'mechanisms':'Coordination,steric diffusion control,site geometry,tip density,junction formation,passivation and SWNT limits are author interpretations. Figure8 architecture is conceptual with TDPA omitted,not atomic ground truth. Device/transport claims remain future work.',
'source-context':'All9main+1SI,8figures and43numberedreferences covered; priorCdSe/TiO2/EDC and other nanostructures remain cited context. No external full-text procedure or unsupported new material record imported.'}
rows=[{'record_id':r['record_id'],'sha256':sha(B/'canonical-drafts'/(r['record_id']+'.json')),'manual_source_review':'passed','operations_reviewed':[o['id']for o in r['operations']],'measurement_rows_reviewed':[x['id']for x in r['measurements']],'findings':notes[k]}for k,r in sorted(R.items())];fail=[x for x in C if not x['passed']]
out={'status':'passed'if not fail else'failed','source_id':'banerjee2003','audited_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':'24faaec54cea1293bc7951b7d363587e2ec80edaa68d6e90049b5525bc312837','si_sha256':'0746611853616b5531750d1cd4c610d605c551eec0b3317805c0fcc98fce301e','source_inventory_sha256':sha(B/'source-audit.json'),'canonical_manifest_sha256':sha(B/'canonical-record-manifest.json'),'record_hashes':{x['record_id']:x['sha256']for x in rows},'record_count':14,'operation_count':39,'measurement_count':97,'material_slots':41,'manual_review_scope':'Full9main+1SI pages independently read and visually inspected; complete authoring and byte-bound actual14records checked against source,including every operation,measurement row,material/stock/product/state and context. Supporting assertions supplement manual scientific review.','records':rows,'check_count':len(C),'checks':C,'failure_count':len(fail),'failures':fail,'limits':['Reproducible reagent quantities and detailed oxidation recipe are absent; referenced external papers were not imported.','Source descriptions do not establish unique physical batch identities,phase fractions or atomic junction coordinates.','Controls,free washings,no-tube comparison and citedbulk Raman remain distinct.'],'site_mutated':False,'browser_verified':False}
(B/'canonical-records-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(B/'canonical-records-audit.md').write_text('# Banerjee2003 canonical source audit\n\n'+out['status']+f':14records,39operations,97measurements,41materialslots. {len(C)} supportingchecks,{len(fail)} failures.\n\n'+'\n\n'.join('**'+k+'**: '+v for k,v in notes.items())+'\n\nExact current hashes in JSON. No Site mutation or browser verification.\n',encoding='utf8');print(json.dumps({'status':out['status'],'checks':len(C),'failures':fail},ensure_ascii=False))
