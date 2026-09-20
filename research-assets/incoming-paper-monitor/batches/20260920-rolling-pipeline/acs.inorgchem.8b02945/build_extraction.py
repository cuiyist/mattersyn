"""Private source authoring only. Refuses to overwrite a frozen extraction."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re,copy,math
from decimal import Decimal
from pypdf import PdfReader
import pypdfium2 as pdfium
from PIL import Image,ImageOps,ImageDraw
import source_author_data as A
import source_numeric_data as N
P=Path(__file__).resolve().parent;SID='friedfeld2019';DOI='10.1021/acs.inorgchem.8b02945';AUTHOR='/root/peng1998_reader_assets'
assert not(P/'package-freeze.json').exists(),'Preserve frozen package; version any correction.'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
prep=read(P/'source-preparation.json');docs={x['role']:x for x in prep['documents']}
for role,d in docs.items():
 assert sha(d['source_path'])==d['sha256'] and d['page_count']==(8 if role=='main'else 25)
 assert Path(d['source_path']).read_bytes().startswith(b'%PDF-')
def ev(role,page,locator):return {'source_id':SID+'-'+role,'document_role':role,'source_sha256':docs[role]['sha256'],'pdf_page':page,'printed_page':802+page if role=='main'else page,'locator':locator}
def q(raw,unit,meaning,evidence,flags=()):
 raw=str(raw);t=raw.replace('−','-').replace(' × 10','e').replace('×10','e').replace('^','');ap=t.startswith('~');t=t.lstrip('~');comp=None;ran=None;value=None;ordered=None
 for c in ['<=','>=','<','>']:
  if t.startswith(c):comp=c;t=t[len(c):];break
 if re.fullmatch(r'[+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?',t):value=float(Decimal(t))
 elif '–'in t:
  vals=t.split('–')
  if len(vals)==2:
   try:ordered=[float(Decimal(z))for z in vals];ran={'min':min(ordered),'max':max(ordered)}
   except Exception:pass
 return {'raw_text':raw,'value':value,'unit':unit,'uncertainty':None,'range':ran,'ordered_endpoints':ordered,'comparison':comp,'approximate':ap,'status':'reported'if value is not None or ran else'reported_text','meaning':meaning,'evidence':evidence,'conflict_ids':[f for f in flags if f.startswith('C')],'gap_ids':[f for f in flags if f.startswith('G')]}
facts=[]
for fid,role,page,loc,title,claim,scope,qs,flags,kind in A.FACTS:
 e=[ev(role,page,loc)];flags=flags.split()
 extra={'prior-cluster':[('main',2,'Introduction prior structure')],'labeled-msc':[('main',7,'Synthesis of In37P20(O2-13CCH2Ph)51')],'conversion-monitor':[('main',5,'Constant overall20mL additive experiment')],'nmr-acquisition':[('main',4,'Figure4A caption202Hz')],'si-ripening':[('si',8,'FigureS10 two original images')],'si-growth-fits':[('si',7,'FigureS8')],'si-pretreat':[('si',10,'FigureS14')],'si-orders':[('si',22,'FiguresS34/S35'),('si',23,'FiguresS36/S37')],'si-scherrer':[('si',25,'FigureS39 boxes and prose')],'pretreat72':[('si',10,'FigureS15'),('si',11,'FigureS16')],'abs-vt':[('main',3,'Variabletemperatureprose'),('si',4,'FigureS3')]}
 for x in extra.get(fid,[]):e.append(ev(*x))
 facts.append({'id':SID+'-'+fid,'title':title,'claim':claim,'sample_scope':scope,'claim_class':kind,'evidence':e,'quantities':[q(raw,u,m,e,flags)for m,raw,u in qs],'conflict_ids':[x for x in flags if x.startswith('C')],'gap_ids':[x for x in flags if x.startswith('G')],'independent_audit_status':'pending'})
fb={x['id'].removeprefix(SID+'-'):x for x in facts}
materials=[{'id':mid,'name':name,'source_formula_or_abbreviation':formula,'role':role,'scope_note':note,'source_fact_ids':[SID+'-'+fid],'evidence':fb[fid]['evidence'],'identity_qualification':'Source names/formulas only; no molecular or atomic visual qualification in this extraction.'}for mid,name,formula,role,note,fid in A.MATERIALS]
def fq(fid,indices=None):
 values=fb[fid]['quantities'];return copy.deepcopy(values if indices is None else [values[i]for i in indices])
stocks=[
 {'id':'bnmgcl-stock','name':'Purchased benzylmagnesium chloride in2-Me-THF','components':[{'material_id':'bnmgcl','role':'solute','amount':None},{'material_id':'methyltetrahydrofuran','role':'solvent','amount':None}],'quantities':fq('materials',[3]),'preparation':'Commercial solution used without further purification; no solution-complex model.','final_volume':None,'subsequent_transfer_volume':fq('acid-charge',[0]),'source_fact_ids':[SID+'-materials',SID+'-acid-charge'],'evidence':fb['materials']['evidence']},
 {'id':'msc-injection','name':'Representative myristate-MSC injection inODE','components':[{'material_id':'msc-myristate','role':'solute','amount_quantities':fq('conversion-inject',[0,1])},{'material_id':'ode','role':'solvent','amount_quantities':fq('conversion-inject',[2])}],'quantities':fq('conversion-inject'),'preparation':'Dissolve by sonication and rapidly inject;20mL final reaction is not the stock volume.','final_volume':None,'source_fact_ids':[SID+'-conversion-inject'],'evidence':fb['conversion-inject']['evidence']},
 {'id':'indium-myristate-additive','name':'Indium myristate additive inODE','components':[{'material_id':'indium-myristate','role':'solute','amount':None},{'material_id':'ode','role':'solvent','amount':None}],'quantities':[],'preparation':'Desired additive solution inODE; concentration/preparation amount not supplied. Equivalents belong to selected reaction conditions.','final_volume':None,'source_fact_ids':[SID+'-conversion-charge',SID+'-additive-series'],'evidence':fb['conversion-charge']['evidence']},
 {'id':'myristic-acid-additive','name':'Myristic acid additive inODE','components':[{'material_id':'myristic-acid','role':'solute','amount':None},{'material_id':'ode','role':'solvent','amount':None}],'quantities':[],'preparation':'Analogous desired additive solution; no stock concentration or isolated charge inferred.','final_volume':None,'source_fact_ids':[SID+'-conversion-charge',SID+'-additive-series'],'evidence':fb['conversion-charge']['evidence']},
 {'id':'hcl-aqueous','name':'Aqueous1M HCl','components':[{'material_id':'hcl','role':'solute','amount':None},{'material_id':'water','role':'solvent','amount':None}],'quantities':fq('acid-quench',[0]),'preparation':'Source specifies solution concentration only; used to reachpH2.','final_volume':None,'source_fact_ids':[SID+'-acid-quench'],'evidence':fb['acid-quench']['evidence']},
]
for x in stocks:x.update(storage=None,scope_note='Only explicitly stated stock quantities apply; transferred and final-reaction quantities remain distinct.')
samples=[]
def sample(i,label,fid,kind='observation_context',formula=None,parents=()):
 samples.append({'id':i,'label':label,'kind':kind,'reported_whole_composition':formula,'parent_context_ids':list(parents),'source_fact_ids':[SID+'-'+fid],'evidence':fb[fid]['evidence'],'physical_batch_join':'Unknown unless explicit; same compound or condition is not an exact aliquot match.','atomic_structure_supplied':False})
sample('acid-isolated','Isolated carbonyl-13C phenylacetic acid','acid-crystallize','isolated_product','PhCH2-13CO2H')
sample('phenylacetate-reference','Natural-abundance phenylacetate MSC / cited structure','prior-cluster','reference_context','In37P20(O2CCH2Ph)51')
sample('nmr-labeled','Labeled phenylacetate MSC','labeled-msc','prepared_reference','In37P20(O2-13CCH2Ph)51')
for i,l,f in [('vt-absorption','Phenylacetate MSC temperature-dependent absorption','abs-vt'),('nmr-acid-exchange','UnlabeledMSC with labeled acid','acid-exchange'),('nmr-indium-exchange','UnlabeledMSC with labeled indium salt','indium-exchange'),('acid-optical-control','MSC plus myristic acid absorption control','si-acid-abs'),('temperature-series','No-additive temperature-series optical comparison','temperature-series'),('xrd-context','Temperature-series powder/reference patterns','phase-result'),('extended-300','300C extended optical aging','si-ripening'),('extended-300-tem','300C extended-timeTEM; exactimageages unspecified','si-ripening'),('pretreat30','130C30h optical/NMR pretreatment','pretreat'),('pretreat-xrd','130C diffraction / oleate-labeled control ambiguity','si-pretreat'),('pretreat72-conversion','130C72h followed by250C conversion','pretreat72'),('thermal','Solid myristateMSC thermal analysis','thermal-result'),('thermal-cycle','MSC DSC cycle/reheat experiment','si-dsc-cycle'),('concentration-fit','Source log-rate concentration regression','si-logfit'),('additive-fit','Source additive-concentration regressions','additive-series'),('additive-250','250C acid versus indium additive comparison','additive-effects'),('kinetic-model','Three transformed optical kinetic analyses','si-orders'),('scherrer150','150C powder Gaussian/Scherrer analysis','si-scherrer'),('scherrer250','250C powder Gaussian/Scherrer analysis','si-scherrer'),('author-mechanism','Proposed monomer/fragment pathways','scheme2-model')]:sample(i,l,f)
for t in [150,200,250,300]:sample(f'temp-{t}',f'{t}C no-additive conversion/optical context','temperature-series','reaction_condition_context')
for t in [150,250]:sample(f'temp-{t}-tem',f'{t}C local TEM specimen','tem-result','characterization_context')
for t in [250,300]:
 sample(f'concentration-{t}',f'{t}C concentration-series comparison','concentration-series')
 for c in ['0.030','0.061','0.182']:sample(f'c-{t}-{c.replace(".","p")}',f'{t}C initialMSC{c}mM','concentration-series','reaction_condition_context')
for additive,temps in [('acid',[150,250]),('indium',[150,200,250])]:
 for t in temps:
  sample(f'{additive}-{t}',f'{t}C {additive} additive optical series','additive-series')
  for eq in [0,10,20,50]:sample(f'{additive}-{t}-eq{eq}',f'{t}C {eq}equiv {additive} additive','additive-series','reaction_condition_context')
# Preparation operations preserve sequence and retained fractions; data/analysis quantities are not synthesis controls.
def op(i,title,fid,inputs,outputs,indices=None,missing=(),retained=None):
 return {'id':i,'action':title,'inputs':inputs,'outputs':outputs,'source_fact_ids':[SID+'-'+fid],'quantities':fq(fid,indices),'evidence':fb[fid]['evidence'],'missing_fields':list(missing),'retained_fraction':retained}
conversion=[
 op('dry-flask','Oven- and Schlenk-dry apparatus','glassware',[],['dry-flask'],missing=['Schlenk drying pressure/time']),
 op('charge-ode','ChargeODE and selected additive solution','conversion-charge',['dry-flask','ode','selected-additive-stock'],['preinjection-mixture'],missing=['additive stock concentration']),
 op('heat-baseline','Heat underN2; calibrate probe and collect baseline','conversion-heat',['preinjection-mixture','nitrogen'],['heated-baseline-mixture'],missing=['ramp','stirring speed','calibration standard']),
 op('sonicate-msc','Prepare representative MSC-in-ODE injection','conversion-inject',['msc-myristate','ode'],['msc-injection'],missing=['sonication duration/power']),
 op('inject-msc','Rapidly inject MSC solution and homogenize','conversion-inject',['heated-baseline-mixture','msc-injection'],['growing-mixture'],[],['injection rate','mixing duration']),
 op('monitor-growth','Acquire time-resolved absorption','conversion-monitor',['growing-mixture'],['growth-data','reaction-mixture'],[0],['condition-specific endpoint']),
 op('distill-solvent','Distill solvent after reaction','conversion-workup',['reaction-mixture'],['distilled-reaction-residue','solvent-distillate'],[],['temperature/pressure'],'reaction residue'),
 op('transfer-purify','Transfer residue toglovebox and purify','conversion-workup',['distilled-reaction-residue'],['purified-product-fractions'],[],['full GPC protocol','recovery'],'InP fraction distinguished fromIn2O3; exact fraction collection unreported'),
]
acid=[
 op('acid-charge','ChargeGrignard andTHF; attachCO2 bulb','acid-charge',['bnmgcl-stock','thf','labeled-co2'],['acid-charge-mixture'],missing=['stirring speed']),
 op('acid-condense','Cool withLN2, evacuate and condense13CO2','acid-condense',['acid-charge-mixture','liquid-nitrogen'],['condensed-mixture'],missing=['vacuum pressure','cooling time']),
 op('acid-cold-hold','Warm in dryice/acetone bath and hold','acid-react',['condensed-mixture','dry-ice','acetone'],['cold-reacted-mixture'],[0,1]),
 op('acid-ambient-hold','Warm to room temperature and hold','acid-react',['cold-reacted-mixture'],['reacted-mixture'],[2],['numerical room temperature']),
 op('acid-quench','Ice-water cool and addmethanol dropwise','acid-quench',['reacted-mixture','methanol','water'],['quenched-mixture'],[],['methanol volume/rate']),
 op('acid-acidify','Add1M aqueousHCl topH2','acid-quench',['quenched-mixture','hcl-aqueous'],['acidified-mixture'],[0,1],['HCl volume']),
 op('acid-extract','Extractthree times withEt2O','acid-extract',['acidified-mixture','diethyl-ether'],['ether-extracts','aqueous-raffinate'],[0,1],retained='organic ether extracts'),
 op('acid-wash-dry','Combineorganic fractions, brinewash andNa2SO4dry','acid-extract',['ether-extracts','brine','sodium-sulfate'],['dried-organic-solution'],[],['brine/drying-agent amount'],'organic solution'),
 op('acid-filter-evaporate','Filter and rotary-evaporate','acid-extract',['dried-organic-solution'],['crude-acid'],[],['evaporation settings'],'filtrate followed by crude nonvolatile product'),
 op('acid-layer','Dissolve inminimalDCM and layerpentane','acid-crystallize',['crude-acid','dichloromethane','pentane'],['layered-solution'],[],['solvent volumes']),
 op('acid-crystallize','Standcold to crystallize','acid-crystallize',['layered-solution'],['crystal-motherliquor-mixture'],[0,1]),
 op('acid-isolate','Collect anddrywhite crystals','acid-crystallize',['crystal-motherliquor-mixture'],['acid-isolated','mother-liquor'],[],['drying settings'],'white acid crystals'),
]
protocols=[{'id':'conversion-family','title':'Representative MSC-to-QD conversion with selected condition','kind':'synthesis_condition_family','operations':conversion,'sample_ids':['temp-150','temp-200','temp-250','temp-300'],'condition_fact_ids':[SID+'-'+x for x in ['temperature-series','concentration-series','additive-series']],'condition_scope_note':'Separate figure-defined temperature/concentration/additive contexts do not imply an exhaustive Cartesian matrix or exact replicate count. Representative injection charge is not imputed into changed concentration runs.'},
{'id':'labeled-acid-synthesis','title':'Preparation of carbonyl-13C phenylacetic acid','kind':'upstream_synthesis','operations':acid,'sample_ids':['acid-isolated']},
{'id':'labeled-msc-cited','title':'LabeledMSC preparation by cited isotope substitution','kind':'cited_preparation_with_missing_parameters','operations':[op('substitute-labeled-acid','Replace naturalacid in citedMSC preparation','labeled-msc',['labeled-acid','indium-acetate','phosphine'],['nmr-labeled'],[],['reagent amounts','all reaction/isolationsettings fromcitedprocedure'])],'sample_ids':['nmr-labeled']},
{'id':'exchange-acid','title':'Labeled-acid exchange titration','kind':'chemical_perturbation_measurement','operations':[op('add-labeled-acid','Addselected equivalents oflabeledacid tonaturalMSC','acid-exchange',['msc-phenylacetate','labeled-acid','toluene-d8'],['nmr-acid-exchange'],[0,1,2],['aliquot volumes','equilibration time'])],'sample_ids':['nmr-acid-exchange']},
{'id':'exchange-indium','title':'Labeledindium-carboxylate exchange titration','kind':'chemical_perturbation_measurement','operations':[op('add-labeled-indium','Addlabeledindium salt tonaturalMSC','indium-exchange',['msc-phenylacetate','indium-labeled-phenylacetate'],['nmr-indium-exchange'],missing=['aliquot volumes','equilibration time'])],'sample_ids':['nmr-indium-exchange']},
{'id':'low-temperature-pretreat','title':'Low-temperatureMSC pretreatment','kind':'post_treatment_comparison','operations':[op('pretreat-msc','HeatMSC at130C; keep30h and72h sourcecontexts distinct','pretreat',['msc-myristate'],['pretreated-mixture'],[0,1],['exact30h/72h cross-panel join'])],'sample_ids':['pretreat30','pretreat-xrd','pretreat72-conversion'],'condition_fact_ids':[SID+'-pretreat72'],'scope_note':'No unique same-aliquot join resolved; subsequent250C conversion uses representative conversion family without invented charges.'}]
for pid,title,fid,ss,idx in [('nmr','NMR acquisition','nmr-acquisition',['nmr-labeled','nmr-acid-exchange','nmr-indium-exchange','pretreat30'],None),('uvvis','Absorption acquisition','uv-acquisition',['vt-absorption'],None),('tem','TEM acquisition','tem-acquisition',['temp-150-tem','temp-250-tem','extended-300-tem'],None),('xrd','PowderXRD acquisition','xrd-acquisition',['xrd-context','pretreat-xrd'],None),('tga','Thermogravimetry','thermal-acquisition',['thermal'],[0]),('dsc','Calorimetry','thermal-acquisition',['thermal','thermal-cycle'],[1]),('optical-analysis','Smoothing and baseline subtraction','optical-processing',['temperature-series','concentration-fit'],None),('kinetic-analysis','Source kinetic transformations and fits','si-orders',['kinetic-model'],None),('scherrer-analysis','Source Gaussian/Scherrer analysis','si-scherrer',['scherrer150','scherrer250'],None),('acid-nmr','LabeledacidNMR characterization','acid-nmr',['acid-isolated'],None)]:
 protocols.append({'id':pid,'title':title,'kind':'measurement_or_analysis','operations':[op(pid+'-analyze',title,fid,ss,[pid+'-data'],idx,['See source acquisition/analysis gapG5'])],'sample_ids':ss})

tables=[]
def cell(raw,u,m,role,page,loc,flags=()):return q(raw,u,m,[ev(role,page,loc)],flags)
def make_table(i,title,headers,rows,role,page,scope,footnotes=(),flags=()):
 obj={'id':i,'title':title,'column_headers':headers,'rows':rows,'evidence':[ev(role,page,title)],'sample_scope':scope,'footnotes':list(footnotes),'conflict_ids':list(flags),'numeric_cell_count':sum(c['value']is not None or c['range']is not None for r in rows for c in r['cells']),'cell_count':sum(len(r['cells'])for r in rows),'independent_numerical_audit':'pending'};tables.append(obj);return obj
rows=[]
for j,vals in enumerate(N.RATE_TABLE):
 cs=[]
 for k,v in enumerate(vals):
  raw=v if k==0 else v.replace('e',' × 10').replace('-','−')
  cs.append(cell(raw,'equiv per MSC'if k==0 else'delta_abs500/s','indium additive equivalents'if k==0 else f'growth rate at{[150,200,250][k-1]}C','main',5,f'Table1 row{j+1} column{k+1}'))
 rows.append({'id':f'table1-r{j+1}','sample_context':f'indium-additive-{vals[0]}eq; temperature supplied by each column','cells':cs})
make_table('table-1','MSC growth rate versus temperature and indium-myristate equivalents',['equiv In(MA)3','150°C','200°C','250°C'],rows,'main',5,'four additive rows; separate temperature columns')
rows=[]
for j,vals in enumerate(N.ENERGY_TABLE):rows.append({'id':f's22-r{j+1}','sample_context':'0.182mM MSC250C Gaussianmax','cells':[cell(v,['min','eV'][k],['time','Gaussian fit maximum (literal eV)'][k],'si',15,f'S22 embedded table row{j+1} column{k+1}',['C8'])for k,v in enumerate(vals)]})
make_table('table-s22','Gaussian peak maxima as printed',['time(min)','Max from Gaussian fit(eV)'],rows,'si',15,'0.182mM250C',['Printed energy values are not rescaled.'],['C8'])
rows=[]
equations=[]
for lab,role,page,ctx,xu,yu,a,b,r2,expr in N.FITS:
 rows.append({'id':'fit-'+lab,'sample_context':ctx,'x_unit':xu,'y_unit':yu,'raw_expression':expr,'cells':[cell(v,u,m,role,page,lab+' '+m,['C9'])for v,u,m in [(a,f'({yu})/({xu})','slope'),(b,yu,'intercept'),(r2,'dimensionless','R_squared')]]})
 equations.append({'id':'equation-fit-'+lab,'raw_expression':expr,'source_context':ctx,'evidence':[ev(role,page,lab+' printed regression')],'interpretation':'Literal published fit; no independently refitted curve.','numerical_recalculation_performed':False})
make_table('printed-linear-fits','All printed linear-fit annotations',['slope','intercept','R²'],rows,'si',6,'row-specific main/SI equation locators',['Each row retains its own axis units, concentration wording and source precision.'],['C9'])
rows=[]
for j,(page,ctx,heading,a,x0,dx,D)in enumerate(N.SCHERRER_PROSE):
 vals=[(heading,'deg 2theta','nominal heading'),(a,'source area units unspecified','a'),(x0,'deg 2theta','x0'),(dx,'deg 2theta (Gaussian HWHM convention from boxes)','dx'),(D,'nm','D source calculation')]
 rows.append({'id':f'scherrer-prose-{j+1}','sample_context':ctx,'cells':[cell(v,u,m,'si',page,f'FigureS{38 if page==24 else 39} prose peak{heading} {m}',['C10'])for v,u,m in vals]})
make_table('scherrer-prose','All Scherrer prose entries',['heading2theta','a','x0','dx','D'],rows,'si',24,'row-specific150C/250C',['Reported D values are not newly calculated.'],['C10'])
rows=[]
for j,(page,ctx,pos,a,x0,dx,amp,s)in enumerate(N.GAUSSIAN_BOXES):
 vals=[(a,'source area units unspecified','Area a'),(x0,'deg 2theta','X Position x0'),(dx,'deg 2theta','HWHM dx'),(amp,'source intensity units unspecified','ampl'),(s,'source unit unspecified','s')]
 rows.append({'id':f'gaussian-box-{j+1}','sample_context':ctx,'box_position':pos,'raw_column_headers':['Param','Description','Value','Lock','Std. Dev.'],'raw_parameter_labels':['a','x0','dx'],'std_dev_raw':['','',''],'lock_cells':'three visually unchecked boxes','raw_expression':N.GAUSSIAN_FORMULA,'cells':[cell(v,u,m,'si',page,f'FigureS{38 if page==24 else 39} {pos} fit box {m}',['C10'])for v,u,m in vals]})
 equations.append({'id':f'equation-gaussian-{j+1}','raw_expression':N.GAUSSIAN_FORMULA,'source_context':ctx+' '+pos+' fitbox','evidence':[ev('si',page,f'Gaussian function in {pos} box')],'parameter_definitions':{'a':'Area','x0':'X Position','dx':'HWHM','ampl':'derived amplitude displayed by source software','s':'displayed source width parameter; no explicit prose definition'},'numerical_recalculation_performed':False})
make_table('gaussian-boxes','All Gaussian fit-box parameters',['a','x0','dx','ampl','s'],rows,'si',24,'row-specific150C/250C',['Uncertainties are blank in the supplied boxes, not zero.','dx is explicitly labeled HWHM; no silent FWHM substitution.'],['C10'])
rows=[]
for j,(nu,sol,shift,mult,count,coupling,clabel,assignment)in enumerate(N.ACID_NMR):
 cs=[cell(shift,'ppm','chemical shift','main',7,f'{nu} {sol} analytical peak{j+1}')]
 if count:cs.append(cell(count,'H_count','integrated proton count','main',7,f'{nu} {sol} peak{j+1} integration'))
 if coupling:cs.append(cell(coupling,'Hz',clabel,'main',7,f'{nu} {sol} peak{j+1} coupling'))
 rows.append({'id':f'acid-nmr-{j+1}','sample_context':'isolated labeled acid','nucleus':nu,'solvent':sol,'multiplicity_raw':mult,'assignment_raw':assignment,'temperature_C':'23','frequency_MHz':'700'if nu=='1H'else'176','cells':cs})
make_table('acid-nmr','Complete labeled-acid analytical NMR listing',['shift','integration where supplied','coupling where supplied'],rows,'main',7,'source analytical13C/1H environments',['Missing coupling/integration is not zero. Descending multiplet intervals remain ordered as printed.'])
save('source-tables.json',{'schema':'mattersyn-source-tables/1','source_id':SID,'author':AUTHOR,'tables':tables,'total_numeric_cells':sum(x['numeric_cell_count']for x in tables),'curves_digitized':False,'independent_audit_status':'pending'})

figures=[]
mainfig=[
('figure-1',2,'Variable-temperature13C NMR and absorption',['nmr-labeled','vt-absorption'],{'A':'tol-d8,176MHz;−30,25,80,return25°C','B':'20–110°C in10°Csteps;captionphenylacetateMSCin toluene'},[.515,.545,.907,.779]),
('figure-2',3,'Labeledacid and indium-carboxylate exchange',['nmr-acid-exchange','nmr-indium-exchange'],{'A':'NaturalMSC+1/10/30eq13Cacid;authentic13CMSCandfreeacidreferences','B':'NaturalMSC+1/5/10/20eq labeledindiumsalt;authentic13CMSC;tol-d8,176MHz'},[.515,.081,.907,.372]),
('figure-3',4,'Optical evolution, diffraction andTEM',['temperature-series','temp-150-tem','temp-250-tem','xrd-context'],{'A':'250°C spectra0,10,20,30,40,50,60min;inset500/600/700nm','B':'150/200/250/300°C at500nm','C':'finalabsorption150/200/250/300°C','D':'150/250°C XRDandInP/In2O3references','E':'150°Cagglomerates;20nmbar','F':'250°Cspheres;20nmbar;2.6±0.5nm,n315'},[.094,.337,.484,.841]),
('figure-4',4,'Pretreatment NMR and conversion comparison',['pretreat30','pretreat72-conversion'],{'A':'31P,C6D6,202Hz asprinted;130°C30h','B':'250°C500nmconversion;pretreatment30/72h cross-panelambiguity'},[.515,.73,.907,.932]),
('figure-5',5,'MSC concentration dependence',['concentration-250'],{'main':'0.182/0.061/0.030mM,250°C,500nm','inset':'Rate axis×10^4ΔAbs/s;captionfit0.00564x−0.00012,R².9904'},[.515,.081,.907,.345]),
]
crop_specs=[]
for i,page,title,ss,ann,box in mainfig:
 figures.append({'id':i,'role':'main','page':page,'title':title,'sample_context_ids':ss,'panels':ann,'evidence':[ev('main',page,i+' complete figure andcaption')],'raw_curves_digitized':False});crop_specs.append((i,'main',page,box,title))
layout=read(P/'source-render/crop-layout.json');caption_map={};page_start={}
for page_layout in layout:
 previous=.055
 for b in page_layout['blocks']:
  number=int(re.match(r'Figure S(\d+)',b['text']).group(1));end=b['box'][3]/page_layout['size'][1]+.008
  caption_map[number]=(b['text'],[.10,previous,.97,end]);previous=end+.003
for num,page,title,ctx,ann,box in N.SI_FIGURES:
 i=f'figure-s{num}';caption,box=caption_map[num]
 if num==36:box[3]=.528
 if num==37:box[1]=.528
 figures.append({'id':i,'role':'si','page':page,'title':title,'sample_context_ids':[ctx],'annotations':ann,'raw_caption':caption,'evidence':[ev('si',page,f'Actual printed FigureS{num} caption and graphic')],'raw_curves_digitized':False});crop_specs.append((i,'si',page,box,title))
schemes=[{'id':'scheme-1','title':'General mechanisms describingMSC conversion','sample_context_ids':['author-mechanism'],'evidence':[ev('main',2,'Scheme1')],'source_fact_ids':[SID+'-scheme1-stoichiometry'],'atomic_geometry_claim':False,'paths':['MSC⇌20[InP]monomer+17In(O2CR)3;path1toQDs','monomer+additionalMSC;path2toQDs','MSC+P(SiMe3)3 aggregation/assembly;path3toQDs']},{'id':'scheme-2','title':'Competing pathways dependent ontemperature/additive','sample_context_ids':['author-mechanism'],'evidence':[ev('main',4,'Scheme2 andfootnotea')],'source_fact_ids':[SID+'-scheme2-model'],'atomic_geometry_claim':False,'paths':['MSC+X⇌monomer1+[InPX]fragment','fragment→off-pathdecomposition','path1monomer1→QDs','path2combinedspecies→QDs','higher-temperaturepath3via monomer2'],'footnote':'Δcrit(130–150°C) is lowest temperature givingQD formation with significant nonproductive decomposition;Δ′>200°C full conversion. X=myristicacid or indium myristate.'}]
crop_specs += [('scheme-1','main',2,[.094,.791,.484,.932],'Scheme1 andtitle'),('scheme-2','main',4,[.094,.082,.484,.299],'Scheme2 andcompletefootnote'),('table-1','main',5,[.515,.547,.907,.675],'MainTable1 complete numericcells'),('graphical-abstract','main',1,[.58,.255,.89,.425],'Graphicalabstract; conceptual/citedcluster depiction, no newcoordinates'),('acid-preparation','main',7,[.092,.154,.486,.548],'Labeledacid preparation, completeanalyticalNMR andcitedMSC substitution'),('s38-fit-boxes','si',24,[.703,.17,.896,.532],'S38 three Gaussianfitboxes at readable scale'),('s39-fit-boxes','si',25,[.703,.098,.901,.469],'S39 three Gaussianfitboxes at readable scale')]
# A source equation inventory includes explicitly drawn chemical/model relations as schemes and all30 printed regressions/Gaussian boxes.
equations += [{'id':'scheme1-relation','raw_expression':'In37P20(O2CR)51 ⇌ 20[InP] + 17In(O2CR)3','source_context':'proposed dissolution bookkeeping','evidence':[ev('main',2,'Scheme1')],'numerical_recalculation_performed':False}]

# Extract exact cited references from supplied pages into local structured records. No cited papers are fetched.
readers={role:PdfReader(d['source_path'])for role,d in docs.items()}
payload=[]
for role,r in readers.items():
 for j,page in enumerate(r.pages,1):
  raw=page.extract_text()or''
  payload.append({'id':f'{SID}-{role}-p{j:02d}','document_role':role,'pdf_page':j,'text':raw,'evidence':[ev(role,j,'complete private extracted page text')],'public_export_allowed':False})
save('source-render/complete-source-payloads.json',{'schema':'mattersyn-private-full-source-payloads/1','source_id':SID,'public_export_allowed':False,'pages':payload})
reftexts=[]
for page in [7,8]:
 tx=readers['main'].pages[page-1].extract_text();tx=tx.split('■ REFERENCES')[-1] if page==7 else tx
 tx=tx.split('Inorganic Chemistry Article')[0]
 reftexts.append((page,tx))
refs=[]
for page,tx in reftexts:
 for m in re.finditer(r'\((\d+)\)\s*(.*?)(?=\(\d+\)\s|\Z)',tx,re.S):
  n=int(m.group(1));refs.append({'id':f'main-reference-{n}','number':n,'raw_citation':m.group(2).strip(),'evidence':[ev('main',page,f'Printed reference{n}')],'access_level':'Citation in supplied article only; cited document not retrieved','conflict_ids':['C12']if n==56 else[]})
assert [x['number']for x in refs]==list(range(1,57))
conflicts=[{'id':i,'title':t,'description':d,'status':'unresolved_source_discrepancy','source_fact_ids':[x['id']for x in facts if i in x['conflict_ids']]}for i,t,d in A.CONFLICTS]
gaps=[{'id':i,'title':t,'description':d,'status':'unreported_or_unverified','source_fact_ids':[x['id']for x in facts if i in x['gap_ids']]}for i,t,d in A.GAPS]
for entry in conflicts+gaps:entry['evidence']=list({json.dumps(e,sort_keys=True):e for f in facts if f['id']in entry['source_fact_ids']for e in f['evidence']}.values())
sf={'schema':'mattersyn-source-facts/1','source_id':SID,'doi':DOI,'title':A.TITLE,'authors':A.AUTHORS,'year':2019,'author':AUTHOR,'created_at':datetime.now(timezone.utc).isoformat(),'source_generation':1,'bundle_sha256':prep['bundle_sha256'],'source_scope':'All8main+25matchedSIpages read andvisuallyinspected; author extraction, independentauditpending.','facts':facts,'materials':materials,'stocks':stocks,'protocols':protocols,'sample_contexts':samples,'figures':figures,'schemes':schemes,'equations':equations,'conflicts':conflicts,'missingness':gaps,'references':refs,'tables_file':'source-tables.json','independent_audit_status':'pending','canonical_status':'not authored','training_eligibility':False,'atomic_model_status':'No current product atomic coordinate/CIF supplied or admitted'}
save('source-facts.json',sf)
save('intake-identity.json',{'schema':'mattersyn-intake-identity/1','source_id':SID,'doi':DOI,'title':A.TITLE,'authors':A.AUTHORS,'year':2019,'journal':'Inorganic Chemistry','volume':'58','pages':'803–810','online_publication_date':'2018-12-26','source_generation':1,'bundle_sha256':prep['bundle_sha256'],'file_copies':[{k:v for k,v in d.items()if k!='pages'}for d in docs.values()],'pairing_status':'matched_by_actual_title_authors_content_and_main_SI_declaration','evidence':[ev('main',1,'Article title/authors/DOI'),ev('main',7,'Associated content declaration'),ev('si',1,'On the Conversion of InP Clusters to Quantum Dots; identicalthreeauthors'),ev('si',3,'Matching labeledMSC studies'),ev('si',24,'Matching Scherrer study')],'recipe_present':True,'recipe_evidence':[ev('main',6,'Representative conversion'),ev('main',7,'Complete labeledacid preparation')],'no_source_downloads':True})

# Crops are direct PDFium rendering, never re-drawn or edited scientific image data.
assetdir=P/'reader-assets';assetdir.mkdir(exist_ok=True)
assets=[];renders={}
for aid,role,page,box,title in crop_specs:
 key=(role,page)
 if key not in renders:
  document=pdfium.PdfDocument(docs[role]['source_path']);pg=document[page-1];im=pg.render(scale=220/72).to_pil().convert('RGB');renders[key]=im;pg.close();document.close()
 im=renders[key];w,h=im.size;b=[round(box[0]*w),round(box[1]*h),round(box[2]*w),round(box[3]*h)]
 path=assetdir/(aid+'.png');im.crop(tuple(b)).save(path)
 figure=next((f for f in figures if f['id']==aid),None)
 assets.append({'id':'asset-'+SID+'-'+aid,'object_id':aid,'title':title,'path':str(path),'sha256':sha(path),'document_role':role,'source_sha256':docs[role]['sha256'],'pdf_page':page,'printed_page':802+page if role=='main'else page,'crop_box_normalized':box,'crop_box_render_pixels':b,'render_dpi':220,'renderer':'pypdfium2/PDFium','rendered_page_dimensions':[w,h],'pixel_dimensions':[b[2]-b[0],b[3]-b[1]],'contains_complete_source_page':False,'source_transform':'Direct rectangularcrop from faithfulPDFiumrender; no scientificpixelredrawing','evidence':[ev(role,page,title)],'sample_context_ids':figure['sample_context_ids']if figure else ['author-mechanism']if aid.startswith('scheme')or aid=='graphical-abstract'else ['acid-isolated']if aid=='acid-preparation'else ['scherrer150']if aid=='s38-fit-boxes'else ['scherrer250']if aid=='s39-fit-boxes'else['additive-fit'],'author_visual_inspection':'pending_final_crop_review','publication_approved':False})
save('original-assets-manifest.json',{'schema':'mattersyn-original-assets/1','source_id':SID,'assets':assets,'full_source_pages_public':False,'asset_review_scope':'Source pagesallread; finalselectedcropsawaitauthorvisualcheck','independent_audit_status':'pending'})
# Contact sheets for navigation; native crops remain available for actual small-text inspection.
contactdir=P/'source-render'/'crop-contacts';contactdir.mkdir(exist_ok=True)
for g in range(math.ceil(len(assets)/6)):
 group=assets[g*6:g*6+6];canvas=Image.new('RGB',(1500,1500),'#dddddd');draw=ImageDraw.Draw(canvas)
 for j,a in enumerate(group):
  x=(j%3)*500;y=(j//3)*750;im=Image.open(a['path']);thumb=ImageOps.contain(im,(480,695));canvas.paste(thumb,(x+(500-thumb.width)//2,y+30));draw.text((x+8,y+8),a['object_id'],fill='black')
 canvas.save(contactdir/f'contact-{g+1:02d}.png')

units=[]
def unit(i,kind,title,evidence,targets,summary):units.append({'id':SID+'-unit-'+i,'kind':kind,'title':title,'evidence':evidence,'source_payload_ids':[f'{SID}-{e["document_role"]}-p{e["pdf_page"]:02d}'for e in evidence],'extraction_targets':targets,'summary':summary,'coverage_status':'authored_pending_independent_audit'})
for j,f in enumerate(facts):unit('fact-'+f['id'].removeprefix(SID+'-'),'scientific_or_context_claim',f['title'],f['evidence'],[{'file':'source-facts.json','json_pointer':f'/facts/{j}'}],f['claim'])
for j,f in enumerate(figures):unit(f['id'],'figure',f['title'],f['evidence'],[{'file':'source-facts.json','json_pointer':f'/figures/{j}'}],f.get('annotations',json.dumps(f.get('panels',{}),ensure_ascii=False)))
for j,x in enumerate(schemes):unit(x['id'],'scheme',x['title'],x['evidence'],[{'file':'source-facts.json','json_pointer':f'/schemes/{j}'}],'Proposedmechanism; exactoriginalandfootnote retained.')
for j,x in enumerate(tables):unit(x['id'],'numeric_table_or_listing',x['title'],x['evidence'],[{'file':'source-tables.json','json_pointer':f'/tables/{j}'}],'Everytypedcellretainsitsownsourcepagelocatorandrawtoken.')
for j,x in enumerate(equations):unit(x['id'],'printed_equation',x['raw_expression'],x['evidence'],[{'file':'source-facts.json','json_pointer':f'/equations/{j}'}],x['source_context'])
for j,x in enumerate(refs):unit(x['id'],'reference',f'Reference{x["number"]}',x['evidence'],[{'file':'source-facts.json','json_pointer':f'/references/{j}'}],'Exactcitationpreserved; citedpaperunread.')
unit('graphical-abstract','conceptual_figure','Graphicalabstract',[ev('main',1,'Graphicalabstract')],[{'file':'original-assets-manifest.json','asset_id':'asset-'+SID+'-graphical-abstract'}],'Sourceillustration/summary, not newly qualifiedcoordinates.')
for page in [1,2]:unit(f'si-contents-{page}','source_contents','SI title/contents',[ev('si',page,'Identity and printedcontents')],[{'file':'source-render/complete-source-payloads.json','private_payload_id':f'{SID}-si-p{page:02d}'}],'Contentslistis retainedprivately withnumberingconflicts; actualcaptionscontrolfigureIDs.')
save('source-inventory.json',{'schema':'mattersyn-source-inventory/1','source_id':SID,'title':A.TITLE,'doi':DOI,'source_documents':[{k:v for k,v in d.items()if k!='pages'}for d in docs.values()],'semantic_units':units,'units':units,'counts':{'semantic_units':len(units),'facts':len(facts),'materials':len(materials),'stocks':len(stocks),'stock_components':sum(len(x['components'])for x in stocks),'protocols':len(protocols),'operations':sum(len(x['operations'])for x in protocols),'sample_contexts':len(samples),'figures':len(figures),'schemes':len(schemes),'tables_or_numeric_listings':len(tables),'table_numeric_cells':sum(x['numeric_cell_count']for x in tables),'equations':len(equations),'references':len(refs),'original_crops':len(assets)},'fact_ids':[f['id']for f in facts],'figure_ids':[f['id']for f in figures],'table_ids':[x['id']for x in tables],'source_conflicts':conflicts,'remaining_gaps':gaps,'private_payload_path':'source-render/complete-source-payloads.json','public_source_text_allowed':False,'independent_audit_status':'pending'})
pages=[]
for role,d in docs.items():
 for pg in d['pages']:
  p=copy.deepcopy(pg);p.update(document_role=role,text_read=True,visual_review=True,actual_reading_scope='Completeoriginalpageincludingcaptions,notes,plotsandtables; finalsmallfitboxesreadfromnativecrops.',source_unit_ids=[u['id']for u in units if any(e['document_role']==role and e['pdf_page']==pg['pdf_page']for e in u['evidence'])],original_asset_ids=[a['id']for a in assets if a['document_role']==role and a['pdf_page']==pg['pdf_page']]);pages.append(p)
save('page-coverage.json',{'schema':'mattersyn-page-coverage/1','source_id':SID,'author':AUTHOR,'source_generation':1,'source_sha256':{r:d['sha256']for r,d in docs.items()},'pages':pages,'actual_text_pages_read':33,'actual_visual_pages_inspected':33,'curve_digitization_performed':False,'independent_audit_claim':False})
print(json.dumps({'counts':read(P/'source-inventory.json')['counts'],'facts_quantities':sum(len(x['quantities'])for x in facts),'crop_contacts':math.ceil(len(assets)/6)},indent=2))
