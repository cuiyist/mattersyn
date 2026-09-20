"""Prepare read-only actual-build audits; do not execute before root integration."""
from pathlib import Path
import json
O=Path(__file__).resolve().parent;B=O.parent;OLD=B.parent/'jp0208743/reader-assets'
r=json.loads((B/'public-review-proposal/yi2002.json').read_text(encoding='utf8'))
records={p.stem:json.loads(p.read_text(encoding='utf8')) for p in (B/'canonical-drafts').glob('*.json')}
nitems=r['counts']['reader_items'];nunits=r['counts']['source_audit_units'];nops=sum(len(x['operations']) for x in records.values());nmeas=sum(len(x['measurements']) for x in records.values());nparams=sum(len(o['parameters']) for x in records.values() for o in x['operations'])
s=(OLD/'check_reader_runtime.mjs').read_text(encoding='utf8').replace('dantas2002','yi2002').replace('Dantas2002','Yi2002')
s=s.replace('All 101 source items executed',f'All {nitems} source items executed').replace('cards.length===101&&items.length===101',f'cards.length==={nitems}&&items.length==={nitems}')
s=s.replace("'Seven original figure cards',figureCards.length===7","'Ten original figure cards',figureCards.length===10")
s=s.replace('All 11 original assets accessible','All 16 original assets accessible').replace('allAssets.length===11&&filenames.length===11','allAssets.length===16&&filenames.length===16')
a=s.index("check('SI search limitation explicit'");z=s.index('const input=',a)
s=s[:a]+"""check('SI limitation explicit',cardMap.get('coverage')?.textContent.includes('SI'));
check('Mass and mole conflict explicit',cardMap.get('mass-amount-check')?.textContent.includes('209'));
check('Concentration-series source conflict explicit',cardMap.get('erbium-conflict')?.textContent.includes('6%'));
check('Power-band source label conflict explicit',cardMap.get('power-label-conflict')?.textContent.includes('520'));
check('Model remains source interpretation',cardMap.get('figure9-model')?.textContent.includes('model'));
"""+s[z:]
s=s.replace("input.value='AFM1'","input.value='Scherrer'")
s=s.replace("scene.svg.includes('explanatory')","/illustrative|explanatory/.test(scene.svg)")
s=s.replace('All 48 operations',f'All {nops} operations').replace('operationCount===48',f'operationCount==={nops}')
s=s.replace('All 48 actual mounted',f'All {nops} actual mounted').replace('mountedOperations===48',f'mountedOperations==={nops}')
s=s.replace('All 67 actual condition',f'All {nparams} actual condition').replace('mountedQuantities===67',f'mountedQuantities==={nparams}')
(O/'check_reader_runtime.mjs').write_text(s,encoding='utf8')
s=(OLD/'check_integrated_presentation.py').read_text(encoding='utf8').replace('dantas2002','yi2002').replace('dantas-2002','yi-2002').replace('Dantas 2002','Yi 2002')
s=s.replace("ck('16 records / 48 operations / 110 measurements',len(records)==16 and sum(len(r['operations']) for r in records.values())==48 and sum(len(r['measurements']) for r in records.values())==110)",f"ck('18 records / {nops} operations / {nmeas} measurements',len(records)==18 and sum(len(r['operations']) for r in records.values())=={nops} and sum(len(r['measurements']) for r in records.values())=={nmeas})")
s=s.replace('6 literature protocols / 8 procedures / 2 observations','6 literature protocols / 11 procedures / 1 observation').replace('Counter(literature_protocol=6,procedure=8,observation=2)','Counter(literature_protocol=6,procedure=11,observation=1)')
structprops={m['property'] for rid,x in records.items() for m in x['measurements'] if rid.rsplit('-',1)[-1] in ['xrd','tem'] or rid.endswith('particle-size')}
structprops.update(m['property'] for rid,x in records.items() if 'anneal-' in rid for m in x['measurements'] if m['id'] in ['bulk-like','crystallite-size','phase-reference','growth'])
a=s.index(' expected_structure=');z=s.index('\n def structural',a);s=s[:a]+' expected_structure='+repr(structprops)+s[z:]
s=s.replace(" ck('Electronic model threshold stays under Properties',not structural('source_strong_confinement_size_upper_bound'))", " expected_optical={'prose_power_law_exponent','figure_power_law_exponent','author_inferred_excitation_photon_count'}\n for prop in expected_optical:ck(prop+' stays under Properties',not structural(prop))")
s=s.replace("m['property']=='source_strong_confinement_size_upper_bound'", "m['property'] in expected_optical")
s=s.replace("'101 reader items intact'",f"'{nitems} reader items intact'").replace('len(items)==101',f'len(items)=={nitems}')
s=s.replace("'147 source units retained'",f"'{nunits} source units retained'").replace('len(source[\'units\'])==147',f"len(source['units'])=={nunits}")
s=s.replace('11 original assets and category counts','16 original assets and category counts').replace('len(assets)==11','len(assets)==16').replace('==[7,0,0,4]','==[10,0,0,6]')
a=s.index(" ck('Figure 3 pure model association'");z=s.index(" ck('Missing SI stays explicit'",a)
s=s[:a]+""" ck('Figure 1 explicit 800 C association',assets['figure-1']['sample_links']==['yi-2002-anneal-800','yi-2002-xrd'])
 ck('Figure 3 analyzer cohort association',assets['figure-3']['sample_links']==['yi-2002-particle-size'])
 ck('Figure 7 incomplete concentration-series association',assets['figure-7']['sample_links']==['yi-2002-erbium-series'])
 ck('Figure 9 pure model association',assets['figure-9']['sample_links']==['yi-2002-mechanisms'])
 ck('Figure 10 separate bulk reference association',assets['figure-10']['sample_links']==['yi-2002-bulk','yi-2002-upconversion'])
"""+s[z:]
s=s.replace("runtime['reader_items']==101",f"runtime['reader_items']=={nitems}").replace("runtime['unique_original_assets']==11","runtime['unique_original_assets']==16").replace("runtime['operation_count']==48",f"runtime['operation_count']=={nops}")
s=s.replace('11 originals, material hubs, 48 operation scenes',f'16 originals, material hubs, {nops} operation scenes')
s=s.replace("'records':16,'operations':48,'measurements':110,'reader_items':101,'source_units':147,'original_assets':11",f"'records':18,'operations':{nops},'measurements':{nmeas},'reader_items':{nitems},'source_units':{nunits},'original_assets':16")
(O/'check_integrated_presentation.py').write_text(s,encoding='utf8')
print(json.dumps({'items':nitems,'source_units':nunits,'operations':nops,'measurements':nmeas,'condition_quantities':nparams,'structural_properties':sorted(structprops)}))
