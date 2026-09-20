"""Private complete supplied-main extraction. Original PDFs and shared state are read only."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
import json,hashlib,re,copy
import pypdfium2
from PIL import Image,ImageDraw,ImageOps
import source_author_data as A
P=Path(__file__).resolve().parent; SID='sommer2020'; DOI='10.1021/acs.cgd.9b01519'
NOW=datetime.now(timezone.utc).isoformat(); AUTHOR='/root/backlog_eta'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(n,v):(P/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
intake=json.loads((P/'intake-identity.json').read_bytes());copies=intake['file_copies'];SOURCE=Path(copies[0]['source_path']);HASH=copies[0]['sha256']
for c in copies:assert sha(c['source_path'])==HASH
pdf=pypdfium2.PdfDocument(str(SOURCE));assert len(pdf)==11
def ev(p,loc):return {'source_id':SID+'-main','document_role':'main','source_sha256':HASH,'pdf_page':p,'printed_page':1788+p,'locator':loc}
def quantity(raw,unit,meaning,p,loc,flags=()):
 s=str(raw);t=s.replace('−','-').replace('–','-');ap=False;v=unc=ran=comp=parts=None;st='reported'
 if t.startswith('~'):ap=True;t=t[1:]
 m=re.match(r'^(>=|<=|>|<)',t)
 if m:comp=m[1];t=t[len(m[1]):]
 n=r'[+-]?\d+(?:\.\d+)?'
 esd=re.fullmatch(r'('+n+r')\((\d+)\)',t)
 if esd:
  v=float(Decimal(esd[1]));places=len(esd[1].split('.')[1])if'.'in esd[1]else 0;unc=float(Decimal(esd[2])*Decimal(10)**(-places))
 elif re.fullmatch(n,t):v=float(Decimal(t))
 elif re.fullmatch(r'\d+(?:\.\d+)?-\d+(?:\.\d+)?',t):lo,hi=t.split('-');ran={'min':float(lo),'max':float(hi)}
 elif unit=='ratio_parts' and re.fullmatch(r'\d+(?:\.\d+)?(?::\d+(?:\.\d+)?)+',t):parts=[float(x)for x in t.split(':')];st='reported_ratio_parts'
 elif t=='1/2':v=0.5;st='reported_fraction'
 else:st='reported_text'
 return {'raw_text':s,'value':v,'unit':unit,'uncertainty':unc,'uncertainty_definition':'parenthetic digits in last reported places; statistical definition not restated'if unc is not None else None,'range':ran,'comparison':comp,'approximate':ap,'components':parts,'status':st,'meaning':meaning,'evidence':[ev(p,loc)],'conflict_ids':[x for x in flags if x.startswith('C')],'gap_ids':[x for x in flags if x.startswith('G')]}
facts=[]
for i,p,loc,title,claim,scope,qs,flags,kind in A.FACTS:
 facts.append({'id':SID+'-'+i,'title':title,'claim':claim,'sample_scope':scope,'claim_class':kind,'evidence':[ev(p,loc)],'quantities':[quantity(r,u,n,p,loc,flags)for n,r,u in qs],'conflict_ids':[x for x in flags if x.startswith('C')],'gap_ids':[x for x in flags if x.startswith('G')],'independent_audit_status':'pending'})
fb={f['id'].removeprefix(SID+'-'):f for f in facts}
for fid,p,loc in [('structures-background',1,'Introduction: spinel structure'),('d4-solution',3,'Figure 3 and Figure 4b caption/legend'),('mw-time-outcome',5,'Microwave discussion begins'),('uvvis-transform',9,'UV-vis Spectroscopy continuation'),('mw-middle-outcome',6,'Figure 10 caption and phase-pure qualification'),('insitu-middle',5,'Crystallite discussion: I4-I8 initially phase-pure')]:fb[fid]['evidence'].append(ev(p,loc))
fb['d4-solution']['quantities'][1]['evidence']=[ev(3,'First paragraph: coordination features up to about 8 angstrom')]
fb['insitu-i7-i8-scope']['evidence'].append(ev(4,'In situ discussion: 1:2:7.81 and 1:2:8.34 initially ZnO-bearing'))

rows=[];cols=['C_NaOH','T_rxn','Zn_Al_OH','t_rxn','t_dwell']
for ir,line in enumerate(A.TABLE.splitlines(),1):
 sid,*vals=line.split();cells=[]
 flags=(['C1']if sid.startswith('M')else['C2']if sid=='S2'else['C3']if sid in['A1','A2','A3']else['C11']if sid in['I12','I13','I14']else[])
 for col,raw,un in zip(cols,vals,['M','degC','ratio_parts','min','min']):
  unit='day'if raw.endswith('day')else un;t=raw.removesuffix('day');q=quantity(t,unit,col,4,f'Table 1 {sid}, {col}',flags)
  q['raw_text']=t+' days'if raw.endswith('day')and t!='1'else t+' day'if raw.endswith('day')else t
  if raw=='RT':q['unit']=None;q['meaning']='room temperature; numerical value not supplied'
  cells.append({'id':f'table-1-r{ir:02}-{col}','column':col,**q})
 rows.append({'row_label':sid,'sample_id':sid,'source_raw_row':line,'row_label_evidence':[ev(4,f'Table 1 sample column row {ir}')],'cells':cells})
table={'id':'table-1','title':'Samples Prepared in This Study','columns':cols,'rows':rows,'evidence':[ev(4,'Table 1, all 37 rows and nomenclature footnote')],'notes':['37 row labels plus 185 typed data cells = 222 printed body cells.','Source column headings give minutes, but autoclave body cells explicitly say days; preserve their day units.','Native SCF rows contain ~1 in t_rxn and 0 in t_dwell; text extraction merges them into ~10.','In situ 0-40 min entries are reported ranges, not invented fixed-duration process endpoints.','C_NaOH basis is not silently harmonized across different preparation branches.','RT remains room-temperature text without an assumed numeric temperature.'],'footnotes':[{'id':'table-1-footnote-a','text':'M: microwave synthesis; S: supercritical flow synthesis; A: autoclave synthesis; I: in situ XRD; D: solutions for X-ray total scattering experiments.','evidence':[ev(4,'Table 1 footnote a')]}],'independent_numerical_audit':'pending'}
table['notes'].append('D1-D4 are total-scattering solution observations at RT; their 3.3 min table entries are not a demonstrated synthesis-heating or growth duration.')
write('source-tables.json',{'schema':'mattersyn-source-tables/1','source_id':SID,'author':AUTHOR,'tables':[table],'independent_audit_status':'pending'})

material_data=[
('zn-nitrate','Zinc nitrate hexahydrate','Zn(NO3)2·6H2O','precursor','Sigma-Aldrich, >=99%; hydration explicitly supplied.',7),
('al-nitrate','Aluminum nitrate nonahydrate','Al(NO3)3·9H2O','precursor','Sigma-Aldrich, >=98%; hydration explicitly supplied.',7),
('naoh','Sodium hydroxide','NaOH','base','Sigma-Aldrich >=97%; do not invent charge masses from table concentrations.',7),
('zno-feed','Nanosized zinc oxide','ZnO','alternative_precursor','Inframat Advanced Materials ~30 nm; I15/I16 feed, distinct from reaction-generated ZnO.',7),
('aloh3','Aluminum hydroxide','Al(OH)3','alternative_precursor','Sigma-Aldrich, purity unreported; I15/I16 only.',7),
('demin-feed-water','Demineralized water for nitrate feed','H2O','solvent','MW stock charge and ACS shared feed; not automatically Millipore or PDF background water.',7),
('demin-wash-water','Demineralized wash water','H2O','wash_solvent','Three washes of laboratory powders; quantity unreported.',7),
('ethanol-96','Ethanol, 96%','C2H6O','wash_solvent','One laboratory powder wash; not microscopy 99%.',7),
('insitu-water','Water-based nitrate-stock solvent','H2O','solvent','Grade not specified in the in situ nitrate preparation.',8),
('millipore-water','Millipore water','H2O','solvent','I15/I16 ZnO/Al(OH)3 preparation; no assumed volume.',8),
('deionized-background','Deionized water background','H2O','measurement_reference','PDF background in matching capillary type and temperature.',8),
('ethanol-99','Ethanol, 99%','C2H6O','dispersion_solvent','Microscopy dispersion; sonication settings unknown.',8),
('quartz-vessel','Thick-walled quartz vessel',None,'apparatus','80 mL nominal vessel, 10 mL fill; symbolic apparatus only.',7),
('sapphire-tube','Sapphire sensor immersion tube',None,'apparatus','MW temperature/pressure sensor housing, not in situ capillary.',7),
('ptfe-autoclave','Teflon-lined stainless-steel autoclave',None,'apparatus','20.0 mL nominal vessel, 10 mL fill; pressure unknown.',8),
('sapphire-capillary','Single-crystal sapphire capillary',None,'support','In situ ID 0.6 mm, OD 1.1 mm; no supplied atomistic substrate model.',8),
('glass-capillary','Glass diffraction capillary',None,'support','Selected ex situ synchrotron sample diameter 0.3 mm; rotates during acquisition.',8),
('tem-grid','Copper Formvar/carbon TEM grid',None,'support','200 mesh; ambient drying.',8),
('lab6-660a','LaB6 NIST 660A','LaB6','measurement_reference','Laboratory XRD resolution reference.',8),
('lab6-660b','LaB6 NIST 660b','LaB6','measurement_reference','PDF Qdamp and reciprocal-space resolution reference.',8),
('ceria-reference','Cerium oxide standard','CeO2','measurement_reference','Selected synchrotron resolution/wavelength standard.',8),
('baso4-reference','Barium sulfate reference','BaSO4','measurement_reference','Diffuse-reflectance optical reference.',8),
('spinel-product','Zinc aluminate spinel product','ZnAl2O4','product_family','Phase fractions/sizes remain sample-specific; no source-supplied measured-coordinate file.',1),
('zno-intermediate','Reaction-generated ZnO','ZnO','intermediate_or_impurity','D2 and specified I/M/S/A contexts; not automatically the ~30 nm purchased feed.',3),
('alooh-impurity','Aluminum oxyhydroxide','AlOOH','impurity','Boehmite-type impurity separate from Al(OH)3 feed.',1),
('zinc-aquo-context','Proposed solvated zinc precursor species',None,'model_context','Protonation/hydration and weak long-range associations unresolved; not a recovered molecular graph.',2),
('al-dimer-context','Proposed octahedral aluminum dimer',None,'model_context','Source-dependent delta formula and literature-supported context; exact speciation unknown.',2),
('nitrate-context','Nitrate-ion PDF context','NO3-','model_context','N-O correlation at 1.2 angstrom; not a distinct reagent charge.',2)]
materials=[{'id':i,'name':n,'source_formula_or_abbreviation':form,'role':role,'scope_note':note,'evidence':[ev(p,'Source material / apparatus / structural context')]}for i,n,form,role,note,p in material_data]

def quantities(fs):return [copy.deepcopy(q)for f in fs for q in fb[f]['quantities']]
stocks=[]
for i,name,comps,fs,scope,note in [
('mw-nitrate-stock','Microwave/autoclave mixed-nitrate feed',['zn-nitrate','al-nitrate','demin-feed-water'],['mw-stock'],'M1-M9/A1-A6','20 mL water charge, not asserted final solution volume.'),
('mw-low-base','Low-base laboratory formulation',['mw-nitrate-stock','naoh'],['mw-base'],'M1/A1/A4','Final NaOH 1.5 M only; shared fact also retains other alternative concentrations.'),
('mw-middle-base','Middle-base laboratory formulation',['mw-nitrate-stock','naoh'],['mw-base'],'M2/M4-M9/A2/A5','Final NaOH 1.7 M only; variants are alternatives, not mixed together.'),
('mw-high-base','High-base laboratory formulation',['mw-nitrate-stock','naoh'],['mw-base'],'M3/A3/A6','Final NaOH 2.0 M only.'),
('insitu-nitrate-stock','Concentrated in situ nitrate stock',['zn-nitrate','al-nitrate','insitu-water'],['insitu-nitrate-stock'],'I1-I14','30.0 mL solution volume, distinct from the laboratory feed.'),
('insitu-base-solutions','Variable NaOH(aq) solutions',['naoh','insitu-water'],['insitu-mix'],'I1-I14','Individual preparation masses absent; zero-base branch diluent and concentration basis not resolved.'),
('insitu-oxide-slurry','ZnO/Al(OH)3 suspension',['zno-feed','aloh3','millipore-water'],['insitu-oxide-stock'],'I15/I16','Both masses and final metal concentrations reported; water volume not given.')]:
 stocks.append({'id':i,'name':name,'components':comps,'source_fact_ids':[SID+'-'+f for f in fs],'quantities':quantities(fs),'sample_scope':scope,'notes':note,'evidence':[e for f in fs for e in fb[f]['evidence']]})
for stock,idx in [(stocks[1],0),(stocks[2],1),(stocks[3],2)]:stock['quantities']=[stock['quantities'][idx]]

specs=[
('mw-route','Microwave laboratory synthesis','synthesis',['M'+str(i)for i in range(1,10)],[
('mw-dissolve','Dissolve nitrate hydrates in water',['zn-nitrate','al-nitrate','demin-feed-water'],['mw-nitrate-stock'],['mw-stock'],None,['mixing duration']),
('mw-base','Prepare separate NaOH-adjusted formulations',['mw-nitrate-stock','naoh'],['mw-formulations'],['mw-base'],None,['NaOH masses','final mixture volumes']),
('mw-load','Load aliquot into quartz microwave vessel',['mw-formulations','quartz-vessel','sapphire-tube'],['mw-loaded'],['mw-vessel'],None,[]),
('mw-heat','Apply sample-specific heating profile and Table 1 dwell',['mw-loaded'],['mw-crude'],['mw-profile-1','mw-profile-2','mw-pressure'],None,['unresolved total-time discrepancy','power settings'])]),
('scf-route','Supercritical-flow synthesis','synthesis',['S1','S2'],[
('scf-feed','Supply precursor and solvent to the cited in-house flow reactor',['zn-nitrate','al-nitrate','naoh','insitu-water'],['scf-feed'],['scf-settings'],None,['full precursor formulation','solvent grade','reactor dimensions']),
('scf-react','React at sample-specific SCF conditions',['scf-feed'],['scf-crude'],['scf-settings'],None,['450/380 degree source conflict','collection protocol'])]),
('acs-route','Autoclave laboratory synthesis','synthesis',['A'+str(i)for i in range(1,7)],[
('acs-load','Load previously described laboratory feed into lined autoclave',['mw-formulations','ptfe-autoclave'],['acs-loaded'],['acs-settings'],None,['pressure']),
('acs-heat','Heat at 220 °C for the source-specific short or long duration',['acs-loaded'],['acs-crude'],['acs-settings','acs-ramp-assumption'],None,['17 days/2.5 weeks discrepancy','measured heating trace'])]),
('lab-workup','Common laboratory powder isolation','workup',['M1-M9','S1-S2','A1-A6'],[
('lab-separate','Centrifuge and separate powders until solution appears colorless',['mw-crude','scf-crude','acs-crude'],['retained-lab-powder','supernatant'],['workup'],'retained-lab-powder',['speed','duration']),
('lab-wash','Wash retained powder three times with demineralized water then once with 96% ethanol',['retained-lab-powder','demin-wash-water','ethanol-96'],['washed-powder','wash-supernatants'],['workup'],'washed-powder',['solvent amounts']),
('lab-dry','Vacuum-dry retained powder at 50 °C for 4 h',['washed-powder'],['dried-lab-powders'],['workup'],'dried-lab-powders',['vacuum pressure','yield'])]),
('insitu-nitrate','Nitrate-based in situ synthesis/observation','synthesis_observation',['I'+str(i)for i in range(1,15)],[
('insitu-stock','Prepare concentrated nitrate stock',['zn-nitrate','al-nitrate','insitu-water'],['insitu-nitrate-stock'],['insitu-nitrate-stock'],None,[]),
('insitu-mix','Mix equal nitrate-stock and varying NaOH-solution aliquots',['insitu-nitrate-stock','insitu-base-solutions'],['insitu-slurry'],['insitu-mix'],None,['zero-base diluent']),
('insitu-stir-load','Vigorously stir then inject slurry into sapphire capillary',['insitu-slurry','sapphire-capillary'],['loaded-nitrate-capillary'],['insitu-load'],None,[]),
('insitu-heat','Heat and follow sample-specific phase formation over the Table 1 intervals',['loaded-nitrate-capillary'],['insitu-nitrate-series'],['insitu-acquisition','insitu-lowbase'],None,['complete pressure/exposure schedule','Figure 6 time-unit conflict'])]),
('insitu-oxide','ZnO/Al(OH)3 alternative in situ branch','synthesis_observation',['I15','I16'],[
('oxide-slurry','Mix solid precursors in Millipore water and stir for 4 h',['zno-feed','aloh3','millipore-water'],['insitu-oxide-slurry'],['insitu-oxide-stock'],None,['water volume']),
('oxide-load','Inject suspension into sapphire capillary',['insitu-oxide-slurry','sapphire-capillary'],['loaded-oxide-capillary'],['insitu-load'],None,['injected suspension volume']),
('oxide-heat','Heat I15/I16 at their separate Table 1 temperatures and follow conversion',['loaded-oxide-capillary'],['insitu-oxide-series'],['insitu-oxide-outcome','insitu-acquisition'],None,['exact completion times'])]),
('insitu-refinement','Sequential in situ refinement','analysis',['I1-I16'],[
('insitu-fit','Fit phases, size and constrained defect parameters',['insitu-nitrate-series','insitu-oxide-series'],['insitu-analysis-data'],['insitu-defects','insitu-minor-phase'],None,['SI Table S7 results'])]),
('pdf-procedure','Precursor solution total scattering','characterization',['D1','D2','D3','D4'],[
('pdf-solutions','Prepare the separately named nitrate/base solution contexts',['zn-nitrate','al-nitrate','naoh','insitu-water'],['pdf-solutions'],['d3-solution','d4-solution','d2-pdf'],None,['D1/D2 exact recipe concentrations','solution volumes']),
('pdf-acquire','Acquire solution scattering and matching water background',['pdf-solutions','deionized-background','lab6-660b'],['total-scattering-data'],['pdf-acquisition'],None,['full detector/energy settings']),
('pdf-reduce-fit','Reduce PDFs and fit scoped molecular/crystalline models',['total-scattering-data'],['precursor-analysis-data'],['pdf-fit'],None,['unavailable SI parameter tables'])]),
('lab-xrd-procedure','Laboratory diffraction and refinement','characterization',['M1-M9','S1-S2','A1-A6'],[
('lab-xrd-acquire','Acquire laboratory Cu Kalpha1 diffraction',['dried-lab-powders','lab6-660a'],['lab-diffraction'],['lab-xrd'],None,['scan interval','step and exposure']),
('lab-xrd-fit','Fit phases and spherical-harmonic size using literature-fixed positions/occupancies',['lab-diffraction'],['lab-refinement-data'],['lab-fit','synchrotron-fit'],None,['SI detailed refinements'])]),
('synchrotron-procedure','Selected ex situ synchrotron diffraction','characterization',['M1','M2','M3','M7','S1','A1','A2'],[
('synchrotron-load-acquire','Pack and rotate glass capillaries and acquire diffraction',['dried-lab-powders','glass-capillary','ceria-reference'],['synchrotron-data'],['synchrotron-xrd'],None,['packing mass','exposure']),
('synchrotron-fit','Refine using MAUD with glass/background features and anisotropic size',['synchrotron-data'],['synchrotron-refinement-data'],['synchrotron-fit'],None,['SI results'])]),
('microscopy-procedure','TEM/STEM/EDS preparation and acquisition','characterization',['S1','M2','A2','other selected samples unspecified'],[
('microscopy-disperse','Sonicate dried powder in 99% ethanol',['dried-lab-powders','ethanol-99'],['microscopy-dispersion'],['tem-prep'],None,['sonication settings','concentration']),
('microscopy-deposit','Drop onto supported copper grids and dry in ambient atmosphere',['microscopy-dispersion','tem-grid'],['microscopy-specimens'],['tem-prep'],'microscopy-specimens',['drop volume']),
('microscopy-acquire','Acquire bright-field TEM, HAADF-STEM and EDS',['microscopy-specimens'],['microscopy-data'],['tem-acquire'],None,['explicit operating voltage','per-grid exact sample identity'])]),
('optical-procedure','Diffuse-reflectance and optical-gap analysis','characterization',['M2','A2','S1'],[
('optical-acquire','Measure diffuse reflectance at room temperature against BaSO4',['dried-lab-powders','baso4-reference'],['reflectance-data'],['uvvis-acquire'],None,['sample preparation details']),
('optical-transform','Apply the printed transform and linear Tauc fit',['reflectance-data'],['optical-analysis-data'],['uvvis-transform'],None,['SI Tauc plots','exact printed sample gap values'])])]
protocols=[]
for i,title,kind,sids,ops in specs:
 operations=[]
 for oi,action,ins,outs,fs,retained,missing in ops:
  operations.append({'id':oi,'action':action,'inputs':ins,'outputs':outs,'retained_fraction':retained,'source_fact_ids':[SID+'-'+f for f in fs],'quantities':quantities(fs),'quantity_scope_note':'Source-context quantities are retained for evidence coverage; only the explicitly applicable subset is an action condition. Alternative sample conditions must never be applied simultaneously.','evidence':[e for f in fs for e in fb[f]['evidence']],'missing_fields':missing})
 protocols.append({'id':i,'title':title,'kind':kind,'sample_ids':sids,'operations':operations,'source_table_ids':['table-1'],'independent_audit_status':'pending','exact_protocol_eligibility':False})
# Do not accidentally assign nitrate-branch five-minute stirring to oxide loading.
oxide_load=next(o for p in protocols for o in p['operations']if o['id']=='oxide-load')
oxide_load['source_fact_ids']=[SID+'-insitu-oxide-stock'];oxide_load['quantities']=[];oxide_load['evidence']=[ev(8,'ZnO Based Solutions: subsequent injection into sapphire capillary')]
# Per-action subsets: shared evidence is retained, but unrelated settings do not masquerade as process conditions.
keep={
'lab-separate':[], 'lab-wash':['water washes','ethanol washes','wash ethanol grade'],'lab-dry':['drying temperature','drying duration'],
'acs-load':['vessel capacity','precursor fill'],'acs-heat':['set point','short duration','methods long duration','assumed time to set point'],
'scf-feed':['solvent flow rate','precursor flow rate','OH concentration','Zn:Al:OH molar ratio'],'scf-react':['pressure','methods temperature each synthesis'],
'microscopy-disperse':['dispersion ethanol grade'],'microscopy-deposit':['grid mesh'],
'lab-xrd-fit':['Chebyshev coefficient count','maximum spherical-harmonic functions'],
'insitu-heat':['temperature after increase','reported time before increase'],
'pdf-solutions':['Zn concentration','pH','Al-only concentration','Zn:Al:OH']}
for pr in protocols:
 for o in pr['operations']:
  if o['id'] in keep:o['quantities']=[q for q in o['quantities']if q['meaning']in keep[o['id']]]
  o['context_fact_ids']=o['source_fact_ids']
  if o['id']=='insitu-heat':o['condition_scope_note']='430 °C at ~34 min applies only to I1/I2; other I rows use their own Table 1 condition, with the seconds/minutes conflict retained.'
  if o['id']=='mw-heat':o['condition_scope_note']='Profile 2 only M4-M6; profile 1 only M1-M3/M7-M9. See independent Table 1 row condition schedules.'

contexts=[{'id':r['sample_id'],'kind':{'M':'laboratory_microwave_sample','S':'laboratory_scf_sample','A':'laboratory_autoclave_sample','I':'in_situ_experiment','D':'precursor_solution_context'}[r['sample_id'][0]],'table_row_pointer':f'/tables/0/rows/{i}','table_id':'table-1','evidence':r['row_label_evidence'],'phase_assignment_note':'Use explicit result facts/figure scopes. A table row alone is not proof of phase purity, a yield or a new independent batch.','verified_cross_technique_exact_pair':False}for i,r in enumerate(rows)]
for i,n in [('formation-model','Proposed precursor/nucleation pathways'),('literature-structures','Cited crystal structure depictions'),('laboratory-XRD','Shared laboratory refinement assumptions'),('microscopy','Acquisition scope with incomplete per-grid assignments'),('literature-band-gap','Cited prior ranges'),('article-summary','Author summary claims'),('source-availability','Main-only supplied source')]:contexts.append({'id':i,'kind':'context_only','name':n,'verified_cross_technique_exact_pair':False})

equations=[
{'id':'heating-profile-1','source_label':'(1)','expression':'RT --1.45 min--> 130 °C --7.85 min--> 210 °C --15 min--> 240 °C --1 °C/min--> T_rxn','sample_ids':['M1','M2','M3','M7','M8','M9'],'evidence':[ev(8,'Equation 1')],'conflict_ids':['C1']},
{'id':'heating-profile-2','source_label':'(2)','expression':'RT --1.45 min--> 130 °C --7.45 min--> 250 °C','sample_ids':['M4','M5','M6'],'evidence':[ev(8,'Equation 2')],'conflict_ids':['C1']},
{'id':'zn-hydrolysis','source_label':'unnumbered reaction','expression':'Zn(NO3)2(s) + 6 H2O(l) -> [Zn(H2O)_(6-delta)(OH)_delta]^(2-delta)(aq) + delta H+(aq) + 2 NO3-(aq)','sample_ids':['D3'],'evidence':[ev(2,'Total Scattering: Zn precursor protonation reaction')],'notes':'Literal proposed variable-protonation context; delta unknown. No new chemical balancing or precise molecular structure is asserted.'},
{'id':'zn-dissolution','source_label':'unnumbered equilibrium','expression':'ZnO(s) + 5 H2O(l) <=> [Zn(H2O)_(4-delta)(OH)_delta]^(2-delta)(aq) + 2 OH-(aq)','sample_ids':['D2'],'evidence':[ev(3,'ZnO dissolution paragraph')],'notes':'Source formula retained literally; no silently repaired stoichiometry or resolved aqueous speciation.'},
{'id':'al-dimer','source_label':'unnumbered precursor formula','expression':'[Al2(H2O)_(11±delta)(OH)_delta]^(6±delta)(aq)','sample_ids':['D4'],'evidence':[ev(2,'Al precursor paragraph, cited ref 41')],'notes':'Main p3 separately prints 11-delta; preserve source-dependent symbols and unknown protonation, not a unique molecular graph.'},
{'id':'spinel-defects','source_label':'unnumbered occupancy constraint','expression':'[(A2+)_(1-x-y)(B3+)_x]_tet[(B3+)_(2-x)(A2+)_x]_okt[(A2+)_y]_000 O4','sample_ids':['I1-I16'],'evidence':[ev(8,'In situ refinement paragraph')],'notes':'Stoichiometric model constraint; x/y results unavailable in SI Table S7. Does not constitute a complete coordinate set.'},
{'id':'kubelka-munk','source_label':'unnumbered optical expression','expression':'C/S = (1-R)^2 (2R)^x; x=1/2','sample_ids':['M2','A2','S1'],'evidence':[ev(8,'UV-vis Spectroscopy formula and exponent'),ev(9,'Tauc fit continuation')],'notes':'Native printed layout is multiplication by (2R)^x, with no division bar or negative exponent; retained literally. Original visual is authoritative; no standard-convention correction or independently validated optical model.'}]

conflicts=[{'id':i,'title':t,'description':d,'status':'unresolved_source_discrepancy','evidence':[ev(p,t)for p in ps]}for i,t,d,ps in A.CONFLICTS]
gaps=[{'id':i,'title':t,'description':d,'status':'open'}for i,t,d in A.GAPS]
figures=[{'id':i,'label':lab,'title':title,'sample_ids':sids,'evidence':[ev(p,lab+' including caption')],'asset_id':i,'conflict_ids':[f for f in flags if f.startswith('C')],'gap_ids':[f for f in flags if f.startswith('G')],'interpretation_scope':'Literature or author model where stated; graph-only values are not digitized as reported exact numbers.'}for i,p,lab,title,sids,flags,bbox in A.FIGURES]
next(f for f in figures if f['id']=='figure-11')['conflict_ids'].append('C12')

# References remain literal local-source text with page locators; no cited full texts are claimed read.
refs=[];reftext=''
for p in [9,10,11]:
 txt=(P/f'private/text/main-{p:02}.txt').read_text(encoding='utf-8')
 txt=txt.split('Crystal Growth & Design pubs.acs.org/crystal Article')[0]
 if p==9:txt=txt.split('■ REFERENCES',1)[1]
 reftext+='\n'+txt
for m in re.finditer(r'\((\d+)\)\s+([\s\S]*?)(?=\n\(\d+\)\s|\Z)',reftext):
 num=int(m[1]);txt=' '.join(m[2].split());pg=next(p for p in [9,10,11]if re.search(r'\('+str(num)+r'\)\s',(P/f'private/text/main-{p:02}.txt').read_text(encoding='utf-8')))
 refs.append({'id':f'reference-{num}','number':num,'citation_as_extracted':txt,'evidence':[ev(pg,f'Reference {num}')],'cited_full_text_read':False})
assert [r['number']for r in refs]==list(range(1,66))
write('source-facts.json',{'schema':'mattersyn-source-facts/1','source_id':SID,'doi':DOI,'title':'Atomic Scale Design of Spinel ZnAl2O4 Nanocrystal Synthesis','authors':['Sanna Sommer','Espen D. Bøjesen','Hazel Reardon','Bo B. Iversen'],'year':2020,'author':AUTHOR,'created_at':NOW,'source_generation':intake['source_generation'],'bundle_sha256':intake['bundle_sha256'],'source_scope':'complete supplied 11-page main; declared SI unlocated/unverified','facts':facts,'materials':materials,'stocks':stocks,'protocols':protocols,'sample_contexts':contexts,'figures':figures,'equations':equations,'conflicts':conflicts,'missingness':gaps,'references':refs,'independent_audit_status':'pending','canonical_status':'not authored','training_eligibility':[],'atomic_model_status':'not qualified'})

crop_specs=[(i,p,lab,title,bbox)for i,p,lab,title,sids,flags,bbox in A.FIGURES]+[
('table-1',4,'Table 1','All 37 sample rows and footnote',(.09,.224,.489,.832)),
('heating-profiles',8,'Equations 1 and 2','Literal microwave heating profiles',(.09,.077,.488,.141)),
('spinel-defect-expression',8,'Unnumbered defect constraint','Refinement constraint with context',(.09,.681,.49,.812)),
('optical-transform',8,'Unnumbered optical expression','Printed transformation and exponent',(.512,.8245,.911,.936)),
('zn-hydrolysis-expression',2,'Unnumbered reaction','Source Zn-aquo reaction with unknown delta',(.512,.704,.911,.799)),
('zn-dissolution-expression',3,'Unnumbered equilibrium','Source ZnO dissolution with unknown delta',(.512,.650,.911,.785))]
assets=[];images={}
for i,p,lab,title,bbox in crop_specs:
 if p not in images:images[p]=pdf[p-1].render(scale=3).to_pil().convert('RGB')
 im=images[p];box=tuple(round(v*(im.width if j%2==0 else im.height))for j,v in enumerate(bbox));crop=im.crop(box);dest=P/'reader-assets'/f'{i}.png';crop.save(dest)
 assets.append({'id':i,'label':lab,'title':title,'path':str(dest),'relative_path':'reader-assets/'+dest.name,'sha256':sha(dest),'source_sha256':HASH,'pdf_page':p,'printed_page':1788+p,'evidence':[ev(p,lab)],'render_engine':'pypdfium2','render_scale':3,'normalized_bbox':list(bbox),'pixel_bbox':list(box),'width':crop.width,'height':crop.height,'asset_kind':'selected_original_crop','contains_complete_source_page':False,'visual_author_review':'pending'})
for k in range(0,len(assets),4):
 subset=assets[k:k+4];contact=Image.new('RGB',(1440,1320),'#dddddd');d=ImageDraw.Draw(contact)
 for j,a in enumerate(subset):
  im=Image.open(a['path']);im.thumbnail((700,610));x=(j%2)*720+(720-im.width)//2;y=(j//2)*660+40;contact.paste(im,(x,y));d.text(((j%2)*720+14,(j//2)*660+8),a['id'],fill='black')
 contact.save(P/'private'/f'crop-contact-{k//4+1:02}.png')
write('original-assets-manifest.json',{'schema':'mattersyn-original-assets/1','author':AUTHOR,'source_id':SID,'created_at':NOW,'assets':assets,'public_approval':False,'whole_source_pages_are_private':True})

units=[]
for key,arr in [('fact',facts),('material',materials),('stock',stocks),('sample_context',contexts),('figure',figures),('equation',equations),('conflict',conflicts),('gap',gaps),('reference',refs)]:
 field={'fact':'facts','material':'materials','stock':'stocks','sample_context':'sample_contexts','figure':'figures','equation':'equations','conflict':'conflicts','gap':'missingness','reference':'references'}[key]
 for j,o in enumerate(arr):units.append({'id':f'{key}:{o["id"]}','kind':key,'source_object_id':o['id'],'path':'source-facts.json','json_pointer':f'/{field}/{j}','evidence':o.get('evidence',[]),'disposition':'extracted_main_source'})
for j,p in enumerate(protocols):
 units.append({'id':'protocol:'+p['id'],'kind':'protocol','source_object_id':p['id'],'path':'source-facts.json','json_pointer':f'/protocols/{j}','disposition':'extracted_main_source'})
 for k,o in enumerate(p['operations']):units.append({'id':'operation:'+o['id'],'kind':'operation','source_object_id':o['id'],'path':'source-facts.json','json_pointer':f'/protocols/{j}/operations/{k}','evidence':o['evidence'],'disposition':'extracted_main_source'})
units.append({'id':'table:table-1','kind':'table','source_object_id':'table-1','path':'source-tables.json','json_pointer':'/tables/0','evidence':table['evidence'],'disposition':'all_37_rows_185_data_cells_and_37_labels_transcribed'})
for j,r in enumerate(rows):units.append({'id':'table_row:'+r['sample_id'],'kind':'table_row','source_object_id':r['sample_id'],'path':'source-tables.json','json_pointer':f'/tables/0/rows/{j}','evidence':r['row_label_evidence'],'disposition':'transcribed_with_literal_units_and_ranges'})
units.append({'id':'footnote:table-1-a','kind':'footnote','source_object_id':'table-1-footnote-a','path':'source-tables.json','json_pointer':'/tables/0/footnotes/0','evidence':[ev(4,'Table 1 footnote a')],'disposition':'extracted_main_source'})
assert len({x['id']for x in units})==len(units)
counts={'facts':len(facts),'fact_quantities':sum(len(f['quantities'])for f in facts),'materials':len(materials),'stocks':len(stocks),'protocols':len(protocols),'operations':sum(len(p['operations'])for p in protocols),'sample_contexts':len(contexts),'table_rows':len(rows),'table_data_cells':185,'table_row_labels':37,'table_total_body_cells':222,'figures':len(figures),'equations_or_expressions':len(equations),'references':len(refs),'selected_original_crops':len(assets),'inventory_units':len(units),'source_conflicts_or_qualifications':len(conflicts),'gap_categories':len(gaps)}
write('source-inventory.json',{'schema':'mattersyn-source-inventory/1','source_id':SID,'author':AUTHOR,'created_at':NOW,'counts':counts,'inventory_units':units,'supporting_information_status':'declared_not_locally_verified','complete_supplied_main_inventory':True,'complete_main_plus_si_inventory':False,'source_table_scope':'all visible main Table 1 body cells and footnote; no SI table values inferred','main_page_count':11,'si_page_count':None,'si_expected':True,'independent_audit_status':'pending'})
pages=[]
for p,n in enumerate(A.PAGE_NOTES,1):
 if p==10:n='References continued, 21-56; cited studies retained as references only, not newly read source evidence.'
 if p==11:n='References 57-65 and footer; complete supplied-main scope, with no local SI read or inferred.'
 pages.append({'document_id':'main','pdf_page':p,'printed_page':1788+p,'source_sha256':HASH,'text_path':str(P/f'private/text/main-{p:02}.txt'),'text_sha256':sha(P/f'private/text/main-{p:02}.txt'),'image_path':str(P/f'source-render/main-{p:02}.png'),'image_sha256':sha(P/f'source-render/main-{p:02}.png'),'text_read':True,'native_page_visually_inspected':True,'reader':AUTHOR,'coverage_notes':n,'fact_ids':[f['id']for f in facts if any(e['pdf_page']==p for e in f['evidence'])],'asset_ids':[a['id']for a in assets if a['pdf_page']==p]})
write('page-coverage.json',{'schema':'mattersyn-page-coverage/1','author':AUTHOR,'created_at':NOW,'pages':pages,'main_read_pages':11,'main_visually_inspected_pages':11,'si_read_pages':0,'si_status':'declared_unlocated_not_claimed_read','complete_supplied_page_coverage':True,'complete_main_plus_si_coverage':False})
write('complete-source-payloads.json',{'schema':'mattersyn-complete-source-payloads/1','source_id':SID,'publication_scope':'PRIVATE ONLY: source PDFs, complete extracted text and full page images are not public selected assets','source_copies':copies,'documents':[{'document_id':'main','source_path':str(SOURCE),'source_sha256':HASH,'page_count':11,'text_files':[{'path':str(p),'sha256':sha(p)}for p in sorted((P/'private/text').glob('*.txt'))],'full_page_images':[{'path':p['image_path'],'sha256':p['image_sha256']}for p in pages]}],'supporting_information':{'status':'declared_unlocated','not_read':True}})
write('pairing-review.json',{'schema':'mattersyn-pairing/1','source_id':SID,'doi':DOI,'author':AUTHOR,'created_at':NOW,'main_identity':'Title/byline/DOI/printed pagination agree with intake','main_sha256':HASH,'main_page_count':11,'duplicate_copies_verified':True,'source_copies':copies,'si_status':'declared_unlocated_unverified','main_si_pairing_status':'cannot_pair_absent_local_candidate','si_declaration_evidence':[ev(9,'Associated Content')],'local_search_report':'local-source-search.json','complete_main_only_scope':True,'independent_audit_status':'pending'})
write('relevance-screening.json',{'schema':'mattersyn-relevance/1','author':AUTHOR,'source_id':SID,'status':'synthesis_recipe_present','evidence':[ev(7,'Laboratory and Microwave Synthesis'),ev(8,'SCFS/ACS/In Situ methods'),ev(4,'Table 1')],'reason':'Quantified precursor formulations, heating, sample variants and powder isolation are explicitly reported. SI absence limits completeness but does not erase the main recipes.','no_synthesis_recipe':False,'independent_audit_status':'pending'})
print(json.dumps(counts,indent=2))
