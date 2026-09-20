"""Prepare private reusable build helpers; no Site import or publication."""
from pathlib import Path
B=Path(__file__).resolve().parent
prior=B.parent/'cm970189m'
t=(prior/'build_inventory_actual.py').read_text(encoding='utf-8')
t=t.replace("+'-veinot-actual-local-snapshot'","+'-yao-actual-local-snapshot'").replace("g='veinot1997';","g='yao1998';")
start=t.index('row={');end=t.index("inv['per_paper']",start)
row='''review=read(S/'data/paper-reviews/yao1998.json')
row={'source_group':g,'doi':src['doi'],'url':src['url'],'title':src['title'],'year':src['year'],'has_local_corpus_group':src['doi'].lower()in localdois,'review_status':'full_supplied_main_review_si_unverified','review_scope':'All seven supplied main pages text and visually reviewed with independent audits. Matching SI not located or verified; deployment tracked separately.','documents':[{'role':'main','page_count':7,'all_text_read':True,'all_visually_reviewed':True}],'evidence_locator':'data/paper-reviews/yao1998.json','paper_review_url':'paper-review.html?id=yao1998','si_status':'not_located_or_verified','canonical_record_count':len(rr),'synthesis_route_variant_count':len(rr.keys()&routes.keys()),'contextual_control_count':len(rr.keys()&controls.keys()),'contextual_observation_count':len(rr.keys()&observations.keys()),'procedure_count':len(rr.keys()&procedures.keys()),'benchmark_row_count':0,'measurement_entry_count':sum(len(r['measurements'])for r in rr.values()),'record_type_counts':dict(sorted(Counter(r['record_type']for r in rr.values()).items())),'canonical_recipe_family_ids':sorted({r['lineage']['recipe_family']for r in rr.values()}),'direct_route_material_systems':sorted({routes[k]['material']['formula']for k in rr.keys()&routes.keys()}),'record_ids':sorted(rr),'record_urls':{k:'records/'+k+'.html'for k in sorted(rr)},'notes':['Two aqueous CdS/polymer routes retain the nominal NaCl and reaction-clock ambiguities.','Host conditioning and cadmium loading have stage-specific product identities; comparative electrolytes are incomplete qualitative observations, not additional full routes.','Host dimensions, regional nanocrystal sizes, dispersion-layer widths, XRD size estimates and author diffusion/potential models retain distinct measurement scopes.','Nine figures and three numbered equations are preserved. The supplied paper contains no original XRD plot, SAED image, Raman spectrum or measured atomic coordinates.']}
'''
t=t[:start]+row+t[end:]
start=t.index('checks={');end=t.index('assert all(checks.values())',start)
t=t[:start]+'''expected_new=len(list((B/'canonical-drafts').glob('*.json')))
checks={'record_id_inventory_exact':{k for p in inv['per_paper']for k in p['record_ids']}==set(records),'category_partition':len(routes)+len(controls)+len(procedures)+len(observations)+len(benchmark)==len(records),'all_yao_records':len(row['record_ids'])==expected_new,'two_yao_routes':row['synthesis_route_variant_count']==2,'unchanged_benchmark':len(benchmark)==100,'full_corpus_totals_unknown':ss['full_corpus_recipe_count']is None and ss['full_corpus_distinct_synthesized_material_count']is None,'one_source_group':len({groups[k]for k in row['record_ids']})==1,'no_new_size_labels':elig['size_conditioned_recipe']==6,'no_exact_structure':elig['exact_structure_recipe']==0,'no_success_labels':elig['success_prediction']==0,'no_new_optical_labels':elig['optical_outcome']==95,'old_records_preserved':len(records)-expected_new==base['summary']['canonical_records']}
'''+t[end:]
(B/'build_inventory_actual.py').write_text(t,encoding='utf-8')
t=(prior/'run_build.py').read_text(encoding='utf-8').replace("'veinot-protocol.mjs'","'yao-protocol.mjs'")
(B/'run_build.py').write_text(t,encoding='utf-8')
print('Prepared private inventory and build helpers; not executed.')
