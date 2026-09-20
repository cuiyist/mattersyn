"""Reconcile a private inventory proposal against current local canonical/build data.

Never writes the Site, source library, monitor ledger, or incoming folder. The saved
baseline preserves the prior manual review notes independently of later imports.
"""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json
import sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
SITE = OUT.parents[4] / 'recipe-atlas'
sys.path.insert(0, str(SITE / 'scripts'))
from build_atlas import synthesis_route
from review_scope import MAIN_SI, MAIN_ONLY, source_review_scope


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(value):
    return sha(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())


def write(path, value):
    assert path.resolve().is_relative_to(OUT.resolve())
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    evidence = {}
    def read(rel):
        data=(SITE/rel).read_bytes()
        evidence[rel]={'sha256':sha(data),'bytes':len(data)}
        return json.loads(data)
    baseline_path=OUT/'base-inventory-summary.json'
    if not baseline_path.exists():
        OUT.mkdir(parents=True,exist_ok=True)
        baseline_path.write_bytes((SITE/'data/inventory-summary.json').read_bytes())
    baseline=json.loads(baseline_path.read_bytes())
    inventory=copy.deepcopy(baseline)
    corpus=read('data/corpus/library-source.json')
    library=read('dist/data/library-index.json')
    manifest=read('dist/data/dataset-manifest.json')
    validation=read('dist/data/validation-report.json')
    hub_index=read('dist/data/materials-index.json')
    review_index=read('dist/data/paper-review-index.json')
    benchmark=read('dist/data/baseline-report.json')
    records={}
    for path in sorted((SITE/'data/records').glob('*.json')):
        record=read(path.relative_to(SITE).as_posix())
        assert record['record_id'] not in records
        records[record['record_id']]=record
    ledgers={}
    for path in sorted((SITE/'data/paper-reviews').glob('*.json')):
        ledger=read(path.relative_to(SITE).as_posix())
        ledgers[ledger['paper_id']]=ledger
    hubs={h['formula']:read('dist/data/materials/'+h['id']+'.json') for h in hub_index['materials']}
    original_papers={p['source_group']:p for p in baseline['per_paper']}
    original_materials={m['material_system']:m for m in baseline['per_material']}
    lit={k:r for k,r in records.items() if r['collection']=='reviewed_literature'}
    bench={k:r for k,r in records.items() if r['collection']=='published_benchmark'}
    routes={k:r for k,r in lit.items() if synthesis_route(r)}
    procedures={k:r for k,r in lit.items() if r['record_type']=='procedure'}
    observations={k:r for k,r in lit.items() if r['record_type']=='observation'}
    controls={k:r for k,r in lit.items() if k not in routes and k not in procedures and k not in observations}
    source_groups=sorted({r['lineage']['source_group'] for r in records.values()})
    source_meta={g:next(s for r in records.values() if r['lineage']['source_group']==g for s in r['sources'] if s['id']==g) for g in source_groups}
    local_corpus={p['doi'].lower():p for p in corpus['papers'] if p['coverage']['localDocumentCount']>0}
    local_canonical={source_meta[g]['doi'].lower() for g in source_groups} & local_corpus.keys()
    record_groups={g:{k:r for k,r in records.items() if r['lineage']['source_group']==g} for g in source_groups}
    scoped_reviews={g:source_review_scope(r) for g,r in ledgers.items()}
    main_si={g:r for g,r in ledgers.items() if scoped_reviews[g]['scope']==MAIN_SI}
    main_only={g:r for g,r in ledgers.items() if scoped_reviews[g]['scope']==MAIN_ONLY}
    reviewed_pages=lambda data:sum(d['page_count'] for r in data.values() for d in r['documents'])
    direct_systems=sorted({r['material']['formula'] for r in routes.values()})
    component_hubs=sorted(f for f,h in hubs.items() if h['component_only'])
    all_nonprocedure={k:r for k,r in lit.items() if r['record_type']!='procedure'}
    families={r['lineage']['recipe_family'] for r in lit.values()}
    primary_families={r['lineage']['recipe_family'] for r in routes.values()}
    obs_families={r['lineage']['recipe_family'] for r in observations.values()}
    elig=Counter({task:0 for task in validation['eligible_by_task']})
    for item in manifest['records']:
        for task,gate in item['eligibility'].items():
            elig[task]+=bool(gate['eligible'])
    summary=inventory['summary']
    summary.update({
        'canonical_records':len(records),'reviewed_literature_records':len(lit),
        'reviewed_literature_source_groups':len({r['lineage']['source_group'] for r in lit.values()}),
        'published_benchmark_rows':len(bench),
        'published_benchmark_source_groups':len({r['lineage']['source_group'] for r in bench.values()}),
        'total_canonical_source_groups':len(source_groups),
        'formal_full_main_and_matched_si_reviews':len(main_si),
        'formal_full_review_pages':reviewed_pages(main_si),
        'formal_full_main_reviews_si_unverified':len(main_only),
        'formal_full_main_only_review_pages':reviewed_pages(main_only),
        'local_groups_without_canonical_records':len(local_corpus)-len(local_canonical),
        'synthesis_route_variant_records':len(routes),
        'contextual_control_variant_records':len(controls),
        'contextual_observation_records':len(observations),
        'shared_preparation_workup_characterization_assay_procedures':len(procedures),
        'nonprocedure_literature_records':len(all_nonprocedure),
        'recipe_or_control_literature_records':len(routes)+len(controls),
        'literature_record_type_counts':dict(sorted(Counter(r['record_type'] for r in lit.values()).items())),
        'canonical_record_type_counts':dict(sorted(Counter(r['record_type'] for r in records.values()).items())),
        'literature_recipe_family_ids':len(families),
        'primary_synthesis_recipe_family_ids':len(primary_families),
        'contextual_observation_family_ids':len(obs_families),
        'public_material_hubs':len(hubs),'direct_synthesis_target_systems':len(direct_systems),
        'component_only_hubs':len(component_hubs),
        'all_nonprocedure_literature_product_identity_categories_including_controls':len({r['material']['formula'] for r in all_nonprocedure.values()}),
        'verified_exact_structure_recipe_pairs':elig['exact_structure_recipe'],
    })
    inventory['inventory_version']=datetime.now(timezone.utc).date().isoformat()+'-littau-local-reconciled-snapshot'
    inventory['scope']='Read-only reconciliation of the legacy corpus baseline, current canonical records, local generated hubs and formal review ledgers. Incoming-folder queue totals are separate. Counts are curation units, not independent experiments; local generated public-facing routes do not establish remote publication.'
    definitions=inventory['count_definitions']
    definitions.update({
        'contextual_control':f'The {len(controls)} Nakonechnyi core-stability/no-seed/low-OA control variants, kept distinct from the {len(routes)} current synthesis-route records and contextual observations.',
        'contextual_observation':'A source-reviewed characterization/context record without a reconstructed synthesis recipe. AKS41 is an earlier-apparatus observation, not a fourth Littau recipe, control experiment or current-apparatus batch.',
        'recipe_family':f'Assigned canonical grouping for related records, not unique physical recipes: {len(families)} literature grouping IDs; {len(primary_families)} contain primary synthesis routes, one is the ZnO post-treatment family and one is the AKS41 observation family.',
        'material_system':f'Direct product identity retaining architecture and unresolved stoichiometry. The {len(direct_systems)} direct system labels include unresolved Fe–O and Si/SiOx. Adding the no-seed control product labels CdS and ZnSe gives 13 nonprocedure literature identity categories. The {len(hubs)} generated hubs include {len(component_hubs)} component-only cross-links; these are not additional standalone syntheses.',
        'public_material_hub':'A locally generated public-facing material/component route. Existence is checked against generated files, not a remote deployment check. Shared canonical record IDs are counted once globally.',
        'nonprocedure_literature':'All literature records except supporting procedures: synthesis routes, contextual controls and contextual observations. The observation is excluded from recipe_or_control_literature_records.',
        'legacy_corpus_baseline':'The fixed indexed downloaded_papers corpus: 7,373 document files and 4,176 groups with local documents. Incoming-folder tracking is not added to these counts, including byte-duplicate incoming copies.',
    })
    inventory['material_system_lists']['direct_synthesis_targets']=direct_systems
    inventory['material_system_lists']['component_only_public_hubs']=component_hubs
    inventory['material_system_lists']['contextual_observation_product_labels']=sorted({r['material']['formula'] for r in observations.values()})
    inventory['training_eligibility']=dict(elig)
    papers=[]
    for group in source_groups:
        rr=record_groups[group]; source=source_meta[group]
        p=copy.deepcopy(original_papers.get(group,{}))
        if not p:
            assert group=='littau1993','Unknown new source requires manual scope review: '+group
            p={'source_group':group,'doi':source['doi'],'url':source['url'],'title':source['title'],'year':source['year'],
                'review_status':'full_supplied_main_review_si_unverified',
                'review_scope':'All seven supplied main pages read and visually inspected with independent source and bounded record-join audits. Matching SI not located or verified. The three current-apparatus formulation records, nine supporting procedures and AKS41 observation retain unresolved specimen linkage, source conflicts and missing parameters. Final reader integration and publication are separate gates.',
                'documents':[{'role':d['role'],'page_count':d['page_count'],
                    'all_text_read':all(page['text_read'] for page in d['pages']),
                    'all_visually_reviewed':all(page['visual_review'] for page in d['pages'])} for d in ledgers[group]['documents']],
                'evidence_locator':'data/paper-reviews/littau1993.json','paper_review_url':'paper-review.html?id=littau1993',
                'si_status':'not_located_or_verified',
                'notes':['The 1.0, 2.0 and 6.0 labels are supplied 0.1%-disilane/He stock-mixture flows and formulation families, not independently identified physical batches.',
                         'AKS41 is a contextual observation from an earlier apparatus; no quantified synthesis is reconstructed and no training task is enabled.',
                         'Si/SiOx retains unresolved surface stoichiometry and the unconfirmed 1.0 crystallinity; Si is a component-only link, not a bare-silicon synthesis.',
                         '48 measurement entries are scoped separately across the 13 records; they are not 48 independent experiments.']}
        ids=sorted(rr)
        p.update({'has_local_corpus_group':source['doi'].lower() in local_corpus,
            'canonical_record_count':len(rr),'synthesis_route_variant_count':len(rr.keys() & routes.keys()),
            'contextual_control_count':len(rr.keys() & controls.keys()),
            'contextual_observation_count':len(rr.keys() & observations.keys()),
            'procedure_count':len(rr.keys() & procedures.keys()),'benchmark_row_count':len(rr.keys() & bench.keys()),
            'measurement_entry_count':sum(len(r['measurements']) for r in rr.values()),
            'record_type_counts':dict(sorted(Counter(r['record_type'] for r in rr.values()).items())),
            'canonical_recipe_family_ids':sorted({r['lineage']['recipe_family'] for r in rr.values()}),
            'direct_route_material_systems':sorted({r['material']['formula'] for k,r in rr.items() if k in routes}),
            'record_ids':ids,'record_urls':{rid:'records/'+rid+'.html' for rid in ids}})
        papers.append(p)
    inventory['per_paper']=papers
    materials=[]
    for formula in sorted(original_materials.keys() | hubs.keys()):
        m=copy.deepcopy(original_materials.get(formula,{}))
        h=hubs.get(formula)
        rr={k:r for k,r in records.items() if r['material']['formula']==formula}
        direct=sorted(rr.keys() & routes.keys())
        hub_ids=set(h['record_ids']) if h else set()
        component=sorted(hub_ids-set(direct))
        linked_groups=sorted({records[k]['lineage']['source_group'] for k in rr.keys() | hub_ids})
        notes=m.get('notes',[])
        if formula=='Si/SiOx':
            notes=['Three current-apparatus formulation variants; nine supporting procedures and one earlier-apparatus AKS41 observation are separate curation units, not additional synthesis routes.',
                   'The oxide stoichiometry is unresolved and 1.0 crystallinity is not directly established. Neither the slash label nor the illustrative lattice is a measured atomic-structure label.']
        elif formula=='Si':
            notes=['Component-only cross-links to the same three surface-oxidized Si/SiOx formulations; no separate bare-Si synthesis is established.',
                   'Oxide-layer information remains within Si/SiOx; no standalone SiOx synthesis or separate oxide material page is counted.']
        m.update({'material_system':formula,'direct_synthesis_route_variant_count':len(direct),'direct_route_record_ids':direct,
            'contextual_control_count':len(rr.keys() & controls.keys()),'contextual_control_record_ids':sorted(rr.keys() & controls.keys()),
            'contextual_observation_count':len(rr.keys() & observations.keys()),'contextual_observation_record_ids':sorted(rr.keys() & observations.keys()),
            'procedure_count':len(rr.keys() & procedures.keys()),'benchmark_row_count':len(rr.keys() & bench.keys()),
            'public_hub_exists':h is not None,'public_hub_component_only':h['component_only'] if h else None,
            'public_hub_route_contributions':len(hub_ids),'component_route_contribution_count':len(component),
            'component_route_record_ids':component,
            'primary_reviewed_source_count':len({r['lineage']['source_group'] for k,r in rr.items() if k in all_nonprocedure}),
            'notes':notes,'material_hub_id':h['id'] if h else None,'material_hub_url':h['url'] if h else None,
            'source_groups':linked_groups,'source_links':[{'source_group':g,'doi':source_meta[g]['doi'],'url':source_meta[g]['url'],'title':source_meta[g]['title']} for g in linked_groups],
            'direct_route_recipe_family_ids':sorted({routes[k]['lineage']['recipe_family'] for k in direct})})
        materials.append(m)
    inventory['per_material']=materials
    canonical_hash_lines=''.join(rel+'\0'+meta['sha256']+'\n' for rel,meta in sorted(evidence.items()) if rel.startswith('data/records/'))
    inventory['provenance']={
        **baseline['provenance'],'canonical_record_files':len(records),
        'canonical_tree_sha256':sha(canonical_hash_lines.encode()),
        'canonical_tree_hash_rule':'SHA256 of sorted UTF-8 relative-path + NUL + raw-file-SHA256 + LF records; raw file hashes appear in private validation.json.',
        'base_inventory_sha256':sha(baseline_path.read_bytes()),
        'corpus_summary_snapshot':corpus['summary']['updatedAt'],
        'generated_dataset_version_observed':manifest['dataset_version'],
        'dataset_version_note':'Observed local build version; this inventory does not bump dataset version or verify deployment.',
        'publication_verification':'Not assessed; local build only.',
        'files_used':sorted(set(baseline['provenance']['files_used']) | set(evidence)),
        'summary_artifact_sha256':{rel:meta['sha256'] for rel,meta in evidence.items() if not rel.startswith(('data/records/','dist/data/materials/'))},
    }
    checks=[]
    def check(label, condition):
        checks.append({'check':label,'passed':bool(condition)})
    check('Legacy corpus baseline: 7373 documents and 4176 local groups',corpus['summary']['sourceDocumentCount']==summary['local_document_files_indexed']==7373 and len(local_corpus)==summary['local_paper_groups_indexed']==4176)
    check('Generated library is the same baseline, not incoming totals',len(library['papers'])==4176 and library['summary']==corpus['summary'] and library['local_paper_groups']==4176)
    check('Candidate counts and legacy hashes preserved',len(corpus['papers'])==summary['paper_candidate_groups_total']==4570 and summary['candidate_groups_without_local_documents']==394 and corpus['summary']['uniqueContentHashes']==summary['unique_document_content_hashes']==6857)
    check('Corpus metadata and benchmark manual notes unchanged',inventory['corpus_candidate_metadata']==baseline['corpus_candidate_metadata'] and inventory['benchmark_scope']==baseline['benchmark_scope'])
    check('Five-way category partition covers every canonical record once',set(records)==set(routes)|set(controls)|set(procedures)|set(observations)|set(bench) and sum(map(len,[routes,controls,procedures,observations,bench]))==len(records))
    check('Current expected category counts',tuple(map(len,[records,routes,controls,procedures,observations,bench]))==(168,35,9,23,1,100))
    check('Contextual controls retain the exact prior nine IDs',set(controls)=={rid for m in baseline['per_material'] for rid in m['contextual_control_record_ids']})
    check('Littau contains 48 scoped measurement entries',next(p for p in papers if p['source_group']=='littau1993')['measurement_entry_count']==48)
    check('Canonical source groups',len(source_groups)==11 and len({r['lineage']['source_group'] for r in lit.values()})==10)
    check('Per-paper IDs partition canonical IDs once',{rid for p in papers for rid in p['record_ids']}==set(records) and sum(len(p['record_ids']) for p in papers)==len(records))
    check('Library availability used for uncurated-group count',summary['local_groups_without_canonical_records']==4165)
    for old in baseline['per_paper']:
        new=next(p for p in papers if p['source_group']==old['source_group'])
        for key in ['review_scope','review_status','documents','evidence_locator','notes']:
            if key in old:
                check(old['source_group']+': preserve manual '+key,new[key]==old[key])
        check(old['source_group']+': original record set unchanged',set(old['record_ids'])==set(new['record_ids']))
    for old in baseline['per_material']:
        new=next(m for m in materials if m['material_system']==old['material_system'])
        check(old['material_system']+': preserve prior source-specific notes',old['notes']==new['notes'])
    check('Formal scope separation: five matched-SI ledgers/74 pages and one main-only/7 pages',(len(main_si),reviewed_pages(main_si),len(main_only),reviewed_pages(main_only))==(5,74,1,7))
    check('Littau main-only has no SI document',scoped_reviews['littau1993']['si_status']=='not_located_or_verified' and [d['role'] for d in ledgers['littau1993']['documents']]==['main'])
    check('Review index matches ledgers and page counts',{p['id'] for p in review_index['papers']}==set(ledgers) and all(p['review_scope']==scoped_reviews[p['id']]['scope'] and p['pages_read']==sum(d['page_count'] for d in ledgers[p['id']]['documents']) and set(p['record_ids'])<=set(records) for p in review_index['papers']))
    check('Legacy main-only and selected scopes remain distinct',summary['legacy_main_article_reviews_si_unverified']==2 and summary['legacy_main_pages_inspected']==13 and summary['selected_recipe_figure_review_sources']==2)
    check('15 hubs: 11 direct systems and four component-only pages',len(hubs)==15 and len(direct_systems)==11 and len(component_hubs)==4)
    check('Only generated Si and Si/SiOx pages added',set(hubs)-{m['material_system'] for m in baseline['per_material'] if m['public_hub_exists']}=={'Si','Si/SiOx'} and 'SiOx' not in hubs)
    all_hub_ids={rid for h in hubs.values() for rid in h['record_ids']}
    check('Shared hub contributions count as 35 unique routes',all_hub_ids==set(routes))
    for formula,h in hubs.items():
        check(formula+': generated hub IDs and direct/component assignments',set(h['record_ids'])=={r['record_id'] for r in h['records']} and set(h['direct_record_ids'])=={k for k,r in routes.items() if r['material']['formula']==formula} and h['component_only']==(not h['direct_record_ids']))
    for item in manifest['records']:
        rid=item['record_id']
        check(rid+': manifest canonical digest',rid in records and item['record_sha256']==digest(records[rid]))
    check('Manifest and validation contain same canonical records',manifest['record_count']==validation['records']==len(records) and {r['record_id'] for r in manifest['records']}==set(records))
    check('Existing schema/graph validation passed',validation['status']=='passed')
    check('Eligibility counts reconcile',dict(elig)==validation['eligible_by_task']==inventory['training_eligibility'])
    check('Validation categories reconcile',validation['curated_recipes']==len(routes)+len(controls) and validation['shared_procedures']==len(procedures) and validation['contextual_observation_records']==len(observations) and validation['published_benchmark_rows']==len(bench))
    check('Evaluation/source grouping reconciles',manifest['group_count']==validation['source_groups']==len(source_groups) and len({r['group_id'] for r in manifest['records']})==len(source_groups))
    check('No exact-structure labels or full-corpus recipe/material claims',summary['verified_exact_structure_recipe_pairs']==0 and all(summary[k] is None for k in ['independent_experiment_count','full_corpus_distinct_synthesized_material_count','full_corpus_recipe_count']))
    check('Published benchmark baseline remains 2552 source rows',benchmark['rows']==inventory['benchmark_scope']['full_source_dataset_rows']==2552 and benchmark['uniquePhysicalRecipeGroups']==inventory['benchmark_scope']['full_source_physical_recipe_groups_by_documented_input_rule'])
    unmapped_procedures=sorted(k for k,r in procedures.items() if r['material']['formula'] not in {m['material_system'] for m in materials})
    check('Only intentionally excluded iron-precursor procedures absent from material-system rows',len(unmapped_procedures)==2 and all(records[k]['material']['formula']==inventory['material_system_lists']['excluded_precursor_procedure_identity'] for k in unmapped_procedures))
    # Detect concurrent build changes; never issue a mixed-generation snapshot.
    check('Evidence files unchanged through reconciliation',all(sha((SITE/rel).read_bytes())==meta['sha256'] for rel,meta in evidence.items()))
    errors=[x['check'] for x in checks if not x['passed']]
    report={'status':'failed' if errors else 'passed','created_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Independent inventory/count reconciliation only; no new scientific reading, source-corpus expansion, final reader approval or publication.',
        'checks':checks,'errors':errors,'summary':summary,'training_eligibility':dict(elig),
        'unmapped_material_row_procedure_ids':unmapped_procedures,
        'note':'The two iron-precursor preparation records are counted in the global and per-paper procedure totals but intentionally excluded from product-material rows. Component route contributions overlap and must not be summed as independent routes.',
        'baseline_inventory_sha256':sha(baseline_path.read_bytes()),'evidence_files':evidence,
        'site_files_written':False,'published':False}
    write(OUT/'validation.json',report)
    assert not errors,'; '.join(errors)
    write(OUT/'inventory-summary.json',inventory)
    report_text=f'''# Littau inventory reconciliation proposal

The private inventory reconciles **{len(records)} canonical records = {len(routes)} synthesis routes + {len(controls)} contextual controls + {len(procedures)} supporting procedures + {len(observations)} contextual observation + {len(bench)} benchmark rows**. These are curation units, not independent experiments.

- **{len(lit)} reviewed-literature records from 10 sources**, plus 100 benchmark rows from one source: 11 source/evaluation groups.
- **15 generated material hubs**: 11 direct systems and four component-only hubs. Si/SiOx adds three direct formulation variants; Si links to those same three records. There is no generated SiOx hub.
- **Five formal main-plus-SI reviews / 74 pages**, plus **one formal main-only review / seven pages** (Littau; SI unverified). The prior two legacy main-article reviews / 13 pages and two selected-recipe/figure reviews remain separate.
- **Legacy corpus unchanged: 7,373 document files; 4,176 local paper groups; 6,857 byte-content hashes**. 4,165 local groups have no canonical records. The growing incoming folder is not added or double-counted here.
- All source-specific manual review notes and benchmark details from the saved baseline are retained. Littau has 13 records and 48 measurement entries; AKS41 is one observation, not a fourth synthesis or a control.
- Eligibility: {dict(elig)}. No exact-structure recipe pair or full-corpus material/recipe total is claimed.

**{len(checks)} checks passed.** They bind every canonical file to its generated manifest digest, reconcile every source/hub/category, verify separate review scopes and preserve baseline manual notes. `validation.json` records raw-file hashes and the evidence paths; `inventory-summary.json` includes the canonical-tree hash and hash rule.

Two iron-precursor preparation records are intentionally excluded from product-material rows but included in the global/per-paper procedure counts. Component contribution counts overlap; use unique record IDs for the 35 global routes. The 12 literature grouping IDs include 10 primary synthesis families, ZnO post-treatment and the AKS41 observation family; they are not 12 unique physical recipes.

## Parent integration

Inspect and copy only `inventory-summary.json` into the Site when accepted. The parent owns renderer changes to display `contextual_observation_records` and `per_paper.contextual_observation_count` as a fifth category, then rebuilds inventory and checks the resulting pages. Add the same distinct category to material rows where relevant. Do not label the five-way total as four categories.

The observed dataset version is {manifest['dataset_version']}; no version bump was performed. Root plans the later 0.5.0 build. Rerun this generator after that build if its version/hash provenance must reflect the final artifacts. Final reader audit and publication remain pending outside this reconciliation.

## Regenerate

Run `C:\\Users\\jiacu\\miniforge3\\python.exe -B -X utf8` with this directory's `build_inventory_proposal.py`. It reads current Site data, preserves `base-inventory-summary.json` for manual notes, and writes only this private directory. It rejects stale or concurrently changed evidence.
'''
    (OUT/'REPORT.md').write_text(report_text,encoding='utf-8')
    print(json.dumps({'status':'passed','checks':len(checks),'canonical_records':len(records),'routes':len(routes),'controls':len(controls),'procedures':len(procedures),'observations':len(observations),'benchmark_rows':len(bench),'hubs':len(hubs),'source_groups':len(source_groups)}))


if __name__=='__main__':
    main()
