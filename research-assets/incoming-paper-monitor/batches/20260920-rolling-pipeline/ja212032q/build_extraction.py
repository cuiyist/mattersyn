"""Build local author extraction; no independent approval or canonical publication is implied."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
import json,re,hashlib,copy,math
from PIL import Image,ImageOps,ImageDraw
import pypdfium2
import source_author_data as A
P=Path(__file__).resolve().parent
SID='ghosh2012';DOI='10.1021/ja212032q';NOW=datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,data):(P/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
payload=json.loads((P/'complete-source-payloads.json').read_bytes());docs={d['document_id']:d for d in payload['documents']}
for f in payload['source_copies']:assert sha(f['source_path'])==f['sha256']
def ev(role,page,loc):return {'source_id':SID+'-'+role,'document_role':role,'source_sha256':docs[role]['source_sha256'],'pdf_page':page,'printed_page':9633+page if role=='main' else 'S'+str(page),'locator':loc}
def q(raw,unit,meaning,role,page,loc,flags=()):
 s=str(raw).strip();t=s.replace('−','-').replace('–','-');v=u=rg=cmp=parts=None;ap=False;status='reported'
 if t.startswith('~'):ap=True;t=t[1:]
 m=re.match(r'^(>=|<=|>|<|≥|≤)',t)
 if m:cmp={'≥':'>=','≤':'<='}.get(m[1],m[1]);t=t[len(m[1]):].strip()
 n=r'[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'
 if re.fullmatch(n,t):v=float(Decimal(t))
 elif re.fullmatch(n+r'±'+n,t):v,u=[float(Decimal(a))for a in t.split('±')]
 elif re.fullmatch(n+'-'+n,t):a,b=t.split('-');rg={'min':float(a),'max':float(b)}
 elif unit in['ratio_parts','weight_ratio_parts'] and re.fullmatch(r'\d+:\d+',t):parts=[int(a)for a in t.split(':')];status='reported_ratio_parts'
 else:status='reported_text'
 if unit=='identifier':v=None;status='reported_identifier'
 return {'raw_text':s,'value':v,'unit':unit,'uncertainty':u,'uncertainty_definition':'not specified'if u is not None else None,'range':rg,'comparison':cmp,'approximate':ap,'components':parts,'status':status,'meaning':meaning,'evidence':[ev(role,page,loc)],'conflict_ids':[f for f in flags if f.startswith('C')],'gap_ids':[f for f in flags if f.startswith('G')]}
facts=[]
for fid,role,page,loc,title,claim,scope,qs,flags,kind in A.FACTS:
 facts.append({'id':SID+'-'+fid,'title':title,'claim':claim,'sample_scope':scope,'claim_class':kind,'evidence':[ev(role,page,loc)],'quantities':[q(raw,unit,name,role,page,loc,flags)for name,raw,unit in qs],'conflict_ids':[f for f in flags if f.startswith('C')],'gap_ids':[f for f in flags if f.startswith('G')],'independent_audit_status':'pending'})
fb={f['id'].removeprefix(SID+'-'):f for f in facts}
fb['lattice-background']['evidence'].append(ev('main',2,'Introduction continuation: CdSe/ZnS 12%'))
fb['lattice-background']['quantities'][1]['evidence']=[ev('main',2,'Introduction continuation: CdSe/ZnS 12%')]
fb['ode-cycling']['evidence'].append(ev('main',5,'Solubility cycling continuation: >11 ML incompletely clears'))
fb['ode-cycling']['quantities'][2]['evidence']=[ev('main',5,'Solubility cycling continuation: >11 ML incompletely clears')]
fb['blinking-examples']['evidence'].append(ev('si',9,'Figure S8 continued caption: separate dot-index 6 examples'))
fb['no-added-amine']['quantities'][1]['evidence']=[ev('main',4,'Table 2 row 6 >6 ML faceting')]
fb['no-added-amine']['evidence'].append(ev('main',4,'Table 2 row 6 >6 ML faceting'))
materials=[{'id':i,'name':name,'source_formula_or_abbreviation':form,'role':role,'scope_note':note,'evidence':[ev('main',p,'Materials / General Methods'if p==2 else'Optimized Synthetic Protocol')]}for i,name,form,role,note,p in A.MATERIALS]
tables=[]
def table(i,title,cols,rows,role,page,scope,notes):
 for ir,r in enumerate(rows):
  for ic,c in enumerate(r['cells']):c['id']=f'{i}-r{ir+1:03}-c{ic+1:02}'
 t={'id':i,'title':title,'columns':cols,'rows':rows,'sample_scope':scope,'evidence':[ev(role,page,i)],'notes':notes,'author_transcription':'All native rows visually read by extraction author; distinct numerical audit pending.','independent_numerical_audit':'pending'};tables.append(t);return t
rows=[]
for ir,(st,su,ct,cu,y5,y11,y15)in enumerate([('10','min','10','min','~20','~10','~5'),('10','min','3','h','>45','~40','~15'),('3','h','10','min','~35','~10','~6'),('1','h','3','h','~70','~25','~20'),('3','h','1','h','~25','~10','~5')],1):
 cells=[]
 for col,raw,unit in [('post_S',st,su),('post_Cd',ct,cu),('QY_5ML',y5,'%'),('QY_11ML',y11,'%'),('QY_15ML',y15,'%')]:cells.append({'column':col,**q(raw,unit,col,'main',3,f'Table 1 row {ir} {col}',('C1','C2'))})
 rows.append({'row_label':str(ir),'sample_id':f'anneal-row-{ir}','cells':cells})
table('table-1','Influence of shell-addition anneal protocol',['post_S','post_Cd','QY_5ML','QY_11ML','QY_15ML'],rows,'main',3,'anneal-comparison',['All five schedules, bounds and approximate QYs preserved.','Three QY columns apply at 5, 11 and 15 ML respectively; no unique core/batch identity given.','The preferred S 1 h/Cd 2.5 h protocol is not one of these rows.'])
t2=[
('Octadecene / Primary Amine','Early','Rounded at thin shells, but polydisperse at thick shells','80:20','Low','ode-primary'),
('Octadecane / Primary Amine','Middle','Improved structural dispersity','74:26','Low','od-primary'),
('Octadecane / Primary Amine (longer anneal times)','Middle to late','Rounded to faceted hexagonal (>15 MLs)','~85:15','Mod-High','od-long-anneal'),
('Octadecane / Primary Amine (extreme dilution)','None','Half-moons','60:40','Low','od-extreme-dilution'),
('Octadecane / Secondary Amine','None','Octahedral','~70:30','None','od-secondary'),
('Octadecane / No Added Amine','Early','Faceted hexagonal (>6 MLs)','~80:20','Mod-High','od-no-added-amine')]
rows=[]
for ir,(*values,sid)in enumerate(t2,1):
 cs=[{'column':col,**q(raw,'weight_ratio_parts'if col=='WZ_ZB'else None,col,'main',4,f'Table 2 row {ir} {col}',('C5',)if ir==5 else())}for col,raw in zip(['solvent_ligand','precipitation_onset','shape','WZ_ZB','thick_shell_QY'],values)]
 cs.append({'column':'TEM','raw_text':'Original row TEM, scale bar 10 nm','value':None,'status':'original_image','asset_id':f'table-2-tem-{ir}','evidence':[ev('main',4,f'Table 2 row {ir} TEM')]})
 rows.append({'row_label':str(ir),'sample_id':sid,'cells':cs})
table('table-2','Influence of solvent and ligand parameters',['solvent_ligand','precipitation_onset','shape','WZ_ZB','thick_shell_QY','TEM'],rows,'main',4,'solvent-ligand-series',['QY column explicitly applies to thickest shells >15 ML; Low/Mod-High/None are qualitative, not invented numeric ranges.','WZ:ZB ratios are semiquantitative phase weight fractions per SI S4 methodology.','Every original TEM image has a 10 nm bar. Exact core/shell/batch joins are absent for most rows.'])
t3=[('Excess Precursor (10%)','~None','Misshapen','Low','withdraw-10'),('Excess Precursor (1%)','Late','Rods','Mod.','withdraw-1'),('Excess Precursor (1%) + Excess Oleic Acid','Middle','Spherical/hexagonal','High','withdraw-1-oa'),('Constant Sulfur','Middle (minimal & persistent)','Rods','Low','constant-s')]
rows=[]
for ir,(*vals,sid)in enumerate(t3,1):
 cs=[{'column':col,**q(raw,None,col,'main',7,f'Table 3 row {ir} {col}')}for col,raw in zip(['stoichiometry_variation','precipitation_onset','shape','thick_shell_QY'],vals)]
 cs.append({'column':'TEM','raw_text':'Original moderately thick-shell TEM, scale bar 10 nm','value':None,'status':'original_image','asset_id':f'table-3-tem-{ir}','evidence':[ev('main',7,f'Table 3 row {ir} TEM'),ev('main',6,'Stoichiometry discussion: moderately thick shell TEM')]})
 rows.append({'row_label':str(ir),'sample_id':sid,'cells':cs})
table('table-3','Influence of reaction stoichiometry',['stoichiometry_variation','precipitation_onset','shape','thick_shell_QY','TEM'],rows,'main',7,'stoichiometry-series',['Percentages are aliquot-removal fractions, not direct molar precursor excess.','QYs concern thickest shells >15 ML. Main p.6 explicitly says the TEM images depict moderately thick shells because image quality was better. Never join TEM and QY as a verified exact same-thickness specimen.','Qualitative QY labels retained as text; scale bars 10 nm.'])
cols=['core_diameter','shell_monolayers_TEM','volume_TEM','A1','T1','A2','T2','A3','T3','Tavg'];units=['nm','monolayer','nm^3','dimensionless','ns','dimensionless','ns','dimensionless','ns','ns']
rows=[]
for ir,line in enumerate(A.TABLE_S1.splitlines(),1):
 ts=line.split();assert len(ts)==10
 rows.append({'row_label':str(ir),'sample_id':f'lifetime-row-{ir:02}','source_raw_line':line,'cells':[{'column':c,**q(raw,u,c,'si',6,f'Table S1 row {ir} {c}')}for c,u,raw in zip(cols,units,ts)]})
table('table-s1','Coefficients and lifetimes',cols,rows,'si',6,'lifetime-table',['All eighteen rows and 180 numeric cells preserve printed decimal precision.','ML and volume derive from TEM/model accounting; amplitudes and lifetimes are fit-derived averages, not atomic coordinates.','Individual displayed amplitudes are rounded. Recalculation from mean/rounded coefficients is diagnostic only, not a replacement for the reported average lifetime.','Rows are not force-joined to 5.5 nm/16.9 ML Figure S7/S8 specimens.'])
rows=[]
for label,raw,note in [('nu(O-H)','3300-2500','Printed descending range retained.'),('nu(CH) of -CH=CH-','3000',''),('nu_as(CH3)','2954',''),('nu_as(CH2)','2920',''),('nu_s(CH3)','2866',''),('nu_s(CH2)','2850',''),('nu(C=O)','1705',''),('nu(C=C)','1650','v. weak'),('delta(CH2)','1456',''),('delta(C-O-H)','1427',''),('nu(C-OH)','1283','')]:
 cell=q(raw,'cm^-1',label,'si',2,'Figure S2 inset '+label)
 if label=='nu(O-H)':cell['range']={'min':2500.0,'max':3300.0};cell['source_order']='descending'
 rows.append({'row_label':label,'qualifier':note,'cells':[{'column':'wavenumber',**cell}]})
table('table-s2-inset','Oleic-acid characteristic FTIR bands',['wavenumber'],rows,'si',2,'pure-oa-reference',['This is the unnumbered inset table inside Figure S2, not a source-named Table S2.','Wavenumber unit is cm−1 from adjacent spectrum. Functional symbols normalized to nu/delta, with source original retained.','Very weak qualifier applies to C=C 1650 cm−1.'])
write('source-tables.json',{'schema':'mattersyn-source-tables/1','source_id':SID,'author':'/root/backlog_eta','created_at':NOW,'tables':tables,'independent_audit_status':'pending','structure_model_qualification':False})

def op(i,action,ins,outs,fs,retained=None,missing=()):return {'id':i,'action':action,'inputs':ins,'outputs':outs,'retained_fraction':retained,'source_fact_ids':[SID+'-'+f for f in fs],'quantities':[copy.deepcopy(x)for f in fs for x in fb[f]['quantities']],'evidence':[e for f in fs for e in fb[f]['evidence']],'missing_fields':list(missing),'independent_audit_status':'pending'}
specs=[
('core-standard-route','Standard 3 or 4 nm CdSe core route','synthesis',[
('core-charge','Charge TOPO, ODE and Cd-oleate',['topo','ode','cd-oleate'],['core-feed'],['core-charge'],None,['Cd-oleate preparation']),
('core-evacuate','Evacuate at room temperature then 80 °C; heat under argon',['core-feed','argon'],['heated-core-feed'],['core-degas'],None,['pressure','argon flow']),
('core-inject','Rapidly inject TOP-Se/oleylamine/ODE and lower to growth temperature',['heated-core-feed','top-se-injection'],['core-growth'],['core-inject'],None,['injection duration','TOP-Se preparation']),
('core-grow-cool','Grow for several minutes then cool to room temperature',['core-growth'],['core-crude'],['core-standard'],None,['exact duration for each size']),
('core-isolate','Precipitate with ethanol, centrifuge and repeat; disperse retained particles in hexane',['core-crude','ethanol','hexane'],['core-3-or-4'],['core-wash'],'core-3-or-4',['centrifuge settings','solvent amounts','yield'])]),
('core-small-variant','Cold-toluene early-quench core variant','synthesis_variant',[
('small-quench','Use common initial charge/evacuation/injection, then quench rapidly with cold toluene',['core-growth','toluene'],['core-2p2'],['core-small'],'core-2p2',['quench temperature','quench volume','exact delay'])]),
('core-large-variant','Additional-feed large-core variant','synthesis_variant',[
('large-feed','Use common initial steps; after initial growth add extra Cd-oleate/TOP-Se dropwise, then raise temperature',['core-growth','cd-oleate','top-se'],['core-5p5'],['core-large'],'core-5p5',['dropwise rate','extra precursor formulation','yield'])]),
('optimized-shell-route','Preferred CdSe/nCdS shell route','synthesis',[
('shell-charge','Charge washed cores, oleylamine and OD',['cdse-core','ola','od'],['shell-feed'],['shell-charge'],None,['individual core batch']),
('shell-passivate','Prepassivate Se-rich cores with one Cd monolayer equivalent',['shell-feed','cd-oleate-stock'],['passivated-cores'],['shell-passivation'],None,['delivered volume']),
('shell-cycles','Add separate S and Cd stocks with specified anneals and evolving Cd:OA ratios',['passivated-cores','s-od-stock','cd-oleate-stock'],['growing-shells'],['shell-stocks','shell-ligand-switch','shell-anneal'],None,['per-layer doses','exact switch cycle']),
('shell-withdraw','Remove one percent after each completed cycle; keep planned precursor charges',['growing-shells'],['remaining-shell-growth','withdrawn-aliquots'],['shell-withdraw'],'remaining-shell-growth',['aliquot destination','layerwise remaining amount']),
('shell-purify','Precipitate with ethanol and redisperse particles in hexane',['remaining-shell-growth','ethanol','hexane'],['optimized-cdse-cds'],['shell-wash-qy'],'optimized-cdse-cds',['centrifuge settings','volumes','yield'])]),
('anneal-series','Five comparative post-S/post-Cd schedules','parameter_comparison',[
('compare-anneals','Vary post-precursor anneals using the five Table 1 schedules',['cdse-core','sulfur','cd-oleate'],['anneal-series-particles'],['anneal-qy-summary','anneal-asymmetry'],None,['complete per-row formulation','core identity'])]),
('solvent-ligand-series','Solvent/ligand/dilution comparisons','parameter_comparison',[
('compare-ode-od','Compare ODE/OD primary-amine shell conditions and optional late OD dilution',['cdse-core','ode','od','ola','oa','sulfur','cd-oleate'],['solvent-series-particles'],['ode-cycling','od-cycling','od-late-dilution'],None,['complete per-row protocol']),
('extreme-dilution','Start at the reported extreme dot dilution',['cdse-core','od','ola','oa','sulfur','cd-oleate'],['half-moon-particles'],['extreme-dilution'],None,['full precursor schedule']),
('compare-ligands','Compare primary, secondary and no-added-amine preparations',['cdse-core','od','ola','doa','oa','sulfur','cd-oleate'],['ligand-series-particles'],['ligand-amounts','secondary-shape','no-added-amine'],None,['exact secondary-amine amount','all row batch labels'])]),
('stoichiometry-series','Withdrawal and OA-excess comparisons','parameter_comparison',[
('compare-withdrawals','Remove one or ten percent per shell cycle without reducing shell precursor doses',['growing-shells'],['withdrawal-series-particles','withdrawn-aliquots'],['withdrawal-series'],None,['full per-layer accounting']),
('withdraw-oa','Combine one-percent withdrawals with increased OA at the reported transition span',['growing-shells','oa'],['withdrawal-oa-particles','withdrawn-aliquots'],['withdrawal-oa'],None,['exact switch cycle'])]),
('constant-s-variant','All sulfur supplied at the start','synthesis_variant',[
('constant-s-grow','Supply sulfur for thirteen layers at the beginning; add Cd layerwise with four-hour intervals',['cdse-core','sulfur','cd-oleate'],['constant-s-particles'],['constant-s-protocol','constant-s-outcome'],'constant-s-particles',['complete initial formulation','exact aliquots'])]),
('ftir-procedure','Particle and pure-ligand FTIR','characterization',[
('ftir-purify-cast','Wash particles six times; cast particle or ligand/hexane references onto diamond and evaporate',['cdse-cds','oa','ola','doa','top','topo','hexane','diamond'],['ftir-film'],['ftir-acquisition'],None,['sample-specific wash solvents','casting volumes']),
('ftir-acquire','Acquire ATR-FTIR with stated resolution and averaging',['ftir-film'],['ftir-data'],['ftir-acquisition'],None,['precise row sample links'])]),
('tem-procedure','TEM morphology/size measurement','characterization',[
('tem-acquire','Acquire JEOL 2010 TEM images',['cdse-cds'],['tem-data'],['tem-acquisition'],None,['grid','voltage','deposition'])]),
('xrd-procedure','PXRD and semiquantitative phase fitting','characterization',[
('xrd-deposit','Deposit particles on background-less silicon',['cdse-cds','silicon'],['xrd-specimen'],['xrd-acquisition'],None,['loading']),
('xrd-acquire-fit','Acquire PXRD and fit phase fractions using Jade WPF/Rietveld',['xrd-specimen'],['xrd-phase-data'],['xrd-acquisition','xrd-phase-fit'],None,['refinement outputs','coordinate files'])]),
('ensemble-optics','Ensemble absorption/emission and relative QY','characterization',[
('ensemble-acquire','Measure absorption/emission and compare QY to Rhodamine 6G',['cdse-cds','r6g'],['ensemble-optical-data'],['ensemble-acquisition','shell-wash-qy'],None,['matching absorbance','concentration'])]),
('single-dot-procedure','Single-dot imaging and threshold analysis','characterization',[
('single-deposit','Dilute hexane dispersion and drop-cast on acetone-cleaned glass',['cdse-cds','hexane','acetone','glass'],['single-dot-slide'],['single-dot-preparation'],None,['dilution','deposition volume']),
('single-acquire','Illuminate continuously and acquire CCD time series',['single-dot-slide','liquid-nitrogen'],['single-dot-images'],['single-dot-excitation','single-dot-frames'],None,['exact power per specimen']),
('single-analyze','Classify each dot/frame against background threshold and use ever-emitting population',['single-dot-images'],['blinking-data'],['single-dot-analysis','nonblinking-definition'],None,['raw trajectories'])]),
('lifetime-procedure','Pulsed PL lifetime measurement','characterization',[
('lifetime-deposit','Cast rough particle films on acetone-cleaned glass',['cdse-cds','hexane','acetone','glass'],['lifetime-film'],['lifetime-preparation'],None,['film thickness']),
('lifetime-acquire-fit','Acquire TCSPC, fit triexponentials and report mean lifetime',['lifetime-film','immersion-oil'],['lifetime-data'],['lifetime-excitation','lifetime-detection','lifetime-table-contract'],None,['raw fit files'])]),
('core-only-control','Separate seven-nanometer core-only optical control','contextual_control',[
('core-control-wash','Compare washed and unwashed 7 nm core emission; assess diluted slide visibility',['core-only-7nm','hexane','glass'],['core-only-control-data'],['core-only-control'],None,['core synthesis','exact washing/deposition'])])]
protocols=[{'id':i,'title':title,'kind':kind,'operations':[op(*o)for o in ops],'complete_laboratory_sop':False,'independent_audit_status':'pending'}for i,title,kind,ops in specs]
# Avoid attaching characterization or product-output quantities to physical charge/processing steps.
for pr in protocols:
 for o in pr['operations']:
  if o['id']=='shell-purify':o['quantities']=[x for x in o['quantities']if x['meaning']=='precipitation cycles']
  if o['id']=='ensemble-acquire':o['quantities']=[x for x in o['quantities']if x['meaning']!='precipitation cycles']
protocols[1]['inherited_operation_refs']=[{'protocol_id':'core-standard-route','operation_id':x}for x in['core-charge','core-evacuate','core-inject','core-isolate']]
protocols[1]['inheritance_note']='Early quench replaces the standard several-minute growth/cooling operation; common workup is inherited as described, without new quantities.'
protocols[2]['inherited_operation_refs']=[{'protocol_id':'core-standard-route','operation_id':x}for x in['core-charge','core-evacuate','core-inject','core-isolate']]
protocols[2]['inheritance_note']='Extended growth/feed replaces standard growth; common workup is inherited. Exact dropwise rate remains absent.'
for pr in protocols:
 if pr['id']=='anneal-series':pr['source_table_ids']=['table-1'];pr['variant_rows']=[{'sample_id':r['sample_id'],'table_row':r['row_label']}for r in tables[0]['rows']]
 if pr['id']=='solvent-ligand-series':pr['source_table_ids']=['table-2'];pr['variant_rows']=[{'sample_id':r['sample_id'],'table_row':r['row_label']}for r in tables[1]['rows']]
 if pr['id']=='stoichiometry-series':pr['source_table_ids']=['table-3'];pr['variant_rows']=[{'sample_id':r['sample_id'],'table_row':r['row_label']}for r in tables[2]['rows']]
stocks=[
{'id':'top-se-injection','components':[{'material_id':'top-se','role':'precursor'},{'material_id':'ola','role':'ligand'},{'material_id':'ode','role':'solvent'}],'source_fact_id':SID+'-core-inject','quantities':[copy.deepcopy(x)for x in fb['core-inject']['quantities']if x['unit']!='degC'],'concentration':None,'scope':'Whole injection mixture charges; no exact final volume or upstream TOP-Se synthesis.'},
{'id':'s-od-stock','components':[{'material_id':'sulfur','role':'solute'},{'material_id':'od','role':'solvent'}],'source_fact_id':SID+'-shell-stocks','quantities':[copy.deepcopy(fb['shell-stocks']['quantities'][0])],'concentration':copy.deepcopy(fb['shell-stocks']['quantities'][0]),'scope':'0.2 M elemental sulfur stock, allotrope/dissolved speciation unknown; layer-specific dose absent.'},
{'id':'cd-oleate-stock','components':[{'material_id':'cd-oleate','role':'precursor'},{'material_id':'oa','role':'ligand'},{'material_id':'od','role':'solvent'}],'source_fact_ids':[SID+'-shell-stocks',SID+'-shell-ligand-switch'],'quantities':[copy.deepcopy(fb['shell-stocks']['quantities'][1]),*copy.deepcopy(fb['shell-ligand-switch']['quantities'])],'concentration':copy.deepcopy(fb['shell-stocks']['quantities'][1]),'scope':'Two source-defined Cd:OA formulations, 1:4 then 1:10; neither metal complex geometry nor per-layer amount inferred.'}]

# Explicit variants retain separate workup outputs; inherited steps stop at initial injection.
for index,stem,product in[(1,'small','core-2p2'),(2,'large','core-5p5')]:
 pr=protocols[index];pr['operations'][0]['outputs']=[stem+'-core-crude'];pr['operations'][0]['retained_fraction']=None
 pr['operations'].append(op(stem+'-isolate','Apply common ethanol precipitation/centrifugation and hexane redispersion',[stem+'-core-crude','ethanol','hexane'],[product],['core-wash'],product,['centrifuge settings','volumes','yield']))
 pr['inherited_operation_refs']=[r for r in pr['inherited_operation_refs']if r['operation_id']!='core-isolate']

equations=[
{'id':'equation-on-main','expression':'I_pix > BG + 2*sqrt(BG) => ON','meaning':'Average dot intensity per pixel is not background-subtracted; BG is frame background counts per pixel.','scope':'single-dot-analysis','evidence':[ev('main',2,'Single-NQD Imaging displayed equation')],'asset_ids':['equation-on-main']},
{'id':'equation-average-main','expression':'T_avg = sum_m(a_m*T_m^2) / sum_n(a_n*T_n)','meaning':'Reported average lifetime computed from amplitude and lifetime coefficients; fit amplitudes need not be the SI normalized printed means.','scope':'lifetime-acquisition','evidence':[ev('main',2,'Lifetime Measurements displayed equation'),ev('main',3,'Equation symbol definition')],'asset_ids':['equation-average-main']},
{'id':'equation-triexponential','expression':'y = y0 + A1*exp(-(x-x0)/T1) + A2*exp(-(x-x0)/T2) + A3*exp(-(x-x0)/T3)','meaning':'Three-component decay fit including background and time offset; original unreported fitted y0/x0 not invented.','scope':'lifetime-table','evidence':[ev('si',6,'Table S1 caption fit equation'),ev('si',7,'Figure S7 caption repeated fit equation')],'asset_ids':['equations-si-fit','equation-si-fit-repeat']},
{'id':'equation-amplitude-normalization','expression':'sum_n A_n = 1','meaning':'Normalized amplitudes; finite printed precision may sum to 0.99 or 1.01.','scope':'lifetime-table','evidence':[ev('si',6,'Table S1 caption normalization')],'asset_ids':['equations-si-fit']},
{'id':'equation-average-si','expression':'T_avg = sum_n [A_n*T_n^2 / sum_m(A_m*T_m)]','meaning':'Source reports mean component parameters and mean average lifetimes; diagnostic recomputation from means does not supersede printed values.','scope':'lifetime-table','evidence':[ev('si',6,'Table S1 caption mean-lifetime equation')],'asset_ids':['equations-si-fit']},
{'id':'equation-on-si','expression':'T = B + 2*sqrt(B)','meaning':'Threshold subtracted from selected line traces so zero counts is the threshold.','scope':'si-blinking-examples','evidence':[ev('si',9,'Figure S8 continued caption threshold')],'asset_ids':['equation-on-si']}]
references=[]
text=docs['main']['pages'][9]['text'].split('■ REFERENCES',1)[1].split('Journal of the American Chemical Society Article',1)[0]
matches=list(re.finditer(r'(?m)^\((\d+)\)\s',text));assert len(matches)==23
for j,m in enumerate(matches):
 raw=text[m.end():matches[j+1].start()if j+1<len(matches)else len(text)].strip()
 references.append({'id':'main-reference-'+m[1],'number':int(m[1]),'raw_text':raw,'citation':' '.join(raw.split()),'subreferences':[],'full_text_read':False,'evidence':[ev('main',10,'References '+m[1])]})
 if m[1]=='8':
  a,b=raw.split('(b)',1);references[-1]['subreferences']=[{'label':'8a','raw_text':a.removeprefix('(a)').strip()},{'label':'8b','raw_text':b.strip()}];references[-1]['scope_note']='Both works retained; anomalous printed year/volume in 8a not externally repaired.'
figures=[{'id':i,'title':title,'sample_scope':scope,'scope_note':note,'evidence':[ev(role,page,i+' artwork'),ev(role,cp,i+' caption')],'asset_ids':[i]}for role,page,cp,i,title,scope,note in A.FIGURES]
schemes=[{'id':'scheme-1','title':'SILAR reaction flow and controllable parameters','sample_scope':'generic-silar','scope_note':'Anion then cation in the generic drawing; blue general flow and green adjustable variables; preferred protocol separately prepassivates Cd. Diagram is conceptual, not an atomistic model.','footnotes':[{'label':'a','text':'Blue text denotes general reaction parameters and reaction flow; green text shows options for modifying specific reaction conditions to influence physicochemical and optical properties.'}],'evidence':[ev('main',3,'Scheme 1 and footnote a')],'asset_ids':['scheme-1']}]
conflicts=[{'id':i,'title':title,'description':desc,'resolution':'Retained explicitly; no numerical or identity substitution.'}for i,title,desc in A.CONFLICTS]
gaps=[{'id':i,'title':title,'description':desc,'status':'retained'}for i,title,desc in A.GAPS]
samples=[]
scopes=sorted({f['sample_scope']for f in facts}|{t['sample_scope']for t in tables}|{f['sample_scope']for f in figures}|{'generic-silar'})
for scope in scopes:
 related=[f for f in facts if f['sample_scope']==scope]
 samples.append({'id':scope,'name':scope.replace('-',' '),'scope_type':'interpretive_context'if scope.startswith(('author-','cited-'))else'comparison_or_acquisition_context','physical_sample_identity_verified':False,'source_fact_ids':[f['id']for f in related],'source_units':[t['id']for t in tables if t['sample_scope']==scope]+[f['id']for f in figures if f['sample_scope']==scope],'evidence':[e for f in related for e in f['evidence']],'parent_ids':[],'scope_note':'Source-scoped context only; matching context labels do not certify a unique batch or a cross-technique exact sample join.'})
existing={s['id']for s in samples}
for t in tables:
 for r in t['rows']:
  sid=r.get('sample_id')
  if not sid:continue
  if sid not in existing:samples.append({'id':sid,'name':t['id']+' row '+r['row_label'],'scope_type':'source_table_row','physical_sample_identity_verified':False,'parent_ids':[t['sample_scope']],'source_units':[t['id']],'evidence':t['evidence'],'scope_note':'Row-specific source context; no unique batch identifier or cross-technique sample join inferred.'});existing.add(sid)
  if t['id']=='table-s1':
   s=next(s for s in samples if s['id']==sid);s['reported_core_diameter_nm']=r['cells'][0]['value'];s['reported_shell_monolayers_TEM']=r['cells'][1]['value'];s['reported_volume_nm3_TEM']=r['cells'][2]['value'];s['scope_note']='Distinct row defined by printed core diameter and TEM-derived shell count/volume; fitted coefficients and mean lifetime belong to this row only.'
  if t['id']=='table-3':next(s for s in samples if s['id']==sid)['scope_note']='Parameter-variant context includes moderately thick-shell TEM and a separate >15 ML QY descriptor; not a verified identical specimen across modalities.'
sampleby={s['id']:s for s in samples}
for sid in['core-2p2','core-3-or-4','core-5p5']:
 sampleby[sid]['parent_ids']=['core-common'];sampleby[sid]['lineage_relation']='source-described alternative core-growth branches from the common initial charge/injection; not serial transformations between final sizes'
for r in tables[3]['rows']:
 sid=r['sample_id'];d=r['cells'][0]['value'];parent='core-2p2'if d==2.2 else'core-5p5'if d==5.5 else'core-3-or-4'
 sampleby[sid]['source_core_family']=parent;sampleby[sid]['lineage_relation']='Known reported initial core diameter; no unique synthesis-batch identity or physical-lot join is asserted.'
for f in figures:
 f['source_context_ids']={
 'figure-1':['ftir-primary-1to4','ftir-primary-1to10','ftir-secondary-thick'],
 'figure-3':['four-core-series','core-2p2','core-3-or-4','core-5p5'],
 'figure-4':['four-core-series','lifetime-table'],
 'figure-s4':['xrd-three-contexts'],
 }.get(f['id'],[f['sample_scope']])
 f['context_link_qualification']='Only explicitly reported comparison, size or figure context; no inferred same-particle/batch join across techniques.'

# Native PDF crops only. Coordinates are normalized to page size; full pages stay in source-render.
CROPS=[
('graphical-abstract','main',1,(.593,.329,.890,.496)),('scheme-1','main',3,(.515,.082,.905,.294)),
('table-1','main',3,(.515,.682,.897,.932)),('table-2','main',4,(.095,.081,.906,.562)),('table-3','main',7,(.095,.081,.485,.489)),
('figure-1','main',5,(.52,.226,.921,.434)),('figure-2','main',7,(.524,.417,.896,.689)),('figure-3','main',8,(.54,.081,.88,.632)),('figure-4','main',9,(.111,.281,.474,.496)),
('figure-s1','si',2,(.128,.205,.719,.361)),('figure-s2','si',2,(.121,.50,.833,.819)),('figure-s3','si',3,(.116,.182,.477,.286)),
('figure-s4','si',3,(.116,.354,.539,.795)),('figure-s4-caption-continuation','si',4,(.115,.089,.887,.182)),
('figure-s5','si',4,(.174,.223,.456,.479)),('figure-s6','si',5,(.174,.094,.586,.551)),
('table-s1','si',6,(.129,.109,.872,.555)),('equations-si-fit','si',6,(.115,.555,.894,.77)),
('figure-s7','si',7,(.135,.087,.727,.339)),('equation-si-fit-repeat','si',7,(.267,.446,.611,.468)),
('figure-s8','si',8,(.116,.089,.887,.808)),('figure-s8-caption-continuation','si',9,(.115,.089,.897,.2)),
('table-s2-inset','si',2,(.542,.5,.833,.819)),('equation-on-main','main',2,(.53,.511,.718,.537)),('equation-average-main','main',2,(.53,.895,.65,.932)),('equation-on-si','si',9,(.732,.164,.821,.183))]
for ir,(top,bottom)in enumerate([(.164,.226),(.228,.29),(.292,.355),(.358,.42),(.423,.485),(.49,.556)],1):CROPS.append((f'table-2-tem-{ir}','main',4,(.724,top,.840,bottom)))
for ir,(top,bottom)in enumerate([(.188,.259),(.262,.332),(.335,.406),(.412,.482)],1):CROPS.append((f'table-3-tem-{ir}','main',7,(.344,top,.462,bottom)))
(P/'reader-assets').mkdir(exist_ok=True);(P/'private').mkdir(exist_ok=True)
assets=[];pdfs={role:pypdfium2.PdfDocument(d['source_path'])for role,d in docs.items()}
for aid,role,page,box in CROPS:
 pg=pdfs[role][page-1];bitmap=pg.render(scale=4);im=bitmap.to_pil();w,h=im.size;rect=[round(v*(w if k%2==0 else h))for k,v in enumerate(box)];crop=im.crop(rect);path=P/'reader-assets'/f'{aid}.png';crop.save(path)
 assets.append({'id':aid,'path':str(path),'sha256':sha(path),'kind':'original_source_crop','whole_source_page':False,'source_role':role,'pdf_page':page,'source_sha256':docs[role]['source_sha256'],'bbox_normalized':list(box),'bbox_pixels_at_render':rect,'render_scale':4,'pixel_dimensions':list(crop.size),'evidence':[ev(role,page,aid)],'manual_visual_review':'pending final selected-crop inspection','public_import_approval':False})
 crop.close();im.close();bitmap.close();pg.close()
for pdf in pdfs.values():pdf.close()
for f in figures:f['asset_ids']=[a['id']for a in assets if a['id']in[f['id'],f['id']+'-caption-continuation']]
for t in tables:t['asset_ids']=[a['id']for a in assets if a['id']==t['id']or a['id'].startswith(t['id']+'-tem-')]
write('source-tables.json',{'schema':'mattersyn-source-tables/1','source_id':SID,'author':'/root/backlog_eta','created_at':NOW,'tables':tables,'independent_audit_status':'pending','structure_model_qualification':False})
write('original-assets-manifest.json',{'schema':'mattersyn-original-source-assets/1','source_id':SID,'author':'/root/backlog_eta','created_at':NOW,'assets':assets,'private_full_page_images':[{'document_role':role,'path':pg['render_path'],'sha256':sha(pg['render_path']),'whole_source_page':True,'public_import_approval':False}for role,d in docs.items()for pg in d['pages']],'independent_audit_status':'pending'})
for start in range(0,len(assets),6):
 subset=assets[start:start+6];out=Image.new('RGB',(2100,740*((len(subset)+1)//2)),'#e4e8ec');draw=ImageDraw.Draw(out)
 for j,a in enumerate(subset):
  im=Image.open(a['path']);im.thumbnail((1030,690));x=(j%2)*1050;y=(j//2)*740;out.paste(im,(x+(1050-im.width)//2,y+34));draw.text((x+10,y+8),a['id'],fill='black');im.close()
 out.save(P/'private'/f'crop-contact-{start//6+1:02}.png');out.close()

pairing={'schema':'mattersyn-source-pairing/1','source_id':SID,'paper_id':'10.1021_ja212032q','source_generation':2,'bundle_sha256':payload['bundle_sha256'],'author':'/root/backlog_eta','reviewed_at':NOW,'status':'content_verified_by_extraction_author_independent_audit_pending','title':A.TITLE,'authors':A.AUTHORS,'main_pages':10,'si_pages':9,'main_sha256':docs['main']['source_sha256'],'si_sha256':docs['si']['source_sha256'],'original_file_copies':payload['source_copies'],'checks':[
{'criterion':'Main identity','result':'Main first page title, six-person byline and DOI; JACS 2012, 134, 9634–9643.','evidence':[ev('main',1,'Title/byline/DOI')]},
{'criterion':'SI content identity','result':'Same title and all six authors on S1; main S1–S8/Table S1 citations match actual TEM/FTIR/XRD/blinking/lifetime content. Main p.10 explicitly declares this SI.','evidence':[ev('si',1,'Title/byline/contents'),ev('main',10,'Associated Content'),ev('main',9,'Lifetime and volume discussion')]},
{'criterion':'Copy equivalence','result':'All four original copies hashed; incoming and legacy pairs represent two unique PDFs, not four experiments.'}],
'pairing_gaps':[],'source_scope_gaps':['No raw diffraction/trajectory/fit files, atomistic coordinates or separately deposited crystal data are supplied or claimed. Cited external full texts are not read.'],'independent_audit':False}
write('pairing-review.json',pairing)
write('relevance-screening.json',{'schema':'mattersyn-evidenced-synthesis-screening/1','source_id':SID,'group_id':'10.1021_ja212032q','source_generation':2,'bundle_sha256':payload['bundle_sha256'],'author':'/root/backlog_eta','screened_at':NOW,'decision':'retain_for_full_curation','status':'recipe_present_full_supplied_pdf_extraction_author_complete_independent_audit_pending','recipe_evidence':[ev('main',3,'Optimized Synthetic Protocol'),ev('main',6,'Stoichiometry modifications')],'reason':'Quantitative CdSe core and CdS shell syntheses, three core-growth variants and extensive shell parameter comparisons; full local SI supports structure/property interpretation.','no_recipe_claim':False,'independent_audit':False,'pairing_review_sha256':sha(P/'pairing-review.json')})
coverage=[]
for role,d in docs.items():
 assert len(A.PAGE_NOTES[role])==d['page_count']
 for pg,note in zip(d['pages'],A.PAGE_NOTES[role]):
  coverage.append({'document_role':role,'pdf_page':pg['pdf_page'],'printed_page':9633+pg['pdf_page']if role=='main'else'S'+str(pg['pdf_page']),'source_sha256':d['source_sha256'],'text_read_in_full':True,'native_page_image_visually_inspected':True,'read_by':'/root/backlog_eta','scope_notes':note,'text_path':pg['text_path'],'text_sha256':sha(pg['text_path']),'render_path':pg['render_path'],'render_sha256':sha(pg['render_path']),'public_full_page_reuse_approved':False,'independent_audit':False})
write('page-coverage.json',{'schema':'mattersyn-page-coverage/1','source_id':SID,'created_at':NOW,'author':'/root/backlog_eta','pages':coverage,'supplied_pdf_pages_read':19,'supplied_pdf_pages_visually_inspected':19,'unread_supplied_pdf_pages':[],'independent_audit_status':'pending'})
counts={'facts':len(facts),'fact_quantities':sum(len(f['quantities'])for f in facts),'materials':len(materials),'stocks':len(stocks),'protocols':len(protocols),'operations':sum(len(p['operations'])for p in protocols),'tables':len(tables),'table_rows':sum(len(t['rows'])for t in tables),'table_cells':sum(len(r['cells'])for t in tables for r in t['rows']),'scalar_numeric_table_cells':sum(c.get('value')is not None for t in tables for r in t['rows']for c in r['cells']),'figures_including_graphical_abstract':len(figures),'schemes':len(schemes),'equations':len(equations),'numbered_references':len(references),'individual_reference_works':24,'sample_contexts':len(samples),'original_crops':len(assets),'page_count':19}
src={'schema':'mattersyn-source-facts/1','source_id':SID,'doi':DOI,'title':A.TITLE,'authors':A.AUTHORS,'author':'/root/backlog_eta','created_at':NOW,'source_generation':2,'bundle_sha256':payload['bundle_sha256'],'source_documents':[{'role':r,'sha256':d['source_sha256'],'pages':d['page_count']}for r,d in docs.items()],'review_status':'author_extracted_independent_audit_pending','complete_scope':'All supplied 10 main + 9 SI PDF pages; original plot data and external cited full texts are not supplied or claimed read.','counts':counts,'facts':facts,'tables':tables,'materials':materials,'stocks':stocks,'protocols':protocols,'samples':samples,'figures':figures,'schemes':schemes,'equations':equations,'references':references,'conflicts':conflicts,'gaps':gaps,'training_admission':{'approved':False,'requested_tasks':[],'exact_recipe_structure_pair':False,'atomistic_model_qualified':False}}
write('source-facts.json',src)
units=[]
for key,kind in[('facts','fact'),('tables','table'),('materials','material'),('stocks','stock'),('protocols','protocol'),('samples','sample_context'),('figures','figure'),('schemes','scheme'),('equations','equation'),('references','reference')]:
 for i,item in enumerate(src[key]):units.append({'id':kind+':'+item['id'],'source_object_id':item['id'],'type':kind,'json_pointer':'/'+key+'/'+str(i),'evidence':item.get('evidence',[]),'source_fact_ids':item.get('source_fact_ids',[])})
write('source-inventory.json',{'schema':'mattersyn-source-inventory/1','source_id':SID,'author':'/root/backlog_eta','created_at':NOW,'counts':counts,'inventory_units':units,**{k:src[k]for k in['materials','stocks','protocols','samples','figures','schemes','equations','references','conflicts','gaps']},'table_inventory':[{'id':t['id'],'rows':len(t['rows']),'cells':sum(len(r['cells'])for r in t['rows']),'scope':t['sample_scope'],'evidence':t['evidence'],'notes':t['notes']}for t in tables],'notes':['Whole pages/complete source payloads remain local-only under recognized exclusion paths.','All negative outcomes and parameter comparisons are retained; no success-only selection or cross-product experiment generation.','Table 3 TEM depicts moderately thick shells, whereas its QY column refers to >15 ML.','No atomic coordinates, exact recipe–structure training pair or independent audit approval is claimed.'],'independent_audit_status':'pending'})
print(json.dumps(counts,ensure_ascii=False))
