"""Prepare private read-only actual-build audits. Run only after root build."""
from pathlib import Path
import json
O=Path(__file__).resolve().parent;B=O.parent;OLD=B.parent/'cm0115416/reader-assets'
r=json.loads((B/'public-review-proposal/banerjee2003.json').read_text(encoding='utf8'));records={p.stem:json.loads(p.read_text(encoding='utf8')) for p in (B/'canonical-drafts').glob('*.json')}
nitems=r['counts']['reader_items'];nunits=r['counts']['source_audit_units'];nops=sum(len(x['operations']) for x in records.values());nmeas=sum(len(x['measurements']) for x in records.values());nparams=sum(len(o['parameters']) for x in records.values() for o in x['operations'])
s=(OLD/'check_reader_runtime.mjs').read_text(encoding='utf8').replace('yi2002','banerjee2003').replace('Yi2002','Banerjee2003')
s=s.replace('All 115 source items executed',f'All {nitems} source items executed').replace('cards.length===115&&items.length===115',f'cards.length==={nitems}&&items.length==={nitems}')
s=s.replace("'Ten original figure cards',figureCards.length===10","'Eight main and one SI original figure cards',figureCards.length===9")
s=s.replace('All 16 original assets accessible','All 15 original assets accessible').replace('allAssets.length===16&&filenames.length===16','allAssets.length===15&&filenames.length===15')
a=s.index("check('Five-page main-only review displayed'");z=s.index('const input=',a)
s=s[:a]+"""check('Nine main and one SI page displayed',document.getElementById('review-summary').textContent.includes('10 pages')&&ledger.documents.length===2&&ledger.documents.find(d=>d.role==='main')?.page_count===9&&ledger.documents.find(d=>d.role==='si')?.page_count===1);
check('SI matched identity explicit',ledger.supporting_information.status==='matched_local_si'&&cardMap.get('si-identity')?.textContent.includes('ja035980c'));
check('SI precursor scope explicit',cardMap.get('si-ir')?.textContent.includes('oxidized multiwalled nanotubes'));
check('EDS source unit ambiguity explicit',cardMap.get('eds-unit-conflict')?.textContent.includes('keV'));
check('Literal source TeO3 assignment explicit',cardMap.get('teo3')?.textContent.includes('TeO₃'));
check('No-tube comparison remains separate',cardMap.get('free-particle-size')?.textContent.includes('without nanotube'));
check('Atomic figure remains source model',cardMap.get('figure8-model')?.textContent.includes('model'));
"""+s[z:]
s=s.replace("input.value='Scherrer'","input.value='TDPA'")
s=s.replace('All 105 operations',f'All {nops} operations').replace('operationCount===105',f'operationCount==={nops}')
s=s.replace('All 105 actual mounted',f'All {nops} actual mounted').replace('mountedOperations===105',f'mountedOperations==={nops}')
s=s.replace('All 138 actual condition',f'All {nparams} actual condition').replace('mountedQuantities===138',f'mountedQuantities==={nparams}')
(O/'check_reader_runtime.mjs').write_text(s,encoding='utf8')
s=(OLD/'check_integrated_presentation.py').read_text(encoding='utf8').replace('yi2002','banerjee2003').replace('yi-2002','banerjee-2003').replace('Yi 2002','Banerjee 2003')
s=s.replace("ck('18 records / 105 operations / 91 measurements',len(records)==18 and sum(len(r['operations']) for r in records.values())==105 and sum(len(r['measurements']) for r in records.values())==91)",f"ck('14 records / {nops} operations / {nmeas} measurements',len(records)==14 and sum(len(r['operations']) for r in records.values())=={nops} and sum(len(r['measurements']) for r in records.values())=={nmeas})")
s=s.replace('6 literature protocols / 11 procedures / 1 observation','1 literature protocol / 9 procedures / 4 observations').replace('Counter(literature_protocol=6,procedure=11,observation=1)','Counter(literature_protocol=1,procedure=9,observation=4)')
structprops={m['property'] for rid,x in records.items() if rid in {'banerjee-2003-'+v for v in ['electron-microscopy','sem','eds','xrd','oxidation']} for m in x['measurements']}
for key,ids in {'growth':['long-axis','aspect','junctions'],'oxidation-controls':['strong-oxygen','mild-oxygen','strong-result','mild-result','pristine-result','correlation'],'free-nanocrystals':['free-prose-size','no-tube-size','free-shape','later-comparison'],'xps':['cd-binding','strong-oxygen','mild-oxygen','carbon','tellurium','oxygen-curve']}.items():structprops.update(m['property'] for m in records['banerjee-2003-'+key]['measurements'] if m['id'] in ids)
a=s.index(' expected_structure=');z=s.index('\n def structural',a);s=s[:a]+' expected_structure='+repr(structprops)+s[z:]
s=s.replace("expected_optical={'prose_power_law_exponent','figure_power_law_exponent','author_inferred_excitation_photon_count'}","expected_optical={'cdte_lo_raman_peak','cited_bulk_cdte_lo_peak','nanotube_g_mode','nanotube_disorder_band_range','si_infrared_axis_scope','figure7_displayed_wavelength_range'}")
s=s.replace("'115 reader items intact'",f"'{nitems} reader items intact'").replace('len(items)==115',f'len(items)=={nitems}')
s=s.replace("'148 source units retained'",f"'{nunits} source units retained'").replace("len(source['units'])==148",f"len(source['units'])=={nunits}")
s=s.replace('16 original assets and category counts','15 original assets and category counts').replace('len(assets)==16','len(assets)==15').replace('==[10,0,0,6]','==[9,0,0,6]')
s=s.replace("a['asset_provenance']['source_sha256']==cm['sources'][0]['sha256']","a['asset_provenance']['source_sha256']==next(d['sha256'] for d in cm['sources'] if d['role']==a['document_role'])")
a=s.index(" ck('Figure 1 explicit 800 C association'");z=s.index(" ck('Obsolete private pending-audit gap removed'",a)
s=s[:a]+""" ck('Figure 1 precursor-only association',assets['figure-1']['sample_links']==['banerjee-2003-oxidation'])
 ck('Figure 8 pure model association',assets['figure-8']['sample_links']==['banerjee-2003-mechanisms'])
 ck('SI precursor-only association',assets['si-infrared']['sample_links']==['banerjee-2003-infrared'])
 ck('SI exactly matched and reviewed',reader['supporting_information']['status']=='matched_local_si' and [(d['role'],d['page_count']) for d in reader['documents']]==[('main',9),('si',1)])
 ck('CdTe excludes precursor-only IR', 'banerjee-2003-infrared' not in reader['material_evidence_records']['CdTe'])
 ck('MWNT excludes free-only comparator','banerjee-2003-free-nanocrystals' not in reader['material_evidence_records']['MWNT'])
"""+s[z:]
s=s.replace("runtime['reader_items']==115",f"runtime['reader_items']=={nitems}").replace("runtime['unique_original_assets']==16","runtime['unique_original_assets']==15").replace("runtime['operation_count']==105",f"runtime['operation_count']=={nops}")
s=s.replace('16 originals, material hubs, 105 operation scenes',f'15 originals, material hubs, {nops} operation scenes')
s=s.replace("'records':18,'operations':105,'measurements':91,'reader_items':115,'source_units':148,'original_assets':16",f"'records':14,'operations':{nops},'measurements':{nmeas},'reader_items':{nitems},'source_units':{nunits},'original_assets':15")
(O/'check_integrated_presentation.py').write_text(s,encoding='utf8')
(O/'expected-structural-properties.json').write_text(json.dumps(sorted(structprops),indent=2)+'\n',encoding='utf8')
print(json.dumps({'items':nitems,'source_units':nunits,'operations':nops,'measurements':nmeas,'condition_quantities':nparams,'structural_properties':sorted(structprops)}))
