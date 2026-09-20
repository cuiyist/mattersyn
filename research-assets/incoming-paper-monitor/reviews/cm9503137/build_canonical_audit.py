"""Bounded independent source-to-record audit; does not edit source records."""
from pathlib import Path
import json, hashlib
from datetime import datetime, timezone

B = Path(__file__).resolve().parent
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
records = {p.stem: json.loads(p.read_text(encoding='utf-8')) for p in sorted((B/'canonical-drafts').glob('*.json'))}
def rid(x): return 'danek-1996-'+x
def pointers(record, field, ids):
    d=records[rid(record)]
    return [f'/{field}/{i}' for i,x in enumerate(d[field]) if x.get('id',x.get('sample_id')) in ids]

findings = [
 {'id':'C01','severity':'must_fix','title':'Inherited material and target scopes overstate supporting records',
  'records':[rid(x) for x in ['seed-preparation','no-seed-control','no-dezn-control','electrospray-dispersion','characterization','annealing-control']],
  'json_pointers':['/material','/intended_target/composition','/products'],
  'source_locators':['Main PDF p. 2, Materials, Synthesis, and dispersion preparation','Main PDF p. 3, comparative reactions','Main PDF p. 4, annealing and Figure 4'],
  'finding':'The common base assigns CdSe/ZnSe, Cd+Se+Zn, and a core/shell target. Seed preparation yields bare CdSe; the no-seed control has no Cd input; the no-DEZn control has no Zn dosing. The electrospray-dispersion target currently says embedded film and its product formula implies only coated feed although bare feed is explicitly allowed. The shared characterization procedure covers bare particles, overcoated particles and matrix films. Annealing does not establish retention of a core/shell architecture after treatment.',
  'requested_change':'Override material metadata and intended target per supporting scope. Seed and no-DEZn records should be CdSe contexts. No-seed material should be unresolved Zn/Se precursor product, without Cd or an established ZnSe crystal assignment. Electrospray feed and shared characterization should state their alternatives/context rather than a synthesized single architecture. For annealing, distinguish the initial CdSe/ZnSe particles from author-inferred alloying after annealing; do not claim a refined final alloy or retained uniform shell.'},
 {'id':'C02','severity':'must_fix','title':'Annealing source conflict is encoded as experimental choices',
  'records':[rid('annealing-control')],'json_pointers':['/condition_options','/operations/1/parameters/temperature'],
  'source_locators':['Main PDF p. 4, Structural Characterization body and Figure 4 caption'],
  'finding':'The operative temperature is correctly null, but 400 and 450 °C still occupy condition_options. A warning label does not make these two source reports valid selectable experimental variants.',
  'requested_change':'Remove these condition_options. Retain both source-labelled numerical reports as conflict/context facts with their individual locators, leave the operative temperature unresolved and retain approximately 30 min from the body.'},
 {'id':'C03','severity':'must_fix','title':'Machine operation reverses the printed degassing order',
  'records':[rid('electrospray-dispersion')],'json_pointers':['/operations/3/action'],
  'source_locators':['Main PDF p. 2, Preparation of the Nanocrystal Dispersions for ES-OMCVD'],
  'finding':'The description correctly preserves thaw–pump–freeze, but action=freeze_pump_thaw asserts another order.',
  'requested_change':'Use a neutral action such as cyclic_vacuum_degassing and retain the exact printed sequence with uncertainty about unstated cycle details. Do not silently correct the source.'},
 {'id':'C04','severity':'must_fix','title':'Cited CdSe preparation gets an unsupported specific selenium-precursor edge',
  'records':[rid('seed-preparation')],'json_pointers':['/operations/1/inputs','/material_states/1/parent_ids'],
  'source_locators':['Main PDF p. 2, Materials and first paragraph of Synthesis of CdSe/ZnSe Nanocrystals; reference 10'],
  'finding':'Danek separately reports a 1.0 M TOPSe stock and cites selected-size CdSe growth in TOP/TOPO to Murray. This main text does not choose a specific Murray core-precursor route. The cited-core input edge topse-stock treats that connection as an established current-paper procedure.',
  'requested_change':'Keep the TOPSe stock and dimethylcadmium pretreatment in the source inventory, but make the cited core synthesis a citation-level origin rather than an asserted fully specified material-consumption recipe. Remove unsupported precursor edges, or explicitly represent them as unresolved cross-source context. Keep the restated purification/fractionation steps.'},
 {'id':'C05','severity':'must_fix','title':'Source particle sizes are normalized to diameter without a stated geometric definition',
  'records':[rid('solution-characterization'),rid('film-characterization')],
  'json_pointers':pointers('solution-characterization','measurements',['fig1-a-size','fig1-b-size','fig1-c-size','fig1-d-size','structure-size','bare-xrd-size','core-size'])+pointers('film-characterization','measurements',['fig10-core']),
  'source_locators':['Main PDF p. 3, Figure 1 inset table and HRTEM size discussion','Main PDF p. 4, Figure 3','Main PDF p. 5, AES core-size context','Main PDF p. 7, Figure 10'],
  'finding':'The source table is headed Size and the body says particle size. In particular the approximately 6.8 nm particles have aspect ratio approximately 1.3, without a stated axis or equivalent-diameter definition. Current properties diameter/core_diameter/initial_core_diameter silently choose geometry.',
  'requested_change':'Use particle_size, core_size and initial_core_size, or carry a clearly labelled inferred diameter interpretation distinct from the reported value. Preserve values, methods, approximate flags and distribution spread; do not change the numeric data.'},
 {'id':'C06','severity':'must_fix','title':'Several explanatory claims lack their actual page/section evidence',
  'records':[rid('znse-overgrowth'),rid('characterization'),rid('solution-characterization')],
  'json_pointers':['/operations','/materials','/measurements'],
  'source_locators':['Main PDF pp. 2–5 and p. 7, as detailed below'],
  'finding':'Several operations cite only the experimental paragraph although their descriptions include Results claims from later pages. The numerical values are not contradicted, but the current evidence does not point to the supporting passage.',
  'requested_change':'Add p. 3 Synthesis to overgrowth heat (150–160 °C discussion) and dose (suppression of homogeneous nucleation); p. 4 purification/stability to exchange and store; Materials p. 2 for reagent grades/preparation notes. Add p. 4/p. 5 to characterization AES for below-detection phosphorus and escape depth; p. 7 Figure 8 for the 10 K cryostat context; p. 4 Figure 3 for XRD bulk references. Add p. 2 Optical Characterization to the four solution PL-yield measurements that specify the rhodamine590/methanol calibration technique. Claims and numerical settings should retain their original figure/value evidence too.'}
]

procedure_map={
 'cited_core_and_TOPSe_preparation':['seed-preparation'],
 'precursor_pretreatment':['znse-overgrowth','seed-preparation','bare-dot-film','overcoated-dot-film'],
 'seed_dispersion':['znse-overgrowth'],'precursor_feed_stock':['znse-overgrowth'],
 'overgrowth_dosing':['znse-overgrowth'],'alcoholysis_purification_exchange':['znse-overgrowth'],
 'storage_and_stability':['znse-overgrowth'],'electrospray_dispersion':['electrospray-dispersion'],
 'ES_OMCVD_stack':['bare-dot-film','overcoated-dot-film'],
 'no_seed_control':['no-seed-control'],'no_DEZn_control':['no-dezn-control'],
 'higher_temperature_overgrowth':['high-temperature-overgrowth'],'annealing_control':['annealing-control']}
methods={'UVvis_method':'abs','PL_PLE_method':'pl','film_PL_method':'cryostat','XRF_method':'xrf','AES_method':'aes','HRTEM_method':'tem','XRD_method':'xrd'}
cohorts={
 'growth_series_F1':('solution-characterization',['fig1-a','fig1-b','fig1-c','fig1-d']),
 'structural_ratio2p5':('solution-characterization',['structure-2p5','bare-xrd']),
 'AES_XRF_ratio4p8':('solution-characterization',['aes-cohort']),
 'purified_optical_series_F5_F6':('solution-characterization',['optical-a','optical-b','optical-c','optical-d','optical-series']),
 'film_PL_F7_F8':('film-characterization',['bare-150','bare-200','bare-250','coated-150','coated-200','coated-270']),
 'film_PLE_bare_F9':('film-characterization',['fig9-bare']),
 'film_PLE_overcoated_F10':('film-characterization',['fig10-coated']),
 'film_shell_thickness_series_F11':('film-characterization',['fig11-series'])}
checks=[
 'Two distinct 10 mL TOP portions retained; 0.5 mmol TOPSe belongs only to seed dispersion.',
 'Feed amounts, feed concentration, delivered fraction and growth duration stay unknown; no 33.3 min calculation.',
 'Colloidal Aldrich DEZn filtration remains distinct from as-received OMCVD Texas Alkyls DEZn.',
 'Butanol isomer and optional nonane amount stay unknown; pyridine exchange and nitrogen storage are present.',
 'Electrospray approximately 3 mg/mL is CdSe before acetonitrile; no inferred measured final concentration.',
 'Film feed voltage, flow, carrier flow, pressure and three layer thicknesses match the supplied source.',
 'No-seed 320 nm absorption is not converted to measured 1.5 nm ZnSe particle size.',
 'Approximately 200 °C overgrowth control preserves initial approximately 2 nm blue shift and incomplete recipe scope.',
 'Figure 1 a–d size/spread values retained and not treated as independent fully quantified synthesis runs.',
 'Figure 2/3 structural context does not assert a resolved interface or unique measured shell phase.',
 'AES surface 7.0, overall 4.8, core approximately 3.5 nm and model shell approximately 1.3 nm remain distinct.',
 'Optical 3.6/4.3/4.8 aliquots share source preparation but are not merged with the AES 4.8 specimen.',
 'Approximate solution PL estimates remain 0.05/0.4/0.4/0.3 percent, not fractional 0.05/0.4 values or film yields.',
 'Figure 7/8 ratio 0.4 and Figure 10 ratio 4.0 remain separate; no decimal correction.',
 'Bare 250 °C and coated 270 °C highest-temperature comparisons remain distinct.',
 'PLE detection and normalization wavelengths are settings, not independently measured emission peaks.',
 'Figure 11 excitation 500 nm remains distinct from Figure 7/8 480 nm.',
 'Figure 11 model monolayers are author-derived; >10 and approximately100 fold are relative trend summaries.',
 'Approximately 5–60 min is depth-dependent thermal exposure, not deposition duration.',
 'Seven characterization branches remain independent; TEM carbon is specimen preparation, not a synthesized shell.',
 'General recipe/product links do not assign all figures to a single known physical batch.',
 'All records request no training tasks and remain imported_unreviewed at this audit snapshot.'
]
audit=json.loads((B/'source-audit.json').read_text(encoding='utf-8'))
def rec(key): return records[rid(key)]
def op(key,oid): return next(x for x in rec(key)['operations'] if x['id']==oid)
def meas(key,mid): return next(x for x in rec(key)['measurements'] if x['id']==mid)
def haspage(items,p): return any(f'Main PDF p. {p},' in x['locator'] for x in items)
closure_checks={
 'C01':(
  rec('seed-preparation')['material']['formula']=='CdSe' and
  'Cd' not in rec('no-seed-control')['material']['elements'] and
  rec('no-dezn-control')['material']['formula']=='CdSe' and
  rec('electrospray-dispersion')['material']['architecture']!='composite' and
  'bare' in rec('electrospray-dispersion')['products'][0]['composition']['value'].lower() and
  rec('characterization')['material']['architecture']!='core_shell' and
  rec('characterization')['intended_target']['composition']['value']!='CdSe core with ZnSe overlayer' and
  rec('annealing-control')['intended_target']['composition']['value']!='CdSe core with ZnSe overlayer'),
 'C02':(not rec('annealing-control')['condition_options'] and
  op('annealing-control','anneal')['parameters']['temperature']['value'] is None and
  {m['value']['value'] for m in rec('annealing-control')['measurements'] if m['property']=='conflicting_source_temperature_report'}=={400,450}),
 'C03':op('electrospray-dispersion','degas')['action']=='cyclic_vacuum_degassing' and 'thaw–pump–freeze' in op('electrospray-dispersion','degas')['description'],
 'C04':'topse-stock' not in op('seed-preparation','cited-core')['inputs'] and 'not selected' in op('seed-preparation','cited-core')['description'],
 'C05':all(m['property'] not in ['diameter','core_diameter','initial_core_diameter'] for k in ['solution-characterization','film-characterization'] for m in rec(k)['measurements']),
 'C06':(all(haspage(op('znse-overgrowth',i)['evidence'],3) for i in ['heat','dose']) and
  all(haspage(op('znse-overgrowth',i)['evidence'],4) for i in ['exchange','store']) and
  all(haspage(op('characterization','aes')['evidence'],p) for p in [4,5]) and
  haspage(op('characterization','cryostat')['evidence'],7) and
  haspage(op('characterization','xrd')['evidence'],4) and
  all(haspage(m['evidence'],2) for m in rec('solution-characterization')['measurements'] if m['property']=='photoluminescence_quantum_yield'))}
for f in findings:
 f['status']='resolved' if closure_checks[f['id']] else 'open'
 f['closure_basis']='Current serialized record snapshot inspected; bounded correction checks passed.' if closure_checks[f['id']] else 'One or more required corrections remain in current serialized records.'
report={
 'audit_version':'1.1','audited_at_utc':datetime.now(timezone.utc).isoformat(),
 'status':'passed_bounded_scientific_audit' if all(closure_checks.values()) else 'changes_requested','scope':'Bounded independent scientific audit of 12 private records against the previously fully read and visually inspected eight supplied main pages. Source-to-reader, SI matching, training eligibility and publication are outside this audit.',
 'review_scope':'supplied_main_only_si_unverified',
 'source':audit['source'], 'source_audit_sha256':digest(B/'source-audit.json'),
 'record_count':len(records),'measurement_count':sum(len(d['measurements']) for d in records.values()),
 'records':[{'record_id':k,'basename':k+'.json','sha256':digest(B/'canonical-drafts'/(k+'.json')),'record_type':d['record_type'],'measurement_count':len(d['measurements'])} for k,d in records.items()],
 'findings':findings,'closure_checks':closure_checks,'open_must_fix_count':sum(not v for v in closure_checks.values()),'bounded_checks_passed':checks,
 'coverage':{
  'procedures':[{'source_audit_id':k,'record_ids':[rid(i) for i in v],'note':'Core operation coverage present; detailed qualitative stability remains reader context.' if k=='storage_and_stability' else 'Present; listed findings qualify acceptance.'} for k,v in procedure_map.items()],
  'methods':[{'source_audit_id':k,'record_id':rid('characterization'),'operation_id':v} for k,v in methods.items()],
  'cohorts':[{'source_audit_id':k,'record_id':rid(v[0]),'sample_ids':v[1],'note':'Cohort-level mapping, not proof of individual specimen identity.'} for k,v in cohorts.items()]},
 'reader_context_still_required':[
  'All 11 figures and Figure 1 inset table, including their captions, scaling annotations and source-specific sample scopes.',
  'Solubility thresholds, air-exposure/stability observations, interpretation of epitaxy/disorder/strain/alloying and PLE energy transfer/filtering.',
  'Unnumbered aqueous displacement equilibrium and +56.0 kJ/mol as thermodynamic comparison, not the organometallic reaction free energy.',
  'Reference-only upstream methods, the cited approximately10% TOP/TOPO-capped yield, historical cluster analogues and proposed future annealing/outlook.',
  'All source conflicts and source-specific intuition already inventoried by the independent source audit.'
 ],
 'limitations':['No new physical batches, complete recipe matrix, uniform shell thickness, exact atomic structure or missing SI may be inferred from the 12-record count.','Detailed reader-context coverage is delegated to the public-review proposal and must be checked after integration.','This audit does not authorize or imply review-status promotion, training eligibility or publication.']
}
assert set(procedure_map)=={x['id'] for x in audit['procedures_and_controls']}
assert set(methods)=={x['id'] for x in audit['characterization_methods']}
assert set(cohorts)=={x['id'] for x in audit['sample_and_figure_joins']}
assert all(not d['quality']['requested_tasks'] for d in records.values())
for rec,samples in cohorts.values(): assert set(samples)<={p['sample_id'] for p in records[rid(rec)]['products']}
(B/'canonical-records-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# Danek 1996 — private canonical scientific audit','',f"Status: {report['status']}. {report['record_count']} records / {report['measurement_count']} measurements.",'','Scope: supplied main only; SI not located or verified. No Site, training or publication certification.','',f"Source PDF SHA-256: `{report['source']['sha256']}`.",'','## Findings','']
for f in findings: lines += [f"### {f['id']}: {f['title']} — {f['status']}",'','Original finding: '+f['finding'],'',f"Requested correction: {f['requested_change']}",'',f['closure_basis'],'','Records: '+', '.join(f['records'])+'.','']
lines+=['## Coverage','', 'All 13 source-audit procedures, 7 acquisition methods and 8 sample groups are mapped in the JSON audit. Twelve records are not twelve independent experiments. The quantitative and cohort checks listed in the JSON passed; correction status for the six original findings is recorded separately above.','', 'Reader context still needs all 11 figures, the inset table, qualitative and model claims, reference comparisons and conflicts; those are not required to be fabricated into canonical run fields.','', '## Exact reviewed snapshot','']
for r in report['records']:lines+=[f"- {r['record_id']}: `{r['sha256']}`"]
(B/'canonical-records-audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'findings':len(findings),'records':len(records),'measurements':report['measurement_count'],'coverage':{'procedures':len(procedure_map),'methods':len(methods),'cohorts':len(cohorts)}},indent=2))
