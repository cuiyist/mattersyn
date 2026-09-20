from pathlib import Path
B=Path(__file__).resolve().parent
t=(B/'ja0496423/build_inventory_actual.py').read_text(encoding='utf8')
t=t.replace("O=B/'inventory-proposal'","O=B/'integration-proposal'")
t=t.replace("read(O/'base-inventory-summary.json')","read(O/'base-site-inputs/data/inventory-summary.json')")
t=t.replace("(O/'base-inventory-summary.json').read_bytes()","(O/'base-site-inputs/data/inventory-summary.json').read_bytes()")
t=t.replace('-gu-actual-local-snapshot','-three-source-actual-local-snapshot').replace('current Gu audit inputs','current batch audit inputs')
start=t.index("g='gu2004';");end=t.index("old={m['material_system']",start)
t=t[:start]+'''newgroups=['nagasaki2004','ribeiro2004','norberg2004']
newrows=[]
for g in newgroups:
 rr={k:r for k,r in records.items()if r['lineage']['source_group']==g};src=sources[g];review=read(S/'data/paper-reviews'/(g+'.json'))
 row={'source_group':g,'doi':src['doi'],'url':src['url'],'title':src['title'],'year':src['year'],'has_local_corpus_group':src['doi'].lower()in localdois,'review_status':'full_supplied_main_and_matched_si_review' if review['review_scope']=='supplied_main_and_matched_si' else 'full_supplied_main_only_si_unverified','review_scope':review['independent_audit'],'documents':[{'role':d['role'],'page_count':d['page_count'],'all_text_read':all(p['text_read']for p in d['pages']),'all_visually_reviewed':all(p['visual_review']for p in d['pages'])}for d in review['documents']],'evidence_locator':'data/paper-reviews/'+g+'.json','paper_review_url':'paper-review.html?id='+g,'si_status':'matched_and_reviewed' if review['review_scope']=='supplied_main_and_matched_si' else 'unverified','canonical_record_count':len(rr),'synthesis_route_variant_count':len(rr.keys()&routes.keys()),'contextual_control_count':len(rr.keys()&controls.keys()),'contextual_observation_count':len(rr.keys()&observations.keys()),'procedure_count':len(rr.keys()&procedures.keys()),'benchmark_row_count':0,'measurement_entry_count':sum(len(r['measurements'])for r in rr.values()),'record_type_counts':dict(sorted(Counter(r['record_type']for r in rr.values()).items())),'canonical_recipe_family_ids':sorted({r['lineage']['recipe_family']for r in rr.values()}),'direct_route_material_systems':sorted({routes[k]['material']['formula']for k in rr.keys()&routes.keys()}),'record_ids':sorted(rr),'record_urls':{k:'records/'+k+'.html'for k in sorted(rr)},'notes':[review['training_note'],'Source-specific original figures and independent reference illustrations retain their distinct roles. Records, protocols, characterization contexts and independent physical experiments are not interchangeable counts.']}
 newrows.append(row)
inv['per_paper']=sorted([p for p in inv['per_paper']if p['source_group']not in newgroups]+newrows,key=lambda p:p['source_group'])
''' + t[end:]
t=t.replace("expected_new=len(list((B/'canonical-drafts').glob('*.json')))","expected_new=46")
t=t.replace("'all_gu_records':len(row['record_ids'])==expected_new","'all_three_sources':sum(len(row['record_ids'])for row in newrows)==expected_new")
t=t.replace("'one_source_group':len({groups[k]for k in row['record_ids']})==1","'three_separate_source_groups':all(len({groups[k]for k in row['record_ids']})==1 for row in newrows) and len({groups[k]for row in newrows for k in row['record_ids']})==3")
t=t.replace("'source_group':g,'measurement_entries':row['measurement_entry_count']","'source_groups':newgroups,'measurement_entries':sum(row['measurement_entry_count']for row in newrows)")
(B/'build_inventory_actual.py').write_text(t,encoding='utf8')
t=(B/'ja0496423/build_and_check.py').read_text(encoding='utf8').replace("B/'inventory-proposal/inventory-summary.json'","B/'integration-proposal/inventory-summary.json'")
t=t.replace("['gu2004-protocol.mjs','protocol-visuals.mjs','chemical-viewer.mjs','crystal-viewer.mjs']","['nagasaki2004-protocol.mjs','ribeiro2004-protocol.mjs','norberg2004-protocol.mjs','protocol-visuals.mjs','chemical-viewer.mjs','crystal-viewer.mjs','material-guide.mjs']")
(B/'build_and_check.py').write_text(t,encoding='utf8')
print('Prepared batch inventory/build runner.')
