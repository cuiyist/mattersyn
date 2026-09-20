"""Private Friedfeld schema plan. This does not author or approve canonical records."""
from pathlib import Path
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib, json, re

C=Path(__file__).resolve().parent; F=C.parent
O=C/'mapping-draft-v1'
assert not O.exists() or not any(O.iterdir()), 'Preserve the existing mapping checkpoint; use a new version.'
O.mkdir(parents=True,exist_ok=True)
S=Path('[local path redacted]')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_bytes())
def save(n,x): (O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def resolve(x,p):
    for k in p.strip('/').split('/') if p else []:
        k=k.replace('~1','/').replace('~0','~'); x=x[int(k)] if isinstance(x,list) else x[k]
    return x
def key(s): return re.sub('[^a-z0-9]+','_',s.lower()).strip('_')
INPUTS=['source-facts.json','source-inventory.json','source-tables.json','page-coverage.json','original-assets-manifest.json','intake-identity.json']
initial={str(F/n):sha(F/n) for n in INPUTS}
D=read(F/'source-facts.json'); I=read(F/'source-inventory.json'); T=read(F/'source-tables.json')
SID='friedfeld2019'; PRE='friedfeld-2019-'; assert D['source_id']==SID
PAY={'source-facts.json':D,'source-tables.json':T}
FM={f['id']:f for f in D['facts']}; PM={p['id']:p for p in D['protocols']}
SC={x['id']:x for x in D['sample_contexts']}
R={}
def rec(k,title,typ,section,scope,protocol=None,target=None,notes=()):
    R[k]={'record_id':PRE+k,'proposed_record_type':typ,'title':title,'reader_section':section,
          'source_protocol_id':protocol,'intended_target_proposal':target,'scope':scope,
          'source_group':SID,'batch_id':None,'quality_review_status':'imported_unreviewed',
          'requested_tasks':[],'collection':None,'reader_role_promotion':None,
          'notes':list(notes),'field_pointers_are_templates':True}

rec('conversion-representative','Representative thermal conversion of InP clusters','literature_protocol','protocol',
    'Representative experimental sequence and no-additive temperature contexts; not four independently identified physical batches.',
    'conversion-family','InP', ['The representative 20.0 mg / 0.00121 mmol charge does not prove that every figure specimen used the same physical injection.',
    'Temperature options refer only to the printed no-additive series; observed sizes and fit slopes remain measurements.'])
rec('conversion-acid-additive','Myristic-acid perturbation of cluster conversion','protocol_variant','protocol',
    'Selected myristic-acid additions at the paired source temperatures, using the shared experimental sequence.',
    'conversion-family','InP', ['Only source-paired temperature/equivalent combinations may be selected; stock concentration and transfer volume remain unreported.',
    'The zero-equivalent control has no added acid; additive input is optional, not a mandatory material flow.'])
rec('conversion-indium-additive','Indium-myristate perturbation of cluster conversion','protocol_variant','protocol',
    'Selected indium-myristate additions and Table 1 rates; a rate table is not a table of full independent recipes.',
    'conversion-family','InP', ['Table columns establish temperature-to-rate pairing, not an inferred physical-batch identifier.',
    'The zero-equivalent control has no added salt; no theoretical yield is an isolated product mass.'])
rec('conversion-concentration','Initial-cluster-concentration variation','protocol_variant','protocol',
    'The printed concentration series at 250 and 300 degrees C, with changed injection quantities explicitly unresolved.',
    'conversion-family','InP', ['Do not copy the representative 20.0 mg / 0.00121 mmol MSC charge into changed-concentration variants.',
    'Report the selected reaction concentration as a condition, not as an unreported stock concentration.',
    'Inherited operations must cite the common procedure and state which condition-specific amounts are missing.'])
for p in D['protocols']:
    if p['id']=='conversion-family': continue
    section='protocol'
    if p['id'] in ['tem','xrd','scherrer-analysis']: section='structures'
    if p['id'] in ['nmr','uvvis','tga','dsc','optical-analysis','kinetic-analysis','acid-nmr']: section='properties'
    target='PhCH2-13CO2H' if p['id']=='labeled-acid-synthesis' else None
    rec(p['id'],p['title'],'procedure',section,
        'Source-defined '+p['kind']+'; neither a new QD synthesis nor a verified physical replicate.',p['id'],target)

OBS={
 'source-materials':('Precursors, solvents and source-qualified identities','precursors'),
 'cited-phosphine-context':('Cited phosphorus-precursor preparation','precursors'),
 'cluster-ligand-observations':('Cluster and ligand-exchange observations','properties'),
 'temperature-results':('Conversion-temperature and extended-aging observations','properties'),
 'concentration-results':('Concentration-dependent conversion and printed regressions','properties'),
 'additive-results':('Carboxylate-additive responses and source rate tables','properties'),
 'structural-results':('Microscopy, diffraction and domain-size observations','structures'),
 'thermal-results':('Solid-cluster thermal observations','properties'),
 'pretreatment-results':('Pretreatment-dependent spectral and conversion observations','properties'),
 'mechanistic-context':('Chemical intuition and cited mechanistic context','intuition'),
 'source-context':('Sources, reference inventory and limitations','sources')}
for k,(title,section) in OBS.items():
    rec(k,title,'observation',section,'Context only. No implied synthesis operation, missing recipe completion or exact sample join.')

GROUPS={
 'source-context':['identity','declaration'],
 'source-materials':['materials','co2-supply','solvent-treatment','glassware'],
 'cited-phosphine-context':['phosphine-gap'],
 'labeled-msc-cited':['labeled-msc'],
 'cluster-ligand-observations':['nmr-vt','abs-vt','acid-exchange','indium-exchange','si-nmr','si-acid-abs','si-exchange'],
 'conversion-representative':['conversion-charge','conversion-heat','conversion-inject','conversion-monitor','conversion-workup'],
 'labeled-acid-synthesis':['acid-charge','acid-condense','acid-react','acid-quench','acid-extract','acid-crystallize'],
 'acid-nmr':['acid-nmr'], 'nmr':['nmr-acquisition'],'uvvis':['uv-acquisition'],'tem':['tem-acquisition'],
 'xrd':['xrd-acquisition'], 'tga':['thermal-acquisition'],'optical-analysis':['optical-processing'],
 'temperature-results':['temperature-series','growth-time','si-growth-fits','si-ripening'],
 'structural-results':['tem-result','phase-result','scherrer-summary','si-xrd','si-fft','si-scherrer'],
 'pretreatment-results':['pretreat','pretreat72','si-pretreat'],
 'thermal-results':['thermal-result','si-thermal','si-dsc-cycle'],
 'concentration-results':['concentration-series','si-logfit','si-energy'],
 'additive-results':['additive-series','si-additive-yield','additive-factor'],
 'kinetic-analysis':['si-orders'],
 'mechanistic-context':['prior-cluster','prior-squalane','surface-model','additive-effects','scheme2-model','conclusion','background','abstract-threshold','scheme1-stoichiometry']}
OWN={SID+'-'+f:k for k,fs in GROUPS.items() for f in fs}
assert set(OWN)==set(FM), {'missing':sorted(set(FM)-set(OWN)), 'extra':sorted(set(OWN)-set(FM))}

def sample_owner(s):
    if s=='acid-isolated': return 'labeled-acid-synthesis'
    if s in ['phenylacetate-reference','nmr-labeled','vt-absorption','nmr-acid-exchange','nmr-indium-exchange','acid-optical-control']: return 'cluster-ligand-observations'
    if s in ['xrd-context','extended-300-tem','temp-150-tem','temp-250-tem','scherrer150','scherrer250']: return 'structural-results'
    if s.startswith('pretreat'): return 'pretreatment-results'
    if s.startswith('thermal'): return 'thermal-results'
    if s=='author-mechanism': return 'mechanistic-context'
    if s=='kinetic-model': return 'kinetic-analysis'
    if s.startswith(('concentration','c-')): return 'concentration-results'
    if s.startswith(('acid-','indium-','additive-')): return 'additive-results'
    if s in ['temperature-series','extended-300'] or s.startswith('temp-'): return 'temperature-results'
    raise AssertionError(s)
SOWN={s:sample_owner(s) for s in SC}

def equation_owner(e):
    i=e['id']
    if 'gaussian' in i:return 'scherrer-analysis'
    if i=='scheme1-relation':return 'mechanistic-context'
    if any(t in i for t in ['s32','s33','s34','s35','s36','s37']):return 'kinetic-analysis'
    if any(t in i for t in ['s30','s31']):return 'additive-results'
    if any(t in i for t in ['figure5','s20','s21']):return 'concentration-results'
    return 'temperature-results'
EQOWN={e['id']:equation_owner(e) for e in D['equations']}
TABLEOWN={'table-1':'additive-results','table-s22':'concentration-results','printed-linear-fits':'kinetic-analysis',
          'scherrer-prose':'scherrer-analysis','gaussian-boxes':'scherrer-analysis','acid-nmr':'acid-nmr'}
FIGOWN={f['id']:list(dict.fromkeys(SOWN[s] for s in f['sample_context_ids'])) for f in D['figures']}
FACTMAP=[]
for j,f in enumerate(D['facts']):
    rid=R[OWN[f['id']]]['record_id']
    FACTMAP.append({'source_fact_id':f['id'],'source_file':'source-facts.json','source_pointer':f'/facts/{j}',
        'primary_record_id':rid,'reader_section':R[OWN[f['id']]]['reader_section'],'claim_class':f['claim_class'],
        'sample_scope':f['sample_scope'],'claim_mapping':'/measurements/{claim_index}/value',
        'quantities':[{'source_pointer':f'/facts/{j}/quantities/{qi}','meaning':q['meaning'],
             'canonical_pointer_template':'/measurements/{quantity_index}/value',
             'canonical_key':key(q['meaning']),'numeric_or_qualitative':'qualitative' if q['status'].startswith('reported_') else 'numeric',
             'source_status':q['status'],'conflict_ids':q.get('conflict_ids',[]),'gap_ids':q.get('gap_ids',[])} for qi,q in enumerate(f['quantities'])]})

OPS=[]
for ri,r in R.items():
    if not r['source_protocol_id']: continue
    p=PM[r['source_protocol_id']]
    for oi,o in enumerate(p['operations']):
        action=o['id']; constraints=[]
        if action=='dry-flask':constraints += ['Overnight is a reported qualitative duration; retain it in description and a qualitative fact. Do not invent a numeric hour count.']
        if action=='sonicate-msc' and ri=='conversion-concentration':constraints += ['Omit representative 20.0 mg and 0.00121 mmol from operational parameters and stock component amounts; retain explicitly unknown changed charges. Source representative values remain in their own record.']
        if action=='charge-ode':constraints += ['Resolve the selected additive using a concrete optional stock ID. Do not pass a fictitious selected-additive-stock ID into the canonical graph.']
        if action=='monitor-growth':constraints += ['growth-data is analysis_data; reaction-mixture is reaction_batch. Do not pool them as one material.']
        if action=='distill-solvent':constraints += ['Retained fraction is the resolvable residue state, never the solvent distillate.']
        if action=='transfer-purify':constraints += ['Keep InP and In2O3 fraction identities distinct, with unresolved collection details; output is a set of fractions, not a new pure pooled material.']
        if action in ['nmr-analyze','uvvis-analyze','tem-analyze','xrd-analyze','tga-analyze','dsc-analyze','kinetic-analysis-analyze','scherrer-analysis-analyze']:
            constraints += ['Multiple specimens are a sample_set, not a mixture. Acquisition data have kind analysis_data; no new synthesis product.']
        if action=='nmr-analyze':constraints += ['The general 700 MHz instrument label and printed Figure 4 202 Hz label remain separately scoped. Do not normalize the latter to MHz.']
        if action in ['tga-analyze','dsc-analyze']:constraints += ['Do not inherit the reaction N2 atmosphere into thermal-analysis settings.']
        if action=='pretreat-msc':constraints += ['The 30 h and 72 h contexts and subsequent 250 degrees C conversion remain distinct; no exact aliquot join or automatic 30-to-72 correction.']
        if action in ['add-labeled-acid','add-labeled-indium']:constraints += ['Equivalents denote source comparison levels; do not sum them into a total delivered charge without explicit sequential-dose evidence.']
        if action=='substitute-labeled-acid':constraints += ['Cited preparation remains incomplete; do not import charges, temperature, workup or atomic coordinates from another paper.']
        if action in ['acid-condense','acid-quench']:constraints += ['Coolants/bath water are external apparatus context, not assumed reaction inputs.']
        OPS.append({'record_id':r['record_id'],'source_protocol_id':p['id'],'source_operation_id':action,
            'source_pointer':f'/protocols/{D["protocols"].index(p)}/operations/{oi}',
            'canonical_pointer_template':f'/operations/{oi}','source_operation_identity_retained':True,
            'source_quantity_count':len(o['quantities']),'missing_fields':o['missing_fields'],
            'qualitative_quantity_indices':[i for i,q in enumerate(o['quantities']) if q['status'].startswith('reported_')],
            'constraints':constraints})

STOCKOWN={'bnmgcl-stock':['labeled-acid-synthesis'],'msc-injection':['conversion-representative','conversion-acid-additive','conversion-indium-additive'],
    'indium-myristate-additive':['conversion-indium-additive'],'myristic-acid-additive':['conversion-acid-additive'],'hcl-aqueous':['labeled-acid-synthesis']}
STOCKS=[]
for j,s in enumerate(D['stocks']):
    STOCKS.append({'source_id':s['id'],'source_pointer':f'/stocks/{j}',
        'proposed_record_ids':[R[k]['record_id'] for k in STOCKOWN[s['id']]],
        'components':[{'source_pointer':f'/stocks/{j}/components/{ci}','material_id':c['material_id'],
                       'canonical_pointer_template':'/stocks/{stock_index}/components/'+str(ci)} for ci,c in enumerate(s['components'])],
        'final_volume_reported':s.get('final_volume') is not None,
        'concentrations_only_in_concentrations':True,'transferred_volume_destination':'operation parameter, not total stock volume',
        'representative_charge_excluded_from_changed_concentration_record':s['id']=='msc-injection'})

def target_owner(file,ptr):
    ob=resolve(PAY[file],ptr)
    if file=='source-tables.json':return [TABLEOWN[ob['id']]]
    category=ptr.split('/')[1]
    if category=='facts':return [OWN[ob['id']]]
    if category=='figures':return FIGOWN[ob['id']]
    if category=='schemes':return ['mechanistic-context']
    if category=='equations':return [EQOWN[ob['id']]]
    if category in ['references','conflicts','missingness']:return ['source-context']
    raise AssertionError((file,ptr))
UNITS=[]
for u in I['units']:
    owners=[];targets=[]
    for t in u['extraction_targets']:
        file=t['file'];ptr=t.get('json_pointer')
        if file=='original-assets-manifest.json':
            targets.append({**t,'transport':'Selected original graphical-abstract crop only; explanatory source art, not a coordinate model.'})
            owners.append('mechanistic-context');continue
        # Private full-page payload/TOC regions are not copied to a public canonical field.
        if file not in PAY:
            targets.append({**t,'transport':'private provenance/coverage reference only; no raw full text in public assets'})
            owners.append('source-context');continue
        owners += target_owner(file,ptr);targets.append({**t,'transport':'exact structured source object; typed values mapped separately'})
    if not owners:owners=['source-context']
    UNITS.append({'source_unit_id':u['id'],'kind':u['kind'],'source_targets':targets,
                  'record_ids':[R[k]['record_id'] for k in dict.fromkeys(owners)],
                  'reader_item_id_template':'source-'+u['id'],
                  'raw_full_page_transport_allowed':False})

coverage={'status':'mapping_only_not_executed_transport','facts':FACTMAP,'source_units':UNITS,
    'protocol_operations':OPS,'stocks':STOCKS,
    'materials':[{'source_pointer':f'/materials/{j}','material_id':m['id'],'primary_record_id':R['source-materials']['record_id'],
                  'canonical_pointer_template':'/materials/{material_index}','additional_operation_bindings':'Only where named in that operation or its declared stock; no role-based automatic charge.'} for j,m in enumerate(D['materials'])],
    'sample_contexts':[{'source_pointer':f'/sample_contexts/{j}','sample_id':s['id'],'record_id':R[SOWN[s['id']]]['record_id'],
        'canonical_pointer_template':'/products/{product_index}','whole_composition_policy':'Retain source value including null; observed InP phase does not prove whole-powder purity.',
        'batch_id':None,'source_physical_join_statement':s['physical_batch_join']} for j,s in enumerate(D['sample_contexts'])],
    'table_cells':[{'source_pointer':f'/tables/{ti}/rows/{ri}/cells/{ci}','table_id':t['id'],'row_id':row['id'],
          'record_id':R[TABLEOWN[t['id']]]['record_id'],'canonical_pointer_template':'/measurements/{cell_index}/value',
          'context_rule':'Use both row and column headings. Preserve fitted/model versus measured basis, original unit and conflicting source scope.'}
        for ti,t in enumerate(T['tables']) for ri,row in enumerate(t['rows']) for ci,cell in enumerate(row['cells'])],
    'figures':[{'figure_id':f['id'],'source_pointer':f'/figures/{j}','record_ids':[R[k]['record_id']for k in FIGOWN[f['id']]],
         'sample_context_ids':f['sample_context_ids'],'asset_policy':'Selected original crop only; no whole-page public asset or reconstructed data.'}for j,f in enumerate(D['figures'])],
    'equations':[{'equation_id':e['id'],'source_pointer':f'/equations/{j}','record_id':R[EQOWN[e['id']]]['record_id'],
          'status_policy':'Author fit/calculation or proposed relation; never a new measured reaction condition.'}for j,e in enumerate(D['equations'])]}
save('source-to-schema-map.json',coverage)

CONTRACT={
 'status':'planned_contract_not_reader_validation','canonical_schema':'1.3.0',
 'required_review_scope_after_pass':'supplied_main_and_matched_si',
 'reader_sections':[{'id':i,'title':t}for i,t in [('precursors','Precursors'),('protocol','Synthesis protocol'),('structures','Final structures'),('properties','Properties'),('intuition','Chemical intuition'),('sources','Sources and limitations')]],
 'recipe_inventory':{'record_ids':'Arrays of actual candidate record IDs; no prose in ID fields.','records_are_not_papers_or_batches':True},
 'route_evidence_contexts':{R[k]['record_id']:[R[o]['record_id']for o in OBS]for k in R if R[k]['proposed_record_type']in ['literature_protocol','protocol_variant']},
 'route_evidence_scope_notes':'Comparative context links do not assert exact recipe-to-measurement, particle-to-CIF or same-aliquot matches.',
 'characterization_inventory':{'reader_item_ids':'Resolve actual items in structures/properties; do not supply an array of strings to an object-card renderer.'},
 'typed_reader_fields':{'json_pointer':'Exact leaf object, normally /measurements/{n}/value; operations/materials/stocks and target fields also covered.',
    'canonical_quantity':'Byte-equivalent parsed quantity/fact object; prose normalization is separate and declared.',
    'malformed_or_conflicting_values':'Display literal source claim with qualification; never repaired into a new usable recipe condition.'},
 'unresolved_qualitative_duration':{'example':'overnight','measurement':'Reported qualitative fact with raw text and evidence.',
    'operation_numeric_parameter':'If present, numeric null/not_reported with raw_text and a note that qualitative duration is reported; never fabricate hours.'},
 'uncertainty_transport':'Preserve source uncertainty and ordered endpoints in qualifier/raw text or exact source payload because current quantity schema has no dedicated uncertainty/endpoints field.',
 'model_and_source_calculation':'Use author_derived for source fitted/calculated values with exact original source status in provenance; not a fresh fit or measured target.',
 'thermal_typography':'The malformed DSC 1800°C rate remains source evidence; it cannot be an operational heating-rate setting.',
 'source_material_formulas':'Printed abbreviations/formulas remain separate from any later qualified molecular identity or geometry.',
 'gates':{'source':'pending distinct source audit','canonical':'pending complete authorship and separate audit','molecules':False,'apparatus':False,'browser_render':False,'publication':False,'training':False},
 'actual_consumer_validation_required_before_freeze':['Current dataset_lib.validate_record on every actual record.',
    'Current build_paper_reviews.validate in a private exact asset/record fixture.',
    'Additional strict arrays-of-record-IDs and reader-item checks beyond the current permissive list branch.',
    'All source units, facts, numeric listings, material/stock/operation/product objects and exact reader field pointers resolve.',
    'One source split group and zero task eligibility.']}
save('reader-contract-map.json',CONTRACT)

constraints=[
 'No template quantity may silently fill a changed-concentration run.',
 'Do not expand independent temperature, concentration and additive lists into a Cartesian experimental matrix.',
 'Cited-only MSC and P(SiMe3)3 preparations remain incomplete and separate from current ligand synthesis.',
 'Isotopic enrichment, isotope position, natural-abundance controls and unlabeled/labeled salt preparations remain separate.',
 'The source supplies no current QD coordinates or exact pair; prior cluster literature structure is reference context only.',
 '130 degrees C / 30 h and 72 h evidence remains separately attributed, with the oleate/myristate label discrepancy.',
 'Local TEM, FFT, XRD, optical data, solid thermal analysis, NMR titrations and source fits retain their own specimen contexts.',
 'Purified fraction sets are not a pure pooled QD product. Retain InP versus In2O3 and unknown collection details.',
 'A rate, Gaussian peak maximum, Scherrer width or model coefficient is not a synthesis-operation input.',
 'No all-success label or independent repeat count; all training tasks remain absent.']
save('record-boundary-plan.json',{'status':'draft_schema_mapping_source_audit_pending','source_group':SID,
    'records':list(R.values()),'record_count_is_provisional':True,'constraints':constraints,
    'counts':dict(Counter(r['proposed_record_type']for r in R.values())),
    'source_operations':sum(len(p['operations'])for p in D['protocols']),'proposed_operation_instances':len(OPS)})

schema_files=[S/'scripts'/n for n in ['schema_definition.py','record_helpers.py','dataset_lib.py','build_paper_reviews.py','review_scope.py']]+[S/'dist/paper-review.mjs',S/'data/README.md']
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
ck('source files unchanged during mapping',all(sha(p)==h for p,h in initial.items()))
ck('all source facts assigned once',len(FACTMAP)==len(FM) and len(set(x['source_fact_id']for x in FACTMAP))==len(FM))
ck('all fact quantities mapped',sum(len(x['quantities'])for x in FACTMAP)==sum(len(f['quantities'])for f in D['facts']))
ck('all source units mapped',len(UNITS)==len(I['units']))
ck('all original source operations assigned',set((x['source_protocol_id'],x['source_operation_id'])for x in OPS)=={(p['id'],o['id'])for p in D['protocols']for o in p['operations']})
ck('all stock components mapped',sum(len(x['components'])for x in STOCKS)==sum(len(x['components'])for x in D['stocks']))
ck('all original table cells mapped',len(coverage['table_cells'])==sum(len(r['cells'])for t in T['tables']for r in t['rows']))
ck('all 62 context assignments resolve',set(SOWN)==set(SC) and all(o in R for o in SOWN.values()))
ck('all source figures assigned',len(FIGOWN)==len(D['figures']))
ck('all source equations assigned',len(EQOWN)==len(D['equations']))
ck('no changed-concentration representative stock bind','conversion-concentration' not in STOCKOWN['msc-injection'])
ck('no training or publication promotion',all(r['requested_tasks']==[] and r['quality_review_status']=='imported_unreviewed' for r in R.values()))
ck('one source group',set(r['source_group']for r in R.values())=={SID})
ck('unique proposed record identifiers',len({r['record_id']for r in R.values()})==len(R))
save('mapping-checks.json',{'status':'passed_mapping_consistency_only','checks':checks,'count':len(checks),
    'not_performed':['Full source scientific audit','Actual canonical record validation','Actual reader fixture validation','Scientific asset approval','Website publication']})
(O/'README.md').write_text('''# Friedfeld schema-mapping checkpoint

This private checkpoint plans conversion from the supplied source draft. It is **not a canonical dataset, a completed reader or a scientific approval**. The extraction is still awaiting its own immutable freeze and Backlog’s independent source audit. Any source correction must be reconciled before canonical records are frozen.

The provisional plan contains one representative conversion record and three linked conversion variants (acid additive, indium additive and initial concentration), plus separately scoped isotope-ligand preparation, cited preparation, exchange/acquisition procedures and observations. Records and operation instances are not independent batches. The source’s 34 operations can appear in several explicitly inherited variants.

`source-to-schema-map.json` assigns every current fact, semantic unit, stock component, material, original operation, sample context, table cell, figure and equation. These are **pointer templates**, not claims that final canonical fields already exist. `record-boundary-plan.json` defines the boundaries; `reader-contract-map.json` specifies the current consumer’s required shapes and remaining gates.

The current schema can represent the science without a schema migration. Qualitative “overnight”, source uncertainties and malformed rate typography need explicit fact/raw-text/qualifier transport rather than invented numeric values. The representative 20.0 mg injection is excluded from changed-concentration stock bindings. The 20 mL reaction volume is never a stock preparation volume. Only demonstrated row/column or caption pairings become condition options; no Cartesian matrix or physical replicate count is created.

All original figures will use selected source crops. The older cluster coordinates are cited context, and no current QD atomic coordinates or exact structure–recipe pair are supplied. No molecular, apparatus, browser, publication or training approval is implied.

Next: bind the completed source freeze and independent audit, reconcile their exact deltas, then author canonical records and a readable six-section reader. Validate every actual field and asset in an isolated fixture with the current Site consumer before a distinct canonical/reader audit.
''',encoding='utf-8')
bound={str(p):sha(p)for p in O.iterdir()if p.is_file()}
save('mapping-checkpoint.json',{'status':'preserved_mapping_checkpoint_not_canonical_freeze','created_at':datetime.now(timezone.utc).isoformat(),
    'author':'/root/norberg2004_extract','source_author':'/root/peng1998_reader_assets','source_auditor':'/root/backlog_eta',
    'source_id':SID,'source_input_hashes':initial,'source_freeze_present_at_mapping':(F/'package-freeze.json').exists(),
    'source_scientific_approval_inferred':False,'current_consumer_hashes':{str(p):sha(p)for p in schema_files},
    'bound_outputs':bound,'author_script_sha256':sha(__file__),
    'counts':{'proposed_records':len(R),'source_facts':len(FACTMAP),'fact_quantities':sum(len(x['quantities'])for x in FACTMAP),
        'semantic_units':len(UNITS),'source_operations':sum(len(p['operations'])for p in D['protocols']),
        'proposed_operation_instances':len(OPS),'materials':len(D['materials']),'stocks':len(STOCKS),'stock_components':sum(len(x['components'])for x in STOCKS),
        'sample_contexts':len(SC),'numeric_listing_cells':len(coverage['table_cells']),'figures':len(FIGOWN),'equations':len(EQOWN)},
    'next_action':'Reconcile the immutable source freeze and passed independent source audit before final canonical authoring/freeze.'})
print(json.dumps({'checkpoint':str(O/'mapping-checkpoint.json'),'sha256':sha(O/'mapping-checkpoint.json'),'records':len(R),'operation_instances':len(OPS),'checks':len(checks)}))
