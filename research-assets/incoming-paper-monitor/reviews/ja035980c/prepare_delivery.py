from pathlib import Path
import json
B=Path(__file__).resolve().parent;P=B.parent/'cm0115416'
scope='All nine supplied main pages and the matched one-page SI text-read and visually inspected, with independent source, canonical, molecular, apparatus and reader audits. Nanotube pretreatment, in situ CdTe growth, control populations, separated washings and analytical specimens retain distinct evidence scopes. Missing precursor amounts, Te stock speciation/concentration and final drying conditions remain explicit; cited external works not independently inspected.'
for name in ['run_build.py','build_inventory_actual.py','verify_archive.py','finalize_publication.py','save_prepublication_checkpoint.py']:
 t=(P/name).read_text(encoding='utf-8').replace('yi2002','banerjee2003').replace('yi-2002-','banerjee-2003-').replace('cm0115416','ja035980c').replace('0.18.0','0.19.0').replace('La2(MoO4)3:Yb,Er','CdTe/MWNT').replace('all_yi_records','all_banerjee_records').replace('-yi-actual','-banerjee-actual')
 if name=='build_inventory_actual.py':
  start=t.index("row={'source_group'");end=t.index("\ninv['per_paper']",start)
  row=t[start:end]
  row=row.replace("'full_supplied_main_review_si_unverified'","'full_documents_reviewed'")
  a=row.index("'review_scope':");b=row.index(",'evidence_locator'",a)
  row=row[:a]+"'review_scope':"+repr(scope)+",'documents':[{'role':'main','page_count':9,'all_text_read':True,'all_visually_reviewed':True},{'role':'si','page_count':1,'all_text_read':True,'all_visually_reviewed':True}]"+row[b:]
  row=row.replace("'si_status':'not_located_or_verified'","'si_status':'matched_and_reviewed'")
  row=row[:row.index(",'notes':")]+",'notes':"+repr(['One CdTe–MWNT growth route, nine supporting procedures and four observations; the source does not quantify every reagent or establish atomically resolved junction geometry.','All eight main figures and the matched SI infrared spectrum, plus six source excerpts preserve microscopy, EDS, XPS, XRD, Raman, UV-visible and IR evidence.','Bound CdTe, free/washings particles, no-tube comparison and oxidized MWNT precursor retain distinct sample scopes. The EDS caption unit discrepancy and literal TeO3 assignment remain explicit.'])+'}'
  t=t[:start]+row+t[end:]
 if name=='finalize_publication.py':
  t=t.replace('5025768ecf6ddd21d556ffb63dac2e912982fc4adf6835cdd0b9bebc647e56e7','792b19f3ec9915f869b1759227761a909337731a1d1237bb4ac3c9e72047b58e')
  t=t.replace("{'6438ee53b3fffb86f5e36508f265041d9235b8ee9f3e20dd99d46aae91c68a57'}","{'24faaec54cea1293bc7951b7d363587e2ec80edaa68d6e90049b5525bc312837','0746611853616b5531750d1cd4c610d605c551eec0b3317805c0fcc98fce301e'}")
  t=t.replace('supplied_main_only_si_unverified','supplied_main_and_matched_si').replace('original_figures=10','original_figures=9,original_main_figures=8,original_si_figures=1')
  t=t.replace("si_status='No SI declaration observed in supplied main; matching SI not located or verified.'","si_status='Matched one-page SI fully read and visually reviewed; oxidized-MWNT precursor infrared spectrum.'")
  t=t.replace("len(records)==18 and p['synthesis_routes']==6 and p['operations']==105","len(records)==14 and p['synthesis_routes']==1 and p['operations']==39")
  t=t.replace('Closure covers supplied main only; later SI reopens review.','Closure covers all nine main pages and matched one-page SI; later or changed evidence reopens review.').replace('Supplied-main contribution published and closed.','Supplied main and matched SI contribution published and closed.')
 if name=='save_prepublication_checkpoint.py':
  t=t.replace("len(records)==18 and sum(len(r['operations'])for r in records)==105 and sum(len(r['measurements'])for r in records)==91","len(records)==14 and sum(len(r['operations'])for r in records)==39 and sum(len(r['measurements'])for r in records)==97")
  t=t.replace('Six synthesis routes, eleven supporting procedures and one interpretation observation retain 105 operations and 91 measurement entries. All 148 source units mapped to the 115-item reader. Matching SI unverified.','One synthesis route, nine supporting procedures and four contextual observations retain 39 operations and 97 measurement entries. All 176 source units mapped to the reader. All nine main pages and matched one-page SI reviewed.')
  t=t.replace('sixteen original assets, molecular, binding and 105 apparatus-scene','fifteen original assets, molecular, binding and 39 apparatus-scene')
  t=t.replace('Stock mass/mole and feed/formula conflicts, comparison-batch missingness, spectral label discrepancies and separate analytical specimen identities remain explicit.','Missing doses and Te stock identity, separate particle populations, precursor-only SI infrared scope and the printed EDS unit discrepancy remain explicit.')
  t=t.replace('One new lanthanum-molybdate material hub, six equal route cards, periodic discovery and all original figures.','A new CdTe–MWNT material hub, explicit component-only CdTe and MWNT discovery, the reviewed synthesis route and all original figures.')
  t=t.replace('close supplied-main scope','close supplied main and matched SI scope')
 (B/name).write_text(t,encoding='utf-8')
print('Prepared build, inventory and publication helpers; not integrated or published.')
