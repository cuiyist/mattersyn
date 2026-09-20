"""Build the private author extraction after complete manual page review.
Writes only this paper folder. Scientific review by a distinct agent is pending.
"""
from pathlib import Path
from datetime import datetime,timezone
import json,re,hashlib,copy,math
from decimal import Decimal
from PIL import Image,ImageOps,ImageDraw
import pypdfium2
import source_author_data as A

P=Path(__file__).resolve().parent
NOW=datetime.now(timezone.utc).isoformat()
SOURCE_ID='morrison2017';GROUP='10.1021_acs.inorgchem.7b01711';DOI='10.1021/acs.inorgchem.7b01711'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,obj):(P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
payload=json.loads((P/'complete-source-payloads.json').read_bytes())
docs={d['document_id']:d for d in payload['documents']}
def ev(role,page,locator):return {'source_id':SOURCE_ID+'-'+role,'document_role':role,'source_sha256':docs[role]['source_sha256'],'pdf_page':page,'printed_page':12919+page if role=='main' else 'S'+str(page),'locator':locator}
def evidence(role,page,locator):return [ev(role,page,locator)]
def q(raw,unit,meaning,role,page,locator,scale=1,conflicts=None):
    s=str(raw).strip();t=s.replace('−','-').replace('–','-');status='reported';approx=False;comparison=None;value=None;error=None;lower=None;upper=None
    for word in ['approximately ','approx. ','ca. ','about ','within ','after ']:
        if t.startswith(word):
            t=t[len(word):];approx=word in ['approximately ','approx. ','ca. ','about '];comparison={'within ':'<=','after ':'>'}.get(word);break
    if t.startswith('<'):comparison='<';t=t[1:]
    if t in ['-','---','']:
        status='not_reported'
    elif re.fullmatch(r'[+-]?\d+(?:\.\d+)?\(\d+\)',t):
        v,e=t.split('(');value=float(Decimal(v)*Decimal(str(scale)));error=float(Decimal(e[:-1])*(Decimal(10)**(-len(v.split('.')[1]) if '.' in v else 0))*Decimal(str(scale)))
    elif '±' in t:
        v,e=t.split('±');value=float(Decimal(v.strip())*Decimal(str(scale)));error=float(Decimal(e.strip())*Decimal(str(scale)))
    elif re.fullmatch(r'[+-]?\d+(?:\.\d+)?',t):value=float(Decimal(t)*Decimal(str(scale)))
    elif re.fullmatch(r'\d+(?:\.\d+)?-\d+(?:\.\d+)?',t):
        lo,hi=t.split('-');lower=float(Decimal(lo)*Decimal(str(scale)));upper=float(Decimal(hi)*Decimal(str(scale)))
    else:status='reported_text'
    if unit=='identifier':value=None;status='reported_identifier'
    return {'raw_text':s,'value':value,'unit':unit,'uncertainty':error,'range':{'min':lower,'max':upper}if lower is not None else None,'comparison':comparison,'approximate':approx,'status':status,'printed_to_value_scale':scale,'meaning':meaning,'evidence':evidence(role,page,locator),'conflict_ids':conflicts or []}

for f in payload['source_copies']:assert sha(f['source_path'])==f['sha256']
pairing={'schema':'mattersyn-source-pairing/1','source_id':SOURCE_ID,'paper_id':GROUP,'source_generation':2,'bundle_sha256':payload['bundle_sha256'],'author':'/root/backlog_eta','reviewed_at':NOW,'status':'content_verified_by_extraction_author_independent_audit_pending','title':A.TITLE,'authors':A.AUTHORS,'main_sha256':docs['main']['source_sha256'],'si_sha256':docs['si']['source_sha256'],'main_pages':10,'si_pages':17,'original_file_copies':payload['source_copies'],'checks':[
 {'criterion':'Main DOI/journal/title/authors','evidence':evidence('main',1,'Title, byline, DOI and journal footer'),'result':'10.1021/acs.inorgchem.7b01711; Inorganic Chemistry 2017,56,12920–12929; all six authors'},
 {'criterion':'SI content identity','evidence':evidence('si',1,'Title, full byline, affiliations and contents'),'result':'Exact title and six author identities match main; SI DOI not printed on cover, not claimed as independently printed.'},
 {'criterion':'Main explicitly identifies supplied SI contents','evidence':evidence('main',8,'Associated Content')+evidence('si',1,'Table of Contents'),'result':'IR, positions/ADPs/H bonds, packing, NMR, kinetics, elemental/EDS, dispersibility, XRD and HRTEM match.'},
 {'criterion':'Cross-source table/figure continuity','evidence':evidence('main',3,'Tables S1–S4 and Figures S2/S3/S6 references')+evidence('si',3,'Table S1')+evidence('si',16,'Figure S9 caption'),'result':'All referenced Figures S1–S9 and Tables S1–S5 present across S1–S17; S9 spans S15/S16.'},
 {'criterion':'Duplicate identity','result':'Four original copies verified, exactly two distinct SHA256 contents. Copies do not add pages or experiments.'}],
 'pairing_gaps':[],'source_scope_gaps':['Upstream NH4PTC and CdSe-QB procedures only cited.','CCDC 1560097 and electronic structure-factor data mentioned but not supplied as local files.'],'independent_audit':False}
write('pairing-review.json',pairing)
screen={'schema':'mattersyn-evidenced-synthesis-screening/1','source_id':SOURCE_ID,'group_id':GROUP,'source_generation':2,'bundle_sha256':payload['bundle_sha256'],'author':'/root/backlog_eta','screened_at':NOW,'status':'recipe_present_full_extraction_author_complete_independent_audit_pending','decision':'retain_for_full_curation','screening_scope':'Entire main and matched SI read; screening decision grounded in explicit procedures, not keyword score.','recipe_evidence':[ev('main',2,'Preparation of Bis(phenyldithiocarbamato)cadmium(II)'),ev('main',3,'Monolayer CdS Shell Growth on CdSe QBs'),ev('main',3,'Monitoring conversion; THF comparison')],'reason':'Explicit quantitative precursor preparation and controlled CdS-shell growth; structural and optical characterization present.','no_recipe_claim':False,'main_sha256':docs['main']['source_sha256'],'si_sha256':docs['si']['source_sha256'],'pairing_review_sha256':sha(P/'pairing-review.json'),'independent_audit':False}
write('relevance-screening.json',screen)

facts=[]
for fid,role,page,locator,title,claim,scope,quantities,conflicts in A.FACTS:
    facts.append({'id':SOURCE_ID+'-'+fid,'title':title,'claim':claim,'sample_scope':scope,'claim_class':'author_interpretation' if scope.startswith('author-') else 'cited_context' if scope.startswith('cited-') else 'reported_source_evidence','evidence':evidence(role,page,locator),'quantities':[q(raw,unit,name,role,page,locator,conflicts=conflicts)for name,raw,unit in quantities],'conflict_ids':[c for c in conflicts if c.startswith('C')],'gap_ids':[c for c in conflicts if c.startswith('G')],'independent_audit_status':'pending'})

instrument_data=[
 ('uvvis','UV–visible','PerkinElmer Lambda 950 UV/vis/NIR,150mm integrating sphere to minimize scattering',[('integrating sphere diameter','150','mm')]),
 ('pl','Photoluminescence','Horiba Fluorolog3 with Quanta-phi integration sphere',[]),
 ('powder-xrd','Powder XRD','Bruker AXS D8 ADVANCE; Cu Kα',[('radiation wavelength','1.5418','angstrom')]),
 ('ftir','FTIR','Bruker ALPHA Platinum ATR',[]),
 ('hrtem','HRTEM','JEOL JEM2100F microscope',[('electron energy','200','keV')]),
 ('eds','EDS','JEOL2000FX microscope',[('electron energy','200','keV')]),
 ('nmr','1H/13C{1H} NMR','Varian Unity Inova-500; specific frequencies in precursor characterization',[]),
 ('elemental','C/H/N/S elemental analysis','Galbraith Laboratories,Knoxville,TN',[])]
for iid,tech,details,qs in instrument_data:
    facts.append({'id':SOURCE_ID+'-instrument-'+iid,'title':tech+' acquisition','claim':details,'sample_scope':'study-wide acquisition; sample-specific assignment remains in figure/measurement entries','claim_class':'reported_acquisition','evidence':evidence('main',2,'Analyses'),'quantities':[q(raw,unit,name,'main',2,'Analyses')for name,raw,unit in qs],'conflict_ids':[],'gap_ids':[],'independent_audit_status':'pending'})

materials=[{'id':i,'name':n,'source_formula_or_abbreviation':f,'role':r,'scope_note':note,'evidence':evidence('main',page,'Materials/protocol/results as specified in linked facts')} for i,n,f,r,page,note in A.MATERIALS]
materialids={x['id']for x in materials}
factsby={f['id'].removeprefix(SOURCE_ID+'-'):f for f in facts}
def operation(oid,name,inputs,outputs,fids,retained=None,missing=None):
    fs=[factsby[x]for x in fids]
    return {'id':oid,'action':name,'inputs':inputs,'outputs':outputs,'retained_fraction':retained,'source_fact_ids':[f['id']for f in fs],'quantities':[copy.deepcopy(x)for f in fs for x in f['quantities']],'evidence':[e for f in fs for e in f['evidence']],'missing_fields':missing or [],'conflict_ids':sorted({c for f in fs for c in f['conflict_ids']}),'scope':'Reported operation or explicitly separated source branch; no independent repetition inferred. Quantity meaning distinguishes charges, conditions and observed endpoints; linked facts preserve broader context.'}
protocol_specs=[
 ('precursor-preparation','Aqueous Cd(PTC)2 precipitation','precursor_preparation',[
 ('precursor-add','Dissolve and add cadmium solution dropwise',['cdcl2','nh4ptc','water'],['precursor-slurry'],['precursor-charge'],None,['addition duration','absolute temperature','stirring rate']),
 ('precursor-stir-filter','Stir30min and vacuum filter',['precursor-slurry'],['wet-cdptc'],['precursor-workup'],'wet-cdptc',['filter pore size']),
 ('precursor-wash-dry','Water/ethanol washing and vacuum drying',['wet-cdptc','water','ethanol'],['precursor-powder'],['precursor-workup','precursor-yield'],'precursor-powder',['vacuum pressure','drying temperature'])]),
 ('precursor-crystallization','THF/hexane vapor-diffusion crystals','precursor_crystallization',[
 ('crystal-solution','Prepare printed20mmol THF solution',['cdptc','thf'],['crystal-feed'],['crystal-growth'],None,['THF volume','concentration basis']),
 ('crystal-vapor','Seal small vial inside hexane jar overnight',['crystal-feed','hexane'],['precursor-crystal'],['crystal-growth'],'precursor-crystal',['jar/vial dimensions','hexane amount','numerical duration','temperature'])]),
 ('decomposition-nmr','DMSO-d6 decomposition without added base','standalone_control',[
 ('nmr-heat','Heat Cd(PTC)2/DMSO-d6 and acquire hourly spectra',['cdptc','dmso-d6'],['nmr-time-series','powder-dmso-nmr'],['nmr-charge','nmr-evolution'],None,['tube atmosphere','heating hardware']),
 ('nmr-isolate','Centrifuge, wash precipitate and deposit for XRD',['powder-dmso-nmr','toluene','xrd-substrate'],['powder-dmso-xrd'],['nmr-powder-isolate'],'powder-dmso-xrd',['centrifuge rpm/time','drying'])]),
 ('decomposition-thf','THF CdS powder control','standalone_control',[
 ('thf-heat','Heat septum-capped THF solution',['cdptc','thf'],['powder-thf'],['thf-powder'],None,['duration']),
 ('thf-wash','Wash yellow product and deposit for XRD',['powder-thf','toluene','xrd-substrate'],['powder-thf-xrd'],['thf-powder'],'powder-thf-xrd',['recovery method','drying'])]),
 ('decomposition-dmso-hot','Narrative DMSO70°C powder experiment','partial_standalone_control',[
 ('dmso-hot','Heat in DMSO without belts',['cdptc','dmso'],['powder-dmso-hot'],['dmso-powder','powder-eds-prose'],None,['precursor amount','solvent volume','yield mass','specimen link to SI EDS'])]),
 ('excess-precursor-rt','Room-temperature excess-precursor reaction/back exchange','partial_shell_growth_branch',[
 ('rt-combine','Combine starting belts with saturated precursor/DMSO',['cdse-qb','cdptc','dmso'],['excess-shell-rt'],['rt-excess','rt-shift'],None,['absolute amounts','precursor solution volume','defined reaction room temperature']),
 ('rt-backexchange','Remove excess precursor and redisperse in neat amine',['excess-shell-rt','n-octylamine'],['excess-shell-rt-backexchanged'],['rt-shift'],None,['precursor removal technique','amine volume'])]),
 ('excess-precursor-hot','70°C excess-precursor thick-shell growth','partial_shell_growth_branch',[
 ('hot-growth','React excess precursor with CdSe belts at70°C',['cdse-qb','cdptc','dmso'],['excess-shell-hot'],['hot-excess','hot-pl','thick-morphology'],None,['exact charges/volumes','heating vessel']),
 ('hot-backexchange','Redisperse resulting belts in octylamine',['excess-shell-hot','n-octylamine'],['excess-shell-hot-amine'],['hot-pl'],None,['separation procedure','amine volume'])]),
 ('monolayer-shell','Controlled monolayer CdS growth','representative_shell_growth',[
 ('qb-wash','Three precipitate-retaining toluene wash cycles',['cdse-qb','toluene'],['washed-qb'],['qb-purify'],'washed-qb',['core concentration in0.512g dispersion']),
 ('qb-shell','Suspend in precursor/THF and heat66°C',['washed-qb','cdptc','thf'],['monolayer-shell-family'],['qb-grow','monolayer-dose'],None,['core mass/surface estimate']),
 ('qb-sample','Collect2–3drop aliquots at specified times',['monolayer-shell-family'],['monolayer-optical-aliquots'],['qb-grow','qb-aliquot'],'monolayer-optical-aliquots',['drop volume calibration']),
 ('aliquot-thf','THF dilution and precipitate recovery',['monolayer-optical-aliquots','thf'],['washed-aliquot'],['qb-aliquot'],'washed-aliquot',[]),
 ('aliquot-repassivate','Resuspend in n-octylamine',['washed-aliquot','n-octylamine'],['amine-repassivated-aliquot'],['qb-aliquot'],None,['amine volume','repassivation duration']),
 ('aliquot-toluene-wash','Repeat toluene wash and retain precipitate',['amine-repassivated-aliquot','toluene'],['optical-precipitate'],['qb-optical-wash'],'optical-precipitate',['repeat count']),
 ('aliquot-optics','Final toluene dispersion for optical spectra',['optical-precipitate','toluene'],['monolayer-optical-context'],['qb-optical-wash','monolayer-optics'],None,['final volume/concentration']),
 ('qb-tem','Separate TEM context: amine redispersion and grid deposition',['monolayer-shell-family','n-octylamine','tem-grid'],['monolayer-tem-context'],['tem-prep','tem-thickness'],None,['physical aliquot join to optical context','drying'])]),
 ('added-base-comparison','Added-aniline versus no-base NMR comparison','partial_mechanistic_control',[
 ('base-nmr','Compare50°C DMSO conversion with and without added aniline',['cdptc','dmso','aniline'],['nmr-base-comparison'],['catalyst-identity','base-rate','si-base'],None,['added base amount','precursor charge','main p5 catalyst-identity conflict'])]),
 ('single-crystal-acquisition','Precursor single-crystal diffraction','characterization',[
 ('crystal-mount-measure','Mount crystal and collect/refine diffraction',['cdptc-thf-crystal'],['precursor-crystal-structure'],['crystal-mount','crystal-refine'],None,['electronic original reflection/CIF file'])])]
protocols=[]
operation_quantity_names={
 'precursor-stir-filter':['stirring duration'],
 'precursor-wash-dry':['water wash','ethanol wash cycles','ethanol each wash','vacuum drying','isolated mass','printed isolated amount','reported yield'],
 'crystal-vapor':[],
 'thf-heat':['precursor mass','printed precursor amount','THF volume','temperature'],
 'thf-wash':['wash count','toluene each wash'],
 'rt-backexchange':['back-exchanged feature'],
 'hot-backexchange':[],
 'qb-shell':['THF solution volume','precursor concentration','temperature','ideal time','relative estimated monolayer precursor'],
 'qb-sample':['time1','time2','time3','time4','time5','aliquot'],
 'aliquot-thf':['THF dilution','centrifuge speed','centrifuge duration'],
 'aliquot-repassivate':[],
 'aliquot-optics':['absorption energy shift','PL QY','cited starting QY']}
for pid,title,kind,ops in protocol_specs:
    protocols.append({'id':pid,'title':title,'kind':kind,'operations':[operation(*o)for o in ops],'complete_laboratory_sop':False,'independent_audit_status':'pending'})
for protocol in protocols:
    for op in protocol['operations']:
        if op['id'] in operation_quantity_names:
            op['quantities']=[qv for qv in op['quantities']if qv['meaning']in operation_quantity_names[op['id']]]
        unique={}
        for qv in op['quantities']:
            unique.setdefault((qv['meaning'],qv['raw_text'],qv['unit']),qv)
        op['quantities']=list(unique.values())
stocks=[
 {'id':'cdcl2-aqueous','solute':'cdcl2','solvent':'water','source_fact_id':SOURCE_ID+'-precursor-charge','quantities':copy.deepcopy(factsby['precursor-charge']['quantities'][:3]),'concentration':None,'scope':'40mL water charged; final solution volume not independently stated.'},
 {'id':'nh4ptc-aqueous','solute':'nh4ptc','solvent':'water','source_fact_id':SOURCE_ID+'-precursor-charge','quantities':copy.deepcopy(factsby['precursor-charge']['quantities'][3:]),'concentration':None,'scope':'60mL water charged; no volumetric stock calibration.'},
 {'id':'cdptc-thf-shell','solute':'cdptc','solvent':'thf','source_fact_id':SOURCE_ID+'-qb-grow','quantities':copy.deepcopy(factsby['qb-grow']['quantities'][:2]),'concentration':q('10','mM','reported shell-growth precursor concentration','main',3,'Monolayer growth'),'scope':'2mL10mM solution; does not establish exact ratio to unknown CdSe amount.'},
 {'id':'cdptc-dmso-excess','solute':'cdptc','solvent':'dmso','source_fact_id':SOURCE_ID+'-rt-excess','quantities':copy.deepcopy(factsby['rt-excess']['quantities'][:1]),'concentration':q('ca. 40','mM','approximate saturated precursor concentration','main',4,'Attempted exchange'),'scope':'Absolute volume and precursor/core ratio unknown.'},
 {'id':'cdptc-thf-crystal-feed','solute':'cdptc','solvent':'thf','source_fact_id':SOURCE_ID+'-crystal-growth','quantities':copy.deepcopy(factsby['crystal-growth']['quantities']),'concentration':None,'scope':'Printed20mmol solution is not a defined20mM stock.','conflict_ids':['C3']}]

tables=[]
def table(tid,title,role,page,columns,rows,notes=None,scope='precursor-crystal'):
    out={'id':tid,'title':title,'sample_scope':scope,'columns':columns,'rows':rows,'notes':notes or [],'evidence':evidence(role,page,tid),'author_transcription':'Native PDF text parsed or manually entered and all table rows visually compared by extraction author.','independent_numerical_audit':'pending'};tables.append(out);return out
for page,tid,title,columns,num in [(3,'table-s1','Atomic coordinates and Ueq',['x','y','z','Ueq'],26),(4,'table-s2','Anisotropic displacement parameters',['U11','U22','U33','U23','U13','U12'],26),(5,'table-s3','Hydrogen coordinates and isotropic displacement',['x','y','z','Ueq'],20)]:
    rows=[]
    for line in docs['si']['pages'][page-1]['text'].splitlines():
        m=re.match(r'^\s*((?:Cd|S|N|C|O|H)\([^\)]+\))\s+(.+)$',line)
        if not m:continue
        tokens=m.group(2).replace('−','-').split()
        assert len(tokens)==len(columns),(tid,line)
        cells=[]
        for col,tok in zip(columns,tokens):
            unit='fractional_coordinate' if col in ['x','y','z'] else 'angstrom^2';scale=1e-4 if col in ['x','y','z'] else 1e-3
            cells.append({'column':col,**q(tok,unit,m.group(1)+' '+col,'si',page,tid+' row '+m.group(1)+' '+col,scale)})
        rows.append({'row_label':m.group(1),'cells':cells})
    assert len(rows)==num
    table(tid,title,'si',page,columns,rows,['Printed coordinates ×10^4; divide by10^4 for fractional coordinates.' if page!=4 else 'Literal printed U11,U22,U33,U23,U13,U12 order retained.','Printed displacement Å²×10^3; divide by10^3 for Å².','Ueq is one-third trace of orthogonalized Uij.' if page==3 else 'N–H atoms located/refined; other H riding as main describes.' if page==5 else 'Exponent −2π²[h²a*²U11+…+2hka*b*U12].','Coordinates are for Cd(PTC)2·THF precursor, not product QBs.'])
hb=[('N(1)–H(1)…S(3)#3',['0.847(14)','2.603(14)','3.4396(9)','170.0(16)']),('N(2)–H(2)…O(1S)#4',['0.841(13)','1.984(13)','2.8195(12)','172.1(16)']),('C(3)–H(3)…S(3)#3',['0.95','3.02','3.8342(11)','144.0']),('C(7)–H(7)…S(2)',['0.95','2.54','3.1760(11)','124.6']),('C(1S)–H(1SA)…S(2)#1',['0.99','2.87','3.6577(12)','137.0'])]
table('table-s4','Hydrogen bonds','si',6,['d(D–H)','d(H…A)','d(D…A)','angle(DHA)'],[{'row_label':label,'cells':[{'column':c,**q(v,'deg'if i==3 else'angstrom',label+' '+c,'si',6,'Table S4 '+label)}for i,(c,v)in enumerate(zip(['d(D–H)','d(H…A)','d(D…A)','angle(DHA)'],vals))]}for label,vals in hb],['#1 −x+1,−y+1,−z+1','#2 −x+1,−y,−z+1','#3 x,y+1,z','#4 x,y−1,z'])
t1spec=[('empirical formula','C18H20CdN2OS4',None),('formula weight','521.00','g/mol'),('temperature','100(2)','K'),('wavelength','0.71073','angstrom'),('crystal system','monoclinic',None),('space group','P21/n',None),('a','15.5501(6)','angstrom'),('b','7.3761(3)','angstrom'),('c','17.2620(7)','angstrom'),('alpha','90','deg'),('beta','90.915(2)','deg'),('gamma','90','deg'),('volume','1979.68(14)','angstrom^3'),('Z','4','count'),('density calculated','1.748','g/cm^3'),('absorption coefficient','1.535','mm^-1'),('F(000)','1048','count'),('crystal size1','0.598','mm'),('crystal size2','0.121','mm'),('crystal size3','0.075','mm'),('theta lower','1.749','deg'),('theta upper','45.000','deg'),('h lower','−28','index'),('h upper','30','index'),('k lower','−9','index'),('k upper','14','index'),('l lower','−34','index'),('l upper','34','index'),('collected reflections','66935','count'),('independent reflections','16292','count'),('R(int)','0.0464','dimensionless'),('completeness','99.7','%'),('completeness theta','25.242','deg'),('absorption correction','semiempirical from equivalents',None),('max transmission','0.4481','dimensionless'),('min transmission','0.3434','dimensionless'),('refinement method','full-matrix least-squares on F^2',None),('data','16292','count'),('restraints','1','count'),('parameters','243','count'),('goodness of fit on F2','1.002','dimensionless'),('R1 I>2sigma(I)','0.0309','dimensionless'),('wR2 I>2sigma(I)','0.0554','dimensionless'),('R1 all data','0.0583','dimensionless'),('wR2 all data','0.0632','dimensionless'),('largest difference peak','0.914','e/angstrom^3'),('largest difference hole','−1.026','e/angstrom^3')]
table('table-1','Crystal data and structure refinement','main',3,['field','value'],[{'row_label':name,'cells':[q(raw,unit,name,'main',3,'Table 1 '+name)]}for name,raw,unit in t1spec],['Formula includes one THF per Cd, unlike powder elemental-analysis formula.','Crystal dimensions are more precise than approximate acquisition prose.'])
dist=[('Cd1–S1','2.7992(3)'),('Cd1–S4′','2.7691(3)'),('Cd1–S1′','2.6719(3)'),('Cd1–S2','2.6149(3)'),('Cd1–S3','2.6917(3)'),('Cd1–S4','2.6687(3)')]
angles=[('S1–Cd–S1′','85.461(8)'),('S1–Cd–S2','66.752(8)'),('S1–Cd–S3','89.032(8)'),('S1–Cd–S4','110.441(8)'),('S3–Cd1–S4','160.512(8)'),('S1–Cd–S4′','67.689(8)')]
table('table-2','Selected bond distances and angles','main',4,['geometry','value'],[{'row_label':name,'cells':[q(raw,'angstrom'if i<6 else'deg',name,'main',4,'Table 2 '+name,conflicts=['C10'])]}for i,(name,raw)in enumerate(dist+angles)],['All printed atom primes retained; no guessed correction to prose label.'])
ea=[('C',['2.83','2.41','2.47']),('H',['0.61','<0.5','0.50']),('N',['<0.5','<0.5','<0.5']),('S',['21.32','-','20.01'])]
table('table-s5','Elemental analysis after excess precursor','si',11,['trial1','trial2','trial3'],[{'row_label':el,'cells':[{'column':'trial'+str(i),**q(v,'wt%',el+' trial'+str(i),'si',11,'Table S5 '+el+' trial'+str(i))}for i,v in enumerate(vals,1)]}for el,vals in ea],['Three analytical trial columns are not proved to be separate syntheses.','Dash is null/unreported; <0.5 remains an upper bound, not zero.'],'excess-shell-family')
edcols=['net_counts','net_counts_error','intensity_Cps_per_nA','K_factor','weight_percent','weight_percent_error','atom_percent','atom_percent_error']
edrows=[('S K',['14119','190','---','1.030','23.99','0.32','52.53','0.71']),('S L',['0','371','---','---','---','---','---','---']),('Cd L',['26583','440','---','1.732','76.01','1.26','47.47','0.79']),('Cd M',['0','61','---','---','---','---','---','---']),('Total',['---','---','---','---','100.00','---','100.00','---'])]
table('figure-s7-eds-table','EDS embedded quantification table','si',13,edcols,[{'row_label':el,'cells':[{'column':c,**q(v,'count'if i<2 else'Cps/nA'if i==2 else'dimensionless'if i==3 else'%' ,el+' '+c,'si',13,'Figure S7 embedded table '+el+' '+c,conflicts=['C7','C9'])}for i,(c,v)in enumerate(zip(edcols,vals))]}for el,vals in edrows],['± is the printed error convention; error columns retained separately.','S L label placed on next line in artwork; row association is source-layout reading, flaggedC9.','Total only weight and atom percent printed; no total counts invented.'],'powder-thf')
for t in tables:
    for ir,row in enumerate(t['rows']):
        for ic,c in enumerate(row['cells']):c['id']=f"{t['id']}-r{ir+1:03}-c{ic+1:02}"
write('source-tables.json',{'schema':'mattersyn-source-tables/1','source_id':SOURCE_ID,'author':'/root/backlog_eta','created_at':NOW,'tables':tables,'independent_audit_status':'pending','structure_model_qualification':False})

# Crop coordinates are normalized against the actual page canvas. No content is painted or redrawn.
CROPS=[
 ('graphical-abstract','main',1,(.59,.33,.907,.495)),('figure-1','main',2,(.087,.074,.497,.421)),('scheme-1','main',2,(.087,.42,.497,.634)),
 ('table-1','main',3,(.087,.178,.497,.609)),('figure-2','main',4,(.087,.075,.497,.522)),('table-2','main',4,(.087,.526,.497,.669)),('figure-3','main',4,(.510,.078,.916,.777)),
 ('figure-4','main',5,(.510,.078,.916,.708)),('figure-5','main',6,(.087,.075,.497,.335)),('figure-6','main',6,(.087,.4,.497,.653)),('figure-7','main',6,(.510,.341,.916,.612)),('equations-1-3','main',6,(.075,.738,.497,.889)),
 ('figure-8','main',7,(.087,.077,.497,.350)),('figure-9','main',7,(.087,.505,.916,.942)),('scheme-2','main',8,(.087,.077,.916,.298)),
 ('figure-s1','si',2,(.108,.19,.886,.667)),('table-s1','si',3,(.105,.12,.89,.84)),('table-s2','si',4,(.105,.12,.89,.872)),('table-s3','si',5,(.105,.12,.89,.722)),('table-s4','si',6,(.105,.12,.89,.42)),
 ('figure-s2','si',7,(.107,.076,.89,.915)),('figure-s3','si',8,(.107,.076,.89,.915)),('figure-s4','si',9,(.107,.111,.89,.853)),('figure-s5','si',10,(.107,.088,.89,.576)),('table-s5-and-calculation','si',11,(.107,.082,.889,.584)),
 ('figure-s6','si',12,(.105,.077,.89,.622)),('figure-s7','si',13,(.102,.083,.9,.693)),('figure-s8','si',14,(.105,.142,.89,.778)),('figure-s9-ab','si',15,(.216,.086,.749,.824)),('figure-s9-c','si',16,(.108,.086,.89,.603))]
assets=[]
for role in ['main','si']:
    pdf=pypdfium2.PdfDocument(docs[role]['source_path'])
    for aid,r,page,bbox in [c for c in CROPS if c[1]==role]:
        native=pdf[page-1];bitmap=native.render(scale=3);img=bitmap.to_pil();w,h=img.size;box=tuple(round(v*(w if i%2==0 else h))for i,v in enumerate(bbox));crop=img.crop(box)
        out=P/'reader-assets'/(aid+'.png');out.parent.mkdir(exist_ok=True);crop.save(out)
        assets.append({'id':aid,'path':str(out),'sha256':sha(out),'source_sha256':docs[role]['source_sha256'],'evidence':evidence(role,page,aid),'crop_normalized':bbox,'source_render_scale':3,'pixel_dimensions':crop.size,'original_selected_excerpt':True,'complete_page':False,'raw_data_recovered':False,'author_crop_validation':'dimensions/bounds and source-page content checked; separate rendered-crop inspection recorded in author-validation','independent_audit_status':'pending'})
        crop.close();img.close();bitmap.close();native.close()
    pdf.close()
write('original-assets-manifest.json',{'schema':'mattersyn-original-selected-assets/1','source_id':SOURCE_ID,'author':'/root/backlog_eta','assets':assets,'source_files_unchanged':True,'independent_audit_status':'pending'})

figures=[{'id':fid,'title':title,'label':locator,'sample_scope':scope,'scientific_scope':note,'evidence':evidence(role,page,locator),'asset_id':fid,'disposition':'source original and reported observations retained; no graph digitization','independent_audit_status':'pending'}for role,page,locator,fid,title,scope,note in A.FIGURES]
schemes=[{'id':sid,'title':title,'sample_scope':scope,'scope_note':note,'evidence':evidence('main',page,sid),'asset_id':sid,'claim_class':'author_or_cited_model'}for sid,page,title,scope,note in A.SCHEMES]
equations=[{'id':'equation-'+str(n),'kind':'author_proposed_reaction','description':desc,'evidence':evidence('main',6,'Equation '+str(n)),'asset_id':'equations-1-3','measured_reaction_intermediate_structure':False}for n,desc in enumerate(['Base deprotonates Cd(PTC)2; CdS,PhNCS,PTC− and BH+ produced.','PTC−+BH+ gives aniline+CS2+base.','Aniline+PhNCS gives1,3-diphenylthiourea.'],1)]
equations.extend([{'id':'refinement-objective','kind':'refinement_definition','description':'Minimize sum w(Fo²−Fc²)².','evidence':evidence('main',3,'Structure refinement')},{'id':'adp-exponent','kind':'crystallographic_definition','description':'−2π²[h²a*²U11+…+2hka*b*U12]','evidence':evidence('si',4,'Table S2 heading')},{'id':'ueq-definition','kind':'crystallographic_definition','description':'One third trace of orthogonalized Uij tensor.','evidence':evidence('si',3,'Table S1 heading')},{'id':'hypothetical-sulfur-mass-balance','kind':'author_calculation','description':factsby['si-sulfur-model']['claim'],'source_fact_id':SOURCE_ID+'-si-sulfur-model','evidence':evidence('si',11,'Calculation below Table S5')}])

# Citations are preserved as citations, not assertions that their full articles were read.
reftext=docs['main']['pages'][8]['text'].split('■ REFERENCES',1)[1].split('Inorganic Chemistry Article',1)[0]+'\n'+docs['main']['pages'][9]['text'].split('■ NOTE ADDED',1)[0]
refs=[]
for m in re.finditer(r'\((\d+)\)\s+(.*?)(?=\n\(\d+\)\s|\Z)',reftext,re.S):
    n=int(m.group(1));refs.append({'id':'main-reference-'+str(n),'number':n,'citation':' '.join(m.group(2).split()),'source_role':'main','evidence':evidence('main',9 if n<30 else 10,'Reference '+str(n)),'external_full_text_inspected':False})
assert len(refs)==50 and [r['number']for r in refs]==list(range(1,51))
sitext=docs['si']['pages'][16]['text'].split('References',1)[1]
for m in re.finditer(r'(?:^|\n)\s*([12])\.\s+(.*?)(?=\n\s*[12]\.\s|\Z)',sitext,re.S):
    n=int(m.group(1));refs.append({'id':'si-reference-'+str(n),'number':n,'citation':' '.join(m.group(2).split()),'source_role':'si','evidence':evidence('si',17,'Reference '+str(n)),'external_full_text_inspected':False})
assert len(refs)==52

scope_ids=sorted({f['sample_scope']for f in facts}|{f['sample_scope']for f in figures}|{t['sample_scope']for t in tables})
samples=[{'id':s,'meaning':'source-defined preparation, measurement, model or reference context; not an independent experiment count','source_fact_ids':[f['id']for f in facts if f['sample_scope']==s],'figure_ids':[f['id']for f in figures if f['sample_scope']==s],'table_ids':[t['id']for t in tables if t['sample_scope']==s],'physical_batch_id':None,'cross_technique_join':'Only explicit figure/prose joins retained; physical batch identity not inferred.'}for s in scope_ids]
measurements=[{'id':f['id']+'-q'+str(i),'sample_scope':f['sample_scope'],'quantity':qv,'source_fact_id':f['id'],'claim_class':f['claim_class']}for f in facts for i,qv in enumerate(f['quantities'],1)]
conflicts=[{'id':cid,'title':title,'description':description,'status':'unresolved_source_discrepancy_or_layout_qualification','evidence':[ev(*e)for e in es],'affected_fact_ids':[f['id']for f in facts if cid in f['conflict_ids']]}for cid,title,description,es in A.CONFLICTS]
gaps=[{'id':gid,'description':text,'status':'explicitly_unresolved'}for gid,text in A.GAPS]
documents=[]
for role,d in docs.items():
    pages=[]
    for page,note in zip(d['pages'],A.PAGE_NOTES[role]):
        pages.append({'pdf_page':page['pdf_page'],'printed_page':page['printed_page'],'text_read':True,'visual_inspection':True,'reviewer':'/root/backlog_eta','text_cache':page['text_path'],'text_sha256':page['text_sha256'],'render_cache':page['render_path'],'render_sha256':page['render_sha256'],'covered_content':note,'remaining_page_coverage_gap':None})
    documents.append({'role':role,'original_path':d['source_path'],'source_sha256':d['source_sha256'],'page_count':d['page_count'],'pages':pages})
coverage={'schema':'mattersyn-page-coverage/1','source_id':SOURCE_ID,'doi':DOI,'reviewer':'/root/backlog_eta','reviewed_at':NOW,'scope':'All10 main and17 matched SI pages actually text-read and visually inspected. All tabulated numeric rows transcribed and author-compared; a distinct scientific/numerical audit remains pending.','documents':documents,'totals':{'main_pages':10,'si_pages':17,'text_read':27,'visually_inspected':27},'figure_inventory_complete':True,'scientific_audit_complete':False,'raw_plot_digitization_performed':False,'external_reference_full_texts_reviewed':False}
write('page-coverage.json',coverage)
units=[]
for kind,rows in [('fact',facts),('figure_or_graphical_abstract',figures),('table',tables),('scheme',schemes),('displayed_equation_or_definition',equations),('reference',refs)]:
    for row in rows:units.append({'id':row['id'],'kind':kind,'title':row.get('title',row.get('citation',row.get('description',''))),'evidence':row['evidence'],'extraction_pointer':('/facts/'if kind=='fact'else'/figures/'if kind=='figure_or_graphical_abstract'else'/tables/'if kind=='table'else'/schemes/'if kind=='scheme'else'/equations/'if kind=='displayed_equation_or_definition'else'/references/')+str(rows.index(row)),'disposition':'extracted; source scientific scope and uncertainty retained'})
for pid,title,kind,_ in protocol_specs:units.append({'id':pid,'kind':'protocol','title':title,'evidence':[e for op in next(p for p in protocols if p['id']==pid)['operations']for e in op['evidence']],'extraction_pointer':'/protocols/'+str([p['id']for p in protocols].index(pid)),'disposition':'structured operations with unreported fields and source conflicts'})
admin=[{'id':'main-frontmatter','kind':'bibliographic_and_administrative','title':'Title/authors/affiliations/DOI/received/published','evidence':evidence('main',1,'Frontmatter')},{'id':'author-info','kind':'bibliographic_and_administrative','title':'Correspondence/ORCID/conflict declaration','evidence':evidence('main',9,'Author Information')},{'id':'funding','kind':'bibliographic_and_administrative','title':'NSF CHE-1607862,DMR-1611149,MRI CHE-0420497 and acknowledgment to Yang Zhou','evidence':evidence('main',9,'Acknowledgments')},{'id':'artwork-correction','kind':'version_note','title':'October6/October9 artwork replacement note','evidence':evidence('main',10,'Note Added After ASAP Publication')},{'id':'si-cover-contents','kind':'bibliographic_and_administrative','title':'SI title/authors and complete contents','evidence':evidence('si',1,'SI cover')}]
units.extend(admin)
counts={'facts':len(facts),'materials':len(materials),'stocks':len(stocks),'protocols':len(protocols),'operations':sum(len(p['operations'])for p in protocols),'sample_or_context_ids':len(samples),'scalar_or_range_quantities_in_facts':len(measurements),'tables_including_eds_table':len(tables),'table_rows':sum(len(t['rows'])for t in tables),'table_cells':sum(len(r['cells'])for t in tables for r in t['rows']),'table_numeric_or_bound_cells':sum(c['value']is not None for t in tables for r in t['rows']for c in r['cells']),'table_null_or_text_cells':sum(c['value']is None for t in tables for r in t['rows']for c in r['cells']),'main_numbered_figures':9,'si_numbered_figures':9,'graphical_abstracts':1,'figure_parts_in_inventory':len(figures),'schemes':2,'numbered_reaction_equations':3,'displayed_equations_definitions_calculations':len(equations),'references':52,'selected_original_crops':len(assets),'source_units':len(units),'source_conflicts_or_qualifications':len(conflicts),'gaps':len(gaps)}
inventory={'schema':'mattersyn-source-inventory/1','source_id':SOURCE_ID,'created_at':NOW,'reviewer':'/root/backlog_eta','documents':documents,'original_file_copies':payload['source_copies'],'pairing':pairing,'source_units':units,'figures':figures,'tables':[{'id':t['id'],'title':t['title'],'evidence':t['evidence'],'row_count':len(t['rows']),'cell_count':sum(len(r['cells'])for r in t['rows']),'typed_table_path':'source-tables.json','typed_table_pointer':'/tables/'+str(i)}for i,t in enumerate(tables)],'schemes':schemes,'displayed_or_numbered_equations':equations,'absence_scope':{'Raman':'No present-source Raman measurement; cited reference43 only.','SAED':'Not present in supplied main/SI.','product_atomic_coordinates':'Not supplied. Precursor Cd(PTC)2·THF coordinates do not provide CdSe/CdS belt structure.','external_files':'CCDC/electronic structure factors cited, not part of supplied local intake.'},'references':refs,'administrative_and_footnote_units':admin,'assets':assets,'counts':counts,'independent_scientific_audit_status':'pending','source_originals_modified':False,'live_ledger_modified':False,'site_modified':False}
write('source-inventory.json',inventory)
inventory.update({'materials':materials,'stock_solution_contexts':stocks,'protocols':protocols,'sample_or_measurement_contexts':samples,'contradictions':conflicts,'gaps':gaps})
write('source-inventory.json',inventory)
extraction={'schema':'mattersyn-full-source-extraction/1','revision':1,'source_id':SOURCE_ID,'group_id':GROUP,'source_generation':2,'bundle_sha256':payload['bundle_sha256'],'doi':DOI,'title':A.TITLE,'authors':A.AUTHORS,'bibliography':{'journal':'Inorganic Chemistry','year':2017,'volume':56,'pages':'12920–12929','received':'2017-07-05','published':'2017-10-06','corrected_artwork_repost':'2017-10-09'},'extracted_by':'/root/backlog_eta','extracted_at':NOW,'source_sha256':docs['main']['source_sha256'],'si_sha256':docs['si']['source_sha256'],'scope':'Complete supplied main+matched SI author extraction. Original graphs retained; no digitized curves, unreported upstream recipes, external CIF, inferred sample joins or independent-audit approval.','original_file_copies':payload['source_copies'],'facts':facts,'materials':materials,'stocks':stocks,'protocols':protocols,'samples':samples,'measurements':measurements,'tables':tables,'figures':figures,'schemes':schemes,'equations':equations,'references':refs,'contradictions':conflicts,'gaps':gaps,'structure_status':{'precursor':'Tables1/2/S1–S4 provide measured precursor crystal metadata,26non-H/20H coordinates and ADPs. Transcribed, not model-qualified.','product':'TEM/XRD/optical evidence for CdSe/CdS belts; no supplied atomic coordinates.','CCDC':'1560097 cited; originalCIF not supplied/read.','exact_structure_recipe_admission':False},'completion':{'main_pages_read_and_viewed':10,'si_pages_read_and_viewed':17,'author_extraction_complete':True,'independent_scientific_audit':False,'canonical_complete':False,'published':False},'training_status':{'requested_tasks':[],'eligibility_not_evaluated':True,'exact_pairs':0,'reason':'Extraction author does not admit tasks; source conflicts, missing upstream details and sample joins remain explicit.'},'counts':counts}
write('source-facts.json',extraction)
checks=[]
def ck(label,ok):checks.append({'check':label,'passed':bool(ok)})
ck('Four source copies remain hash-exact',all(sha(f['source_path'])==f['sha256']for f in payload['source_copies']))
ck('All27text/render cache hashes still exact',all(sha(pg['text_path'])==pg['text_sha256']and sha(pg['render_path'])==pg['render_sha256']for d in docs.values()for pg in d['pages']))
ck('All27pages actually read/viewed recorded',sum(len(d['pages'])for d in documents)==27 and all(p['text_read']and p['visual_inspection']for d in documents for p in d['pages']))
ck('Distinct references exact sequential inventories',len(refs)==52 and len({r['id']for r in refs})==52)
ck('S1/S2/S3 complete row counts26/26/20',[len(t['rows'])for t in tables[:3]]==[26,26,20])
ck('360printed crystal/Hbond numeric positions',sum(len(r['cells'])for t in tables[:4]for r in t['rows'])==360)
ck('Four upper bounds and sulfur missing kept',sum(c['comparison']=='<'for r in tables[6]['rows']for c in r['cells'])==4 and tables[6]['rows'][3]['cells'][1]['value']is None)
ck('No crystal fractional wrapping or source uncertainty loss',tables[0]['rows'][10]['cells'][1]['value']==1.0645 and tables[0]['rows'][6]['cells'][1]['value']==-.0756 and tables[0]['rows'][0]['cells'][0]['uncertainty']==.0001)
ck('No current training or audit completion asserted',not extraction['completion']['independent_scientific_audit'] and extraction['training_status']['requested_tasks']==[])
for f in facts:
    ck(f['id']+' evidence present',bool(f['evidence']))
    for e in f['evidence']:ck(f['id']+' valid page/source',1<=e['pdf_page']<=docs[e['document_role']]['page_count']and e['source_sha256']==docs[e['document_role']]['source_sha256'])
for t in tables:
    for row in t['rows']:
        for c in row['cells']:ck(c['id']+' typed raw/evidence/finite',bool(c['raw_text'])and bool(c['evidence'])and(c['value']is None or math.isfinite(c['value'])))
for asset in assets:ck(asset['id']+' asset hash and cropped bounds',sha(asset['path'])==asset['sha256']and all(0<=v<=1 for v in asset['crop_normalized'])and asset['pixel_dimensions'][0]>100 and asset['pixel_dimensions'][1]>100)
validation={'schema':'mattersyn-author-extraction-validation/1','source_id':SOURCE_ID,'at':NOW,'author':'/root/backlog_eta','status':'author_checks_passed_pending_distinct_scientific_audit'if all(c['passed']for c in checks)else'findings','counts':counts,'checks':checks,'failures':[c for c in checks if not c['passed']],'actual_manual_scope':'All27pages individually viewed with native rendered figures/tables; all main/SI text, table entries, captions, equations and references read. This is author review, not an independent audit.','rendered_crop_inspection':'pending final contact/direct inspection','scientific_models_created':0}
write('author-validation.json',validation)
notes=f'''# Morrison et al. 2017 — private full-source extraction

Source title: {A.TITLE}. DOI {DOI}. All 10 main pages and 17 matched SI pages were text-read and visually inspected by the extraction author. Four incoming/legacy copies remain exact, representing two documents, not extra experiments. A distinct scientific audit remains pending.

The paper is synthesis-relevant: aqueous Cd(PTC)2 preparation, THF-solvated crystal growth, standalone CdS decomposition controls, excess-precursor shell growth and controlled monolayer CdS-shell growth are represented as separate procedures/branches. The 0.512 g starting-belt charge is a dispersion mass. Optical workup aliquots and TEM/XRD/elemental contexts do not become separate synthetic runs or invented exact specimen joins.

The structured extraction contains {len(facts)} source facts, {len(materials)} material identities, {len(stocks)} stock/solution contexts, {len(protocols)} protocol families and {counts['operations']} operations; {len(measurements)} quantitative fields in facts and {counts['table_cells']} tabulated cells. All 9 main figures, 9 SI figures (S9 spans two pages), the graphical abstract, 2 schemes, 3 reaction equations, full crystallographic tables, 50 main references and 2 SI references are inventoried. Thirty selected original crops are separate from the 27 local-only full-page renders.

The crystal data belong to Cd(PTC)2·THF precursor. They do not supply CdSe/CdS product coordinates. CCDC 1560097 and electronic structure factors are cited but not supplied locally. No model, CIF, external reference, raw-curve digitization or task-training eligibility was generated. Main precursor powder composition and THF-solvated crystal composition are distinct.

Source discrepancies are retained: mass/amount pairs, ambiguous “20 mmol solution,” IR assignments, added-base identity, thiourea onset, powder EDS solvent context, percentage lattice arithmetic, EDS row-layout qualification and Cd–S prime labels. No reported value was silently corrected. Qualitative SILAR/c-ALD failures remain author observations without fabricated failed-run recipes.

`complete-source-payloads.json`, `private/text/` and `source-render/` are local-only source material under the public exclusion policy. `source-facts.json`, `source-inventory.json`, `source-tables.json`, `page-coverage.json` and the selected-crop manifest provide the audit-facing structured outputs. Final freeze follows rendered-crop checks; this file does not claim independent passage or publication.
'''
(P/'extraction-notes.md').write_text(notes,encoding='utf-8')
print(json.dumps({'status':validation['status'],'counts':counts,'failures':validation['failures']},ensure_ascii=False))
