import json, hashlib, datetime
from pathlib import Path
B=Path(__file__).parent
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
manifest=json.loads((B/'source-render-manifest.json').read_text(encoding='utf-8'))
units=[]
def add(id,role,page,loc,kind,claim,disposition='retain_with_source_scope',**kw):
    units.append(dict(id=id,source_unit_id=id,source_role=role,pdf_page=page,printed_page=(5342+page if role=='main' else ('cover' if page==1 else 'S'+str(page-1))),locator=loc,kind=kind,claim=claim,disposition=disposition,**kw))
def m1(id,loc,kind,claim,**kw):add(id,'main',1,loc,kind,claim,**kw)
def m2(id,loc,kind,claim,**kw):add(id,'main',2,loc,kind,claim,**kw)
m1('identity','Title/byline/banner/footer','identity','Kinetics of II-VI and III-V Colloidal Semiconductor Nanocrystal Growth: “Focusing” of Size Distributions. Xiaogang Peng, J. Wickham, A. P. Alivisatos. JACS1998,120,5343–5344; received1998-02-18; online1998-05-14; issue21 verified on page2; terminal code JA9805425 and SI DOI bind10.1021/ja9805425.')
for i,t in enumerate([
'Prior preparations from molecular precursors encompass II-VI CdS/CdSe and III-V InP/InAs; cited references1–16, not four new recipes in this paper.',
'Cited previous strategy: extended nucleation/growth at moderate180–300°C yields broad sizes subsequently sortable; references5/6. These are not current recipe temperatures.',
'Cited previous strategy: rapid350°C injection separates nucleation from cooler growth, sensitive to initial kinetics and not previously possible in III-Vs; reference7. Current CdSe recipe explicitly360°C, not350°C.',
'Reiss theory of diffusion-limited size focusing in micron colloids (ref17), and size-dependent surface energy/Gibbs–Thomson at nanoscales (refs18–20) motivate this study.'
],1):m1(f'm1-context-{i:02}','Introduction, left column','cited_context',t,disposition='context_not_current_experiment')
for i,t in enumerate([
'CdSe/InAs band-edge luminescence energy is used as a size proxy; energy–size relation previously calibrated by TEM, refs5/7/9.',
'PL-to-size conversion assumes delta-function emission for each single size.',
'PL-to-size conversion assumes equal emission efficiency across sizes.',
'Authors state both assumptions systematically overestimate real size-distribution widths. Preserve as an author-method limitation, not corrected widths.',
'Only average size (first moment) and variance (second moment) reported; third moment/asymmetry is not resolved and requires more accurate sizing.'
],1):m1(f'm1-pl-{i:02}','Right column, PL sizing paragraphs','measurement_method',t)
cdse_ops=[
('to-po-charge','chemical_inventory','Trioctylphosphine oxide (TOPO),4g in growth vessel; source does not provide supplier/purity.'),
('heat','operation','Heat4gTOPO to360°C with Ar flowing; rapidly stirred hot solution at injection; no heating duration or pressure.'),
('stock','stock','Cold stock comprises Se:Cd(CH3)2:tributylphosphine=2:5:100 by mass. Exact stock preparation/speciation, totalstock mass, temperature and componentmolarity not reported; tributylphosphine is not TOP.'),
('initial-injection','operation','Quickly inject2.4mL coldstock into hotTOPO, injectionduration<0.1s; retain strict upper bound rather than0.1sexact.'),
('temperature-drop','condition','Injection lowers temperature to300°C; distinct from360°C preinjection. No measured cooling curve/ramp/bath specified.'),
('aliquot','operation','At various intervals withdraw0.2mL reactionmixture aliquots; distinguish an aliquot from whole reaction batch.'),
('precipitate','operation','Precipitate each0.2mL aliquot in2mL methanol; not wholebatch2mLworkup.'),
('purification','operation','Mass and particleyield measured after purification from excessTOPO/byproducts/solvent; purification procedure/cycles not given, so no invented centrifugation or washes.'),
('redissolve','operation','Redissolve nanocrystals in toluene for UV–vis and PL spectra; toluene volume not given.'),
('optical-density','condition','Optical density0.09±0.02 for all CdSe PLsamples within footnote21; do not transfer to InAs without source support.'),
('reinjection','operation','190min after firstinjection slowly inject0.8mLstock into same reactionmixture; slowduration/rate not quantified, not independent new batch.'),
('missing','missingness','No numerical gasflow, pressure, vesselgeometry, stirrate, precursorpurity, heatingtime, exact coldstocktemperature, finalbatchisolation, storage or termination specified in supplied main/SI.')]
for s,k,t in cdse_ops:m1('m1-cdse-'+s,'Footnote21, p5343',k,t)
inas_ops=[
('indium-stock','stock','Prepare concentrated InCl3·TOP solution by heating0.33gInCl3 per mL distilledTOP to260°C under argon; basis is amount per solventvolume, not verified0.33g/mL finalsolution.'),
('indium-storage','operation','Cool prepared InCl3·TOP solution and take into drybox forstorage; storage temperature/duration unreported; do not inherit −35°C from Murray.'),
('top-charge','chemical_inventory','2gTOP is the separate growthmedium; TOP denotes trioctylphosphine, distinct from CdSe tributylphosphine and TOPO.'),
('heat','operation','Heat2gTOP to300°C; footnote givesAr explicitly for InCl3·TOP preparation, not separately measured growthvessel atmosphere/flow.'),
('stock','stock','Cold injectionstock has TMS3As:InCl3:TOP=1:1.1:2.8 by mass; TMS3As denotes tris(trimethylsilyl)arsine. Mixingtime, preparationdetails, and exact amount of prepared InCl3·TOP stock consumed are unreported.'),
('initial-injection','operation','Rapidly inject1mLcoldstock into300°C hotTOP in<0.1s; strictupperbound.'),
('drop','condition','Injection initially lowers temperature to250°C; not the continued growthtemperature.'),
('growth','condition','Growth continues at260°C; distinct temperature stage after250°Cinitialdrop; ramp/durationunspecified.'),
('aliquots','operation','Withdraw aliquots at varioustimeintervals and dilute in toluene; aliquotvolumeunreported. No CdSe0.2mL/methanolprocedure inherited.'),
('spectra','measurement_method','UV–vis and PLspectra recorded in toluene; dilutionvolume and opticaldensitynot reported forInAs.'),
('reinjection1','operation','Additional0.5mL injection after23min into same InAsgrowthsequence; source callsadditionalinjections, stocklink contextual but ratesnot stated.'),
('reinjection2','operation','Additional0.8mL injection after158min into same sequence; time interpretedelapsedfrominitialinjection, not+158min after second.'),
('missing','missingness','InAs suppliedscope lacks finalisolation, washing, purification, vesselgeometry, stirrate, pressure, numericalgrowthgasflow, stockpurities, storageconditions/duration, injectionratesafterfirst and exact sampletimejoin.')]
for s,k,t in inas_ops:m1('m1-inas-'+s,'Footnote22, p5343',k,t)
for i,t in enumerate([
'One CdSe growth experiment supplies Figures1/2left; initial inferreddiameter2.1nm and standarddeviation20%.',
'First22min: inferredmean diameter2.1→3.3nm while relative standarddeviation20→7.7%; same kinetictrajectory.',
'Subsequentperiod up to190min: mean3.3→3.9nm and widthbroadens to10.6%; growthslows.',
'A secondinjection increasesgrowthrate and refocuses distribution to8.7%; body does not assign exact8.7% endpointtime.',
'Particleyielddata indicate approximately constant particlecount duringfocusing/refocusing and decliningcount duringdefocusing; no numerical counts/yields tabulated.',
'Monomer concentration inferred from particleyield drops duringfocusing/refocusing and staysapproximatelyconstant duringdefocusing; no numerical concentrationseries supplied.',
'Similar kinetics reported forInAs Fig2right; qualitative highyield/facetedparticles statement follows, with actualTEMFig3 specificallyCdSe. Do not fabricate numerical yield or assign Fig3 toInAs.',
'Authors interpret nucleation as rapidafterinjection untiltemperature/monomerconcentration belowcriticalthreshold; no numerical nucleationtime or thresholdconcentration measured.'
],1):m1(f'm1-growth-{i:02}','Right column, growthresults and followingparagraph','reported_observation' if i<8 else 'author_interpretation',t)
m1('m1-eq1-expression','Rightcolumn Gibbs–Thomson equation','equation','Sr=Sb exp(2σVm/rRT); unnumbered expression in source; retain original rendering and symbols.',expression='S_r = S_b exp(2 σ V_m / (r R T))')
m1('m1-eq1-symbols','Rightcolumn equationdefinitions','equation_context','Sr andSb=nanocrystal andbulk solubility;σ=specificsurfaceenergy;r=nanocrystalradius;Vm=molarmaterialvolume;R=gasconstant;T=temperature. Theoryassumesfixedmonomerconcentration/diffusionratelimiting; no fittedconstants supplied.')
m2('m2-fig1-overview','Figure1 andcaption','figure','Room-temperature CdSe PL andabsorption spectra from the same examplegrowth; secondmonomerinjection at190min. PLnormalized, absorptionarbitraryunits, notquantumyield.')
for t in ['0.2','1.0','12','35','55','190','210','240']:
    m2('m2-fig1-time-'+t.replace('.','p'),'Figure1 labeledtrace t='+t+'min','spectrum','Paired normalizedPL/absorption traces labeled t='+t+'min in sameCdSetrajectory; no tabulatedexactpeakvalues or independentbatch.',time_min=float(t))
m2('m2-fig1-axes','Figure1 axes','figure_metadata','PL/absorptionxaxes Energy(eV); PLticks1.8,2.2,2.6 andabsorptionticks2,2.5,3. No digitizedcurvevalues asserted; visibleoffset traces retained.')
m2('m2-fig2-cdse','Figure2 leftpanels andcaption','figure','CdSe mean size(nm)andstandarddeviation(%)versustime(minutes), extractedfromFig1PL; arrowsinitial/secondaryinjections. Do not claimdirectTEM or independentrecordperpoint.')
m2('m2-fig2-inas','Figure2 rightpanels andcaption','figure','InAs mean size(nm)andstandarddeviation(%)versustime(minutes), PLderived; arrowsinjections. Underlyingnumericcurve nottabulated; no exact pixelreadlabels asserted.')
m2('m2-fig2-visible-axes','Figure2 axes','figure_metadata','CdSe displayedmean ticks4/6nm, width6/14%, time0/80/180min; InAs mean3/4nm,width20/25%, time0/100/200min. Plottedaxes retainedwithout falseexactsamplevalues.')
m2('m2-fig3-tem','Figure3 image/caption','figure','TEMimage of8.5nm diameterCdSe nanocrystals preparedbydistributionfocusing;25nm scalebar. Facetedparticles visible. This is separateunassignedspecimen from smaller2.1–4.xnmkineticsequence; no source-supported growthtime/recipeparameters for8.5nm.')
m2('m2-fig3-characterization-scope','Figure3 andsuppliedsources','missingness','TEMinstrument,voltage,gridpreparation,crystallographicphase,latticeparameters,SAED/XRD/elementalanalysis notgiven; do not labelgeometricatomicmodel asmeasuredcrystal.')
m2('m2-eq2-condition','Leftcolumn belowFig3','equation_assumption','Approximation2σVm/rRT≪1 precedesdiffusioncontrolledgrowth equation; source usesmuchlessthan, notmerelylessthan.')
m2('m2-eq2-expression','Leftcolumn growthrateequation','equation','dr/dt=K(1/r+1/δ)(1/r*−1/r); unnumberedexpression, not measuredkineticfit.',expression='dr/dt = K (1/r + 1/δ) (1/r* − 1/r)')
m2('m2-eq2-symbols','Leftcolumn lastparagraph continuingrightcolumn','equation_context','Kproportionaltomonomerdiffusionconstant;δdiffusionlayerthickness;r*criticalradiuswherenanocrystalsolubilityequalsmonomerconcentration andgrowthratezero. No fittedK/δ/r*values.')
m2('m2-fig4','Figure4/caption andopeningrightcolumn','model_figure','Sugimoto-model growthrate(arbitraryunits)versusr/r*, with infinitediffusionthickness. Curvepositiveabovecriticalradius,negativebelow; not actualCdSe/InAsmeasurement.')
for i,t in enumerate([
'At fixedmonomerconcentration criticalsize is equilibrium; smallerparticlesdissolve,largergrow atsize-dependentrates.',
'Authors explainfocusing whenallpresentparticlesareslightlylargerthancriticalsize, withsmallerparticlesgrowingfaster.',
'Asmonomerisdepletedcriticalsizeincreases; smallerparticlesdissolve/disappearwhilelargergrow, producingOstwaldripening/defocusing.',
'Injectingadditionalmonomeratgrowthtemperaturereducescriticalsize andrefocusesdistribution.',
'Changinginitialmonomerconcentrationchangestimetodepletion,hencefocusingtime/focusedsize.',
'AuthorssayCdS/InPalsoshowtheseeffects andpresumablyentireII-VI/III-Vclass. NoCdS/InPrecipesordatasetofferedhere.',
'Authorsproposecontinuousmonitoring/adjustmentofmonomerconcentrationtokeepmeansizeslightlyabovecriticalsize; suggestedautomation/outlook, notdemonstratedclosedloopsystem.'
],1):m2(f'm2-intuition-{i:02}','Rightcolumn modelinterpretation/conclusion','author_interpretation',t)
for s,t in [
('lower-volume','ReducingfirstCdSeinjectionvolumeabout15%withotherconditionssame shortensfocusing22→11min andfocusdiameter3.3→2.7nm. Retainapproximatefactor;2.04mLwouldbecalculated,notreported.'),
('baseline-ratio','AuthorsreportCd:Se stockmolarratioabout1.4:1 inreactiondescribed; separatefrommassratio2:5:100.'),
('cd-rich','AtCd:Semolarratio1.9:1, focusednanocrystalscanremainatgrowthtemperatureforhoursbeforedefocusing; exacthours/stockcharges/focusedsizeunreported.'),
('lower-cd','AtCd:Se1.1:1defocusingrapid; authorssayalmostdoublingbothCdandSeconcentrationsisrequiredfortightdistribution. Noexactconcentrations,size,width,time orvolumegiven; distinguishlowratiocondition andconcentrationrescuequalitatively.')]:m2('m2-variant-'+s,'Rightcolumn recipevariationparagraph','protocol_variant',t)
m2('m2-ack','Acknowledgment','administrative','DOEBasicEnergySciencesMaterialsSciences supportcontractDE-AC03-76SF00098; administrative,notexperiment.',disposition='administrative_record_only')
m2('m2-si-announcement','SupportingInformationAvailable','identity','Announces3scientificSIpages:CdSe/InAsTEMsizecalibrationtablesandInAsUV–vis/PLspectra. LocalPDF4pagesincludesaddedACScover; no missingfourthscientificpage implied.')
refs=[
('Brennan,J.G.;Siegrist,T.;Carroll,P.J.;Stuczynski,S.M.;Reynders,P.;Brus,L.E.;Steigerwald,M.L. Chem.Mater.1990,2,403–409.','molecularprecursorbackground'),
('Steigerwald,M.L. Polyhedron1994,13,1245–1252.','molecularprecursorbackground'),
('Steigerwald,M.L.;Stuczynski,S.M.;Kwon,Y.U.;Vennos,D.A.;Brennan,J.G. Inorg.Chim.Acta1993,212,219–224.','molecularprecursorbackground'),
('Stuczynski,S.M.;Brennan,J.G.;Steigerwald,M.L. Inorg.Chem.1989,28,4431–4432.','molecularprecursorbackground'),
('Murray,C.B.;Norris,D.J.;Bawendi,M.G. J.Am.Chem.Soc.1993,115,8706–8715.','priorCdSeandTEMcalibration'),
('Vossmeyer,T.;Katsikas,L.;Giersig,M.;Popovic,I.G.;Diesner,K.;Chemseddine,A.;Eychmuller,A.;Weller,H. J.Phys.Chem.1994,98,7665–7673.','sizefractionation'),
('Katari,J.E.B.;Colvin,V.L.;Alivisatos,A.P. J.Phys.Chem.1994,98,4109–4117.','priorCdSeandTEMcalibration'),
('Guzelian,A.A.;Katari,J.E.B.;Kadavanich,A.V.;Banin,U.;Hamad,K.;Juban,E.;Alivisatos,A.P.;Wolters,R.H.;Arnold,C.C.;Heath,J.R. J.Phys.Chem.1996,100,7212–7219.','priorIII-V'),
('Guzelian,A.A.;Banin,U.;Kadavanich,A.V.;Peng,X.;Alivisatos,A.P. Appl.Phys.Lett.1996,69,1432–1434.','priorIII-VandTEMcalibration'),
('Olshavsky,M.A.;Goldstein,A.N.;Alivisatos,A.P. J.Am.Chem.Soc.1990,112,9438–9439.','priorIII-V'),
('Micic,O.I.;Curtis,C.J.;Jones,K.M.;Sprague,J.R.;Nozik,A.J. J.Phys.Chem.1994,98,4966–4969.','priorIII-V'),
('Micic,O.I.;Sprague,J.R.;Curtis,C.J.;Jones,K.M.;Machol,J.L.;Nozik,A.J.;Giessen,H.;Fluegel,B.;Mohs,G.;Peyghambarian,N. J.Phys.Chem.1995,99,7754–7759.','priorIII-V'),
('Micic,O.I.;Nozik,A.J. J.Luminescence1996,70,95–107.','priorIII-V'),
('Micic,O.I.;Sprague,J.;Lu,Z.H.;Nozik,A.J. Appl.Phys.Lett.1996,68,3150–3152.','priorIII-V'),
('Douglas,T.;Theopold,K.H. Inorg.Chem.1991,30,594–596.','priorIII-V'),
('Kher,S.S.;Wells,R.L. NanostructuredMater.1996,7,591–603.','priorIII-V'),
('Reiss,H. J.Chem.Phys.1951,19,482–487.','diffusionfocusingtheory'),
('Lifshitz,I.M.;Slyozov,V.V. J.Phys.Chem.Solids1961,19,35–50.','ripeningtheory'),
('Wagner,C.Z. Zeit.Electrochemie1961,65,581–591.','ripeningtheory'),
('Sugimoto,T. Adv.ColloidInterfac.Sci.1987,28,65–108.','Gibbs–Thomson/growthmodel')]
for i,(citation,role) in enumerate(refs,1):m1(f'ref{i:02}',f'Reference{i}','bibliography',citation,disposition='bibliography_context_only_cited_source_not_inspected_in_this_review',reference_number=i,reference_role=role)
m1('ref21','Footnote21','reference_note','Number21 iscurrentCdSesynthesisexperimentalnote, notseparatecitedpaper; granularrecipeunitsabove.',disposition='fully_extracted_elsewhere_in_same_inventory')
m1('ref22','Footnote22','reference_note','Number22 iscurrentInAssynthesisexperimentalnote, notseparatecitedpaper; granularrecipeunitsabove.',disposition='fully_extracted_elsewhere_in_same_inventory')
add('si-cover','si',1,'ACScover','identity','ExactDOI10.1021/ja9805425 andJACS1998,120(21),5343–5344 matchmain. Publisherterms/copyrightadministrative; notscientificpage orrecipe.',disposition='identity_and_administrative_record')
cdse=[[484,2.47,2.1],[488,2.46,2.1],[516,2.34,2.4],[526,2.30,2.6],[534,2.27,2.7],[542,2.24,2.9],[550,2.21,3.1],[560,2.17,3.3],[566,2.16,3.4],[570,2.14,3.5],[576,2.09,3.6],[596,2.04,4.3],[600,2.03,4.4],[606,2.02,4.6],[608,2.01,4.7],[610,2.00,4.8]]
inas=[[838,1.41,2.3],[861,1.38,2.4],[886,1.34,2.6],[905,1.31,2.8],[929,1.28,3.0],[954,1.24,3.2],[976,1.22,3.4],[1004,1.19,3.6],[1029,1.16,3.8],[1051,1.13,4.0],[1078,1.10,4.2],[1107,1.08,4.4],[1132,1.05,4.6],[1159,1.03,4.8],[1187,1.01,5.0],[1216,0.98,5.2],[1246,0.96,5.4],[1272,0.94,5.6],[1305,0.92,5.8],[1333,0.90,6.0]]
for material,rows,page in [('cdse',cdse,2),('inas',inas,4)]:
    add('si-'+material+'-table','si',page,'Unnumberedcalibrationtable,printedS'+str(page-1),'calibration_table','UV–visexcitonpeak(nm),PLpeak(eV),TEMsize(nm); manuallytranscribedfromrenderbecauseembeddedOCRseverelycorrupted. '+str(len(rows))+'datarows; priorcalibration,notcurrentreactiontimepoints orindependentlyidentifiedruns. Noindividualrowreference orrecipeassigned.')
    for i,(uv,pl,size) in enumerate(rows,1):add(f'si-{material}-row{i:02}','si',page,f'Calibrationtable,datarow{i}','calibration_row',f'{material.upper()}:UV–vispeak{uv}nm;PLpeak{pl:g}eV;TEMsize{size:g}nm.',disposition='calibration_evidence_no_recipe_sample_join',values={'uv_vis_peak_nm':uv,'pl_peak_eV':pl,'tem_size_nm':size},material=('CdSe' if material=='cdse' else 'InAs'))
add('si-inas-spectra-overview','si',3,'PrintedS2,twoopticalpanels','figure','InAsabsorption(left)androom-temperaturePL(right)time-series;Energy(eV)axes,arbitraryintensity;differentselectedtimegrids,notone-to-oneabsorption/PLpairs.')
for t in [18,28,43,158,176,245]:add(f'si-inas-spectra-abs{t}','si',3,f'Absorptionpanel,trace t={t}','spectrum',f'InAsabsorptiontrace t={t};sourcepaneldoesnotprinttimeunit,timeinminutescontextualviaMainFig2. Noexactdigitizedpeakvalues asserted.',time_label=t,time_unit_scope='minutes_linked_context_from_main_Fig2')
for t in [23,28,80,158,176]:add(f'si-inas-spectra-pl{t}','si',3,f'PLpanel,trace t={t}','spectrum',f'InAsroom-temperaturePLtrace t={t};timeunitcontextualviaMainFig2. Noexactdigitizedpeakvalues asserted.',time_label=t,time_unit_scope='minutes_linked_context_from_main_Fig2')
add('si-inas-spectra-reabsorption','si',3,'Noteunderplots','measurement_method','Becauseofreabsorptiononthelower-energyhalfofthePLspectrum(around1eV),onlyhigher-energyhalfwasusedtodeterminesizedistributionandstandarddeviation. Do notassumewholePLprofileusedforInAs.')
add('si-inas-spectra-axes','si',3,'Panelaxes','figure_metadata','Absorptionxaxislabeled0.9,1.3,1.7eV;yaxisAbsorption(a.u.),0–7offsetpresentation. PLxaxis0.75,1.25,1.75eV;yaxisIntensity(a.u.). Traceoffset/normalizationnotabsolutequantumyield.')
gaps=[
('No exactstockmassesfrominjectionvolumes','Massratiosplusstockvolumesdonotuniquelyestablishcomponentmassesormoleswithoutdensity/stockbatchrecipe.'),
('No structuralphaseassignment','Main/SIdonotreportphase,XRD,SAED,latticeconstantsorunitcell. TEMimageisnotitselfverifiedphaseassignment.'),
('No universal PL-densitysetting','Footnote21OD0.09±0.02mustnotsilentlypropagatetoInAsfootnote22.'),
('No time-labeledcalibrationexperiment','SItablesareTEMcalibrationpoints; no28or23min etcjoinsfromsimilarsizes.'),
('No dose-durationprecision','Initialinjections<0.1s;CdSesecondinjectionslow;InAsadditionalinjectiondurationsunreported.'),
('No 8.5nm exactrecipe','TEM8.5nmproductfromdistributionfocusingnotmappedtoexactparameters ofsmallerkineticrun.'),
('No second route fromsequentialdose','CdSe0.8mL190minandInAs0.5mL23min/0.8mL158minarewithintrajectories,notindependentstartingrecipes.'),
('No automatic exacttemperatureinheritance','InAs300°Cpreheat→250°Cpostinjection→260°Cgrowth;CdSe360→300. Priorliterature350°Ccannotreplacecurrent360°C.')]
for i,(title,detail) in enumerate(gaps,1):m2(f'audit-gap-{i:02}','Fullsuppliedmain/SI cross-check','audit_guardrail',title+': '+detail,disposition='preserve_missingness_or_join_restriction')
page_review=[]
for doc in manifest['documents']:
    for p in doc['pages']:
        page_review.append({'source_role':doc['role'],'pdf_page':p['page'],'text_read':True,'visual_review':True,'text_sha256':hashlib.sha256((B/p['text_file']).read_bytes()).hexdigest(),'render_sha256':hashlib.sha256((B/p['render_file']).read_bytes()).hexdigest(),'source_unit_ids':[u['id'] for u in units if u['source_role']==doc['role'] and u['pdf_page']==p['page']]})
identity={'schema':'mattersyn-local-source-identity-1','checked_utc':now,'source_id':'peng1998','doi':'10.1021/ja9805425','title':'Kinetics of II-VI and III-V Colloidal Semiconductor Nanocrystal Growth: “Focusing” of Size Distributions','authors':['Xiaogang Peng','J. Wickham','A. P. Alivisatos'],'journal':'Journal of the American Chemical Society','year':1998,'volume':120,'issue':21,'printed_pages':[5343,5344],'dates':{'received':'1998-02-18','published_web':'1998-05-14'},'main_pdf_page_count':2,'si_pdf_page_count':4,'si_scientific_page_count':3,'si_status':'matched_by_content','identity_evidence':['Mainp1title/byline/JACS1998,120,5343–5344 andonline1998-05-14; mainp2issue21 andterminalJA9805425','SIcoverexactDOI10.1021/ja9805425 andmatchingjournal/year/issue/pages','SIS1–S3 headersPeng,JACS120,page5343,year1998;contentsmatchmainSupportingInformationannouncement','Mainannounces3SIpages;local4-pagePDFhasaddedACScover plus3scientificpages'],'documents':[{'role':d['role'],'path':d['source'],'sha256':d['sha256'],'page_count':d['page_count'],'hash_rechecked':hashlib.sha256(Path(d['source']).read_bytes()).hexdigest()==d['sha256']} for d in manifest['documents']],'scope':'AllsixsuppliedPDFpagesindependentlytextandvisuallyreviewed;noexternalcitedpaperread/downloaded','not_claimed':'Noidentityassertionsforothercopiesoutsideprovidedmanifest;rootcorpusfingerprinthandlesdeduplication.'}
report={'schema':'mattersyn-independent-source-audit-1','source_id':'peng1998','doi':identity['doi'],'title':identity['title'],'checked_utc':now,'reviewer':'independent_peng1998_source_audit','status':'supplied_main_and_matched_si_text_visual_inventory_complete','review_scope':'2mainpagesplus4SIpagesincludingadministrativecover;all6textandvisual','source_identity_file':'source-identity.json','source_sha256':manifest['documents'][0]['sha256'],'si_sha256':manifest['documents'][1]['sha256'],'page_review':page_review,'unit_count':len(units),'units':units,'calibration_tables':{'CdSe':cdse,'InAs':inas},'independent_canonical_audit_status':'awaiting_root_drafts','scope_limits':['Sourceinventoryonly;notproofthatcanonicalorpublicreaderalreadyretainsallunits.','Nofullproceduresfromcitedreferences1–20verifiedinthispaperreview.','Noexternalfigurecurve digitization,structuralassignment ormeasuredquantumyieldinferred.']}
for filename,data in [('source-identity.json',identity),('source-audit.json',report),('independent-page-coverage.json',{'reviewer':report['reviewer'],'checked_utc':now,'page_review':page_review})]:
    (B/filename).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# Independent source audit: Peng, Wickham and Alivisatos (1998)','',f"DOI: {identity['doi']}. All 2 main pages and 4 SI PDF pages (one ACS cover plus 3 scientific pages) were read and visually inspected. {len(units)} stable source units inventoried. SI identity is verified by its exact DOI cover, Peng headers and matching content.",'','Key restrictions: SI calibration tables are not current batches; Figure 3 TEM 8.5 nm is not joined to the smaller kinetic trajectory; additional injections are sequential; InAs PL widths use only the high-energy half; CdSe PL OD does not automatically apply to InAs. Initial injection bounds remain <0.1 s. No crystal phase, SAED, XRD, CIF, isolation cycle, pressure or exact stock mass is invented.','']
for u in units:lines+=['## '+u['id'],f"{u['source_role']} PDF page {u['pdf_page']}; {u['locator']}. [{u['kind']}; {u['disposition']}]",u['claim'],'']
(B/'source-audit.md').write_text('\n'.join(lines),encoding='utf-8')
(B/'source-identity.md').write_text('# Source identity\n\n'+identity['title']+'\n\nXiaogang Peng; J. Wickham; A. P. Alivisatos. JACS 1998, 120(21), 5343–5344. DOI 10.1021/ja9805425.\n\nThe supplied main has 2 pages; its title, byline, publication fields and terminal article code match the supplied SI. The SI PDF has an added ACS cover with the exact DOI and 3 scientific pages carrying Peng/JACS120/page5343 headers. Its two calibration tables and InAs spectra match the main SI announcement. Both source hashes were independently rechecked against the render manifest. No network downloads or additional source claims were made.\n',encoding='utf-8')
print(json.dumps({'units':len(units),'pages':len(page_review),'identity_hash_checks':[d['hash_rechecked'] for d in identity['documents']],'audit_sha256':hashlib.sha256((B/'source-audit.json').read_bytes()).hexdigest()}))
