"""Private Heo planning only; no records, structures, shared state or source edits."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib
import json

H = Path(__file__).resolve().parent
S = H.parents[4] / 'recipe-atlas'
def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
facts = read(H/'source-facts.json')['facts']
inventory = read(H/'source-inventory.json')
tables = read(H/'main-tables.json')
audit = read(H/'source-scientific-audit.json')
progress = read(H/'si-numerical-progress-index.json')
schema = read(S/'dist/data/record.schema.json')
bound = {}
checks = []
def check(label, ok):
    checks.append({'check':label,'passed':bool(ok)})
    if not ok: raise AssertionError(label)
def bind(p, expected=None):
    p=Path(p).resolve(); h=sha(p); bound[str(p)]=h
    if expected: check('Existing evidence hash: '+str(p),h==expected)
    return h
def ref(name, pointer, identity=None):
    p=H/name; value=read(p)
    for token in pointer.split('/')[1:]:
        token=token.replace('~1','/').replace('~0','~')
        value=value[int(token)] if isinstance(value,list) else value[token]
    check('Source pointer resolves: '+name+pointer,True)
    return {'source_file':name,'json_pointer':pointer,**({'source_item_id':identity} if identity else {})}

for item in audit['audited_artifacts']: bind(item['path'],item['sha256'])
for doc in inventory['source_documents'].values():bind(doc['path'],doc['sha256'])
for p in [H/'source-scientific-audit.json',H/'source-scientific-audit.md',H/'si-numerical-progress-index.json',S/'scripts/schema_definition.py',S/'scripts/dataset_lib.py',S/'dist/data/record.schema.json']:
    bind(p)
for page in range(1,10):bind(H/f'main-{page:02}.txt')
for c in progress['chunks']:
    for kind in ['transcription','audit']:bind(c[kind]['path'],c[kind]['sha256'])

scopes=[
 ('in66-route','literature_protocol','One Na-X → Tl-X → In-X → H2S-treated In66-X route','Nine preparation/synthesis/workup/handling operations. The tenth inventory step is a handoff to separate characterization contexts. One reported batch family; condition conflicts are not successful variants.'),
 ('single-crystal-acquisition','procedure','Single-crystal diffraction acquisition','Sealed final crystal at 294 K; acquisition and absorption-correction trial are separate from synthesis conditions.'),
 ('epxma-acquisition','procedure','EPXMA/EDS specimen and measurement context','Post-diffraction, atmosphere-exposed final crystal; parent control and copied reference-34 spectrum remain distinct.'),
 ('xps-acquisition','procedure','XPS and Ar depth-profile acquisition','Final product, parent In87-X comparison and metal reference have distinct sample IDs. Sputter-history gap retained.'),
 ('average-structure','observation','Adopted Fd-3m average In66-X structure','Tables 2–4 and Figures 5–7; same final single crystal. Atom sites and geometry are refinement outputs, not separate preparations.'),
 ('refinement-comparison','observation','Alternative space group and refinement iterations','Fd-3 is a trial model of the same diffraction study. Five successive occupancy/refinement stages are models, not five experiments.'),
 ('ionic-radius-comparison','observation','Author-derived ionic radii and cited comparisons','All Table 5 rows, including averages and two current refinement columns. No radius is a measured nanocluster diameter.'),
 ('framework-topology','observation','Zeolite topology and site definitions','Figure 4 background schematic; no measured ordered Si/Al framework is inferred from its alternating illustration.'),
 ('charge-and-mechanism','observation','Charge, disproportionation and compensation hypotheses','Eight equations, site-charge interpretations, possible O loss/H compensation and local arrangements. No confirmed sulfide product or added/deleted coordinate sites.'),
 ('reference-and-outlook','observation','Cited historical comparisons and proposed applications','Cited failures are not failed trials in this paper; no measured optical/device/transport or success labels.')
]
scope_rows=[{'plan_scope_id':k,'candidate_record_type':t,'title':title,'boundary':b,'record_created':False,'requested_tasks':[]} for k,t,title,b in scopes]
scope_ids={x[0] for x in scopes}

fact_groups={k:[] for k,_,_,_ in scopes}
def group(f):
    s=f['id'].removeprefix('heo2003-')
    if s.startswith('epxma-'):return 'epxma-acquisition'
    if s.startswith(('xps-','sputter-')) or s in ['in-metal-xps','atomic-like-xps','depth-prose']:return 'xps-acquisition'
    if s in ['in-vapor-pressure','tl-vapor-pressure','prior-parent-sites','motivation','prior-exchange-failure','outlook']:return 'reference-and-outlook'
    if s in ['zeolite-description','site-definitions']:return 'framework-topology'
    if s in ['inIIa-radius']:return 'ionic-radius-comparison'
    if s.startswith(('equation-','oxygen-loss-','proton-')) or s in ['oxidation-assignment','cluster-charge','charge-deficit','supercage-filling','extra-ligand','inU-density','h2s-site-increase','cluster-stability','scattering-model']:return 'charge-and-mechanism'
    if s in ['refinement-stages','alternative-si-al-distance','data-ratio-mismatch']:return 'refinement-comparison'
    if s.startswith('xrd-') or s in ['cell-reflections','background-count','absorption-correction','reflection-conditions','refinement-method','weight-model']:return 'single-crystal-acquisition'
    if s.startswith('table2-') or s in ['unit-cell','space-group','si-al-order','unrefined-peaks','cluster-count','ellipsoid-probability','cluster-bond','cluster-oxygen','cluster-size','cluster-spacing','dot-count']:return 'average-structure'
    return 'in66-route'
for i,f in enumerate(facts):
    k=group(f);fact_groups[k].append({'fact_id':f['id'],'source':ref('source-facts.json',f'/facts/{i}',f['id']),
        'destination_field_family':'materials/stocks/operations/products/measurements/quality' if k=='in66-route' else 'products/measurements/quality',
        'preserve_source_status':f['status'],'preserve_sample_scope':f['sample_scope']})

opmap=[]
for i,o in enumerate(inventory['protocols'][0]['steps']):
    opmap.append({'source':ref('source-inventory.json',f'/protocols/0/steps/{i}',o['id']),
      'destination_scope_ids':['epxma-acquisition','xps-acquisition'] if i==9 else ['in66-route'],
      'canonical_field_templates':['operations[]','material_states[]'],
      'stage_plan':'characterization' if i==9 else 'workup' if i in [4,5,7,8] else 'precursor_preparation' if i==0 else 'synthesis',
      'retained_fraction_plan':'Retain the treated crystal through workup; no quantitative residue-removal or isolated-powder yield is reported.',
      'source_conflict_or_missingness':o['missingness_or_conflict']})
materials=[]
for i,m in enumerate(inventory['materials']):
    disposition='Preserve identity, role and source-specific notes; do not create geometry or assign unreported quantities.'
    if m['id']=='heo2003-water':disposition='Two source-role slots: aqueous-feed water, purity unspecified; explicitly deionized wash water. Reuse H2O identity without transferring grade.'
    if m['id']=='heo2003-ar':disposition='Characterization sputtering gas only, never synthesis atmosphere.'
    if m['id']=='heo2003-pyrex':disposition='Apparatus/context inventory; never a chemical precursor, dopant or measured host element.'
    if m['id']=='heo2003-surface-powder':disposition='Unidentified surface residue, formula null. Candidate In2O/In2S/InS/In identities remain hypotheses, not separate products/routes.'
    materials.append({'source':ref('source-inventory.json',f'/materials/{i}',m['id']),'name':m['name'],'role_as_source':m['role'],'disposition':disposition})

tabmap=[]
tabdest=['in66-route + single-crystal-acquisition + refinement-comparison','average-structure','average-structure','average-structure + charge-and-mechanism','ionic-radius-comparison']
tabnotes=[
 '17 shared rows: preparation rows → operation parameters; diffraction rows → acquisition conditions. Ten model rows retain the two space-group columns. All three equation footnotes and the m/s definition conflict survive.',
 'Nine atom rows: preserve xyz, all six literal Uij columns, multiplicity, fixed and varied counts separately, raw precision, ESD and symmetry-fixed marks. Scalar measurement rows may reference the complete typed sidecar; do not reduce to nominal formula.',
 '23 geometry values retain atom sequences, symmetry-fixed versus refined status, ESDs and both blocks. Use for later symmetry/coordinate checks, not a second sample count.',
 'Four signed offsets retain their oxygen ring plane and its own sign convention. Separate tentative charge assignments from geometric values; preserve II versus II′ heading conflict.',
 '34 author-derived radii and six source blanks in ten rows. Preserve four site/charge column definitions, all 13 footnotes, cited-reference numbers, current selected/trial models and averages. Do not use as particle sizes.'
]
for i,t in enumerate(tables['tables']):tabmap.append({'source':ref('main-tables.json',f'/tables/{i}',t['table_id']),'destination_scopes':tabdest[i],'mapping':tabnotes[i],'raw_table_sidecar_required':True})

figmap=[]
figscopes=[['epxma-acquisition'],['xps-acquisition'],['xps-acquisition'],['framework-topology'],['average-structure'],['average-structure','charge-and-mechanism'],['average-structure']]
samples=[
 ['A: final In66-X, atmosphere-exposed after diffraction','B: parent In87-X spectrum copied from reference 34; not the same measured product'],
 ['A: In metal reference, source caption scaling 1/20','B: final In66-X','C: parent In87-X comparison; same exact physical parent as other controls not established'],
 ['Final In66-X depth-profile specimen; measurement sequence and sputtered state distinct from sealed diffraction state'],
 ['Generic zeolite-X framework/site convention; no exact sample link'],
 ['Final average-model supercage; possible partially occupied local arrangement, not a unique observed microstate'],
 ['Final average-model sodalite In5 cluster; proposed +7 charge separate from positions'],
 ['Adjacent sodalite units in the final average model; coordinate-derived center spacing, not microscopy']]
for i,f in enumerate(inventory['figures']):figmap.append({'source':ref('source-inventory.json',f'/figures/{i}',f['id']),'destination_scope_ids':figscopes[i],'sample_associations':samples[i],'asset_id':f['asset_id'],'original_source_scope':f['scope']})

atom_checks=[]
for i,row in enumerate(tables['tables'][1]['rows']):
    n=row['quantities']['occupancy: fixed']['value'];mult=row['wyckoff']['multiplicity']
    atom_checks.append({'source':ref('main-tables.json',f'/tables/1/rows/{i}',row['row_id']),'label':row['atom_label'],'wyckoff_as_printed':row['wyckoff']['raw'],
      'reported_fixed_atoms_per_conventional_cell':n,'reported_multiplicity':mult,'prospective_site_fraction':n/mult,
      'fraction_status':'calculated_planning_arithmetic_only','formula':'fixed atom count / reported multiplicity; validate actual symmetry before CIF use',
      'special_caveat':'Mixed (Si,Al) table model is 96 Si + 96 Al: if encoded as coincident species, each occupancy is 0.5; do not silently substitute nominal 100/92.' if i==0 else 'Fixed versus varied refinement columns are not two experimental samples.'})

plan={
 'schema':'mattersyn.private-canonical-mapping-plan/1','source_id':'heo2003','doi':inventory['doi'],'author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),
 'evidence_root':str(H),'source_reference_contract':'Every source_file is resolved relative to evidence_root; json_pointer is an actual checked RFC 6901 pointer in that existing JSON artifact. Canonical field templates are proposed schema destinations, not claims of existing records.',
 'status':'planning_only_not_canonical_or_independent_scientific_approval',
 'scope':'Reuse existing independently audited main narrative/tables and source inventory. Targeted reread of cached main pages 2–3 for preparation/specimen/refinement linkage. No repeat full-source audit; no external research, source edits, records, CIF, models, exports or publication.',
 'source_dependency':{'main_audit_path':str(H/'source-scientific-audit.json'),'main_audit_status':audit['status'],'main_pages':9,'main_facts':len(facts),'main_tables':tables['counts'],'historical_pending_labels':'Frozen author artifacts retain their old pending flags; independent main audit is the scope authority. Do not edit them or interpret old summary flags as a new failure.'},
 'schema_plan':{'versions_available':schema['properties']['schema_version']['enum'],'preferred_existing_version':'1.3.0','record_types_used':sorted({x['candidate_record_type'] for x in scope_rows}),
  'quantity_handling':'Preserve raw text, unit, approximation, basis and evidence. The current quantity schema has no dedicated ESD/tensor/table fields: retain ESD in raw_text and qualifier and keep typed main-tables.json as a linked provenance sidecar. Do not add unsupported schema keys or flatten the table away.',
  'source_status_translation':{'reported/refined/reported_refinement':'reported, with technique and qualifier explicitly identifying refinement output','author_derived':'author_derived','author_model/author_interpretation/author_hypothesis/author_outlook':'inferred, with note explicitly crediting the authors and retaining the original claim class; not a measured label','cited_reference':'reported as a quotation/summary in the inspected main article; full cited work uninspected, no imported experiment','source_conflict':'reported statement with both conflicting values and explicit unresolved conflict','not_supplied_or_blank':'not_reported, value null; never zero'},
  'measurement_sample_requirement':'Each measurement needs a declared local product/context sample ID. Reference/model contexts use general_context or unresolved recipe links; do not attach their values to the current route as direct outcomes.',
  'host_representation':'intended_target.host = zeolite X; distinguish guest indium clusters from extended aluminosilicate host. Do not index this as a free colloidal In particle preparation.'},
 'route_and_variant_policy':{'reported_route_count':1,'verified_distinct_successful_variants':0,'proposed_scope_count':len(scope_rows),'source_operations':10,'synthesis_handling_operations':9,'characterization_handoff_steps':1,
  'conflicting_conditions':'Store source-prose and Table 1 values under clearly labeled conflict representations (condition_options labels must say source conflict, not experimental alternatives). No unique resolved default duration/temperature, no arbitrary choice, no pseudo-replicates.',
  'upstream_boundary':'Starting Na-X synthesis is cited to reference 28, not supplied. Tl exchange/redox/wash/redehydration steps described here remain in this route. Cited In-A, In88-X and In87-X experiments are context only.'},
 'candidate_scopes':scope_rows,'fact_mapping':fact_groups,'operation_mapping':opmap,'material_mapping':materials,
 'stock_mapping':[{'stock_id_candidate':'heo2003-thallous-acetate-feed','components':['thallous acetate','water, feed purity unspecified'],'concentration':'0.1 mol/L reported','pH':'6.4 reported','reported_use_volume':'10.0 mL in Table 1; passed/reservoir/stock-preparation basis unresolved','preparation':'No solute mass, stock preparation operation, mixing time, storage or shelf-life reported; do not invent an operation merely to populate preparation_operation_ids.','target_fields':['stocks[].components','stocks[].concentrations','stocks[].scope','operations[].parameters'],'source_refs':[ref('source-facts.json','/facts/5'),ref('source-facts.json','/facts/6'),ref('main-tables.json','/tables/0/shared_rows/1')]}],
 'table_mapping':tabmap,'figure_mapping':figmap,
 'equation_mapping':[{'source':ref('source-inventory.json',f'/chemical_equations/{i}',x['id']),'destination_scope':'charge-and-mechanism','status':'author hypothesis; preserve formula and chemical interpretation, never generated reaction products or measured charge balance'} for i,x in enumerate(inventory['chemical_equations'])],
 'reference_mapping':{'source':ref('source-inventory.json','/references'),'count':len(inventory['references']),'destination':'source/context appendix with exact original IDs; references 28, 32–35, 39–42 and cited scattering/comparison papers do not become fully read source records'},
 'cif_feasibility':{
  'verdict':'Sufficient published ingredients for a candidate derived average-structure CIF, conditional on independent crystallographic validation; no CIF is created or approved here.',
  'available':{'cell_a_angstrom':'24.942(4)','system':'cubic','data_collection_temperature_K':294,'adopted_space_group':'Fd-3m, No. 227','alternative_model':'Fd-3, No. 203, not an independent phase or experiment','asymmetric_table_rows':9,'coordinate_scale':'printed xyz ×10^5; convert by 10^-5 with ESD','displacement_scale':'printed Uij ×10^4; 10^-4 and Å² from the stated cubic temperature-factor expression','occupancy_basis':'atoms/ions per conventional cell; not site fractions'},
  'site_fraction_planning':atom_checks,
  'required_validation':['Confirm space-group origin/setting from Table 2 coordinates and the printed Wyckoff labels; do not choose a default origin solely from group number.','Derive a=b=c and 90° angles from the stated cubic symmetry, recording that derivation; do not present missing cell angles as independently measured numbers.','Validate symmetry expansion and deduplication against multiplicities, weighted In66/T192/O384 totals and all Table 3 distances/angles, Table 4 plane offsets and Figures 5–7.','Preserve mixed Si/Al scatterer as the published average 96/96 representation and retain the nominal 100/92 discrepancy. Do not fabricate site-specific Si/Al ordering.','Use final fixed occupancies, retaining freely varied values/ESDs as refinement history. In(II)=25/32 and In(IIa)=1/32; their local correlations remain unknown.','Retain exact literal U12/U13/U23 values; independently test tensor/space-group compatibility and positive definiteness. Do not permute or repair entries silently. If a coordinate-only file omits ADPs, label it explicitly as omitting supplied ADPs, not a full reproduction.','Run a CIF parser/round trip, symmetry, cell-content and geometry checks, and independently review provenance before supplying a downloadable model. No such checks were performed in this planning pass.'],
  'cannot_support':['A uniquely ordered, charge-neutral microscopic arrangement or DFT-ready supercell. Partial occupancies and lost Si/Al ordering do not resolve a particular local configuration.','Measured sulfur, extra ligand, hydrogen positions, oxygen vacancies or exact site oxidation states. Proposed 4.5 missing O or 9 H+ per cell must not alter measured sites.','A free-standing colloidal indium particle or unique finite nanocrystal surface. The 0.15 mm host crystal, approximately 3.5 Å author-derived cluster radius and approximately 10.8 Å spacing are different quantities.','A complete experimental-CIF-to-exact-recipe pair: inconsistent dehydration/redox conditions, unreported reagent amounts/flow/vacuum details and current source-completion gates remain.'],
  'asset_role_after_future_validation':'measured_sample may describe a faithful file derived from reported refinement, with explicit averaged/disordered provenance; eligible_as_measured_label remains false until a separate asset and sample-link decision. No asset entry at this plan stage.',
  'si_boundary':'Reflection indices h,k,l and Fcal²/Fobs²/ESD are diffraction observations/model predictions, not atomic coordinates. Reflections are not a prerequisite for CIF syntax and their completion does not resolve the recipe conflicts or microscopic disorder. Never substitute them for Table 2.'},
 'si_dependency_snapshot':{'as_of':progress['at'],'audited_pages':progress['transcribed_and_independently_audited_pages'],'rows':progress['rows'],'numeric_cells':progress['numeric_cells'],'unresolved_signs':progress['uncertain_signs'],'remaining_pages_at_snapshot':progress['remaining_untranscribed_and_unaudited_pages'],'complete':progress['complete_SI_numerical_review'],'progress_path':str(H/'si-numerical-progress-index.json'),'policy':'This is an existing checkpoint snapshot, not a new SI audit. Preserve raw Fobs² negatives, null signed values with both candidates, printed precision, unknown intensity units and raw o-like markers; model max(Fo²,0) is only a weight equation. Require final chunk/aggregate audits before describing full SI numerical coverage.'},
 'unresolved_gaps':[x['description'] for x in inventory['evidence_conflicts']]+['Upstream Na-X and cited parent/comparison papers are uninspected; host count, In charge, flow and temperature-gradient details are absent.','No raw EDS/XPS trace digitization or fitted peak-area table; source image and stated energy assignments remain available.','No supplied TEM/SAED, Raman, absorption/PL, device transport, individually addressed dots or demonstrated data storage.','Source rows/table ESDs are already audited; this plan does not renew or expand the scientific audit.'],
 'training_plan':{'requested_tasks_now':[],'future_candidates':['precursor_selection: only after source/canonical/visual audits, explicit host identity and correct reagent-role review; H2S treatment does not establish a sulfide target.','partial_protocol: a possible explicitly incomplete route after audit; preserve conflicts and mask unavailable fields rather than claiming a complete executable SOP.'],
  'withhold':['exact_structure_recipe','size_conditioned_recipe','optical_outcome','success_prediction'],
  'exact_gate':'Current dataset_lib requires a reviewed nonduplicate record, explicitly linked eligible measured structure, no missing_fields and no typed not_reported protocol fields, plus explicit task request. A future valid average CIF alone cannot satisfy those conditions.',
  'size_gate':'Do not rename author-derived cluster radius or host cross-section to measured product diameter merely to satisfy the generic diameter gate.'},
 'no_mutations':{'site':True,'ledger':True,'memory':True,'source_or_frozen_evidence':True,'github':True},
 'reusable_input_paths':{'main_source':inventory['source_documents']['main']['path'],'si_source':inventory['source_documents']['si']['path'],'facts':str(H/'source-facts.json'),'inventory':str(H/'source-inventory.json'),'main_audit':str(H/'source-scientific-audit.json'),'main_tables':str(H/'main-tables.json'),'main_table_assets':str(H/'main-table-assets.json'),'original_crop_manifest':str(H/'root-asset-manifest.json'),'page_coverage':str(H/'page-coverage.json'),'main_text_pattern':str(H/'main-XX.txt'),'main_table_crop_pattern':str(H/'reader-assets/main-table-X.png'),'si_progress':str(H/'si-numerical-progress-index.json'),'schema':str(S/'dist/data/record.schema.json'),'schema_source':str(S/'scripts/schema_definition.py'),'validation_and_task_gates':str(S/'scripts/dataset_lib.py')},
}
check('All 114 facts mapped once',len(facts)==114 and Counter(x['fact_id'] for v in fact_groups.values() for x in v)==Counter(x['id'] for x in facts))
check('All ten operations accounted for',len(opmap)==10)
check('All eleven original material inventory entries accounted for',len(materials)==11)
check('All five tables, seven figures, eight equations and 71 references accounted for',len(tabmap)==5 and len(figmap)==7 and len(plan['equation_mapping'])==8 and len(inventory['references'])==71)
check('Current schema supports chosen record types',all(x['candidate_record_type'] in schema['properties']['record_type']['enum'] for x in scope_rows))
check('Current schema supports host and structure provenance fields','host' in schema['properties']['intended_target']['properties'] and 'eligible_as_measured_label' in schema['properties']['structure_assets']['items']['properties'])
check('Planned fixed In fractions sum to 66 atoms per cell',sum(x['reported_fixed_atoms_per_conventional_cell'] for x in atom_checks if x['label'].startswith('In'))==66)
check('Existing main audit passed only its explicit partial scope',audit['status']=='passed_for_declared_partial_scope' and not audit['overall_source_extraction_complete'])
bind(__file__)
plan['validation']={'kind':'planning pointer/hash/coverage checks only; not independent scientific audit','count':len(checks),'passed':True,'source_pointer_checks':sum(x['check'].startswith('Source pointer resolves:') for x in checks),'hash_checks':sum(x['check'].startswith('Existing evidence hash:') for x in checks),'coverage_and_schema_checks':[x for x in checks if not x['check'].startswith(('Source pointer resolves:','Existing evidence hash:'))]}
plan['bound_files']=bound
(H/'canonical-mapping-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md='''# Heo private canonical mapping plan

One reported preparation route is supported. The prose/Table 1 discrepancies are unresolved reports of that route, not independently successful variants; the two space groups and five refinement stages are models of the same diffraction study.

The provisional organization has one route, three acquisition procedures (single-crystal diffraction, EPXMA and XPS), and six observation/context scopes. It maps all 114 facts, 10 source operations, 11 original material entries, one aqueous thallous-acetate stock, five main tables, seven figures, eight equations and 71 references. These are proposed boundaries, not newly created canonical records. Feed water and explicitly deionized wash water require separate source-role slots; Ar belongs only to sputtering and Pyrex to apparatus.

The source-defined crystal proceeds through Na-X, Tl-X, black In-X, washing/redehydration, H2S treatment, evacuation and sealing. Nine preparation/handling steps remain with the route; the tenth source step hands the product to characterization. No unique dehydration setting is selected: prose 623 K/48 h versus Table 1 673 K/3 days, and In-contact 96 h versus 5 days, remain explicit. The H2S stage is 0.5 atm, 673 K, 12 h. Missing amounts, flow, reactor pressure and temperature-gradient details remain missing.

Table 1 separates process and diffraction parameters. Table 2 supplies nine average atomic sites with coordinates, displacement tensors and fixed/varied atom counts. Tables 3–4 supply geometry and signed ring-plane offsets, with tentative charges separate. Table 5 contains author-derived ionic radii, cited comparisons and model averages, not particle sizes. The schema lacks dedicated ESD/tensor cells, so retain the complete typed table sidecar and place raw uncertainties and provenance in supported quantity fields.

A future derived average-structure CIF is feasible in principle from a = 24.942(4) Å, cubic Fd-3m and Table 2, after origin/setting, symmetry, multiplicity, disorder, tensors and geometry are independently validated. Occupancies are atoms per conventional cell: In(II) gives 25/32 and In(IIa) 1/32 site fractions. The table's average 96 Si/96 Al differs from nominal 100 Si/92 Al and must stay explicit. Do not silently permute Uij columns or add hypothetical S/H/oxygen vacancies. A valid average CIF would not resolve a unique ordered, charge-balanced microscopic model or make this an exact-recipe training pair.

Figure 1 separates the current product from a parent spectrum copied from reference 34; Figure 2 separates product, parent and scaled metal reference; Figure 3 retains the sputter-history/depth gap. Figure 4 is topology, and Figures 5–7 are structural-model illustrations. Their nominal composition does not authorize new cross-specimen joins. The 0.15 mm host cross-section, approximately 3.5 Å author-derived cluster radius and approximately 10.8 Å model spacing are different observables.

SI reflection rows remain h,k,l and calculated/observed squared structure factors with ESDs, not atom coordinates. This plan records the existing pages 1–12 checkpoint, including two unresolved signs; the final two pages are a separate ongoing dependency. Preserve negatives and uncertain signs without clamping or guessing. No full SI approval is issued here.

All requested tasks remain empty at this planning stage. Precursor selection and an explicitly partial protocol may later be reviewed; exact-structure, size-conditioned, optical-outcome and success tasks remain withheld. No records, CIF, source edits, Site/ledger/memory or GitHub changes were made. This is a mapping plan using the prior main audit, not a repeat source audit.

The JSON contains exact reusable input paths, source JSON pointers, input hashes, scope assignments and mechanical coverage checks. Key inputs are `source-facts.json`, `source-inventory.json`, `source-scientific-audit.json`, `main-tables.json`, `main-table-assets.json`, `root-asset-manifest.json`, `page-coverage.json`, and `si-numerical-progress-index.json` beside this plan; the current Site schema and task-gate paths are also bound.
'''
(H/'canonical-mapping-plan.md').write_text(md,encoding='utf-8')
print(json.dumps({'status':plan['status'],'checks':len(checks),'bound_files':len(bound),'facts':len(facts),'candidate_scopes':len(scope_rows),'json_sha256':sha(H/'canonical-mapping-plan.json'),'md_sha256':sha(H/'canonical-mapping-plan.md')},indent=2))
