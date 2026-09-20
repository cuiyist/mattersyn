"""Build private source extraction only; shared files and original PDFs are read-only."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
import copy,hashlib,json,re
import pypdfium2
from PIL import Image,ImageDraw,ImageOps
import source_author_data as A
P=Path(__file__).resolve().parent;SID='matuhina2023';DOI='10.1021/acsanm.2c04342';AUTHOR='/root/backlog_eta';NOW=datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def wr(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
intake=json.loads((P/'intake-identity.json').read_bytes());prep=json.loads((P/'source-preparation.json').read_bytes())
docs={d['role']:d for d in prep['documents']}
for c in intake['file_copies']:assert sha(c['source_path'])==c['sha256']
def ev(d,p,l):return {'source_id':SID+'-'+d,'document_role':d,'source_sha256':docs[d]['sha256'],'pdf_page':p,'printed_page':952+p if d=='main' else 'S'+str(p),'locator':l}
def q(raw,unit,meaning,d,p,l,flags=()):
 s=str(raw);t=s.replace('−','-').replace('–','-');v=unc=ran=comp=parts=None;ap=t.startswith('~');st='reported'
 if ap:t=t[1:]
 m=re.match(r'^(>=|<=|>|<)',t)
 if m:comp=m[1];t=t[len(comp):]
 n=r'[+-]?\d+(?:\.\d+)?';pm=re.fullmatch('('+n+')±('+n+')',t)
 esd=re.fullmatch('('+n+r')\((\d+)\)',t);rng=re.fullmatch('('+n+')-('+n+')',t)
 if pm:v=float(pm[1]);unc=float(pm[2])
 elif esd:v=float(esd[1]);unc=float(Decimal(esd[2])*Decimal(10)**(-len(esd[1].split('.')[1]) if '.' in esd[1] else 0))
 elif re.fullmatch(n,t):v=float(t)
 elif rng:ran={'min':float(rng[1]),'max':float(rng[2])}
 elif unit in ['ratio_parts','grid_dimensions'] and re.fullmatch(n+'(?::'+n+')+',t):parts=[float(z)for z in t.split(':')];st='reported_ratio_parts'
 elif t in ['','-']:st='not_reported'
 else:st='reported_text'
 return {'raw_text':s,'value':v,'unit':unit,'uncertainty':unc,'uncertainty_definition':'as printed; statistical definition unspecified'if unc is not None else None,'range':ran,'comparison':comp,'approximate':ap,'components':parts,'status':st,'meaning':meaning,'evidence':[ev(d,p,l)],'conflict_ids':[z for z in flags if z.startswith('C')],'gap_ids':[z for z in flags if z.startswith('G')]}
facts=[]
for i,d,p,l,title,claim,scope,qs,flags,kind in A.FACTS:
 facts.append({'id':SID+'-'+i,'title':title,'claim':claim,'sample_scope':scope,'claim_class':kind,'evidence':[ev(d,p,l)],'quantities':[q(raw,u,n,d,p,l,flags)for n,raw,u in qs],'conflict_ids':[z for z in flags if z.startswith('C')],'gap_ids':[z for z in flags if z.startswith('G')],'independent_audit_status':'pending'})
fb={x['id'].removeprefix(SID+'-'):x for x in facts}
for fid,d,p,l in [('phase','main',4,'Rhombohedral structure and Figure2'),('phase-hypothesis','main',4,'Cited bulk conversion paragraph'),('tem-histograms','main',4,'Figure3d'),('phase-stability','main',9,'Cubic aging paragraph'),('ltpl','main',9,'Figure7 caption'),('binding-energy','main',9,'Figure7b fit inset'),('trpl','si',10,'TableS6'),('ta-acquisition','main',7,'Figure6 caption')]:fb[fid]['evidence'].append(ev(d,p,l))
fb['tem-histograms']['quantities'][-1]['evidence']=[ev('main',4,'Figure3d histogram annotation')]
for qq in fb['binding-energy']['quantities'][2:]:qq['evidence']=[ev('main',9,'Figure7b fit inset')]
for qq in fb['phase-hypothesis']['quantities']:qq['evidence']=[ev('main',4,'Cited bulk transformation, reference24')]
fb['ltpl-width']['conflict_ids']=['C13']
for j in [3,4]:fb['literature-optical-context']['quantities'][j]['evidence']=[ev('main',2,'Introduction first line, reference8')]
fb['literature-optical-context']['quantities'][5]['evidence']=[ev('main',5,'Prior benzoyl-chloride synthesis comparison, reference8')]
for j in [6,7]:fb['literature-optical-context']['quantities'][j]['evidence']=[ev('main',9,'Prior stability comparison, reference8')]
fb['literature-optical-context']['evidence'] += [ev('main',2,'Introduction continuation'),ev('main',5,'Cited QY comparison'),ev('main',9,'Cited stability comparison')]

samplemap={'NCs@150':'nc150','150@NCs':'nc150','NCs@200':'nc200','NCs@180//0.7':'nc180-07','180@NCs//0.7':'nc180-07','NCs@180//0.5':'nc180-05','180@NCs//0.5':'nc180-05','NCs@180//0.35':'nc180-035','temperature150':'nc150','temperature180':'nc180-07','temperature200':'nc200','ratio0.7':'nc180-07','ratio0.5':'nc180-05','ratio0.35':'nc180-035'}
tables=[]
for tid,d,p,title,cols,units,txt in A.TABLES:
 rows=[]
 for ir,line in enumerate(txt.splitlines(),1):
  vals=line.split('|');assert len(vals)==len(cols);rp=7 if tid=='table-s2'and ir>=9 else p
  sample=samplemap.get(vals[0],'nc180-05'if tid in ['table-s5','table-s6']else vals[0]);cells=[]
  for ic,(col,un,raw)in enumerate(zip(cols,units,vals)):
   flags=['C7']if tid in ['table-s1','table-s2']else['C6','C8']if tid=='table-s6'else['C10']if tid=='table-s5'else[]
   cell={'id':f'{tid}-r{ir:02}-{col}','column':col,**q(raw,un,col,d,rp,f'{tid} row {ir}, {col}',flags)}
   if tid=='table-s2'and col=='sample':cell['source_cell_kind']='repeated_group_heading';cell['is_printed_body_cell']=False
   else:cell['source_cell_kind']='body';cell['is_printed_body_cell']=True
   if tid=='table-s5'and vals[0]=='Delta/B'and col=='wavenumber':cell['unit']='dimensionless';cell['printed_column_unit']='cm^-1';cell['unit_interpretation']='ratio Delta/B; common column heading retained separately'
   if tid=='table-s4'and col=='sample':cell['raw_text']=raw.removeprefix('temperature').removeprefix('ratio');cell['meaning']='injection temperature'if raw.startswith('temperature')else'Mn:Cs loading ratio';cell['unit']='degC'if raw.startswith('temperature')else'ratio';cell['value']=float(cell['raw_text']);cell['status']='reported';cell['group_header']='Injection temperature, °C'if raw.startswith('temperature')else'Mn:Cs ratio'
   cells.append(cell)
  rows.append({'id':f'{tid}-row-{ir:02}','row_label':vals[0],'sample_id':sample,'source_raw_row':line,'evidence':[ev(d,rp,f'{tid} row {ir}')],'cells':cells})
 notes=[];foot=[]
 if tid=='table-s1':notes=['Superscripts a/b on Rwp/chi-squared have no corresponding explanatory footnote on supplied page. Cell angles and parameter uncertainties are absent. No geometry model is validated.']
 if tid=='table-s2':notes=['Four sample blocks only; no NCs@200 atomic block. The source block label NCs@180//0.5 occurs at the end of S6 and its rows continue on S7.','All zero occupancies, Wyckoff labels, repeated position/B values and exchanged Cl labels retained literally. B header is B/10^4 pm^2; no conversion or ADP-model validation implied.','Repeated sample fields are grouping metadata rather than new printed body cells.']
 if tid=='table-s6':foot=[{'id':'table-s6-footnote','text':'Bi-exponential function was used to fit the TRPL decays. The source identifies tau1,A1 as non-radiative and tau2,A2 as radiative components and prints tau_avg = sum Ai*taui. All are source assignments; the numerical averaging discrepancy remains C8.','evidence':[ev('si',10,'TableS6 complete footnote')]}]
 if tid=='table-1':notes=['The two A3/tau3 cells in the cubic row are blank, not zero. Fitted decay parameters are not reaction times.']
 tables.append({'id':tid,'title':title,'columns':cols,'column_units':units,'rows':rows,'evidence':[ev(d,p,tid)]+([ev('si',7,'TableS2 continuation')]if tid=='table-s2'else[]),'notes':notes,'footnotes':foot,'independent_numerical_audit':'pending'})
wr('source-tables.json',{'schema':'mattersyn-source-tables/1','source_id':SID,'author':AUTHOR,'tables':tables,'independent_audit_status':'pending'})

material_specs=[
('cs-carbonate','Cesium carbonate','Cs2CO3','precursor','Sigma-Aldrich99.9%; Cs-oleate feed',2),('ode','Octadecene (ODE)','ODE','solvent','Source90%; exact positional/isomer distribution not given; dry in preparation.',2),('oa','Oleic acid','C18H34O2','ligand_precursor','Source90%; dry; no source-specific isomer assay or surface coverage.',2),('olam','Oleylamine','C18H37N','ligand','Technical70%; no batch-specific composition/surface binding model.',2),('mncl2','Anhydrous manganese(II) chloride','MnCl2','precursor','99%; weighing in inert atmosphere.',2),('argon','Argon','Ar','atmosphere','Inert handling/heating; flow rate/grade unknown.',2),('hexane','Hexane','C6H14','dispersion_solvent','>=95%; primary redispersion volume absent.',2),('meoac','Anhydrous methyl acetate','C3H6O2','antisolvent','>=98% supplied, conventionally distilled; alternative purification.',2),('ipa','Anhydrous isopropanol','C3H8O','antisolvent','Alternative trial; no visible PL of precipitate.',2),('etoac','Anhydrous ethyl acetate','C4H8O2','antisolvent','Separate alternative trial; no visible PL of precipitate.',2),('quench-water','Ice-water bath','H2O','thermal_medium','External quench medium; not injected reaction solvent.',2),('hno3','Nitric acid','HNO3','analytical_reagent','Concentrated acid dissolves NC precipitate;2% matrix concentration basis not supplied.',3),('milliq','Milli-Q dilution water','H2O','analytical_solvent','18.2 Mohm cm; not reaction/quench water.',3),('cs-standard','Cs ionic calibration standard',None,'measurement_reference','0.001–1000 ug/L in2% HNO3; counterion/speciation not specified.',3),('mn-standard','Mn ionic calibration standard',None,'measurement_reference','0.001–1000 ug/L in2% HNO3; counterion/speciation not specified.',3),('heavy-water','Heavy-water continuum generator','D2O','instrument_medium','TA white-light generator, not NC dispersion solvent.',3),('cover-glass','Microscopy cover glass',None,'support','Precleaned20×20mm XRD substrate; no thickness or cleaning recipe.',2),('cu-grid','Carbon-coated copper grid',None,'support','TEM/SAED substrate; no mesh specified.',2),('quartz-cuvette','Quartz cuvette',None,'support','2mm thickness for TA; no atomistic substrate model.',3),('silica-substrate','Silica substrate',None,'support','Low-temperature PL deposition substrate; no deposition recipe.',3),('lsc-glass','LSC glass plate',None,'support','Deposited unencapsulated NC film; edge~2×0.15cm.',3),('si-photodiode','Silicon pn-junction photodiode','Si','device_component','2×2cm2; doping/contact details not supplied.',3),('nc-series','CsMnCl3 nanocrystal sample family','CsMnCl3','sample_family','Five named preparation conditions; cubic/rhombohedral and separate film/dispersion contexts.',3),('cs-oleate-identity','Cs-oleate solution identity',None,'stock_identity','Source calls precursor Cs-oleate; unknown final concentration/speciation, not an invented molecular aggregate.',2),('manganese-oleate-context','Mn(oleate)2 in reaction schematic',None,'schematic_product','Figure1 idealized reaction equation only; no isolated compound/product analysis.',3),('cscl-aged','CsCl assigned in aged cubic refinement','CsCl','degradation_phase','FigureS8 author-refined phase; not purchased reagent.',9),('cs3mncl5-aged','Cs3MnCl5 assigned in aged cubic refinement','Cs3MnCl5','degradation_phase','FigureS8 author-refined phase; not a separate synthesis route.',9),('csmn4cl9-aged','CsMn4Cl9 assigned in aged cubic refinement','CsMn4Cl9','degradation_phase','FigureS8 author-refined phase; not a separate synthesis route.',9)]
materials=[{'id':i,'name':n,'source_formula_or_abbreviation':form,'role':role,'scope_note':note,'evidence':[ev('main',p,'Material/method/result context')]}for i,n,form,role,note,p in material_specs]
for m in materials:
 if m['id'].endswith('-aged'):m['evidence']=[ev('si',13,'FigureS8 native inset phase labels')]
def qs(fs,meanings=None):
 vals=[copy.deepcopy(z)for fid in fs for z in fb[fid]['quantities']]
 return vals if meanings is None else[z for z in vals if z['meaning']in meanings]
stocks=[]
for i,name,comp,fs,scope,note in [
('cs-oleate-stock','Cesium oleate precursor solution',['cs-carbonate','ode','oa'],['cs-charge','cs-oa'],'all-five','407mg Cs2CO3,18mL ODE,1.74mL OA are whole preparation charges;2/3/4mL injections are aliquots, not each total stock.'),
('mn-precursor','MnCl2/OA/OlAm precursor in ODE',['mncl2','ode','oa','olam'],['mn-charge'],'all-five','Shared formulation reused for separate temperature/loading variants.'),
('icp-matrix','Diluted ICP acid matrix',['hno3','milliq'],['icp'],'icp-analysis','2% HNO3 basis unspecified; resistivity is water grade, not concentration.'),
('cs-calibration','Cs ionic calibration series',['cs-standard','hno3','milliq'],['icp'],'icp-calibration','Concentration series, not a single physical mixture; salt counterion unknown.'),
('mn-calibration','Mn ionic calibration series',['mn-standard','hno3','milliq'],['icp'],'icp-calibration','Concentration series, separate from Cs series; do not pool by default.')]:
 quantities=qs(fs)
 if i=='cs-oleate-stock':quantities=[z for z in quantities if z['meaning']in['Cs2CO3 mass','ODE charge','dry OA charge']]
 if i=='mn-precursor':quantities=[z for z in quantities if z['meaning']!='flask capacity']
 if i=='icp-matrix':quantities=[z for z in quantities if z['meaning']=='HNO3 matrix concentration']
 stocks.append({'id':i,'name':name,'components':comp,'source_fact_ids':[SID+'-'+f for f in fs],'quantities':quantities,'sample_scope':scope,'notes':note,'evidence':[e for f in fs for e in fb[f]['evidence']]})

# Operations carry only their stage-applicable numerical fields; context facts retain all source quantities.
specs=[
('cs-oleate-preparation','Cs-oleate stock preparation','precursor_procedure',['cs-oleate-stock'],[
('cs-load','Load Cs2CO3 and ODE',['cs-carbonate','ode'],['cs-charge'],['cs-charge'],None,None),
('cs-degas','Degas initial mixture',['cs-charge'],['cs-degassed'],['cs-degas'],None,None),
('cs-add-oa','Add dry OA under Ar and complete transparent dissolution',['cs-degassed','oa','argon'],['cs-oleate-stock'],['cs-oa'],None,None),
('cs-store','Cool to room temperature and store under vacuum',['cs-oleate-stock'],['stored-cs-stock'],['cs-store'],[],None),
('cs-reactivate','Degas and heat stock before injection',['stored-cs-stock','argon'],['hot-cs-stock'],['cs-store'],None,None)]),
('hot-injection-series','Five source-defined CsMnCl3 conditions','synthesis',['nc150','nc180-07','nc180-05','nc180-035','nc200'],[
('mn-load','Charge manganese salt, dry solvent and ligands under inert atmosphere',['mncl2','ode','oa','olam'],['mn-precursor'],['mn-charge'],None,None),
('mn-degas','Heat and degas Mn precursor under vacuum',['mn-precursor'],['conditioned-mn'],['mn-degas'],None,None),
('nc-inject','Heat under Ar and swiftly inject the variant-specific Cs-oleate aliquot',['conditioned-mn','hot-cs-stock','argon'],['nc-reaction-series'],['inject','variant-map'],None,None),
('nc-grow-quench','Hold5s then quench in external ice-water bath',['nc-reaction-series','quench-water'],['nc-crude-series'],['quench'],None,'nc-crude-series')]),
('primary-isolation','Primary NC isolation','workup',['five-series separately'],[
('nc-centrifuge','Centrifuge crude solution without antisolvent',['nc-crude-series'],['nc-precipitate-series','discarded-supernatants'],['isolate'],None,'nc-precipitate-series'),
('nc-dry','Discard supernatant and vacuum-desiccate retained precipitate',['nc-precipitate-series'],['dried-nc-series'],['dry-redisperse'],None,'dried-nc-series'),
('nc-redisperse','Redisperse retained dry NCs in hexane',['dried-nc-series','hexane'],['nc-dispersion-series'],['dry-redisperse'],[],'nc-dispersion-series')]),
('purification-trials','Separate purification trials','control_procedure',['hexane-only-trial','ipa-trial','etoac-trial','meoac-trial'],[
('hexane-spin','Test centrifugation of prepurified NCs in hexane',['nc-precipitate-series','hexane'],['no-visible-pellet'],['centrifuge-trial'],None,None),
('ipa-or-etoac','Split crude into separate portions and precipitate with one of two antisolvents',['nc-crude-series','ipa','etoac'],['ipa-nonemissive-precipitate','etoac-nonemissive-precipitate'],['antisolvent-trial'],None,None),
('meoac-spin','Add MeOAc to prepurified suspension and centrifuge',['nc-dispersion-series','meoac'],['meoac-precipitate'],['meoac-trial'],None,'meoac-precipitate')]),
('unisolated-control','Unisolated degradation observation','control_observation',['unisolated-control'],[
('leave-crude','Leave unisolated NCs in ODE in air',['nc-crude-series'],['black-degraded-crude'],['unisolated'],None,None)]),
('xrd-procedure','XRD specimen preparation and analysis','characterization',['five-series separately'],[
('xrd-deposit','Drop-cast separate dispersions onto covers',['nc-dispersion-series','cover-glass'],['xrd-films'],['xrd-prep'],None,'xrd-films'),
('xrd-acquire','Acquire powder XRD in ambient conditions',['xrd-films'],['xrd-data'],['xrd-acquire','xrd-ambient'],None,None),
('xrd-refine','Refine diffraction and draw source crystal illustrations',['xrd-data'],['reported-refinement-data'],['xrd-acquire'],[],None)]),
('tem-procedure','TEM and SAED preparation and acquisition','characterization',['five-series separately'],[
('tem-deposit','Adjust optical density and drop dispersion on carbon-coated Cu grid',['nc-dispersion-series','hexane','cu-grid'],['tem-specimens'],['tem'],['deposition aliquot','absorbance at 280 nm','absorbance wavelength'],'tem-specimens'),
('tem-acquire','Acquire TEM and SAED from source-labeled specimens',['tem-specimens'],['tem-saed-data'],['tem'],['accelerating voltage'],None)]),
('optical-procedure','Solution absorption/PL/QY/TRPL','characterization',['source-scoped optical dispersions'],[
('optical-acquire','Measure absorption and PL/QY/decays with corresponding instruments',['nc-dispersion-series'],['optical-data'],['optical-acquisition'],None,None),
('trpl-fit','Fit optimized-sample decay curves and retain literal averaging expression',['optical-data'],['trpl-fits'],['trpl'],[],None)]),
('ta-procedure','Transient absorption','characterization',['nc150','nc180-07','nc180-05'],[
('ta-load','Place dispersion in quartz cuvette',['nc-dispersion-series','quartz-cuvette'],['ta-specimens'],['ta-acquisition'],['cuvette thickness'],None),
('ta-acquire','Acquire source-specific pump/probe spectra and decay series',['ta-specimens','heavy-water'],['ta-data'],['ta-acquisition','ta-power','ta-below-gap'],['laser excitation wavelength','time resolution','excitation power','cubic probe wavelength','rhombohedral probe wavelength','probe wavelength','excitation1','excitation2','excitation3'],None),
('ta-fit','Fit cubic bi-exponential and rhombohedral tri-exponential decays',['ta-data'],['ta-fits'],['ta-components'],[],None)]),
('icp-procedure','ICP-MS preparation and composition measurement','characterization',['five-series separately'],[
('icp-dissolve','Dissolve purified precipitate in concentrated nitric acid',['nc-precipitate-series','hno3'],['icp-digests'],['icp'],[],None),
('icp-dilute','Dilute into2% HNO3 matrix',['icp-digests','icp-matrix'],['icp-solutions'],['icp'],['HNO3 matrix concentration','Milli-Q water resistivity'],None),
('icp-calibrate-measure','Calibrate with ionic standards and measure Mn:Cs',['icp-solutions','cs-calibration','mn-calibration'],['icp-results'],['icp'],['ionic standard concentration interval','HNO3 matrix concentration'],None)]),
('ltpl-procedure','Deposited-film low-temperature PL','characterization',['ltpl-nc180-05'],[
('ltpl-deposit','Deposit NCs on silica',['nc-dispersion-series','silica-substrate'],['ltpl-film'],['ltpl'],[],'ltpl-film'),
('ltpl-acquire','Cool to30K then warm through measured PL sequence',['ltpl-film'],['ltpl-data'],['ltpl'],None,None),
('ltpl-fit','Fit thermal-quenching model over stated interval',['ltpl-data'],['binding-energy-fit'],['binding-energy'],['fit temperature interval'],None)]),
('stability-procedure','Separate film and dispersion aging','stability_observation',['rhombohedral-film','cubic-film','rhombohedral-dispersion'],[
('age-specimens','Store separate films/dispersions in the dark in ambient conditions',['xrd-films','nc-dispersion-series'],['aged-specimen-set'],['stability-storage'],None,None),
('stability-measure','Follow film XRD, dispersion PL and aged-specimen TEM in their own contexts',['aged-specimen-set'],['stability-data'],['phase-stability','pl-stability','aged-tem'],['rhombohedral structural observation','cubic aging time','first observation time','second time','third time'],None)]),
('dft-procedure','Source structural/electronic modeling','computational',['dft-cubic','dft-rhombohedral'],[
('dft-calculate','Select magnetic states and calculate electronic structures',['reported-refinement-data'],['dft-results'],['dft-method','dft-exchange'],None,None)]),
('lsc-procedure','Photocurrent proof-of-concept','device_procedure',['lsc-fresh','lsc-aged','lsc-bare','lsc-dark'],[
('lsc-deposit','Deposit an unencapsulated NC film on glass',['nc-dispersion-series','lsc-glass'],['lsc-film'],['lsc-setup'],[],'lsc-film'),
('lsc-assemble','Place film-coated glass edge on diode with opaque surrounding cover and dark box',['lsc-film','lsc-glass','si-photodiode'],['lsc-assembly'],['lsc-setup'],['window edge length','window edge thickness','photodiode side 1','photodiode side 2'],None),
('lsc-measure','Measure bias-dependent current under scoped lighting/control conditions',['lsc-assembly'],['lsc-curves'],['lsc-setup'],['beam spectrum','spot diameter','beam power','applied bias interval'],None),
('lsc-age-remeasure','Remeasure the same film after11 weeks in air',['lsc-film'],['aged-lsc-curves'],['lsc-result'],['film aging time'],None)])]
protocols=[]
for i,title,kind,samples,ops in specs:
 oo=[]
 for oi,action,ins,outs,fs,keep,retained in ops:
  oo.append({'id':oi,'action':action,'inputs':ins,'outputs':outs,'retained_fraction':retained,'source_fact_ids':[SID+'-'+f for f in fs],'context_fact_ids':[SID+'-'+f for f in fs],'quantities':qs(fs,keep),'evidence':[e for f in fs for e in fb[f]['evidence']],'quantity_scope_note':'Only source-scoped action conditions are listed. Alternative preparation/measurement series are separate specimens, never a pooled charge.','missing_fields':['See source missingness G1-G6; no unreported settings inferred.']})
 protocols.append({'id':i,'title':title,'kind':kind,'sample_ids':samples,'operations':oo,'specimen_application':'Separate alternative specimens/conditions unless a same-specimen link is explicitly stated; ICP digestion is destructive.','independent_audit_status':'pending','exact_protocol_eligibility':False})
next(o for pr in protocols for o in pr['operations']if o['id']=='ipa-or-etoac')['alternative_inputs']=[['nc-crude-series','ipa'],['nc-crude-series','etoac']]
next(o for pr in protocols for o in pr['operations']if o['id']=='ta-acquire')['condition_scope_note']='300nm/80uW and445/550nm probes belong Figure6. FigureS6 uses nc180-07 only,300/370/420nm excitation and600nm probe. They are separate acquisition conditions.'

variants=[]
for i,label,temp,ratio,vol,phase in [('nc150','150@NCs',150,.7,2,'cubic'),('nc180-07','180@NCs//0.7',180,.7,2,'rhombohedral'),('nc180-05','180@NCs//0.5',180,.5,3,'rhombohedral'),('nc180-035','180@NCs//0.35',180,.35,4,'rhombohedral'),('nc200','200@NCs',200,.7,2,'rhombohedral')]:
 variants.append({'id':i,'name':label,'kind':'source_preparation_condition','injection_temperature':q(temp,'degC','injection temperature','main',3,'Results sample-label definition'),'reported_loading_Mn_Cs':q(ratio,'ratio','source-defined loading ratio','main',3,'Results sample-label definition'),'cs_oleate_aliquot':q(vol,'mL','corresponding aliquot','main',2,'Synthesis injection mapping'),'reported_phase':phase,'phase_scope_note':'Source assignment, model validation separate.','independent_batch_count':None,'evidence':[ev('main',3,'Results sample definitions'),ev('main',4,'Figure2 sample profiles')]})
contexts=variants[:]
for i,name,kind,parents,d,p,l in [
('cs-oleate-stock','Cs-oleate stock','stock',[], 'main',2,'Preparation of Cs-oleate'),('below150','Unspecified below150°C trials','unsuccessful_condition',[],'main',3,'No NC formation below150°C'),('unisolated-control','Unpurified NCs in ODE','control',[],'si',3,'FigureS1d'),('hexane-only-trial','Hexane-only centrifugation trial','control',[],'main',2,'Purification'),('ipa-trial','Isopropanol purification trial','control',[],'main',2,'Purification'),('etoac-trial','Ethyl acetate purification trial','control',[],'main',2,'Purification'),('meoac-trial','MeOAc purification trial','control',[],'main',2,'Purification'),('ltpl-nc180-05','Optimized deposited-film LTPL','measurement',['nc180-05'],'main',8,'LTPL discussion'),('nc180-05-trpl','Optimized dispersion decay fits','measurement',['nc180-05'],'si',10,'TableS6'),('nc180-07-ta','Excitation-dependent TA control','measurement',['nc180-07'],'si',11,'FigureS6'),('dft-cubic','Cubic magnetic/electronic model','model',['nc150'],'main',5,'DFT input structures'),('dft-rhombohedral','Rhombohedral magnetic/electronic model','model',['nc180-05'],'main',5,'DFT input structures'),('rhombohedral-film','Rhombohedral film XRD stability','measurement',[],'main',8,'Film storage paragraph'),('cubic-film','Cubic film XRD stability','measurement',['nc150'],'main',9,'9week diffraction'),('aged-nc150','Aged cubic phase refinement','model',['nc150'],'si',13,'FigureS8'),('rhombohedral-dispersion','Diluted rhombohedral PL stability','measurement',[],'main',9,'Figure8b'),('aged-rhombohedral','Aged rhombohedral TEM','measurement',[],'si',13,'FigureS9; exact age/loading label unspecified'),('lsc-fresh','Fresh unencapsulated NC film device','device',[],'main',10,'Figure9'),('lsc-aged','Same film after11weeks','device',['lsc-fresh'],'main',10,'Same-film aging paragraph'),('lsc-bare','Bare-glass illuminated control','control',[],'main',10,'Figure9'),('lsc-dark','Dark photodiode control','control',[],'main',10,'Figure9')]:contexts.append({'id':i,'name':name,'kind':kind,'source_supported_parent_contexts':parents,'same_physical_batch_across_methods':False,'evidence':[ev(d,p,l)]})
for variant in variants:
 for method,d,p,l in [('xrd','main',4,'Figure2'),('tem','main',4,'Figure3'if variant['id']=='nc180-05'else'SI FiguresS2-S3'),('icp','si',7,'TableS3')]:contexts.append({'id':variant['id']+'-'+method,'name':variant['name']+' '+method.upper(),'kind':'measurement','source_supported_parent_contexts':[variant['id']],'same_physical_batch_across_methods':False,'evidence':[ev('si'if method=='tem'and variant['id']!='nc180-05'else d,4 if method=='tem'and variant['id']!='nc180-05'else p,l)]})

figspec=[
('graphical-abstract','main',1,'Graphical abstract','Conceptual phase/LSC illustration; no additional recipe or measured coordinates.',[],[],[.52,.331,.916,.494]),
('figure-1','main',3,'Hot-injection synthesis schematic','Apparatus cartoon, source reaction equation and emissive vial; not a full apparatus specification.',['cs-oleate-stock'],[],[.51,.07,.916,.278]),
('figure-2','main',4,'Diffraction and reported structure models','a/h reference phase/code captions conflict with visible labels; b-e/i fit the five explicitly labeled variants; f/g are reported crystal illustrations.',['nc150','nc180-07','nc180-05','nc180-035','nc200'],['C1','C7'],[.08,.069,.916,.638]),
('figure-3','main',4,'Optimized-sample TEM, SAED and size','All panels identify nc180-05; histogram13.4±0.9nm and pentagon-diameter wording retained.',['nc180-05'],['C2','C3'],[.08,.644,.916,.779]),
('figure-4','main',5,'Absorption, PLE, PLQY and TRPL','a compares150 and180//0.5; b/d rhombohedral/optimized, c source0.5/0.7; caption inverted ratio name retained.',['nc150','nc180-05','nc180-07'],['C4'],[.08,.07,.916,.466]),
('figure-5','main',6,'Calculated AFM bands, PDOS and wavefunctions','Computed cubic/rhombohedral Γ states; no measured atomistic model or transition approval.',['dft-cubic','dft-rhombohedral'],['C7'],[.08,.07,.916,.717]),
('figure-6','main',7,'Ultrafast transient absorption','Three source-labeled dispersions; pump300nm80uW, separate probes445/550nm; original fits/equations.',['nc150','nc180-07','nc180-05'],['C11'],[.08,.07,.916,.491]),
('figure-7','main',9,'Low-temperature PL and thermal-quenching fit','Optimized film,380nm excitation,30K initialcooling then20K increments; fitted binding-energy model.',['ltpl-nc180-05'],[],[.08,.07,.916,.438]),
('figure-8','main',9,'Separate phase and luminescence aging','Film XRD at0,1,3,5,8,10,12weeks and dispersion integratedPL plot; no implicit same specimen.',['rhombohedral-film','rhombohedral-dispersion'],['C9'],[.08,.441,.916,.707]),
('figure-9','main',10,'Photocurrent proof-of-concept','Schematic and dark/bare/fresh/11weekaged curves; unencapsulated deposited film.',['lsc-fresh','lsc-aged','lsc-bare','lsc-dark'],['C12'],[.08,.07,.916,.32]),
('figure-s1','si',3,'Preparation and unisolated degradation photographs','Preinjection precursor,quenched crude,centrifuged NCs and crude left1h in air.',['unisolated-control'],[],[.115,.09,.9,.45]),
('figure-s2','si',4,'TEM and SAED of four variants','a150,b200,c180//0.7,d180//0.35; visible panel/caption inconsistencies preserved.',['nc150','nc200','nc180-07','nc180-035'],['C5'],[.115,.13,.92,.898]),
('figure-s2-caption-continuation','si',5,'FigureS2 caption continuation','x2 high magnification andx3SAED convention; conflicts with c2/c3 native labels.',['nc150','nc200','nc180-07','nc180-035'],['C5'],[.115,.086,.9,.156]),
('figure-s3','si',5,'Four source size histograms','a150,b180//0.7,c200,d180//0.35; cubic diameter wording; source sample means are typed.',['nc150','nc180-07','nc200','nc180-035'],['C2','C3'],[.115,.214,.9,.605]),
('figure-s4','si',8,'Optical and decay comparison','Original a/c/d1:3/1:4labels conflict with b0.5/0.35; plot content retained without silent reassignment.',['nc150','nc180-07','nc180-05','nc180-035','nc200'],['C4'],[.115,.136,.93,.727]),
('figure-s5','si',9,'Excitation-dependent PL and decay','Optimized0.5, monitored670nm;335nm plotted versus330nm table entry.',['nc180-05'],['C6'],[.115,.082,.9,.47]),
('figure-s6','si',11,'Excitation-dependent transient absorption','180//0.7 with300/370/420nm pumps,600nm decay probe.',['nc180-07-ta'],['C11'],[.115,.082,.9,.489]),
('figure-s7','si',12,'Temperature-dependent FWHM','meV ordinate,380nm excitation; plotted lowest point near70K versus main50K prose.',['ltpl-nc180-05'],['C13'],[.115,.085,.9,.375]),
('figure-s8','si',13,'Fresh and aged cubic diffraction refinements','Literal aged phase fractions and fresh100% CsMnCl3 label; no geometry model validation.',['aged-nc150','nc150'],['C7'],[.115,.087,.9,.525]),
('figure-s9','si',13,'Aged rhombohedral TEM','Source age and exact loading ratio unknown;50nm/20nm scale bars and aggregation markings retained.',['aged-rhombohedral'],[],[.115,.562,.9,.908])]
figures=[];crop_specs=[]
for i,d,p,title,note,samples,flags,box in figspec:
 figures.append({'id':i,'title':title,'scope_note':note,'sample_ids':samples,'evidence':[ev(d,p,i)],'conflict_ids':flags,'gap_ids':['G5']if i in ['figure-2','figure-5','figure-s8']else['G3'],'asset_ids':[i]})
 crop_specs.append((i,d,p,box))
fg={x['id']:x for x in figures}
fg['figure-3']['panel_metadata']={'a':'nc180-05 TEM,50nm scale','b':'nc180-05 TEM,10nm scale','c':'SAED,10 1/nm scale; (0213),(036),(024),(110),(015) source labels','d':'13.4±0.9nm histogram; diameter of pentagons wording'}
fg['figure-s2']['panel_metadata']={'a':'nc150;50nm,10nm,10 1/nm scales; (420),(311),(220),(211),(200),(111),(110)','b':'nc200;50nm,10nm,10 1/nm scales; (315),(220),(300),(024),(110),(015)','c':'nc180-07;50nm,10nm,10 1/nm scales; (315),(0213),(036),(027),(024),(110),(015); source c3/c2 swapped','d':'nc180-035;50nm,10nm,10 1/nm scales; (229),(0213),(220),(205),(024),(110),(015); caption instead(e)'}
fg['figure-s9']['panel_metadata']={'a':'50nm scale; marked aggregates','b':'20nm scale; marked aggregates','age':'not given in caption','exact_loading_variant':'not given in caption'}
fg['figure-7']['temperature_labels_K']=[30,50,70,90,110,130,150,170,190,210,230,250,270,293]
fg['figure-8']['xrd_storage_labels_week']=[0,1,3,5,8,10,12]
fg['figure-6']['spectral_delay_labels']={'a_nc150':['<0ps','0.6ps','0.7ps','0.8ps','1ps','1.5ps','2ps','3ps','10ps'],'b_nc180_07':['<0ps','0.3ps','0.5ps','1ps','2ps','5ps','100ps','200ps','1.05ns'],'c_nc180_05':['<0ps','0.3ps','0.5ps','1ps','2ps','5ps','100ps','200ps','1.05ns','5.05ns']}
for i,d,p,box in [('table-1','main',8,[.08,.686,.483,.792]),('table-s1','si',6,[.115,.23,.9,.49]),('table-s2-a','si',6,[.115,.547,.9,.91]),('table-s2-b','si',7,[.115,.08,.9,.403]),('table-s3','si',7,[.115,.478,.9,.718]),('table-s4','si',9,[.115,.535,.765,.826]),('table-s5','si',10,[.115,.115,.9,.42]),('table-s6','si',10,[.115,.458,.9,.899]),('expression-distortion','main',5,[.517,.547,.916,.701]),('expression-thermal-quenching','main',8,[.532,.559,.715,.596])]:crop_specs.append((i,d,p,box))
equations=[]
for i,title,expr,d,p,l,scope,notes,assets in [
('synthesis-schematic','Idealized synthesis equation','2Cs-oleate + 3MnCl2 → 2CsMnCl3 + Mn(oleate)2','main',3,'Figure1 top','nc-series','Schematic mass-balance depiction; does not prove isolated Mn(oleate)2 or solution speciation.',['figure-1']),
('distortion','Octahedral bond-length distortion','D = (1/6) sum(i=1..6) |li-lavg|/lavg','main',5,'Octahedral distortion paragraph','structure-model','Average relative absolute deviation, not squared deviation;7.8% is source result.',['expression-distortion']),
('ta-triexponential','Rhombohedral TA decay fit','DeltaOD = A1 exp(-t/tau1) + A2 exp(-t/tau2) + A3 exp(-t/tau3)','main',7,'Figure6 caption','nc180-07/nc180-05','Source fit;Table1 values.',['figure-6']),
('ta-biexponential','Cubic TA decay fit','DeltaOD = A1 exp(-t/tau1) + A2 exp(-t/tau2)','main',7,'Figure6 caption','nc150','Source fit;A3/tau3 absent.',['figure-6']),
('thermal-quenching','Activated PL-quenching fit','I(T) = I0 / (1 + A exp(-Eb/(kB*T)))','main',8,'Displayed equation','ltpl-nc180-05','I0 is extrapolated0K intensity;sourcefit over100–300K,not direct binding-energy measurement.',['expression-thermal-quenching']),
('trpl-biexponential','TRPL decay fit','y = A1 exp(-t/tau1) + A2 exp(-t/tau2)','si',10,'TableS6 footnote','nc180-05-trpl','Source assigns nonradiative/radiative components;not independently proven channels.',['table-s6']),
('trpl-average','Printed average PL lifetime','tau_avg = sum(i=1..n) Ai*taui','si',10,'TableS6 final line','nc180-05-trpl','Literal source expression;C8 discrepancy retained, no silent normalization/replacement.',['table-s6']),
('tauc-axes','Printed Tauc ordinate labels','Left ordinate: (alpha*h*nu)^2, with printed unit exponent 2; right ordinate: (alpha*h*nu)^2, with printed unit exponent 1/2','si',8,'FigureS4b axes','cubic/rhombohedral optical gaps','Retain the left/right axis typography separately. The right ordinate retains its printed mismatch between the squared quantity and one-half unit exponent; no fit points, gap values or corrected formula are inferred.',['figure-s4'])]:equations.append({'id':i,'title':title,'expression':expr,'sample_scope':scope,'scope_note':notes,'evidence':[ev(d,p,l)],'asset_ids':assets})
conflicts=[{'id':i,'title':title,'description':desc,'status':'unresolved_source_discrepancy','evidence':[ev(d,p,l)]}for i,title,d,p,l,desc in A.CONFLICTS]
conflicts.append({'id':'C13','title':'Lowest FWHM temperature differs between prose and plot','description':'Main8 describes52meV at50K, but FigureS7 lowest visible marker is near70K. No exact curve digitization or silent temperature correction.','status':'unresolved_source_discrepancy','evidence':[ev('main',8,'FWHM paragraph'),ev('si',12,'FigureS7')]})
gaps=[{'id':i,'title':title,'description':desc,'status':'not_resolved_by_supplied_sources'}for i,title,desc in A.GAPS]
# References retain their source text with footers removed; no cited paper is treated as read.
txt='\n'.join((P/f'source-render/text/main-{p:02}.txt').read_text(encoding='utf-8')for p in [11,12,13])
txt=txt.split('REFERENCES',1)[1]
txt=re.sub(r'ACS Applied Nano Materials www\.acsanm\.org Article\s+https://doi\.org/10\.1021/acsanm\.2c04342\s+ACS Appl\. Nano Mater\. 2023, 6, 953[−–-]965\s+\d+','',txt)
refs=[]
for m in re.finditer(r'\((\d+)\)\s+(.*?)(?=\n\(\d+\)|\Z)',txt,re.S):
 num=int(m[1]);raw=' '.join(m[2].split());refs.append({'id':f'ref-{num}','number':num,'text':raw,'scope':'cited reference; not independently read in this source task','evidence':[ev('main',11 if num<=14 else 12 if num<=47 else 13,f'Reference {num}') ]})
assert len(refs)==55
refs[13]['evidence'].append(ev('main',12,'Reference14 continuation'))
payload={'schema':'mattersyn-source-facts/1','source_id':SID,'doi':DOI,'title':'Role of CsMnCl3 Nanocrystal Structure on Its Luminescence Properties','author':AUTHOR,'created_at':NOW,'source_generation':2,'bundle_sha256':intake['bundle_sha256'],'source_documents':[{k:d[k]for k in ['role','source_path','sha256','page_count']}for d in docs.values()],'facts':facts,'materials':materials,'stocks':stocks,'protocols':protocols,'sample_contexts':contexts,'figures':figures,'equations':equations,'conflicts':conflicts,'missingness':gaps,'references':refs,'source_table_path':'source-tables.json','training_eligibility':[],'atomic_model_status':'not qualified','independent_audit_status':'pending','source_scope':'All13 main+13 matched SI pages read/viewed; no external source downloads. No task/model/canonical approval implied.'}
wr('source-facts.json',payload)

# Faithful selected original crops; only source-render retains whole pages.
(P/'reader-assets').mkdir(exist_ok=True);pdfs={role:pypdfium2.PdfDocument(d['source_path'])for role,d in docs.items()};renders={};assets=[]
for i,d,p,b in crop_specs:
 key=(d,p)
 if key not in renders:renders[key]=pdfs[d][p-1].render(scale=3).to_pil().convert('RGB')
 im=renders[key];bbox=tuple(round(z*(im.width if j%2==0 else im.height))for j,z in enumerate(b));crop=im.crop(bbox);path=P/'reader-assets'/f'{i}.png';crop.save(path)
 assets.append({'id':i,'path':str(path),'relative_path':path.relative_to(P).as_posix(),'sha256':sha(path),'source_sha256':docs[d]['sha256'],'source_role':d,'source_path':docs[d]['source_path'],'pdf_page':p,'printed_page':952+p if d=='main'else'S'+str(p),'render_scale':3,'normalized_bbox':b,'pixel_bbox':list(bbox),'size_px':list(crop.size),'contains_complete_source_page':False,'scope':'selected original figure/table/expression crop; no publication approval','visual_author_review':'pending selected-crop review'})
wr('original-assets-manifest.json',{'schema':'mattersyn-original-assets/1','author':AUTHOR,'assets':assets,'independent_audit_status':'pending'})
# Contact images are derivative review aids, never original evidence.
for start in range(0,len(assets),4):
 sheet=Image.new('RGB',(1600,1300),'#edf1f5');draw=ImageDraw.Draw(sheet)
 for j,a in enumerate(assets[start:start+4]):
  img=Image.open(a['path']).convert('RGB');img.thumbnail((770,595));x=(j%2)*800+15;y=(j//2)*650+38;sheet.paste(img,(x,y));draw.text((x,y-25),a['id'],fill='black')
 sheet.save(P/'reader-assets'/f'author-contact-{start//4+1:02}.png')

notes_main=['title/abstract/introduction/graphical abstract','materials and complete synthesis/purification/acquisition','methods continuation,DFT/LSC,variant definitions,Figure1','Figures2–3,phase/morphology,caption discrepancies','Figure4,morphology,optics,distortion,DFT','Figure5 and model interpretation','Figure6,PLE/QY/structure correlation','TA,LTPL,Table1,thermal model,stability','Figures7–8,stability/LSC introduction','Figure9,device results,conclusion,SI declaration','author information/acknowledgments/references1–14','references14–47','references48–55; publisher advertisement excluded from scientific inventory']
notes_si=['title/byline/affiliations','affiliation continuation and contents','FigureS1 synthesis/control photos','FigureS2 TEM/SAED and caption','S2caption continuation,FigureS3 histograms','TablesS1 andS2 first blocks','S2 continuation,TableS3','FigureS4 optical comparison','FigureS5,TableS4','TablesS5–S6,fit/average footnote','FigureS6 TA control','FigureS7 FWHM','FiguresS8–S9 aging']
pages=[]
for d in docs.values():
 for row in d['pages']:
  rr=copy.deepcopy(row);rr.update({'document_role':d['role'],'source_sha256':d['sha256'],'text_read':True,'visually_inspected':True,'native_page_visually_inspected':True,'disposition':'read_and_visually_inspected','scope_note':(notes_main if d['role']=='main'else notes_si)[row['pdf_page']-1]});pages.append(rr)
wr('page-coverage.json',{'author':AUTHOR,'created_at':NOW,'main_read_pages':13,'si_read_pages':13,'complete_supplied_page_coverage':True,'complete_main_plus_si_coverage':True,'pages':pages,'method':'Actual full text/native-page review; all tables manually transcribed and every page viewed with view_image. Flags are set only after those actions.','independent_audit_status':'pending'})
wr('pairing-review.json',{'author':AUTHOR,'status':'content_verified_author_pairing','independent_audit_status':'pending','source_generation':2,'bundle_sha256':intake['bundle_sha256'],'four_original_hashes':{c['source_path']:c['sha256']for c in intake['file_copies']},'evidence':['Main title/byline matches SI title/byline; SI adds initial The.','Main10 associated-content declaration matches SI synthesis/TEM/Rietveld/optical/stability sections.','Source-defined five sample labels and main references toTablesS1–S6/FiguresS1–S9 match the local SI.'],'documents':[{k:d[k]for k in ['role','source_path','sha256','page_count']}for d in docs.values()],'pairing_gaps':[]})
wr('relevance-screening.json',{'author':AUTHOR,'decision':'synthesis_relevant','basis':'Main2 supplies Cs-oleate preparation, five-defined-condition hot-injection method, isolation and alternative purification controls; SI adds source photos/structural/optical tables.','evidence':[ev('main',2,'Preparation/Synthesis/Purification'),ev('main',3,'Sample definitions'),ev('si',3,'FigureS1')],'no_recipe_terminal_status':False,'independent_audit_status':'pending'})
units=[]
for key in ['facts','materials','stocks','protocols','sample_contexts','figures','equations','conflicts','missingness','references']:
 for j,x in enumerate(payload[key]):
  units.append({'id':key+':'+x['id'],'kind':key,'source_object_id':x['id'],'path':'source-facts.json','json_pointer':f'/{key}/{j}'})
  if key=='protocols':
   for k,o in enumerate(x['operations']):units.append({'id':'operation:'+o['id'],'kind':'operation','source_object_id':o['id'],'path':'source-facts.json','json_pointer':f'/protocols/{j}/operations/{k}'})
for j,t in enumerate(tables):
 units.append({'id':'table:'+t['id'],'kind':'table','source_object_id':t['id'],'path':'source-tables.json','json_pointer':f'/tables/{j}'})
 for k,r in enumerate(t['rows']):units.append({'id':'table_row:'+r['id'],'kind':'table_row','source_object_id':r['id'],'path':'source-tables.json','json_pointer':f'/tables/{j}/rows/{k}'})
counts={k:len(payload[k])for k in ['facts','materials','stocks','protocols','sample_contexts','figures','equations','conflicts','missingness','references']};counts.update({'fact_quantities':sum(len(f['quantities'])for f in facts),'operations':sum(len(p['operations'])for p in protocols),'tables':len(tables),'table_rows':sum(len(t['rows'])for t in tables),'table_typed_cells':sum(len(r['cells'])for t in tables for r in t['rows']),'printed_body_cells':sum(c['is_printed_body_cell']for t in tables for r in t['rows']for c in r['cells']),'numeric_table_cells':sum(c['value']is not None for t in tables for r in t['rows']for c in r['cells']),'selected_crops':len(assets),'main_pages':13,'si_pages':13,'inventory_units':len(units)})
wr('source-inventory.json',{'schema':'mattersyn-source-inventory/1','author':AUTHOR,'source_id':SID,'counts':counts,'inventory_units':units,'all_local_supplied_pages_accounted':True,'source_unit_ids_globally_unique':True,'model_approval':False,'independent_audit_status':'pending'})
raw=[]
for d in docs.values():
 for row in d['pages']:
  for name,hkey in [('text_path','text_sha256'),('layout_text_path','layout_text_sha256'),('image_path','image_sha256')]:raw.append({'path':row[name],'sha256':row[hkey],'kind':'complete_source_page_render'if name=='image_path'else'complete_source_page_text','public_export_allowed':False})
wr('complete-source-payloads.json',{'policy':'Original PDFs/SI, complete page scans and complete source text stay local; source-render is the recognized exclusion directory.','original_files':[{'path':c['source_path'],'sha256':c['sha256'],'public_export_allowed':False}for c in intake['file_copies']],'payloads':raw})
print(json.dumps(counts,indent=2))
