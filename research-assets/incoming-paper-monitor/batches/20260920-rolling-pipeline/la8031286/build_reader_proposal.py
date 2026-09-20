"""Private six-section Pati source reader, typed canonical fields and selected crops."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import json,hashlib,re
P=Path(__file__).resolve().parent;C=P/'canonical-proposal/v1';O=P/'public-review-proposal/v1';O.mkdir(parents=True,exist_ok=True)
assert not(C/'package-manifest.json').exists()
S=Path('[local path redacted]');SID='pati2009';PRE='pati-2009-'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(x):return re.sub('[^a-z0-9]+','-',str(x).lower()).strip('-')
def esc(x):return str(x).replace('~','~0').replace('/','~1')
def resolve(x,p):
 for t in p.strip('/').split('/')if p else[]:x=x[int(t)]if isinstance(x,list)else x[t.replace('~1','/').replace('~0','~')]
 return x
def uniq(x):return list({json.dumps(a,ensure_ascii=False,sort_keys=True):a for a in x}.values())
def prose(x):
 x=str(x).replace('degC','°C').replace('angstrom','Å')
 x=re.sub(r'\b(Figure|Table|Whatman)(S?\d)',r'\1 \2',x)
 x=re.sub(r'\b(at|after|about|from|to|over|near|below|above|under|reports|gives|than|of|and|main|states|for|in|with|the|before|versus|diameter|calcined|as-prepared|reference|Refs?|SI|approximately|around|powder|precipitate|interval|water|ethanol|propanol|butanol|a|an|is|are|have|deviation|distance|spacing|labels?|label|repeats|preweighed|calculates|follows|observed|uses|component|energy|density|spectrum|strict|agglomerates|temperature|Supplied|contains|cites)(?=[<>~\d])',r'\1 ',x,flags=re.I)
 x=re.sub(r'(?<=\d)(nm|µm|um|eV|min|mL|h|g/cm³|m²/g|°C)(?=\b)',r' \1',x)
 x=re.sub(r',(?=\S)',', ',x);x=re.sub(r'\b(Main|main|SI)p(\d)',r'\1 p. \2',x);x=re.sub(r'\b(SI)(caption|prose)',r'\1 \2',x)
 x=re.sub(r'\b(September|November|December)(\d)',r'\1 \2',x);x=re.sub(r'\bSD(?=\d)', 'SD ',x);x=x.replace('DOI10.','DOI 10.').replace('et al.23','et al. 23').replace('laser05-','laser 05-').replace('JEOL2100','JEOL 2100').replace('ASAP2010C','ASAP 2010C').replace('Instruments2920','Instruments 2920').replace('AXIS165','AXIS 165').replace('isS1','is S1').replace('contractW','contract W').replace('NSFDMR','NSF DMR')
 x=x.replace('%Ce','% Ce').replace('%Gaussian','% Gaussian').replace('%Lorentzian','% Lorentzian').replace('as(a)','as (a)').replace('(a)as','(a) as').replace('(b)as','(b) as').replace('(c)calcined','(c) calcined').replace('(d)calcined','(d) calcined')
 return x
D=read(P/'source-facts.json');T=read(P/'source-tables.json');I=read(P/'source-inventory.json');A=read(P/'original-assets-manifest.json');PC=read(P/'page-coverage.json');FR=read(P/'package-freeze.json');CM=read(C/'record-manifest.json');CV=read(C/'source-to-field-coverage.json');OWN=read(C/'source-owner-map.json')
R={x['record_id']:read(x['path'])for x in CM['records']};U={x['id']:x for x in I['inventory_units']};UB={x['source_unit_id']:x['canonical_bindings']for x in CV['source_units']};PAY={'source-facts.json':D,'source-tables.json':T}
SECTIONS=[{'id':i,'title':t,'items':[]}for i,t in [('precursors','Precursors'),('protocol','Synthesis protocol'),('structures','Final structures'),('properties','Properties'),('intuition','Chemical intuition'),('sources','Sources and limitations')]]
ITEM={};UNIT={};FIELD={};OPS={};MAT={};STOCK={};PRODUCT={};MEAS={};UNITKEY={}
def evidence(es):
 out=[]
 for e in es:
  if'document_role'in e:out.append({k:e[k]for k in['source_id','document_role','pdf_page','printed_page','locator']});continue
  m=re.search(r'(MAIN|SI) PDF p\. (\d+) \(printed ([^)]+)\)',e['locator']);out.append({'source_id':SID,'document_role':m[1].lower()if m else'main','pdf_page':int(m[2])if m else None,'printed_page':m[3]if m else None,'locator':e['locator']})
 return out
def section(rid):
 k=rid.removeprefix(PRE)
 if k=='source-materials':return'precursors'
 if k in['xrd','tem','dls','structure-results']:return'structures'
 if k in['bet','tga','dsc','xps','xps-fit','packing','property-results']:return'properties'
 if k=='mechanistic-context':return'intuition'
 if k=='source-context':return'sources'
 return'protocol'
def add(sec,i,title,text,es=(),uid=None,scope='source context'):
 assert i not in ITEM
 x={'id':i,'title':prose(title),'text':prose(text),'source_audit_unit_ids':[uid]if uid else[],'source_fact_ids':[],'evidence':evidence(es),'facts':[],'canonical_links':[],'sample_scope':{'label':scope,'canonical_sample_links':[],'same_batch_verified':False},'original_assets':[],'notes':[],'reviewed':False,'training_eligible':False};ITEM[i]=x;next(s for s in SECTIONS if s['id']==sec)['items'].append(x)
 if uid:UNIT.setdefault(uid,[]).append(i)
 return x
OVERVIEW={
'precursors':('Separate stocks in three alcohols','Cerium nitrate hexahydrate and triethanolamine are dissolved separately in ethanol, 1-propanol or 1-butanol. Each preparation uses the same alcohol for its two stocks and precipitate wash. Six stock formulations retain their reported 0.1 M nitrate and 0.4 M TEA concentrations; the 100 mL transfers do not establish total stock preparation volume. Only ethanol is explicitly called anhydrous. Hydrate-associated water is not a separately charged solvent, and ammonium hydroxide serves only a filtrate diagnostic.'),
'protocol':('Precipitation, workup and separate calcination','At room temperature, 100 mL of nitrate stock is dripped into 100 mL of TEA stock at 3–4 mL/min under mild stirring. The additional 1 h stirring period begins after precipitation; no calculated dripping duration replaces it. Suction filtration separates the retained precipitate from a diagnostic filtrate aliquot. The solid is washed with its alcohol, dried for 24 h at room temperature, then washed with acetone. A further drying step is not supplied. Calcination is a separate treatment at 200 °C for 3 h with a 10 °C/min ramp and unreported atmosphere.'),
'structures':('Local crystallites and unresolved whole-powder identity','Microscopy shows approximately 3 nm crystallites aggregated into larger particles. SAED and local fringes support a CeO2 assignment, while as-prepared bulk diffraction remains unidentified and the authors propose a mixture. Calcined material is assigned cubic CeO2 with an approximately 5 nm Scherrer diameter. DLS values of 72, 50 and 14 nm are called radii in Results and diameters in Conclusions; both definitions are retained without a factor-of-two correction. No atomic coordinates or valid source CIF are supplied.'),
'properties':('Surface, thermal and packing measurements','BET areas and source-calculated equivalent diameters refer to calcined solvent-derived powders. TGA in air, DSC, XPS and rough hand-packed density describe separate measurement contexts. XPS fractions are surface and exposure dependent: short-exposure as-prepared and calcined values differ from long-exposure behavior. They are not whole-powder stoichiometries. The SI peak labels, calibration discrepancy and printed area expression are retained rather than repaired.'),
'intuition':('Proposed chemistry and cited comparisons','The paper attributes precipitation to TEA acting with precursor-associated water and discusses possible hydroxo and TEA complexes, deprotonation and solvent-dependent dispersion. These are author interpretations. Inconsistent statements about hydroxo-complex formation remain explicit. Prior diethylamine routes, yttria-doped ceria and proposed future catalysts retain their own source boundaries and do not supply missing current recipe conditions.'),
'sources':('Complete supplied source scope','All four main and four matched SI pages have been read and visually inspected in the passed distinct source audit. This reader retains 58 facts, 90 fact quantities, one ten-row XPS table, four figures and four printed expressions. Missing reference 27 remains unresolved. Canonical, molecular, apparatus, browser and publication approvals are separate; this is a private author proposal.')}
for sec,(title,text)in OVERVIEW.items():add(sec,'overview-'+sec,title,text)
FIGTEXT={
'figure-1':'Panels a–c show the as-prepared ethanol, 1-propanol and 1-butanol products; panel d shows calcined 1-butanol material. Each image has a 5 nm bar. The local crystallites and SAED indices support CeO2, without establishing a pure whole as-prepared powder. The calcined panel also labels the 111 reflection.',
'figure-2':'As-prepared and calcined diffraction patterns are compared. The as-prepared pattern is unidentified; the calcined pattern is assigned cubic CeO2 after 200 °C for 3 h. The solvent and exact physical-batch correspondence are not explicit. The source supplies no atomic coordinates or numerical lattice parameter.',
'figure-3':'Panel a is thermogravimetry of as-prepared 1-butanol material. Panels b and c compare as-prepared and calcined DSC contexts. The 173 °C endotherm and author-inferred transition range are retained separately from the synthesis calcination conditions. TGA uses air; that atmosphere does not specify DSC or synthesis calcination.',
'figure-s1':'The four XPS panels are mapped from the SI first paragraph and plotted fitting context: a, as-prepared long exposure; b, as-prepared short exposure; c, calcined long exposure; d, calcined short exposure. The conflicting caption and fitting labels remain explicit. Short exposure has less-than, approximate and unqualified 15 min wording in different passages; long exposure is more than 5 h. No numerical spectral curve or missing complementary fraction is invented.'}
for num,(uid,u)in enumerate(U.items(),1):
 obj=resolve(PAY[u['payload_path']],u['json_pointer']);kind=u['kind'];oid=obj.get('id',u['json_pointer']);sec=section(UB[uid][0]['record_id']);title=obj.get('title',obj.get('name',u['title']));scope=obj.get('sample_scope',obj.get('label',oid));txt=title
 if kind=='facts':txt=obj['claim']
 elif kind=='materials':sec='precursors';txt=obj['name']+'. '+obj['scope_note']
 elif kind=='stocks':sec='precursors';txt=obj['name']+'. '+obj['scope_note']+' '+obj['preparation']
 elif kind=='protocols':txt=obj['title']+' retains separately identified operations and source-defined specimens; alternative solvents or analytical specimens are not pooled.'
 elif kind=='operation':title=obj['action'];txt=obj['action']+'. '+obj['quantity_scope_note']+' Missing fields: '+', '.join(obj['missing_fields'])+'.'
 elif kind=='sample_contexts':txt=obj['label']+'. '+obj.get('lineage_note','')+' '+obj['cross_technique_physical_batch_join']+'.';scope=obj['id']
 elif kind=='figures':txt=FIGTEXT[oid];scope=' / '.join(p['sample_id']for p in obj['panels'])
 elif kind=='figure_panel':fig=D['figures'][int(u['json_pointer'].split('/')[2])];title=fig['title']+' · panel '+obj['label'];txt='This original panel is assigned to '+obj['sample_id']+'. '+fig['scope_note'];scope=obj['sample_id']
 elif kind=='equations':txt=obj['raw_expression']+'. '+obj['note']+' '+ ' '.join(c['description']for c in D['conflicts']if c['id']in obj['conflict_ids'])
 elif kind=='table':txt='Table S1 retains the binding energies and FWHM of ten fitted XPS peaks, all 20 numerical cells and all 36 raw grid cells. Printed spin labels, peak assignments and spectrum 3(c) wording remain unresolved source context.'
 elif kind=='table_row':title='Table S1 · '+obj['source_group_header']+' '+obj['peak_label'];txt='The '+obj['peak_label']+' row preserves the printed '+obj['oxidation_assignment_as_printed']+' assignment, binding energy and FWHM. It belongs to the shared source fit context; inconsistent specimen labels are not silently resolved.'
 elif kind=='references':sec='sources';txt=obj['raw_citation']+' This citation does not imply that the prior full text was supplied or independently read.'
 elif kind in['conflicts','missingness','reference_gap']:sec='sources';txt=obj['description']
 else:raise AssertionError(kind)
 item=add(sec,'source-'+str(num)+'-'+norm(uid),title,txt,u['evidence'],uid,scope);item['canonical_links']=[{'record_id':b['record_id'],'json_pointer':b['pointer'],'relation':'Exact source-unit canonical pointer; no additional specimen join.'}for b in UB[uid]]
 UNITKEY[(kind,oid)]=uid
 if kind=='facts':item['claim_type']=obj['claim_class'];item['notes']+=[prose(c['description'])for c in D['conflicts']if c['id']in obj['conflict_ids']]
for rid,r in R.items():
 x=add(section(rid),'record-'+rid,r['title'].split(' · ',1)[1],r['method']+'. This record keeps the source preparation or analytical context separate. It does not add a replicate or a universal same-batch association.');x['canonical_links']=[{'record_id':rid,'json_pointer':'','relation':'Private unapproved canonical record.'}];x['notes']=[prose(s)for s in r['quality']['conflicts']]
PTRUNIT={}
for uid,bs in UB.items():
 for b in bs:PTRUNIT.setdefault((b['record_id'],b['pointer']),uid)
def unititem(kind,oid):return ITEM[UNIT[UNITKEY[(kind,oid)]][0]]
def nearest(rid,ptr):
 p=ptr
 while p:
  if(rid,p)in PTRUNIT:return ITEM[UNIT[PTRUNIT[(rid,p)]][0]]
  p=p.rsplit('/',1)[0]
 return ITEM['record-'+rid]
def displayed(q):
 if q['value']is not None:return q['value']
 lo,hi=q.get('minimum'),q.get('maximum')
 if lo is not None and hi is not None:return str(lo)+'–'+str(hi)
 if lo is not None:return('> 'if q.get('minimum_exclusive')else'≥ ')+str(lo)
 if hi is not None:return('< 'if q.get('maximum_exclusive')else'≤ ')+str(hi)
 return'Not reported'
def walk(v,ptr,rid):
 if isinstance(v,dict):
  if{'value','status','evidence'}<=v.keys():
   item=nearest(rid,ptr);label=ptr.rsplit('/',1)[-1].replace('_',' ');sid=None
   if ptr.startswith('/measurements/'):
    m=resolve(R[rid],'/'.join(ptr.split('/')[:3]));label=m['property'].replace('_',' ');sid=m['sample_id']
   q={'id':rid+'::'+ptr,'label':prose(label.capitalize()),'value':displayed(v),'unit':v.get('unit'),'status':v['status'],'approximate':v.get('approximate',False),'basis':'exact_canonical_field','qualifier':prose(' '.join(v.get(k,'')for k in['basis','qualifier','note'])),'evidence':evidence(v['evidence']),'canonical_record_id':rid,'json_pointer':ptr,'canonical_quantity':deepcopy(v),'presentation_kind':'exact_quantity','training_eligible':False}
   if sid:q['sample_id']=sid
   if isinstance(v['value'],str)and label=='source claim':q['value']=prose(v['value']);q['basis']='exact_canonical_claim_with_spacing_normalization'
   if isinstance(v['value'],str)and v['value'].startswith('{'):
    try:q['value']=json.loads(v['value']);q['presentation_kind']='curated_source_inventory';q['basis']='exact_canonical_payload_with_academic_display'
    except json.JSONDecodeError:pass
   item['facts'].append(q);FIELD[(rid,ptr)]=(item['id'],q);return
  for k,x in v.items():walk(x,ptr+'/'+esc(k),rid)
 elif isinstance(v,list):
  for j,x in enumerate(v):walk(x,ptr+'/'+str(j),rid)
for rid,r in R.items():
 for j,m in enumerate(r['materials']):
  it=unititem('materials',m['id']);it.setdefault('material_contexts',[]).append({'record_id':rid,'json_pointer':f'/materials/{j}',**deepcopy(m),'exact_molecular_asset_binding_approved':False});MAT[rid+'::'+m['id']]=it['id']
 for j,st in enumerate(r['stocks']):
  it=unititem('stocks',st['id']);it.setdefault('stock_contexts',[]).append({'record_id':rid,'json_pointer':f'/stocks/{j}',**deepcopy(st),'molecular_bindings_approved':False});STOCK[rid+'::'+st['id']]=it['id']
 for j,op in enumerate(r['operations']):
  it=unititem('operation',op['id']);it.setdefault('operation_contexts',[]).append({'record_id':rid,'json_pointer':f'/operations/{j}',**deepcopy(op),'apparatus_binding_approved':False});it['notes'].append(prose(op['description']));OPS[rid+'::'+op['id']]=it['id']
 for j,p in enumerate(r['products']):
  it=ITEM['record-'+rid];it.setdefault('product_contexts',[]).append({'record_id':rid,'json_pointer':f'/products/{j}',**deepcopy(p),'atomic_asset_binding_approved':False});it['canonical_links'].append({'record_id':rid,'json_pointer':f'/products/{j}','relation':'Exact source context; no new product assertion.'});PRODUCT[rid+'::'+p['sample_id']]=it['id']
 walk(r,'',rid)
 for j,m in enumerate(r['measurements']):MEAS[rid+'::'+m['id']]=FIELD[(rid,f'/measurements/{j}/value')][0]
FACTMAP={};TABLEMAP={}
for row in CV['facts']:
 bs=[]
 for b in row['canonical_bindings']:
  iid,q=FIELD[(b['record_id'],b['pointer'])];q.setdefault('source_fact_ids',[]).append(row['source_fact_id']);ITEM[iid]['source_fact_ids'].append(row['source_fact_id']);bs.append({**b,'reader_item_id':iid,'reader_fact_id':q['id']})
 FACTMAP[row['source_fact_id']]=bs
for row in CV['table_cells']:
 b=row['canonical_bindings'][0];iid,q=FIELD[(b['record_id'],b['pointer'])];q['source_table_cell_id']=row['source_cell_id'];TABLEMAP[row['source_cell_id']]={**b,'reader_item_id':iid,'reader_fact_id':q['id']}
for item in ITEM.values():
 item['canonical_links']=uniq(item['canonical_links']);item['source_fact_ids']=uniq(item['source_fact_ids']);item['notes']=uniq(item['notes'])
 for q in item['facts']:
  if q.get('sample_id'):
   rid=q['canonical_record_id'];j=next(j for j,p in enumerate(R[rid]['products'])if p['sample_id']==q['sample_id']);item['sample_scope']['canonical_sample_links'].append({'record_id':rid,'json_pointer':f'/products/{j}','sample_id':q['sample_id'],'relation':'Source-scoped canonical context, not a new batch join.'})
 for b in item['canonical_links']:
  if re.fullmatch(r'/products/\d+',b['json_pointer']):p=resolve(R[b['record_id']],b['json_pointer']);item['sample_scope']['canonical_sample_links'].append({**b,'sample_id':p['sample_id'],'recipe_link':p['recipe_link']})
 item['sample_scope']['canonical_sample_links']=list({(x['record_id'],x['json_pointer']):x for x in item['sample_scope']['canonical_sample_links']}.values())
for fig in D['figures']:
 for obj,it in [(fig,unititem('figures',fig['id']))]+[(p,unititem('figure_panel','/figures/'+str(D['figures'].index(fig))+'/panels/'+str(j)))for j,p in enumerate(fig['panels'])]:
  for label in([obj['sample_id']]if'sample_id'in obj else[p['sample_id']for p in obj['panels']]):
   rid=PRE+OWN['sample_owner'][label];j=next(j for j,p in enumerate(R[rid]['products'])if p['source_sample_label']==label);it['sample_scope']['canonical_sample_links'].append({'record_id':rid,'json_pointer':f'/products/{j}','sample_id':label,'relation':'Explicit source figure panel assignment; physical-batch identity across methods remains unknown.'})
  it['sample_scope']['canonical_sample_links']=list({(x['record_id'],x['json_pointer']):x for x in it['sample_scope']['canonical_sample_links']}.values())
ASSETUNIT={a['id']:[UNITKEY[('figures',a['id'])]]for a in A['assets']if a['id']in{f['id']for f in D['figures']}}
for j in range(4):ASSETUNIT['figure-1'+chr(97+j)]=[UNITKEY[('figure_panel','/figures/0/panels/'+str(j))]]
ASSETUNIT.update({'table-s1':[UNITKEY[('table','table-s1')]],'reaction':[UNITKEY[('equations','reaction')]],'xps-equations':[UNITKEY[('equations',e)]for e in['ceiii-area','ceiv-area','ceiii-percentage']]})
for aid,fids in {'materials-stocks':['stocks'],'workup-calcination':['calcination','alcohol-wash-dry'],'xps-fitting':['si-fitting'],'xps-results':['si-short-results','si-long-results'],'asprep-phase':['asprep-xrd'],'asprep-phase-continuation':['asprep-xrd'],'mechanism-conflict':['hydroxo-conflict'],'mechanism-conflict-continuation':['hydroxo-conflict']}.items():ASSETUNIT[aid]=[UNITKEY[('facts',SID+'-'+fid)]for fid in fids]
ASSETUNIT['si-reference-list']=[u['id']for u in U.values()if u['kind']=='references'and any(e['document_role']=='si'for e in u['evidence'])]
GROUP={k:[]for k in['figures','tables','schemes','equations','source_notes']};PUBLIC=[]
for a in A['assets']:
 assert sha(a['path'])==a['sha256']and not a['contains_complete_source_page'];uids=ASSETUNIT[a['id']];it=ITEM[UNIT[uids[0]][0]];kind=U[uids[0]]['kind'];group='figures'if kind in['figures','figure_panel']else'tables'if kind=='table'else'equations'if kind=='equations'else'source_notes';public='assets/figures/'+SID+'/'+Path(a['path']).name;rids=sorted({b['record_id']for uid in uids for b in UB[uid]})
 e={'id':SID+'-'+a['id'],'label':it['title'],'caption_paraphrase':it['text'],'document_role':a['document_role'],'page':a['pdf_page'],'printed_page':66+a['pdf_page']if a['document_role']=='main'else None,'sample_scope':deepcopy(it['sample_scope']),'sample_links':rids,'sample_linkage':'Source-defined context only; no extra same-aliquot or atomic-coordinate join.','public_asset':public,'public_asset_sha256':a['sha256'],'asset_provenance':{'source_sha256':a['source_sha256'],'source_pdf_page':a['pdf_page'],'crop_normalized':a['crop_fraction'],'source_render_dpi':a['dpi'],'pixel_dimensions':a['dimensions'],'transformation':'Selected original crop; no reconstructed data or whole-page attachment.'},'source_locators':[x['locator']for x in it['evidence']],'notes':it['notes'].copy(),'reader_render_verified':False,'reviewed':False,'training_eligible':False}
 if kind=='table':e.update(source_rows=deepcopy(T['tables'][0]['rows']),source_raw_grid=deepcopy(T['tables'][0]['raw_grid']))
 GROUP[group].append(e);PUBLIC.append({'id':e['id'],'private_path':a['path'],'public_asset':public,'sha256':a['sha256'],'selected_original_only':True,'publication_approved':False})
 for uid in uids:ITEM[UNIT[uid][0]]['original_assets'].append({'id':e['id'],'label':'Open original '+e['label'],'public_asset':public,'public_asset_sha256':a['sha256']})
docs=[]
for role in['main','si']:
 pages=[p for p in PC['pages']if p['document_role']==role];docs.append({'role':role,'filename':'10.1021_la8031286'+('_si_1'if role=='si'else'')+'.pdf','sha256':pages[0]['source_sha256'],'page_count':len(pages),'pages':[{'page':p['pdf_page'],'printed_page':66+p['pdf_page']if role=='main'else None,'text_read':p['text_read'],'visual_review':p['visual_review'],'sections':[p['coverage_note']]}for p in pages]})
routes={rid:[x for x in R if x!=rid]for rid,r in R.items()if r['record_type']=='literature_protocol'}
counts={'reader_items':len(ITEM),'source_units':len(UNIT),'source_facts':len(FACTMAP),'source_fact_bindings':sum(map(len,FACTMAP.values())),'source_table_cells':len(TABLEMAP),'typed_reader_fields':len(FIELD),'canonical_records':len(R),'operations':len(OPS),'material_slots':len(MAT),'stock_slots':len(STOCK),'sample_context_slots':len(PRODUCT),'measurements':len(MEAS),'selected_original_assets':len(PUBLIC),'full_page_public_assets':0,'main_pages':4,'si_pages_read':4,'eligible_training_rows':0,'atomic_structure_assets':0}
status='Complete supplied main/SI source extraction passed distinct audit; canonical/reader, visual, browser and publication gates remain separate.'
review={'schema_version':'1.0','paper_id':SID,'doi':D['doi'],'title':D['title'],'paper':{'authors':D['authors'],'year':2009,'journal':'Langmuir','volume':25,'pages':'67–70'},'source_group':SID,'review_scope':'complete_supplied_main_and_matched_si','documents':docs,'supporting_information':{'status':'locally_matched_complete_supplied_pages_read','matched_local_si_count':1,'pdf_pages':4,'scope':'Matched XPS spectra, fitting details and surface fractions; no separate raw data or atomic-coordinate file supplied.'},'coverage_status':'private_author_reader_proposal','independent_audit':status+' Historical source-payload pending flags record the extraction author-freeze stage.','publication_status':'Private unapproved proposal only.','source_review_promoted':False,'training_eligible':False,'recipe_inventory':[{'id':rid,'label':r['title'],'record_ids':[rid],'record_type':r['record_type'],'status':'author_draft_pending_independent_review','scope':'Three explicit solvent routes, separate diagnostic/calcination/acquisition procedures and observations; not an independent batch count.','gaps':r['quality']['missing_fields']}for rid,r in R.items()],'characterization_inventory':{'reader_item_ids':[i['id']for s in SECTIONS if s['id']in['structures','properties']for i in s['items']]},'chemical_intuition':{'reader_item_ids':[i['id']for s in SECTIONS if s['id']=='intuition'for i in s['items']]},'reader_contract':{'version':'1.0','section_ids':[s['id']for s in SECTIONS]},'reader_sections':SECTIONS,**GROUP,'remaining_gaps':[prose(g['description'])for g in D['missingness']]+[status],'evidence_conflicts':deepcopy(D['conflicts']),'route_evidence_contexts':routes,'route_evidence_scope_notes':{'all':'Linked records provide comparative study context, not an exact product measurement for every route.','specimens':'As-prepared/calcined powders, solution DLS, four exposure-dependent XPS contexts and local microscopy remain distinct.','structure':'No source coordinates, lattice parameter, qualified atomic model or exact pair.','chemistry':'Printed TEA formula and proposed species are not silently converted into verified solution complexes.'},'material_evidence_records':{'CeO2':[rid for rid,r in R.items()if r['material']['formula']=='CeO2']},'counts':counts}
save(SID+'.json',review);save('reader-bindings-proposal.json',{'source_id':SID,'status':'private_unapproved','reader_sha256':sha(O/(SID+'.json')),'original_assets':PUBLIC,'operation_to_reader_item':OPS,'material_to_reader_item':MAT,'stock_to_reader_item':STOCK,'product_to_reader_item':PRODUCT,'molecular_apparatus_bindings_approved':False,'publication_approved':False});save('source-item-coverage.json',{'source_units':UNIT,'source_facts':FACTMAP,'table_cells':TABLEMAP,'canonical_field_map':[{'record_id':rid,'json_pointer':ptr,'reader_item_id':v[0],'reader_fact_id':v[1]['id']}for(rid,ptr),v in FIELD.items()],'measurement_to_reader_item':MEAS,'private_canonical_manifest_sha256':sha(C/'record-manifest.json')})
checks=[]
def ck(n,ok):checks.append({'check':n,'passed':bool(ok)});assert ok,n
for(rid,ptr),(iid,q)in FIELD.items():ck(iid+' '+ptr+' exact field equality',resolve(R[rid],ptr)==q['canonical_quantity'])
for it in ITEM.values():
 for b in it['canonical_links']:ck(it['id']+' canonical pointer',resolve(R[b['record_id']],b['json_pointer'])is not None)
 for b in it['sample_scope']['canonical_sample_links']:ck(it['id']+' sample pointer',resolve(R[b['record_id']],b['json_pointer'])['sample_id']==b['sample_id'])
for a in PUBLIC:ck(a['id']+' crop hash',sha(a['private_path'])==a['sha256'])
ck('All218 units/58 facts/20numeric cells',len(UNIT)==218 and len(FACTMAP)==58 and len(TABLEMAP)==20)
ck('All canonical slots/operations/products/measurements',len(OPS)==35 and len(MAT)==CM['counts']['material_slots']and len(STOCK)==6 and len(PRODUCT)==CM['counts']['sample_context_slots']and len(MEAS)==CM['counts']['measurements'])
ck('20 selected crops only',len(PUBLIC)==20 and all(not a['contains_complete_source_page']for a in A['assets']))
ck('No local source path in reader',not re.search(r'[A-Z]:[\\/]',json.dumps(review)))
ck('Source and canonical unchanged',all(sha(p)==h for p,h in FR['bound_files'].items())and all(sha(x['path'])==x['sha256']for x in CM['records']))
save('author-validation.json',{'status':'author_pointer_transport_contract_checks_passed','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'check_count':len(checks),'checks':checks,'counts':counts,'independent_source_audit':'passed','independent_canonical_reader_audit':'pending','browser_visual_gate':'not_performed','site_written':False,'published':False})
paths=[P/n for n in['package-freeze.json','source-facts.json','source-inventory.json','source-tables.json','page-coverage.json','original-assets-manifest.json','source-independent-audit/independent-audit.json']]+[C/'record-manifest.json',C/'source-to-field-coverage.json',S/'scripts/build_paper_reviews.py',S/'dist/source-evidence.mjs']
save('reader-manifest.json',{'schema':'mattersyn-private-reader-proposal/1','source_id':SID,'version':1,'author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'status':'private_author_draft_pending_distinct_review','input_hashes':{str(p):sha(p)for p in paths},'outputs':{n:sha(O/n)for n in[SID+'.json','reader-bindings-proposal.json','source-item-coverage.json','author-validation.json']},'author_script_sha256':sha(__file__),'counts':counts,'published':False})
print(json.dumps(counts));print('READER',sha(O/(SID+'.json')))
