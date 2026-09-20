from pathlib import Path
import json
O=Path(__file__).resolve().parent;B=O.parent;OLD=B.parent/'ja036811v/reader-assets'
s=(OLD/'check_reader_runtime.mjs').read_text(encoding='utf8').replace('schwartz2003','sashchiuk2004').replace('schwartz-2003','sashchiuk-2004').replace('Schwartz2003','Sashchiuk2004')
s=s.replace('All 184 source items executed','All 147 source items executed').replace('cards.length===184&&items.length===184','cards.length===147&&items.length===147')
s=s.replace("'Eleven main and six SI original figure cards',figureCards.length===17","'All five main original figure cards',figureCards.length===5")
s=s.replace('All 38 original assets accessible','All 13 original assets accessible').replace('allAssets.length===38&&filenames.length===38','allAssets.length===13&&filenames.length===13')
a=s.index("check('Fourteen main and four SI pages displayed'");z=s.index('const input=',a)
s=s[:a]+"""check('All seven supplied main pages displayed',document.getElementById('review-summary').textContent.includes('7 pages')&&ledger.documents.length===1&&ledger.documents[0].page_count===7);
check('SI remains not located',ledger.supporting_information.status==='not_located'&&ledger.review_scope==='supplied_main_only_si_unverified');
check('Caption and method ratio conflict visible',cardMap.get('ratio-conflicts')?.textContent.includes('0.5:1.2:50')&&cardMap.get('ratio-conflicts')?.textContent.includes('0.5:1:50'));
check('Summary stock conflict visible',cardMap.get('low-stock')?.textContent.includes('0.25:0.6:0.5'));
check('Individual image not15minendpoint',cardMap.get('individual-hrtem')?.textContent.includes('15 min route endpoint'));
check('Wire SAED actually linked',cardMap.get('wire-saed')?.textContent.includes('020'));
check('Three electrical specimen dimensions remain paired',cardMap.get('electrical-specimens')?.textContent.includes('110×700')&&cardMap.get('electrical-specimens')?.textContent.includes('60×1000')&&cardMap.get('electrical-specimens')?.textContent.includes('150×1200'));
check('Unsquared dipole expression remains explicit',cardMap.get('interaction-energy')?.textContent.includes('single μ'));
check('Negative entropy argument caveat visible',cardMap.get('entropy')?.textContent.includes('Negative ΔS alone'));
"""+s[z:]
s=s.replace('All 95 operations','All 47 operations').replace('operationCount===95','operationCount===47').replace('All 95 actual mounted','All 47 actual mounted').replace('mountedOperations===95','mountedOperations===47')
s=s.replace('All 79 actual condition','All 85 actual condition').replace('mountedQuantities===79','mountedQuantities===85')
a=s.index('// Exercise actual mountEvidence');z=s.index('const failures=checks.filter',a);s=s[:a]+(O/'check_contextual_evidence.fragment.js').read_text(encoding='utf8')+'\n'+s[z:]
s=s.replace("'material-guide.mjs'","'material-guide.mjs','crystal-viewer.mjs','assets/crystal-references/registry.json'") if False else s
s=s.replace("'data/paper-reviews/sashchiuk2004.json','assets/chemical-registry/bindings.json'","'data/paper-reviews/sashchiuk2004.json','crystal-viewer.mjs','assets/crystal-references/registry.json','assets/chemical-registry/bindings.json'")
(O/'check_reader_runtime.mjs').write_text(s,encoding='utf8')
s=(OLD/'check_integrated_presentation.py').read_text(encoding='utf8').replace('schwartz2003','sashchiuk2004').replace('schwartz-2003','sashchiuk-2004').replace('Schwartz 2003','Sashchiuk 2004')
s=s.replace("reader_science['canonical_record_hashes']","reader_science.get('canonical_record_hashes',reader_science.get('record_hashes'))")
s=s.replace("'/sources/0/si_status'}","'/sources/0/si_status','/collection'}")
s=s.replace("ck(rid+' only review metadata promoted'","ck(rid+' reviewed literature collection',r.get('collection')=='reviewed_literature');ck(rid+' only review metadata promoted'")
s=s.replace("'30 records / 95 operations / 277 measurements',len(records)==30 and sum(len(r['operations']) for r in records.values())==95 and sum(len(r['measurements']) for r in records.values())==277","'15 records / 47 operations / 137 measurements',len(records)==15 and sum(len(r['operations']) for r in records.values())==47 and sum(len(r['measurements']) for r in records.values())==137")
s=s.replace('3 literature protocols / 20 procedures / 7 observations','4 literature protocols / 5 procedures / 6 observations').replace('Counter(literature_protocol=3,procedure=20,observation=7)','Counter(literature_protocol=4,procedure=5,observation=6)')
structprops=set(json.loads((B/'structural-property-additions.json').read_text(encoding='utf8')))
a=s.index(' expected_structure=');z=s.index('\n def structural',a);s=s[:a]+' expected_structure='+repr(structprops)+s[z:]
a=s.index(' expected_optical=');z=s.index('\n for prop in expected_optical',a);s=s[:a]+" expected_optical={'reported_exciton_wavelength_window','reported_exciton_energy_window','growth_series_absorption_redshift','assembly_absorption_blueshift_from_bulk','reported_specific_resistivity','reported_conductivity','current_voltage_behavior','author_estimated_internal_field','author_estimated_permanent_dipole','author_estimated_interparticle_interaction_energy'}"+s[z:]
s=s.replace('184 reader items intact','147 reader items intact').replace('len(items)==184','len(items)==147').replace('261 source units retained','184 source units retained').replace("len(source['units'])==261","len(source['units'])==184")
s=s.replace("'record_formulation_labels']","'record_formulation_labels','route_evidence_contexts','material_original_asset_ids','material_asset_scope_note']")
s=s.replace('38 original assets and category counts','13 original assets and category counts').replace('len(assets)==38','len(assets)==13').replace('==[17,2,10,8]','==[5,0,2,6]')
a=s.index(" ck('Figure 5 separately scoped microscopy'");z=s.index(" ck('Obsolete private pending-audit gap removed'",a)
s=s[:a]+""" ck('Figure1 distinct individual and sphere contexts',assets['figure-1']['sample_links']==['sashchiuk-2004-individual-structure','sashchiuk-2004-sphere-structure'])
 ck('Figure2 only unresolved wire observation',assets['figure-2']['sample_links']==['sashchiuk-2004-wire-structure'])
 ck('Figure4 separate optical aliquots',assets['figure-4']['sample_links']==['sashchiuk-2004-absorption'])
 ck('Figure5 device and three electrical wires',assets['figure-5']['sample_links']==['sashchiuk-2004-device-fabrication','sashchiuk-2004-electrical'])
 ck('Only supplied main reviewed',reader['supporting_information']['status']=='not_located' and [(d['role'],d['page_count']) for d in reader['documents']]==[('main',7)])
"""+s[z:]
s=s.replace("runtime['reader_items']==184","runtime['reader_items']==147").replace("runtime['unique_original_assets']==38","runtime['unique_original_assets']==13").replace("runtime['operation_count']==95","runtime['operation_count']==47")
s=s.replace("  for n,m in enumerate(r['measurements']):", "  for option in r.get('condition_options',[]):\n   groups=tree.find('div','condition-options');optioncards=groups[0].find('article') if groups else []\n   matched=[x for x in optioncards if option['label'] in x.text]\n   ck(rid+'/'+option['id']+' alternative grade label visible',len(matched)==1)\n   for key,q in option['parameters'].items():ck(rid+'/'+option['id']+'/'+key+' exact alternative quantity visible',bool(matched) and plain(fmt(q)) in matched[0].text)\n  for n,m in enumerate(r['measurements']):")
s=s.replace('38 originals, material hubs, 95 operation scenes','13 originals, material hub, 47 operation scenes')
s=s.replace("'records':30,'operations':95,'measurements':277,'reader_items':184,'source_units':261,'original_assets':38","'records':15,'operations':47,'measurements':137,'reader_items':147,'source_units':184,'original_assets':13")
(O/'check_integrated_presentation.py').write_text(s,encoding='utf8')
(O/'expected-structural-properties.json').write_text(json.dumps(sorted(structprops),indent=2)+'\n',encoding='utf8')
print('Prepared actual-build checks for15records/47operations/137measurements/147items/184sourceunits/13assets')
