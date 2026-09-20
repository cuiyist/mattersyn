"""Manually curated after full main/SI text reading and visual inspection of all 9 pages."""
import json, sys, copy, hashlib, subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
SITE=ROOT/'recipe-atlas'
sys.path.insert(0,str(SITE/'scripts'))
from record_helpers import ev, fact, qty, record, material, operation, product, state, measurement
E=lambda loc:ev('fu2007',loc)
EXP='Main p.16030, Experimental Section / Sample Preparation'
e=E(EXP)
base=json.loads((SITE/'data/records/fu-2007-zno-s1.json').read_text(encoding='utf-8'))
base['revision']=3
base['sources'][0]['main_status']='All 5 main pages read in full and visually inspected, including all 7 figures.'
base['sources'][0]['si_status']='Matching SI verified by title/authors and main-text cross-references; all 4 pages read in full and visually inspected, including all 3 figures.'
scope='Full main/SI text and every page visually reviewed; all recipe variants, controls and figures inventoried in paper coverage. Canonical record is a named literature protocol, not an independently reproduced SOP or unique physical batch. Plot curves are preserved as original evidence, not digitized raw data.'
base['quality']['review_scope']=scope
base['context_links'].append({'label':'Full-paper coverage and characterization archive','url':'paper-review.html?id=fu2007','relation':'source_coverage'})
base['quality']['conflicts'].append('Main p.16032 prints the hole effective mass as 1.8 m_h; possible self-referential typographical error. No corrected numerical mass is supplied here.')
def add_m(r,mid,sample,prop,value,unit,tech,loc,conditions='',status='reported',qualifier='',approx=False):
    ee=E(loc)
    r['measurements'].append(measurement(mid,sample,prop,qty(value,unit,ee,status=status,qualifier=qualifier,approximate=approx),tech,ee,conditions))
def add_range(r,mid,sample,prop,lo,hi,unit,loc,conditions):
    ee=E(loc);r['measurements'].append(measurement(mid,sample,prop,qty(unit=unit,evidence=ee,minimum=lo,maximum=hi), 'ATR-FTIR',ee,conditions))
add_m(base,'s1-ftir-c-c','fu2007-s1','ftir_band',1640,'cm^-1','ATR-FTIR','Main pp.16030–16031, Fig.3a','Authors assign C=C stretching in OA; dried purified particles.')
add_range(base,'s1-ftir-interface','fu2007-s1','ftir_band_region',1400,1600,'cm^-1','Main pp.16030–16031, Fig.3a','Two bands; authors assign C=O stretching in ZnO/OA surface complexes. Exact individual positions not supplied.')
add_range(base,'s1-ftir-nh-oh','fu2007-s1','ftir_band_region',3300,3600,'cm^-1','Main pp.16030–16031, Fig.3a','Authors assign DEA N–H and surface O–H; not quantitative ligand coverage.')
for mid,val,prop in [('zno-slope',113.8,'quantum_yield_calibration_slope'),('reference-slope',82.6,'quantum_yield_reference_slope'),('zno-r2',.998,'quantum_yield_fit_r_squared'),('reference-r2',.995,'quantum_yield_reference_fit_r_squared')]:
    add_m(base,mid,'fu2007-s1',prop,val,'plot units' if 'slope' in mid else 'dimensionless','Relative PL quantum-yield calibration','SI p.S3, Part2, Fig.S2','Five optical dilutions per material; these are not five independently synthesized batches. Quinine sulfate reference in 0.5 M sulfuric acid.')
records=[base]
def variant(label,title):
    r=copy.deepcopy(base);r['record_id']='fu-2007-zno-'+label.lower();r['revision']=1;r['record_type']='protocol_variant';r['title']=title
    r['lineage']['parent_record_id']=base['record_id'];r['measurements']=[];r['quality']['conflicts']=[]
    old='fu2007-s1';new='fu2007-'+label.lower()
    r['products']=[product(new,'ZnO',e,link='explicit',state='aqueous-'+label.lower(),notes=['Author-defined sample '+label+'; parent links describe protocol derivation, not reuse of an S1 physical batch.'])]
    r['products'][0]['source_sample_label']=label
    for s in r['material_states']:
        if s['id']=='aqueous-s1':s['id']='aqueous-'+label.lower();s['name']='Aqueous '+label+' dispersion'
    r['operations'][-1]['outputs']=['aqueous-'+label.lower()];r['operations'][-1]['label']='Disperse final '+label+' QDs in water'
    for o in r['operations']:o['description']+=' Inherited from the common preparation framework where not explicitly changed for '+label+'; no independent numerical repeat is claimed.'
    r['quality']['review_scope']=scope+' Unchanged preparation steps are inherited from the paper’s common framework.'
    return r
s2=variant('S2','ZnO aqueous synthesis without oleic acid: Fu et al. (2007), S2')
s2['method']='Aqueous solution synthesis with diethanolamine, without oleic acid'
s2['materials']=[m for m in s2['materials'] if m['id']!='oleic_acid']
comb=s2['operations'][2];comb['inputs'].remove('oleic_acid');comb['label']='Combine DEA and zinc stocks without OA'
for key in ['oleic_acid_amount','nominal_OA_to_Zn_ratio']:comb['parameters'].pop(key)
s2['material_states'][0]['parent_ids'].remove('oleic_acid');s2['material_states'][0]['name']='Both aqueous stocks combined without OA'
s2['products'][0]['phase']=fact('wurtzite',E('Main p.16030, Fig.1'))
s2['products'][0]['surface']=fact('DEA and hydroxyl association inferred by authors from FTIR',E('Main pp.16030–16031, Fig.3b'),status='author_derived')
s2['quality']['missing_fields']=[x for x in s2['quality']['missing_fields'] if 'OA mass' not in x and '+/-0.4' not in x]+['definition of +/-0.5 nm size spread','early 60 C / about 20 min sample timing origin relative to the common 30 min room-temperature stirring step','dry-powder preparation conditions']
add_m(s2,'s2-diameter','fu2007-s2','diameter',5.0,'nm','HRTEM','Main pp.16030–16032, Fig.2b','Mean particle diameter; ±0.5 nm spread definition not stated.')
add_m(s2,'s2-spread','fu2007-s2','diameter_spread',.5,'nm','HRTEM','Main p.16030, Fig.2b','Definition of ± spread not supplied.')
add_m(s2,'s2-onset','fu2007-s2','optical_absorption_onset',3.67,'eV','UV–visible absorption','Main pp.16031–16032, Fig.5b','Extrapolation of (alpha h nu)^2 versus photon energy.')
add_m(s2,'s2-modeled-gap','fu2007-s2','modeled_optical_gap',3.68,'eV','Author confinement calculation','Main p.16032, Eq.1','Model value, not independently measured band structure.',status='author_derived')
for mid,lo,hi,assign in [('cncoh',1000,1100,'C–N and C–OH'),('nh',1600,1650,'N–H bending'),('ch',2850,3000,'C–H'),('nhoh',3300,3600,'N–H and O–H')]:
    add_range(s2,'s2-ftir-'+mid,'fu2007-s2','ftir_band_region',lo,hi,'cm^-1','Main pp.16030–16031, Fig.3b','Authors’ assignments: '+assign+'.')
s2['material_states'] += [state('s2-dry-powder','S2 dry powder; drying conditions unspecified',['aqueous-s2'],'product'),state('s2-early-60c','Early S2-related sample at 60 C, about 20 min after reaction start',[],'aliquot')]
for sid,st,label,link in [('fu2007-s2-dry','s2-dry-powder','S2 dry powder','explicit'),('fu2007-s2-early','s2-early-60c','SI low-temperature early sample','general_context')]:
    p=product(sid,'ZnO',E('Main p.16032 Fig.6a; SI p.S2 Part1 Fig.S1'),link=link,state=st,notes=['Characterization state or aliquot, not a separate complete synthesis recipe.']);p['source_sample_label']=label
    if sid.endswith('dry'):p['parent_sample_id']='fu2007-s2'
    s2['products'].append(p)
for val,qual in [(392,'strong UV emission'),(450,'weak blue emission'),(479,'weak blue emission')]:
    add_m(s2,'s2-dry-pl-'+str(val),'fu2007-s2-dry','photoluminescence_peak',val,'nm','PL','Main p.16032, Fig.6a','Dry powder, distinct from aqueous S2; '+qual)
add_m(s2,'s2-early-diameter','fu2007-s2-early','diameter',3.,'nm','HRTEM','SI p.S2, Part1, Fig.S1','60 C; about 20 min after starting the reaction, not a 20 min hold at 60 C. Relation of timing origin to main recipe is unresolved.',approx=True)
s2['products'][0]['notes']+=['Authors describe aqueous S2 as nonluminescent while Fig.4a displays weak traces scaled by 10. No zero quantum yield or absolute zero emission is encoded.']
records.append(s2)
s3=variant('S3','ZnO aqueous synthesis with ammonia replacing DEA: Fu et al. (2007), S3')
s3['method']='Aqueous solution synthesis with ammonia and oleic acid'
s3['materials']=[m for m in s3['materials'] if m['id']!='diethanolamine']+[material('ammonia','ammonia','NH3','base','synthesis',e,notes=['Ammonia replaces DEA; charge, formulation and concentration are not given. DEA mass and stock molarity must not be copied.'])]
st=s3['stocks'][0];st['id']='ammonia-stock';st['name']='Ammonia replacement reagent; formulation unspecified';st['components']=[{'material_id':'ammonia','quantities':{'amount':qty(unit='mmol',evidence=e)}}];st['concentrations']={'ammonia':qty(unit='mmol/L',evidence=e)};st['preparation_operation_ids']=['prepare-ammonia-input'];st['scope']='Ammonia substitutes for DEA. Neither concentration nor preparation volume is explicitly restated; no DEA values transferred.'
s3['operations'][0]=operation('prepare-ammonia-input','prepare_reagent','Prepare ammonia replacement input',e,['ammonia'],['ammonia-stock'],parameters={'amount':qty(unit='mmol',evidence=e),'volume':qty(unit='mL',evidence=e),'concentration':qty(unit='mmol/L',evidence=e)},description=st['scope'])
for o in s3['operations']:
    o['depends_on']=['prepare-ammonia-input' if x=='prepare-dea-stock' else x for x in o['depends_on']]
    o['inputs']=['ammonia-stock' if x=='dea-stock' else x for x in o['inputs']]
for st in s3['material_states']:st['parent_ids']=['ammonia-stock' if x=='dea-stock' else x for x in st['parent_ids']]
s3['operations'][2]['label']='Combine ammonia input, zinc stock and OA'
for key in ['nominal_DEA_to_Zn_ratio','nominal_water_charge_sum']:s3['operations'][2]['parameters'].pop(key)
s3['quality']['missing_fields']+=['ammonia charge, concentration, formulation and replacement-stock volume','S3 size and sample-specific phase evidence']
s3['quality']['missing_fields']=[x for x in s3['quality']['missing_fields'] if '+/-0.4' not in x]
s3['products'][0]['notes']+=['Weak broad visible PL in Fig.6a, multiplied by 10 for display; no quantum yield or particle diameter supplied. S1 phase/size/QY are not inherited.']
records.append(s3)
s4=variant('S4','ZnO aqueous synthesis with 4.0 mM zinc stock: Fu et al. (2007), S4')
z=s4['stocks'][1];z['concentrations']['zinc_nitrate']=qty(4.0,'mmol/L',E('Main p.16030; SI p.S4 Part3 Fig.S3'))
z['components'][0]['quantities']['mass']=qty(unit='mg',evidence=e,qualifier='S4 salt mass not supplied; 37.2 mg belongs to 2.5 mM S1.')
z['components'][0]['quantities']['nominal_zinc_amount']=qty(.2,'mmol',e,status='calculated',derivation='4.0 mmol/L × inherited 0.050 L stock-water charge',basis='Conditional on unchanged common preparation volume')
s4['operations'][1]['parameters']['precursor_mass']=copy.deepcopy(z['components'][0]['quantities']['mass']);s4['operations'][1]['parameters']['stock_concentration']=copy.deepcopy(z['concentrations']['zinc_nitrate'])
for k,v in [('nominal_DEA_to_Zn_ratio',1.25),('nominal_OA_to_Zn_ratio',1.75)]:s4['operations'][2]['parameters'][k]=qty(v,'mol/mol',e,status='calculated',derivation=('0.25' if 'DEA' in k else '0.35')+' mmol / (4.0 mmol/L × inherited 0.050 L)',basis='Conditional on inherited stock-water volume')
for m in s4['materials']:
    if m['id']=='zinc_nitrate_hexahydrate':m['notes']=[x for x in m['notes'] if '37.2 mg' not in x]+['S4 uses 4.0 mM stock; mass not supplied.']
s4['quality']['missing_fields']=[x for x in s4['quality']['missing_fields'] if '+/-0.4' not in x]+['S4 precursor mass, size-spread definition and sample-specific phase measurement']
add_m(s4,'s4-particle-size','fu2007-s4','particle_size',4.2,'nm','HRTEM','Main p.16033; SI p.S4 Fig.S3','Author calls this average particle size; no explicit diameter definition or spread for S4.')
add_m(s4,'s4-surface-area-reduction','fu2007-s4','relative_surface_area_reduction',9.5,'%','Author geometric estimate','Main p.16033','Relative to S1, under authors’ fixed-amount argument; not a BET measurement.',status='author_derived')
add_m(s4,'s4-pl-reduction','fu2007-s4','relative_photoluminescence_intensity_reduction',28.8,'%','PL','Main p.16033, Fig.6a','Relative to S1 under compared measurement conditions; not a QY or synthesis yield.')
records.append(s4)
for suffix,title,parent,reagent,formula,volume,times in [
 ('s2-oa-post-treatment','OA post-treatment of as-prepared S2 ZnO dispersion','S2','oleic_acid','C18H34O2',20,[.5,1.5,2.5,3.5]),
 ('s1-hcl-perturbation','Dilute-HCl perturbation of S1 ZnO dispersion','S1','hydrochloric_acid','HCl',None,[1,3,8])]:
    loc='Main p.16033, Fig.6'+('b' if parent=='S2' else 'c');ee=E(loc)
    r=record('fu-2007-zno-'+suffix,title,'ZnO','Metal oxides','Post-synthesis ligand/interface control',copy.deepcopy(base['sources'][0]),loc,kind='procedure');r['collection']='reviewed_literature';r['material']=copy.deepcopy(base['material']);r['lineage']['recipe_family']='fu2007-zno-post-treatment';r['lineage']['parent_record_id']='fu-2007-zno-'+parent.lower()
    r['materials']=[material('starting-dispersion','As-prepared '+parent+' ZnO dispersion','ZnO','starting_dispersion','post_treatment',ee,quantities={'volume':qty(volume,'mL',ee)},notes=['Protocol dependency on '+parent+'; no physical batch identity or concentration inferred.']),material(reagent,reagent.replace('_',' '),formula,'post_treatment_reagent','post_treatment',ee,quantities={'amount':qty(.35 if parent=='S2' else None,'mmol',ee)},notes=[] if parent=='S2' else ['Several drops of diluted HCl; concentration, drop volume and exact number unknown.'])]
    r['material_states']=[state('treated-series','Treated dispersion aliquot series',['starting-dispersion',reagent],'mixture')]
    r['operations']=[operation('add-reagent','add','Add '+reagent.replace('_',' ')+' to '+parent,ee,['starting-dispersion',reagent],['treated-series'],stage='surface_exchange',parameters={'starting_dispersion_volume':qty(volume,'mL',ee),'reagent_amount':qty(.35 if parent=='S2' else None,'mmol',ee)},description='Addition formulation and detailed mixing conditions are not given.'),operation('heat-treatment','heat','Heat treatment and time-series sampling',ee,['treated-series'],['treated-series'],depends=['add-reagent'],stage='surface_exchange',parameters={'temperature':qty(80,'C',ee),'total_duration':qty(unit='h',evidence=ee)},description='Figure provides discrete sampling times, not independent synthesis runs or a universally specified endpoint.')]
    for i,t in enumerate(times):
        sid='fu2007-'+suffix+'-'+str(t).replace('.','p')+'h';p=product(sid,'ZnO',ee,link='explicit',state='treated-series',notes=['Aliquot in a common treatment series; not an independent synthesis experiment.']);p['source_sample_label']=parent+' '+str(t)+' h';r['products'].append(p)
        add_m(r,'sampling-'+str(i),sid,'treatment_sampling_time',t,'h','PL/PLE',loc,('PL/PLE increase with treatment time' if parent=='S2' else 'PL/PLE decline with heating after acid addition; dissolution/interface loss is an author interpretation')+'; quantitative curves retained as original Fig.6, not digitized.')
    r['quality']['review_scope']=scope;r['quality']['experimental_outcome']='reported_product';r['quality']['requested_tasks']=['partial_protocol'];r['quality']['missing_fields']=['starting particle concentration and unique batch identity','mixing rate, ramp and atmosphere','final recovery conditions and quantitative product size/phase']+(['HCl concentration, volume and drop count','starting S1 dispersion volume'] if parent=='S1' else ['exact processing stage of the as-prepared S2 input','OA formulation'])
    r['context_links']=copy.deepcopy(base['context_links']);records.append(r)
for r in records:
    for m in r['measurements']:
        # Preserve source value while correcting no content by automated chemistry assumptions.
        assert m['evidence']
can=OUT/'canonical';can.mkdir(exist_ok=True)
for r in records:(can/(r['record_id']+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

figs=[
 ('fig1','main',2,[145,79,532,399],'XRD of S1 and S2; wurtzite assignment; broad signal near 25 degrees attributed to glass substrate.',['S1','S2'],'experimental'),
 ('fig2','main',2,[682,82,1020,574],'HRTEM panels a=S1, b=S2, both with 10 nm scale bars; mean diameters 3.8±0.4 and 5.0±0.5 nm.',['S1','S2'],'experimental'),
 ('fig3','main',2,[653,607,1049,916],'ATR-FTIR of S1 and S2; OA/DEA/hydroxyl assignments are author interpretations.',['S1','S2'],'experimental'),
 ('fig4','main',3,[662,82,1064,981],'S1 PL/PLE; luminescence photograph; photostability monitored at 440 nm under 350 nm UV, 130 µW/cm². Plot extends to 48 h.',['S1'],'experimental'),
 ('fig5','main',4,[133,83,541,688],'UV–visible absorption spectra (a) and extrapolated absorption onsets (b) of S1/S2. S2 absorption in panel a is scaled by ten.',['S1','S2'],'experimental'),
 ('fig6','main',4,[631,84,1066,1055],'a: PL of S1, dry S2 powder, S3 (multiplied by ten) and S4; b: OA addition to S2 at .5/1.5/2.5/3.5 h; c: S1/HCl at 1/3/8 h and baseline.',['S1','S2 dry powder','S3','S4','S2 OA-treated series','S1 acid-treated series'],'experimental'),
 ('fig7','main',5,[659,82,1033,450],'Proposed interface-state energy diagram; excitation near 3.54 eV and emission near 2.82 eV. An author mechanistic model, not a measured atomic/electronic structure.',['S1'],'author_model'),
 ('figS1','si',2,[389,146,805,489],'Early-stage HRTEM at 60 C, about 20 min after starting; average diameter about 3 nm; 10 nm scale bar. Timing origin relative to main recipe unresolved.',['S2-related early sample'],'experimental'),
 ('figS2','si',3,[310,145,864,594],'Five-dilution relative-QY fits; ZnO slope113.8,R².998; quinine sulfate slope82.6,R².995. 76% QY calculation.',['S1','quinine sulfate reference'],'calibration'),
 ('figS3','si',4,[389,102,805,427],'S4 HRTEM, 5 nm scale bar; 4.0 mM starting zinc stock, average size4.2 nm reported in main text.',['S4'],'experimental')]
sources={role:ROOT/'downloaded_papers'/name for role,name in [('main','10.1021_ja075604i.pdf'),('si','10.1021_ja075604i_si_1.pdf')]}
documents=[]
sections={'main':[['Abstract','Introduction'],['Experimental','Results: XRD/TEM/FTIR'],['Results: FTIR/PL/photostability','Confinement model'],['Results: absorption, dry-powder PL','Comparison controls'],['Post-treatment controls','Mechanistic model','Conclusion','References']], 'si':[['Title and author identity'],['Part1 early-stage HRTEM'],['Part2 relative quantum yield'],['Part3 S4 HRTEM']]}
for role,path in sources.items():
    documents.append({'role':role,'source_path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'page_count':len(sections[role]),'pages':[{'page':i+1,'text_read':True,'visual_review':True,'sections':ss,'unresolved':[]} for i,ss in enumerate(sections[role])]})
coverage={'schema_version':'paper-coverage-1.0','paper_id':'fu2007','doi':'10.1021/ja075604i','title':base['sources'][0]['title'],'documents':documents,'main_si_match':{'status':'verified','basis':'Title, authors, Part1–3 references and corresponding figures in main article match.'},'coverage_status':'full_text_and_visual_review_complete','independent_audit':'pending','recipe_inventory':[],'figures':[],'tables':[],'characterization_inventory':[], 'evidence_conflicts':base['quality']['conflicts'], 'referenced_methods':[], 'remaining_gaps':[]}
for r in records:coverage['recipe_inventory'].append({'id':r['record_id'],'label':r['title'],'record_ids':[r['record_id']],'status':'extracted_with_reported_gaps','source_locators':[EXP] if r['record_type']!='procedure' else ['Main p.16033 Fig.6b/c'],'gaps':r['quality']['missing_fields']})
coverage['recipe_inventory'] += [
 {'id':'early-nucleation','label':'Early 60 C sample','record_ids':[s2['record_id']],'status':'contextual_aliquot','source_locators':['SI p.S2 Fig.S1'],'gaps':['Timing origin relative to main framework unresolved; not a standalone 60 C/20 min recipe.']},
 {'id':'blank-controls','label':'DEA-only, OA-only and combined aqueous blank controls','record_ids':[],'status':'qualitative_controls','source_locators':['Main p.16031'],'gaps':['No complete quantities or acquisition protocol; authors report absence of the characteristic blue emission.']},
 {'id':'dry-s2','label':'Dry S2 powder for PL','record_ids':[s2['record_id']],'status':'characterization_state','source_locators':['Main p.16032 Fig.6a'],'gaps':['Drying conditions unspecified.']},
 {'id':'relative-qy','label':'Relative quantum-yield calibration','record_ids':[base['record_id']],'status':'measurement_procedure','source_locators':['SI p.S3 Part2 Fig.S2'],'gaps':['Exact concentrations of five optical dilutions and raw integrated intensities are not listed.']}
]
for id,role,page,box,caption,samples,kind in figs:
    coverage['figures'].append({'id':id,'document_role':role,'page':page,'caption_paraphrase':caption,'sample_links':samples,'evidence_kind':kind,'review_status':'visually_verified','source_sha256':next(d['sha256'] for d in documents if d['role']==role),'crop':{'path':'figures/'+id+'.png','coordinate_system':'pixels on 140 dpi full-page render','bbox':box,'output_dpi':300},'quantitative_extraction':'Explicit text and labelled values extracted; continuous plotted traces are not digitized.'})
coverage['characterization_inventory']=[
 {'technique':'XRD','samples':['S1','S2'],'details':'Freeze-dried products; Rigaku D/max2500v/pc; wurtzite JCPDS89-1397. Broad ~25° signal attributed to glass substrate. No refined atomic coordinates or quantitative phase fraction.','source_locators':['Main p.16030 Fig.1']},
 {'technique':'HRTEM','samples':['S1','S2','S4','early sample'],'details':'FEI Tecnai G2 F20 field-emission microscope, 200 kV; diluted dispersion on carbon-coated copper grids. No particle count or ± definition. SI early particles described as stable under strong beam, dose not specified.','source_locators':['Main p.16030 Fig.2','SI p.S2 Fig.S1','SI p.S4 Fig.S3']},
 {'technique':'ATR-FTIR','samples':['S1','S2'],'details':'Nicolet470; purified dried particles. S1 1640,1400–1600,3300–3600 cm^-1 bands; free-OA1700–1725 not observed. S2 1000–1100,1600–1650,2850–3000,3300–3600. Assignments are author interpretations. Prior bare-ZnO450 cm^-1 comes from reference15, not a new measurement.','source_locators':['Main pp.16030–16031 Fig.3']},
 {'technique':'UV–visible absorption','samples':['S1','S2'],'details':'Philips3000; squared alpha*h*nu versus h*nu extrapolation gives3.94/3.67 eV. Model3.92/3.68 eV is kept separate.','source_locators':['Main pp.16030–16032 Fig.5a']},
 {'technique':'PL/PLE','samples':['S1','S2','S3','S4','post-treatment series'],'details':'Hitachi F-4500; direct aqueous room-temperature measurements. Excitation350 nm; PLE detection432 nm is not the440 nm PL maximum. Fig.4a aqueous S2 curves scaled×10; Fig.6a S3 scaled×10, while the S2 curve is dry powder.','source_locators':['Main p.16030','Main Figs.4–6']},
 {'technique':'Relative quantum yield','samples':['S1','quinine sulfate standard'],'details':'Quinine sulfate in0.5 M H2SO4, reference yield.55; five optical dilutions each with absorbance<.1 at350 nm; both refractive indices1.33; quartz1.00 cm cell;2.5 nm excitation/emission slits. Slopes113.8/82.6, R².998/.995; yield.55×1.38=.76. Calibration chemicals are not synthesis precursors.','source_locators':['SI p.S3 Part2 Fig.S2']},
 {'technique':'Photostability','samples':['S1'],'details':'350 nm UV130 µW/cm², PL monitored440 nm.9.4% loss in first6 h then nearly constant. Plot spans48 h; does not establish dark-storage stability.','source_locators':['Main p.16031 Fig.4c']},
 {'technique':'Mechanistic interpretation','samples':['S1','comparison controls'],'details':'OA-associated ZnO surface/interface states proposed; DEA influences formation but blanks do not reproduce blue emission. Acid/ligand perturbations support an interface interpretation but do not identify unique atomic defects. The confinement equation cites Kayanuma1988; prior redshift bounds cite other work. Fig.7 is an author model.','source_locators':['Main pp.16031–16033 Eq.1 Figs.6–7']}
]
coverage['referenced_methods']=[{'reference':'19: Kayanuma, Physical Review B1988,38,9797','purpose':'Confinement model used for theoretical gap estimate','status':'Bibliographic reference and use inventoried; cited full paper not reviewed in this batch.'},{'reference':'15: Wang et al., Nanotechnology2003,14,11','purpose':'Bare-ZnO infrared comparison;450 cm^-1 is contextual prior work','status':'Cited full paper not reviewed in this batch.'}]
coverage['remaining_gaps']=['No raw spectra, raw microscopy, instrument files or experimentally refined CIF in the supplied documents.','Continuous curves are retained as original figures; no numerical trace digitization performed.','Preparation omissions in recipe inventories remain unknown, rather than inferred.','Referenced background studies have not all been retrieved and read.','No tables, SAED pattern or Raman measurement appears in the supplied main/SI.','Source reading is complete for this paper; independent extraction audit is tracked separately.']
(OUT/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'review.md').write_text('# Fu et al.2007 — full-paper review\n\nAll5 main pages and4 matching SI pages were read in full and visually inspected. All7 main figures and3 SI figures are inventoried. Four synthesis conditions (S1–S4), two post-treatment series, early-stage sampling, dry-powder characterization, blank controls and relative-QY calibration remain distinct.\n\nThe main recipe has operational omissions; a fully read paper is not automatically a complete experimental SOP or training-eligible exact-structure pair. See coverage.json for all techniques, sample links, cited-method gaps and figure provenance.\n\nS3 ammonia amount is unknown; S4 zinc salt mass is unknown. S1 numeric outcomes are not inherited into variants. Early60 C/20 min is not a20 min isothermal hold. S2 dry-powder emission is not aqueous S2 emission. QY calibration standards do not enter the precursor list.\n',encoding='utf-8')
if '--render' in sys.argv:
    poppler=Path(r'[local path redacted]')
    (OUT/'figures').mkdir(exist_ok=True)
    for id,role,page,box,*rest in figs:
        x,y,x2,y2=[round(v*300/140) for v in box]
        subprocess.run([str(poppler),'-f',str(page),'-l',str(page),'-singlefile','-r','300','-x',str(x),'-y',str(y),'-W',str(x2-x),'-H',str(y2-y),'-png',str(sources[role]),str(OUT/'figures'/id)],check=True,stdout=subprocess.DEVNULL)
    for f in coverage['figures']:f['crop']['sha256']=hashlib.sha256((OUT/f['crop']['path']).read_bytes()).hexdigest()
    (OUT/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Authored',len(records),'canonical records and',len(figs),'figure inventory items.')
