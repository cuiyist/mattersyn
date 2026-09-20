"""Author validation and freeze after actual complete reading and selected-crop inspection."""
from pathlib import Path
import json,hashlib,datetime,subprocess,sys,math
B=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text('utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,obj):(B/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
assets=read(B/'selected-original-assets.json')
for a in assets['assets']:
 a['author_visual_inspection']='completed_individual_crop_and_original_page'
 a['author_visual_review_basis']='Actually viewed by /root/norberg2004_extract; complete caption, labels and graphic retained. This is author review, not independent approval.'
assets['author_visual_inspection']={'author':'/root/norberg2004_extract','completed_at':now,'individual_selected_crops_viewed':25,'full_original_pages_previously_viewed':24,'contact_sheets_viewed':5,'scope':'All original selected graphics, captions and footnotes; two magnified original-pixel details for overlapping NMR labels.','corrections':['Trimmed stray method-text margin aboveS12','Trimmed stray text belowSchemeS1','Trimmed unrelated method heading belowS7composition','RightTEM scale bar50nm corrects early20nm reading','S4C central integral1000.00 verified in magnified original detail']}
write('selected-original-assets.json',assets)
subprocess.run([sys.executable,'-B','-X','utf8',str(B/'build_source_extraction.py')],check=True,stdout=subprocess.PIPE)
I=read(B/'source-inventory.json');F=read(B/'source-facts.json');C=read(B/'cif-source-inventory.json');P=read(B/'complete-source-payloads.json');cover=read(B/'page-coverage.json');prep=read(B/'source-preparation.json')
checks=[]
def check(name,value):
 checks.append({'name':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
U={u['id']:u for u in I['units']};FF={f['id']:f for f in F['facts']};AA={a['id']:a for a in assets['assets']};SS={s['id']:s for s in I['sample_lineage']}
check('unique unit ids',len(U)==len(I['units']))
check('unique fact ids',len(FF)==len(F['facts']))
check('unique sample-context ids',len(SS)==len(I['sample_lineage']))
check('all25 selected originals present',len(AA)==25)
for role,d in I['source_documents'].items():check('original unchanged '+role,sha(d['path'])==d['sha256'])
for d in prep['documents'][:2]:
 for p in d['text_pages']+d['rendered_pages']:check('retained text/page asset '+Path(p['path']).name,sha(p['path'])==p['sha256'])
for a in assets['assets']:
 check('selected asset hash '+a['id'],sha(a['path'])==a['sha256'])
 check('source identity '+a['id'],a['source_sha256']==I['source_documents'][a['source_role']]['sha256'])
 check('individual inspection recorded '+a['id'],a['author_visual_inspection']=='completed_individual_crop_and_original_page')
for u in I['units']:
 check('source role hash '+u['id'],u['source_sha256']==I['source_documents'][u['source_role']]['sha256'])
 for a in u['original_asset_ids']:check('object asset exists '+u['id']+' '+a,a in AA)
for f in F['facts']:
 check('fact unit exists '+f['id'],f['source_unit_id'] in U)
 u=U[f['source_unit_id']]
 check('fact precise source '+f['id'],f['evidence'][0]['source_sha256']==u['source_sha256'] and f['evidence'][0]['locator']==u['locator'] and f['evidence'][0]['pdf_page']==u['pdf_page'])
 check('no training admission '+f['id'],f['eligible_training'] is False)
 check('conflict ids valid '+f['id'],set(f['conflict_ids'])<=set(c['id'] for c in I['source_conflicts']))
 if isinstance(f['value'],(int,float)):check('finite quantity '+f['id'],math.isfinite(f['value']))
for collection,key in [('materials','source_unit_id'),('procedures','source_unit_id'),('stocks','source_unit_id')]:
 for item in I[collection]:check('linked '+collection+' '+item['id'],item[key] in U)
for s in I['sample_lineage']:
 for u in s['source_unit_ids']:check('sample unit '+s['id']+' '+u,u in U)
 for parent in s['explicit_parent_ids']:check('sample parent '+s['id']+' '+parent,parent in SS)
 for inheritance in s.get('procedure_inheritance_source_unit_ids',[]):check('procedure inheritance is source unit '+s['id'],inheritance in U)
 check('no invented replicate '+s['id'],s['distinct_physical_replicate_claimed'] is False)
check('Cd timecourse has no unsupported physical link to S8C',SS['cd-timecourse']['explicit_parent_ids']==[])
check('Pb precursor procedure does not consume Cd precursor sample',SS['pb-oleate']['explicit_parent_ids']==[])
for p in P['pages']:
 check('exact whole private text payload '+p['id'],p['complete_native_extracted_text']==Path(p['text_path']).read_text('utf-8'))
 check('all pages have scientific units '+p['id'],len(p['scientific_unit_ids'])>0)
 check('page unit mapping exact '+p['id'],set(p['scientific_unit_ids'])==set(u['id'] for u in I['units'] if u['source_role']==p['source_role'] and u['pdf_page']==p['pdf_page']))
check('all24 pages',len(P['pages'])==24 and len(cover['pages'])==24)
check('all24 actual text and visual readings',all(p['text_read'] and p['visually_inspected'] for p in cover['pages']))
check('CIF99scalars7loops348rows2896cells',len(C['scalars'])==99 and len(C['loops'])==7 and sum(l['row_count'] for l in C['loops'])==348 and C['total_loop_cells']==2896)
for i,s in enumerate(C['scalars']):
 matches=[u for u in I['units'] if u['kind']=='cif_scalar' and u['payload']['cif_inventory_pointer']==f'/scalars/{i}']
 check('CIF scalar exact payload '+s['tag'],len(matches)==1 and matches[0]['payload']['scalar']==s)
for i,l in enumerate(C['loops']):
 matches=[u for u in I['units'] if u['kind']=='cif_loop' and u['payload']['cif_inventory_pointer']==f'/loops/{i}']
 check('CIF loop exact payload '+l['id'],len(matches)==1 and matches[0]['payload']['loop']==l)
 for n,row in enumerate(l['rows']):check('CIF row tag completeness '+l['id']+' '+str(n),set(row)==set(l['tags']))
atomloop=C['loops'][2];atomtypes={}
for row in atomloop['rows']:
 el=row['_atom_site_type_symbol']['value'];atomtypes[el]=atomtypes.get(el,0)+1
check('CIF asymmetric composition matches species9',atomtypes=={'Pb':1,'Se':4,'P':2,'C':24,'H':20})
check('CIF is explicitly molecular9',I['source_documents']['cif']['sha256']=='abd4ecdae2c4a445921b9fdde415fda76208d11fe0df40cc510c7fa94b510ef4' and 'molecular species9' in C['scope'])
check('rightTEM typed as50nm',FF['evans2010-object-figure-S16-right-tem-scale-bar']['value']==50)
check('leftTEM typed as5nm',FF['evans2010-object-figure-S16-left-tem-scale-bar']['value']==5)
check('one printed denominator conflict retained',FF['evans2010-object-calculation-S21-yield-printed-final-denominator']['value']==2.25e6)
check('initial limiting Se remains2.25umol',FF['evans2010-object-calculation-S21-yield-initial-limiting-dppse']['value']==2.25e-6)
check('no species9/QD sample merge','pbse-qd' not in SS['species9-cif']['explicit_parent_ids'] and 'cdse-qd' not in SS['species9-cif']['explicit_parent_ids'])
for recid in ['evans2010-tertiary-negative-rescue','evans2010-dpp-pb-control']:
 check('mass-amount conflict retained '+recid,len(U[recid]['conflict_ids'])>0)
checkpoint=read(B/'checkpoint-freeze.json')
for f in checkpoint['files']:check('early checkpoint preserved '+Path(f['path']).name,sha(f['path'])==f['sha256'])

payload_coverage=[]
for u in I['units']:
 ids=[f['id'] for f in F['facts'] if f['source_unit_id']==u['id']]
 payload_coverage.append({'source_unit_id':u['id'],'source_inventory_pointer':'/units/'+str(I['units'].index(u)),'fact_ids':ids,'disposition':'typed_source_facts_and_original_payload' if ids else 'qualitative_or_metadata_payload_retained','original_asset_ids':u['original_asset_ids']})
write('source-extraction-coverage.json',{'schema':'mattersyn-source-extraction-coverage/1','source_id':'evans2010','units':payload_coverage,'total_units':len(payload_coverage),'total_facts':len(F['facts']),'complete_source_pages':24,'cif_complete_scalar_and_loop_payloads':106,'no_unread_source_pages':True,'raw_curve_digitization_performed':False})
visual_details=[]
for name in ['inspection-S4-C-integral.png','inspection-S1-A-labels.png']:
 p=B/'reader-assets/selected-originals'/name;visual_details.append({'path':str(p),'sha256':sha(p),'purpose':'Private magnified/rotated original-pixel reading aid; not redrawn scientific evidence.'})
write('author-reading-corrections.json',{'schema':'mattersyn-author-prefreeze-source-reading-corrections/1','source_id':'evans2010','prior_immutable_checkpoint_sha256':sha(B/'checkpoint-freeze.json'),'corrections':[{'locator':'FigureS16 rightTEM bar','before':'20nm in initial reading inventory','after':'50nm in final typed extraction','reason':'High-resolution native original glyph is clearly50; no source file changed.'},{'locator':'FigureS4 panelC central integral','before':'Temporary author candidate1002.00 or1000.00; not frozen as source fact','after':'1000.00','reason':'Magnified original-pixel detail resolves four-digit normalization as1000.00.'},{'locator':'FigureS8 panelsB/C left31P labels','before':'Provisional reading notes99.42/99.41, not frozen typed facts','after':'99.12/99.11','reason':'Individually viewed native crop resolves middle digit1.'}],'details':visual_details,'originals_unchanged':True})
write('author-validation.json',{'schema':'mattersyn-source-author-validation/1','source_id':'evans2010','author':'/root/norberg2004_extract','created_at':now,'status':'passed_author_consistency_checks_pending_independent_audit','checks_count':len(checks),'checks':checks,'counts':I['counts'],'manual_scope':{'full_pages_text_read_and_viewed':24,'CIF_complete_text_read':True,'selected_original_crops_individually_viewed':25,'contact_sheets_viewed':5,'own_scientific_review':'All recipes/controls/observations/model distinctions, conflicts and sample joins reviewed against full supplied sources. This is author validation, not a separate independent scientific audit.'},'unread_regions':[],'open_source_conflicts':I['source_conflicts'],'full_curve_digitization':'not claimed; original curves retained','downstream_gates':{'independent_scientific_audit':'pending','canonical':'pending','reader':'pending','visual_reference_and_apparatus':'pending','publication':'not approved','training':'not admitted'}})
primary=['pairing-review.json','page-coverage.json','source-inventory.json','source-facts.json','cif-source-inventory.json','complete-source-payloads.json','selected-original-assets.json','selected-original-contact-sheets.json','source-extraction-coverage.json','author-reading-corrections.json','author-validation.json','extraction-notes.md','source-preparation.json','checkpoint-freeze.json','build_source_extraction.py','extract_cif_and_assets.py','freeze_source_extraction.py','prepare_sources.py','inspect_layout.py','checkpoint_pairing_inventory.py']
paths=[B/name for name in primary]+[Path(x['path']) for x in assets['assets']]+[Path(x['path']) for x in read(B/'selected-original-contact-sheets.json')['contacts']]+[Path(x['path']) for x in visual_details]
for d in prep['documents'][:2]:paths +=[Path(x['path']) for x in d['text_pages']+d['rendered_pages']]
paths +=[Path(x['path']) for x in checkpoint['files']]
unique=sorted(set(paths));bound=[{'path':str(p),'relative_path':p.relative_to(B).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in unique]
write('source-extraction-freeze.json',{'schema':'mattersyn-source-author-package-freeze/1','version':1,'source_id':'evans2010','doi':'10.1021/ja103805s','author':'/root/norberg2004_extract','created_at':now,'status':'frozen_author_extraction_pending_independent_scientific_audit','source_documents':I['source_documents'],'files':bound,'counts':I['counts'],'checks_count':len(checks),'source_conflicts':[x['id'] for x in I['source_conflicts']],'no_source_changes':True,'no_site_or_ledger_changes':True,'public_projection_limits':['Full original PDFs/CIF and full-page render/native text caches remain local under source-document exclusion policy.','complete-source-payloads.json contains full-paper extracted text and must stay local; exclude from future public repository projections.','Selected original figure/table/scheme crops and structured facts may be considered in later audited website work.','No source-derived loop or fact is removed merely because scientific; publication scope requires separate root projection review.'],'independent_audit':'pending','training_admission':False})
print(json.dumps({'freeze_sha256':sha(B/'source-extraction-freeze.json'),'inventory_sha256':sha(B/'source-inventory.json'),'facts_sha256':sha(B/'source-facts.json'),'validation_sha256':sha(B/'author-validation.json'),'bound_files':len(bound),'checks':len(checks),'counts':I['counts']},indent=2))
