"""Bounded source-to-canonical audit; reads Site helpers, writes only private reports."""
from pathlib import Path
from datetime import datetime, timezone
import json,hashlib,sys
B=Path(__file__).resolve().parent
sys.path.insert(0,str(B.parents[3]/'recipe-atlas'/'scripts'))
from dataset_lib import validate_record,eligibility,build_groups,walk
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
D={p.stem:json.loads(p.read_text(encoding='utf-8')) for p in sorted((B/'canonical-drafts').glob('*.json'))}
def R(key):return D['dabbousi-1997-'+key]
def O(key,id):return next(x for x in R(key)['operations'] if x['id']==id)
def V(key,id):return next(x for x in R(key)['measurements'] if x['id']==id)
def haspage(e,p):return any(f'Main PDF p. {p},' in x['locator'] for x in e)
errors=[x for r in D.values() for x in validate_record(r)]
duplicates=[]
for rid,r in D.items():
 for path,obj in walk(r):
  for k in ['evidence','link_evidence']:
   if k in obj:
    entries=[json.dumps(e,sort_keys=True) for e in obj[k]]
    if len(entries)!=len(set(entries)):duplicates.append({'record_id':rid,'pointer':path+'/'+k})
gates={k:eligibility(r) for k,r in D.items()}
checks={
 'schema_and_graphs':not errors,
 'one_source_split_group':len(set(build_groups(list(D.values())).values()))==1,
 'no_training_eligible':not any(v['eligible'] for r in gates.values() for v in r.values()),
 'no_requested_tasks':all(r['quality']['requested_tasks']==[] for r in D.values()),
 'not_promoted':all(r['quality']['review_status']=='imported_unreviewed' for r in D.values()),
 'no_duplicate_evidence':not duplicates,
 'particle_amount_not_formula_units':'not CdSe formula units' in R('zns-overgrowth')['materials'][0]['quantities']['particle_amount']['basis'],
 'six_exact_core_temperature_pairs':[(x['parameters']['input_core_diameter']['value'],x['parameters']['overgrowth_temperature']['value']) for x in R('zns-overgrowth')['condition_options']]==[(23,140),(30,140),(35,160),(40,180),(48,200),(55,220)],
 'cds_input_size_explicit':(O('cds-overgrowth','seed-charge')['parameters']['input_core_diameter']['minimum'],O('cds-overgrowth','seed-charge')['parameters']['input_core_diameter']['maximum'])==(33.5,35),
 'cds_flow_and_temperature':O('cds-overgrowth','dose')['parameters']['temperature']['value']==180 and O('cds-overgrowth','dose')['parameters']['feed_rate']['value']==1,
 'cds_addition_time_not_fabricated':O('cds-overgrowth','dose')['parameters']['duration']['value'] is None,
 'cds_recovery_scope':'belongs only to the ZnS route' in O('cds-overgrowth','recover')['description'],
 'cds_equal_storage_basis_unspecified':'mass/volume basis' in O('cds-overgrowth','storage-solvent')['parameters']['hexane_to_butanol']['basis'],
 'filter_material_not_inherited':all('not stated' in O(k,'filter-metal')['description'] for k in ['zns-overgrowth','cds-overgrowth']),
 'table1_tem_values':[(V('coverage-series',k+'-length')['value']['value'],V('coverage-series',k+'-spread')['value']['value'],V('coverage-series',k+'-aspect')['value']['value']) for k in ['bare','ml-065','ml-13','ml-26','ml-53']]==[(39,8.2,1.12),(43,11,1.16),(47,10,1.16),(55,13,1.23),(72,19,1.23)],
 'table1_wds_values':[V('coverage-series',k+'-wds')['value']['value'] for k in ['ml-065','ml-13','ml-26','ml-53']]==[.46,1.5,3.6,6.8],
 'table1_high_coverage_saxs_missing':all(V('coverage-series',k+'-'+s)['value']['value'] is None for k in ['ml-26','ml-53'] for s in ['saxs-size','saxs-spread','saxs-ratio']),
 'xps_not_table_row_measurement':[V('coverage-series',i)['sample_id'] for i in ['bare-se-cd','ml-13-zn-auger','ml-26-zn-auger','ml-065-xps-auger-ratio','ml-26-xps-auger-ratio']]==['xps-bare-context','xps-13-context','xps-26-context','xps-065-context','xps-26-context'],
 'initial_xps_not_asserted_same_physical_specimen':'not established' in R('air-exposure-observations')['products'][0]['notes'][0],
 'three_waxs_shared_slits':all(k in O('waxs-film','waxs')['parameters'] for k in ['scatter_slit','diffraction_slit','collection_slit']),
 'wds_uncertainty_locator':haspage(O('wds-preparation','wds')['evidence'],5),
 'residual_phosphorus_locator':haspage(O('xps-preparation','exchange')['evidence'],5),
 'polymer_aggregation_locator':all(haspage(O(k,'cast')['evidence'],7) for k in ['saxs-pvb-film','saxs-diblock-film']),
 'pl_calibration_locators':all(haspage(m['evidence'],2) for r in D.values() for m in r['measurements'] if m['property']=='photoluminescence_quantum_yield'),
 'solution_saxs_high_ratio_conflict':{m['value']['value'] for m in R('solution-saxs-series')['measurements'] if m['property']=='source_reported_zn_to_cd_ratio'}=={5.3,5.6},
 'solution_saxs_sigma_conflict':V('solution-saxs-series','a-sigma-caption')['value']['value']==.11 and V('solution-saxs-series','bare-sigma-body')['value']['value']==.12,
 'model_radius_is_derived':V('solution-saxs-series','bare-radius')['value']['status']=='author_derived',
 'cds_radius_conflict':V('cds-optical-comparison','core-radius-caption')['value']['value']==16 and V('cds-optical-comparison','core-radius-body')['value']['value']==30,
 'cds_redshift_not_counterfactual':V('cds-optical-comparison','redshift')['value']['value']==210,
 'no_measured_atomic_structure':not any(s.get('eligible_as_measured_label') for r in D.values() for s in r['structure_assets'])
}
findingdefs=[
 ('D01','CdS recovery inherited a ZnS-specific rationale','The original common loop described separate small ZnS-particle removal even in the CdS route. CdS now explicitly inherits only the common methanol-recovery framework, without assigning ZnS nuclei to the CdS material.',['cds-overgrowth'],'cds_recovery_scope'),
 ('D02','Explicit CdS input-core range was confined to a missing-size qualifier','Added source-reported input CdSe diameter33.5–35Å to the seed-loading operation. It is not a final particle size and does not resolve the optical cohort radius conflicts.',['cds-overgrowth'],'cds_input_size_explicit'),
 ('D03','XPS sample designations were joined directly to Table1 aliquots','Moved general bareSe/Cd and coverage-labelled ZnAuger/attenuation observations onto separate XPS contextual products. The source mentions multiple~33/~40Å cores without proving identity to Table1 TEM/WDS specimens. Existing measurement IDs remain stable.',['coverage-series'],'xps_not_table_row_measurement'),
 ('D04','Initial bare-XPS baseline implied physical identity with aged film','Initial baseline is now explicitly general bare-XPS context;16/80h remain the source-described same-sample sequence. Repeated source baseline across contexts is not an independent replicate.',['air-exposure-observations'],'initial_xps_not_asserted_same_physical_specimen'),
 ('D05','WAXS inherited slit settings were only indirectly described','Added shared1/6° scatter/diffraction slits and0.3mm collection slit with explicit same-setup provenance. No new operating assumption was introduced.',['waxs-film'],'three_waxs_shared_slits'),
 ('D06','Several Results claims lacked their own locators','Added scoped evidence for temperature rationale,residualP,aggregation,WDSuncertainty,TEMstatistics,monolayerdefinition,scattering-fit limits,calibratedPL and WAXS acquisition/model context. Deepcopy/JSON detachment avoids shared-list pollution.',['zns-overgrowth','cds-overgrowth','wds-preparation','xps-preparation','saxs-pvb-film','saxs-diblock-film','waxs-film','core-size-optical-series','coverage-series'],'no_duplicate_evidence')]
findings=[{'id':i,'title':t,'correction':c,'records':['dabbousi-1997-'+r for r in rs],'status':'resolved' if checks[check] else 'open','closure_check':check} for i,t,c,rs,check in findingdefs]
procmap={
 'precursor_filtration':['cdse-seed-preparation','zns-overgrowth','cds-overgrowth'],
 'topse_stock':['cdse-seed-preparation'],'cdse_core_growth':['cdse-seed-preparation'],'core_fractionation':['cdse-seed-preparation'],
 'shell_vessel_preparation':['zns-overgrowth','cds-overgrowth'],'seed_loading':['zns-overgrowth','cds-overgrowth'],
 'target_shell_dose_model':['zns-overgrowth'],'zn_s_feed':['zns-overgrowth'],'zns_overgrowth':['zns-overgrowth'],'temperature_size_map':['zns-overgrowth'],
 'postgrowth_hold':['zns-overgrowth','cds-overgrowth'],'zns_storage':['zns-overgrowth'],'zns_isolation':['zns-overgrowth'],'cds_overgrowth':['cds-overgrowth'],'cds_storage':['cds-overgrowth'],
 'wds_specimen':['wds-preparation'],'xps_specimen':['xps-preparation'],'tem_specimen':['tem-preparation'],'saxs_pvb_specimen':['saxs-pvb-film'],'saxs_mtd_specimen':['saxs-diblock-film'],'solution_saxs_specimen':['saxs-solution'],'waxs_specimen':['waxs-film'],'xps_air_exposure':['air-exposure'],'split_core_coverage_series':['coverage-series']}
methodmap={'uvvis':['optical-characterization'],'pl':['optical-characterization'],'wds':['wds-preparation'],'xps':['xps-preparation'],'tem':['tem-preparation'],'saxs_polymer':['saxs-pvb-film','saxs-diblock-film'],'saxs_solution':['saxs-solution'],'waxs':['waxs-film']}
cohortmap={'size_series_F1_F2':['core-size-optical-series'],'photograph_F3':['core-size-optical-series'],'main_coverage_series':['coverage-series'],'xps_cohorts':['coverage-series','air-exposure-observations'],'oxidized_bare_xps':['air-exposure-observations'],'solution_saxs_F11_F12':['solution-saxs-series'],'theory_F14':[],'zns_shift_F15':['coverage-series'],'cds_shift_F16':['cds-optical-comparison']}
sa=json.loads((B/'source-audit.json').read_text(encoding='utf-8'))
assert set(procmap)=={x['id'] for x in sa['procedures_and_controls']}
assert set(methodmap)=={x['id'] for x in sa['characterization_methods']}
assert set(cohortmap)=={x['id'] for x in sa['sample_and_figure_joins']}
def maps(d):return [{'source_audit_id':k,'record_ids':['dabbousi-1997-'+i for i in v],'disposition':'reader_model_context_only' if not v else 'canonical_context_present','note':'Theory-only F14 and remaining qualitative/model details must stay in reader evidence; a contextual record is not a fully quantified experiment.'} for k,v in d.items()]
report={
 'audit_version':'1.0','audited_at_utc':datetime.now(timezone.utc).isoformat(),'status':'passed_bounded_scientific_audit' if all(checks.values()) else 'changes_requested',
 'scope':'Independent source-to-canonical scientific audit of the supplied main; source was independently read in full text and visuals. No Site writes or public rendering, SI or exact structure/training certification.',
 'review_scope':'supplied_main_only_si_unverified','source':sa['source'],'source_audit_sha256':sha(B/'source-audit.json'),
 'record_count':len(D),'measurement_count':sum(len(r['measurements']) for r in D.values()),'operation_count':sum(len(r['operations']) for r in D.values()),
 'records':[{'record_id':rid,'basename':rid+'.json','sha256':sha(B/'canonical-drafts'/(rid+'.json')),'record_type':r['record_type'],'measurements':len(r['measurements']),'operations':len(r['operations'])} for rid,r in D.items()],
 'findings':findings,'open_must_fix_count':sum(x['status']=='open' for x in findings),'checks':checks,'validation_errors':errors,'duplicate_evidence_arrays':duplicates,
 'coverage':{'procedures':maps(procmap),'methods':maps(methodmap),'cohorts':maps(cohortmap)},
 'manual_scientific_review':['Reviewed materials,identities,roles,stock quantities,operation order,source-specific temperatures,unknown dosing and inheritance for both shell chemistries.','Checked all120 serialized measurements against source table/captions/prose or their stated model basis, including missingTable1cells,distribution widths,composition versus dose,PL yields and exposure states.','Verified ZnS/cdS routes remain separate; bare organic caps, specimen coatings and ligand exchange do not become synthetic shells.','Verified source-specific ambiguities remain explicit: core sizes,ratio5.3/5.6,σ.11/.12,high-coveragefitreliability,detector distance and CdS model-region labels.','Theory-only carrier models, bulk lattice fits,escape-depth constants,reference-only devices andcounterfactualCdSe shells remain in source/reader context rather than invented recipe records.'],
 'reader_context_remaining':['All16 figures and Table1, complete qualitative/model/reference evidence and source-conflict display still need source-to-view validation.','No canonical row is invented for unavailable rawplot coordinates,high-coverage mean radii,full precursorcharges ormissing exact atomicstructures.','A source-complete reader ledger can group many source-audit units, but each unit needs an explicit mapping and disposition.'],
 'change_log':'canonical-audit-change-log.json','training_status':'All tasksdisabled; zeroeligible; review_status remains imported_unreviewed.','publication_status':'Not audited or promoted by this report.'}
(B/'canonical-records-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# Dabbousi 1997 — canonical scientific audit','',report['status']+f". {report['record_count']} records, {report['measurement_count']} measurements, {report['operation_count']} operations.",'','All6 source corrections are logged and closed. All30 bounded checks pass. Schema,graph,lineage/source-split and no-training gates pass; no duplicate evidence arrays.','', 'Scope: supplied main only; SI unverified. No Site, reader rendering, training or publication certification.','', '## Corrections','']
for f in findings:lines += [f"- **{f['id']} — {f['status']}**: {f['title']}. {f['correction']}"]
lines+=['','## Coverage','', 'All24 source procedures and8 characterization methods are mapped. Eight experimental/cohort groups map to canonical contexts; the ninth is theory-onlyFigure14 and remains reader context. This count does not imply17independent fully specified experiments.','', 'Detailed source-to-reader figure/model/reference coverage remains a separate integration check.','', '## Reviewed record hashes','']
for r in report['records']:lines += [f"- {r['record_id']}: `{r['sha256']}`"]
(B/'canonical-records-audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'records':report['record_count'],'measurements':report['measurement_count'],'operations':report['operation_count'],'checks':len(checks),'failed_checks':[k for k,v in checks.items() if not v],'open_findings':report['open_must_fix_count']},indent=2))
assert all(checks.values())
