"""Prepare private read-only actual-build audits; execute only after root builds."""
from pathlib import Path
import json,re
O=Path(__file__).resolve().parent;B=O.parent;OLD=B.parent/'ja035980c/reader-assets'
r=json.loads((B/'public-review-proposal/schwartz2003.json').read_text(encoding='utf8'));records={p.stem:json.loads(p.read_text(encoding='utf8')) for p in (B/'canonical-drafts').glob('*.json')}
nitems=r['counts']['reader_items'];nunits=r['counts']['source_audit_units'];nops=sum(len(x['operations']) for x in records.values());nmeas=sum(len(x['measurements']) for x in records.values());nparams=sum(len(o['parameters']) for x in records.values() for o in x['operations'])
s=(OLD/'check_reader_runtime.mjs').read_text(encoding='utf8').replace('banerjee2003','schwartz2003').replace('Banerjee2003','Schwartz2003')
s=s.replace('All 143 source items executed',f'All {nitems} source items executed').replace('cards.length===143&&items.length===143',f'cards.length==={nitems}&&items.length==={nitems}')
s=s.replace("'Eight main and one SI original figure cards',figureCards.length===9","'Eleven main and six SI original figure cards',figureCards.length===17")
s=s.replace('All 15 original assets accessible','All 38 original assets accessible').replace('allAssets.length===15&&filenames.length===15','allAssets.length===38&&filenames.length===38')
a=s.index("check('Nine main and one SI page displayed'");z=s.index('const input=',a)
s=s[:a]+"""check('Fourteen main and four SI pages displayed',document.getElementById('review-summary').textContent.includes('18 pages')&&ledger.documents.length===2&&ledger.documents.find(d=>d.role==='main')?.page_count===14&&ledger.documents.find(d=>d.role==='si')?.page_count===4);
check('SI matched identity explicit',ledger.supporting_information.status==='matched_local_si'&&cardMap.get('si-identity')?.textContent.includes('S1 through S6'));
check('Surface cobalt control remains separate',cardMap.get('surface-control')?.textContent.includes('deliberately')||cardMap.get('surface-control')?.textContent.includes('intentionally'));
check('Nominal and retained dopants distinguished',cardMap.get('dopant-substitution')?.textContent.includes('measured dopant'));
check('Co monitoring conflict explicit',cardMap.get('field-co')?.textContent.includes('15 600')&&cardMap.get('field-co')?.textContent.includes('15 700'));
check('Ni monitoring conflict explicit',cardMap.get('field-ni')?.textContent.includes('15 400')&&cardMap.get('field-ni')?.textContent.includes('15 165'));
check('Curie result remains lower bound',cardMap.get('curie-bound')?.textContent.includes('T_C > 350'));
check('Table2 literature comparison distinct',cardMap.get('table2-comparators')?.textContent.includes('Blank cells'));
"""+s[z:]
s=s.replace("input.value='TDPA'","input.value='TOPO'")
s=s.replace('All 39 operations',f'All {nops} operations').replace('operationCount===39',f'operationCount==={nops}')
s=s.replace('All 39 actual mounted',f'All {nops} actual mounted').replace('mountedOperations===39',f'mountedOperations==={nops}')
s=s.replace('All 53 actual condition',f'All {nparams} actual condition').replace('mountedQuantities===53',f'mountedQuantities==={nparams}')
s=s.replace('const failures=checks.filter(c=>!c.passed);',(O/'check_contextual_evidence.fragment.js').read_text(encoding='utf8')+'\nconst failures=checks.filter(c=>!c.passed);')
s=s.replace("'paper-review.mjs','source-evidence.mjs'","'paper-review.mjs','source-evidence.mjs','material-guide.mjs'")
(O/'check_reader_runtime.mjs').write_text(s,encoding='utf8')
s=(OLD/'check_integrated_presentation.py').read_text(encoding='utf8').replace('banerjee2003','schwartz2003').replace('banerjee-2003','schwartz-2003').replace('Banerjee 2003','Schwartz 2003')
s=s.replace("reader_science['record_hashes']","reader_science['canonical_record_hashes']")
s=s.replace("ck('14 records / 39 operations / 97 measurements',len(records)==14 and sum(len(r['operations']) for r in records.values())==39 and sum(len(r['measurements']) for r in records.values())==97)",f"ck('30 records / {nops} operations / {nmeas} measurements',len(records)==30 and sum(len(r['operations']) for r in records.values())=={nops} and sum(len(r['measurements']) for r in records.values())=={nmeas})")
s=s.replace('1 literature protocol / 9 procedures / 4 observations','3 literature protocols / 20 procedures / 7 observations').replace('Counter(literature_protocol=1,procedure=9,observation=4)','Counter(literature_protocol=3,procedure=20,observation=7)')
structprops=set(json.loads((B/'structural-property-additions.json').read_text(encoding='utf8')))
a=s.index(' expected_structure=');z=s.index('\n def structural',a);s=s[:a]+' expected_structure='+repr(structprops)+s[z:]
a=s.index(' expected_optical=');z=s.index('\n for prop in expected_optical',a);s=s[:a]+" expected_optical={'mcd_c0_d0','mcd_b0_d0','mcd_monitor_energy','table1_mcd_transition_energy','average_zeeman_redshift_per_tesla','curie_temperature_lower_bound','fitted_n0_beta','estimated_n0_beta','room_temperature_coercivity','trap_luminescence_quenching_fraction'}"+s[z:]
s=s.replace("'143 reader items intact'",f"'{nitems} reader items intact'").replace('len(items)==143',f'len(items)=={nitems}')
s=s.replace("'176 source units retained'",f"'{nunits} source units retained'").replace("len(source['units'])==176",f"len(source['units'])=={nunits}")
s=s.replace('15 original assets and category counts','38 original assets and category counts').replace('len(assets)==15','len(assets)==38').replace('==[9,0,0,6]','==[17,2,10,8]')
a=s.index(" ck('Figure 1 precursor-only association'");z=s.index(" ck('Obsolete private pending-audit gap removed'",a)
s=s[:a]+""" ck('Figure 5 separately scoped microscopy',assets['figure-5']['sample_links']==['schwartz-2003-microscopy'])
 ck('Figure 6 optical cohorts only',assets['figure-6']['sample_links']==['schwartz-2003-optical-absorption','schwartz-2003-mcd'])
 ck('SI surface-control association',assets['si-figure-2']['sample_links']==['schwartz-2003-surface-cleaning-control'])
 ck('SI exactly matched and reviewed',reader['supporting_information']['status']=='matched_local_si' and [(d['role'],d['page_count']) for d in reader['documents']]==[('main',14),('si',4)])
 ck('Ni excludes Co-only magnetometry','schwartz-2003-magnetometry' not in reader['material_evidence_records']['ZnO:Ni'])
 ck('Pure ZnO excludes Co-only magnetometry','schwartz-2003-magnetometry' not in reader['material_evidence_records']['ZnO'])
"""+s[z:]
s=s.replace("runtime['reader_items']==143",f"runtime['reader_items']=={nitems}").replace("runtime['unique_original_assets']==15","runtime['unique_original_assets']==38").replace("runtime['operation_count']==39",f"runtime['operation_count']=={nops}")
s=s.replace('15 originals, material hubs, 39 operation scenes',f'38 originals, material hubs, {nops} operation scenes')
s=s.replace("'records':14,'operations':39,'measurements':97,'reader_items':143,'source_units':176,'original_assets':15",f"'records':30,'operations':{nops},'measurements':{nmeas},'reader_items':{nitems},'source_units':{nunits},'original_assets':38")
(O/'check_integrated_presentation.py').write_text(s,encoding='utf8')
(O/'expected-structural-properties.json').write_text(json.dumps(sorted(structprops),indent=2)+'\n',encoding='utf8')
print(json.dumps({'items':nitems,'source_units':nunits,'operations':nops,'measurements':nmeas,'condition_quantities':nparams,'structural_properties':sorted(structprops)}))
