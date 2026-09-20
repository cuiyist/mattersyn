"""Author consistency checks and immutable handoff; never independent approval."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re
from PIL import Image
import pypdfium2
P=Path(__file__).resolve().parent;NOW=datetime.now(timezone.utc).isoformat();AUTHOR='/root/backlog_eta'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(n):return json.loads((P/n).read_bytes())
def write(n,v):(P/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[]
def ck(ok,name):
 checks.append({'check':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
f=load('source-facts.json');t=load('source-tables.json');inv=load('source-inventory.json');a=load('original-assets-manifest.json');coverage=load('page-coverage.json');intake=load('intake-identity.json')
for c in intake['file_copies']:ck(sha(c['source_path'])==c['sha256'],'source copy hash '+c['source_collection'])
H=intake['file_copies'][0]['sha256'];pdf=pypdfium2.PdfDocument(intake['file_copies'][0]['source_path']);ck(len(pdf)==11,'all supplied main pages')
for key in ['facts','materials','stocks','sample_contexts','figures','equations','conflicts','missingness','references','protocols']:
 ids=[x['id']for x in f[key]];ck(len(ids)==len(set(ids)),'unique '+key+' IDs')
ck(len(inv['inventory_units'])==len(set(u['id']for u in inv['inventory_units'])),'globally namespaced inventory IDs')
def ptr(doc,p):
 for tok in p.strip('/').split('/'):doc=doc[int(tok)]if isinstance(doc,list)else doc[tok.replace('~1','/').replace('~0','~')]
 return doc
for u in inv['inventory_units']:
 obj=ptr(f if u['path']=='source-facts.json'else t,u['json_pointer']);ck(obj.get('id',obj.get('sample_id'))==u['source_object_id'],'inventory pointer '+u['id'])
factids={x['id']for x in f['facts']};cid={x['id']for x in f['conflicts']};gid={x['id']for x in f['missingness']}
for key in ['facts','figures']:
 for o in f[key]:
  for x in o.get('conflict_ids',[]):ck(x in cid,o['id']+' conflict '+x)
  for x in o.get('gap_ids',[]):ck(x in gid,o['id']+' gap '+x)
for pr in f['protocols']:
 for o in pr['operations']:
  for fid in o['source_fact_ids']:ck(fid in factids,o['id']+' source fact '+fid)
  expected=[q for fact in f['facts']if fact['id']in o['source_fact_ids']for q in fact['quantities']]
  for q in o['quantities']:ck(q in expected,o['id']+' unchanged source quantity '+q['meaning'])
def walk(x,loc=''):
 if isinstance(x,dict):
  if 'source_sha256'in x and 'pdf_page'in x:ck(x['source_sha256']==H and 1<=x['pdf_page']<=11,'source-bound locator '+loc)
  if 'raw_text'in x and 'comparison'in x:
   ck(x['status']in['reported','reported_text','reported_ratio_parts','reported_fraction'],'typed quantity status '+loc)
   if x['range']:ck(x['range']['min']<=x['range']['max'],'ordered interval '+loc)
   if x['uncertainty']is not None:ck(x['uncertainty']>=0,'nonnegative ESD '+loc)
  for k,v in x.items():walk(v,loc+'/'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,loc+'/'+str(i))
walk(f);walk(t)
rs=t['tables'][0]['rows'];ck(len(rs)==37,'37 original Table 1 rows');ck(sum(len(r['cells'])for r in rs)==185,'185 data cells plus 37 labels')
rb={r['sample_id']:{x['column']:x for x in r['cells']}for r in rs}
for sid in ['S1','S2']:
 ck(rb[sid]['t_rxn']['value']==1 and rb[sid]['t_rxn']['approximate']and rb[sid]['t_dwell']['value']==0,sid+' native ~1 and separate zero')
for sid in ['A1','A2','A3','A4','A5','A6']:
 for col in ['t_rxn','t_dwell']:ck(rb[sid][col]['unit']=='day',sid+' literal body day unit '+col)
for sid in ['D1','D2','D3','D4']:ck(rb[sid]['T_rxn']['value']is None and rb[sid]['T_rxn']['raw_text']=='RT',sid+' unknown numerical RT')
for i in range(1,17):
 for col in ['t_rxn','t_dwell']:ck(rb['I'+str(i)][col]['range']=={'min':0.0,'max':40.0},f'I{i} original range {col}')
fb={x['id']:x for x in f['facts']}
ck('almost phase-pure ZnAl2O4 with AlOOH below' in fb['sommer2020-acs-outcome']['claim'],'A1 majority target spinel not reversed')
ck(next(e for e in f['equations']if e['id']=='kubelka-munk')['expression']=='C/S = (1-R)^2 (2R)^x; x=1/2','native optical multiplication retained literally')
ck(next(x for x in f['facts']if x['id']=='sommer2020-synchrotron-xrd')['quantities'][1]['uncertainty']==0.00006,'wavelength last-digit ESD')
ck(next(x for x in f['facts']if x['id']=='sommer2020-acs-bimodal-size')['quantities'][2]['uncertainty']==0.06,'7.42(6) size ESD')
ck([x['number']for x in f['references']]==list(range(1,66)),'all 65 references in order')
ck(not f['training_eligibility']and f['atomic_model_status']=='not qualified','no premature task/model qualification')
ck(coverage['complete_supplied_page_coverage']and not coverage['complete_main_plus_si_coverage']and coverage['si_read_pages']==0,'main-only SI-gap honesty')
rendered={}
for asset in a['assets']:
 ck(sha(asset['path'])==asset['sha256'],'asset stored hash '+asset['id'])
 p=asset['pdf_page']
 if p not in rendered:rendered[p]=pdf[p-1].render(scale=3).to_pil().convert('RGB')
 crop=rendered[p].crop(tuple(asset['pixel_bbox']));actual=Image.open(asset['path']).convert('RGB')
 ck(crop.size==actual.size and crop.tobytes()==actual.tobytes(),'fresh original pixel replay '+asset['id'])
 ck(not asset['contains_complete_source_page'],'selected crop not complete page '+asset['id'])
 asset['visual_author_review']='actually inspected by author, including final corrected crop framing'
for page in coverage['pages']:
 ck(page['text_read']and page['native_page_visually_inspected'],'page read and visually inspected '+str(page['pdf_page']))
 ck(sha(page['text_path'])==page['text_sha256'],'text cache hash '+str(page['pdf_page']))
 ck(sha(page['image_path'])==page['image_sha256'],'full-page local image hash '+str(page['pdf_page']))
write('original-assets-manifest.json',a)
write('author-visual-review.json',{'author':AUTHOR,'created_at':NOW,'scope':'All 11 complete native main pages and all 20 selected crops actually viewed. Five contact sheets inspected; individual table/expressions and corrected figures 6-7 were reopened. No SI page viewed.','page_count':11,'selected_crops':20,'native_table_body_cells_read':222,'crop_hashes':{x['relative_path']:x['sha256']for x in a['assets']},'notes':['Source Figure 11 colors and plotted sample labels remain unmodified despite source discrepancies.','Literal optical expression is multiplication by (2R)^x, not a silently repaired standard formula.','Source-derived molecular formulas and literature structure cartoons do not confer model approval.'],'independent_review':False})
write('author-validation.json',{'schema':'mattersyn-source-author-validation/1','author':AUTHOR,'created_at':NOW,'status':'passed_author_consistency_checks','passed_checks':len(checks),'checks':checks,'counts':inv['counts'],'independent_audit_status':'pending','limitations':['Checks complement actual source reading; they do not independently audit the author.','SI is declared but not found in the bounded local filename/cache searches.','No source-derived full atomic structure or exact recipe/structure training eligibility is approved.']})
notes='''# Sommer et al. (2020): complete supplied-main source extraction

Title: Atomic Scale Design of Spinel ZnAl2O4 Nanocrystal Synthesis. DOI: 10.1021/acs.cgd.9b01519. All 11 supplied main pages were read and visually inspected. The incoming and legacy PDFs have the same verified hash. The article is synthesis-relevant.

The main-only package preserves 37 named Table 1 contexts (185 typed data cells plus 37 sample-label cells), three laboratory reactor families and the distinct in situ nitrate/oxide branches. It includes common isolation, all characterization/refinement methods, 13 numbered figures plus the graphical abstract, seven equations/expressions, the complete 65-reference list, and source-linked material/stock/operation inventories.

SI is declared on main page 9 but remains unlocated and unverified after a bounded search in both source folders and the existing legacy full-text cache. No SI tables, precise graph-only optical gaps, atomic coordinates, implicit pH values, unreported workup settings or cross-reactor identical batches were invented. Native S1/S2 table rows read approximately 1 min reaction time followed by a separate zero dwell. The D-series time entries are measurement contexts, not established synthesis-heating times.

Unresolved source discrepancies are explicit in C1-C13: microwave ramp/total times; SCF temperature; autoclave long duration; Figure 6 seconds/minutes; Figure 4b precursor legend; Figure 11 caption colors and plotted identities versus durations; final-conclusion coordination regime; conclusion size range; M2 trace impurity; a Zn coordination-reference phrase; the I12-I14 count; and I7/I8 initial-phase scope. Figure 11 and all other original graphics remain unchanged. The printed optical formula is retained literally as multiplication by (2R)^x, with x=1/2. A1 is correctly described in the prose as almost phase-pure ZnAl2O4, with AlOOH below quantification.

The full-page renders are only under source-render; complete text is only under private/text. complete-source-payloads.json enumerates these local-only payloads. reader-assets contains selected original crops, with source/page/pixel locators and fresh-render replay checks. Their presence is not publication approval.

Independent source audit, canonical record construction, reader mapping, visual models, integration and publication remain separate gates. No shared Site, ledger, source PDF or public lifecycle state was modified.
'''
(P/'extraction-notes.md').write_text(notes,encoding='utf-8')
# Bind the complete author package without absorbing the distinct reviewer's files.
files=[]
for child in P.iterdir():
 if child.is_file()and child.name not in ['package-freeze.json','build_canonical_proposal.py','build_reader_proposal.py','freeze_proposals.py']:files.append(child)
for folder in ['private','reader-assets','source-render']:files.extend(x for x in(P/folder).rglob('*')if x.is_file())
bound={str(x.resolve()):sha(x)for x in sorted(set(files))}
freeze={'schema':'mattersyn-source-package-freeze/1','source_id':f['source_id'],'doi':f['doi'],'author':AUTHOR,'frozen_at':NOW,'revision':2,'status':'author_frozen_pending_distinct_source_audit','scope':'Complete supplied main: 11 pages. SI declared, locally unlocated/unverified.','source_generation':intake['source_generation'],'bundle_sha256':intake['bundle_sha256'],'source_hashes':{c['source_path']:c['sha256']for c in intake['file_copies']},'counts':inv['counts'],'author_validation_sha256':sha(P/'author-validation.json'),'bound_files':bound,'independent_audit_status':'pending','publication_approval':False}
write('package-freeze.json',freeze);print(json.dumps({'freeze':str(P/'package-freeze.json'),'sha256':sha(P/'package-freeze.json'),'checks':len(checks),'bound_files':len(bound),'counts':inv['counts']},indent=2))
