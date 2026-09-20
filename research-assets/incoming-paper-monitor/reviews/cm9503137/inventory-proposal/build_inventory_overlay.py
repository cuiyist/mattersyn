"""Private 12-record Danek inventory overlay, with optional actual-build check.

Source/Site/queue are read-only. A prospective source-reviewed promotion is an
explicit assumption for counting, not a change to the drafts or a passed audit.
"""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import argparse,copy,hashlib,json,sys
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
REVIEW=OUT.parent
SITE=REVIEW.parents[3]/'recipe-atlas'
sys.path.insert(0,str(SITE/'scripts'))
from dataset_lib import eligibility,build_groups,digest,validate_record
from build_atlas import synthesis_route
SID='danek1996'
ROUTES={f'danek-1996-{x}' for x in ['znse-overgrowth','bare-dot-film','overcoated-dot-film']}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,v):(OUT/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--actual',action='store_true');args=ap.parse_args()
    basepath=OUT/'base-inventory-summary.json'
    if not basepath.exists():
        basepath.write_bytes((SITE/'data/inventory-summary.json').read_bytes())
    base=read(basepath);assert base['summary']['canonical_records']==172
    inv=copy.deepcopy(base)
    draftfiles={p.stem:p for p in (REVIEW/'canonical-drafts').glob('*.json')};assert len(draftfiles)==12
    canonicalfiles={p.stem:p for p in (SITE/'data/records').glob('*.json')}
    records={rid:read(p) for rid,p in canonicalfiles.items() if rid not in draftfiles};assert len(records)==172
    baseline_records=copy.deepcopy(records)
    promoted={};errors=[]
    for rid,p in draftfiles.items():
        r=read(canonicalfiles[rid]) if args.actual else read(p)
        if not args.actual:
            r['quality']['review_status']='source_reviewed'
            r['quality']['requested_tasks']=['precursor_selection','partial_protocol'] if rid in ROUTES else []
        assert r['quality']['review_status']=='source_reviewed'
        assert r['quality']['requested_tasks']==(['precursor_selection','partial_protocol'] if rid in ROUTES else [])
        errors+=validate_record(r);promoted[rid]=r;records[rid]=r
    assert not errors,errors
    routes={rid:r for rid,r in records.items() if synthesis_route(r)}
    literature={rid:r for rid,r in records.items() if r['collection']=='reviewed_literature'}
    procedures={rid:r for rid,r in literature.items() if r['record_type']=='procedure'}
    observations={rid:r for rid,r in literature.items() if r['record_type']=='observation'}
    controls={rid:r for rid,r in literature.items() if rid not in routes and rid not in procedures and rid not in observations}
    benchmark={rid:r for rid,r in records.items() if r['collection']=='published_benchmark'}
    sourcegroups=sorted({r['lineage']['source_group'] for r in records.values()})
    src={g:next(s for r in records.values() if r['lineage']['source_group']==g for s in r['sources'] if s['id']==g) for g in sourcegroups}
    groups=build_groups(list(records.values()))
    elig={t:sum(eligibility(r)[t]['eligible'] for r in records.values()) for t in eligibility(next(iter(records.values())))}
    corpus=read(SITE/'data/corpus/library-source.json')
    localdois={p['doi'].lower() for p in corpus['papers'] if p['coverage']['localDocumentCount']>0}
    reviewed_local={s['doi'].lower() for s in src.values()}&localdois
    index=read(SITE/'dist/data/materials-index.json')
    hubs={m['formula']:read(SITE/'dist/data/materials'/f'{m["id"]}.json') for m in index['materials']}
    for h in hubs.values():
        h['record_ids']=[rid for rid in h['record_ids'] if rid not in promoted]
        h['direct_record_ids']=[rid for rid in h['direct_record_ids'] if rid not in promoted]
    for rid in ROUTES:
        r=promoted[rid]
        for f in dict.fromkeys([r['material']['formula'],*r['material']['components']]):
            assert f in hubs,('Unexpected new material hub',f)
            h=hubs[f];h['record_ids'].append(rid)
            if f==r['material']['formula']:h['direct_record_ids'].append(rid)
    for h in hubs.values():
        h['record_ids']=sorted(set(h['record_ids']));h['direct_record_ids']=sorted(set(h['direct_record_ids']));h['component_only']=not h['direct_record_ids']
    direct=sorted({r['material']['formula'] for r in routes.values()});components=sorted(f for f,h in hubs.items() if h['component_only'])
    s=inv['summary']
    s.update({'canonical_records':len(records),'reviewed_literature_records':len(literature),'reviewed_literature_source_groups':len({r['lineage']['source_group'] for r in literature.values()}),'total_canonical_source_groups':len(sourcegroups),'local_groups_without_canonical_records':len(localdois)-len(reviewed_local),'synthesis_route_variant_records':len(routes),'contextual_control_variant_records':len(controls),'shared_preparation_workup_characterization_assay_procedures':len(procedures),'contextual_observation_records':len(observations),'nonprocedure_literature_records':len(literature)-len(procedures),'recipe_or_control_literature_records':len(routes)+len(controls),'literature_record_type_counts':dict(sorted(Counter(r['record_type'] for r in literature.values()).items())),'canonical_record_type_counts':dict(sorted(Counter(r['record_type'] for r in records.values()).items())),'literature_recipe_family_ids':len({r['lineage']['recipe_family'] for r in literature.values()}),'primary_synthesis_recipe_family_ids':len({r['lineage']['recipe_family'] for r in routes.values()}),'contextual_observation_family_ids':len({r['lineage']['recipe_family'] for r in observations.values()}),'public_material_hubs':len(hubs),'direct_synthesis_target_systems':len(direct),'component_only_hubs':len(components),'all_nonprocedure_literature_product_identity_categories_including_controls':len({r['material']['formula'] for r in literature.values() if r['record_type']!='procedure'}),'formal_full_main_reviews_si_unverified':base['summary']['formal_full_main_reviews_si_unverified']+1,'formal_full_main_only_review_pages':base['summary']['formal_full_main_only_review_pages']+8,'verified_exact_structure_recipe_pairs':elig['exact_structure_recipe']})
    inv['inventory_version']=datetime.now(timezone.utc).date().isoformat()+'-danek-'+('actual-local' if args.actual else 'prospective')+'-snapshot'
    inv['scope']='Inventory '+('reconciled to locally integrated canonical records' if args.actual else 'proposal over the saved 172-record baseline plus 12 Danek drafts; source-review promotion is simulated conditionally in memory pending independent canonical audit')+'. Incoming-folder counts are separate. Record/hub counts are not independent experiment counts or confirmation of deployment.'
    inv['count_definitions'].update({'contextual_control':f'{len(controls)} protocol-variant controls are separate from {len(routes)} synthesis routes, {len(procedures)} procedures and {len(observations)} observations. Danek no-seed/no-DEZn variants add two controls; the annealing diagnostic is typed as a procedure.','contextual_observation':'Scoped characterization series or incomplete growth observations: Littau AKS41, Heath unpatterned growth and three Danek observations. They do not create additional synthesis routes.','recipe_family':f'{s["literature_recipe_family_ids"]} literature grouping IDs; {s["primary_synthesis_recipe_family_ids"]} contain primary synthesis routes. Grouping IDs are not unique physical recipes or independent runs.','material_system':f'{len(direct)} direct product-system labels retain architecture and unresolved stoichiometry. {len(hubs)} public hubs include {len(components)} component-only cross-links. Colloidal CdSe-core/ZnSe-overlayer particles and ZnSe-matrix films have distinct routes under the shared CdSe/ZnSe system.','danek_series':'Figure-defined particle sizes, shell ratios, optical aliquots and film-deposition categories are source-scoped observations. Their number must not be interpreted as fully specified independent synthesis recipes.'})
    inv['material_system_lists']['direct_synthesis_targets']=direct
    inv['material_system_lists']['component_only_public_hubs']=components
    inv['material_system_lists']['contextual_observation_product_labels']=sorted({r['material']['formula'] for r in observations.values()})
    inv['training_eligibility']=elig
    source=src[SID]
    row={'source_group':SID,'doi':source['doi'],'url':source['url'],'title':source['title'],'year':1996,'has_local_corpus_group':source['doi'].lower() in localdois,'review_status':'full_supplied_main_review_si_unverified','review_scope':'Eight supplied main pages read and visually checked; independent supplied-main source audit complete. Matching SI not located or verified. Canonical record review and reader/publication acceptance are separate gates; prospective inventory promotion is conditional.','documents':[{'role':'main','page_count':8,'all_text_read':True,'all_visually_reviewed':True}],'evidence_locator':'data/paper-reviews/danek1996.json','paper_review_url':'paper-review.html?id=danek1996','si_status':'not_located_or_verified','canonical_record_count':len(promoted),'synthesis_route_variant_count':len(promoted.keys()&routes.keys()),'contextual_control_count':len(promoted.keys()&controls.keys()),'contextual_observation_count':len(promoted.keys()&observations.keys()),'procedure_count':len(promoted.keys()&procedures.keys()),'benchmark_row_count':0,'measurement_entry_count':sum(len(r['measurements']) for r in promoted.values()),'record_type_counts':dict(sorted(Counter(r['record_type'] for r in promoted.values()).items())),'canonical_recipe_family_ids':sorted({r['lineage']['recipe_family'] for r in promoted.values()}),'direct_route_material_systems':sorted({routes[rid]['material']['formula'] for rid in promoted if rid in routes}),'record_ids':sorted(promoted),'record_urls':{rid:'records/'+rid+'.html' for rid in sorted(promoted)},'notes':['Three routes: solution ZnSe overgrowth, matrix deposition with bare dots, and matrix deposition with pre-overcoated dots.','Four procedures include cited upstream preparation, delivery dispersion, characterization and the annealing diagnostic; only no-seed/no-DEZn are counted as control variants.','Three observation records preserve incomplete high-temperature overgrowth and multiple solution/film characterization cohorts.','Figure1 has an embedded four-row table, not four complete recipes; the article contains11figures, one embedded table, one unnumbered reaction and18 numbered references.','Product ratios, surface ratios, derived shell dimensions and absolute versus relative luminescence values retain distinct scopes.']}
    inv['per_paper']=sorted([*copy.deepcopy(base['per_paper']),row],key=lambda x:x['source_group'])
    old={r['material_system']:r for r in base['per_material']};material_rows=[]
    for f in sorted(old.keys()|hubs.keys()):
        m=copy.deepcopy(old.get(f,{'material_system':f,'notes':[]}));h=hubs.get(f)
        rr={rid:r for rid,r in records.items() if r['material']['formula']==f};dr=sorted(rr.keys()&routes.keys());hids=set(h['record_ids']) if h else set();component_ids=sorted(hids-set(dr));sg=sorted({records[rid]['lineage']['source_group'] for rid in rr.keys()|hids})
        m.update({'direct_synthesis_route_variant_count':len(dr),'direct_route_record_ids':dr,'contextual_control_count':len(rr.keys()&controls.keys()),'contextual_control_record_ids':sorted(rr.keys()&controls.keys()),'contextual_observation_count':len(rr.keys()&observations.keys()),'contextual_observation_record_ids':sorted(rr.keys()&observations.keys()),'procedure_count':len(rr.keys()&procedures.keys()),'benchmark_row_count':len(rr.keys()&benchmark.keys()),'public_hub_exists':bool(h),'public_hub_component_only':h['component_only'] if h else None,'public_hub_route_contributions':len(hids),'component_route_contribution_count':len(component_ids),'component_route_record_ids':component_ids,'primary_reviewed_source_count':len({r['lineage']['source_group'] for rid,r in rr.items() if rid in literature and rid not in procedures}),'material_hub_id':h['id'] if h else None,'material_hub_url':h['url'] if h else None,'source_groups':sg,'source_links':[{'source_group':g,'doi':src[g]['doi'],'url':src[g]['url'],'title':src[g]['title']} for g in sg],'direct_route_recipe_family_ids':sorted({routes[rid]['lineage']['recipe_family'] for rid in dr})})
        if f in ['CdSe','ZnSe','CdSe/ZnSe']:
            m['notes']=['Before the Danek1996 addition: '+n for n in old.get(f,{}).get('notes',[])]+[f'Danek1996 adds three existing route IDs to this hub; the current route contribution count is {len(hids)}. The shell-overgrowth route is distinct from the two matrix-film routes; component links do not create standalone CdSe or ZnSe synthesis recipes.']
        material_rows.append(m)
    inv['per_material']=material_rows
    evidencepaths=[SITE/'data/corpus/library-source.json',SITE/'dist/data/materials-index.json',SITE/'dist/data/library-index.json',SITE/'dist/data/dataset-manifest.json',SITE/'dist/data/validation-report.json',REVIEW/'source-identity.json',REVIEW/'source-audit.json',REVIEW/'public-review-proposal/danek1996.json']
    auditpath=REVIEW/'canonical-records-audit.json'
    canonical_audit=read(auditpath) if auditpath.exists() else None
    if auditpath.exists():evidencepaths.append(auditpath)
    inv['provenance']={**base['provenance'],'canonical_record_files':len(records),'canonical_tree_sha256':digest({rid:digest(r) for rid,r in sorted(records.items())}),'canonical_tree_hash_rule':'SHA256 of sorted record-ID to normalized-record-digest JSON; '+('actual integrated records.' if args.actual else '172 baseline records plus 12 in-memory conditionally promoted drafts.'),'baseline_inventory_sha256':sha(basepath),'inventory_mode':'actual_local' if args.actual else 'prospective_overlay','promotion_assumption':'Source-reviewed metadata is simulated only after required canonical audit passes. Only znse-overgrowth, bare-dot-film and overcoated-dot-film request precursor_selection and partial_protocol. No draft/Site promotion occurs here.','canonical_audit_status_observed':canonical_audit.get('status') if canonical_audit else 'not_available_at_snapshot','publication_verification':'Not assessed; publication remains outside this private inventory task.','generated_dataset_version_observed':read(SITE/'dist/data/dataset-manifest.json')['dataset_version'],'source_input_sha256':{str(p.relative_to(SITE)) if p.is_relative_to(SITE) else 'private/'+p.name:sha(p) for p in evidencepaths}}
    checks=[]
    def check(n,v):checks.append({'check':n,'passed':bool(v)})
    check('Five record categories partition entire dataset',set(records)==routes.keys()|controls.keys()|procedures.keys()|observations.keys()|benchmark.keys() and len(records)==sum(map(len,[routes,controls,procedures,observations,benchmark])))
    check('Derived totals from actual types',tuple(map(len,[records,routes,controls,procedures,observations,benchmark,hubs,direct,components]))==(184,40,11,28,5,100,17,12,5))
    check('Only three new synthesis routes',promoted.keys()&routes.keys()==ROUTES)
    check('One new source/evaluation group, no split leakage',len(sourcegroups)==len(set(groups.values()))==13 and len({groups[rid] for rid in promoted})==1)
    check('Legacy corpus unchanged',s['local_document_files_indexed']==corpus['summary']['sourceDocumentCount']==7373 and s['local_paper_groups_indexed']==len(localdois)==4176 and s['unique_document_content_hashes']==6857)
    check('Source scopes remain separate',s['formal_full_main_and_matched_si_reviews']==5 and s['formal_full_review_pages']==74 and s['formal_full_main_reviews_si_unverified']==3 and s['formal_full_main_only_review_pages']==21)
    check('Prior per-paper manual rows exact',all(next(x for x in inv['per_paper'] if x['source_group']==p['source_group'])==p for p in base['per_paper']))
    check('Unaffected material notes exact',all(next(x for x in material_rows if x['material_system']==m['material_system'])['notes']==m['notes'] for m in base['per_material'] if m['material_system'] not in ['CdSe','ZnSe','CdSe/ZnSe']))
    check('Affected old notes retained with explicit historical scope',all(all('Before the Danek1996 addition: '+note in next(x for x in material_rows if x['material_system']==f)['notes'] for note in old[f]['notes']) for f in ['CdSe','ZnSe','CdSe/ZnSe']))
    check('No new material hub',set(hubs)=={m['formula'] for m in index['materials']})
    check('Three intended hubs gain the three existing route IDs',all(ROUTES<=set(hubs[f]['record_ids']) for f in ['CdSe/ZnSe','CdSe','ZnSe']))
    check('Per-paper counts reconcile',sum(x['canonical_record_count'] for x in inv['per_paper'])==len(records) and sum(x['synthesis_route_variant_count'] for x in inv['per_paper'])==len(routes) and sum(x['contextual_control_count'] for x in inv['per_paper'])==len(controls) and sum(x['procedure_count'] for x in inv['per_paper'])==len(procedures) and sum(x.get('contextual_observation_count',0) for x in inv['per_paper'])==len(observations))
    check('Exactly three records eligible for the two requested tasks',all({t for t,v in eligibility(r).items() if v['eligible']}==({'precursor_selection','partial_protocol'} if rid in ROUTES else set()) for rid,r in promoted.items()))
    check('No exact-structure or success labels',elig['exact_structure_recipe']==elig['success_prediction']==0)
    check('Unknown corpus recipe/material/experiment totals remain unknown',all(s[k] is None for k in ['independent_experiment_count','full_corpus_recipe_count','full_corpus_distinct_synthesized_material_count']))
    manifest=read(SITE/'dist/data/dataset-manifest.json');compare={'status':'pending_actual_rebuild','observed_records':manifest['record_count']}
    if manifest['record_count']==len(records):
        validation=read(SITE/'dist/data/validation-report.json');actual_index=read(SITE/'dist/data/materials-index.json');reviews=read(SITE/'dist/data/paper-review-index.json')
        compare={'status':'compared','observed_records':manifest['record_count'],'dataset_version':manifest['dataset_version']}
        check('Actual eligibility matches overlay',validation['eligible_by_task']==elig)
        check('Actual record membership matches overlay',{r['record_id'] for r in manifest['records']}==set(records))
        check('Actual hub identities match overlay',{(h['formula'],h['component_only']) for h in actual_index['materials']}=={(f,h['component_only']) for f,h in hubs.items()})
        check('Actual main-only review set includes all three',{r['id'] for r in reviews['papers'] if r['review_scope']=='supplied_main_only_si_unverified'}=={'littau1993','heath1996','danek1996'})
        for f in ['CdSe','CdSe/ZnSe','ZnSe']:
            actual=read(SITE/'dist/data/materials'/f'{hubs[f]["id"]}.json')
            check(f+' actual route membership',set(actual['record_ids'])==set(hubs[f]['record_ids']) and set(actual['direct_record_ids'])==set(hubs[f]['direct_record_ids']))
    if args.actual:check('Actual mode has matching rebuild',compare['status']=='compared')
    failures=[x['check'] for x in checks if not x['passed']]
    validation={'status':'passed' if not failures else 'failed','created_utc':datetime.now(timezone.utc).isoformat(),'mode':'actual_local' if args.actual else 'prospective_overlay','checks':checks,'errors':failures,'summary':s,'training_eligibility':elig,'actual_rebuild_comparison':compare,'draft_sha256':{rid:sha(p) for rid,p in draftfiles.items()},'baseline_canonical_file_sha256':{rid:sha(canonicalfiles[rid]) for rid in baseline_records},'source_groups':sourcegroups,'danek_evaluation_group':groups[next(iter(promoted))],'danek_measurement_entry_count':row['measurement_entry_count'],'site_files_written':False,'published':False}
    write('validation.json',validation);assert not failures,failures
    write('inventory-summary.json',inv)
    (OUT/'REPORT.md').write_text(f'''# Danek1996 inventory proposal

Mode: **{validation['mode']}**. Counts derive from the 172-record saved baseline plus 12 current drafts. Source-reviewed status is a conditional counting assumption pending independent canonical approval; only the three route IDs request precursor selection and partial protocol. No files are promoted.

**184 records = 40 routes + 11 controls + 28 procedures + 5 observations + 100 benchmark rows.** The 12 Danek additions are three literature protocols, four procedures (including the annealing diagnostic), two protocol-variant controls and three observations. They retain {row['measurement_entry_count']} measurement entries and one evaluation group. There are **13 source/evaluation groups** overall.

The existing **17 hubs (12 direct systems and five component-only hubs)** remain. CdSe/ZnSe, CdSe and ZnSe gain links to the same three route IDs. Colloidal passivation and matrix-film fabrication remain distinct; component links do not create extra recipes. Prior manual notes are preserved, with affected old hub counts explicitly scoped to the pre-Danek baseline.

Scope: **five matched-main/SI reviews / 74 pages; three supplied-main-only reviews / 21 pages**. SI for Danek remains unverified. The separate historical scopes remain. The legacy library remains **7,373 documents / 4,176 local groups / 6,857 unique hashes**; incoming documents are not added to those totals. Full-corpus materials, recipes and independent experiment counts remain unknown.

Training eligibility: `{elig}`. **{len(checks)} checks passed**. Actual rebuild comparison: **{compare['status']}**, observed records {manifest['record_count']}. Refresh with `--actual` after root imports/builds, and review source/canonical/reader/publication gates separately. No Site, source or queue file changed.
''',encoding='utf-8')
    print(json.dumps({'status':'passed','mode':validation['mode'],'checks':len(checks),'records':len(records),'routes':len(routes),'controls':len(controls),'procedures':len(procedures),'observations':len(observations),'hubs':len(hubs),'source_groups':len(sourcegroups),'danek_measurements':row['measurement_entry_count'],'actual_comparison':compare['status']}))

if __name__=='__main__':main()
