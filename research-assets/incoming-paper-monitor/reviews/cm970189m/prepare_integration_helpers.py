from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;OLD=B.parent/'jp971091y';S=B.parents[3]/'recipe-atlas'
t=(OLD/'build_inventory_actual.py').read_text(encoding='utf-8').replace('dabbousi','veinot').replace('Dabbousi','Veinot')
t=t.replace('All13supplied','All6supplied').replace("'page_count':13","'page_count':6")
t=t.replace("'veinot17':len(row['record_ids'])==17","'veinot21':len(row['record_ids'])==21")
t=t.replace("'veinot2routes':row['synthesis_route_variant_count']==2","'veinot6routes':row['synthesis_route_variant_count']==6")
t=t.replace("'old_records_preserved':len(records)-17==184","'old_records_preserved':len(records)-21==201")
t=t.replace("'notes':['General ZnS and CdS overgrowth routes are separate; six note22 size-temperature pairs are condition choices, not six asserted independent runs.','Ten supporting procedures retain seed synthesis, sample preparation, acquisition and post-synthesis exposure.','Five observation records preserve optical, table/coverage, oxidation, solution-SAXS and CdS-comparison cohorts; exact recipe/outcome joins remain unresolved.','Sixteen original figures, Table1, five numbered equations and additional source notes/formulas are retained. Model dimensions and fitted parameters do not become experimental atomic structures.']","'notes':['One phenolic CdS preparation and five surface-esterification variants; variants retain inherited framework and independently reported values.','Eleven supporting procedures preserve six molecular precursor preparations, reagent conditioning and four analytical methods. Organic products are not CdS synthesis targets.','One deliberate nonreactive control and three observation records remain distinct; no calibrated failure labels.','Six original figures, three complete tables, Scheme1 and compound illustration; all15references/notes and141source units inventoried. Typed qualitative observations preserve solubility and spectral behavior without numeric guesses.']")
assert "==21"in t and 'len(records)-21==201'in t
(B/'build_inventory_actual.py').write_text(t,encoding='utf-8')
t=(OLD/'run_build.py').read_text(encoding='utf-8').replace('dabbousi-protocol.mjs','veinot-protocol.mjs')
t=t.replace("for name in ['veinot-protocol.mjs'", "run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py'])\nfor name in ['veinot-protocol.mjs'")
t=t.replace("'paper-review.mjs']","'paper-review.mjs','chemical-viewer.mjs','material-hub.mjs','material-guide.mjs']")
(B/'run_build.py').write_text(t,encoding='utf-8')
identity=json.loads((B/'source-identity.json').read_text(encoding='utf-8'))
manifest={'source_id':'veinot1997','doi':identity['doi'],'title':identity['title'],'source_sha256':identity['main_sha256'],'files':identity['local_files'],'source_generation':2,'review_scope':'supplied_main_only_si_unverified','pages':[],'si_status':'Not located or verified; no SI-absence claim.'}
for p in range(1,7):
 row={'page':p,'text_read':True,'visually_reviewed':True}
 for key,path in [('text',B/f'plain-page-{p}.txt'),('render',B/f'main-{p:02}.png')]:row[key+'_file']=path.name;row[key+'_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
 manifest['pages'].append(row)
(B/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared source manifest and derived-inventory/build helpers; no publication claim.')
