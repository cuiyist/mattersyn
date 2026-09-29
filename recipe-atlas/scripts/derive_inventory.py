"""Derive inventory membership and counts without changing scientific inputs."""
from pathlib import Path
from collections import Counter
import copy,hashlib,json
from build_atlas import synthesis_route
from review_scope import MAIN_SI,MAIN_ONLY,SI_ONLY,source_review_scope

PAPER_DERIVED={'canonical_record_count','synthesis_route_variant_count','contextual_control_count','contextual_observation_count','procedure_count','benchmark_row_count','measurement_entry_count','record_type_counts','canonical_recipe_family_ids','direct_route_material_systems','record_ids','record_urls','experimental_row_count','source_checked_synthesis_structure_rows'}
CORPUS_SUMMARY={'local_document_files_indexed','local_paper_groups_indexed','paper_candidate_groups_total','candidate_groups_without_local_documents','unique_document_content_hashes'}
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def hashed(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def reviewed_seed(inventory,original_sha256):
    """One-time migration; preserve authored scopes/notes, never cached totals."""
    return {'schema':'mattersyn-inventory-evidence/1',
      'baseline_inventory_sha256':original_sha256,
      'scope':inventory['scope'],
      'count_definitions':copy.deepcopy(inventory['count_definitions']),
      'corpus_snapshot':{k:inventory['summary'][k] for k in sorted(CORPUS_SUMMARY)},
      'corpus_candidate_metadata':copy.deepcopy(inventory['corpus_candidate_metadata']),
      'benchmark_scope':copy.deepcopy(inventory['benchmark_scope']),
      'review_priority_constraints':copy.deepcopy(inventory['review_priority_constraints']),
      'per_paper':[{k:copy.deepcopy(v) for k,v in p.items() if k not in PAPER_DERIVED} for p in inventory['per_paper']],
      'material_notes':{p['material_system']:copy.deepcopy(p.get('notes',[])) for p in inventory['per_material']},
      'excluded_precursor_procedure_identities':copy.deepcopy(inventory['material_system_lists']['excluded_precursor_procedure_identities'])}

def category(r):
    if r['collection']=='published_benchmark':return 'benchmark'
    if r['collection']!='reviewed_literature':raise ValueError('Unknown collection in gold inventory')
    if synthesis_route(r):return 'route'
    kind=r['record_type']
    if kind=='procedure':return 'procedure'
    if kind=='observation':return 'observation'
    if kind=='experiment':return 'experiment'
    if kind in ('literature_protocol','protocol_variant'):return 'control'
    raise ValueError('Unclassified inventory record type: '+kind)

def checked_library_sources(seed,library,primary,corpus_source):
    """Frozen intake is immutable; reviewed primary sources may extend its public view."""
    binding=seed.get('corpus_source_binding',{})
    if binding.get('canonical_json_sha256')!=hashed(corpus_source):raise ValueError('Corpus snapshot changed: frozen intake content differs')
    corpus=seed['corpus_snapshot'];source_summary=corpus_source['summary']
    source_papers=corpus_source['papers']
    local=[p['doi'].lower() for p in source_papers if p.get('doi') and p['coverage']['localDocumentCount']>0]
    if len(local)!=len(set(local)):raise ValueError('Corpus snapshot changed: duplicate local intake DOI')
    checks=[(source_summary['sourceDocumentCount'],corpus['local_document_files_indexed']),
      (len(source_papers),corpus['paper_candidate_groups_total']),
      (source_summary['paperCandidateCount'],len(source_papers)),
      (source_summary['papersWithLocalDocuments'],len(local)),
      (len(source_papers)-len(local),corpus['candidate_groups_without_local_documents']),
      (source_summary['uniqueContentHashes'],corpus['unique_document_content_hashes']),
      (binding.get('local_paper_groups'),len(local)),
      (binding.get('historical_augmented_library_groups'),corpus['local_paper_groups_indexed'])]
    if any(a!=b for a,b in checks) or library['summary']!=source_summary:raise ValueError('Corpus snapshot changed: intake metadata differs')
    dois=[p.get('doi') for p in library['papers']]
    if any(not isinstance(d,str) or not d for d in dois):raise ValueError('Library source membership has missing DOI')
    normalized=[d.lower() for d in dois]
    if len(normalized)!=len(set(normalized)):raise ValueError('Library source membership has duplicate DOI')
    primary_dois={p['doi'].lower() for p in primary.values()}
    local=set(local)
    if set(normalized)!=local|primary_dois:raise ValueError('Library source membership differs from frozen intake plus canonical primary sources')
    return local,primary_dois

def derive(seed,records,hubs,reviews,library,manifest,pairs,corpus_source):
    if seed.get('schema')!='mattersyn-inventory-evidence/1':raise ValueError('Unknown inventory evidence schema')
    byid={r['record_id']:r for r in records}
    if len(byid)!=len(records):raise ValueError('Duplicate canonical inventory record')
    manifest_ids=[r['record_id'] for r in manifest['records']]
    if len(set(manifest_ids))!=len(manifest_ids) or set(byid)!=set(manifest_ids):raise ValueError('Manifest record membership mismatch or duplicate')
    if manifest.get('record_count')!=len(records):raise ValueError('Manifest record count mismatch')
    metadata={p['source_group']:p for p in seed['per_paper']}
    if len(metadata)!=len(seed['per_paper']):raise ValueError('Duplicate source scope metadata')
    groups={r['lineage']['source_group'] for r in records}
    if groups!=set(metadata):raise ValueError('Each source needs independently reviewed scope metadata; no automatic review promotion')
    review_ids=[r['id'] for r in reviews]
    if len(set(review_ids))!=len(review_ids):raise ValueError('Duplicate formal source review')
    formal_scopes={'full_supplied_main_and_matched_si_review':MAIN_SI,'full_supplied_main_review_si_unverified':MAIN_ONLY,'full_supplied_si_review_main_unverified':SI_ONLY}
    formal_metadata=[(p.get('paper_id',sid),sid,p) for sid,p in metadata.items() if p['review_status'] in formal_scopes]
    expected_review_ids={rid for rid,_,_ in formal_metadata}
    if len(expected_review_ids)!=len(formal_metadata):raise ValueError('Ambiguous authored formal review identity')
    if set(review_ids)!=expected_review_ids:raise ValueError('Formal review membership differs from reviewed scope metadata')
    review_metadata={rid:(sid,p) for rid,sid,p in formal_metadata}
    for review in reviews:
      sid,p=review_metadata[review['id']]
      if review['review_scope']!=formal_scopes[p['review_status']]:raise ValueError('Formal review scope differs from authored evidence')
      # Normalize only the known legacy inventory role for validation; retain
      # authored metadata verbatim in the derived inventory. Unknown roles fail.
      scope_documents=[dict(doc,role='si' if doc.get('role')=='supporting_information' else doc.get('role')) for doc in p['documents']]
      source_review_scope({'review_scope':review['review_scope'],'documents':scope_documents})
      if review['doi'].casefold()!=p['doi'].casefold():raise ValueError('Formal review DOI differs from authored evidence')
      if type(review['pages_read']) is not int or review['pages_read']!=sum(d['page_count'] for d in p['documents']):raise ValueError('Formal review page count differs from authored evidence')
      reviewed_ids=review['record_ids']
      # A formal source review may reference a scoped subset of its canonical records.
      # Never extend that subset automatically to later contextual additions.
      if len(set(reviewed_ids))!=len(reviewed_ids) or any(rid not in byid or byid[rid]['lineage']['source_group']!=sid for rid in reviewed_ids):raise ValueError('Formal review record/source membership mismatch or duplicate')
    pair_ids=[r['pair_row_id'] for r in pairs['rows']]
    if len(set(pair_ids))!=len(pair_ids):raise ValueError('Duplicate structure pair row')
    for pair in pairs['rows']:
      if pair['record_id'] not in byid or pair['source_group']!=byid[pair['record_id']]['lineage']['source_group']:raise ValueError('Structure pair record/source membership mismatch')
    categories={r['record_id']:category(r) for r in records}
    route_ids={rid for rid,c in categories.items() if c=='route'}
    if route_ids!={rid for m in hubs for rid in m['record_ids']}:raise ValueError('Atlas route membership mismatch')
    if any(len(m['record_ids'])!=len(set(m['record_ids'])) for m in hubs):raise ValueError('Duplicate atlas route in a hub')
    if len({m['formula'] for m in hubs})!=len(hubs):raise ValueError('Duplicate material formula in atlas')
    for hub in hubs:
      formula=hub['formula']
      expected_direct={rid for rid in route_ids if byid[rid]['material']['formula']==formula}
      expected_contributions={rid for rid in route_ids if byid[rid]['material']['formula']==formula or formula in byid[rid]['material'].get('components',[byid[rid]['material']['formula']])}
      direct=hub['direct_record_ids']
      if len(direct)!=len(set(direct)) or set(direct)!=expected_direct:raise ValueError('Atlas direct material/record membership mismatch or duplicate')
      if set(hub['record_ids'])!=expected_contributions:raise ValueError('Atlas material/component contribution mismatch')
      if type(hub['component_only']) is not bool or hub['component_only']!= (not bool(expected_direct)):raise ValueError('Atlas component-only classification mismatch')
    primary={}
    for r in records:
      sid=r['lineage']['source_group'];found=[s for s in r['sources'] if s['id']==sid]
      if len(found)!=1:raise ValueError('Missing or ambiguous primary source')
      if sid in primary and primary[sid].get('doi')!=found[0].get('doi'):raise ValueError('Conflicting primary source DOI')
      primary.setdefault(sid,found[0])
    per_paper=[]
    for sid in sorted(groups):
      rr=sorted((r for r in records if r['lineage']['source_group']==sid),key=lambda r:r['record_id'])
      p=copy.deepcopy(metadata[sid]);cc=Counter(categories[r['record_id']] for r in rr)
      if p['doi'].casefold()!=primary[sid]['doi'].casefold():raise ValueError('Reviewed scope DOI mismatch')
      p.update(canonical_record_count=len(rr),synthesis_route_variant_count=cc['route'],contextual_control_count=cc['control'],
        contextual_observation_count=cc['observation'],procedure_count=cc['procedure'],benchmark_row_count=cc['benchmark'],
        experimental_row_count=cc['experiment'],measurement_entry_count=sum(len(r['measurements']) for r in rr),
        record_type_counts=dict(sorted(Counter(r['record_type'] for r in rr).items())),
        canonical_recipe_family_ids=sorted({r['lineage']['recipe_family'] for r in rr}),
        direct_route_material_systems=sorted({r['material']['formula'] for r in rr if r['record_id'] in route_ids}),
        record_ids=[r['record_id'] for r in rr],record_urls={r['record_id']:'records/'+r['record_id']+'.html' for r in rr},
        source_checked_synthesis_structure_rows=sum(row['source_group']==sid for row in pairs['rows']))
      per_paper.append(p)
    byformula={m['formula']:m for m in hubs}
    formulas={r['material']['formula'] for r in records if r['record_type']!='procedure'}|set(byformula)
    formulas|={f for f in seed['material_notes'] if any(r['material']['formula']==f for r in records)}
    materials=[]
    for formula in sorted(formulas):
      rr=[r for r in records if r['material']['formula']==formula];cc=Counter(categories[r['record_id']] for r in rr)
      direct=sorted(r['record_id'] for r in rr if r['record_id'] in route_ids)
      m=byformula.get(formula);contributions=set(m['record_ids']) if m else set()
      components=sorted(contributions-set(direct))
      related_sources=sorted({r['lineage']['source_group'] for r in rr}|{byid[rid]['lineage']['source_group'] for rid in contributions})
      row={'material_system':formula,'notes':copy.deepcopy(seed['material_notes'].get(formula,[])),
        'direct_synthesis_route_variant_count':len(direct),'direct_route_record_ids':direct,
        'contextual_control_count':cc['control'],'contextual_control_record_ids':sorted(r['record_id'] for r in rr if categories[r['record_id']]=='control'),
        'contextual_observation_count':cc['observation'],'contextual_observation_record_ids':sorted(r['record_id'] for r in rr if categories[r['record_id']]=='observation'),
        'procedure_count':cc['procedure'],'benchmark_row_count':cc['benchmark'],'public_hub_exists':bool(m),
        'public_hub_component_only':bool(m['component_only']) if m else None,'public_hub_route_contributions':len(contributions),
        'component_route_contribution_count':len(components),'component_route_record_ids':components,
        'primary_reviewed_source_count':len({r['lineage']['source_group'] for r in rr if r['quality']['review_status']=='source_reviewed' and r['record_type']!='procedure'}),'material_hub_id':m['id'] if m else None,
        'material_hub_url':m['url'] if m else None,'source_groups':related_sources,
        'source_links':[{'source_group':sid,**{k:primary[sid][k] for k in ('doi','url','title')}} for sid in related_sources],
        'direct_route_recipe_family_ids':sorted({byid[rid]['lineage']['recipe_family'] for rid in direct})}
      materials.append(row)
    lit=[r for r in records if r['collection']=='reviewed_literature'];bench=[r for r in records if r['collection']=='published_benchmark']
    cc=Counter(categories.values());main_si=[r for r in reviews if r['review_scope']==MAIN_SI];main_only=[r for r in reviews if r['review_scope']==MAIN_ONLY];si_only=[r for r in reviews if r['review_scope']==SI_ONLY]
    corpus=seed['corpus_snapshot']
    intake_dois,primary_dois=checked_library_sources(seed,library,primary,corpus_source)
    direct_formulas=sorted({byid[rid]['material']['formula'] for rid in route_ids})
    eligibility={task:sum(bool(row['eligibility'].get(task,{}).get('eligible')) for row in manifest['records']) for task in sorted(set().union(*(set(row['eligibility']) for row in manifest['records'])))}
    summary={**corpus,'historical_augmented_library_groups':corpus['local_paper_groups_indexed'],
      'frozen_intake_local_paper_groups':len(intake_dois),'curated_library_additions':len(primary_dois-intake_dois),
      'local_paper_groups_indexed':len(library['papers']),'canonical_records':len(records),'reviewed_literature_records':len(lit),'reviewed_literature_source_groups':len({r['lineage']['source_group'] for r in lit}),
      'published_benchmark_rows':len(bench),'published_benchmark_source_groups':len({r['lineage']['source_group'] for r in bench}),
      'total_canonical_source_groups':len(groups),'formal_full_main_and_matched_si_reviews':len(main_si),'formal_full_review_pages':sum(p['pages_read'] for p in main_si),
      'formal_full_main_reviews_si_unverified':len(main_only),'formal_full_main_only_review_pages':sum(p['pages_read'] for p in main_only),
      'formal_full_si_reviews_main_unverified':len(si_only),'formal_full_si_only_review_pages':sum(p['pages_read'] for p in si_only),
      'legacy_main_article_reviews_si_unverified':sum(p['review_status']=='legacy_main_article_review_si_unverified' for p in per_paper),
      'legacy_main_pages_inspected':sum(d['page_count'] for p in per_paper if p['review_status']=='legacy_main_article_review_si_unverified' for d in p['documents']),
      'selected_recipe_figure_review_sources':sum(p['review_status']=='selected_recipe_and_figure_review' for p in per_paper),
      'local_groups_without_canonical_records':len(intake_dois-primary_dois),
      'synthesis_route_variant_records':cc['route'],'contextual_control_variant_records':cc['control'],'shared_preparation_workup_characterization_assay_procedures':cc['procedure'],
      'nonprocedure_literature_records':len(lit)-cc['procedure'],'literature_record_type_counts':dict(sorted(Counter(r['record_type'] for r in lit).items())),
      'canonical_record_type_counts':dict(sorted(Counter(r['record_type'] for r in records).items())),
      'literature_recipe_family_ids':len({r['lineage']['recipe_family'] for r in lit}),
      'primary_synthesis_recipe_family_ids':len({byid[rid]['lineage']['recipe_family'] for rid in route_ids}),
      'public_material_hubs':len(hubs),'direct_synthesis_target_systems':len(direct_formulas),'component_only_hubs':sum(m['component_only'] for m in hubs),
      'all_nonprocedure_literature_product_identity_categories_including_controls':len({r['material']['formula'] for r in lit if r['record_type']!='procedure'}),
      'independent_experiment_count':None,'full_corpus_distinct_synthesized_material_count':None,'full_corpus_recipe_count':None,
      'verified_exact_structure_recipe_pairs':eligibility.get('exact_structure_recipe',0),'exact_coordinate_training_ready_records':eligibility.get('exact_structure_recipe',0),
      'contextual_observation_records':cc['observation'],'recipe_or_control_literature_records':cc['route']+cc['control'],
      'contextual_observation_family_ids':len({r['lineage']['recipe_family'] for r in lit if r['record_type']=='observation'}),
      'source_checked_synthesis_structure_rows':len(pairs['rows']),'source_groups_with_synthesis_structure_rows':len({r['source_group'] for r in pairs['rows']}),
      'deduplicated_physical_sample_outcomes':None,'reviewed_literature_experimental_rows':cc['experiment']}
    return {'inventory_version':'generated-from-reviewed-inputs-v1','scope':seed['scope'],'summary':summary,'count_definitions':copy.deepcopy(seed['count_definitions']),
      'material_system_lists':{'direct_synthesis_targets':direct_formulas,
        'control_only_additional_product_labels':sorted({r['material']['formula'] for r in records if categories[r['record_id']]=='control'}-set(direct_formulas)),
        'component_only_public_hubs':sorted(m['formula'] for m in hubs if m['component_only']),
        'benchmark_only_product':next(iter({r['material']['formula'] for r in bench})) if len({r['material']['formula'] for r in bench})==1 else None,
        'contextual_observation_product_labels':sorted({r['material']['formula'] for r in lit if r['record_type']=='observation'}),
        'excluded_precursor_procedure_identities':copy.deepcopy(seed['excluded_precursor_procedure_identities'])},
      'corpus_candidate_metadata':copy.deepcopy(seed['corpus_candidate_metadata']),'per_paper':per_paper,'per_material':materials,
      'benchmark_scope':copy.deepcopy(seed['benchmark_scope']),'training_eligibility':eligibility,
      'review_priority_constraints':copy.deepcopy(seed['review_priority_constraints']),
      'provenance':{'mode':'deterministic_build_output','baseline_inventory_sha256':seed['baseline_inventory_sha256'],
        'reviewed_evidence_sha256':hashed(seed),'record_ids_sha256':hashed(sorted(byid)),
        'generated_dataset_version_observed':manifest['dataset_version'],'publication_verification':'Separate live deployment receipt; generation alone grants no publication credit.'}}

def generate(root):
    root=Path(root);dist=root/'dist/data'
    return derive(read(root/'data/inventory-evidence.json'),[read(p) for p in sorted((root/'data/records').glob('*.json'))],
      [read(p) for p in sorted((dist/'materials').glob('*.json'))],read(dist/'paper-review-index.json')['papers'],
      read(dist/'library-index.json'),read(dist/'dataset-manifest.json'),read(dist/'synthesis-structure-pairs.json'),
      read(root/'data/corpus/library-source.json'))
