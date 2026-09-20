"""Private source authoring. Source-specific content is in source_author_data.py."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
import json,hashlib,re,copy,math,logging
import pypdfium2 as pdfium
from pypdf import PdfReader
from PIL import Image,ImageOps,ImageDraw
import source_author_data as A
logging.getLogger('pypdf').setLevel(logging.ERROR)
P=Path(__file__).resolve().parent;SID='sasongko2025';DOI='10.1021/acs.jpcc.5c05144';AUTHOR='/root/peng1998_reader_assets'
assert not(P/'package-freeze.json').exists(),'Preserve frozen author revision.'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
prep=read(P/'source-preparation.json');docs={d['role']:d for d in prep['documents']}
for role,d in docs.items():assert sha(d['source_path'])==d['sha256'] and d['page_count']==(9 if role=='main' else 11)
def ev(role,page,loc):return {'source_id':SID+'-'+role,'document_role':role,'source_sha256':docs[role]['sha256'],'pdf_page':page,'printed_page':15341+page if role=='main'else'S'+str(page),'locator':loc}
def q(raw,unit,meaning,evidence,flags=()):
    raw=str(raw);t=raw.replace('−','-').replace(' × 10','e').replace('×10','e').replace('^','');ap=t.startswith('~');t=t.lstrip('~');comparison=None;value=None;ran=None;unc=None;ordered=None
    for op in ['<=','>=','<','>']:
        if t.startswith(op):comparison=op;t=t[len(op):];break
    if '±'in t:
        bits=t.split('±');value=float(Decimal(bits[0].strip()));unc={'value':float(Decimal(bits[1].strip())),'kind':'source ± statistic; exact statistical definition unreported','unit':unit}
    elif re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?',t):value=float(Decimal(t))
    elif '–'in t:
        ordered=[float(Decimal(z))for z in t.split('–')];ran={'min':min(ordered),'max':max(ordered)}
    return {'raw_text':raw,'value':value,'unit':unit,'uncertainty':unc,'range':ran,'ordered_endpoints':ordered,'comparison':comparison,'approximate':ap,'status':'reported'if value is not None or ran else'missing'if raw==''else'reported_text','meaning':meaning,'evidence':evidence,'conflict_ids':[f for f in flags if f.startswith('C')],'gap_ids':[f for f in flags if f.startswith('G')]}
extra={'identity':[('si',1,'Same title and seven authors')],'temperature-design':[('main',4,'Figure 3 caption')],'temperature-phase':[('main',4,'Figure 3a')],'temperature-size':[('main',4,'Figure 3d–i and inset')],'temperature-lifetimes':[('main',4,'Figure 3b')],'pl-temperature-scan':[('main',5,'Figures 4 and 5')],'raman-observation':[('si',5,'Actual Figure S2'),('si',7,'Raman discussion continuation')],'fringe':[('main',6,'Quoted reference cell')],'source-notes':[('main',6,'Associated content')],'literature-transition':[('si',8,'Table S1')],'background':[('main',2,'Introduction continuation')]}
facts=[]
for fid,role,pg,loc,title,claim,scope,qs,flags,kind in A.FACTS:
    ee=[ev(role,pg,loc)]+[ev(*x)for x in extra.get(fid,[])];flags=flags.split()
    facts.append({'id':SID+'-'+fid,'title':title,'claim':claim,'sample_scope':scope,'claim_class':kind,'evidence':ee,'quantities':[q(raw,u,m,ee,flags)for m,raw,u in qs],'conflict_ids':[f for f in flags if f.startswith('C')],'gap_ids':[f for f in flags if f.startswith('G')],'independent_audit_status':'pending'})
fb={x['id'].removeprefix(SID+'-'):x for x in facts}
def fq(fid,indices=None):
    vals=fb[fid]['quantities'];return copy.deepcopy(vals if indices is None else[vals[i]for i in indices])
matdata=[
('pbi2','Lead(II) iodide','PbI2','precursor','Supplier/purity absent; no dissolved coordination inferred.','materials'),
('formamidine-acetate','Formamidine acetate salt','CH4N2·C2H4O2; HN=CHNH2·CH3COOH','upstream precursor','99%, Sigma-Aldrich; printed neutral-pair formula retained.','materials'),
('oa','Oleic acid','OA','ligand/stock reagent','99%; no source cis/trans assay. Stock charge and QD charge distinct.','materials'),
('oam','Oleylamine','OAm','ligand','70%; technical mixture, no isomer/chain assay.','materials'),
('ode','1-Octadecene','1-ODE','solvent','>90%; no pure-batch assumption.','materials'),
('toluene','Toluene','toluene','washing solvent','99.8%, anhydrous as printed.','materials'),
('acetonitrile','Acetonitrile','acetonitrile','antisolvent','99.8%, anhydrous as printed.','materials'),
('hexane','Hexane','hexane','redispersion solvent','95%, anhydrous; no n-isomer specification.','materials'),
('nitrogen','Nitrogen','N2','synthesis atmosphere','Not automatically inherited by optical/TEM/XRD acquisition.','qd-charge'),
('fa-oleate','Prepared FA-oleate precursor','FA-oleate','prepared precursor','Operational stock identity; no solution-species geometry/concentration.','fa-hot'),
('fapbi3','Formamidinium lead iodide','FAPbI3','QD phase identity','α/β/γ source assignments depend on experiment/measurement temperature; no coordinates.','temperature-phase'),
('delta-fapbi3','Delta formamidinium lead iodide','δ-FAPbI3','observed competing phase','25C synthesis source assignment, not every product.','temperature-phase'),
('pbo2-reference','Lead dioxide cited Raman reference','PbO2','literature interpretation only','Not claimed detected in current QDs.','raman-reference'),
]
materials=[{'id':mid,'name':name,'source_formula_or_abbreviation':formula,'role':role,'scope_note':note,'source_fact_ids':[SID+'-'+fid],'evidence':fb[fid]['evidence'],'identity_qualification':'Source identity only; molecular/atomic illustration review not performed.'}for mid,name,formula,role,note,fid in matdata]
stocks=[{'id':'fa-oleate-stock','name':'Prepared FA-oleate in OA/ODE','components':[{'material_id':'formamidine-acetate','role':'precursor','amount_quantities':fq('fa-charge',[0])},{'material_id':'oa','role':'ligand/reaction medium','amount_quantities':fq('fa-charge',[1])},{'material_id':'ode','role':'solvent','amount_quantities':fq('fa-charge',[2])}],'quantities':fq('fa-charge'),'final_volume':None,'concentration':None,'storage':None,'subsequent_transfer':fq('qd-inject'),'preparation':'60C/30min vacuum then135C/2h N2; 0.51mL transfer does not set the stock final volume.','source_fact_ids':[SID+'-fa-charge',SID+'-fa-vacuum',SID+'-fa-hot'],'evidence':fb['fa-charge']['evidence']}]
for ratio in [1,10,20]:
    ee=fb['wash-formulation']['evidence'];stocks.append({'id':f'wash-1-{ratio}','name':f'Acetonitrile:toluene 1:{ratio} washing formulation','components':[{'material_id':'acetonitrile','role':'antisolvent','amount':None,'parts':q('1','volume_parts','acetonitrile parts',ee)},{'material_id':'toluene','role':'solvent','amount':None,'parts':q(str(ratio),'volume_parts','toluene parts',ee)}],'quantities':[q('1','volume_parts','acetonitrile parts',ee),q(str(ratio),'volume_parts','toluene parts',ee)],'final_volume':None,'concentration':None,'storage':None,'preparation':'Alternative wash composition only; absolute amounts and premixing procedure unspecified.','source_fact_ids':[SID+'-wash-formulation'],'evidence':ee})
samples=[]
def sample(i,label,fid,kind='observation_context',cond=None,phase=None,parents=()):
    samples.append({'id':i,'label':label,'kind':kind,'condition_scope':cond or{},'reported_phase_scope':phase,'reported_whole_composition':None,'parent_context_ids':list(parents),'source_fact_ids':[SID+'-'+fid],'evidence':fb[fid]['evidence'],'physical_batch_join':'Unknown; a shared optimized condition is not an exact shared aliquot or replicate.','atomic_structure_supplied':False})
sample('fa-stock','Prepared FA precursor','fa-hot','prepared_stock')
for ratio in [2,3,4]:sample(f'ligand-1-{ratio}',f'Figure1 OAm:OA1:{ratio}','ligand-design','reaction_condition_context',{'growth_temperature_C':100,'OAm_OA_volume_parts':[1,ratio],'acetonitrile_toluene_volume_parts':[1,20]},'Source FAPbI3 diffraction assignment; phase fractions not quantified')
for ratio in [1,10,20]:sample(f'wash-1-{ratio}',f'Figure2 acetonitrile:toluene1:{ratio}','wash-design','purification_condition_context',{'growth_temperature_C':100,'OAm_OA_volume_parts':[1,3],'acetonitrile_toluene_volume_parts':[1,ratio]})
for temp in [25,50,100]:sample(f'growth-{temp}',f'Figure3 growth{temp}C','temperature-design','reaction_condition_context',{'growth_temperature_C':temp,'OAm_OA_volume_parts':[1,3],'acetonitrile_toluene_volume_parts':[1,20]},'α-FAPbI3 + δ-FAPbI3 + PbI2'if temp==25 else'α-FAPbI3 source assignment')
for i,l,f,k in [('crude','Post-injection crude dispersion','qd-inject','process_fraction'),('first-precipitate','Retained first precipitate','wash-spin','process_fraction'),('washing-waste','S1 washing-waste vials','washing-photo','discarded_fraction_observation'),('hexane-redispersion','Hexane redispersion','redisperse','process_fraction'),('final-supernatant','Stored final supernatant','clarify-spin','retained_fraction'),('temperature-pl','80–430K PL experiment','pl-temperature-scan','characterization_context'),('temperature-raman','S2 80–190K Raman experiment','raman-range','characterization_context'),('aging-350','S3 350K aging experiment','thermal-stability','characterization_context'),('gamma-reference','Quoted gamma reference cell','cited-cell-gamma','literature_structure_context'),('beta-reference','Quoted beta reference cell','cited-cell-beta','literature_structure_context'),('alpha-reference','Quoted alpha reference cell','cited-cell-alpha','literature_structure_context'),('phase-model','Scheme1 phase/emission interpretation','scheme-model','author_model')]:sample(i,l,f,k)
for i in range(1,12):sample('table-s1-row-'+str(i),'Table S1 '+('current study'if i==11 else'cited specimen')+' row'+str(i),'literature-transition','current_study_summary'if i==11 else'literature_context')
def op(i,title,fid,inputs,outputs,indices=None,missing=(),retained=None):return {'id':i,'action':title,'description':fb[fid]['claim'],'inputs':inputs,'outputs':outputs,'source_fact_ids':[SID+'-'+fid],'quantities':fq(fid,indices),'evidence':fb[fid]['evidence'],'missing_fields':list(missing),'retained_fraction':retained}
fa=[op('fa-charge','Charge formamidine acetate, OA and ODE','fa-charge',['formamidine-acetate','oa','ode'],['fa-charge-mixture']),op('fa-vacuum-hold','Vacuum hold','fa-vacuum',['fa-charge-mixture'],['fa-degassed'],missing=['vacuum pressure']),op('fa-nitrogen-hold','N2 high-temperature hold','fa-hot',['fa-degassed','nitrogen'],['fa-oleate-stock'])]
qd=[op('lead-charge-degas','Charge and degas PbI2/ODE','qd-charge',['pbi2','ode','nitrogen'],['lead-degassed'],missing=['degassing pressure']),op('lead-preheat','Preheat lead precursor','qd-preheat',['lead-degassed'],['lead-hot']),op('add-oa','Inject selected OA volume','qd-ligands',['lead-hot','oa'],['lead-oa'],[0,1,2,4]),op('add-oam','Inject OAm after OA','qd-ligands',['lead-oa','oam'],['ligated-lead'],[3,4]),op('cool-equilibrate','Cool to selected growth temperature and hold','qd-equilibrate',['ligated-lead'],['growth-ready']),op('inject-fa','Inject FA precursor','qd-inject',['growth-ready','fa-oleate-stock'],['growing-qd']),op('prompt-cool','Promptly cool to room temperature','qd-inject',['growing-qd'],['crude'],[],['post-injection dwell','numeric room temperature','cooling rate'])]
workup=[op('add-wash','Wash with selected acetonitrile:toluene formulation','wash-formulation',['crude','selected-wash'],['washed-dispersion'],missing=['absolute solvent volumes','repetition count']),op('first-spin','Centrifuge and retain precipitate','wash-spin',['washed-dispersion'],['first-precipitate','washing-waste'],retained='first precipitate'),op('redisperse-hexane','Redisperse precipitate in hexane','redisperse',['first-precipitate','hexane'],['hexane-redispersion'],missing=['hexane volume']),op('second-spin','Clarify by centrifugation','clarify-spin',['hexane-redispersion'],['final-supernatant','second-precipitate'],retained='supernatant'),op('store-supernatant','Store final supernatant','clarify-spin',['final-supernatant'],['stored-supernatant'],[],['storage duration/temperature/concentration'])]
protocols=[{'id':'fa-oleate-preparation','title':'FA-oleate preparation','kind':'upstream_preparation','operations':fa,'sample_ids':['fa-stock']},{'id':'qd-synthesis-family','title':'Selected-condition FAPbI3 synthesis','kind':'synthesis_condition_family','operations':qd,'sample_ids':[f'ligand-1-{i}'for i in[2,3,4]]+[f'growth-{i}'for i in[25,50,100]],'condition_scope_note':'Keep the figure-specific one-factor comparisons separate; do not generate all27 combinations or imply replicates.'},{'id':'purification-family','title':'Two-fraction purification','kind':'workup','operations':workup,'sample_ids':['wash-1-1','wash-1-10','wash-1-20','final-supernatant']}]
for pid,title,fid,ss in [('xrd','Powder diffraction','xrd-method',['growth-25','growth-50','growth-100']),('trpl','TRPL acquisition','trpl-method',['growth-25','growth-50','growth-100']),('tem','TEM/ImageJ acquisition','tem-method',['growth-25','growth-50','growth-100']),('temperature-pl','Variable-temperature PL and Lorentzian analysis','pl-temperature-scan',['temperature-pl']),('temperature-raman','Variable-temperature Raman','raman-range',['temperature-raman']),('thermal-aging','350K optical aging','thermal-stability',['aging-350'])]:
    if pid in ['xrd','trpl']:ss=[f'ligand-1-{i}'for i in[2,3,4]]+[f'wash-1-{i}'for i in[1,10,20]]+ss
    protocols.append({'id':pid,'title':title,'kind':'measurement_or_analysis','operations':[op(pid+'-acquire',title,fid,ss,[pid+'-data'],missing=['See source acquisition missingness G5'])],'sample_ids':ss})
    if pid in ['temperature-pl','temperature-raman','thermal-aging']:
        operation=protocols[-1]['operations'][0];operation['source_fact_ids'].append(SID+'-temperature-method');operation['evidence']+=copy.deepcopy(fb['temperature-method']['evidence'])

tables=[]
def make_table(i,title,headers,rows,role,pg,loc,notes=()):
    obj={'id':i,'title':title,'column_headers':headers,'rows':rows,'evidence':[ev(role,pg,loc)],'footnotes':list(notes),'cell_count':sum(len(r['cells'])for r in rows),'numeric_cell_count':sum(c['value']is not None or c['range']is not None for r in rows for c in r['cells']),'independent_numerical_audit':'pending'};tables.append(obj);return obj
def row(i,scope,values,role,pg,loc,units,meanings=None):return {'id':i,'sample_context':scope,'cells':[q(v,u,(meanings or units)[j],[ev(role,pg,f'{loc}; row{i}; column{j+1}')])for j,(v,u)in enumerate(zip(values,units))]}
rows=[]
for ratio,w1,w2,life in [('2','.56','.60','~95'),('3','.37','.44','~150'),('4','.71','.78','~70')]:rows.append(row('ligand-'+ratio,'ligand-1-'+ratio,['1',ratio,w1,w2,life],'main',2,'Figure1 labels/text',['volume_parts','volume_parts','deg 2theta (axis)','deg 2theta (axis)','ns'],['OAm parts','OA parts','(001) FWHM','(002) FWHM','average PL lifetime']))
make_table('ligand-numeric','Figure1 ligand-series numerical results',['OAm parts','OA parts','(001) width','(002) width','lifetime'],rows,'main',2,'Figure1 and associated text')
rows=[]
for ratio,w1,w2,life in [('1','.48','.53','80'),('10','.42','.48','135'),('20','.37','.44','150')]:rows.append(row('wash-'+ratio,'wash-1-'+ratio,['1',ratio,w1,w2,life],'main',3,'Figure2 labels/text',['volume_parts','volume_parts','deg 2theta (axis)','deg 2theta (axis)','ns'],['acetonitrile parts','toluene parts','(001) FWHM','(002) FWHM','average PL lifetime']))
make_table('wash-numeric','Figure2 washing-series numerical results',['acetonitrile parts','toluene parts','(001) width','(002) width','lifetime'],rows,'main',3,'Figure2 and associated text')
rows=[]
for temp,diam,width,life in [('25','7.6 ± 2.4','5.7','~60'),('50','9.5 ± 1.6','3.7','~70'),('100','10.4 ± 1.1','2.7','~150')]:rows.append(row('growth-'+temp,'growth-'+temp,[temp,diam,width,life,'20'],'main',4,'Figure3d–i; lifetimes main3',['degC','nm','nm','ns','nm'],['growth temperature','mean dimension ± source spread','histogram FWHM','average lifetime','TEM scale bar']))
make_table('growth-numeric','Figure3 size and lifetime comparison',['growth temperature','dimension ± spread','histogram FWHM','lifetime','bar'],rows,'main',4,'Figure3 plus prose main3',['Source does not define the statistical meaning of ± or state a particle count.'])
rows=[]
for tag,interval,s1,s2 in [('gamma','80–140','-7.9e-5','4.01e-4'),('beta','140–250','4.32e-4','2.29e-4'),('alpha-enhanced','250–350','3.97e-4','1.69e-4'),('alpha-decline','350–430','7.26e-4','3.35e-4')]:rows.append(row(tag,'temperature-pl',[interval,s1,s2],'main',4 if tag in['gamma','beta']else 5 if tag=='alpha-enhanced'else 6,'Figure5 regime discussion',['K','eV/K','eV/K'],['temperature regime','peak-energy slope','FWHM slope']))
make_table('pl-slopes','All stated temperature-dependent optical slopes',['temperature regime','energy slope','FWHM slope'],rows,'main',4,'Main4–6 Figure5 discussion',['Intervals describe adjacent source regimes; no double counting of boundary measurements implied.'])
rows=[]
for phase,group,vals in [('gamma','P4/mbm',['8.88','8.88','6.28']),('beta','P4/mbm',['8.92','8.92','6.33']),('alpha','Pm3m',['6.36','6.36','6.36'])]:
    rr=row(phase,phase+'-reference',vals,'main',6,'Quoted cell parameters citing mainref15',['angstrom']*3,['a','b','c']);rr.update(space_group_raw=group,coordinate_source='Quoted reference parameters, no supplied atomic positions');rows.append(rr)
make_table('reference-cells','Quoted phase-reference cell parameters',['a','b','c'],rows,'main',6,'Scheme1 discussion',['No current QD cell refinement, fractional coordinates, occupancies or CIF.'])
comparison=[
('FAPbI3 (bulk)','6','140','285','synchrotron XRD and steady-state PL',None),
('FAPbI3 (bulk)','7','130','270','synchrotron XRD, neutron diffraction, and steady-state PL',None),
('FAPbI3 (bulk)','8','140','285','neutron diffraction',None),
('FAPbI3 (single crystals)','9','150','260–280','XRD',None),
('FAPbI3 (single crystals)','10','140','280','Differential Scanning Calorimetry',None),
('FAPbI3 (powder)','11','140','285','neutron diffraction',None),
('(FAPbI3)0.85(MAPbBr3)0.15 (thin film)','12','90','260','XRD, steady-state and time-resolved PL',None),
('FAPbI3 (nanocrystals = 13.3 nm)','13','140','','steady-state and time-resolved PL','13.3'),
('FAPbI3 (nanocrystals = 15.6 nm)','14','140','','UV-Vis, steady-state, and time-resolved PL','15.6'),
('FAPbI3 (nanocrystals = 40 nm)','15','110','250','XRD, steady-state, and time-resolved PL','40'),
('This study (QDs = 10 nm)',None,'140','250','Raman and steady-state PL','10'),
]
rows=[]
for n,(label,ref,t1,t2,method,size)in enumerate(comparison,1):
    rr=row('s1-'+str(n),'table-s1-row-'+str(n),[str(n),label,t1,t2,method],'si',8,'TableS1',['row_number','source specimen text','K','K','source method text'],['row number','sample','gamma to beta','beta to alpha','instruments']);rr.update(reference_id='si-reference-'+ref if ref else None,source_scope='current study summary'if n==11 else'cited literature only',raw_sample_cell=label+(' [superscript '+ref+']'if ref else''),additional_quantities=[])
    if size:rr['additional_quantities'].append(q(size,'nm','size printed inside sample cell',[ev('si',8,'TableS1 row'+str(n)+' sample cell')]))
    if n==7:rr['additional_quantities'] += [q('0.85','formula_fraction','FAPbI3 fraction as written',[ev('si',8,'TableS1 row7')]),q('0.15','formula_fraction','MAPbBr3 fraction as written',[ev('si',8,'TableS1 row7')])]
    if n==9:rr['conflict_ids']=['C3']
    rows.append(rr)
make_table('table-s1','Phase-transition literature comparison',['NO','SAMPLE','gamma to beta (K)','beta to alpha (K)','INSTRUMENTS'],rows,'si',8,'Full TableS1',['Every raw cell and citation marker is retained; blank transition cells have null values, not zero.','Current-study 10nm is the table summary; TEM mean10.4±1.1nm is separately retained.','Row9 cited title is inconsistent with the row FAPbI3 label; unresolved C3.'])
equations=[{'id':'lifetime-eq2','raw_expression':'τ_avg = (Σ[i=1..n] A_i τ_i²)/(Σ[i=1..n] A_i τ_i)','printed_number':'(2)','source_context':'Triple-exponential average lifetime','parameter_definitions':{'A_i':'fit amplitude','τ_i':'component lifetime','n':'summation limit; prose states triple exponential'},'evidence':[ev('si',4,'Printed equation(2)')],'numerical_recalculation_performed':False,'conflict_ids':['C5']},{'id':'aging-fit','raw_expression':'PL_Intensity(t) = -0.026(t) + 1','source_context':'350K normalized intensity, t in hours','evidence':[ev('si',9,'FigureS3b printed linear fit')],'parameter_definitions':{'t':'hours','PL_Intensity':'normalized intensity'},'numerical_recalculation_performed':False}]
figures=[
{'id':'figure-1','role':'main','page':2,'title':'Ligand ratio: XRD, steady-state PL and TRPL','sample_context_ids':['ligand-1-2','ligand-1-3','ligand-1-4'],'panels':{'a':'XRD; all six printed widths transcribed','b':'Normalized PL versus energy/wavelength; no peak digitization','c':'TRPL; source average lifetimes in main text'}},
{'id':'figure-2','role':'main','page':3,'title':'Washing-ratio XRD and TRPL','sample_context_ids':['wash-1-1','wash-1-10','wash-1-20'],'panels':{'a':'XRD; all six widths transcribed','b':'TRPL; no invented component lifetimes'}},
{'id':'figure-3','role':'main','page':4,'title':'Growth-temperature diffraction, PL, TEM and distributions','sample_context_ids':['growth-25','growth-50','growth-100'],'panels':{'a':'▲PbI2 and #δ-FAPbI3 labels at25C; source plane labels retained','b':'TRPL','c':'Normalized PL','d':'25C TEM20nm bar','e':'50C TEM20nm bar','f':'100C TEM20nm bar; insetd(002)=6.38Å','g':'25C D_ave7.6±2.4nm,FWHM5.7nm','h':'50C D_ave9.5±1.6nm,FWHM3.7nm','i':'100C D_ave10.4±1.1nm,FWHM2.7nm'}},
{'id':'figure-4','role':'main','page':5,'title':'80–430K absolute and normalized PL maps','sample_context_ids':['temperature-pl'],'panels':{'a':'Absolute PL intensity scale×10⁴','b':'Normalized PL intensity; source phase boundaries140/250K'}},
{'id':'figure-5','role':'main','page':5,'title':'PL energy, width and intensity versus temperature','sample_context_ids':['temperature-pl'],'panels':{'a':'Peak-energy trends','b':'FWHM trends','c':'Integrated PL; phase boundaries140/250K and enhancement to350K'}},
{'id':'figure-s1','role':'si','page':5,'title':'Washing waste at three ligand ratios','sample_context_ids':['washing-waste'],'panels':{'vials':'1:2,1:3,1:4 OAm:OA; waste photograph, not retained product'}},
{'id':'figure-s2','role':'si','page':5,'title':'80–190K low-frequency Raman','sample_context_ids':['temperature-raman'],'panels':{'a':'50–300cm−1 Raman curves; labels80/140/150/190K','b':'Raman peak position and FWHM versus temperature; no curve digitization'}},
{'id':'figure-s3','role':'si','page':9,'title':'Thermal PL stability at350K','sample_context_ids':['aging-350'],'panels':{'a':'300K red reference;350K times0,30,60,90,120,150,180,210min','b':'Normalized PL intensity versus hours; printed fit−0.026t+1'}},
]
for fig in figures:fig.update(evidence=[ev(fig['role'],fig['page'],fig['id']+' complete graphic and caption')],raw_curves_digitized=False)
schemes=[{'id':'scheme-1','title':'Temperature-dependent phase and PL model','sample_context_ids':['phase-model','gamma-reference','beta-reference','alpha-reference'],'paths':['γ-tetragonal → β-tetragonal at140K','β-tetragonal → α-cubic at250K','α thermal expansion with PL enhancement through350K','α excessive expansion and nonradiative decline beyond350K'],'evidence':[ev('main',6,'Scheme1')],'atomic_geometry_claim':False}]
crop_specs=[
('figure-1','main',2,[.515,.07,.916,.721]),('figure-2','main',3,[.08,.187,.488,.446]),('figure-3','main',4,[.08,.073,.916,.639]),('figure-4','main',5,[.08,.07,.487,.493]),('figure-5','main',5,[.52,.069,.916,.757]),('scheme-1','main',6,[.514,.071,.917,.532]),('graphical-abstract','main',1,[.515,.334,.916,.47]),
('figure-s1','si',5,[.114,.102,.919,.491]),('figure-s2','si',5,[.114,.5,.918,.857]),('figure-s3','si',9,[.114,.142,.919,.426]),('table-s1','si',8,[.113,.099,.92,.704]),('materials','si',3,[.114,.137,.914,.344]),('fa-preparation','si',3,[.114,.355,.914,.49]),('qd-preparation','si',3,[.114,.502,.914,.761]),('qd-workup','si',3,[.114,.763,.914,.895]),('characterization-equation','si',4,[.114,.101,.92,.552]),('raman-context','si',6,[.114,.1,.921,.288])]
# These are source excerpts, not recreated figures or full-page public copies.
assets=[];raster={};adir=P/'reader-assets';adir.mkdir(exist_ok=True)
for oid,role,pg,box in crop_specs:
    if (role,pg)not in raster:
        dd=pdfium.PdfDocument(docs[role]['source_path']);pp=dd[pg-1];raster[(role,pg)]=pp.render(scale=220/72).to_pil().convert('RGB');pp.close();dd.close()
    im=raster[(role,pg)];w,h=im.size;b=[round(box[0]*w),round(box[1]*h),round(box[2]*w),round(box[3]*h)];path=adir/(oid+'.png');im.crop(tuple(b)).save(path)
    obj=next((f for f in figures+schemes if f['id']==oid),None)
    ss=obj['sample_context_ids']if obj else['phase-model']if oid=='graphical-abstract'else['table-s1-row-'+str(i)for i in range(1,12)]if oid=='table-s1'else['fa-stock']if oid=='fa-preparation'else['crude']if oid=='qd-preparation'else['first-precipitate','final-supernatant']if oid=='qd-workup'else['temperature-raman']if oid.startswith('raman')else[]
    assets.append({'id':'asset-'+SID+'-'+oid,'object_id':oid,'path':str(path),'sha256':sha(path),'document_role':role,'source_sha256':docs[role]['sha256'],'pdf_page':pg,'printed_page':15341+pg if role=='main'else'S'+str(pg),'crop_box_normalized':box,'crop_box_render_pixels':b,'pixel_dimensions':[b[2]-b[0],b[3]-b[1]],'rendered_page_dimensions':[w,h],'render_dpi':220,'renderer':'pypdfium2/PDFium','contains_complete_source_page':False,'evidence':[ev(role,pg,oid+' direct original excerpt')],'sample_context_ids':ss,'source_transform':'Direct rectangular crop from faithful PDFium rendering. No scientific redrawing.','author_visual_inspection':'pending_final_crops','publication_approved':False})
save('original-assets-manifest.json',{'schema':'mattersyn-original-assets/1','source_id':SID,'assets':assets,'full_source_pages_public':False,'independent_audit_status':'pending'})
contacts=P/'source-render/crop-contacts';contacts.mkdir(exist_ok=True)
for g in range(math.ceil(len(assets)/6)):
    canvas=Image.new('RGB',(1500,1500),'#ddd');draw=ImageDraw.Draw(canvas)
    for j,a in enumerate(assets[g*6:g*6+6]):
        x=(j%3)*500;y=(j//3)*750;im=Image.open(a['path']);small=ImageOps.contain(im,(480,690));canvas.paste(small,(x+(500-small.width)//2,y+35));draw.text((x+7,y+8),a['object_id'],fill='black')
    canvas.save(contacts/f'contact-{g+1:02}.png')

readers={role:PdfReader(d['source_path'])for role,d in docs.items()};payload=[]
for role,r in readers.items():
    for j,p in enumerate(r.pages,1):payload.append({'id':f'{SID}-{role}-p{j:02}','document_role':role,'pdf_page':j,'text':p.extract_text()or'','evidence':[ev(role,j,'Complete private source page text')],'public_export_allowed':False})
save('source-render/complete-source-payloads.json',{'schema':'mattersyn-private-full-source-payloads/1','source_id':SID,'public_export_allowed':False,'pages':payload})
refs=[]
for role,pages in [('main',[7,8,9]),('si',[9,10,11])]:
    for pg in pages:
        tx=readers[role].pages[pg-1].extract_text()or''
        if pg==pages[0]:tx=tx.split('REFERENCES')[-1]if role=='main'else tx.split('Reference')[-1]
        tx=tx.split('The Journal of Physical Chemistry C')[0]if role=='main'else re.sub(r'\bS'+str(pg)+r'\s*$','',tx)
        for m in re.finditer(r'^\s*\(([1-9]\d*)\)\s*(?=[A-Z])(.*?)(?=^\s*\([1-9]\d*\)\s*(?=[A-Z])|\Z)',tx,re.S|re.M):
            n=int(m.group(1));refs.append({'id':f'{role}-reference-{n}','number':n,'document_role':role,'raw_citation':m.group(2).strip(),'evidence':[ev(role,pg,f'Printed reference{n}')],'access_level':'Citation in supplied source only; cited paper not retrieved'})
    assert [r['number']for r in refs if r['document_role']==role]==list(range(1,75 if role=='main'else 16)),(role,[r['number']for r in refs if r['document_role']==role])
conflicts=[{'id':i,'title':t,'description':d,'status':'unresolved_source_discrepancy','source_fact_ids':[f['id']for f in facts if i in f['conflict_ids']]}for i,t,d in A.CONFLICTS]
gaps=[{'id':i,'title':t,'description':d,'status':'unreported_or_unverified','source_fact_ids':[f['id']for f in facts if i in f['gap_ids']]}for i,t,d in A.GAPS]
for x in conflicts+gaps:x['evidence']=list({json.dumps(e,sort_keys=True):e for f in facts if f['id']in x['source_fact_ids']for e in f['evidence']}.values())
sf={'schema':'mattersyn-source-facts/1','source_id':SID,'doi':DOI,'title':A.TITLE,'authors':A.AUTHORS,'year':2025,'author':AUTHOR,'created_at':datetime.now(timezone.utc).isoformat(),'source_generation':1,'bundle_sha256':prep['bundle_sha256'],'source_scope':'All9main+11matchedSI pages read and visually inspected; author extraction pending separate audit.','facts':facts,'materials':materials,'stocks':stocks,'protocols':protocols,'sample_contexts':samples,'figures':figures,'schemes':schemes,'equations':equations,'tables_file':'source-tables.json','references':refs,'conflicts':conflicts,'missingness':gaps,'independent_audit_status':'pending','canonical_status':'not authored','training_eligibility':False,'atomic_model_status':'No supplied current QD atomic coordinates/CIF; cited reference cells and scheme remain contextual.'}
save('source-facts.json',sf)
save('source-tables.json',{'schema':'mattersyn-source-tables/1','source_id':SID,'author':AUTHOR,'tables':tables,'total_cells':sum(t['cell_count']for t in tables),'total_numeric_cells':sum(t['numeric_cell_count']for t in tables),'additional_sample_cell_quantities':sum(len(r.get('additional_quantities',[]))for t in tables for r in t['rows']),'curves_digitized':False,'independent_audit_status':'pending'})
save('intake-identity.json',{'schema':'mattersyn-intake-identity/1','source_id':SID,'doi':DOI,'title':A.TITLE,'authors':A.AUTHORS,'year':2025,'journal':'The Journal of Physical Chemistry C','volume':'129','pages':'15342–15350','publication_date':'2025-08-07','received_date':'2025-07-24','revised_date':'2025-07-30','accepted_date':'2025-07-31','source_generation':1,'bundle_sha256':prep['bundle_sha256'],'file_copies':[{k:v for k,v in d.items()if k!='pages'}for d in docs.values()],'pairing_status':'matched_by_actual_title_authors_main_SI_declaration_and_experimental_content','evidence':[ev('main',1,'Title, all authors, DOI and journal'),ev('main',6,'Associated content'),ev('si',1,'Same title and authors'),ev('si',3,'Matching FAPbI3 ligand/wash/temperature synthesis')],'recipe_present':True,'recipe_evidence':[ev('si',3,'FA-oleate preparation and full QD synthesis/workup')],'no_source_downloads':True})
units=[]
def unit(i,kind,title,ee,target,summary):units.append({'id':SID+'-unit-'+i,'kind':kind,'title':title,'evidence':ee,'source_payload_ids':[f'{SID}-{e["document_role"]}-p{e["pdf_page"]:02}'for e in ee],'extraction_targets':[target],'summary':summary,'coverage_status':'authored_pending_independent_audit'})
for key,arr in [('facts',facts),('figures',figures),('schemes',schemes),('equations',equations),('references',refs)]:
    for j,x in enumerate(arr):unit(x['id'],key,x.get('title',x.get('raw_expression',x.get('id'))),x['evidence'],{'file':'source-facts.json','json_pointer':f'/{key}/{j}'},x.get('claim',x.get('source_context','Exact source object retained with its own specimen/reference scope.')))
for j,t in enumerate(tables):unit(t['id'],'numeric_table_or_listing',t['title'],t['evidence'],{'file':'source-tables.json','json_pointer':f'/tables/{j}'},'All raw cells and field-specific evidence retained.')
unit('graphical-abstract','conceptual_figure','Graphical abstract',[ev('main',1,'Graphical abstract')],{'file':'original-assets-manifest.json','asset_id':'asset-'+SID+'-graphical-abstract'},'Source conceptual drawing, not coordinate data.')
unit('si-index','source_contents','SI index',[ev('si',2,'Printed index')],{'file':'source-render/complete-source-payloads.json','private_payload_id':SID+'-si-p02'},'Actual TableS1/S3 pages supersede inconsistent index only for locating source; conflict remains recorded.')
unit('publisher-ad','non_scientific_source_element','Publisher advertising',[ev('main',9,'CAS Biofinder advertisement')],{'file':'source-render/complete-source-payloads.json','private_payload_id':SID+'-main-p09'},'Non-scientific publisher advertising, excluded from scientific facts and public crop selection.')
counts={'semantic_units':len(units),'facts':len(facts),'materials':len(materials),'stocks':len(stocks),'stock_components':sum(len(s['components'])for s in stocks),'protocols':len(protocols),'operations':sum(len(p['operations'])for p in protocols),'sample_contexts':len(samples),'figures':len(figures),'schemes':len(schemes),'tables_or_numeric_listings':len(tables),'table_cells':sum(t['cell_count']for t in tables),'table_numeric_cells':sum(t['numeric_cell_count']for t in tables),'equations':len(equations),'references':len(refs),'original_crops':len(assets)}
save('source-inventory.json',{'schema':'mattersyn-source-inventory/1','source_id':SID,'title':A.TITLE,'doi':DOI,'source_documents':[{k:v for k,v in d.items()if k!='pages'}for d in docs.values()],'semantic_units':units,'units':units,'counts':counts,'fact_ids':[f['id']for f in facts],'figure_ids':[f['id']for f in figures],'table_ids':[t['id']for t in tables],'source_conflicts':conflicts,'remaining_gaps':gaps,'private_payload_path':'source-render/complete-source-payloads.json','public_source_text_allowed':False,'independent_audit_status':'pending'})
pages=[]
for role,d in docs.items():
    for p in d['pages']:
        page=copy.deepcopy(p);page.update(document_role=role,text_read=True,visual_review=True,actual_reading_scope='Complete actual source page, including text, figures, tables, notes and references.',source_unit_ids=[u['id']for u in units if any(e['document_role']==role and e['pdf_page']==p['pdf_page']for e in u['evidence'])],original_asset_ids=[a['id']for a in assets if a['document_role']==role and a['pdf_page']==p['pdf_page']]);pages.append(page)
save('page-coverage.json',{'schema':'mattersyn-page-coverage/1','source_id':SID,'author':AUTHOR,'source_generation':1,'source_sha256':{k:d['sha256']for k,d in docs.items()},'pages':pages,'actual_text_pages_read':20,'actual_visual_pages_inspected':20,'curve_digitization_performed':False,'independent_audit_claim':False})
print(json.dumps({'counts':counts,'fact_quantities':sum(len(f['quantities'])for f in facts),'source_table_additional_quantities':sum(len(r.get('additional_quantities',[]))for t in tables for r in t['rows'])},indent=2))



