"""Author-curated source extraction. Does not mutate source PDFs, CIF or earlier checkpoints."""
from pathlib import Path
import json,hashlib,datetime,re,math
B=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text('utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,obj):(B/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
prep=read(B/'source-preparation.json');pair=read(B/'pairing-review.json');initial=read(B/'checkpoints/pairing-inventory-v1/source-inventory.json')
assets=read(B/'selected-original-assets.json');cif=read(B/'cif-source-inventory.json')
now=datetime.datetime.now(datetime.timezone.utc).isoformat();units=[];facts=[];procedures=[];materials=[];samples=[];tables=[];equations=[];references=[]
docs=pair['source_documents'];unit_by_id={}
def unit(ident,role,page,locator,kind,claim,scope='study',payload=None,asset_ids=None,status='reported',conflicts=None):
 ident='evans2010-'+ident
 u={'id':ident,'source_unit_id':ident,'source_role':role,'pdf_page':page,'printed_page':str(10972+page) if role=='main' else (f'S{page}' if role=='si' else None),'locator':locator,'kind':kind,'claim':claim,'sample_scope':scope,'status':status,'source_sha256':docs[role]['sha256'],'original_asset_ids':asset_ids or [],'payload':payload,'conflict_ids':conflicts or [],'independent_review_status':'pending'}
 assert ident not in unit_by_id;units.append(u);unit_by_id[ident]=u;return ident
def fact(uid,prop,value,unit_symbol=None,raw=None,status=None,qualifier='',approx=False,lo=None,hi=None,lo_exclusive=False,hi_exclusive=False,scope=None):
 u=unit_by_id[uid];n=sum(f['source_unit_id']==uid and f['property']==prop for f in facts)
 f={'id':uid+'-'+re.sub('[^a-z0-9]+','-',prop.lower()).strip('-')+(f'-{n+1}' if n else ''),'source_unit_id':uid,'sample_scope':scope or u['sample_scope'],'property':prop,'value':value,'minimum':lo,'maximum':hi,'minimum_exclusive':lo_exclusive,'maximum_exclusive':hi_exclusive,'unit':unit_symbol,'raw_text':raw if raw is not None else (str(value)+((' '+unit_symbol) if unit_symbol else '') if value is not None else None),'status':status or u['status'],'approximate':approx,'qualifier':qualifier,'conflict_ids':list(u['conflict_ids']),'evidence':[{'source_role':u['source_role'],'pdf_page':u['pdf_page'],'locator':u['locator'],'source_sha256':u['source_sha256']}],'eligible_training':False,'independent_review_status':'pending'}
 facts.append(f);return f['id']
def quantities(uid,rows):
 for row in rows:
  # property,value,unit,optional exact transcription,optional qualifier
  fact(uid,row[0],row[1],row[2],row[3] if len(row)>3 else None,qualifier=row[4] if len(row)>4 else '')
def procedure(ident,page,title,scope,steps,charges,missing,conflicts=None,parents=None,kind='precursor_preparation'):
 uid=unit(ident,'si',page,title,'procedure',title,scope,{'steps':steps,'missing':missing,'explicit_inheritance':parents or []},conflicts=conflicts)
 quantities(uid,charges)
 procedures.append({'id':ident,'source_unit_id':uid,'label':title,'category':kind,'sample_scope':scope,'steps':steps,'quantity_fact_ids':[f['id'] for f in facts if f['source_unit_id']==uid],'explicit_inheritance':parents or [],'missing':missing,'conflict_ids':conflicts or [],'complete_executable_recipe_asserted':False})
 return uid

uid=unit('identity','main',1,'Title, byline, received date and DOI/footer','identity',pair['title'],payload={'authors':pair['authors'],'journal':'Journal of the American Chemical Society','year':2010,'volume':132,'issue':32,'pages':'10973–10975','doi':'10.1021/ja103805s','received':'2010-05-11','published_on_web':'2010-07-26','affiliation':'Department of Chemistry and Institute of Optics, University of Rochester, Rochester NY14627','download_watermark':'Access/download stamp is not publication, experiment or arrival date.'})
unit('main-si-cif-pairing','main',3,'Supporting Information Available; SI S1, S15–17 and retained CIF','source_scope','Matched3-page main,21-page SI and molecular-crystal CIF; exact content-based evidence in pairing-review.json.',payload=pair['pairing_evidence'])
unit('acknowledgments','main',3,'Acknowledgment','metadata','Funding from Camille and Henry Dreyfus Foundation, Rochester Human Immunology Center supported by NIH, NSF; discussions with William Jones, Robert Boeckman, Mary Lenczewski, Pu Luo; crystallography assistance William Brennessel, University of Rochester.')
uid=unit('background','main',1,'Introduction paragraphs1–3, references1–6','cited_background','Literature QDs have high optical quality but high temperature/low conversion; none of these general literature numbers is a measured current sample.',status='cited_background')
fact(uid,'photoluminescence quantum yield',None,'%',raw='QY >50%',lo=50,lo_exclusive=True)
fact(uid,'size distribution statement',5,'%',raw='±5%',qualifier='Cited literature spread; statistical definition not supplied.')
fact(uid,'CdSe growth temperature',300,'degC',raw='~300 °C',approx=True)
fact(uid,'conversion yield',None,'%',raw='<2%',hi=2,hi_exclusive=True)
unit('abstract-mechanistic-scope','main',1,'Abstract','author_interpretation','Authors propose that secondary-phosphine impurities drive nucleation while pure tertiary phosphine selenides do not react with metal carboxylates in the tested conditions. Universality across phosphine-based II–VI/IV–VI QDs is their interpretation, not an exhaustive demonstrated family-wide law.',status='author_interpretation')
uid=unit('commercial-versus-pure','main',1,'Last left-column paragraph continuing in right column','observation','Unlike high-purity TEPSe/TIPPSe/TPPSe controls showing no reaction after5h120°C, commercially obtained TOPSe reacts with Pb oleate within minutes forming a dark product. Adding DIPP to high-purity tertiary phosphine chalcogenides accelerates the reaction. No additional complete commercial-TOPSe recipe or numeric minute value is specified.',scope='qualitative control comparison')
fact(uid,'commercial TOPSe reaction time','within minutes',qualifier='Qualitative reported comparison; do not infer a specific duration.')

reagents=[('cdo','CdO','CdO',99.99,'Sigma-Aldrich',None),('oa','Oleic acid','C18H34O2',90,'Sigma-Aldrich','technical grade'),('ode','1-Octadecene','C18H36',90,'Sigma-Aldrich','technical grade'),('pbo','PbO','PbO',99.9,'Sigma-Aldrich','99.9+% as printed'),('se','Selenium shot','Se',99.999,'Sigma-Aldrich',None),('dpp','Diphenylphosphine','Ph2PH',98,'Sigma-Aldrich',None),('tep','Triethylphosphine','P(C2H5)3',99,'Sigma-Aldrich',None),('top-tech','Trioctylphosphine','P(C8H17)3',90,'Sigma-Aldrich','technical grade'),('toluene','Anhydrous toluene','C7H8',99.8,'Sigma-Aldrich','anhydrous'),('top-strem','Trioctylphosphine','P(C8H17)3',97,'Strem',None),('tipp','Tri-isopropylphosphine','P(C3H7)3',98,'Strem',None),('dipp','Di-isopropylphosphine','HP(C3H7)2',98,'Strem',None),('toluene-d8','Toluene-d8','C7D8',None,'Cambridge Isotope Labs',None)]
for rid,name,formula,purity,supplier,grade in reagents:
 uid=unit('reagent-'+rid,'si',1,'Materials and Methods: supplier list','material',name,'reagent inventory',{'name':name,'formula_or_condensed_identity':formula,'supplier':supplier,'grade':grade,'as_received_unless_noted':True,'formula_basis':'Chemical identity normalization; source uses names and selected condensed formulas.'})
 materials.append({'id':rid,'name':name,'source_unit_id':uid,'formula_or_condensed_identity':formula,'molecular_coordinates':None})
 if purity is not None:fact(uid,'commercial purity',None if rid=='pbo' else purity,'%',raw=grade if rid=='pbo' else str(purity)+'%',lo=99.9 if rid=='pbo' else None,qualifier='Lower-bound-plus notation retained; not exactly99.9.' if rid=='pbo' else 'Commercial label, not this study’s analytical purity.')
 else:fact(uid,'purity',None,status='not_reported')
for rid,name,formula in [('acetone','Acetone','C3H6O'),('tpp','Triphenylphosphine','P(C6H5)3'),('n2','Nitrogen','N2'),('tms','Tetramethylsilane NMR standard','Si(CH3)4'),('h3po4','Phosphoric-acid NMR standard','H3PO4')]:
 page=2 if rid=='tpp' else 1
 uid=unit('reagent-'+rid,'si',page,'Methods and starting-material preparation','material',name,'reagent/context inventory',{'formula_or_condensed_identity':formula,'supplier':None,'purity':None,'note':'No supplier/grade inferred from an unrelated listed reagent.'})
 materials.append({'id':rid,'name':name,'source_unit_id':uid,'formula_or_condensed_identity':formula,'molecular_coordinates':None})
uid=unit('nmr-general','si',1,'Materials and Methods: NMR solvents and spectrometer','acquisition','All NMR solvents dry and degassed with three freeze-pump-thaw cycles. Bruker Avance500; shifts relative to TMS internal and H3PO4 external. Some captions describe H3PO4 physically inside a sealed capillary in the tube; preserve both descriptions.',payload={'instrument':'Bruker Avance 500','solvent_preparation_scope':'NMR experiments only','standards':{'1H and13C':'TMS internal','31P':'H3PO4 external; selected captions sealed capillary'}})
quantities(uid,[('freeze-pump-thaw cycles',3,'cycle'),('1H frequency',500,'MHz'),('31P frequency',202,'MHz'),('13C frequency',125.65,'MHz'),('TMS reference shift',0,'ppm'),('H3PO4 reference shift',0,'ppm')])

u=procedure('cd-oleate',1,'Cadmium(II) oleate preparation','Cd(C18H33O2)2 precursor',[
 'Combine CdO, oleic acid and1-octadecene in a50mL three-neck flask; heat to220°C under flowing N2.',
 'After the red CdO solid dissolves, hold for an additional1h; cool to room temperature.',
 'Add acetone to precipitate white waxy Cd oleate; isolate precipitated solid by centrifugation. Retain solid, not discarded supernatant.'
],[('CdO mass',.642,'g'),('CdO amount',5,'mmol'),('oleic acid volume',3.96,'mL'),('oleic acid amount',12.5,'mmol'),('oleic acid purity',90,'%'),('octadecene volume',10,'mL'),('octadecene purity',90,'%'),('flask capacity',50,'mL'),('temperature',220,'degC'),('hold after dissolution',1,'h')],['heating rate','time to dissolution','N2 flow rate','acetone quantity','centrifuge force/time','number of washes','isolated yield'])
u=procedure('pb-oleate',1,'Lead(II) oleate preparation','Pb(C18H33O2)2 precursor',[
 'Combine PbO, oleic acid and1-octadecene; source explicitly says remaining procedure identical to Cd oleate preparation.',
 'Inherited conditions:50mL three-neck flask, flowing N2,220°C, additional1h after dissolution, room-temperature cooling, acetone precipitation and centrifugation retaining solid.',
 'FTIR is reported to confirm identity/purity of both metal oleates; no FTIR spectrum or bands are supplied.'
],[('PbO mass',1.12,'g'),('PbO amount',5,'mmol'),('oleic acid volume',3.96,'mL'),('oleic acid amount',12.5,'mmol'),('octadecene volume',10,'mL'),('inherited temperature',220,'degC'),('inherited additional hold',1,'h'),('inherited flask capacity',50,'mL')],['centrifugation details','acetone volume','FTIR acquisition/bands','isolated yield'],parents=['evans2010-cd-oleate'])
u=procedure('topse',1,'Trioctylphosphine selenide preparation','TOPSe stock',[
 'Combine TOP and elemental selenium; stir overnight in a nitrogen-filled glovebox.',
 'Use viscous resulting solution without further purification unless otherwise stated; numerous NMR impurities appear in FigureS3.'
],[('TOP volume',30,'mL'),('TOP amount',67,'mmol'),('Se mass',5.29,'g'),('Se amount',67,'mmol'),('31P shift',36.8,'ppm'),('1JP-Se coupling',711,'Hz')],['numeric overnight duration','temperature','specific commercial TOP lot for every later experiment'])
u=procedure('dppse',2,'Diphenylphosphine selenide preparation','DPPSe precursor',[
 'In a nitrogen glovebox combine selenium shot, DPP and anhydrous toluene in a one-neck flask with stir bar. Seal with septum and remove from glovebox.',
 'Quickly replace septum with water-cooled condenser under slight N2 flow. Bring solution to reflux for16h; slightly yellow clear solution results. No numeric reflux temperature supplied.',
 'Rotary evaporate toluene until white solid precipitates; recrystallize solid from hot toluene, yielding diffraction-quality crystals. No DPPSe CIF is supplied.'
],[('selenium mass',1.58,'g'),('selenium amount',20,'mmol'),('DPP volume',3.48,'mL'),('DPP amount',20,'mmol'),('anhydrous toluene volume',25,'mL'),('reflux duration',16,'h'),('1H shift',7.23,'ppm'),('1JH-P coupling',456,'Hz'),('31P shift',7.5,'ppm'),('1JP-Se coupling',768,'Hz'),('31P doublet shift',7.5,'ppm'),('1JP-H coupling',457,'Hz')],['numeric reflux temperature','pressure','N2 flow rate','recrystallization solvent volume/cooling rate','yield'])
u=procedure('tippse',2,'Tri-isopropylphosphine selenide preparation','TIPPSe precursor',[
 'Combine TIPP, elemental selenium and anhydrous toluene in N2 glovebox; stir at room temperature overnight.',
 'Remove volatiles in vacuo; recrystallize remaining white solid from hot toluene.'
],[('TIPP volume',500,'uL'),('TIPP amount',2.6,'mmol'),('Se mass',.205,'g'),('Se amount',2.6,'mmol'),('toluene volume',2.5,'mL'),('31P shift',69.7,'ppm'),('1JP-Se coupling',714,'Hz')],['numeric room temperature','numeric overnight duration','vacuum pressure','recrystallization volumes','yield'])
u=procedure('tepse',2,'Triethylphosphine selenide preparation','TEPSe precursor',[
 'Combine TEP, elemental selenium and anhydrous toluene; stir overnight in N2 glovebox.',
 'Filter off excess solid selenium and retain solution. Rotary evaporate toluene to isolate solid product.',
 'Recrystallize from hot acetone, filter to retain product crystals, and wash with cold acetone.'
],[('TEP volume',2.0,'mL'),('TEP amount',13.6,'mmol'),('Se mass',1.10,'g'),('Se amount',14.0,'mmol'),('toluene volume',20,'mL'),('31P shift',43.5,'ppm'),('1JP-Se coupling',716,'Hz')],['overnight time/temperature','filter specification','acetone volumes/temperatures','yield'])
u=procedure('tppse',2,'Triphenylphosphine selenide preparation','TPPSe precursor',[
 'Combine TPP, elemental selenium and anhydrous toluene; stir overnight in N2 glovebox.',
 'Filter off excess selenium, retaining solution; rotary evaporate toluene to yield white TPPSe solid.',
 'Recrystallize from hot toluene; wash isolated crystals with cold acetone.'
],[('TPP mass',.734,'g'),('TPP amount',2.8,'mmol'),('Se mass',.25,'g'),('Se amount',3.17,'mmol'),('toluene volume',10,'mL'),('31P shift',35.9,'ppm'),('1JP-Se coupling',762,'Hz')],['TPP supplier/purity','numeric overnight duration/temperature','recrystallization conditions','wash volumes','yield'])
u=procedure('tertiary-negative-rescue',2,'Pure tertiary phosphine selenide negative control and DIPP rescue','TIPPSe/Pb oleate control then rescued mixture',[
 'Combine Pb oleate and TIPPSe in a total600uL toluene-d8 in J-Young NMR tube. Source heading says tertiary phosphines, but actual reagent is TIPPSe.',
 'Heat120°C for5h; monitor optical absorption and31P NMR periodically. No reaction evident by either method.',
 'Add DIPP; solution rapidly changes colorless to black, described as indicative of PbSe QD formation. Exact rescue temperature/time and structure/size are not specified.',
 'Analogous TEPSe and TPPSe reactions give identical results; their individual replacement masses/volumes are not supplied.'
],[('Pb oleate mass',36.9,'mg'),('Pb oleate amount',48,'umol'),('TIPPSe mass',23.0,'mg'),('TIPPSe amount',48,'umol'),('toluene-d8 total volume',600,'uL'),('control temperature',120,'degC'),('control duration',5,'h'),('DIPP volume',7,'uL'),('DIPP amount',48,'umol')],['conflicting TIPPSe mass/amount','numeric rescue time/temperature','instrument detection limits','TEPSe/TPPSe replacement charges','QD phase/size/yield'],conflicts=['C1'],kind='negative_control_and_rescue')
fact(u,'outcome before rescue','No evident reaction by absorption and31P NMR',qualifier='Tested control outcome, not universal failure probability.')
fact(u,'outcome after DIPP','Colorless to black; authors infer PbSe QD formation',qualifier='Do not promote color alone to a verified exact crystal structure.')
u=procedure('topse-distillation',6,'Fractional distillation of neat TOPSe','TOPSe fractions A and C plus two unlabelled cuts',[
 'Charge10mL neat TOPSe to one-neck flask with short-path distillation head and receiving flask. Evacuate50mTorr; heat slowly.',
 'Collect A starting185°C for2mL. Collect two further2mL cuts at190°C and195°C; these cuts are not labelled B.',
 'Remaining approximately4mL in round-bottom flask is C. Use31P NMR integrations to determine reported composition.'
],[('initial TOPSe volume',10,'mL'),('pressure',50,'mTorr'),('A collection start temperature',185,'degC'),('A collected volume',2,'mL'),('unlabelled cut2 temperature',190,'degC'),('unlabelled cut2 volume',2,'mL'),('unlabelled cut3 temperature',195,'degC'),('unlabelled cut3 volume',2,'mL')],['heating rate','temperature location/head vs pot','cut collection durations','unlabelled cut identities/compositions'],kind='purification')
fact(u,'C residual volume',4,'mL',raw='~4.0mL',approx=True)
u=procedure('topse-B-stock',6,'Independent sample B stock','TOPSe/TOP B stock',[
 'Make1.0M TOPSe in TOP; prose says dissolve TOPSe in TOP whereas FigureS4 caption says dissolve selenium powder in TOP. Both wordings retained; B is not the second distillation cut.'
],[('nominal TOPSe concentration',1.0,'mol/L')],['total volume/charges','preparation starting-species wording conflict','stirring time/temperature'],conflicts=['C4'],kind='stock_preparation')
u=procedure('pbse-msc-family',7,'PbSe magic-size-cluster composition comparison','PbSe MSC A/B/C family',[
 'Combine PbO, oleic acid and octadecene in a three-neck flask; heat under nitrogen150°C until yellow solid fully dissolves to form Pb oleate.',
 'Cool40°C; inject1mmol TOPSe. Correct source concentration for analytical purity using octadecene dilution; injection volume not reported.',
 'Monitor absorption at regular intervals. A/B/C denote TOPSe sources with different31P-integrated compositions; main Figure1 compares40min. Individual FigureS5 curve times are not reported.',
 'A produces substantial MSCs and absorption saturates near600nm; C has negligible growth under these conditions.'
],[('PbO mass',104,'mg'),('PbO amount',.47,'mmol'),('oleic acid volume',.59,'mL'),('oleic acid amount',1.9,'mmol'),('octadecene volume',1.4,'mL'),('precursor dissolution temperature',150,'degC'),('injection/growth temperature',40,'degC'),('TOPSe amount',1,'mmol'),('comparison time',40,'min')],['dissolution time','corrected injection volume/concentration','individual S5 sampling times','exact N2 flow/pressure','workup','numeric MSC size/yield'],kind='synthesis_variant_family')
fact(u,'A absorption saturation location',600,'nm',raw='near600nm',approx=True,qualifier='Saturation of absorption trace, not assigned excitonic peak.')
u=procedure('dpp-pb-control',8,'DPP and Pb oleate thermal control','DPP/Pb oleate sealed-tube control',[
 'Combine DPP, Pb oleate and toluene-d8 in an NMR tube; flame-seal under vacuum.',
 'Heat in140°C oil bath and monitor NMR with time. Main reports Pb0 formation after hours, unlike QD formation in minutes; species12 and oleic acid appear in time courses.',
 'Main separately reports that resulting Pb0 is inert to TOPSe; no complete challenge protocol supplied.'
],[('DPP volume',100,'uL'),('DPP amount',.57,'mmol'),('Pb oleate mass',.22,'g'),('Pb oleate amount',.57,'mmol'),('toluene-d8 volume',500,'uL'),('oil bath temperature',140,'degC')],['Pb oleate mass/amount mismatch','vacuum pressure','quantitative Pb0 assay','complete Pb0+TOPSe challenge charges/temperature/time'],conflicts=['C2'],kind='mechanistic_control')
u=procedure('dpp-cd-negative',8,'DPP and Cd oleate negative thermal control','DPP/Cd oleate control',[
 'Combine DPP, Cd oleate and toluene-d8 using analogous sealed-tube heating procedure; monitor at140°C over several days.',
 'No reaction observed. A numeric duration, detection limit and separately resolved spectra are not provided.'
],[('DPP volume',25,'uL'),('DPP amount',.14,'mmol'),('Cd oleate mass',.14,'g'),('Cd oleate amount',.21,'mmol'),('toluene-d8 volume',600,'uL'),('inherited bath temperature',140,'degC')],['numeric several-days duration','vacuum pressure','detection limit'],parents=['evans2010-dpp-pb-control'],kind='negative_control')
fact(u,'observed outcome','No reaction after several days')
u=procedure('species9-crystallization',16,'Molecular species9 crystallization','isolated Pb(Se2PPh2)2 crystal9',[
 'Combine500uL0.1M DPPSe in toluene and100uL0.1M Pb oleate in toluene at room temperature.',
 'Allow slow solvent evaporation for several days; isolate single crystals of9. This is the species in the supplied CIF.',
 'SI FigureS12/main describe excessDPPSe>5:1; the given charges nominally give5:1. Retain both rather than redefining an exact threshold.'
],[('DPPSe stock volume',500,'uL'),('DPPSe stock concentration',.1,'mol/L'),('Pb oleate stock volume',100,'uL'),('Pb oleate stock concentration',.1,'mol/L')],['numeric room temperature','exact evaporation duration','vessel/atmosphere','isolation workup','numeric isolated yield'],conflicts=['C5'],kind='molecular_crystal_preparation')
fact(u,'nominal DPPSe amount from concentration-volume',50,'umol',status='computed_from_reported',qualifier='0.5mL×0.1mol/L; not an additional independent reported charge.')
fact(u,'nominal Pb oleate amount from concentration-volume',10,'umol',status='computed_from_reported')
fact(u,'nominal DPPSe-to-Pb ratio',5,'mol/mol',status='computed_from_reported',qualifier='Exact reported charges give5:1, while text says>5:1.')
u=procedure('pbse-qd',19,'PbSe quantum-dot synthesis with DPPSe','PbSe80°C QDs; S15 red optical specimen',[
 'In a nitrogen glovebox dissolve DPPSe in2mL anhydrous toluene; add oleic acid.',
 'Combine with2mL0.025M Pb oleate stock. Its solvent is not explicitly specified here; do not silently infer it from the DPPSe solvent.',
 'Transfer reaction mixture to a Teflon-sealable1cm cuvette and seal under N2. Remove from glovebox; heat in80°C oil bath.',
 'MSCs predominate at short times; QDs grow after several minutes. FigureS15 red absorption/fluorescence example is after20min. No postprocessing/size-selection for that example.'
],[('DPPSe mass',2.6,'mg'),('DPPSe amount',10,'umol'),('anhydrous toluene volume',2,'mL'),('oleic acid volume',12.6,'uL'),('oleic acid amount',40,'umol'),('Pb oleate stock volume',2,'mL'),('Pb oleate stock concentration',.025,'mol/L'),('Pb oleate amount',50,'umol'),('cuvette optical length',1,'cm'),('oil bath temperature',80,'degC'),('optical example heating duration',20,'min')],['Pb oleate stock solvent','internal liquid temperature/ramp','sealed pressure','numeric MSC-to-QD transition time','quench/workup/storage','exact TEM specimen link','numeric PLQY'],kind='nanocrystal_synthesis')
u=procedure('cdse-qd',19,'CdSe quantum-dot synthesis with DPPSe','CdSe200°C QDs; S15 blue optical specimen',[
 'Heat1mL octadecene containing0.025M Cd oleate (25umol) and630umol oleic acid to200°C in a three-neck flask under flowing N2.',
 'At growth temperature rapidly inject1mL octadecene containing0.025M DPPSe (25umol) and630umol oleic acid.',
 'Immediate colorless-to-yellow change indicates CdSe formation. FigureS15 blue absorption/fluorescence example is after10min; no postprocessing/size-selection for that example.'
],[('Cd stock volume',1,'mL'),('Cd oleate stock concentration',.025,'mol/L'),('Cd oleate amount',25,'umol'),('oleic acid in Cd stock',630,'umol'),('growth temperature',200,'degC'),('DPPSe injection stock volume',1,'mL'),('DPPSe stock concentration',.025,'mol/L'),('DPPSe amount',25,'umol'),('oleic acid in Se stock',630,'umol'),('optical example heating duration',10,'min')],['numeric injection rate/duration','N2 flow','flask capacity','temperature recovery','quench/workup/storage','numeric PLQY','exact particle size'],kind='nanocrystal_synthesis')
fact(u,'identity normalization','Cd(oleate)2',qualifier='S19 prints Cd(oleate); S1 defines Cd(C18H33O2)2. Preserve source spelling without inventing a different Cd oxidation state.')

# Original objects, including captions, retain their exact pixels; curve values are not fabricated.
figure_claims={
 'figure-1':('Observed PbSe MSC absorption after40min at40°C for TOPSe sources A/B/C. Composition percentages are31P-integration results, not mass percentages; impurity sums are not normalized to100.','observation'),
 'table-1':('Eight identified organic reaction products; nucleus-specific shifts and identification evidence are expanded in the typed table. R=C17H33; all spectra in toluene-d8.','table'),
 'scheme-1':('Proposed ligand-disproportionation/selenium-exchange mechanism; monomer1 and intermediate6 not isolated. Only stated observed byproducts and molecular9 count as observed.','author_model'),
 'scheme-2':('Proposed DPP/Pb oleate route through10/11 to Pb0+12; no isolated10/11 structures are supplied.','author_model'),
 'figure-2':('31P{1H} neat TOPSe+15%(mol,mol) DPP before and30min after Pb oleate at40°C. Products3 and12 support secondary-phosphine chemistry; no numeric kinetic fit.','observation'),
 'figure-S1':('Commercial TOP90% Aldrich and97% Strem contain numerous unidentified impurities. DOP/DOPO coupling panels support two identities; arbitrary extra peak labels remain unassigned.','observation'),
 'figure-S2':('Neat tributylphosphine shows dibutylphosphine at−69.5ppm among unassigned peaks. Not a complete tributylphosphine-based QD synthesis.','observation'),
 'figure-S3':('TOPSe and DOPSe resonances plus three unidentified P(V) Se species; alkoxy-derivative identities are tentative author proposals. H3PO4 standard in flame-sealed capillary.','observation'),
 'figure-S4':('31P-integrated composition spectra for distilledA/residueC and independently madeB stock; all printed peak/integral labels remain in exact original.','observation'),
 'figure-S5':('Absorption at regular unreported sampling intervals for A/B/C. A saturates near600nm; C nearly unreactive. Curve numbers are not individual synthesis replicates.','observation'),
 'figure-S6':('DPP/Pb140°C31P time course with H3PO4 capillary standard; printed integrals are intensity comparisons, not independent isolated yields.','observation'),
 'figure-S7':('Corresponding1H time course; DPP integrals calibrated using FigureS6 phosphorus signal. Oleic acid grows as DPP decreases.','observation'),
 'figure-S8':('DPPSe/Cd oleate ratio family2:1,1:1,1:2 at approximately10min room temperature. Inset identifies compound8 Se satellites; unassigned resonances remain unassigned.','observation'),
 'figure-S9':('DPPSe/Pb oleate1:1 at approximately10min room temperature; caption notes analogous resonances for Cd. This does not merge the Cd/Pb samples.','observation'),
 'figure-S10':('Same Cd1:2 mixture10min versus24h. Caption describes3 and oleic acid disappearing,4/5 forming; original24h31P panel still labels98.93, so no exactzero concentration inferred. Crystals13 reported after slow evaporation; no13 CIF supplied.','observation'),
 'figure-S11':('13C spectrum of same24h sample as FigureS10C/D supports oleic anhydride5; no new synthesis or independent batch.','observation'),
 'figure-S12':('Single-crystal structure of isolated molecular9; atom labels correspond to retained molecular CIF. High yield qualitative only.','structure'),
 'figure-S13':('Molecular9 nearest-neighbor packing. Authors compare near90° geometry to potential rocksalt-like growth pathways; this is not QD diffraction.','structure_and_interpretation'),
 'figure-S14':('Two coexisting monomer-formation pathways proposed: secondary phosphine selenide reaction, or metal-phosphine formation then selenium exchange.','author_model'),
 'figure-S15':('Absorption solid and fluorescence dotted: CdSe blue after10min, PbSe red after20min. No postsynthetic processing/size-selective precipitation. Exact peak energies, linewidths and PLQY are not tabulated; do not estimate as reported numbers.','property'),
 'figure-S16':('TEM examples: small spherical PbSe left with hexagonal particle packing; larger cubic QDs right with cubic particle packing. Superlattice packing is distinct from atomic crystal phase.5nm/50nm bars are image scales.','characterization'),
 'scheme-S1':('Proposed paths to9 via unobserved1,6,14 and selenium exchange. Only9 was isolated as an M–Se molecular species.','author_model'),
 'scheme-S13-unnumbered':('Proposed disproportionation2eq diphenylphosphine oxide4→diphenylphosphinic acid13+DPP, citing Synthesis1987.','author_model'),
 'table-S7-composition':('Three source-composition rows calculated from31P integrations. Three listed species do not sum100 because other impurities remain.','table'),
 'calculation-S21-yield':('Representative optical conversion calculation using literature extinction/size calibration. Sample charge/volume differ from S19; final denominator has a contradictory printed exponent.','calculation')}
object_units={}
for a in assets['assets']:
 claim,kind=figure_claims[a['id']]
 scope=next((x['sample_scope'] for x in initial['figure_table_scheme_inventory'] if x['id']==a['id']),a['id'])
 uid=unit('object-'+a['id'],a['source_role'],a['pdf_page'],a['id'],kind,claim,scope,{'original_asset':a,'numeric_trace_digitization':'not_performed; original printed curves/labels are retained'},[a['id']],status='author_interpretation' if kind=='author_model' else 'reported',conflicts=['C6'] if a['id']=='calculation-S21-yield' else (['C4'] if a['id']=='figure-S4' else []))
 object_units[a['id']]=uid

uid=object_units['table-1'];rows=[]
for num,name,condensed,nucleus,delta,coupling,identity in [
 (2,'Oleic acid','RCOOH','1H',[12.2,12.5],None,'verified by authentic sample'),
 (3,'9-Octadecenoxydiphenylphosphine','Ph2P-O-C(=O)R','31P',98.9,None,'literature identity: Chemiker Zeitung1982,391–395'),
 (4,'Diphenylphosphine oxide','Ph2P(=O)H','31P',22.0,['1JP-H',441],'verified by authentic sample'),
 (5,'Oleic anhydride','RCO-O-COR','13C',168.9,None,'verified by authentic sample'),
 (7,'Diphenylphosphine','Ph2PH','31P',-40.2,['1JP-H',215],'verified by authentic sample'),
 (8,'9-Octadecenoxydiphenylphosphine selenide','Ph2P(=Se)-O-C(=O)R','31P',77.1,['1JP-Se',875],'literature identity: Chem.Commun.2005,2692–2694'),
 (12,'Tetraphenyldiphosphine','Ph2P-PPh2','31P',-14.5,None,'verified by authentic sample; isolated diffraction-quality single crystals'),
 (13,'Diphenylphosphinic acid','Ph2P(=O)OH','31P',25.7,None,'verified by authentic sample; isolated diffraction-quality single crystals')]:
 row={'source_label':num,'name':name,'condensed_structure':condensed,'R':'C17H33','nucleus':nucleus,'shift_ppm':delta,'coupling':coupling,'identification':identity,'solvent':'toluene-d8','coordinates_supplied':False}
 rows.append(row)
 if isinstance(delta,list):fact(uid,f'compound{num} {nucleus} shift',None,'ppm',raw='12.2–12.5',lo=delta[0],hi=delta[1],scope=f'compound{num}')
 else:fact(uid,f'compound{num} {nucleus} shift',delta,'ppm',scope=f'compound{num}')
 if coupling:fact(uid,f'compound{num} {coupling[0]} coupling',coupling[1],'Hz',scope=f'compound{num}')
tables.append({'id':'table-1','source_unit_id':uid,'rows':rows,'footnotes':{'a':'All spectra in toluene-d8','b':'1H NMR','c':'31P NMR','d':'13C NMR','e':'Verified by addition of authentic sample','f':'Diffraction-quality single crystals isolated from reaction','g':'Chemiker Zeitung1982,391–395','h':'Chem.Commun.2005,2692–2694'},'coordinate_scope':'Table identifies crystal isolation for12/13, but supplied CIF is only9.'})

uid=object_units['table-S7-composition'];rows=[]
for label,v in [('A',[82.7,11.0,1.1]),('B',[45.0,53.6,.1]),('C',[99.3,.14,.02])]:
 row={'sample':label,'basis':'31P peak integration, not weight%','TOPSe_percent':v[0],'TOP_percent':v[1],'DOP_percent':v[2]};rows.append(row)
 for name,val in zip(['TOPSe','TOP','DOP'],v):fact(uid,f'{label} {name} fraction',val,'%',scope=f'TOPSe source {label}',qualifier='Reported31P-integration fraction; other impurities omitted from summary; no renormalization.')
tables.append({'id':'table-S7-composition','source_unit_id':uid,'rows':rows,'duplicate_main_figure':'figure-1','duplicate_policy':'One underlying composition determination, not two independent measurements.'})
uid=object_units['figure-1'];quantities(uid,[('reaction temperature',40,'degC'),('comparison time',40,'min')])
uid=object_units['figure-S1'];quantities(uid,[('DOP 1JH-P',189,'Hz'),('DOPO 1JH-P',435,'Hz')])
uid=object_units['figure-S2'];fact(uid,'dibutylphosphine31P shift',-69.5,'ppm')
uid=object_units['figure-S3'];quantities(uid,[('panelB coupling',726,'Hz'),('panelC coupling',725,'Hz'),('panelD coupling',711,'Hz'),('TOPSe panelE coupling',711,'Hz'),('DOPSe panelF coupling',724,'Hz'),('DOPSe panelG H-P coupling',420,'Hz'),('H3PO4 standard',0,'ppm')])
fact(uid,'tentative identities panelsB-C-D','possible alkoxy derivatives of TOPSe',status='author_interpretation',qualifier='Not chemically identified; keep symbolic/unassigned.')
uid=unit('impurity-reactivity','main',1,'Last two right-column paragraphs','observation','DOP and DBP impurities in commercial tertiary phosphines. DOPSe observed in neat TOPSe disappears immediately with metal carboxylate at300K; authors attribute critical nucleation role.',scope='impurity observation, not a separate full recipe')
quantities(uid,[('DOP31P shift',-69.7,'ppm'),('DBP31P shift',-69.5,'ppm'),('DOPSe31P shift',4.7,'ppm'),('DOPSe P-Se coupling',725,'Hz'),('metal-carboxylate combination temperature',300,'K')])
fact(uid,'shift-coupling context','Main DOPSe725Hz vs FigureS3 panelF724Hz retained separately',qualifier='Reported contextual/rounding difference, not forced consensus.')

uid=object_units['figure-S6'];nmrrows=[]
for panel,time,dpp,product,dpH,acid in zip('ABCDEF',[0,10,20,40,60,240],[35.33,33.37,31.05,30.82,28.02,22.42],[None,1.46,3.11,4.60,5.22,8.21],[10.00,9.44,8.79,8.72,7.93,6.35],[0.00,.62,1.29,2.33,2.69,4.39]):
 nmrrows.append({'panel':panel,'time_min':time,'time_zero_basis':'prior to heating' if panel=='A' else 'elapsed heating','31P_DPP_integral':dpp,'31P_12_integral':product,'31P_standard_integral':100,'1H_DPP_calibrated_integral':dpH,'1H_oleic_acid_integral':acid,'integral_units':'relative arbitrary normalization, not yield'})
 fact(uid,f'panel{panel} sampling time',time,'min',qualifier='A means prior to heating, not a measured kinetic time origin.' if panel=='A' else '')
 fact(uid,f'panel{panel} DPP31P integral',dpp,'relative_integral')
 fact(uid,f'panel{panel} compound12 integral',product,'relative_integral',status='not_tabulated' if product is None else 'reported',qualifier='No A product integral printed; do not invent zero.' if product is None else '')
 fact(object_units['figure-S7'],f'panel{panel} calibrated DPP1H integral',dpH,'relative_integral')
 fact(object_units['figure-S7'],f'panel{panel} oleic acid1H integral',acid,'relative_integral')
tables.append({'id':'nmr-control-timecourse','source_unit_ids':[uid,object_units['figure-S7']],'rows':nmrrows,'sample_link':'dpp-pb-control; one time series with two nuclei, not six replicate syntheses.'})
quantities(uid,[('bath temperature',140,'degC'),('compound12 shift',-14.4,'ppm'),('DPP shift',-40.1,'ppm'),('standard shift',0,'ppm'),('standard normalized integral',100,'relative_integral')])
quantities(object_units['figure-S7'],[('DPP doublet shift',5.2,'ppm'),('oleic acid shift',12.5,'ppm')])
uid=object_units['figure-S8'];ratios=[]
for panel,a,b in [('A',2,1),('B',1,1),('C',1,2)]:
 ratios.append({'panel':panel,'DPPSe_parts':a,'Cd_oleate_parts':b,'basis':'reagent stoichiometric ratio','absolute_amounts':None})
 fact(uid,f'panel{panel} DPPSe-to-Cd ratio',a/b,'mol/mol',raw=f'{a}.0:{b}.0',scope=f'Cd ratio sample{panel}',qualifier='No absolute charges, not independently complete recipe.')
fact(uid,'sampling time',10,'min',raw='~10minutes',approx=True);fact(uid,'reaction temperature','room temperature')
fact(uid,'compound8 Se-satellite coupling',875,'Hz',qualifier='Inset onB, not an atomic structural determination.')
tables.append({'id':'cd-stoichiometry-family','source_unit_id':uid,'rows':ratios})
uid=object_units['figure-S9'];fact(uid,'DPPSe-to-Pb ratio',1,'mol/mol',raw='1:1');fact(uid,'sampling time',10,'min',raw='~10minutes',approx=True);fact(uid,'temperature','room temperature')
uid=object_units['figure-S10'];quantities(uid,[('DPPSe-to-Cd ratio',.5,'mol/mol','1:2'),('early sampling time',10,'min'),('late sampling time',24,'h'),('oleic acid1H shift',12.33,'ppm'),('compound3 31P shift',98.9,'ppm'),('compound4 31P shift caption',21.6,'ppm'),('isolated compound13 shift',25.7,'ppm')])
fact(uid,'late-panel residual label',98.93,'ppm',qualifier='Label remains in plotted late trace despite caption disappearance statement; no exactzero concentration.')
fact(uid,'compound13 crystal preparation','Slow solvent evaporation after synthesis; no numeric time/volume/temperature specified')
uid=object_units['figure-S11'];fact(uid,'anhydride carbonyl13C shift',168.93,'ppm',qualifier='Printed peak label; same sample as S10C/D, not a second experiment.')
uid=unit('dppse-room-temp-reactivity','main',2,'Opening left-column paragraphs and ratio discussion','observation','DPPSe plus Pb oleate in toluene gives immediate PbSe MSCs at room temperature and complete DPPSe consumption by31P NMR. Authors report analogous CdSe organic byproducts; precise absolute charges for NMR panels not supplied.',scope='mechanistic DPPSe/metal-carboxylate experiments')
fact(uid,'DPPSe conversion statement','complete by31P NMR',qualifier='Do not substitute isolated QD yield.')
fact(uid,'examined nominal DPPSe-to-Cd ratio range',None,'mol/mol',raw='10:1 to1:2',lo=.5,hi=10,qualifier='Main then discusses PbSe/species9; metal assignment ambiguity C3.');facts[-1]['conflict_ids']=['C3']
fact(uid,'excess DPPSe threshold',None,'mol/mol',raw='>5:1',lo=5,lo_exclusive=True,qualifier='Strong excess gives molecular9 and minimal larger PbSe species; exact5:1 recipe separately retained.');facts[-1]['conflict_ids']=['C3','C5']
fact(uid,'metal-rich reaction temperature',300,'K');fact(uid,'organic byproduct evolution time',24,'h')
fact(uid,'MSC size during slow organic reaction','No significant size change reported',qualifier='No numeric diameter or resolution provided.')
uid=object_units['figure-2'];quantities(uid,[('DPP addition fraction',15,'mol%','15%(mol,mol)','Denominator not explicitly formalized beyond TOPSe plus DPP description.'),('elapsed time',30,'min'),('temperature',40,'degC'),('product3 shift',98.9,'ppm'),('product12 caption shift',-14.5,'ppm')])
uid=unit('dpp-topse-main-shifts','main',2,'Right column15%DPP/TOPSe paragraph','observation','Secondary phosphine/selenide resonances disappear immediately after Pb oleate addition;3/12 organic products appear.',scope='TOPSe+15%DPP observation')
quantities(uid,[('DOP pre-addition shift',-69.1,'ppm'),('DOPSe pre-addition shift',4.3,'ppm'),('DPPSe pre-addition shift',5.9,'ppm'),('compound12 prose shift',-14.0,'ppm'),('compound3 shift',98.9,'ppm')])
fact(uid,'product12 prose-caption distinction','−14.0ppm prose and−14.5ppm Figure2 caption retained as separate reported contexts')

scheme_steps={
 'scheme-1':['Pb(oleate)2+DPPSe→monomer1+oleic acid2 (proposed)','2eq1→extended(PbSe)2 species+3 (proposed)','3+2→4+5 (byproducts observed; elementary pathway proposed)','1+DPPSe⇌6+DPP7 (proposed selenium exchange)','2eq6→extended PbSe species+8 (proposed)','6+2eqDPPSe→9+2+7 (proposed pathway;9 isolated)'],
 'scheme-2':['Pb(oleate)2+DPP→oleate-Pb-PPh2(10)+oleic acid','10+DPP→Ph2P-Pb-PPh2(11)+oleic acid','11→Pb0+tetraphenyldiphosphine12'],
 'scheme-S1':['Pb oleate+DPPSe→1+oleic acid via ligand disproportionation','1+DPPSe→6+DPP via selenium exchange','alternative1+DPPSe→14+oleic acid via ligand disproportionation','6+2eqDPPSe→9+oleic acid+DPP through ligand disproportionation/selenium exchange','14+2eqDPPSe→9+2eqDPP through two selenium exchanges'],
 'scheme-S13-unnumbered':['2eqPh2P(O)H→Ph2P(O)OH(13)+Ph2PH'],
 'figure-S14':['TOPSe+DOP⇌TOP+DOPSe','DOPSe+Pb oleate→proposed PbSe monomer+oleic acid','alternative DOP+Pb oleate→proposed metal-phosphine+oleic acid; TOPSe selenium exchange generates monomer+TOP']}
for ident,steps in scheme_steps.items():
 uid=object_units[ident];unit_by_id[uid]['payload']['transcribed_reaction_steps']=steps
 fact(uid,'reaction pathway',steps,status='author_interpretation',qualifier='Source-native proposed mechanism; arrows do not establish measured rates or isolated atomic structures.')
uid=unit('se-exchange-evidence','main',3,'Opening paragraph; main PDF2 final paragraph','observation','Authors observed direct selenium exchange between TOPSe and impurity DOP by NMR, with equilibrium weighted toward TOPSe. No equilibrium constant or rate constant is supplied.')
fact(uid,'qualitative equilibrium direction','toward TOPSe');fact(uid,'equilibrium constant',None,status='not_reported')
unit('mechanism-limit-and-outlook','main',3,'Conclusion and ligand/size-control discussion','author_interpretation','Complete kinetic analysis is necessary to prove the proposed mechanism. Extension to secondary phosphine sulfides/tellurides is anticipated, not demonstrated here. Size control depends on interrelated temperature, ligand and stoichiometry; further study underway. Cheaper/benign reagents are future expectations.',status='author_interpretation')
uid=unit('ligand-aggregation','main',3,'Second paragraph','observation','Excess ligand not necessary for growth but suppresses aggregation evident after several hours. No quantitative aggregation threshold or specific ligand-free charge recipe supplied.')
fact(uid,'aggregation onset','after several hours',qualifier='Qualitative study-wide statement; not exact sample time.')

# Printed annotations are transcribed separately from chemical assignment and curve digitization.
annotations={
 'figure-S1':{'A':{'peak_labels_ppm':[130.3,53.5,42.7,28.3,.5,-4.9,-10.4,-21.4,-32.2,-34.1,-37.1,-42.0,-46.3,-50.6,-69.0]},'B':{'peak_labels_ppm':[132.4,131.9,130.3,52.3,40.7,26.9,-13.7,-18.8,-27.5,-32.4,-69.4]},'C':{'peak_labels_ppm':[-68.7,-69.6],'coupling_Hz':189},'D':{'peak_labels_ppm':[28.2,26.0],'coupling_Hz':435}},
 'figure-S2':{'single':{'peak_labels_ppm':[46.19,42.83,28.13,-19.89,-28.25,-32.28],'integrals_left_to_right':[.02,.23,1.12,.14,.15,100.00,.56],'chemical_assignment':'Only caption-identified DBP at−69.5ppm; other numeric labels not assigned to chemical identity.'}},
 'figure-S3':{'A':{'peak_labels_ppm':[58.34,54.49,48.60,36.73,4.74]},'B':{'coupling_Hz':726,'identity':'unidentified; possible alkoxy derivative only'},'C':{'coupling_Hz':725,'identity':'unidentified; possible alkoxy derivative only'},'D':{'coupling_Hz':711,'identity':'unidentified; possible alkoxy derivative only'},'E':{'coupling_Hz':711,'identity':'TOPSe'},'F':{'coupling_Hz':724,'identity':'DOPSe'},'G':{'coupling_Hz':420,'identity':'DOPSe P-H coupled'}},
 'figure-S4':{'A':{'peak_labels_ppm':[36.77,-31.72,-69.21],'integrals_left_to_right':[2.15,32.87,1000.00,1.99,6.29,4.06,132.44,11.86,2.72,1.51,12.99]},'B':{'integrals_left_to_right':[.92,1.19,11.92,1000.00,3.60,17.27,1147.52,2.20]},'C':{'integrals_left_to_right':[.53,.56,4.19,1000.00,.25,.17,1.41,.16],'central_integral_reading_note':'1000.00 confirmed using rotated magnified original-pixel detail; plotted lines cross the label. Original reported composition is retained rather than recomputed.'}},
 'figure-S8':{'A':{'peak_labels_ppm':[77.06,37.63,36.50,20.74,17.18,15.79,7.52,-14.22,-39.93],'integrals_left_to_right':[29.09,24.36,22.28,181.08,65.29,100.00,269.64]},'B':{'peak_labels_ppm':[99.12,76.80,-14.21],'integrals_left_to_right':[147.43,35.85,100.00],'inset_peak_ppm':76.82,'inset_coupling_Hz':875},'C':{'peak_labels_ppm':[99.11,-14.21],'integrals_left_to_right':[557.83,100.00]}},
 'figure-S9':{'single':{'peak_labels_ppm':[98.86,76.31,23.68,-14.48,-40.31]}},
 'figure-S10':{'A':{'peak_labels_ppm':[98.93,-14.40]},'B':{'peak_labels_ppm':[12.33]},'C':{'peak_labels_ppm':[98.93,25.77,21.69,-14.40]},'D':{'peak_labels_ppm':[]}},
 'figure-S11':{'single':{'peak_labels_ppm':[168.93]}},
 'figure-S7':{'F':{'additional_peak_labels_ppm':[12.5,5.5,5.4,5.0],'note':'5.5 is a printed nearby resonance; do not relabel all peaks DPP. DPP identity from caption is the5.2ppm doublet.'}}
}
for ident,panels in annotations.items():
 uid=object_units[ident];unit_by_id[uid]['payload']['printed_annotations']=panels
 for panel,data in panels.items():
  fact(uid,f'panel{panel} printed annotations',data,status='source_figure_transcription',qualifier='Transcribed printed labels only, in visual left-to-right order where stated; not a digitized trace, complete peak-picking result or chemical identity assignment.',scope=unit_by_id[uid]['sample_scope']+' panel'+panel)

uid=unit('species9-acquisition','si',15,'Solution and Refinement of Crystal Structure for9','crystallographic_acquisition','Yellow rod on glass fiber under cold N2 at100.0(1)K on Bruker SMART APEX II CCD. SI reports29063 reflections spanningχ1.89–36.32°; CIF identifies diffraction theta range. Triclinic P-1 assigned, solved SIR97 and refined SHELXL-97. Missing SI reference4 retained.',scope='isolated molecular9 crystal',payload={'crystal_description':'yellow rod','mount':'glass fiber','cooling_gas':'nitrogen','instrument':'Bruker SMART APEX II CCD Platform','space_group':'P-1','structure_solution':'SIR97','refinement':'SHELXL-97','angle_symbol_source_difference':'SI χ; CIF diffraction theta','CIF_pointer':'cif-source-inventory.json'},conflicts=['C7','C8'])
for p,v in [('largest dimension',.22),('middle dimension',.10),('smallest dimension',.08)]:fact(uid,p,v,'mm',approx=True,qualifier='SI gives approximate dimensions0.22×0.10×0.08mm³; separate lengths retained, not one scalar volume.')
fact(uid,'temperature',100.0,'K',raw='100.0(1)K',qualifier='Source uncertainty0.1K.');facts[-1]['standard_uncertainty']=.1
quantities(uid,[('reflections reported in SI',29063,'count'),('diffraction angular minimum',1.89,'deg'),('diffraction angular maximum',36.32,'deg')])
uid=object_units['figure-S13'];quantities(uid,[('Pb-Se-Pb angle',90.48,'deg'),('Se-Pb-Se angle',89.52,'deg'),('intermolecular Pb-Se contact',3.403,'angstrom'),('intramolecular Pb-Se distance1',2.997,'angstrom'),('intramolecular Pb-Se distance2',3.035,'angstrom')])
fact(uid,'contact interpretation','Authors state intermolecular contact too long to be a bond',status='author_interpretation')
fact(uid,'propagation interpretation','Possible transition-state-like alignment for intermolecular metathesis/rocksalt monomer growth',status='author_interpretation',qualifier='Static molecular packing does not measure actual QD growth transition-state structure.')
uid=object_units['figure-S16'];quantities(uid,[('left TEM scale bar',5,'nm'),('right TEM scale bar',50,'nm')])
fact(uid,'left morphology','small spherical PbSe QDs');fact(uid,'right morphology','larger cubic PbSe QDs')
fact(uid,'left particle packing','hexagonal');fact(uid,'right particle packing','cubic')
fact(uid,'TEM particle mean size',None,'nm',status='not_reported',qualifier='Scale bars are not diameters. No image-derived size distribution calculated here.')
fact(uid,'TEM exact route/time linkage',None,status='not_established',qualifier='PbSe/DPPSe family linked; separate morphology examples not tied to exactS19 timed optical sample.')
uid=object_units['figure-S15'];fact(uid,'absorption curve style','solid');fact(uid,'fluorescence curve style','dotted');fact(uid,'CdSe color','blue');fact(uid,'PbSe color','red')
fact(uid,'postsynthetic size-selection','none for illustrated spectra')
for p in ['optical peak wavelengths','linewidths','photoluminescence quantum yield']:fact(uid,p,None,status='not_tabulated',qualifier='Original curves supplied, but exact numeric values not printed; no fabricated curve digitization.')
uid=unit('yield-general','main',3,'Second paragraph','derived_result','PbSe80°C and CdSe200°C QDs show near-quantitative conversion >90% based on literature extinction coefficients; this is optical conversion, not isolated gravimetric yield.',scope='study-wide PbSe/CdSe QD claim')
fact(uid,'conversion yield lower bound',None,'%',raw='yield>90%',lo=90,lo_exclusive=True,status='author_derived',qualifier='Broad claim based on literature extinction calibration; no blanket per-variant outcome attachment.')
uid=object_units['calculation-S21-yield'];yieldrows=[
 ('initial limiting DPPSe',2.25e-6,'mol','2.25×10^-6mol','reported_input'),('absorption maximum',1300,'nm','1300nm','reported_input'),('diameter',4.1,'nm','4.1nm','author_derived'),('extinction coefficient',1.22e5,'L mol^-1 cm^-1','1.22×10^5M^-1cm^-1','author_derived'),('absorbance',.136,'dimensionless','0.136','reported_input'),('optical path length',1,'cm','1cm','reported_input'),('QD concentration',1.1e-6,'mol/L','1.1×10^-6M','author_derived'),('sample volume',3.025e-3,'L','3.025×10^-3L','reported_input'),('QD amount',3.33e-9,'mol','3.33×10^-9molQDs','author_derived'),('Avogadro constant used',6.023e23,'mol^-1','6.023×10^23','author_model_input'),('QD count',2.00e15,'count','2.00×10^15QDs','author_derived'),('single QD volume',3.61e-20,'cm^3','3.61×10^-20cm³/QD','author_derived'),('total QD volume',7.23e-5,'cm^3','7.23×10^-5cm³','author_derived'),('assumed lattice cell volume',2.29e-22,'cm^3','2.29×10^-22cm³','author_model_input'),('lattice cell count',3.16e17,'count','3.16×10^17lattices','author_derived'),('Se atoms per cell',4,'count','4Seatoms/lattice','author_model_input'),('Se atom count',1.26e18,'count','1.26×10^18Seatoms','author_derived'),('incorporated Se amount',2.10e-6,'mol','2.10×10^-6molSe','author_derived'),('reported conversion',93,'%','93%Conversion','author_derived')]
for p,v,s,r,st in yieldrows:fact(uid,p,v,s,raw=r,status=st,qualifier='Representative calculation sample; not proven identical to S19 recipe or S15/S16 specimen. C6 final denominator exponent conflict retained.')
eqs=[('diameter','D=(lambda_max−143.75)/281.25','4.1nm','Empirical optical size calibration, cited ACSNano2009,3(6),1518.'),('extinction','epsilon=(0.03389×D^2.53801)×10^5','1.22×10^5M^-1cm^-1','Same cited calibration.'),('concentration','C=Absorbance(A)/epsilon*b =0.136/[(1.22×10^5)(1cm)]','1.1×10^-6M','Raw symbolic order lacks parentheses; source substituted denominator establishes intended form.'),('moles','1.1×10^-6M×3.025×10^-3L','3.33×10^-9molQDs','Rounded source arithmetic retained.'),('particles','3.33mol×10^-9molQDs×6.023×10^23QDs/molQDs','2.00×10^15QDs','Printed extra mol token retained; do not silently normalize raw source expression.'),('total-volume','2.00×10^15QDs×3.61×10^-20cm³/QD','7.23×10^-5cm³','Spherical size-derived particle volume is an author calculation.'),('cells','7.23×10^-5cm³/(2.29×10^-22cm³/lattice)','3.16×10^17lattices','Lattice volume is a model input, not a measured current QD unit cell.'),('atoms','3.16×10^17lattices×4Seatoms/lattice','1.26×10^18Seatoms','Stoichiometric model.'),('selenium-moles','1.26×10^18Seatoms/(6.023×10^23atoms/mol)','2.10×10^-6molSe','Rounded source arithmetic.'),('conversion','(2.10×10^-6molSe(QD)/2.25×10^6molSe(DPPSe))×100','93%','Printed denominator exponent is+6; inconsistent with initial−6 and result. Keep raw expression; interpreted−6 is only an explicit suspected typographical correction.')]
for ident,expr,result,note in eqs:equations.append({'id':'S21-'+ident,'source_unit_id':uid,'raw_expression_transcribed':expr,'reported_result':result,'note':note,'status':'author_calculation','conflict_ids':['C6'] if ident=='conversion' else []})
fact(uid,'printed final denominator',2.25e6,'mol',raw='2.25×10^6molSe(DPPSe)',status='reported_conflicting_printed_value',qualifier='Do not use as true reagent quantity; contradicts initial2.25×10^-6 and93% result.')
fact(uid,'conversion if initial limiting amount used',100*2.10e-6/2.25e-6,'%',status='computed_from_reported',qualifier='Arithmetic reconciliation only:93.333…%, consistent with rounded93%; does not erase printed exponent error.')

# CIF scalars and loops: full raw tokens plus parsed central value/uncertainty when appropriate.
cif_units=[]
for i,s in enumerate(cif['scalars']):
 tag=s['tag'];token=s['token'];raw=token['value'];uid=unit('cif-'+tag.strip('_').replace('_','-'),'cif',None,f"{tag}; source lines{s['tag_line']}–{token['line_end']}",'cif_scalar','Original CIF scalar '+tag,'molecular species9 crystal',{'cif_inventory_pointer':f'/scalars/{i}','scalar':s})
 cif_units.append(uid)
 m=re.fullmatch(r'([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)(?:\((\d+)\))?',raw.strip())
 val=float(m.group(1)) if m else (None if raw.strip() in ['?','.'] else raw)
 status='not_reported' if raw.strip()=='?' else ('not_applicable' if raw.strip()=='.' else 'reported_refinement_model' if tag.startswith(('_refine','_cell','_symmetry','_chemical_formula')) else 'reported')
 unit_symbol=('angstrom' if tag.startswith('_cell_length_') or tag=='_diffrn_radiation_wavelength' else 'deg' if tag.startswith('_cell_angle_') or tag.endswith(('_theta_min','_theta_max')) else 'angstrom^3' if tag=='_cell_volume' else 'K' if tag in ['_cell_measurement_temperature','_diffrn_ambient_temperature'] else 'mm' if tag.startswith('_exptl_crystal_size_') else None)
 fid=fact(uid,tag,val,unit_symbol,raw=token['raw_token'],status=status,qualifier='Original molecular-crystal CIF. Unknown/missing tokens preserved. For quantities with null normalized unit, use the exact CIF tag semantics; no unsupported unit conversion.')
 if m and m.group(2):
  central=m.group(1).lower();base,exp=(central.split('e')+[0])[:2] if 'e' in central else (central,0)
  decimals=len(base.split('.')[1]) if '.' in base else 0
  facts[-1]['standard_uncertainty']=int(m.group(2))*10**(int(exp)-decimals)
for i,l in enumerate(cif['loops']):
 uid=unit('cif-loop-'+str(i+1),'cif',None,f"loop begins line{l['line_start']}; {l['tags'][0]}",'cif_loop',f"Complete {l['row_count']}-row CIF loop",'molecular species9 crystal',{'cif_inventory_pointer':f'/loops/{i}','loop':l})
 cif_units.append(uid)
 fact(uid,'complete source loop',{'tags':l['tags'],'rows':l['rows']},status='reported_refinement_model',qualifier='Lossless raw CIF loop; parentheses, symmetry labels, missing tokens, calculated-H flags and occupancies retained. No QD coordinate assignment.')
unit('cif-format-limitation','cif',None,'Out-of-block publication-reference prefix and data_krace01','source_format','Strict Gemmi rejects original because publication-reference field precedes data_krace01. Original preserved. Data-block-only in-memory parse verifies all scalar and loop tokens; this is not a repaired downloadable CIF.',payload=cif['parser'])

# Bibliography is preserved as printed. No external cited paper was downloaded/read in this extraction.
mainrefs=[('1a','Nozik, A.J. Annu.Rev.Phys.Chem.2001,52,193.'),('1b','Colvin,V.L.;Schlamp,M.C.;Alivisatos,A.P. Nature1996,370,354.'),('1c','Alivisatos,P. Nat.Biotechnol.2004,22(1),47.'),('2','Steckel,J.S.;Yen,B.K.H.;Oertel,D.C.;Bawendi,M.G. J.Am.Chem.Soc.2006,128(40),13032.'),('3','Peng,Z.A.;Peng,X. J.Am.Chem.Soc.2002,124(13),3343.'),('4','Murray,C.B.;Norris,D.J.;Bawendi,M.G. J.Am.Chem.Soc.1993,115(19),8706.'),('5','Qu,L.;Peng,A.;Peng,X. NanoLett.2001,1(6),333.'),('6','Joo,J.;Pietryga,J.M.;McGuire,J.A.;Jeon,S.-H.;Williams,D.J.;Wang,H.-S.;Klimov,V.I. J.Am.Chem.Soc.2009,131(30),10620.'),('7','Evans,C.M.;Guo,L.;Peterson,J.J.;Maccagnano-Zacher,S.;Krauss,T.D. NanoLett.2008,8(9),2896.'),('8','Liu,H.;Owen,J.S.;Alivisatos,A.P. J.Am.Chem.Soc.2007,129(2),305.'),('9','Driess,M.;Janoschek,R.;Pritzkow,H.;Rell,S.;Winkler,U. Angew.Chem.Int.Ed.Engl.1995,34(15),1614.'),('10','Brown,D.H.;Cross,R.J.;Keat,R.J. J.Chem.Soc.DaltonTrans.1980,6,871.'),('11','Dai,Q.;Wang,Y.;Li,X.;Zhang,Y.;Pelligrino,D.J.;Zhao,M.;Zou,B.;Seo,J.;Wang,Y.;Yu,W.W. ACSNano2009,3(6),1518.')]
for label,text in mainrefs:
 uid=unit('reference-main-'+label,'main',3,'References('+label+')','reference',text,status='citation_only')
 references.append({'id':'main-'+label,'source_unit_id':uid,'citation_as_printed':text,'externally_verified':False,'source_full_text_read':False,'note':'Source year1996 retained as printed; not externally corrected.' if label=='1b' else ''})
for label,text in [('1','J.Am.Chem.Soc.2006,128(40),13032–13033.'),('2','Synthesis1987,6,554–555.')]:
 uid=unit('reference-si-'+label,'si',21,'References('+label+')','reference',text,status='citation_only');references.append({'id':'si-'+label,'source_unit_id':uid,'citation_as_printed':text,'externally_verified':False,'source_full_text_read':False})
for label,text in [('g','Chemiker Zeitung1982,391–395.'),('h','Chem.Commun.2005,2692–2694.')]:
 uid=unit('reference-table-'+label,'main',1,'Table1 footnote'+label,'reference',text,status='citation_only');references.append({'id':'table-'+label,'source_unit_id':uid,'citation_as_printed':text,'externally_verified':False,'source_full_text_read':False})
references.append({'id':'cif-bibliography','source_unit_id':'evans2010-cif-publ-section-references','citation_as_printed':cif['scalars'][0]['token']['value'],'externally_verified':False,'source_full_text_read':False,'bibliographic_entries':5,'note':'Altomare/SIR97; BrukerSAINT; BrukerAPEX2; SheldrickSADABS; SheldrickActaCryst. Complete raw text in CIF scalar.'})

def sample(ident,label,kind,parents,source_ids,assets_list=None,limits=None):
 samples.append({'id':ident,'label':label,'kind':kind,'explicit_parent_ids':parents,'source_unit_ids':source_ids,'original_asset_ids':assets_list or [],'limits':limits or [],'distinct_physical_replicate_claimed':False})
for p in procedures:
 sample(p['id'],p['label'],p['category'],[],[p['source_unit_id']])
 samples[-1]['procedure_inheritance_source_unit_ids']=p['explicit_inheritance']
for label in 'ABC':sample('msc-'+label,'PbSe MSC from TOPSe source'+label,'variant',['pbse-msc-family'],[object_units['table-S7-composition'],object_units['figure-S5'],object_units['figure-1']],['figure-S5','figure-1'],['A/C from distillation, B independently prepared; no paper-assigned replicate count.'])
for label,ratio in [('A','2:1'),('B','1:1'),('C','1:2')]:sample('cd-ratio-'+label,'DPPSe:Cd oleate'+ratio,'observation',[],[object_units['figure-S8']],['figure-S8'],['Absolute reagent charges not provided.'])
sample('cd-timecourse','Cd1:2 mixture10min and24h','time_course',[],[object_units['figure-S10'],object_units['figure-S11']],['figure-S10','figure-S11'],['Same nominal stoichiometry as S8C; physical specimen identity to S8C not explicitly proven. S11 explicitly same sample as S10C/D.'])
samples[-1]['related_nominal_ratio_context_ids']=['cd-ratio-C']
sample('pb-ratio-1to1','DPPSe:Pb oleate1:1','observation',[],[object_units['figure-S9']],['figure-S9'],['Separate from Cd specimens.'])
sample('topse-dpp15','TOPSe plus15mol%DPP/Pb oleate','observation',[],[object_units['figure-2'],'evans2010-dpp-topse-main-shifts'],['figure-2'],['Absolute recipe charge/volume not supplied.'])
sample('species9-cif','Molecular species9 single crystal','crystallographic_model',['species9-crystallization'],['evans2010-species9-acquisition']+cif_units,['figure-S12','figure-S13'],['Not PbSe/CdSe QD coordinates; hydrogen positions include calculated riding model.'])
sample('pbse-tem-spheres','PbSe spherical TEM example','characterization',[],[object_units['figure-S16']],['figure-S16'],['Related DPPSe/Pb oleate synthesis family only; exact recipe/time link unreported.'])
sample('pbse-tem-cubes','PbSe cubic TEM example','characterization',[],[object_units['figure-S16']],['figure-S16'],['Related DPPSe/Pb oleate synthesis family only; not assert same batch as spheres or S15.'])
sample('pbse-yield-example','Representative1300nm PbSe optical yield sample','calculation',[],[object_units['calculation-S21-yield']],['calculation-S21-yield'],['2.25umolSe/3.025mL differs from S19; no exact recipe join.'])

for ident,name,formula,source_uid,scope in [
 ('cd-oleate','Cadmium(II) oleate','Cd(C18H33O2)2','evans2010-cd-oleate','prepared precursor'),('pb-oleate','Lead(II) oleate','Pb(C18H33O2)2','evans2010-pb-oleate','prepared precursor'),('topse','Trioctylphosphine selenide','SeP(C8H17)3','evans2010-topse','prepared/impure stock'),('dppse','Diphenylphosphine selenide','SePPh2H','evans2010-dppse','prepared secondary-phosphine selenide'),('tippse','Tri-isopropylphosphine selenide','SeP(C3H7)3','evans2010-tippse','prepared tertiary-phosphine selenide'),('tepse','Triethylphosphine selenide','SeP(C2H5)3','evans2010-tepse','prepared tertiary-phosphine selenide'),('tppse','Triphenylphosphine selenide','SeP(C6H5)3','evans2010-tppse','prepared tertiary-phosphine selenide'),('dop','Dioctylphosphine','HP(C8H17)2',object_units['figure-S1'],'identified impurity'),('dopo','Dioctylphosphine oxide','O=PH(C8H17)2',object_units['figure-S1'],'identified impurity'),('tbp','Tributylphosphine','P(C4H9)3',object_units['figure-S2'],'impurity-analysis context'),('dbp','Dibutylphosphine','HP(C4H9)2',object_units['figure-S2'],'identified impurity'),('dopse','Dioctylphosphine selenide','Se=PH(C8H17)2',object_units['figure-S3'],'identified impurity/reactive-species interpretation'),('pbse','Lead selenide','PbSe','evans2010-pbse-qd','QD product; MSCs distinct sample state'),('cdse','Cadmium selenide','CdSe','evans2010-cdse-qd','QD product; MSCs distinct sample state'),('pb-metal','Lead metal','Pb','evans2010-dpp-pb-control','observed mechanistic-control product'),('species9','Lead bis(diphenyldiselenophosphinate) species9','Pb(Se2PPh2)2','evans2010-species9-crystallization','isolated molecular crystal')]:
 materials.append({'id':ident,'name':name,'source_unit_id':source_uid,'formula_or_condensed_identity':formula,'scope':scope,'molecular_coordinates':'cif-source-inventory.json molecular9 only' if ident=='species9' else None,'identity_name_basis':'Normalized chemical name/condensed identity from source labels; does not imply additional structural measurement.'})
for row in tables[0]['rows']:
 materials.append({'id':'compound-'+str(row['source_label']),'name':row['name'],'source_unit_id':object_units['table-1'],'formula_or_condensed_identity':row['condensed_structure'],'scope':'Observed organic species; may duplicate a reagent identity across roles','molecular_coordinates':None})
for label,condensed in [(1,'oleate-Pb-Se-PPh2'),(6,'oleate-Pb(Se2PPh2)'),(10,'oleate-Pb-PPh2'),(11,'Ph2P-Pb-PPh2'),(14,'Ph2P-Se-Pb-Se-PPh2')]:
 materials.append({'id':'intermediate-'+str(label),'name':'Proposed intermediate'+str(label),'source_unit_id':object_units['scheme-S1'] if label==14 else object_units['scheme-2'] if label in [10,11] else object_units['scheme-1'],'formula_or_condensed_identity':condensed,'scope':'author-proposed, unisolated intermediate','molecular_coordinates':None,'identity_status':'author_interpretation'})
stocks=[
 {'id':'topse-neat','source_unit_id':'evans2010-topse','components':['TOP','Se'],'result':'TOPSe plus impurities','concentration':None,'preparation':'67mmolTOP+67mmolSe, N2 overnight','note':'Not assumed pure; several later distilled fractions differ.'},
 {'id':'topse-A','source_unit_id':'evans2010-topse-distillation','components':['TOPSe','TOP','DOP','unidentified P impurities'],'volume_mL':2,'collection_start_degC':185,'composition_table':'table-S7-composition A'},
 {'id':'topse-B','source_unit_id':'evans2010-topse-B-stock','components':['TOPSe','TOP','DOP','unidentified P impurities'],'concentration_mol_L':1.0,'solvent':'TOP','total_volume':None,'composition_table':'table-S7-composition B','conflicts':['C4']},
 {'id':'topse-C','source_unit_id':'evans2010-topse-distillation','components':['TOPSe','TOP','DOP','unidentified P impurities'],'volume_mL':4,'volume_approximate':True,'origin':'residue','composition_table':'table-S7-composition C'},
 {'id':'species9-dppse-stock','source_unit_id':'evans2010-species9-crystallization','solute':'DPPSe','solvent':'toluene','volume_uL':500,'concentration_mol_L':.1},
 {'id':'species9-pb-stock','source_unit_id':'evans2010-species9-crystallization','solute':'Pb(oleate)2','solvent':'toluene','volume_uL':100,'concentration_mol_L':.1},
 {'id':'pbse-pb-stock','source_unit_id':'evans2010-pbse-qd','solute':'Pb(oleate)2','solvent':None,'solvent_status':'not_explicitly_reported','volume_mL':2,'concentration_mol_L':.025,'amount_umol':50},
 {'id':'pbse-dppse-solution','source_unit_id':'evans2010-pbse-qd','solute':'DPPSe','amount_umol':10,'solvent':'anhydrous toluene','solvent_volume_mL':2,'oleic_acid_added_umol':40,'oleic_acid_added_uL':12.6},
 {'id':'cdse-cd-stock','source_unit_id':'evans2010-cdse-qd','solute':'Cd(oleate)2','solvent':'octadecene','volume_mL':1,'concentration_mol_L':.025,'amount_umol':25,'oleic_acid_umol':630},
 {'id':'cdse-dppse-stock','source_unit_id':'evans2010-cdse-qd','solute':'DPPSe','solvent':'octadecene','volume_mL':1,'concentration_mol_L':.025,'amount_umol':25,'oleic_acid_umol':630}
]

# Explicit missingness is data, rather than default values for training.
missingness=[{'scope':p['id'],'source_unit_id':p['source_unit_id'],'fields':p['missing']} for p in procedures]
missingness += [
 {'scope':'all-QD-products','fields':['No QD coordinate CIF supplied','No powderXRD/SAED/Raman supplied','No exact atomistic QD structure, ligand coverage or dopant positions','No raw optical spectra or NMR FID files','No fitted kinetic rate constants or quantitative exchange equilibrium']},
 {'scope':'species9','fields':['No numeric isolated yield despite high-yield wording','No complete physical-crystal identifier beyond molecular formula/label9 and CIFkrace01','Original CIF nonstandard prefix needs transparent future delivery handling']},
 {'scope':'observations','fields':['All nonassigned NMR peaks remain nonassigned','Source quantities/conditions do not establish synthesis success probability or independent replicate counts','Curve digitization and image-derived particle sizing are not supplied measurements and were not invented']}
]
conflicts=list(initial['source_conflicts'])
conflicts += [{'id':'C8','locator':'SI S15 crystallographic paragraph vs CIF diffraction tags','printed_values':'SI χ range1.89–36.32°, CIF theta range1.89–36.32°','issue':'Preserve differing printed angle symbols; do not assign this range to an independent chi scan.'},{'id':'C9','locator':'Original CIF beginning','printed_values':'_publ_section_references precedes data_krace01','issue':'Strict original-file parser rejects prefix; all original data retained and data block alone crosschecked in memory. No repaired file silently substituted.'}]

# Full private native-text payloads bind all body/footnotes/references, including non-scientific metadata.
page_payloads=[]
for idx,d in enumerate(prep['documents'][:2]):
 role=['main','si'][idx]
 for p in d['text_pages']:
  pp=p['pdf_page'];content=Path(p['path']).read_text('utf-8')
  mapped=[u['id'] for u in units if u['source_role']==role and u['pdf_page']==pp]
  assert mapped,(role,pp)
  page_payloads.append({'id':f'{role}-{pp:02}','source_role':role,'pdf_page':pp,'source_sha256':d['sha256'],'text_path':p['path'],'text_sha256':p['sha256'],'complete_native_extracted_text':content,'scientific_unit_ids':mapped,'embedded_graphics_policy':'All original page pixels retained separately; every scientific figure/table/scheme extracted as a selected original crop. Numeric printed figure annotations separately transcribed; no raw trace digitization.','source_download_watermark':'Retained only as part of private source payload; never experiment/provenance time.'})
write('complete-source-payloads.json',{'schema':'mattersyn-private-complete-source-payloads/1','source_id':'evans2010','pages':page_payloads,'public_projection':'Do not publish full-paper text/page-render equivalents; use selected original evidence crops and curated facts only.','cif_payload':'cif-source-inventory.json','cif_payload_sha256':sha(B/'cif-source-inventory.json')})
write('source-facts.json',{'schema':'mattersyn-source-facts/1','source_id':'evans2010','source_sha256':docs['main']['sha256'],'si_sha256':docs['si']['sha256'],'cif_sha256':docs['cif']['sha256'],'author':'/root/norberg2004_extract','created_at':now,'scope':'All supplied source recipes, controls, acquisitions, printed quantitative results and categorical observations; CIF scalars/loops retained losslessly. Author-derived/cited/model/missing/conflicting values remain distinct. All admission false pending independent audit/canonical task gates.','facts':facts})
inventory={'schema':'mattersyn-source-inventory/1','source_id':'evans2010','doi':'10.1021/ja103805s','title':pair['title'],'year':2010,'author':'/root/norberg2004_extract','created_at':now,'authoring_status':'complete_supplied_source_extraction_pending_independent_scientific_audit','source_documents':docs,'pairing_status':'author content pairing complete, independent audit pending','units':units,'materials':materials,'procedures':procedures,'stocks':stocks,'sample_lineage':samples,'tables':tables,'equations':equations,'references':references,'source_conflicts':conflicts,'missingness':missingness,'original_assets':assets['assets'],'counts':{'source_documents':3,'main_pages':3,'si_pages':21,'scientific_units_including_cif_units':len(units),'typed_facts':len(facts),'procedure_families_not_independent_paper_count':len(procedures),'material_role_entries':len(materials),'stock_contexts':len(stocks),'sample_contexts':len(samples),'figure_table_scheme_objects':23,'additional_composition_table_and_yield_calculation':2,'selected_assets':25,'typed_tables':len(tables),'worked_calculation_equations':len(equations),'main_numbered_references':11,'main_bibliographic_subentries':13,'si_numbered_references':2,'table_footnote_citations':2,'CIF_bibliography_entries':5,'CIF_scalars':99,'CIF_loops':7,'CIF_loop_rows':sum(x['row_count'] for x in cif['loops']),'CIF_loop_cells':cif['total_loop_cells']},'disposition':'Retain recipe-rich source with PbSe/CdSe routes, precursor/control chemistry and species9 molecular structure; do not turn every observation/model into a synthesis or every data row into a replicate.','full_payload_file':'complete-source-payloads.json','full_payload_sha256':sha(B/'complete-source-payloads.json'),'earlier_checkpoint':'checkpoints/pairing-inventory-v1','independent_scientific_audit':'pending','canonical_review':'not_started','publication_status':'not_published','eligible_training':False}
write('source-inventory.json',inventory)
coverage=read(B/'checkpoints/pairing-inventory-v1/page-coverage.json')
coverage.update(status='complete_author_source_extraction_pending_independent_scientific_audit',created_at=now,cif_structured_loop_inventory_complete=True)
for p in coverage['pages']:
 p['typed_extraction_complete']=True;p['high_resolution_selected_crops']=[a['id'] for a in assets['assets'] if a['source_role']==p['source_role'] and a['pdf_page']==p['pdf_page']]
 p['source_unit_ids']=[u['id'] for u in units if u['source_role']==p['source_role'] and u['pdf_page']==p['pdf_page']]
 if p['source_role']=='si' and p['pdf_page']==20:p['coverage_notes']=p['coverage_notes'].replace('5nm and20nm','5nm and50nm')
coverage['author_corrections_since_first_reading']=[{'field':'SI S20 rightTEM scale bar','earlier_checkpoint':'20nm','final_extraction':'50nm','reason':'High-resolution original FigureS16 crop clearly prints50nm. Initial checkpoint remains immutable. This is an author reading correction, not a source conflict.'}]
write('page-coverage.json',coverage)
notes=f'''# Evans, Evans and Krauss (2010) — source extraction

The supplied three-page article,21-page SI and molecular-crystal CIF were read completely. All24 original PDF pages and the selected original evidence images were visually inspected. Original files and the first reading checkpoint are preserved.

This author package contains {len(units)} scientific/source units, {len(facts)} typed facts, {len(procedures)} procedure families, {len(stocks)} stock contexts and {len(samples)} sample/observation contexts. These are not independent papers or replicate counts. The seven starting-material preparations, tertiary negative/rescue controls, A/B/C impurity family, thermal Pb/Cd controls, molecular9 crystallization and distinct PbSe/CdSe QD recipes remain separate. NMR ratio/time series and the optical yield calculation do not create extra complete recipes.

All23 figure/table/scheme objects, the inline composition table and the complete worked yield calculation have readable original crops. Table1’s eight compounds, all reported recipe quantities, NMR time-series integrals and printed spectral annotations are retained. Unassigned peaks stay unassigned; plotted curves are not fabricated raw numerical traces.

The CIF contains99 scalars and7 loops:5 scattering entries,2 symmetry operations,51 atom sites,31 anisotropy rows,59 bond rows,102 angle rows and98 torsions. Every scalar and loop cell was crosschecked against a separate Gemmi parse of the data block. The original file is not strictly parseable because its reference field precedes the data block; original bytes and the out-of-block field are preserved. The model belongs exclusively to molecular species9, C24H20P2PbSe4; it is not a PbSe/CdSe QD structure pair. Calculated riding hydrogen positions retain their source flags.

Printed TIPPSe and Pb-oleate mass/amount inconsistencies, mixed Cd/Pb narrative, B-stock wording, molecular9 ratio threshold, missing SI citation4, angle-symbol difference and final yield exponent are explicit. The93% conversion is an optical calculation, not isolated mass yield. Its sample charge and volume differ from the S19 PbSe recipe, so no unsupported exact specimen join is made. TEM bars are5nm left and50nm right; the latter corrects20nm in the preserved early reading checkpoint. Image scale is not particle diameter, and particle packing is not atomic phase.

Independent scientific audit is pending. No canonical records, structural training admission, public reader or publication are approved here. Next: a different reviewer checks the full exact source package and selected crops, then canonical/reader/visual stages can proceed through their separate gates.
'''
(B/'extraction-notes.md').write_text(notes,encoding='utf-8')
print(json.dumps(inventory['counts'],indent=2))
