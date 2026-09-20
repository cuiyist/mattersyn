"""Source-author consistency validation and immutable handoff, not peer approval."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy
from PIL import Image
import pypdfium2
P=Path(__file__).resolve().parent;AUTHOR='/root/backlog_eta';NOW=datetime.now(timezone.utc).isoformat()
def load(n):return json.loads((P/n).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def wr(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[]
def ck(b,n):
 checks.append({'check':n,'passed':bool(b)})
 if not b:raise AssertionError(n)
f=load('source-facts.json');t=load('source-tables.json');iv=load('source-inventory.json');cov=load('page-coverage.json');aa=load('original-assets-manifest.json');it=load('intake-identity.json');prep=load('source-preparation.json');docs={x['role']:x for x in prep['documents']}
for c in it['file_copies']:ck(sha(c['source_path'])==c['sha256'],'actual original hash '+c['file_key'])
ck(len({c['sha256']for c in it['file_copies']})==2,'four copies/two unique documents')
ck(f['source_generation']==it['source_generation']==2 and f['bundle_sha256']==it['bundle_sha256'],'generation2 current source binding')
for role,d in docs.items():ck(len(pypdfium2.PdfDocument(d['source_path']))==13,role+'13 pages')
for key in ['facts','materials','stocks','protocols','sample_contexts','figures','equations','conflicts','missingness','references']:
 ids=[x['id']for x in f[key]];ck(len(ids)==len(set(ids)),'unique '+key+' IDs')
ops=[o for pr in f['protocols']for o in pr['operations']];ck(len(ops)==39==len({x['id']for x in ops}),'39 unique operation IDs')
ck(len(iv['inventory_units'])==len({u['id']for u in iv['inventory_units']}),'globally unique inventory IDs')
def ptr(doc,p):
 for token in p.strip('/').split('/'):doc=doc[int(token)]if isinstance(doc,list)else doc[token.replace('~1','/').replace('~0','~')]
 return doc
for u in iv['inventory_units']:ck(ptr(f if u['path']=='source-facts.json'else t,u['json_pointer'])['id']==u['source_object_id'],'inventory pointer '+u['id'])
fb={x['id']:x for x in f['facts']};cid={x['id']for x in f['conflicts']};gid={x['id']for x in f['missingness']}
for op in ops:
 for fid in op['source_fact_ids']:ck(fid in fb,op['id']+' fact binding '+fid)
 allq=[q for fid in op['source_fact_ids']for q in fb[fid]['quantities']]
 for q in op['quantities']:ck(q in allq,op['id']+' source-identical action quantity '+q['meaning'])
materials={x['id']for x in f['materials']};stocks={x['id']for x in f['stocks']};outputs={x for o in ops for x in o['outputs']}
for stock in f['stocks']:
 for comp in stock['components']:ck(comp in materials|stocks,'stock component '+stock['id']+'/'+comp)
for o in ops:
 for inp in o['inputs']:ck(inp in materials|stocks|outputs,'operation input definition '+o['id']+'/'+inp)
 for qty in o['quantities']:ck(qty['meaning']!='fitted exciton binding energy','outcome not stage condition '+o['id']+'/'+qty['meaning'])
def walk(x,path=''):
 if isinstance(x,dict):
  if 'source_sha256'in x and'pdf_page'in x:
   role=x['document_role'];ck(x['source_sha256']==docs[role]['sha256'] and 1<=x['pdf_page']<=13,'source locator '+path)
  for c in x.get('conflict_ids',[]):ck(c in cid,'conflict reference '+path+'/'+c)
  for g in x.get('gap_ids',[]):ck(g in gid,'missingness reference '+path+'/'+g)
  if 'raw_text'in x and'comparison'in x:
   ck(x['comparison']in [None,'>','<','>=','<='],'typed comparator '+path)
   if x['range']:ck(x['range']['min']<=x['range']['max'],'ordered numeric range '+path)
   if x['uncertainty']is not None:ck(x['uncertainty']>=0,'nonnegative source uncertainty '+path)
  for k,v in x.items():walk(v,path+'/'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,path+'/'+str(i))
walk(f);walk(t)
ck([len(x['rows'])for x in t['tables']]==[3,5,20,5,6,9,7],'all seven native tables/55 rows')
ck(sum(c['is_printed_body_cell']for z in t['tables']for r in z['rows']for c in r['cells'])==301,'301 printed body cells')
ck(sum(len(r['cells'])for z in t['tables']for r in z['rows'])==321,'321 typed cells include20 repeated sample heading fields')
tb={z['id']:z for z in t['tables']}
def cell(tid,r,col):return next(c for c in tb[tid]['rows'][r]['cells']if c['column']==col)
for col in ['A3','tau3']:ck(cell('table-1',0,col)['value']is None and cell('table-1',0,col)['raw_text']=='','cubic blank is not zero '+col)
for r in [1,2]:ck(cell('table-s2',r,'sof')['value']==0,'literal zero occupancy preserved row'+str(r))
ck(cell('table-s2',3,'Wyckoff')['raw_text']=='4b'and cell('table-s1',1,'space_group')['raw_text']=='R-3m','unresolved Wyckoff/spacegroup source values preserved')
ck(not any(r['row_label']=='NCs@200'for r in tb['table-s2']['rows']),'no invented200C atomic coordinates')
ck(cell('table-s2',12,'atom')['raw_text']=='Cl2'and cell('table-s2',18,'atom')['raw_text']=='Cl1','literal Cl label exchange preserved')
ck(cell('table-s4',0,'PL_peak')['value']is None and cell('table-s4',0,'FWHM')['value']is None,'nonemissive sample hyphens remain null')
ck(cell('table-s4',5,'absorption_peak')['value']==282,'0.35 absorption282nm unchanged')
ck(cell('table-s5',6,'wavenumber')['unit']=='dimensionless'and cell('table-s5',6,'wavenumber')['printed_column_unit']=='cm^-1','Delta/B interpreted ratio with literal column unit retained')
ck(cell('table-s6',1,'lambda_ex')['value']==330,'literal330nm table row retained against335nm figure')
diagnostic=[]
for ri,r in enumerate(tb['table-s6']['rows']):
 vals={c['column']:c['value']for c in r['cells']};mean=(vals['A1']*vals['tau1']+vals['A2']*vals['tau2'])/100
 diagnostic.append({'lambda_ex_nm':vals['lambda_ex'],'reported_tau_avg_us':vals['tau_avg'],'author_check_normalized_printed_formula_us':mean,'reported_minus_check_us':vals['tau_avg']-mean})
 ck(abs(mean-vals['tau_avg'])>1,'printed formula/table tension persists '+str(ri))
wr('author-lifetime-diagnostic.json',{'author':AUTHOR,'purpose':'Arithmetic consistency check, not correction or source formula replacement','source_table':'table-s6','calculation':'(A1*tau1+A2*tau2)/100; percentages normalized solely for this diagnostic','rows':diagnostic})
eq={x['id']:x for x in f['equations']}
ck(eq['trpl-average']['expression']=='tau_avg = sum(i=1..n) Ai*taui','printed lifetime formula retained')
ck(eq['distortion']['expression']=='D = (1/6) sum(i=1..6) |li-lavg|/lavg','absolute relative distortion not squared formula')
ck(fb['matuhina2023-cs-store']['quantities'][0]['comparison']=='>=','atleast30min bound retained')
ck(fb['matuhina2023-temperature-outcome']['quantities'][0]['comparison']=='<','below150C unsuccessful condition retained')
ck(fb['matuhina2023-lsc-setup']['quantities'][-1]['range']=={'min':-5.0,'max':.5},'negative/positive voltage interval preserved')
ck(fb['matuhina2023-binding-energy']['quantities'][1]['uncertainty']==18,'100±18meV uncertainty preserved')
ck([x['number']for x in f['references']]==list(range(1,56)),'all55references')
ck(all('ACS Applied Nano Materials www.'not in r['text']for r in f['references']),'no journal footer inside references')
ck(not f['training_eligibility']and f['atomic_model_status']=='not qualified','no premature training or structure approval')
ck(all(not pr['exact_protocol_eligibility']for pr in f['protocols']),'all exact-protocol gates closed')
ck(cov['complete_main_plus_si_coverage']and cov['main_read_pages']==13 and cov['si_read_pages']==13,'actual complete26-page coverage')
for p in cov['pages']:
 ck(p['text_read']and p['native_page_visually_inspected'],'actual read/view '+p['document_role']+str(p['pdf_page']))
 for key,hkey in [('text_path','text_sha256'),('layout_text_path','layout_text_sha256'),('image_path','image_sha256')]:ck(sha(p[key])==p[hkey],'page cache hash '+p[key])
 ck('source-render'in p['image_path']and'source-render'in p['text_path'],'full-page payload exclusion directory')
pdfs={d:pypdfium2.PdfDocument(v['source_path'])for d,v in docs.items()};rends={}
for a in aa['assets']:
 ck(sha(a['path'])==a['sha256'],'selected crop hash '+a['id'])
 key=(a['source_role'],a['pdf_page'])
 if key not in rends:rends[key]=pdfs[key[0]][key[1]-1].render(scale=3).to_pil().convert('RGB')
 native=rends[key].crop(tuple(a['pixel_bbox']));stored=Image.open(a['path']).convert('RGB')
 ck(native.size==stored.size and native.tobytes()==stored.tobytes(),'actual fresh PDF pixel replay '+a['id'])
 ck(not a['contains_complete_source_page']and stored.size!=rends[key].size,'selected crop not whole page '+a['id'])
 a['visual_author_review']='actually inspected; all30 crops on eight contacts and four corrected/large originals reopened'
wr('original-assets-manifest.json',aa)
wr('author-visual-review.json',{'author':AUTHOR,'created_at':NOW,'scope':'All13main+13SI native pages actually viewed. All30 selected crops viewed on eight contacts;FigureS3/S8 and both expression crops reopened after final framing correction. Tables compared to native pages.','native_pages':26,'selected_crops':30,'numbered_figures':18,'additional_visual_units':['graphical abstract','FigureS2 caption continuation'],'actual_visual_review':True,'independent_review':False,'asset_hashes':{a['relative_path']:a['sha256']for a in aa['assets']}})
wr('author-validation.json',{'schema':'mattersyn-source-author-validation/1','author':AUTHOR,'created_at':NOW,'status':'passed_author_consistency_checks','passed_checks':len(checks),'checks':checks,'counts':iv['counts'],'independent_audit_status':'pending','limitations':['These are author consistency checks, not independent scientific approval.','No measured CIF, atomistic reconstruction or training eligibility is approved.','Original-source discrepancies remain C1–C13; detailed missingness G1–G6 remains.','Table counts include301 printed body cells and20 repeated sample-heading metadata fields; numeric cell count230 includes numeric condition-label cells, not a distinct experiment count.']})
notes='''# Matuhina et al. (2023): full local main/SI source extraction

DOI 10.1021/acsanm.2c04342 — Role of CsMnCl3 Nanocrystal Structure on Its Luminescence Properties. Both incoming and legacy main/SI copies match the intake hashes. Main13pages and matchedSI13pages were actually read and visually inspected, including all55 rows of seven tables. Title/byline and main Associated Content establish content continuity. The SI adds initial “The” to the title.

The packet preserves Cs-oleate preparation and reactivation, the five explicitly supported temperature/loading conditions, primary isolation, three alternative purification approaches with unsuccessful outcomes, unisolated degradation, all acquisition/model/device methods, stocks and separate specimen contexts. Source ratios are not silently reconstructed from masses or assumed final stock volumes. Blank cells are not zero. The source’s five preparation labels are not independent batch counts or a full crossed condition matrix.

The62facts/186quantities,28materials,5stocks,14protocol scopes/39operations,41sample contexts,seven tables/55rows,18numbered figures plus graphical abstract/caption continuation,8expressions and55references are mapped to353 unique source inventory units. Tables hold301 printed body cells plus20 repeated sample-group fields (321typed fields in total;230numeric-valued fields). Thirty selected original crops are retained with native PDF locators and exact pixel replay. Full text/full pages remain only in source-render and are enumerated in complete-source-payloads.json for local-only exclusion. source-preparation.json retains its original preparation-time pending-reading flags; page-coverage.json is the later actual reading record.

Unresolved source issues C1–C13 include Figure2 phase/code/iodide caption errors; size-summary and rod-dimension differences; ratio and panel-label conflicts;335/330nm excitation; unvalidated structural-table occupancy/Wyckoff entries and missing200°C coordinate block; the printed lifetime-average formula versus table results; stability observable/endpoints; Delta/B column-unit context; the above-gap interpretation; unencapsulated-film versus embedded wording; and the lowest FWHM temperature plotted versus prose. No equation, zero occupancy, unknown unit, missing condition, atomic geometry or raw spectrum was silently repaired. A bounded lifetime arithmetic diagnostic is explicitly author-derived and does not replace source data.

The DFT states, source-refined coordinates/ADPs, spectroscopic fits, phase fractions and proposed mechanisms retain their own evidence classes. In particular, no source-table availability alone approves a CIF or recipe–structure training pair. No cited external paper has been downloaded or newly read. No Site, source PDF, shared ledger or public state was edited. Independent source audit, canonical construction, visuals and publication remain separate gates.
'''
(P/'extraction-notes.md').write_text(notes,encoding='utf-8')
rootfiles=['intake-identity.json','prepare_sources.py','source-preparation.json','source_author_data.py','build_extraction.py','validate_and_freeze.py','source-facts.json','source-tables.json','source-inventory.json','page-coverage.json','pairing-review.json','relevance-screening.json','original-assets-manifest.json','complete-source-payloads.json','author-lifetime-diagnostic.json','author-visual-review.json','author-validation.json','extraction-notes.md']
bound={str(P/n):sha(P/n)for n in rootfiles}
for folder in ['source-render','reader-assets']:
 for path in sorted((P/folder).rglob('*')):
  if path.is_file():bound[str(path)]=sha(path)
for c in it['file_copies']:bound[c['source_path']]=c['sha256']
wr('package-freeze.json',{'schema':'mattersyn-source-package-freeze/1','author':AUTHOR,'source_id':'matuhina2023','doi':'10.1021/acsanm.2c04342','revision':1,'created_at':NOW,'source_generation':2,'bundle_sha256':it['bundle_sha256'],'scope':'Full supplied13main+13SI source extraction; independent scientific audit pending.','status':'frozen_for_independent_source_audit','counts':iv['counts'],'passed_author_checks':len(checks),'bound_files':bound,'independent_audit_status':'pending','excluded_from_author_scope':['source-independent-audit/**'],'not_approved':['atomic_model','canonical_records','training_eligibility','publication'],'publication_policy':'Original PDFs, complete text and whole-page renders are local-only; selected crops separately gated.'})
print(json.dumps({'freeze_sha256':sha(P/'package-freeze.json'),'source_facts_sha256':sha(P/'source-facts.json'),'bound_files':len(bound),'checks':len(checks),'counts':iv['counts']},indent=2))
