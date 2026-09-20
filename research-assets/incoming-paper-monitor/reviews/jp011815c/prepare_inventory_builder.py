from pathlib import Path
B=Path(__file__).resolve().parent
t=(B.parent/'ja9805425/build_inventory_actual.py').read_text(encoding='utf-8')
t=t.replace('peng-actual-local-snapshot','shah-actual-local-snapshot').replace("g='peng1998'","g='shah2001'").replace('paper-reviews/peng1998.json','paper-reviews/shah2001.json').replace('paper-review.html?id=peng1998','paper-review.html?id=shah2001')
t=t.replace("'review_status':'full_supplied_main_and_matched_si_review'","'review_status':'full_supplied_main_review_si_unverified'")
t=t.replace("'review_scope':'All two main and four matched SI PDF pages text and visually reviewed with independent audits; deployment tracked separately.'","'review_scope':'All eight supplied main pages text and visually reviewed with independent source, canonical, reader, chemical and apparatus audits; SI not located or verified; deployment tracked separately.'")
t=t.replace("'documents':[{'role':'main','page_count':2,'all_text_read':True,'all_visually_reviewed':True},{'role':'supporting_information','page_count':4,'all_text_read':True,'all_visually_reviewed':True}]","'documents':[{'role':'main','page_count':8,'all_text_read':True,'all_visually_reviewed':True}]")
t=t.replace("'si_status':'matched_and_reviewed'","'si_status':'not_located_or_verified'")
start=t.index("'notes':['Two hot-injection routes")
end=t.index("}\ninv['per_paper']",start)
t=t[:start]+"'notes':['Nine silver experiments A–I and two separate iridium/platinum conditions provide eleven source-linked synthesis variants.','Four common procedures and four contextual observations remain separate from experimental routes.','Twenty-one original source assets preserve eleven figures, Table 1, equations, definitions and procedural notes.','The platinum precursor remains as printed with unresolved identity. Figure 7 cohorts are not silently joined to same-size Table 1 rows. No measured atomic coordinates or exact-structure training labels supplied.']"+t[end:]
t=t.replace("'all_peng_records'","'all_shah_records'").replace("'two_peng_routes':row['synthesis_route_variant_count']==2","'eleven_shah_routes':row['synthesis_route_variant_count']==11")
t=t.replace("'no_new_size_labels':elig['size_conditioned_recipe']==6","'nine_explicit_ag_size_labels':elig['size_conditioned_recipe']==15")
(B/'build_inventory_actual.py').write_text(t,encoding='utf-8')
print('Prepared source-specific inventory builder; counts will derive from integrated records.')
