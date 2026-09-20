from pathlib import Path
import json,hashlib,copy
from datetime import datetime,timezone
O=Path(__file__).resolve().parent;P=O.parent;A=P/'source-extraction-revision-1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def serial(d):return json.dumps(d,sort_keys=True,ensure_ascii=False)
checks=[]
def ck(name,ok,detail=None):checks.append({'check':name,'passed':bool(ok),**({'detail':detail} if detail is not None else {})})
def diff(a,b,path=''):
 if type(a)!=type(b):return [(path,a,b)]
 if isinstance(a,dict):return sum([diff(a.get(k),b.get(k),path+'/'+k) for k in sorted(set(a)|set(b))],[])
 if isinstance(a,list):
  if len(a)!=len(b):return [(path,a,b)]
  return sum([diff(x,y,path+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))],[])
 return [] if a==b else[(path,a,b)]
oldfreeze=read(A/'package-freeze.json');freeze=read(P/'package-freeze.json')
ck('original_freeze_preserved',sha(A/'package-freeze.json')=='ca9640453f84ee64649ea34f723b717d8e418b3454936faf8e065280268f2594')
ck('effective_freeze_exact',sha(P/'package-freeze.json')=='3b261b2f0aec35ab5fd9452fa8a9fee87ece32d87ef9ef2b29e617d70a74ccc8')
preserved={x['original_path']:x for x in read(A/'preservation-manifest.json')['files']}
for path,h in oldfreeze['bound_files'].items():
 p=Path(preserved[path]['preserved_path']) if path in preserved else Path(path)
 ck('original_boundary_retained:'+path,sha(p)==h)
for path,h in freeze['bound_files'].items():ck('effective_boundary:'+path,sha(path)==h)
old=read(A/'source-facts.json');new=read(P/'source-facts.json')
om={x['id']:x for x in old['facts']};nm={x['id']:x for x in new['facts']}
newid='morrison2017-precursor-yield-results'
ck('one_new_fact',set(nm)-set(om)=={newid} and not(set(om)-set(nm)))
allowed={
 'morrison2017-crystal-mount':{'/quantities/0/approximate','/quantities/1/approximate','/quantities/2/approximate'},
 'morrison2017-hot-excess':{'/quantities/1/comparison','/quantities/1/raw_text'},
 'morrison2017-nmr-evolution':{'/claim','/quantities/2/comparison','/quantities/2/meaning'}
}
fact_deltas=[];reverse_quantities={}
for fid,a in om.items():
 b=nm[fid];delta=diff(a,b)
 ck('fact_delta_paths:'+fid,{x[0] for x in delta}==allowed.get(fid,set()))
 if delta:fact_deltas.append({'id':fid,'changes':[{'pointer':p,'before':x,'after':y}for p,x,y in delta]})
 for qa,qb in zip(a['quantities'],b['quantities']):
  if qa!=qb:reverse_quantities[serial(qb)]=qa
ck('all_approximate_dimensions',all(q['approximate'] is True for q in nm['morrison2017-crystal-mount']['quantities'][:3]))
q=nm['morrison2017-hot-excess']['quantities'][1]
ck('orange_bound_exact',q['value']==15 and q['comparison']=='<=' and q['raw_text']=='within 15' and q['unit']=='min')
q=nm['morrison2017-nmr-evolution']['quantities'][2]
ck('thiourea_observation_not_onset',q['value']==2 and q['unit']=='h' and q['comparison'] is None and q['raw_text']=='after 2' and 'exact onset unknown' in q['meaning'])
ck('thiourea_conflict_retained','C6' in nm['morrison2017-nmr-evolution']['conflict_ids'])
y=nm[newid];q=y['quantities'][0]
ck('results_yield_exact',q['value']==60 and q['comparison']=='>=' and q['unit']=='%' and q['raw_text']=='≥60')
ck('results_yield_scope',y['sample_scope']=='precursor-powder' and y['evidence'][0]['pdf_page']==3 and 'distinct' in y['claim'] and 'does not create additional' in y['claim'])
ck('experimental_yield_unchanged',nm['morrison2017-precursor-yield']==om['morrison2017-precursor-yield'])
ck('protocol_count_unchanged',len(old['protocols'])==len(new['protocols'])==10)
for pa,pb in zip(old['protocols'],new['protocols']):
 restored=copy.deepcopy(pb)
 for op in restored['operations']:
  op['quantities']=[copy.deepcopy(reverse_quantities.get(serial(q),q)) for q in op['quantities']]
 ck('only_corresponding_protocol_quantity_copies:'+pa['id'],restored==pa)
 for op in pb['operations']:
  supported=[q for fid in op['source_fact_ids'] for q in nm[fid]['quantities']]
  for i,q in enumerate(op['quantities']):ck('operation_quantity_binding:'+op['id']+':'+str(i),q in supported)
measurements={x['id']:x for x in new['measurements']}
for f in new['facts']:
 for i,q in enumerate(f['quantities'],1):
  m=measurements[f['id']+'-q'+str(i)]
  ck('measurement_quantity:'+m['id'],m['quantity']==q)
  ck('measurement_sample:'+m['id'],m['sample_scope']==f['sample_scope'] and m['source_fact_id']==f['id'] and m['claim_class']==f['claim_class'])
ck('exact_measurement_count',len(new['measurements'])==sum(len(f['quantities'])for f in new['facts'])==185)
for sa,sb in zip(old['samples'],new['samples']):
 restored=copy.deepcopy(sb);restored['source_fact_ids']=[x for x in restored['source_fact_ids'] if x!=newid]
 ck('sample_scope_unchanged:'+sa['id'],restored==sa)
for key in set(old)-{'revision','extracted_at','facts','measurements','protocols','samples','counts'}:
 ck('other_source_field_unchanged:'+key,old[key]==new[key])
for key in ['facts','scalar_or_range_quantities_in_facts','source_units']:
 ck('count_increment:'+key,new['counts'][key]==old['counts'][key]+1)
for key in set(old['counts'])-{'facts','scalar_or_range_quantities_in_facts','source_units'}:
 ck('other_count_unchanged:'+key,old['counts'][key]==new['counts'][key])
ck('all_tables_unchanged',read(A/'source-tables.json')['tables']==read(P/'source-tables.json')['tables'])
ck('all_asset_manifest_unchanged',read(A/'original-assets-manifest.json')==read(P/'original-assets-manifest.json'))
for a in read(P/'original-assets-manifest.json')['assets']:ck('all_asset_bytes_unchanged:'+a['id'],sha(a['path'])==a['sha256'])
mechanical=read(O/'mechanical-checks-v2.json')
ck('mechanical_current_pass',not mechanical['failures'] and mechanical['source_package_sha256']==sha(P/'package-freeze.json'))
ck('all_training_tasks_empty',new['training_status']['requested_tasks']==[] and new['training_status']['exact_pairs']==0 and new['structure_status']['exact_structure_recipe_admission'] is False)
delta={'schema':'mattersyn.independent-source-delta-check.v1','reviewer':'/root/peng1998_reader_assets','at':datetime.now(timezone.utc).isoformat(),'old_freeze_sha256':sha(A/'package-freeze.json'),'new_freeze_sha256':sha(P/'package-freeze.json'),'fact_deltas':fact_deltas,'added_fact':y,'checks':checks,'check_count':len(checks),'failures':[c for c in checks if not c['passed']]}
(O/'delta-check-v2.json').write_text(json.dumps(delta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if delta['failures']:print(json.dumps(delta['failures'],ensure_ascii=False,indent=2));raise SystemExit('Delta failures; no final pass saved.')

manual=[
 {'scope':'Identity and pairing','locators':'Main1,8–10; SI1,17','assessment':'The title, six authors, main DOI and associated-content declaration match the supplied SI. The SI title page does not print the DOI; its content establishes the pairing. Four original files are two byte-identical pairs of PDF1.5 documents, with10main and17SI pages.'},
 {'scope':'Precursor preparation and missing upstream recipes','locators':'Main1–3','assessment':'The aqueous cadmium/ammonium-PTC charge, addition order, stirring, filtration, ice-chilled DI-water/ethanol washes, vacuum drying and yield are preserved. The cited NH4PTC and starting CdSe-belt procedures remain absent. Powder formula, solvated crystal formula, and solution speciation are distinct.'},
 {'scope':'Precursor characterization','locators':'Main2–4; SI2–6,9','assessment':'All reported NMR shifts, multiplicities, proton counts and coupling constants, melting/decomposition temperature, absorption maximum, elemental percentages, solubilities and IR assignments were checked. The conflicting IR labels and solid versus solution nuclearity remain explicit.'},
 {'scope':'Diffraction and precursor crystal tables','locators':'Main2–4; SI3–6','assessment':'All six structural tables, all uncertainties, coordinate/displacement scaling, atom labels and symmetry operations were visually read and independently numerically compared. These are measured Cd(PTC)2·THF precursor crystal data. No CdSe/CdS product coordinates or external CIF were inferred. Approximate mount dimensions remain distinct from precise Table1 dimensions.'},
 {'scope':'Decomposition and control branches','locators':'Main3,5–6; SI7–8,12–14','assessment':'DMSO-d6 NMR, THF powder, narrative DMSO70°C powder and added-base controls have separate quantities and missing fields. The printed12mg/0.003mmol conflict, n-octylamine/aniline identity wording, main/SI thiourea observation discrepancy and THF/DMSO EDS provenance conflict remain visible.'},
 {'scope':'Controlled shell synthesis and workup fractions','locators':'Main3,6–7','assessment':'The0.512g charge is dispersion mass. The three initial wash cycles,2mL10mM precursor/THF,66°C, sampling times, ideal3h and estimated1.0–1.5monolayer dosage retain their source meanings. Optical aliquot workup and separate TEM preparation keep the precipitate fractions, amine exchange and unknown repeat counts/volumes explicit.'},
 {'scope':'Excess-precursor branch','locators':'Main4–6; Figures3–5','assessment':'Room-temperature optical evolution and back exchange are distinct from the70°C thick-shell branch. All printed wavelengths, energy shifts, times and quantum yields were checked. Thick spiny morphology and epitaxial/islanding explanations are not treated as directly measured atomic trajectories.'},
 {'scope':'Monolayer properties and sample joins','locators':'Main6–8; Figures7–9; SI15–16','assessment':'The red absorption and blue PL curves in Figure7 have an explicit same-specimen join. Broader TEM/XRD/optical batch identity remains unknown. The514meV shift,1.53%QY,3.65%c-axis compression,approximately300thickness measurements,2.5±0.2nm total thickness and0.7±0.2nm combined top/bottom shell are correctly distinguished from cited core/lattice values and inferred one-monolayer-per-face interpretation.'},
 {'scope':'All table data','locators':'Main Tables1–2; SI TablesS1–S5 and FigureS7','assessment':'All8tables,145rows and471cells were read visually, including445numeric-or-bound cells and26text/null cells. Parenthetical uncertainties, printed scaling, strict upper bounds and missing entries were independently recalculated or compared. The EDS source row-layout qualification is retained.'},
 {'scope':'Mechanisms and model quantities','locators':'Main6,8; SI11,14','assessment':'All three reaction equations and both schemes were viewed. Base catalysis, L/Z exchange, shell islanding and p1/p2 NMR interpretations remain author models. The191.37g mass-balance basis is illustrative, not a synthesis charge. No kinetic curve digitization, fit or unreported reaction intermediate geometry was produced.'},
 {'scope':'Figure and crop integrity','locators':'All30selectedoriginalcrops','assessment':'Each actual crop was opened individually after inspection of every full source page. Axes, legends, panel labels, scale bars, captions, Greek symbols, primes, table definitions and footnotes are readable. FigureS9a/b intentionally continues to theS9c crop and full caption. Original traces and images are retained.'},
 {'scope':'References, source version and admission','locators':'Main8–10; SI1,17; frozen extraction metadata','assessment':'All50main and2SI references were read as bibliography, with separate namespaces and no claim that cited papers were inspected. The corrected-artwork notice, CCDC1560097 reference, funding and author information are retained. No original CIF or electronic structure factors are supplied, no product coordinates are recovered, and no training task or exact-pair eligibility is approved.'}
]
inspection=read(O/'inspection-record-v1.json')
findings=read(O/'findings-v1.json')['findings']
bound=dict(freeze['bound_files'])
for p in [P/'package-freeze.json',P/'source-correction-history.json',O/'check_source.py',O/'check_source_v2.py',O/'save_inspection.py',O/'finalize_audit.py',O/'findings-v1.json',O/'inspection-record-v1.json',O/'mechanical-checks-v1.json',O/'mechanical-checks-v2.json',O/'independent-table-tokens.json',O/'independent-table-tokens-v2.json',O/'delta-check-v2.json']:
 bound[str(p)]=sha(p)
report={'schema':'mattersyn.independent-scientific-source-audit.v2','status':'passed','reviewer':'/root/peng1998_reader_assets','author':'/root/backlog_eta','at':datetime.now(timezone.utc).isoformat(),'source_id':'morrison2017','doi':'10.1021/acs.inorgchem.7b01711','source_generation':2,'bundle_sha256':freeze['bundle_sha256'],'effective_source_revision':2,'package_freeze_sha256':sha(P/'package-freeze.json'),'source_facts_sha256':sha(P/'source-facts.json'),'source_inventory_sha256':sha(P/'source-inventory.json'),'source_tables_sha256':sha(P/'source-tables.json'),'scope':'Independent audit of the complete supplied main/SI source extraction, scientific scope, typed quantities, original assets and bounded author corrections. Not a canonical, model, website, browser or training-admission audit.','actual_reading':{'main_text_pages':list(range(1,11)),'main_visual_pages':list(range(1,11)),'si_text_pages':list(range(1,18)),'si_visual_pages':list(range(1,18)),'actual_individually_viewed_selected_crop_ids':[a['id'] for a in inspection['actual_selected_crops_viewed']],'external_papers_or_CIFs_read':[]},'coverage_counts':{'facts':72,'source_units':176,'materials':29,'stocks':5,'protocols':10,'operations':24,'sample_contexts':30,'fact_quantities':185,'tables':8,'table_rows':145,'table_cells':471,'numeric_or_bound_table_cells':445,'text_or_null_table_cells':26,'selected_original_assets':30,'references':52},'manual_scientific_scope_checks':manual,'mechanical_checks':{'source_and_table_checks':mechanical['check_count'],'bounded_revision_checks':len(checks),'total_supporting_checks':mechanical['check_count']+len(checks),'failure_count':0,'not_a_substitute_for_manual_source_reading':True},'resolved_findings':[dict(f,resolution='Corrected in source revision2 and independently rechecked; original version preserved.')for f in findings],'open_author_corrections':[],'retained_source_conflicts':new['contradictions'],'retained_missingness':new['gaps'][:9],'inspection_record_locator_addendum':'The initial inspection note compressed two SI locator ranges incorrectly. Final scope locators above are controlling: structural TablesS1–S4 are SI3–6, NMR FiguresS2/S3 are SI7–8. All27original pages were actually read/viewed; this corrects audit prose only, with no author source or numerical change.','bound_files':bound,'bound_file_count':len(bound),'source_files_mutated':False,'author_files_mutated_by_reviewer':False,'site_ledger_or_publication_mutated':False,'training_admission_approved':False,'product_atomic_model_approved':False,'website_integration_approved':False}
for name,data in [('independent-audit-v2.json',report),('independent-audit.json',report)]:
 p=O/name
 if p.exists():raise RuntimeError('Refusing to overwrite frozen audit '+str(p))
 p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=f'''# Morrison2017 independent source audit

Passed the frozen source extraction revision2 after four bounded author corrections. The original source package and all original PDFs remain preserved.

- Scope: all10main and17SI pages read and visually inspected; all30selected crops opened individually.
- Checked72facts,176source units,29materials,5stocks,10protocols/24operations,30sample contexts and185fact quantities.
- All8tables/145rows/471cells match the source, including uncertainties, scaling, bounds and nulls. All52bibliographic entries retain main/SI identity.
- {mechanical['check_count']} source/table checks and {len(checks)} bounded revision checks passed. These support the manual scientific review described in the JSON.
- Corrections: three approximate crystal-dimension flags; the≤15min orange-observation bound; a separate Results≥60%yield statement; and2h thiourea observation time without a fabricated strict onset bound.
- Ten source discrepancies remain explicit. No original CIF is supplied; precursor Cd(PTC)2·THF coordinates are not product CdSe/CdS coordinates. Upstream cited-only methods and sample-identity gaps remain unresolved.

This audit does not approve canonical records, molecular/crystal models, website integration, browser presentation or training admission. Fulltext and whole-page caches remain private source evidence.

Effective package SHA256: `{report['package_freeze_sha256']}`

Effective facts SHA256: `{report['source_facts_sha256']}`

Audit JSON SHA256: `{sha(O/'independent-audit.json')}`

Bound files: {len(bound)}. The JSON contains the complete manual scope, correction history, source conflicts and exact hash boundary.
'''
# Spacing in the narrative is kept readable without changing raw source tokens.
for a,b in [('all10main','all 10 main'),('and17SI','and 17 SI'),('all30selected','all 30 selected'),('Checked72facts','Checked 72 facts'),('176source','176 source'),('29materials','29 materials'),('5stocks','5 stocks'),('10protocols/24operations','10 protocols / 24 operations'),('30sample','30 sample'),('185fact','185 fact'),('All8tables/145rows/471cells','All 8 tables / 145 rows / 471 cells'),('All52bibliographic','All 52 bibliographic'),('the≤15min','the ≤15 min'),('Results≥60%yield','Results ≥60% yield'),('and2h','and 2 h')]:md=md.replace(a,b)
(O/'independent-audit.md').write_text(md,encoding='utf-8')
print(json.dumps({'status':'passed','audit':str(O/'independent-audit.json'),'sha256':sha(O/'independent-audit.json'),'checks':report['mechanical_checks'],'bound_files':len(bound)},indent=2))
