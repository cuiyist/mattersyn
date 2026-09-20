"""Independent private canonical audit; reads author/Site files, writes only this audit."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib, json, sys
sys.dont_write_bytecode = True
B = Path(__file__).resolve().parent
S = Path(r'[local path redacted]')
sys.path.insert(0, str(S / 'scripts'))
from dataset_lib import validate_record, eligibility, build_groups

def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks, bound = [], {}
def ck(label, ok):
    checks.append({'check': label, 'passed': bool(ok)})
    assert ok, label
def bind(p):
    bound[str(Path(p))] = sha(p)
    return read(p) if str(p).endswith('.json') else None
def resolve(obj, pointer):
    for part in pointer.strip('/').split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj

M = bind(B/'canonical-record-manifest.json')
C = bind(B/'canonical-source-coverage.json')
D = bind(B/'source-facts.json')
I = bind(B/'source-inventory.json')
A = bind(B/'source-scientific-audit.json')
V = bind(B/'canonical-draft-validation.json')
bind(B/'page-coverage.json')
bind(B/'extraction-notes.md')
bind(B/'build_canonical_drafts.py')
for name in ['dataset_lib.py', 'schema_definition.py', 'record_helpers.py']: bind(S/'scripts'/name)
bind(Path(__file__))
for field,name in [('dataset_validator_sha256','dataset_lib.py'),('schema_definition_sha256','schema_definition.py'),('record_helpers_sha256','record_helpers.py')]: ck('author and independent validator version '+field,M[field]==sha(S/'scripts'/name))
ck('frozen canonical manifest exact', sha(B/'canonical-record-manifest.json') == '77f7307e28db74d195271156a48000e6ca67d30bdadd766fdac53fe530bdea55')
ck('frozen source coverage exact', sha(B/'canonical-source-coverage.json') == '1b48c7152dae322451091351f7fa18870d2126b33f3da4e94c1525f8fd80d1da')
ck('independent extraction audit passed', A['status']=='passed_with_preserved_source_ambiguities')
for name,h in A['author_artifact_sha256'].items(): ck('passed extraction artifact '+name, sha(B/name)==h)
for item in M['original_sources']:
    bind(item['path']); ck('original source copy '+item['path'],sha(item['path'])==item['sha256'])
for field,name in [('source_extraction_audit_sha256','source-scientific-audit.json'),('source_inventory_sha256','source-inventory.json'),('source_facts_sha256','source-facts.json'),('page_coverage_sha256','page-coverage.json'),('build_script_sha256','build_canonical_drafts.py')]: ck('manifest provenance '+field,M[field]==sha(B/name))
R = {}
for row in M['records']:
    r=bind(row['path']); R[r['record_id']]=r
    ck('record exact frozen '+r['record_id'],sha(row['path'])==row['sha256']==V['record_hashes'][r['record_id']])
    ck('schema and semantic '+r['record_id'],not validate_record(r))
    ck('source split and DOI '+r['record_id'],r['lineage']['source_group']=='nagasaki2004' and any(s['id']=='nagasaki2004' and s['doi']=='10.1021/la036034c' for s in r['sources']))
    ck('no task admission '+r['record_id'],r['quality']['review_status']=='imported_unreviewed' and r['quality']['requested_tasks']==[] and not any(v['eligible'] for v in eligibility(r).values()))
    ck('no invented atomic or physical sample join '+r['record_id'],not r['structure_assets'] and all(p['batch_id'] is None and p['parent_sample_id'] is None for p in r['products']))
    ck('four unresolved conflicts and ten gaps '+r['record_id'],len(r['quality']['conflicts'])==4 and len(r['quality']['missing_fields'])==10)
    ck('no measurement-derived recipe target '+r['record_id'],r['intended_target']['size']['value'] is None and r['intended_target']['phase']['value'] is None)
    ck('manifest operation/sample inventory '+r['record_id'],row['operations']==[o['id'] for o in r['operations']] and row['samples']==[p['sample_id'] for p in r['products']])

F={f['id']:f for f in D['facts']}
U={u['id']:u for u in I['source_units']}
ck('all 49 facts covered once as source identities',len(C['facts'])==49 and {x['source_fact_id'] for x in C['facts']}==set(F))
for row in C['facts']:
    f=F[row['source_fact_id']]
    ck('exact source fact retained '+f['id'],f==row['source_fact'] and bool(row['canonical_bindings']))
    for link in row['canonical_bindings']:
        q=resolve(R[link['record_id']],link['pointer']); label=f['id']+' '+link['record_id']+link['pointer']
        status={'author_model_derived':'author_derived','reported_qualitative':'reported'}.get(f['status'],f['status'])
        ck('status '+label,q['status']==status)
        if f['status']=='reported_qualitative':
            ck('qualitative stays qualitative '+label,q['value']==f['raw_text'] and f['qualifier'] in q['note'] and 'unit' not in q)
        else:
            v=f['value']; idx=link['source_array_index']
            expected = v[idx] if idx is not None else v
            ck('numeric value/bounds '+label,(q['value'] is None and [q['minimum'],q['maximum']]==expected) if isinstance(expected,list) else q['value']==expected and q['minimum'] is None and q['maximum'] is None)
            ck('unit, precision and original qualifier '+label,q['unit']==(f['unit'] or '') and q['approximate']==f['approximate'] and f['qualifier'] in q['qualifier'] and q['raw_text']==f['raw_text'])
            ck('source scope remains explicit '+label,f['source_unit_id'] in q['basis'])
        ck('fact evidence pages preserved '+label,all(any(('SI' if e['source_id'].endswith('-si') else 'Main')+' PDF p. '+str(e['pdf_page']) in dest['locator'] and dest['source_id']=='nagasaki2004' for dest in q['evidence']) for e in f['evidence']))
ck('32 original units all covered',{x['source_unit_id'] for x in C['source_units']}==set(U) and len(C['source_units'])==32)
for row in C['source_units']:
    ck('exact original unit '+row['source_unit_id'],row['source_unit']==U[row['source_unit_id']] and bool(row['canonical_bindings']))
    for link in row['canonical_bindings']:ck('unit resolves '+row['source_unit_id']+link['pointer'],bool(resolve(R[link['record_id']],link['pointer'])))
for row in C['source_objects']:
    value=resolve(R[row['record_id']],row['pointer'])
    ck('source object pointer '+row['category']+'/'+row['source_object_id']+' '+row['record_id']+row['pointer'],bool(value))
for category in ['materials','stocks','protocols','samples','measurements','author_interpretations_and_outlook','figures','references','contradictions','gaps','unperformed_options']:
    ck('complete source object identities '+category,{x['id'] for x in D[category]}=={x['source_object_id'] for x in C['source_objects'] if x['category']==category})
ck('observation identities complete',{str(i) for i in range(len(D['observations']))}=={x['source_object_id'] for x in C['source_objects'] if x['category']=='observations'})
ck('administrative and substantive footnote identities complete',{x['id'] for x in I['administrative_and_footnote_units']}=={x['source_object_id'] for x in C['source_objects'] if x['category']=='administrative_and_footnote_units'})
for row in C['source_operations']:
    source=next(p for p in D['protocols'] if p['id']==row['source_protocol_id'])
    original=next(o for o in source['operations'] if o['id']==row['source_operation_id'])
    dest=resolve(R[row['record_id']],row['pointer'])
    ck('source operation meaning retained '+original['id'],original['action'] in dest['description'] and all(x in dest['description'] for x in original['unreported_fields']))
for row in C['source_objects']:
    cat=row['category']; sid=row['source_object_id']; dest=resolve(R[row['record_id']],row['pointer'])
    if cat=='references':
        src=next(x for x in D[cat] if x['id']==sid)
        ck('bibliography exact and external scope '+sid,dest['value']==src['bibliography_as_printed_normalized_spacing'] and 'external full text not inspected' in dest['note'].lower())
    elif cat=='samples':
        src=next(x for x in D[cat] if x['id']==sid)
        ck('specimen uncertainty retained '+sid,src['measurement_scope'] in dest['notes'] and 'Source linkage: '+src['link_status'] in dest['notes'])

def rec(key): return R['nagasaki-2004-'+key]
def op(key,oid):return next(o for o in rec(key)['operations'] if o['id']==oid)
def meas(key,mid):return next(m for m in rec(key)['measurements'] if m['id']==mid)
ck('record boundaries 10 procedures, four contexts, one representative and one variant',Counter(r['record_type'] for r in R.values())=={'procedure':10,'observation':4,'literature_protocol':1,'protocol_variant':1})
ck('one common split group',set(build_groups(list(R.values())).values())=={'group-842576c6412b'})
ck('pre-dialysis biotin branch input',op('biotin-polymer','biotin-condense')['inputs']==['cho-polymer-before-dialysis','biocytin-hydrazide'])
ck('biotin 2h belongs before NaBH4 reduction',op('biotin-polymer','biotin-condense')['parameters']['duration']['value']==2 and op('biotin-polymer','biotin-reduce')['depends_on']==['biotin-condense'] and not op('biotin-polymer','biotin-reduce')['parameters'])
ck('unknown protonating reagent distinct from zeta HCl','protonating-agent-unspecified' in op('polymer-preparation','pama-protonate')['inputs'])
ck('Soxhlet removes PEG rather than adding impurity',op('polymer-preparation','soxhlet-clean')['inputs']==['protonated-acetal-block-polymer','thf'])
ck('Cd then S then 1h stirring',op('cho-cds','s-add')['depends_on']==['cd-add'] and op('cho-cds','cds-stir')['depends_on']==['s-add'] and op('cho-cds','cds-stir')['parameters']['duration']['value']==1)
ck('8mL belongs to initial polymer solution',op('cho-cds','polymer-medium')['parameters']['initial_polymer_solution_volume']['value']==8 and all(op('cho-cds',x)['parameters']['addition_volume']['value'] is None for x in ['cd-add','s-add']))
ck('amine basis is not polymer chain molarity','amine groups' in op('cho-cds','polymer-medium')['parameters']['amine_group_concentration']['unit'])
ck('biotin variant has no independently inherited numeric settings',all(q['value'] is None and q['minimum'] is None and q['maximum'] is None for q in rec('biotin-cds')['operations'][0]['parameters'].values()))
ck('no invented new ionic salt in FRET medium',not any(m['formula']=='NaCl' for m in rec('fret')['materials']) and op('fret','fret-mix')['parameters']['ionic_strength']['value']==0.15)
ck('assay CdS formula concentration distinct from particle count','particle-number' in op('fret','fret-mix')['parameters']['initial_nominal_CdS_concentration']['qualifier'])
ck('11 concentration labels remain one Figure4 series',len(rec('fret')['products'])==2 and sum(m['id'].startswith('printed-texasred-streptavidin-concentration-labels-') for m in rec('fret')['measurements'])==11)
ck('C2 no numeric competition curves or guessed additions',all(not o['parameters'] for o in rec('recognition-controls')['operations']) and all('unit' not in m['value'] for m in rec('recognition-controls')['measurements']))
ck('C3 unresolved main/inset calibration', 'No global linear model' in meas('fret','unresolved-C3')['value']['value'])
ck('C4 no invented avidin reagent',all(m['id']!='avidin' for r in R.values() for m in r['materials']))
ck('C1 attached to concentration variants',all('C1' in q['qualifier'] for o in rec('concentration-series')['operations'] for q in o['parameters'].values()))
ck('4.8nm is author-derived and sample-unresolved',meas('optical','band-gap-theory-derived-cds-size')['value']['status']=='author_derived' and meas('optical','band-gap-theory-derived-cds-size')['sample_id']=='figure2-absorption-sample-unresolved')
ck('5nm abstract summary separate from measured diameter',any(m['sample_id']=='abstract-size-context' and m['value'].get('value')==5 and m['value'].get('unit')=='nm' and m['value'].get('approximate') is True for m in rec('biotin-cds')['measurements']) and all(m['property']!='diameter' for m in rec('biotin-cds')['measurements']))
ck('TEM voltage only acquisition',not op('tem','tem-grid-dry')['parameters'] and op('tem','tem-acquire')['parameters']['accelerating_voltage']['value']==200)
ck('XRD preparation denotes separate specimens',next(s for s in rec('xrd')['material_states'] if s['id']=='freeze-dried-xrd-specimens')['kind']=='sample_set' and 'no physical mixing' in op('xrd','xrd-freeze-dry')['description'])
ck('XRD phase not propagated to recipe products',all(p['phase']['value'] is None for r in R.values() if r!=rec('xrd') for p in r['products']))
ck('SI structural specimen linkage unresolved',all(p['recipe_link']=='unresolved' for key in ['tem','xrd'] for p in rec(key)['products']))
ck('zeta adjusters are alternatives',op('zeta','zeta-medium')['optional_inputs']==['hcl','naoh'] and op('zeta','zeta-medium')['parameters']['NaCl_measurement_concentration']['value']==7.5)
ck('post-CdS ligand installation remains unperformed context',not rec('chemical-intuition')['operations'] and 'not performed' in meas('chemical-intuition','post-cds-ligand-installation')['value']['note'])
for prefix in ['main-02','main-03','main-04','main-05','si-01']:
    for ext in ['.txt','.png']:bind(B/(prefix+ext))
ck('frozen inputs unchanged at final binding',all(sha(p)==h for p,h in bound.items()))
counts={'records':len(R),'operations':sum(len(r['operations']) for r in R.values()),'measurements_and_context_entries':sum(len(r['measurements']) for r in R.values()),'material_slots':sum(len(r['materials']) for r in R.values()),'stocks':sum(len(r['stocks']) for r in R.values()),'samples_and_contexts':sum(len(r['products']) for r in R.values()),'source_facts':len(F),'fact_bindings':sum(len(x['canonical_bindings']) for x in C['facts']),'source_units':len(U),'unit_bindings':sum(len(x['canonical_bindings']) for x in C['source_units']),'source_object_links':len(C['source_objects']),'checks':len(checks),'bound_files':len(bound)}
report={'schema':'mattersyn.independent-canonical-scientific-audit.v1','status':'passed_with_preserved_source_ambiguities','source_id':'nagasaki2004','auditor':'/root/backlog_eta','canonical_author':'/root/norberg2004_extract','audited_at':datetime.now(timezone.utc).isoformat(),'scope':'All 16 private canonical drafts, all operations, quantities, sample boundaries, source facts/objects and mappings independently checked against the passed extraction plus targeted original main/SI rereads. This is independent of canonical authoring; the auditor authored the earlier extraction, which has its own independent full-source audit.','source_read_scope':{'prior_passed_full_source_audit':str(B/'source-scientific-audit.json'),'prior_complete_coverage':'5 main + 3 matched SI pages','targeted_text_and_visual_rereads':['main-02','main-03','main-04','main-05','si-01'],'full_source_extraction_repeated':False},'counts':counts,'record_hashes':{rid:sha(B/'canonical-drafts'/(rid+'.json')) for rid in R},'bound_files':bound,'checks':checks,'scientific_findings':[],'corrections_required':[],'preserved_source_conflicts':[x['id'] for x in D['contradictions']],'remaining_limits':['One representative CdS route and one incompletely quantified similar-manner biotin variant; the other ten procedures and four contexts are not additional complete synthesis routes.','Source C1–C4 remain unresolved; no flipped labels, numeric competition fit or global FRET calibration.','8mL initial polymer medium does not establish precursor addition volumes or added moles. Biotin polymer branch starts before dialysis; NaBH4 dose/reaction details and other missing fields stay unknown.','4.8nm is an author optical-model estimate; abstract approximately5nm is a separate summary. No exact SI recipe/specimen join, measured coordinate dataset or CIF.','28 samples/context identifiers and 122 measurement/context entries are not counts of independent experiments or numeric measurements.','Canonical scientific audit does not approve reader/model/apparatus presentation, Site integration, publication or training admission.'],'training_eligible':False,'site_modified':False,'ledger_modified':False,'sources_modified':False,'published':False}
(B/'canonical-records-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'canonical-records-audit.md').write_text('Nagasaki canonical scientific audit passed with C1–C4 preserved. No canonical author correction was required.\n\nAll 16 drafts and 36 operations were inspected; the independent checks cover 49 source facts through 79 bindings, 32 units through 50 bindings, and 170 source-object links. Counts remain one representative synthesis route, one incompletely quantified biotin variant, ten procedures and four contextual records. The 122 measurement/context entries and 28 sample/context identifiers do not imply independent experiments.\n\nThe before-dialysis biotin branch, unknown precursor-volume basis, optical-model size, SI specimen uncertainty, separate assay conditions, controls and all source contradictions remain explicit. No task admission or atomic structure is asserted. Schema and semantic validation passed; all records share source split group group-842576c6412b.\n\nThis audit uses the separately passed full-source extraction audit and targeted main pages 2–5 plus SI methods text/visual rereads; it does not repeat or claim a new full-source extraction. Presentation, Site integration, publication and task admission remain separate gates.\n\nExact hashes and '+str(len(checks))+' checks are recorded in canonical-records-audit.json.\n',encoding='utf8')
print(json.dumps({'status':report['status'],'counts':counts,'audit_sha256':sha(B/'canonical-records-audit.json'),'markdown_sha256':sha(B/'canonical-records-audit.md')}))
