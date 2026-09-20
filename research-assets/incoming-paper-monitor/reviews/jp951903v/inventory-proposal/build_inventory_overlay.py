"""Private Heath1996 inventory overlay, with optional comparison to a rebuilt Site.

Simulates only the parent-authorized metadata promotion in memory. Never changes
canonical records, Site assets or the queue. --actual uses the integrated records.
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
from dataset_lib import eligibility,build_groups,digest
from build_atlas import synthesis_route,slug

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--actual',action='store_true');args=ap.parse_args()
    baseline_path=OUT/'base-inventory-summary.json'
    if not baseline_path.exists():
        OUT.mkdir(parents=True,exist_ok=True);baseline_path.write_bytes((SITE/'data/inventory-summary.json').read_bytes())
    base=read(baseline_path);inv=copy.deepcopy(base)
    assert base['summary']['canonical_records']==168
    audit=read(REVIEW/'canonical-records-audit.json')
    assert audit['status']=='passed_bounded_scientific_draft_audit' and not audit['outstanding_findings']
    drafts={};draft_hashes={}
    for p in sorted((REVIEW/'canonical-drafts').glob('*.json')):
        assert sha(p)==audit['reviewed_hashes'][p.name]
        r=read(p);drafts[r['record_id']]=r;draft_hashes[r['record_id']]=sha(p)
    assert len(drafts)==4
    canonical_files={p.stem:p for p in (SITE/'data/records').glob('*.json')}
    records={rid:read(p) for rid,p in canonical_files.items() if rid not in drafts}
    assert len(records)==168
    proposed_routes=sorted(rid for rid,r in drafts.items() if r['record_type']=='protocol_variant' and any(o['stage']=='synthesis' for o in r['operations']))
    assert len(proposed_routes)==2
    promoted={}
    for rid,draft in drafts.items():
        if args.actual:
            r=read(canonical_files[rid])
            assert r['quality']['review_status']=='source_reviewed'
            assert r['quality']['requested_tasks']==(['precursor_selection','partial_protocol'] if rid in proposed_routes else [])
        else:
            r=copy.deepcopy(draft);r['quality']['review_status']='source_reviewed'
            r['quality']['requested_tasks']=['precursor_selection','partial_protocol'] if rid in proposed_routes else []
        promoted[rid]=r;records[rid]=r
    routes={rid:r for rid,r in records.items() if synthesis_route(r)}
    lit={rid:r for rid,r in records.items() if r['collection']=='reviewed_literature'}
    procedures={rid:r for rid,r in lit.items() if r['record_type']=='procedure'}
    observations={rid:r for rid,r in lit.items() if r['record_type']=='observation'}
    controls={rid:r for rid,r in lit.items() if rid not in routes and rid not in procedures and rid not in observations}
    bench={rid:r for rid,r in records.items() if r['collection']=='published_benchmark'}
    groups=build_groups(list(records.values()))
    source_groups=sorted({r['lineage']['source_group'] for r in records.values()})
    src={g:next(s for r in records.values() if r['lineage']['source_group']==g for s in r['sources'] if s['id']==g) for g in source_groups}
    corpus=read(SITE/'data/corpus/library-source.json')
    library=read(SITE/'dist/data/library-index.json')
    local_dois={p['doi'].lower() for p in corpus['papers'] if p['coverage']['localDocumentCount']>0}
    local_curated={s['doi'].lower() for s in src.values()} & local_dois
    elig={task:sum(eligibility(r)[task]['eligible'] for r in records.values()) for task in eligibility(next(iter(records.values())))}
    # Existing hub identities/notes survive; two Ge-containing hubs are derived from
    # the proposed routes, while Si gains component contributions from both sources.
    current_index=read(SITE/'dist/data/materials-index.json')
    hubs={m['formula']:read(SITE/'dist/data/materials'/f'{m["id"]}.json') for m in current_index['materials'] if m['formula'] not in ['Ge','Ge/Si']}
    for h in hubs.values():
        h['record_ids']=[rid for rid in h['record_ids'] if rid not in drafts]
        h['direct_record_ids']=[rid for rid in h['direct_record_ids'] if rid not in drafts]
    for rid,r in promoted.items():
        if rid not in routes:continue
        for formula in dict.fromkeys([r['material']['formula'],*r['material']['components']]):
            if formula not in hubs:hubs[formula]={'id':slug(formula),'formula':formula,'url':'material.html?id='+slug(formula),'record_ids':[],'direct_record_ids':[]}
            h=hubs[formula]
            if rid not in h['record_ids']:h['record_ids'].append(rid)
            if formula==r['material']['formula'] and rid not in h['direct_record_ids']:h['direct_record_ids'].append(rid)
    for h in hubs.values():h['component_only']=not h['direct_record_ids']
    direct=sorted({r['material']['formula'] for r in routes.values()})
    component=sorted(f for f,h in hubs.items() if h['component_only'])
    s=inv['summary']
    s.update({'canonical_records':len(records),'reviewed_literature_records':len(lit),
        'reviewed_literature_source_groups':len({r['lineage']['source_group'] for r in lit.values()}),
        'total_canonical_source_groups':len(source_groups),'local_groups_without_canonical_records':len(local_dois)-len(local_curated),
        'synthesis_route_variant_records':len(routes),'contextual_control_variant_records':len(controls),
        'shared_preparation_workup_characterization_assay_procedures':len(procedures),
        'contextual_observation_records':len(observations),
        'nonprocedure_literature_records':len(lit)-len(procedures),
        'recipe_or_control_literature_records':len(routes)+len(controls),
        'literature_record_type_counts':dict(sorted(Counter(r['record_type'] for r in lit.values()).items())),
        'canonical_record_type_counts':dict(sorted(Counter(r['record_type'] for r in records.values()).items())),
        'literature_recipe_family_ids':len({r['lineage']['recipe_family'] for r in lit.values()}),
        'primary_synthesis_recipe_family_ids':len({r['lineage']['recipe_family'] for r in routes.values()}),
        'contextual_observation_family_ids':len({r['lineage']['recipe_family'] for r in observations.values()}),
        'public_material_hubs':len(hubs),'direct_synthesis_target_systems':len(direct),'component_only_hubs':len(component),
        'all_nonprocedure_literature_product_identity_categories_including_controls':len({r['material']['formula'] for r in lit.values() if r['record_type']!='procedure'}),
        'formal_full_main_reviews_si_unverified':base['summary']['formal_full_main_reviews_si_unverified']+1,
        'formal_full_main_only_review_pages':base['summary']['formal_full_main_only_review_pages']+6,
        'verified_exact_structure_recipe_pairs':elig['exact_structure_recipe']})
    inv['inventory_version']=datetime.now(timezone.utc).date().isoformat()+'-heath-'+('actual-local' if args.actual else 'prospective')+'-snapshot'
    inv['scope']='Inventory '+('reconciled to locally integrated canonical records' if args.actual else 'proposal over the existing 168-record baseline plus four independently audited Heath drafts, with an explicitly assumed parent-authorized metadata promotion')+'. Incoming-folder counts remain separate; local generated/proposed routes do not establish remote publication or independent experiment counts.'
    inv['count_definitions'].update({
        'contextual_control':f'The {len(controls)} existing Nakonechnyi controls are separate from {len(routes)} synthesis-route variants and {len(observations)} contextual observations.',
        'contextual_observation':'Characterization or incomplete growth-series context without a reconstructed complete synthesis: Littau AKS41 and Heath unpatterned Ge growth. Neither creates an extra synthesis route.',
        'recipe_family':f'{s["literature_recipe_family_ids"]} canonical literature grouping IDs: {s["primary_synthesis_recipe_family_ids"]} contain primary synthesis routes, one is ZnO post-treatment and two are contextual observation families. They are not unique physical recipes.',
        'material_system':f'{len(direct)} direct product-system labels retain architecture and unresolved stoichiometry. Ge/Si means substrate-supported Ge islands; SiO2 is a template mask, not a Ge oxide shell. The {len(hubs)} hubs include {len(component)} component-only cross-links, not extra standalone syntheses.',
        'shared_wafer':'The two Heath template variants were prepared on the same wafer in one reported exposure. Individual wells and variant records are not independent synthesis runs.',
    })
    inv['material_system_lists']['direct_synthesis_targets']=direct
    inv['material_system_lists']['component_only_public_hubs']=component
    inv['material_system_lists']['contextual_observation_product_labels']=sorted({r['material']['formula'] for r in observations.values()})
    inv['training_eligibility']=elig
    heath=src['heath1996'];hr=promoted
    p={'source_group':'heath1996','doi':heath['doi'],'url':heath['url'],'title':heath['title'],'year':1996,
        'has_local_corpus_group':heath['doi'].lower() in local_dois,
        'review_status':'full_supplied_main_review_si_unverified',
        'review_scope':'Six supplied main pages read and visually inspected; independent source and bounded four-record scientific audits passed. Matching SI is not located or verified. Two template populations share one wafer/exposure. Canonical-to-reader audit and publication remain separate gates.',
        'documents':[{'role':'main','page_count':6,'all_text_read':True,'all_visually_reviewed':True}],
        'evidence_locator':'data/paper-reviews/heath1996.json','paper_review_url':'paper-review.html?id=heath1996','si_status':'not_located_or_verified',
        'canonical_record_count':len(hr),'synthesis_route_variant_count':len(set(hr)&set(routes)),
        'contextual_control_count':0,'contextual_observation_count':len(set(hr)&set(observations)),
        'procedure_count':len(set(hr)&set(procedures)),'benchmark_row_count':0,
        'measurement_entry_count':sum(len(r['measurements']) for r in hr.values()),
        'record_type_counts':dict(sorted(Counter(r['record_type'] for r in hr.values()).items())),
        'canonical_recipe_family_ids':sorted({r['lineage']['recipe_family'] for r in hr.values()}),
        'direct_route_material_systems':sorted({routes[rid]['material']['formula'] for rid in hr if rid in routes}),
        'record_ids':sorted(hr),'record_urls':{rid:'records/'+rid+'.html' for rid in sorted(hr)},
        'notes':['The 100 and 150 nm wells are two templates on the same substrate, not independent runs.','The unpatterned temperature/time series is contextual observation, not an additional complete recipe.','Raman and near-IR peaks are prose-only; AFM bounds, inferred pseudo-time and Figure 2 identity conflict remain explicit.']}
    inv['per_paper']=sorted([*copy.deepcopy(base['per_paper']),p],key=lambda p:p['source_group'])
    old_materials={m['material_system']:m for m in base['per_material']};materials=[]
    for formula in sorted(old_materials.keys()|hubs.keys()):
        row=copy.deepcopy(old_materials.get(formula,{'material_system':formula,'notes':[]}));h=hubs.get(formula)
        rr={rid:r for rid,r in records.items() if r['material']['formula']==formula}
        route_ids=sorted(rr.keys()&routes.keys());hids=set(h['record_ids']) if h else set();cids=sorted(hids-set(route_ids))
        sources=sorted({records[rid]['lineage']['source_group'] for rid in rr.keys()|hids})
        row.update({'direct_synthesis_route_variant_count':len(route_ids),'direct_route_record_ids':route_ids,
            'contextual_control_count':len(rr.keys()&controls.keys()),'contextual_control_record_ids':sorted(rr.keys()&controls.keys()),
            'contextual_observation_count':len(rr.keys()&observations.keys()),'contextual_observation_record_ids':sorted(rr.keys()&observations.keys()),
            'procedure_count':len(rr.keys()&procedures.keys()),'benchmark_row_count':len(rr.keys()&bench.keys()),
            'public_hub_exists':bool(h),'public_hub_component_only':h['component_only'] if h else None,
            'public_hub_route_contributions':len(hids),'component_route_contribution_count':len(cids),'component_route_record_ids':cids,
            'primary_reviewed_source_count':len({r['lineage']['source_group'] for rid,r in rr.items() if rid in lit and rid not in procedures}),
            'material_hub_id':h['id'] if h else None,'material_hub_url':h['url'] if h else None,
            'source_groups':sources,'source_links':[{'source_group':g,'doi':src[g]['doi'],'url':src[g]['url'],'title':src[g]['title']} for g in sources],
            'direct_route_recipe_family_ids':sorted({routes[rid]['lineage']['recipe_family'] for rid in route_ids})})
        if formula=='Ge/Si':row['notes']=['Two template variants share one substrate and exposure; no independent-run count is inferred.','Substrate-supported Ge islands on Si(100); SiO2 defines the growth wells and is not a nanocrystal shell.','Shared characterization and incomplete unpatterned growth context remain separate from the two routes.']
        if formula=='Ge':row['notes']=['Component-only links to the same two substrate-supported Ge/Si variants; no separate colloidal or free-standing Ge synthesis is established.']
        if formula=='Si':
            # Retain the original Littau statement as explicitly source-scoped.
            row['notes']=['Littau1993: '+note for note in old_materials['Si']['notes']]+['Heath1996 adds two Ge/Si routes in which Si is the substrate. These do not become isolated Si syntheses or intrinsic Si property labels. The five component links refer to five existing route IDs across two sources.']
        materials.append(row)
    inv['per_material']=materials
    evidence_paths=[SITE/'data/corpus/library-source.json',SITE/'dist/data/materials-index.json',SITE/'dist/data/library-index.json',SITE/'dist/data/dataset-manifest.json',SITE/'dist/data/validation-report.json',REVIEW/'canonical-records-audit.json',REVIEW/'source-audit.json',REVIEW/'public-review-proposal/heath1996.json']
    canonical_hashes={rid:sha(p) for rid,p in canonical_files.items() if rid in records}
    prospective_digest=digest({rid:digest(r) for rid,r in sorted(records.items())})
    inv['provenance']={**base['provenance'],'canonical_record_files':len(records),
        'canonical_tree_sha256':prospective_digest,'canonical_tree_hash_rule':'SHA256 of sorted record-ID to normalized record-digest JSON; '+('actual canonical records' if args.actual else '168 actual records plus four in-memory promoted draft copies')+'.',
        'baseline_inventory_sha256':sha(baseline_path),'draft_audit_sha256':sha(REVIEW/'canonical-records-audit.json'),
        'inventory_mode':'actual_local' if args.actual else 'prospective_overlay',
        'promotion_assumption':'Parent-authorized source_reviewed for four audited records; only two variants request precursor_selection and partial_protocol. No file promotion is performed here.',
        'publication_verification':'Not assessed; final publication remains outside this inventory task.',
        'generated_dataset_version_observed':read(SITE/'dist/data/dataset-manifest.json')['dataset_version'],
        'source_input_sha256':{str(p.relative_to(SITE)) if p.is_relative_to(SITE) else 'private/'+p.name:sha(p) for p in evidence_paths}}
    checks=[]
    def check(label,value):checks.append({'check':label,'passed':bool(value)})
    check('Five categories partition canonical records',len(records)==sum(map(len,[routes,controls,procedures,observations,bench])) and set(records)==routes.keys()|controls.keys()|procedures.keys()|observations.keys()|bench.keys())
    check('Derived expected totals',tuple(map(len,[records,routes,controls,procedures,observations,bench,hubs,direct,component]))==(172,37,9,24,2,100,17,12,5))
    check('No draft counted twice',len(set(records))==172 and len(set(drafts)&set(records))==4)
    check('Two Heath routes only',set(proposed_routes)==set(promoted)&set(routes))
    check('Twelve source/evaluation groups',len(source_groups)==len(set(groups.values()))==12)
    check('SI scopes remain separate',s['formal_full_main_and_matched_si_reviews']==5 and s['formal_full_review_pages']==74 and s['formal_full_main_reviews_si_unverified']==2 and s['formal_full_main_only_review_pages']==13)
    check('Legacy corpus unchanged',s['local_document_files_indexed']==corpus['summary']['sourceDocumentCount']==7373 and s['local_paper_groups_indexed']==len(local_dois)==4176 and s['unique_document_content_hashes']==6857)
    check('Previously reviewed paper notes preserved',all(next(p for p in inv['per_paper'] if p['source_group']==old['source_group'])==old for old in base['per_paper']))
    check('Other material notes preserved',all(next(m for m in materials if m['material_system']==old['material_system'])['notes']==old['notes'] for old in base['per_material'] if old['material_system']!='Si'))
    check('Si remains component-only with five shared IDs/two sources',hubs['Si']['component_only'] and len(set(hubs['Si']['record_ids']))==5 and next(m for m in materials if m['material_system']=='Si')['source_groups']==['heath1996','littau1993'])
    check('Per-paper category sums reconcile',sum(p['canonical_record_count'] for p in inv['per_paper'])==172 and sum(p['synthesis_route_variant_count'] for p in inv['per_paper'])==37 and sum(p['procedure_count'] for p in inv['per_paper'])==24 and sum(p.get('contextual_observation_count',0) for p in inv['per_paper'])==2)
    check('Heath retains 23 measurement entries',p['measurement_entry_count']==23)
    check('No exact structure or success labels',elig['exact_structure_recipe']==elig['success_prediction']==0)
    check('Unknown full-corpus totals retained',all(s[k] is None for k in ['independent_experiment_count','full_corpus_recipe_count','full_corpus_distinct_synthesized_material_count']))
    # Compare whenever a matching actual rebuild exists, without treating an old
    # 168-record build as proof that the prospective overlay failed.
    manifest=read(SITE/'dist/data/dataset-manifest.json');actual_compare={'status':'pending_rebuild','observed_records':manifest['record_count']}
    if manifest['record_count']==len(records):
        v=read(SITE/'dist/data/validation-report.json');idx=read(SITE/'dist/data/materials-index.json');rev=read(SITE/'dist/data/paper-review-index.json')
        actual_compare={'status':'compared','observed_records':manifest['record_count'],'dataset_version':manifest['dataset_version']}
        check('Actual rebuild eligibility matches overlay',v['eligible_by_task']==elig)
        check('Actual rebuilt hub identities match overlay',{(m['formula'],m['component_only']) for m in idx['materials']}=={(f,h['component_only']) for f,h in hubs.items()})
        check('Actual rebuilt records match overlay IDs',{r['record_id'] for r in manifest['records']}==set(records))
        check('Actual rebuilt main-only scope covers Heath and Littau',{r['id'] for r in rev['papers'] if r['review_scope']=='supplied_main_only_si_unverified'}=={'heath1996','littau1993'})
        for formula in ['Ge','Ge/Si','Si']:
            real=read(SITE/'dist/data/materials'/f'{hubs[formula]["id"]}.json')
            check(formula+': actual route-ID set matches simulation',set(real['record_ids'])==set(hubs[formula]['record_ids']) and set(real['direct_record_ids'])==set(hubs[formula]['direct_record_ids']))
    if args.actual:check('Actual mode has a rebuilt matching manifest',actual_compare['status']=='compared')
    errors=[c['check'] for c in checks if not c['passed']]
    validation={'status':'failed' if errors else 'passed','mode':'actual_local' if args.actual else 'prospective_overlay','created_utc':datetime.now(timezone.utc).isoformat(),
        'checks':checks,'errors':errors,'summary':s,'training_eligibility':elig,'actual_rebuild_comparison':actual_compare,
        'draft_sha256':draft_hashes,'baseline_canonical_file_sha256':canonical_hashes,'source_groups':source_groups,
        'site_files_written':False,'published':False}
    write('validation.json',validation);assert not errors,errors
    write('inventory-summary.json',inv)
    (OUT/'REPORT.md').write_text(f'''# Heath1996 inventory overlay

Mode: **{validation['mode']}**. Four independently audited drafts extend the saved 168-record inventory. Promotion is simulated only in memory unless `--actual` is used: four source-reviewed records, with precursor-selection and partial-protocol tasks requested only by the two template variants.

Derived totals: **172 records = 37 routes + 9 controls + 24 procedures + 2 contextual observations + 100 benchmark rows**. There are **17 hubs = 12 direct systems + 5 component-only hubs**, and **12 source/evaluation groups**. The two Heath templates share a wafer/exposure; no independent-run count is inferred.

Ge/Si is the new direct system; Ge is a component-only page. Existing Si remains component-only and links to three Littau and two Heath routes. Si substrate evidence is not bare-Si synthesis. The SiO2 mask is not a Ge shell or an extra product hub.

Formal scope: **five matched-main/SI reviews, 74 pages; two main-only/SI-unverified reviews, 13 pages**. The separate legacy review scopes are retained. The legacy collection remains **7,373 files / 4,176 local groups / 6,857 content hashes**; incoming-folder counts are excluded. There are {s['local_groups_without_canonical_records']} local groups without canonical records.

Eligibility: `{elig}`. All four Heath draft hashes match the passed 13-check independent scientific audit. The source contains 23 scoped measurement entries. Existing manual per-paper notes remain exact; existing Si notes are retained with an explicit Littau prefix before the added Heath-substrate caveat.

**{len(checks)} reconciliation checks passed.** Actual rebuild comparison: **{actual_compare['status']}**, observed manifest records {manifest['record_count']}. Root must inspect/copy the proposal and rebuild the actual inventory before publication. Run this generator with `--actual` after the canonical/review/atlas build to bind provenance to integrated files. No Site, source or queue file was changed.
''',encoding='utf-8')
    print(json.dumps({'status':'passed','checks':len(checks),'mode':validation['mode'],'records':len(records),'routes':len(routes),'procedures':len(procedures),'observations':len(observations),'hubs':len(hubs),'direct':len(direct),'components':len(component),'source_groups':len(source_groups),'actual_comparison':actual_compare['status']}))

if __name__=='__main__':main()
